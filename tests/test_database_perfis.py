"""Isolamento de Dados/BI e CX dentro do banco centralizado."""

import sqlite3

import database.database as db
from core.job import Job


def _vaga() -> Job:
    return Job(
        titulo="Analista de CX e Dados",
        empresa="Empresa Híbrida",
        local="Recife - PE",
        link="https://example.com/vaga-hibrida",
        site="Teste",
        modalidade="Presencial",
        relevancia=7,
    )


def test_mesma_vaga_pode_existir_nos_dois_perfis(monkeypatch, tmp_path):
    caminho = str(tmp_path / "jobs.db")
    monkeypatch.setattr(db, "DB_PATH", caminho)
    db.iniciar_db()

    vaga = _vaga()
    db.salvar_vaga(vaga, "dados_bi")

    assert db.ja_vista(vaga, "dados_bi")
    assert not db.ja_vista(vaga, "cx")

    db.salvar_vaga(vaga, "cx")
    assert db.ja_vista(vaga, "cx")

    with sqlite3.connect(caminho) as conn:
        linhas = conn.execute(
            "SELECT perfil, id FROM vagas_vistas ORDER BY perfil"
        ).fetchall()
    assert linhas == [("cx", vaga.id), ("dados_bi", vaga.id)]


def test_feedback_atualiza_somente_o_perfil_correto(monkeypatch, tmp_path):
    caminho = str(tmp_path / "jobs.db")
    monkeypatch.setattr(db, "DB_PATH", caminho)
    db.iniciar_db()

    vaga = _vaga()
    db.salvar_vaga(vaga, "dados_bi")
    db.salvar_vaga(vaga, "cx")
    db.definir_feedback(vaga.id, "positivo", "cx")

    with sqlite3.connect(caminho) as conn:
        feedbacks = dict(conn.execute(
            "SELECT perfil, feedback FROM vagas_vistas"
        ).fetchall())
    assert feedbacks == {"dados_bi": None, "cx": "positivo"}


def test_migra_banco_legado_sem_perder_historico(monkeypatch, tmp_path):
    caminho = str(tmp_path / "jobs_legado.db")
    with sqlite3.connect(caminho) as conn:
        conn.execute("""
            CREATE TABLE vagas_vistas (
                id TEXT PRIMARY KEY,
                titulo TEXT,
                empresa TEXT,
                local TEXT,
                link TEXT,
                site TEXT,
                encontrada_em TEXT DEFAULT CURRENT_TIMESTAMP,
                perfil TEXT
            )
        """)
        conn.execute(
            "INSERT INTO vagas_vistas (id, titulo, perfil) VALUES ('1', 'Antiga', NULL)"
        )
        conn.execute(
            "INSERT INTO vagas_vistas (id, titulo, perfil) VALUES ('2', 'Brasil', 'brasil')"
        )
        conn.execute(
            "INSERT INTO vagas_vistas (id, titulo, perfil) VALUES ('3', 'Exterior', 'internacional')"
        )

    monkeypatch.setattr(db, "DB_PATH", caminho)
    db.iniciar_db()

    with sqlite3.connect(caminho) as conn:
        info = conn.execute("PRAGMA table_info(vagas_vistas)").fetchall()
        pk = [nome for _, nome in sorted((linha[5], linha[1]) for linha in info if linha[5])]
        perfis = conn.execute(
            "SELECT perfil, COUNT(*) FROM vagas_vistas GROUP BY perfil ORDER BY perfil"
        ).fetchall()

    assert pk == ["perfil", "id"]
    assert perfis == [("dados_bi", 2), ("internacional", 1)]
