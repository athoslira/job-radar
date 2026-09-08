from datetime import date
from types import SimpleNamespace

import pytest

import main
from core.perfis import DefinicaoScraper, FREQUENCIA_ALTA, FREQUENCIA_BAIXA
from scrapers.base import BaseScraper, FonteIndisponivel


class FonteAltaVazia(BaseScraper):
    def __init__(self, termos_busca):
        self.termos_busca = termos_busca

    def buscar_vagas(self):
        return []


class FonteBaixaVazia(FonteAltaVazia):
    pass


class OutraFonteBaixaVazia(FonteAltaVazia):
    pass


class FonteBaixaComFalha(FonteAltaVazia):
    def buscar_vagas(self):
        raise FonteIndisponivel("indisponível")


def _perfil(*definicoes):
    return SimpleNamespace(
        chave="teste",
        nome="Teste",
        termos_busca=["analista"],
        definicao_scrapers=list(definicoes),
        max_scrapers_concorrentes=2,
    )


@pytest.fixture
def metadados(monkeypatch):
    dados = {}
    monkeypatch.setattr(main, "obter_metadado", dados.get)
    monkeypatch.setattr(main, "definir_metadado", dados.__setitem__)
    return dados


def test_cadencia_diaria_e_independente_por_fonte(metadados):
    perfil = _perfil(
        DefinicaoScraper(FonteAltaVazia, FREQUENCIA_ALTA),
        DefinicaoScraper(FonteBaixaVazia, FREQUENCIA_BAIXA),
        DefinicaoScraper(OutraFonteBaixaVazia, FREQUENCIA_BAIXA),
    )

    primeira = main._construir_scrapers(perfil, ["analista"])
    assert {type(s) for s in primeira} == {
        FonteAltaVazia,
        FonteBaixaVazia,
        OutraFonteBaixaVazia,
    }

    main._marcar_fonte_baixa_como_concluida(
        perfil, next(s for s in primeira if type(s) is FonteBaixaVazia)
    )

    segunda = main._construir_scrapers(perfil, ["analista"])
    assert {type(s) for s in segunda} == {FonteAltaVazia, OutraFonteBaixaVazia}
    assert metadados[
        "baixa_frequencia_ultimo_dia_teste_FonteBaixaVazia"
    ] == date.today().isoformat()


def test_fonte_vazia_e_sucesso_e_recebe_marcador_diario(monkeypatch, metadados):
    perfil = _perfil(DefinicaoScraper(FonteBaixaVazia, FREQUENCIA_BAIXA))
    mensagens = []
    monkeypatch.setattr(main, "_proximo_bloco_termos", lambda _perfil: ["analista"])
    monkeypatch.setattr(main, "_enviar_heartbeat_diario", lambda *args: None)
    monkeypatch.setattr(main, "_enviar_digest_diario", lambda *args: None)
    monkeypatch.setattr(main, "enviar_mensagem", mensagens.append)

    main.ciclo_de_busca(perfil)

    assert metadados[
        "baixa_frequencia_ultimo_dia_teste_FonteBaixaVazia"
    ] == date.today().isoformat()
    assert mensagens == []


def test_fonte_com_falha_nao_recebe_marcador_e_volta_no_proximo_ciclo(
    monkeypatch, metadados
):
    perfil = _perfil(DefinicaoScraper(FonteBaixaComFalha, FREQUENCIA_BAIXA))
    monkeypatch.setattr(main, "_proximo_bloco_termos", lambda _perfil: ["analista"])
    monkeypatch.setattr(main, "_enviar_heartbeat_diario", lambda *args: None)
    monkeypatch.setattr(main, "_enviar_digest_diario", lambda *args: None)
    monkeypatch.setattr(main, "enviar_mensagem", lambda *_args: None)

    main.ciclo_de_busca(perfil)

    assert "baixa_frequencia_ultimo_dia_teste_FonteBaixaComFalha" not in metadados
    proximo = main._construir_scrapers(perfil, ["analista"])
    assert [type(s) for s in proximo] == [FonteBaixaComFalha]


class FonteComConsultas(BaseScraper):
    def buscar_vagas(self):
        return []


def test_monitoramento_preserva_sucesso_parcial():
    fonte = FonteComConsultas()

    assert fonte._executar_consulta(lambda: ["vaga"]) == ["vaga"]
    assert fonte._executar_consulta(
        lambda: (_ for _ in ()).throw(FonteIndisponivel("falhou"))
    ) == []
    fonte._validar_disponibilidade()

    assert fonte.consultas_total == 2
    assert fonte.consultas_com_falha == 1


def test_monitoramento_sinaliza_falha_total():
    fonte = FonteComConsultas()
    fonte._executar_consulta(
        lambda: (_ for _ in ()).throw(FonteIndisponivel("falhou"))
    )

    with pytest.raises(FonteIndisponivel):
        fonte._validar_disponibilidade()
