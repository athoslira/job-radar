<div align="center">

<!-- ![JobRadar](assets/cover.png) -->

# 📡 JobRadar
### Monitor automatizado de vagas de Dados/BI e Customer Experience

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Scraping-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Banco%20versionado-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Cron-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Tests](https://img.shields.io/badge/testes-359%20passing-success?style=for-the-badge)
![Status](https://img.shields.io/badge/status-aguardando%20Telegram-yellow?style=for-the-badge)

**Autora:** Liliam Kezia Oliveira Souza

</div>

---

## 💎 Proposta de valor

> O **JobRadar** monitora continuamente dois nichos independentes — **Dados/BI** e **CX** —, identifica cada notificação no mesmo bot do Telegram e mantém deduplicação, digest e feedback separados por perfil. Em Brasília aceita vagas presenciais, híbridas e remotas; no restante do Brasil, apenas remotas; no exterior, apenas 100% remotas em inglês.

## 📄 Resumo executivo

Entre 07 e 15 de agosto, o sistema já processou **1.052 vagas únicas**, sem intervenção manual nenhuma — mas os números também expõem os riscos reais da arquitetura atual:

| Achado | Número |
|---|---|
| 📊 Vagas processadas (deduplicadas) | **1.052** |
| 🔗 Concentração numa única fonte (LinkedIn) | **89,5%** |
| 🧪 Testes automatizados (CI a cada push) | **359** |
| 🌎 Fontes monitoradas | **9** |
| ⏱️ Frequência de checagem | **a cada 3h** |
| 💰 Custo de infraestrutura | **R$ 0** |

A concentração em LinkedIn é um risco medido, não ignorado: o endpoint usado não é oficial e o próprio código documenta a chance de bloqueio — por isso parte do trabalho recente foi medir o rendimento de cada fonte secundária e paginar mais fundo nelas, em vez de só empilhar fonte nova.

---

## 📸 Como chega pra você

<!-- ![Notificação no Telegram](assets/screenshots/notificacao.png) -->

Vaga com match alto chega na hora, com percentual estimado, sinais do currículo, nível e link. O resto do dia entra num resumo único, ranqueado — sem virar spam.

---

## 🗂️ Sumário

- [Como funciona (pipeline)](#-como-funciona-pipeline)
- [Arquitetura técnica](#%EF%B8%8F-arquitetura-técnica)
- [Estrutura do repositório](#-estrutura-do-repositório)
- [Como ativar](#-como-ativar-no-github-actions)
- [Testes](#-testes)

---

## 🧭 Como funciona (pipeline)

| Etapa | O que faz |
|---|---|
| **Busca** | Varre as fontes em paralelo, com rodízio de termos pra controlar custo por ciclo |
| **Filtra** | Brasília em qualquer modalidade; Brasil somente remoto fora do DF; exterior somente remoto em inglês |
| **Lê a vaga** | Abre apenas vagas novas aprovadas, extrai a descrição via HTML e usa OCR quando necessário |
| **Pontua** | Avaliação ATS de até 95%, com cobertura de requisitos e mapas separados do currículo para Dados/BI e CX |
| **Deduplica** | Por perfil, link e empresa+título, sem deixar um nicho apagar o outro |
| **Notifica** | Match alto na hora; o resto num resumo diário ranqueado, melhor vaga no topo |
| **Aprende** | Após 3 avaliações similares, 👍/👎 calibra o match sem reagir a uma opinião isolada |

## 🏗️ Arquitetura técnica

- **Filtro em 3 níveis de confiança:** cargo inequívoco passa sozinho; cargo ambíguo (ex: "Business Analyst") só conta com qualificador de dados junto no título; ferramenta (ex: "Power BI") só conta com palavra de cargo junto — nada aprova por palavra-chave solta.
- **Leitura completa otimizada:** um Chromium compartilhado lê o HTML da descrição apenas depois do filtro inicial. O mesmo link é cacheado entre Dados/BI e CX. OCR em português/inglês só entra quando o texto acessível é insuficiente e nunca é usado para contornar CAPTCHA ou login.
- **Match baseado em ATS e currículo:** separa requisito obrigatório de diferencial, normaliza sinônimos, calcula cobertura técnica atendida, cruza experiência direta/transferível, anos, senioridade, graduação, geografia e inglês fluente. Match abaixo de 40% é descartado após a leitura completa.
- **Fontes públicas adicionais:** Jobicy (categorias próprias de Data Science & Analytics e Customer Support & Success) e Remotive trazem descrição completa por API, com acesso público ao anúncio e ao link de candidatura, e rodam em baixa frequência. We Work Remotely não participa mais do fluxo porque adicionava uma barreira de assinatura à candidatura.
- **Calibração progressiva:** com no mínimo três vagas de título semelhante, feedback positivo ≥75% acrescenta um ponto e ≤25% retira um; amostras pequenas ou inconclusivas não alteram o ranking.
- **Sem falsa precisão:** o percentual não representa chance estatística de contratação e mantém teto de 95%. A notificação informa se analisou HTML, OCR ou apenas o cartão, além dos pontos fortes e lacunas encontrados.
- **Um bot, dois nichos:** Dados/BI e CX compartilham chat e banco, mas mantêm estado e feedback separados pelo perfil.
- **Política geográfica única:** Brasília aceita presencial/híbrido/remoto; o restante do Brasil só remoto; o eixo mundial usa busca remota e títulos em inglês.
- **Zero infraestrutura:** GitHub Actions como motor de cron, SQLite como banco — versionado no próprio Git, o histórico de vagas já vistas *é* o commit.
- **Resiliente:** nunca marca vaga como "vista" sem confirmar que a notificação saiu; alerta automático se metade das fontes falhar num ciclo; heartbeat diário confirmando que o robô ainda está de pé.
- **Execução somente no GitHub Actions:** Chromium, Tesseract e os modelos de idioma são instalados pelo workflow; não existe serviço local ou VPS para configurar.
- **359 testes automatizados em CI:** incluindo localização, descrição completa, ATS, fontes públicas, cache, bloqueios, feedback, mapas de currículo e migração do banco.

## 📁 Estrutura do repositório

jobradar/
├── README.md
├── requirements.txt
├── main.py ← motor único: um ciclo de busca por perfil
├── core/perfis.py ← Dados/BI e CX (dados, não lógica duplicada)
├── core/perfil_candidato.py ← experiências e skills comprovadas por nicho
├── core/match.py ← cálculo explicável do match estimado
├── core/descricao_vaga.py ← Playwright compartilhado + fallback OCR seguro
├── core/config.py / core/config_cx.py ← cargos e termos de cada nicho
├── core/job.py ← Job, filtro e integração do match
├── relatorio_precisao.py ← aprovadas/notificadas por fonte e por semana
├── database/
│ └── database.py ← SQLite: dedup, fila de digest, metadados
├── notifier/
│ └── telegram.py ← notificação individual, digest, botão 👍/👎
├── scrapers/ ← um módulo por fonte (LinkedIn, Gupy, Jobicy, Remotive...)
├── utils/
│ └── filtro.py
├── tests/ ← 359 casos, roda em CI a cada push
├── data/
│ └── jobs.db ← banco versionado (histórico de dedup)
└── .github/workflows/
├── jobradar.yml ← cron de produção (a cada 3h)
└── testes.yml ← CI

## 💻 Como ativar no GitHub Actions

Depois que esta versão estiver no seu repositório, configure somente
`TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` seguindo o
[guia do Telegram](CONFIGURAR_TELEGRAM.md). O workflow `jobradar.yml` instala
automaticamente Python, Chromium, Tesseract e os idiomas português/inglês,
e executa os dois perfis a cada três horas.

## 🧪 Testes

```bash
pytest tests/ -v
```

Casos parametrizados cobrem filtros, leitura da descrição, ranking, migração do banco, callback do Telegram e relatório de precisão — todos rodando automaticamente a cada push via GitHub Actions.

---

<div align="center">

*Case de portfólio em automação de dados — Python, Playwright, SQLite, GitHub Actions e engenharia de filtro sem ML.*

</div>
