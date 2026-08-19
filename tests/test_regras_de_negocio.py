"""Regras de negocio da usuaria, escritas como teste executavel.

Estas regras foram definidas por escrito e sao a especificacao do que o
JobRadar deve ou nao notificar. Ate aqui elas viviam so no config.py -- e
a lista CIDADES tinha divergido em dois sentidos ao mesmo tempo (faltava
Manaus, sobravam quatro cidades fora da regra) sem que nenhum dos 76
testes existentes percebesse.

Regra, resumida:
  BRASÍLIA -> presencial, híbrido ou remoto;
  BRASIL   -> fora de Brasília, somente 100% remoto;
  EXTERIOR -> somente 100% remoto, em busca/fonte de língua inglesa.
"""

import pytest

from core.job import Job
from core.perfis import PERFIL_BR, PERFIL_INTL


def _vaga(titulo, local, modalidade):
    return Job(
        titulo=titulo, empresa="Empresa Teste", local=local,
        link=f"https://exemplo.com/{abs(hash((titulo, local, modalidade)))}",
        site="Teste", modalidade=modalidade,
    )


CIDADES_ACEITAS = [
    ("Brasília", "DF"),
]


# ---------------------------------------------------------------- BRASIL

@pytest.mark.parametrize("modalidade", ["Híbrido", "Presencial"])
@pytest.mark.parametrize("cidade, uf", CIDADES_ACEITAS)
def test_br_hibrido_e_presencial_nas_cidades_aceitas(cidade, uf, modalidade):
    local = f"{cidade} - {uf}"
    assert _vaga("Analista de Dados", local, modalidade).combina_com(PERFIL_BR.regras)


# Variacoes de escrita que as fontes realmente usam -- separador, acento e
# caixa nao podem mudar o resultado.
@pytest.mark.parametrize("local", [
    "Brasília", "Brasília - DF", "Brasília, DF", "Brasília/DF",
    "BRASÍLIA - DF", "brasilia, df",
])
def test_br_variacoes_de_escrita_da_cidade(local):
    assert _vaga("Analista de Dados", local, "Híbrido").combina_com(PERFIL_BR.regras)


@pytest.mark.parametrize("modalidade", ["Híbrido", "Presencial"])
@pytest.mark.parametrize("local", [
    "São Paulo - SP", "Belo Horizonte, MG", "Salvador - BA",
    "Rio de Janeiro, RJ", "Curitiba - PR", "Recife - PE",
    "Fortaleza - CE", "Porto Alegre - RS",
    # Estavam em CIDADES por engano e aceitavam hibrida/presencial
    # fora da regra -- ver MEDIDO em config.py.
    "Jaboatão dos Guararapes - PE", "Teresina - PI",
    "São Luís - MA", "Petrolina - PE",
])
def test_br_hibrido_e_presencial_fora_das_cidades_e_rejeitado(local, modalidade):
    assert not _vaga("Analista de Dados", local, modalidade).combina_com(PERFIL_BR.regras)


@pytest.mark.parametrize("local", [
    "Remoto", "Remoto (São Paulo, SP)", "Remoto (Manaus, AM)",
    "Remoto - Brasil", "Remote, Brazil", "Remoto (Belo Horizonte, MG)",
])
def test_br_remoto_no_brasil_e_aceito_de_qualquer_cidade(local):
    """Remoto nao tem restricao de cidade -- a regra de CIDADES vale so
    pra hibrido/presencial."""
    assert _vaga("Analista de Dados", local, "Remoto").combina_com(PERFIL_BR.regras)


@pytest.mark.parametrize("local", [
    "Remote - US only", "Remote, United States", "Remote (Austin, TX)",
    "Remote - India",
])
def test_br_remoto_de_mercado_nao_aceito_e_rejeitado(local):
    assert not _vaga("Analista de Dados", local, "Remoto").combina_com(PERFIL_BR.regras)


# --------------------------------------------------------- INTERNACIONAL

@pytest.mark.parametrize("local", [
    "Remote - Spain", "Madrid, Spain", "España (En remoto)",
    "Remote - Mexico", "Ciudad de México, México", "Remote - Portugal",
    "Remote - Latin America", "Remote - Colombia", "Buenos Aires, Argentina",
])
def test_intl_remoto_em_mercado_aceito_e_aceito(local):
    assert _vaga("Data Analyst", local, "Remoto").combina_com(PERFIL_INTL.regras)


@pytest.mark.parametrize("modalidade", ["Híbrido", "Presencial"])
@pytest.mark.parametrize("local", [
    "Madrid, Spain", "Barcelona, España", "Lisboa, Portugal",
    "Ciudad de México, México", "Buenos Aires, Argentina",
])
def test_intl_hibrido_e_presencial_sempre_rejeitado(local, modalidade):
    """Do exterior so interessa vaga remota -- nem mesmo em Portugal ou
    Espanha vale presencial/hibrida."""
    assert not _vaga("Data Analyst", local, modalidade).combina_com(PERFIL_INTL.regras)


@pytest.mark.parametrize("local", [
    "Remote - US only", "Remote, United States", "Remote (Seattle, WA)",
    "Remote, but candidates must be located in the United States",
    "Remote - India", "Remote - United Kingdom",
])
def test_intl_remoto_de_mercado_de_lingua_inglesa_e_rejeitado(local):
    assert not _vaga("Data Analyst", local, "Remoto").combina_com(PERFIL_INTL.regras)


def test_intl_titulo_hibrido_vence_a_classificacao_da_fonte():
    """O filtro nativo do LinkedIn as vezes marca como remota uma vaga que
    o proprio anuncio chama de hibrida -- o titulo vence."""
    vaga = _vaga("Data Analyst (Analista de Datos) - Hybrid", "Madrid, Spain", "Remoto")
    assert vaga.modalidade == "Híbrido"
    assert not vaga.combina_com(PERFIL_INTL.regras)


def test_intl_remoto_sem_mercado_declarado_exige_idioma_no_titulo():
    """Sem pais declarado nao da pra saber o mercado -- ai o titulo precisa
    dizer o idioma. Sem nenhum dos dois sinais, a vaga nao entra."""
    assert _vaga("Data Analyst (Spanish speaker)", "Remote - Worldwide", "Remoto").combina_com(PERFIL_INTL.regras)
    assert not _vaga("Data Analyst", "Remote - Worldwide", "Remoto").combina_com(PERFIL_INTL.regras)


# ------------------------------------------------------------------ CARGO

@pytest.mark.parametrize("titulo, esperado", [
    ("Analista de Dados Pleno", True),
    ("Analista de BI", True),
    ("Business Intelligence Analyst", True),
    ("Business Analyst", False),               # ambiguo, sem qualificador
    ("Business Analyst com SQL", True),        # ambiguo + qualificador
    ("Analista de Power BI", True),            # ferramenta + cargo
    ("Desenvolvedor Power BI", False),         # ferramenta sem cargo de analise
    ("Vendedor Externo", False),
    ("Engenheiro de Dados", False),
])
def test_cargo_no_titulo(titulo, esperado):
    assert _vaga(titulo, "Brasília - DF", "Presencial").combina_com(PERFIL_BR.regras) is esperado


# ------------------------- CIDADE DE NOME PARECIDO, ESTADO DIFERENTE

@pytest.mark.parametrize("local", [
    "Brasília de Minas - MG",
    "BRASÍLIA DE MINAS - MG",
    "Brasília - MG",
])
def test_cidade_de_nome_parecido_em_outro_estado_e_rejeitada(local):
    assert not _vaga("Analista de Dados", local, "Presencial").combina_com(PERFIL_BR.regras)


@pytest.mark.parametrize("local", [
    "Brasília - DF", "BRASÍLIA - DF", "Brasília, DF", "Brasilia/DF",
])
def test_cidade_certa_com_a_uf_certa_continua_passando(local):
    assert _vaga("Analista de Dados", local, "Presencial").combina_com(PERFIL_BR.regras)


@pytest.mark.parametrize("local", [
    "Brasília", "Brasilia", "Vaga em Brasília",
])
def test_sem_uf_declarada_a_cidade_continua_valendo(local):
    assert _vaga("Analista de Dados", local, "Presencial").combina_com(PERFIL_BR.regras)
