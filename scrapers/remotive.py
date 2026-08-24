"""Fonte remota pública da Remotive.

A API oficial entrega vagas ativas com descrição completa e restrição
geográfica do candidato. A coleta acontece uma vez por execução da fonte,
sem uma requisição por termo, respeitando a recomendação de baixa frequência.
"""

import requests

from core.job import Job
from core.logger import get_logger
from scrapers.api_jobs_utils import limpar_html_descricao, titulo_em_ingles_do_nicho
from scrapers.base import BaseScraper


logger = get_logger()
_URL = "https://remotive.com/api/remote-jobs"


class RemotiveScraper(BaseScraper):
    def __init__(
        self,
        termos_busca: list[str],
        keywords_titulo_global: list[str] | None = None,
    ):
        self.termos_busca = termos_busca
        self.keywords_titulo_global = keywords_titulo_global or termos_busca

    def buscar_vagas(self) -> list[Job]:
        try:
            resposta = requests.get(
                _URL,
                headers={"User-Agent": "JobRadar/1.0 (personal job search)"},
                timeout=25,
            )
            resposta.raise_for_status()
            itens = resposta.json().get("jobs", [])
        except (requests.RequestException, ValueError, TypeError) as erro:
            logger.warning(
                "[Remotive] API indisponível (%s).",
                type(erro).__name__,
            )
            return []

        vagas: list[Job] = []
        for item in itens:
            titulo = str(item.get("title") or "").strip()
            link = str(item.get("url") or "").strip()
            if not titulo or not link or not titulo_em_ingles_do_nicho(
                titulo, self.keywords_titulo_global
            ):
                continue
            vagas.append(Job(
                titulo=titulo,
                empresa=str(item.get("company_name") or "Não informado").strip(),
                local=str(item.get("candidate_required_location") or "Worldwide").strip(),
                link=link,
                site="Remotive",
                publicado_em=str(item.get("publication_date") or "").strip(),
                descricao=limpar_html_descricao(str(item.get("description") or "")),
                descricao_fonte="API Remotive",
                modalidade="Remoto",
            ))

        logger.info("[Remotive] %s vaga(s) aderente(s) encontrada(s).", len(vagas))
        return vagas
