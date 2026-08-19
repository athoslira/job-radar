"""Extração otimizada da descrição e proteções do fallback OCR."""

from core.descricao_vaga import (
    LeitorDescricaoVaga,
    ResultadoLeitura,
    _limpar_texto,
    _pagina_bloqueada,
    _selecionar_descricao,
    _texto_ocr_parece_vaga,
)


def test_limpa_linhas_repetidas_e_espacos_sem_achatar_secoes():
    texto = "  Requisitos   \nRequisitos\n\n  Python   e   SQL  \n"
    assert _limpar_texto(texto) == "Requisitos\nPython e SQL"


def test_prefere_bloco_com_secoes_de_vaga_ao_corpo_de_navegacao():
    descricao = (
        "Sobre a vaga\nResponsabilidades\nCriar dashboards e análises.\n"
        "Requisitos\nPower BI, SQL e Python. " * 8
    )
    corpo = "Menu\nCookies\nVagas relacionadas\n" * 80
    assert _selecionar_descricao([descricao], corpo).startswith("Sobre a vaga")


def test_detecta_bloqueio_e_nao_confunde_descricao_longa_com_login_do_menu():
    assert _pagina_bloqueada("Verify you are human - CAPTCHA")
    assert not _pagina_bloqueada(
        "Descrição pública da vaga com muitos requisitos. " * 40
        + "Sign in to view this job"
    )


def test_ocr_so_e_aceito_quando_texto_parece_descricao_de_vaga():
    assert _texto_ocr_parece_vaga(
        ("Sobre a vaga. Responsabilidades e requisitos para o cargo. " * 12)
    )
    assert not _texto_ocr_parece_vaga("Menu cookies propaganda " * 30)


def test_cache_evitar_reabrir_mesma_vaga_em_dois_perfis():
    class LeitorFake(LeitorDescricaoVaga):
        def __init__(self):
            super().__init__()
            self.chamadas = 0

        def _ler_pagina(self, link: str) -> ResultadoLeitura:
            self.chamadas += 1
            return ResultadoLeitura("Descrição completa", "HTML")

    leitor = LeitorFake()
    primeira = leitor.ler("https://example.com/vaga")
    segunda = leitor.ler("https://example.com/vaga")

    assert primeira == segunda
    assert leitor.chamadas == 1
