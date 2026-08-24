"""Ranking personalizado pelos dois currículos do candidato."""

from types import SimpleNamespace

import main
from core.job import Job
from core.perfis import PERFIL_CX, PERFIL_DADOS_BI
from notifier.telegram import _linha_match
from utils.filtro import filtrar_vagas


def _pontuar(job: Job, perfil) -> Job:
    vagas, _ = filtrar_vagas([job], perfil.regras)
    assert vagas == [job]
    return job


def test_descricao_completa_eleva_match_dados_bi_ao_teto_de_95():
    vaga = _pontuar(
        Job(
            titulo="Analista de Dados Júnior - Power BI e SQL",
            empresa="Empresa",
            local="Brasília - DF",
            modalidade="Presencial",
                link="https://example.com/dados",
                site="Teste",
                descricao=(
                    "Requisitos: Power BI, SQL e Python. "
                    "Pelo menos 2 anos de experiência com análise de dados."
                ),
        ),
        PERFIL_DADOS_BI,
    )

    assert vaga.relevancia == 10
    assert vaga.probabilidade_match == 95
    assert "experiência direta em Dados/BI" in vaga.motivo
    assert "skills comprovadas: power bi, sql, python" in vaga.motivo
    assert "senioridade alinhada" in vaga.motivo


def test_senioridade_acima_do_historico_reduz_match_sem_descartar_vaga():
    vaga = _pontuar(
        Job(
            titulo="Analista de Dados Sênior",
            empresa="Empresa",
            local="Remoto - Brasil",
            modalidade="Remoto",
            link="https://example.com/senior",
            site="LinkedIn",
        ),
        PERFIL_DADOS_BI,
    )

    assert vaga.relevancia == 3
    assert "nível acima do histórico comprovado" in vaga.motivo


def test_vaga_global_reconhece_ingles_fluente():
    vaga = _pontuar(
        Job(
            titulo="Data Analyst Junior",
            empresa="Global",
            local="Worldwide",
            modalidade="Remoto",
            escopo_indefinido=True,
            link="https://example.com/global",
            site="LinkedIn Global",
        ),
        PERFIL_DADOS_BI,
    )

    assert vaga.relevancia == 7
    assert "inglês fluente atende ao requisito" in vaga.motivo


def test_cx_usa_experiencia_e_metricas_proprias_do_nicho():
    vaga = _pontuar(
        Job(
            titulo="Analista de Customer Success Júnior - NPS e CSAT",
            empresa="Empresa",
            local="Brasília - DF",
            modalidade="Híbrido",
            link="https://example.com/cx",
            site="Teste",
            descricao="Requisitos: NPS, CSAT, Power BI e experiência com clientes.",
        ),
        PERFIL_CX,
    )

    assert vaga.relevancia == 10
    assert "experiência direta em CX/CS" in vaga.motivo
    assert "skills comprovadas: nps, csat, power bi" in vaga.motivo


def test_cargo_transferivel_de_cx_fica_abaixo_da_experiencia_direta():
    vaga = _pontuar(
        Job(
            titulo="Implementation Analyst - Customer Onboarding",
            empresa="Empresa",
            local="Brasília - DF",
            modalidade="Presencial",
            link="https://example.com/implementation",
            site="Teste",
        ),
        PERFIL_CX,
    )

    assert vaga.relevancia == 6
    assert "experiência transferível para CX/CS" in vaga.motivo


def test_requisitos_nao_comprovados_reduzem_match_e_ficam_explicitos():
    vaga = _pontuar(
        Job(
            titulo="Analista de Dados Júnior",
            empresa="Empresa",
            local="Brasília - DF",
            modalidade="Presencial",
            link="https://example.com/lacunas",
            site="Teste",
            descricao=(
                "Requisitos: graduação completa, Tableau e AWS. "
                "Mínimo de 5 anos de experiência em análise de dados."
            ),
        ),
        PERFIL_DADOS_BI,
    )

    assert vaga.relevancia == 2
    assert "cobertura ATS: 0/2 requisitos técnicos (0%)" in vaga.motivo
    assert "lacunas obrigatórias: aws, tableau" in vaga.motivo
    assert "pede 5+ anos; perfil comprova ~2" in vaga.motivo
    assert "graduação ainda em andamento" in vaga.motivo


def test_ferramenta_apenas_desejavel_nao_vira_lacuna():
    vaga = _pontuar(
        Job(
            titulo="Analista de Dados Júnior",
            empresa="Empresa",
            local="Brasília - DF",
            modalidade="Presencial",
            link="https://example.com/diferencial",
            site="Teste",
            descricao="Diferencial desejável: Tableau. Requisito: análise de dados.",
        ),
        PERFIL_DADOS_BI,
    )
    assert "lacunas obrigatórias:" not in vaga.motivo


def test_ats_reconhece_alias_e_mede_cobertura_dos_requisitos():
    vaga = _pontuar(
        Job(
            titulo="Data Analyst Junior",
            empresa="Empresa",
            local="Worldwide",
            modalidade="Remoto",
            escopo_indefinido=True,
            link="https://example.com/ats-alias",
            site="Jobicy",
            descricao=(
                "Requirements\nMicrosoft Power BI\nT-SQL\nTableau Desktop\n"
                "Nice to have\nAmazon Web Services"
            ),
        ),
        PERFIL_DADOS_BI,
    )

    assert "cobertura ATS: 2/3 requisitos técnicos (67%)" in vaga.motivo
    assert "skills comprovadas: power bi, sql" in vaga.motivo
    assert "lacunas obrigatórias: tableau" in vaga.motivo
    assert "aws" not in vaga.motivo.split("lacunas obrigatórias:", 1)[-1]


def test_anos_da_empresa_nao_viram_experiencia_exigida_do_candidato():
    vaga = _pontuar(
        Job(
            titulo="Analista de Dados",
            empresa="Empresa",
            local="Brasília - DF",
            modalidade="Presencial",
            link="https://example.com/idade-empresa",
            site="Teste",
            descricao="Empresa com mais de 40 anos de experiência no mercado. Requisitos: SQL.",
        ),
        PERFIL_DADOS_BI,
    )

    assert "pede 40+ anos" not in vaga.motivo


def test_pipeline_recalcula_match_depois_de_ler_descricao(monkeypatch):
    vaga = _pontuar(
        Job(
            titulo="Analista de Dados Júnior - Power BI e SQL",
            empresa="Empresa",
            local="Brasília - DF",
            modalidade="Presencial",
            link="https://example.com/recalculo",
            site="Teste",
        ),
        PERFIL_DADOS_BI,
    )
    assert vaga.relevancia == 7

    def enriquecer(job):
        job.descricao = "Requisitos: Power BI, SQL e Python."
        job.descricao_fonte = "HTML"
        return SimpleNamespace(metodo="HTML")

    monkeypatch.setattr(main, "enriquecer_vaga", enriquecer)
    monkeypatch.setattr(
        main,
        "obter_ajuste_match_feedback",
        lambda titulo, perfil: (0, 0, 0.0),
    )
    main._atualizar_match_com_descricao(
        vaga,
        PERFIL_DADOS_BI.regras,
        PERFIL_DADOS_BI.chave,
    )

    assert vaga.relevancia == 10
    assert vaga.probabilidade_match == 95


def test_pipeline_rejeita_presencial_no_exterior_depois_da_pagina_completa(monkeypatch):
    vaga = Job(
        titulo="Data Analyst",
        empresa="Petrovis group",
        local="Sukhbaatar, Ulaanbaatar Hot, Mongolia",
        modalidade="Remoto",
        modalidade_presumida=True,
        escopo_indefinido=True,
        link="https://example.com/petrovis",
        site="LinkedIn Global",
    )
    assert vaga.combina_com(PERFIL_DADOS_BI.regras)

    def enriquecer(job):
        job.descricao = "Descrição completa da vaga"
        job.descricao_fonte = "HTML"
        job.modalidade = "Presencial"
        job.modalidade_presumida = False
        return SimpleNamespace(metodo="HTML")

    monkeypatch.setattr(main, "enriquecer_vaga", enriquecer)

    assert not main._atualizar_match_com_descricao(
        vaga,
        PERFIL_DADOS_BI.regras,
        PERFIL_DADOS_BI.chave,
    )


def test_pipeline_rejeita_remoto_presumido_sem_confirmacao(monkeypatch):
    vaga = Job(
        titulo="Data Analyst",
        empresa="Empresa",
        local="Worldwide",
        modalidade="Remoto",
        modalidade_presumida=True,
        escopo_indefinido=True,
        link="https://example.com/sem-confirmacao",
        site="LinkedIn Global",
    )
    monkeypatch.setattr(
        main,
        "enriquecer_vaga",
        lambda job: SimpleNamespace(metodo="indisponível"),
    )

    assert not main._atualizar_match_com_descricao(
        vaga,
        PERFIL_DADOS_BI.regras,
        PERFIL_DADOS_BI.chave,
    )


def test_pipeline_aplica_calibracao_do_feedback(monkeypatch):
    vaga = Job(
        titulo="Analista de Dados Júnior",
        empresa="Empresa",
        local="Brasília - DF",
        modalidade="Presencial",
        link="https://example.com/feedback",
        site="Teste",
    )

    monkeypatch.setattr(
        main,
        "enriquecer_vaga",
        lambda job: SimpleNamespace(metodo="indisponível"),
    )
    monkeypatch.setattr(
        main,
        "obter_ajuste_match_feedback",
        lambda titulo, perfil: (1, 4, 0.75),
    )
    main._atualizar_match_com_descricao(
        vaga,
        PERFIL_DADOS_BI.regras,
        PERFIL_DADOS_BI.chave,
    )

    assert "feedback: 75% positivo em 4 vagas similares" in vaga.motivo


def test_pipeline_descarta_match_ats_muito_baixo(monkeypatch):
    vaga = Job(
        titulo="Senior Business Analyst",
        empresa="Empresa",
        local="LATAM",
        modalidade="Remoto",
        link="https://example.com/match-baixo",
        site="Jobicy",
        descricao=(
            "Requirements: Azure and 8 years of experience. "
            "Bachelor's degree required."
        ),
        descricao_fonte="API Jobicy",
    )
    monkeypatch.setattr(
        main,
        "enriquecer_vaga",
        lambda job: SimpleNamespace(metodo="API Jobicy"),
    )
    monkeypatch.setattr(
        main,
        "obter_ajuste_match_feedback",
        lambda titulo, perfil: (0, 0, 0.0),
    )

    assert not main._atualizar_match_com_descricao(
        vaga,
        PERFIL_DADOS_BI.regras,
        PERFIL_DADOS_BI.chave,
    )
    assert vaga.relevancia < 4


def test_telegram_exibe_percentual_de_match():
    assert _linha_match(8).endswith("(80%)")
    assert _linha_match(10).endswith("(95%)")
