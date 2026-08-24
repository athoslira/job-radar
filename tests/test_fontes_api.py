"""Novas fontes públicas de vagas remotas e preservação da descrição API."""

import core.descricao_vaga as descricao_vaga
import scrapers.jobicy as jobicy
import scrapers.remotive as remotive
from core.descricao_vaga import ResultadoLeitura, enriquecer_vaga
from core.job import Job
from scrapers.jobicy import JobicyScraper
from scrapers.remotive import RemotiveScraper


class _RespostaFake:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_remotive_filtra_titulo_e_entrega_descricao_completa(monkeypatch):
    payload = {"jobs": [
        {
            "title": "Data Analyst",
            "company_name": "Acme",
            "candidate_required_location": "Worldwide",
            "url": "https://remotive.com/remote-jobs/data/data-analyst-1",
            "publication_date": "2026-08-24T10:00:00",
            "description": "<h2>Requirements</h2><p>Power BI and SQL</p>",
        },
        {
            "title": "Software Engineer",
            "url": "https://remotive.com/remote-jobs/software/software-engineer-2",
        },
    ]}
    monkeypatch.setattr(remotive.requests, "get", lambda *args, **kwargs: _RespostaFake(payload))

    vagas = RemotiveScraper([], ["Data Analyst"]).buscar_vagas()

    assert len(vagas) == 1
    assert vagas[0].site == "Remotive"
    assert vagas[0].modalidade == "Remoto"
    assert vagas[0].descricao == "Requirements\nPower BI and SQL"


def test_jobicy_usa_categoria_do_nicho_e_restricao_geografica(monkeypatch):
    capturado = {}
    payload = {"jobs": [{
        "jobTitle": "Customer Success Manager",
        "companyName": "Acme",
        "jobGeo": "LATAM",
        "url": "https://jobicy.com/jobs/customer-success-manager",
        "pubDate": "2026-08-24 10:00:00",
        "jobDescription": "<p>Requirements: NPS and onboarding.</p>",
    }]}

    def get(*args, **kwargs):
        capturado.update(kwargs.get("params", {}))
        return _RespostaFake(payload)

    monkeypatch.setattr(jobicy.requests, "get", get)
    vagas = JobicyScraper([], "supporting", ["Customer Success Manager"]).buscar_vagas()

    assert capturado["industry"] == "supporting"
    assert len(vagas) == 1
    assert vagas[0].local == "LATAM"
    assert vagas[0].descricao_fonte == "API Jobicy"


def test_leitura_bloqueada_nao_apaga_descricao_recebida_da_api(monkeypatch):
    vaga = Job(
        titulo="Data Analyst",
        empresa="Acme",
        local="Worldwide",
        link="https://jobicy.com/jobs/data-analyst",
        site="Jobicy",
        modalidade="Remoto",
        descricao="Requirements: Power BI and SQL",
        descricao_fonte="API Jobicy",
    )
    monkeypatch.setattr(
        descricao_vaga._LEITOR,
        "ler",
        lambda link: ResultadoLeitura(bloqueada=True),
    )

    enriquecer_vaga(vaga)

    assert vaga.descricao == "Requirements: Power BI and SQL"
    assert vaga.descricao_fonte == "API Jobicy"
