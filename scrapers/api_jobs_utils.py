"""Utilitários compartilhados por fontes públicas de vagas em JSON."""

from html.parser import HTMLParser

from core.job import _contem_termo, _normalizar


class _ExtratorTextoHTML(HTMLParser):
    _BLOCOS = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "section"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag in self._BLOCOS:
            self.partes.append("\n")

    def handle_endtag(self, tag: str):
        if tag in self._BLOCOS:
            self.partes.append("\n")

    def handle_data(self, data: str):
        self.partes.append(data)


def limpar_html_descricao(html: str) -> str:
    extrator = _ExtratorTextoHTML()
    extrator.feed(html or "")
    linhas = [" ".join(linha.split()) for linha in "".join(extrator.partes).splitlines()]
    return "\n".join(linha for linha in linhas if linha)


def titulo_em_ingles_do_nicho(titulo: str, keywords: list[str]) -> bool:
    titulo_norm = _normalizar(titulo)
    return any(
        _contem_termo(_normalizar(keyword), titulo_norm)
        for keyword in keywords
    )
