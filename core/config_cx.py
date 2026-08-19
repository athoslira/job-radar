"""Vocabulário do perfil de Customer Experience / Customer Success.

Os termos de busca são deliberadamente mais amplos que o filtro final:
os portais podem encontrar o cargo pela descrição, mas uma vaga só é
aprovada quando o próprio título confirma que pertence ao nicho de CX.
Isso evita transformar atendimento, suporte, vendas e gestão de contas
em falsos positivos só porque a descrição menciona clientes.
"""


KEYWORDS_CARGO_FORTE_CX = [
    "Customer Success Analyst",
    "Customer Success Manager",
    "Customer Success Specialist",
    "Customer Success Associate",
    "Customer Success Coordinator",
    "Customer Success Consultant",
    "Customer Success Executive",
    "Customer Success Lead",
    "Head of Customer Success",
    "Analista de Customer Success",
    "Especialista de Customer Success",
    "Coordenador de Customer Success",
    "Coordenadora de Customer Success",
    "Gerente de Customer Success",
    "Analista de Sucesso do Cliente",
    "Especialista em Sucesso do Cliente",
    "Coordenador de Sucesso do Cliente",
    "Coordenadora de Sucesso do Cliente",
    "Gerente de Sucesso do Cliente",
    "Customer Experience Analyst",
    "Customer Experience Manager",
    "Customer Experience Specialist",
    "Customer Experience Coordinator",
    "Customer Experience Lead",
    "Head of Customer Experience",
    "Analista de Customer Experience",
    "Especialista de Customer Experience",
    "Coordenador de Customer Experience",
    "Coordenadora de Customer Experience",
    "Gerente de Customer Experience",
    "Analista de Experiência do Cliente",
    "Especialista em Experiência do Cliente",
    "Coordenador de Experiência do Cliente",
    "Coordenadora de Experiência do Cliente",
    "Gerente de Experiência do Cliente",
    "CX Analyst",
    "CX Specialist",
    "CX Coordinator",
    "CX Manager",
    "Analista de CX",
    "Especialista de CX",
    "Coordenador de CX",
    "Coordenadora de CX",
    "Gerente de CX",
    "Customer Journey Analyst",
    "Customer Journey Manager",
    "Voice of Customer Analyst",
    "Voice of Customer Manager",
    "Analista de Jornada do Cliente",
    "Analista de Voz do Cliente",
]


# Estes títulos existem em vários departamentos. Só passam quando o título
# também contém um dos qualificadores abaixo (por exemplo, "Analista de
# Relacionamento com Clientes" ou "Customer Onboarding Analyst").
KEYWORDS_CARGO_AMBIGUO_CX = [
    "Analista de Relacionamento",
    "Analista de Atendimento",
    "Analista de Retenção",
    "Analista de Onboarding",
    "Account Manager",
    "Onboarding Analyst",
    "Onboarding Specialist",
    "Implementation Analyst",
]


QUALIFICADORES_CX = [
    "cliente",
    "clientes",
    "customer",
    "client",
    "cx",
    "success",
    "experience",
    "nps",
    "csat",
    "churn",
    "jornada",
    "journey",
    "voice of customer",
    "voz do cliente",
    "voc",
]


KEYWORDS_CX = KEYWORDS_CARGO_FORTE_CX + KEYWORDS_CARGO_AMBIGUO_CX


# Ferramentas aparecem só na busca, nunca aprovam uma vaga sozinhas.
# Assim "Zendesk Administrator" ou "Salesforce Developer" não entra no
# radar, enquanto uma descrição de "Analista de Customer Success" que use
# essas ferramentas ainda pode ser encontrada pelo portal.
TERMOS_BUSCA_CX_EXTRA = [
    "customer success remoto",
    "customer experience remoto",
    "sucesso do cliente",
    "experiência do cliente",
    "jornada do cliente",
    "voice of customer",
    "customer onboarding",
    "customer retention",
    "gainsight customer success",
    "zendesk customer experience",
    "hubspot customer success",
]


TERMOS_BUSCA_CX = sorted(
    set(termo.lower() for termo in KEYWORDS_CX + TERMOS_BUSCA_CX_EXTRA)
)


# Começa um pouco abaixo do perfil de Dados/BI para reduzir carga e permitir
# calibrar a precisão do nicho novo com o feedback do Telegram.
TERMOS_POR_CICLO_CX = 8
