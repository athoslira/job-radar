"""Contrato do novo perfil de Customer Experience / Customer Success."""

import pytest

from core.job import Job
from core.perfis import PERFIL_CX, PERFIL_DADOS_BI


def _vaga(titulo: str) -> Job:
    return Job(
        titulo=titulo,
        empresa="Empresa",
        local="Recife - PE",
        link=f"https://example.com/{titulo}",
        site="Teste",
        modalidade="Presencial",
    )


@pytest.mark.parametrize(
    "titulo",
    [
        "Customer Success Analyst",
        "Analista de Experiência do Cliente",
        "CX Specialist",
        "Analista de Relacionamento com Clientes",
        "Customer Onboarding Analyst",
        "Account Manager - Customer Success",
        "Voice of Customer Analyst",
    ],
)
def test_cargos_de_cx_sao_aprovados(titulo):
    assert _vaga(titulo).combina_com(PERFIL_CX.regras)


@pytest.mark.parametrize(
    "titulo",
    [
        "Analista de Relacionamento",
        "Analista de Atendimento",
        "Customer Support Engineer",
        "Operador de Telemarketing",
        "Sales Account Manager",
        "Analista Financeiro com foco no cliente",
        "Analista de Dados",
    ],
)
def test_titulos_ambiguos_ou_de_outros_nichos_sao_rejeitados(titulo):
    assert not _vaga(titulo).combina_com(PERFIL_CX.regras)


def test_perfis_nao_se_confundem():
    assert _vaga("Analista de Dados Pleno").combina_com(PERFIL_DADOS_BI.regras)
    assert not _vaga("Analista de Dados Pleno").combina_com(PERFIL_CX.regras)
    assert _vaga("Customer Success Analyst").combina_com(PERFIL_CX.regras)
    assert not _vaga("Customer Success Analyst").combina_com(PERFIL_DADOS_BI.regras)
