"""Leitura da descrição completa com Playwright e OCR como fallback.

O navegador é aberto sob demanda e reaproveitado por toda a execução. A
extração prioriza texto acessível do DOM, que é mais rápido e fiel. OCR só
roda quando o texto é insuficiente e nunca é usado em CAPTCHA/login.
"""

from __future__ import annotations

import atexit
from dataclasses import dataclass
from io import BytesIO
import os
import re
from typing import TYPE_CHECKING

from core.logger import get_logger

if TYPE_CHECKING:
    from core.job import Job


logger = get_logger()

_MINIMO_TEXTO_UTIL = 350
_MAXIMO_CARACTERES = int(os.getenv("JOB_DESCRIPTION_MAX_CHARS", "20000"))
_TIMEOUT_MS = int(os.getenv("JOB_DESCRIPTION_TIMEOUT_MS", "15000"))
_OCR_ATIVO = os.getenv("JOB_DESCRIPTION_OCR", "1").strip().lower() not in {
    "0", "false", "nao", "não",
}

_SELETORES_DESCRICAO = (
    "[data-testid*='description']",
    "[data-test*='description']",
    "[id*='job-description']",
    "[id*='jobDescription']",
    "[class*='job-description']",
    "[class*='jobDescription']",
    "[class*='description']",
    ".show-more-less-html__markup",
    "article",
    "main",
)

_TERMOS_BLOQUEIO = (
    "captcha", "verify you are human", "verifique que voce e humano",
    "confirme que voce e humano", "access denied", "acesso negado",
    "sign in to view this job", "faca login para ver esta vaga",
    "log in to continue", "entre para continuar", "login required",
    "authentication required",
)


@dataclass(frozen=True)
class ResultadoLeitura:
    descricao: str = ""
    metodo: str = "indisponível"
    bloqueada: bool = False


def _limpar_texto(texto: str) -> str:
    linhas = []
    for linha in texto.replace("\u00a0", " ").splitlines():
        limpa = re.sub(r"[ \t]+", " ", linha).strip()
        if limpa and (not linhas or limpa != linhas[-1]):
            linhas.append(limpa)
    return "\n".join(linhas)[:_MAXIMO_CARACTERES]


def _pagina_bloqueada(texto: str) -> bool:
    normalizado = texto.lower()
    sem_acento = (
        normalizado.replace("á", "a").replace("ã", "a").replace("â", "a")
        .replace("é", "e").replace("ê", "e").replace("í", "i")
        .replace("ó", "o").replace("ô", "o").replace("õ", "o")
        .replace("ú", "u").replace("ç", "c")
    )
    return len(texto) < 1200 and any(termo in sem_acento for termo in _TERMOS_BLOQUEIO)


def _pontuar_bloco(texto: str) -> int:
    normalizado = texto.lower()
    cabecalhos = (
        "responsabilidades", "requisitos", "qualificações", "qualificacoes",
        "requirements", "responsibilities", "what you'll do", "about the role",
        "sobre a vaga", "descrição da vaga", "descricao da vaga",
    )
    bonus = sum(1800 for termo in cabecalhos if termo in normalizado)
    ruido = sum(
        normalizado.count(termo) * 250
        for termo in ("vagas relacionadas", "política de privacidade", "cookie", "menu")
    )
    return min(len(texto), _MAXIMO_CARACTERES) + bonus - ruido


def _selecionar_descricao(candidatos: list[str], corpo: str = "") -> str:
    blocos = [_limpar_texto(texto) for texto in candidatos]
    blocos = [texto for texto in blocos if len(texto) >= 120]
    if blocos:
        return max(blocos, key=_pontuar_bloco)
    corpo_limpo = _limpar_texto(corpo)
    return corpo_limpo if len(corpo_limpo) >= _MINIMO_TEXTO_UTIL else ""


def _texto_por_ocr(imagem: bytes) -> str:
    if not _OCR_ATIVO:
        return ""
    try:
        import pytesseract
        from PIL import Image

        comando = os.getenv("TESSERACT_CMD", "").strip()
        if comando:
            pytesseract.pytesseract.tesseract_cmd = comando

        idiomas_disponiveis = set(pytesseract.get_languages(config=""))
        idiomas = [idioma for idioma in ("por", "eng") if idioma in idiomas_disponiveis]
        if not idiomas:
            return ""
        texto = pytesseract.image_to_string(
            Image.open(BytesIO(imagem)),
            lang="+".join(idiomas),
            config="--oem 3 --psm 6",
            timeout=10,
        )
        return _limpar_texto(texto)
    except (ImportError, RuntimeError, OSError):
        return ""


def _texto_ocr_parece_vaga(texto: str) -> bool:
    normalizado = texto.lower()
    sinais = (
        "requisitos", "requirements", "responsabilidades", "responsibilities",
        "qualificações", "qualificacoes", "qualifications", "sobre a vaga",
        "about the role", "experiência", "experiencia", "experience",
    )
    return len(texto) >= _MINIMO_TEXTO_UTIL and sum(
        sinal in normalizado for sinal in sinais
    ) >= 2


class LeitorDescricaoVaga:
    """Browser compartilhado, cacheado por URL, para toda a execução."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._cache: dict[str, ResultadoLeitura] = {}

    def _iniciar(self):
        if self._browser is not None:
            return
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._context = self._browser.new_context(
            locale="pt-BR",
            ignore_https_errors=True,
            viewport={"width": 1440, "height": 1800},
        )
        self._context.set_default_timeout(3000)

    @staticmethod
    def _expandir_descricao(page):
        padrao = re.compile(
            r"^(ver mais|mostrar mais|show more|see more|read more|mais detalhes)$",
            re.IGNORECASE,
        )
        clicados = 0
        for botao in page.locator("button, [role='button']").all():
            if clicados >= 3:
                break
            try:
                if padrao.match(botao.inner_text(timeout=500).strip()):
                    botao.click(timeout=1000)
                    clicados += 1
            except Exception:
                continue

    @staticmethod
    def _coletar_blocos(page) -> list[str]:
        candidatos: list[str] = []
        for frame in page.frames:
            for seletor in _SELETORES_DESCRICAO:
                try:
                    locator = frame.locator(seletor)
                    for indice in range(min(locator.count(), 6)):
                        texto = locator.nth(indice).inner_text(timeout=1500)
                        if texto:
                            candidatos.append(texto)
                except Exception:
                    continue
        return candidatos

    @staticmethod
    def _tem_desafio_visual(page) -> bool:
        seletores = (
            "iframe[src*='captcha']", "iframe[src*='recaptcha']",
            "[class*='captcha']", "[id*='captcha']",
            "#challenge-form", "[class*='cf-challenge']",
        )
        for seletor in seletores:
            try:
                if page.locator(seletor).count() > 0:
                    return True
            except Exception:
                continue
        return False

    def _ler_pagina(self, link: str) -> ResultadoLeitura:
        self._iniciar()
        page = self._context.new_page()
        try:
            page.goto(link, wait_until="domcontentloaded", timeout=_TIMEOUT_MS)
            page.wait_for_timeout(700)
            self._expandir_descricao(page)

            try:
                corpo = page.locator("body").inner_text(timeout=2500)
            except Exception:
                corpo = ""
            corpo = _limpar_texto(corpo)
            if _pagina_bloqueada(corpo) or self._tem_desafio_visual(page):
                return ResultadoLeitura(bloqueada=True)

            descricao = _selecionar_descricao(self._coletar_blocos(page), corpo)
            if len(descricao) >= _MINIMO_TEXTO_UTIL:
                return ResultadoLeitura(descricao=descricao, metodo="HTML")

            # Fallback para descrição renderizada em canvas/imagem. Não roda
            # em páginas bloqueadas (checagem acima), portanto não lê CAPTCHA.
            imagem = page.screenshot(full_page=True, type="png", scale="css")
            texto_ocr = _texto_por_ocr(imagem)
            if len(texto_ocr) > len(descricao) and _texto_ocr_parece_vaga(texto_ocr):
                return ResultadoLeitura(descricao=texto_ocr, metodo="OCR")
            if descricao:
                return ResultadoLeitura(descricao=descricao, metodo="HTML parcial")
            return ResultadoLeitura()
        finally:
            page.close()

    def ler(self, link: str) -> ResultadoLeitura:
        if link in self._cache:
            return self._cache[link]
        if not link.lower().startswith(("http://", "https://")):
            resultado = ResultadoLeitura()
        else:
            try:
                resultado = self._ler_pagina(link)
            except Exception as erro:
                logger.warning(
                    "Descrição completa indisponível (%s); usando cartão da vaga.",
                    type(erro).__name__,
                )
                resultado = ResultadoLeitura()
        self._cache[link] = resultado
        return resultado

    def fechar(self):
        if self._context is not None:
            self._context.close()
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()
        self._context = self._browser = self._playwright = None


_LEITOR = LeitorDescricaoVaga()
atexit.register(_LEITOR.fechar)


def enriquecer_vaga(job: Job) -> ResultadoLeitura:
    resultado = _LEITOR.ler(job.link)
    job.descricao = resultado.descricao
    job.descricao_fonte = resultado.metodo
    return resultado
