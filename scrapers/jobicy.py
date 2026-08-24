"""Fonte remota pública da Jobicy, segmentada pelo nicho."""

import requests

from core.job import Job
from core.logger import get_logger
from scrapers.api_jobs_utils import limpar_html_descricao, titulo_em_ingles_do_nicho
from scrapers.base import BaseScraper


logger = get_logger()
_URL = "https://jobicy.com/api/v2/remote-jobs"


class JobicyScraper(BaseScraper):
    def __init__(
        self,
        termos_busca: list[str],
        industry: str,
        keywords_titulo_global: list[str] | None = None,
    ):
        self.termos_busca = termos_busca
        self.industry = industry
        self.keywords_titulo_global = keywords_titulo_global or termos_busca

    def buscar_vagas(self) -> list[Job]:
        try:
            resposta = requests.get(
                _URL,
                params={"count": 100, "industry": self.industry},
                headers={"User-Agent": "JobRadar/1.0 (personal job search)"},
                timeout=25,
            )
            resposta.raise_for_status()
            itens = resposta.json().get("jobs", [])
        except (requests.RequestException, ValueError, TypeError) as erro:
            logger.warning("[Jobicy] API indisponível (%s).", type(erro).__name__)
            return []

        vagas: list[Job] = []
        for item in itens:
            titulo = str(item.get("jobTitle") or "").strip()
            link = str(item.get("url") or "").strip()
            if not titulo or not link or not titulo_em_ingles_do_nicho(
                titulo, self.keywords_titulo_global
            ):
                continue
            vagas.append(Job(
                titulo=titulo,
                empresa=str(item.get("companyName") or "Não informado").strip(),
                local=str(item.get("jobGeo") or "Anywhere").strip(),
                link=link,
                site="Jobicy",
                publicado_em=str(item.get("pubDate") or "").strip(),
                descricao=limpar_html_descricao(str(item.get("jobDescription") or "")),
                descricao_fonte="API Jobicy",
                modalidade="Remoto",
            ))

        logger.info(
            "[Jobicy/%s] %s vaga(s) aderente(s) encontrada(s).",
            self.industry,
            len(vagas),
        )
        return vagas
