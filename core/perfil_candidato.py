"""Mapas derivados dos currículos e de confirmações explícitas do usuário.

Os dois mapas são separados para uma experiência forte em CX não inflar
artificialmente uma vaga de Dados/BI (e vice-versa). O inglês fluente foi
confirmado diretamente pelo usuário após a leitura dos currículos.
"""

from core.match import MapaMatchCurriculo


MAPA_MATCH_DADOS_BI = MapaMatchCurriculo(
    nicho="Dados/BI",
    cargos_experiencia_direta=(
        "analista de dados", "data analyst", "analista de performance",
        "performance analyst", "analista de bi", "bi analyst",
        "business intelligence", "business intelligence analyst",
        "reporting analyst", "data quality analyst", "data insights analyst",
    ),
    cargos_experiencia_transferivel=(
        "business analyst", "analista de negócios", "analista de processos",
        "process analyst", "operations analyst", "analista de operações",
        "crm analyst", "marketing analyst", "insights analyst",
    ),
    competencias_comprovadas=(
        "power bi", "sql", "postgresql", "mysql", "python", "etl",
        "dashboard", "reporting", "kpi", "excel", "automação", "automation",
        "n8n", "api", "django", "vue", "supabase",
        "meta ads", "google ads", "tráfego pago",
    ),
    lacunas_conhecidas=(
        "tableau", "qlik", "looker", "bigquery", "snowflake",
        "databricks", "spark", "aws", "azure", "r studio", "linguagem r",
    ),
    competencias_equivalentes=(
        ("power bi", "powerbi", "microsoft power bi"),
        ("sql", "t-sql", "pl/sql", "structured query language"),
        ("etl", "elt", "pipeline de dados", "data pipeline"),
        ("dashboard", "dashboards", "visualização de dados", "data visualization"),
        ("reporting", "relatório", "relatórios", "reports"),
        ("kpi", "kpis", "indicadores", "métricas de negócio", "business metrics"),
        ("excel", "microsoft excel", "excel avançado", "advanced excel", "power query"),
        ("automação", "automation", "automatização"),
        ("api", "apis", "rest api", "restful api"),
    ),
    lacunas_equivalentes=(
        ("tableau", "tableau desktop"),
        ("looker", "looker studio", "google data studio"),
        ("bigquery", "google bigquery"),
        ("snowflake", "snowflake data cloud"),
        ("aws", "amazon web services"),
        ("azure", "microsoft azure"),
        ("linguagem r", "r studio", "rstudio", "programação em r"),
    ),
    anos_experiencia_relevante=2,
    ingles_fluente=True,
    formacao_superior_concluida=False,
)


MAPA_MATCH_CX = MapaMatchCurriculo(
    nicho="CX/CS",
    cargos_experiencia_direta=(
        "customer success", "sucesso do cliente", "sucesso de franqueados",
        "customer experience", "experiência do cliente", "analista de cx",
        "cx analyst", "customer journey", "jornada do cliente",
        "voice of customer", "voz do cliente",
    ),
    cargos_experiencia_transferivel=(
        "analista de relacionamento", "relationship analyst",
        "analista de atendimento", "customer support", "customer care",
        "analista de retenção", "retention analyst", "onboarding analyst",
        "onboarding specialist", "implementation analyst", "account manager",
        "customer operations",
    ),
    competencias_comprovadas=(
        "nps", "csat", "nrr", "retenção", "retention", "onboarding",
        "customer health", "atendimento", "stakeholder", "carteira",
        "franquia", "franchise", "kpi",
        "power bi", "excel", "dashboard",
    ),
    lacunas_conhecidas=(
        "salesforce", "zendesk", "gainsight", "hubspot", "totango",
        "intercom", "freshdesk",
    ),
    competencias_equivalentes=(
        ("nps", "net promoter score"),
        ("csat", "customer satisfaction score"),
        ("nrr", "net revenue retention"),
        ("retenção", "retention", "renovação", "renewal"),
        ("onboarding", "customer onboarding", "implantação de clientes"),
        ("customer health", "health score", "customer health score"),
        ("atendimento", "customer service", "customer support"),
        ("carteira", "carteira de clientes", "book of business"),
        ("franquia", "franchise", "franqueados"),
        ("kpi", "kpis", "indicadores", "customer metrics"),
        ("dashboard", "dashboards", "painéis gerenciais"),
    ),
    lacunas_equivalentes=(
        ("salesforce", "salesforce crm"),
        ("hubspot", "hubspot crm"),
        ("zendesk", "zendesk support"),
    ),
    anos_experiencia_relevante=4,
    ingles_fluente=True,
    formacao_superior_concluida=False,
)
