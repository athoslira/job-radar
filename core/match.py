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
    # Grupos de equivalência no formato (nome canônico, alias 1, alias 2...).
    # ATS comerciais normalmente normalizam variações antes de comparar;
    # aqui isso é explícito e auditável, sem inventar experiência nova.
    competencias_equivalentes: tuple[tuple[str, ...], ...] = ()
    lacunas_equivalentes: tuple[tuple[str, ...], ...] = ()
    anos_experiencia_relevante: int = 0
    ingles_fluente: bool = False
    formacao_superior_concluida: bool = False


@dataclass(frozen=True)
class ResultadoMatch:
    pontos: int
    sinais: tuple[str, ...]

    @property
    def percentual(self) -> int:
        return min(95, self.pontos * 10)


def _encontrar_termos(texto: str, termos: tuple[str, ...]) -> list[str]:
    return [termo for termo in termos if _contem_termo(texto, termo)]


def _grupos_de_termos(
    termos: tuple[str, ...],
    equivalentes: tuple[tuple[str, ...], ...],
) -> tuple[tuple[str, ...], ...]:
    """Une termos literais e grupos de sinônimos sem contar duplicado."""
    aliases_agrupados = {
        alias for grupo in equivalentes if grupo for alias in grupo
    }
    individuais = tuple((termo,) for termo in termos if termo not in aliases_agrupados)
    return tuple(grupo for grupo in equivalentes if grupo) + individuais


def _encontrar_grupos(texto: str, grupos: tuple[tuple[str, ...], ...]) -> list[str]:
    return [
        grupo[0]
        for grupo in grupos
        if any(_contem_termo(texto, alias) for alias in grupo)
    ]


_SINAIS_OBRIGATORIO = (
    "requisito", "requirements", "qualification", "must have", "must-have",
    "obrigatorio", "necessario", "necessaria", "mandatory", "minimum",
    "minimo", "at least", "pelo menos", "what we are looking for",
    "what we're looking for", "o que buscamos", "perfil que buscamos",
)
_SINAIS_OPCIONAL = (
    "desejavel", "diferencial", "nice to have", "preferred", "optional",
    "bonus", "seria um plus", "considerado um plus",
)
_CABECALHOS_NEUTROS = (
    "responsabilidades", "responsibilities", "about the role", "sobre a vaga",
    "beneficios", "benefits", "atividades", "what you will do", "what you'll do",
)


def _classificar_requisitos(
    descricao: str,
    grupos: tuple[tuple[str, ...], ...],
) -> tuple[set[str], set[str], set[str]]:
    """Separa competências obrigatórias, opcionais e apenas mencionadas.

    Mantém o estado do cabeçalho da seção e também reconhece marcadores na
    própria frase. Assim, "Requisitos" vale para as linhas seguintes, mas
    "Diferencial: Tableau" nunca vira lacuna obrigatória.
    """
    obrigatorios: set[str] = set()
    opcionais: set[str] = set()
    gerais: set[str] = set()
    secao = "geral"
    blocos = re.split(r"[\r\n]+|(?<=[.!?;])\s+", descricao)
    for bloco in blocos:
        normalizado = _normalizar(bloco).strip()
        if not normalizado:
            continue

        tem_opcional = any(sinal in normalizado for sinal in _SINAIS_OPCIONAL)
        tem_obrigatorio = any(sinal in normalizado for sinal in _SINAIS_OBRIGATORIO)
        cabecalho_curto = len(normalizado) <= 90
        if tem_opcional:
            tipo = "opcional"
            if cabecalho_curto:
                secao = "opcional"
        elif tem_obrigatorio:
            tipo = "obrigatorio"
            if cabecalho_curto:
                secao = "obrigatorio"
        elif cabecalho_curto and any(
            cabecalho in normalizado for cabecalho in _CABECALHOS_NEUTROS
        ):
            secao = "geral"
            tipo = "geral"
        else:
            tipo = secao

        encontrados = _encontrar_grupos(bloco, grupos)
        destino = {
            "obrigatorio": obrigatorios,
            "opcional": opcionais,
            "geral": gerais,
        }[tipo]
        destino.update(encontrados)

    # Uma menção obrigatória prevalece sobre repetição opcional/geral.
    opcionais -= obrigatorios
    gerais -= obrigatorios | opcionais
    return obrigatorios, opcionais, gerais


def _anos_exigidos(descricao: str) -> int | None:
    """Maior requisito plausível de anos próximo de 'experiência'.

    O teto de 15 elimina idade da empresa/candidato e frases institucionais
    como "40 anos de experiência no mercado", que antes viravam requisito
    individual e derrubavam o match indevidamente.
    """
    texto = _normalizar(descricao)
    encontrados: list[int] = []
    padrao = re.compile(r"(?<!\d)(\d{1,2})\s*(?:\+|ou mais)?\s*(?:anos?|years?)")
    for match in padrao.finditer(texto):
        contexto = texto[max(0, match.start() - 90):match.end() + 90]
        if "experien" in contexto and not any(
            termo in contexto for termo in ("desejavel", "nice to have", "preferred")
        ):
            anos = int(match.group(1))
            if 1 <= anos <= 15:
                encontrados.append(anos)
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
    - cobertura dos requisitos técnicos: até 3, proporcional ao que o
      currículo comprova, com deságio de até 3 por lacunas obrigatórias;
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
    grupos_comprovados = _grupos_de_termos(
        mapa.competencias_comprovadas,
        mapa.competencias_equivalentes,
    )
    grupos_lacunas = _grupos_de_termos(
        mapa.lacunas_conhecidas,
        mapa.lacunas_equivalentes,
    )
    competencias = _encontrar_grupos(texto_vaga, grupos_comprovados)

    obrigatorios_ok: set[str] = set()
    opcionais_ok: set[str] = set()
    obrigatorios_lacuna: set[str] = set()
    if descricao:
        obrigatorios_ok, opcionais_ok, _ = _classificar_requisitos(
            descricao, grupos_comprovados
        )
        obrigatorios_lacuna, _, _ = _classificar_requisitos(
            descricao, grupos_lacunas
        )

    total_obrigatorios = len(obrigatorios_ok) + len(obrigatorios_lacuna)
    if total_obrigatorios:
        cobertura = len(obrigatorios_ok) / total_obrigatorios
        pontos += round(3 * cobertura)
        sinais.append(
            "cobertura ATS: "
            f"{len(obrigatorios_ok)}/{total_obrigatorios} requisitos técnicos "
            f"({cobertura:.0%})"
        )
    elif competencias:
        pontos += min(3, len(competencias))

    if competencias:
        sinais.append("skills comprovadas: " + ", ".join(competencias[:4]))
    if opcionais_ok:
        pontos += 1
        sinais.append("diferenciais comprovados: " + ", ".join(sorted(opcionais_ok)[:3]))
    if obrigatorios_lacuna:
        pontos -= min(3, len(obrigatorios_lacuna))
        sinais.append(
            "lacunas obrigatórias: "
            + ", ".join(sorted(obrigatorios_lacuna)[:4])
        )

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
        # Sem requisitos não existe base para um ATS afirmar aderência alta,
        # ainda que título, senioridade e localização pareçam perfeitos.
        pontos = min(pontos, 7)

    return ResultadoMatch(
        pontos=max(0, min(10, pontos)),
        sinais=tuple(sinais),
    )
