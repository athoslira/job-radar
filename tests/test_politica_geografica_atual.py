"""Contrato atual de localização compartilhado por Dados/BI e CX."""

import pytest

from core.config import (
    LOCATIONS_LINKEDIN_CIDADES_PRESENCIAL,
    LOCATIONS_LINKEDIN_REMOTO_APENAS,
)
from core.job import Job
from core.perfis import PERFIL_CX, PERFIL_DADOS_BI
from core.config import KEYWORDS_CARGO_INGLES
from core.config import TERMOS_BUSCA_GLOBAL_DADOS_BI
from core.config_cx import KEYWORDS_CX_INGLES, TERMOS_BUSCA_GLOBAL_CX
from scrapers.linkedin import LinkedInScraper, _titulo_global_em_ingles


CASOS_PERFIL = [
    (PERFIL_DADOS_BI, "Data Analyst"),
    (PERFIL_CX, "Customer Success Analyst"),
]


def _vaga(titulo: str, local: str, modalidade: str, **kwargs) -> Job:
    return Job(
        titulo=titulo,
        empresa="Empresa",
        local=local,
        modalidade=modalidade,
        link=f"https://example.com/{abs(hash((titulo, local, modalidade)))}",
        site="Teste",
        **kwargs,
    )


@pytest.mark.parametrize("perfil,titulo", CASOS_PERFIL)
@pytest.mark.parametrize("modalidade", ["Presencial", "Híbrido", "Remoto"])
def test_brasilia_aceita_todas_as_modalidades(perfil, titulo, modalidade):
    assert _vaga(titulo, "Brasília - DF", modalidade).combina_com(perfil.regras)


@pytest.mark.parametrize("perfil,titulo", CASOS_PERFIL)
def test_resto_do_brasil_aceita_somente_remoto(perfil, titulo):
    assert _vaga(titulo, "São Paulo - SP", "Remoto").combina_com(perfil.regras)
    assert not _vaga(titulo, "São Paulo - SP", "Híbrido").combina_com(perfil.regras)
    assert not _vaga(titulo, "Recife - PE", "Presencial").combina_com(perfil.regras)


@pytest.mark.parametrize("perfil,titulo", CASOS_PERFIL)
def test_exterior_exige_remoto(perfil, titulo):
    vaga_global = _vaga(
        titulo,
        "Worldwide",
        "Remoto",
        escopo_indefinido=True,
    )
    assert vaga_global.combina_com(perfil.regras)
    assert not _vaga(titulo, "London, United Kingdom", "Híbrido").combina_com(perfil.regras)


def test_busca_presencial_fica_so_em_brasilia_e_global_so_remoto():
    assert LOCATIONS_LINKEDIN_CIDADES_PRESENCIAL == ["Brasília"]
    assert LOCATIONS_LINKEDIN_REMOTO_APENAS == ["Worldwide"]
    assert all(termo.isascii() for termo in TERMOS_BUSCA_GLOBAL_DADOS_BI)
    assert all(termo.isascii() for termo in TERMOS_BUSCA_GLOBAL_CX)


@pytest.mark.parametrize(
    "titulo,keywords,esperado",
    [
        ("Senior Data Analyst", KEYWORDS_CARGO_INGLES, True),
        ("Analista de Datos", KEYWORDS_CARGO_INGLES, False),
        ("Customer Success Analyst", KEYWORDS_CX_INGLES, True),
        ("Analista de Experiência do Cliente", KEYWORDS_CX_INGLES, False),
    ],
)
def test_eixo_mundial_aceita_somente_titulo_em_ingles(titulo, keywords, esperado):
    assert _titulo_global_em_ingles(titulo, keywords) is esperado


@pytest.mark.parametrize(
    "perfil,keywords,termos",
    [
        (PERFIL_DADOS_BI, KEYWORDS_CARGO_INGLES, TERMOS_BUSCA_GLOBAL_DADOS_BI),
        (PERFIL_CX, KEYWORDS_CX_INGLES, TERMOS_BUSCA_GLOBAL_CX),
    ],
)
def test_cada_nicho_configura_seu_vocabulario_global(perfil, keywords, termos):
    definicao = next(
        item for item in perfil.definicao_scrapers
        if item.classe is LinkedInScraper
    )
    assert definicao.kwargs_extras["keywords_titulo_global"] == keywords
    assert definicao.kwargs_extras["termos_busca_global"] == termos


@pytest.mark.parametrize("perfil", [PERFIL_DADOS_BI, PERFIL_CX])
def test_we_work_remotely_nao_participa_de_nenhum_fluxo_ativo(perfil):
    nomes = {definicao.classe.__name__ for definicao in perfil.definicao_scrapers}
    assert "WeWorkRemotelyIntlScraper" not in nomes
