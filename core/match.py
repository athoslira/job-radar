"""Pontuação explicável de aderência entre vaga e currículo.

O resultado continua sendo um *match estimado*, não uma probabilidade
estatística de contratação. O cálculo cruza título e descrição completa
com fatos declarados pelo candidato e deixa explícitas as lacunas.
"""

from dataclasses import dataclass
import re
import unicodedata


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sem_acento if not unicodedata.combining(c))


def _contem_termo(texto: str, termo: str) -> bool:
    return re.search(
        rf"(?<!\w){re.escape(_normalizar(termo))}(?!\w)",
        _normalizar(texto),
    ) is not None


@dataclass(frozen=True)
class MapaMatchCurriculo:
    """Sinais profissionais comprovados para um nicho específico."""

    nicho: str
    cargos_experiencia_direta: tuple[str, ...]
    cargos_experiencia_transferivel: tuple[str, ...]
    competencias_comprovadas: tuple[str, ...]
    lacunas_conhecidas: tuple[str, ...] = ()
    anos_experiencia_relevante: int = 0
    ingles_fluente: bool = False
    formacao_superior_concluida: bool = False


@dataclass(frozen=True)
class ResultadoMatch:
    pontos: int
    sinais: tuple[str, ...]

    @property
    def percentual(self) -> int:
        return self.pontos * 10


def _encontrar_termos(texto: str, termos: tuple[str, ...]) -> list[str]:
    return [termo for termo in termos if _contem_termo(texto, termo)]


def _encontrar_lacunas_exigidas(texto: str, termos: tuple[str, ...]) -> list[str]:
    """Só penaliza ferramenta próxima de linguagem de obrigatoriedade."""
    normalizado = _normalizar(texto)
    obrigatorios = (
        "requisito", "requirements", "required", "must have", "must-have",
        "obrigatorio", "necessario", "necessaria", "mandatory",
    )
    opcionais = ("desejavel", "diferencial", "nice to have", "preferred", "optional")
    encontrados: list[str] = []
    for termo in termos:
        termo_norm = _normalizar(termo)
        for match in re.finditer(rf"(?<!\w){re.escape(termo_norm)}(?!\w)", normalizado):
            contexto = normalizado[max(0, match.start() - 300):match.end() + 80]
            if any(sinal in contexto for sinal in opcionais):
                continue
            if any(sinal in contexto for sinal in obrigatorios):
                encontrados.append(termo)
                break
    return encontrados


def _anos_exigidos(descricao: str) -> int | None:
    """Maior requisito explícito de anos próximo de 'experiência'."""
    texto = _normalizar(descricao)
    encontrados: list[int] = []
    padrao = re.compile(r"(?<!\d)(\d{1,2})\s*(?:\+|ou mais)?\s*(?:anos?|years?)")
    for match in padrao.finditer(texto):
        contexto = texto[max(0, match.start() - 90):match.end() + 90]
        if "experien" in contexto and not any(
            termo in contexto for termo in ("desejavel", "nice to have", "preferred")
        ):
            encontrados.append(int(match.group(1)))
    return max(encontrados) if encontrados else None


def _exige_ingles(texto: str) -> bool:
    normalizado = _normalizar(texto)
    padroes = (
        "ingles fluente", "fluencia em ingles", "english fluency",
        "fluent english", "fluent in english", "advanced english",
        "ingles avancado", "business english",
    )
    return any(padrao in normalizado for padrao in padroes)


def _exige_formacao_concluida(texto: str) -> bool:
    normalizado = _normalizar(texto)
    padroes = (
        "graduacao completa", "ensino superior completo",
        "superior completo", "bachelor's degree required",
        "bachelors degree required", "completed bachelor's degree",
    )
    return any(padrao in normalizado for padrao in padroes)


def calcular_match_curriculo(
    mapa: MapaMatchCurriculo,
    titulo: str,
    descricao: str,
    senioridade: str,
    geografia_confirmada: bool,
    vaga_global_em_ingles: bool,
) -> ResultadoMatch:
    """Calcula 0–10 por proximidade, requisitos, nível e localização.

    Pesos deliberadamente simples e auditáveis:
    - experiência no cargo: 4 direta, 3 transferível, 2 aderência genérica;
    - competências comprovadas na descrição/título: até 3;
    - senioridade: +2 alinhada, +1 não informada, -2 acima do histórico;
    - geografia/mercado confirmado: +1;
    - inglês explícito: +1 quando atendido, -1 quando não atendido;
    - anos, formação e ferramentas ausentes: deságios explícitos.

    A vaga já passou pelo filtro do nicho antes desta função; por isso existe
    um piso de 2 pontos para cargo aderente mesmo quando o título não replica
    literalmente um cargo anterior.
    """
    sinais: list[str] = []

    diretos = _encontrar_termos(titulo, mapa.cargos_experiencia_direta)
    transferiveis = _encontrar_termos(titulo, mapa.cargos_experiencia_transferivel)
    if diretos:
        pontos = 4
        sinais.append(f"experiência direta em {mapa.nicho}")
    elif transferiveis:
        pontos = 3
        sinais.append(f"experiência transferível para {mapa.nicho}")
    else:
        pontos = 2
        sinais.append(f"cargo aderente a {mapa.nicho}")

    texto_vaga = f"{titulo}\n{descricao}" if descricao else titulo
    competencias = _encontrar_termos(texto_vaga, mapa.competencias_comprovadas)
    if competencias:
        pontos += min(3, len(competencias))
        sinais.append("skills comprovadas: " + ", ".join(competencias[:4]))

    lacunas = (
        _encontrar_lacunas_exigidas(descricao, mapa.lacunas_conhecidas)
        if descricao else []
    )
    if lacunas:
        pontos -= min(2, len(lacunas))
        sinais.append("lacunas: " + ", ".join(lacunas[:3]))

    if senioridade in {"Júnior", "Pleno"}:
        pontos += 2
        sinais.append("senioridade alinhada")
    elif senioridade == "Não especificado" or senioridade.startswith("Nível "):
        pontos += 1
        sinais.append("senioridade não informada")
    elif senioridade in {"Sênior", "Especialista", "Liderança"}:
        pontos -= 2
        sinais.append("nível acima do histórico comprovado")

    if geografia_confirmada:
        pontos += 1
        sinais.append("geografia confirmada")

    ingles_exigido = vaga_global_em_ingles or _exige_ingles(descricao)
    if ingles_exigido:
        if mapa.ingles_fluente:
            pontos += 1
            sinais.append("inglês fluente atende ao requisito")
        else:
            pontos -= 1
            sinais.append("inglês não comprovado")

    anos = _anos_exigidos(descricao)
    if anos is not None:
        if anos <= mapa.anos_experiencia_relevante:
            sinais.append(f"experiência atende {anos}+ anos")
        else:
            diferenca = anos - mapa.anos_experiencia_relevante
            pontos -= min(2, diferenca)
            sinais.append(
                f"pede {anos}+ anos; perfil comprova ~{mapa.anos_experiencia_relevante}"
            )

    if _exige_formacao_concluida(descricao) and not mapa.formacao_superior_concluida:
        pontos -= 1
        sinais.append("graduação ainda em andamento")

    if not descricao:
        sinais.append("descrição completa indisponível")

    return ResultadoMatch(
        pontos=max(0, min(10, pontos)),
        sinais=tuple(sinais),
    )
