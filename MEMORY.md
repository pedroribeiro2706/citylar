# MEMORY.md — Histórico do Projeto Citylar

Arquivo de referência histórica. Para atualizações recentes, ver `log.md`.

---

## Visão Geral do Projeto

**Citylar** é um dashboard executivo de vendas com chatbot consultor de IA integrado, construído com Streamlit. Acompanha o desempenho de "Ticket Médio" dos colaboradores, exibindo rankings, recordes históricos e tendências de evolução. O consultor IA conecta-se a workflows n8n que consultam dados do Google Sheets.

**Stack:** Streamlit (`app.py`) + n8n + Google Sheets  
**Repositório GitHub:** `pedroribeiro2706/citylar`  
**Deploy:** Railway (dois projetos — dark e light)

---

## Arquitetura

### app.py (dark mode, com IA)
- Aplicação Streamlit single-file
- Sidebar: menu de navegação + painel de chat IA + upload de planilha + gravação de áudio
- Dados carregados via `carregar_dados()` com `@st.cache_data(ttl=60)`
- Dois fragments: `renderizar_pontuacao` e `renderizar_dashboard`
- Página atual via query param `?page=pontuacao` ou `?page=dashboard`
- KPI cards (ordem): Média Mês Atual → Média Mesmo Mês Ano Passado → Média 12 Meses → Maior Ticket

### app_light.py (light mode, sem IA)
- Versão sem chat, sem upload, sem áudio, sem toggle de voz
- Sidebar: fundo dark `#1f1f1f`, menu apenas Pontuação e Data Viz
- Área principal: light mode (`#f5f6fa`)
- Mesma fonte de dados, mesmas visualizações

### Tema
- Dark: background `#1f1f1f`, maroon `#800020`, texto branco
- Definido em `.streamlit/config.toml`
- Charts: Plotly com maroon como cor primária, sem mode bar

---

## Deploy — Railway

| Projeto | URL | Arquivo | Modo |
|---|---|---|---|
| `sublime-reflection` | `web-production-0297f.up.railway.app` | `app.py` via `Procfile` | Dark + IA |
| `citylar-production` | `citylar-production.up.railway.app` | `app_light.py` via start command customizado | Light sem IA |

`git push` para `main` atualiza ambos automaticamente.

**Teste local do light mode:**
```bash
streamlit run app_light.py --theme.base=light --theme.primaryColor=#800020 --theme.backgroundColor=#f5f6fa --theme.secondaryBackgroundColor=#ffffff --theme.textColor=#1a1a1a
```

---

## n8n

- **Workflow principal:** "Citylar - Tool de Edição" (ID: `diVS63G6fFpcahVx`)
- **Arquivo local:** `n8n-workflows/Citylar - Tool de Edição - 25fev2026.json`
- **Base URL webhooks:** `https://workflows-mvp.clockdesign.com.br/webhook`
  - `/dados-dashboard` — GET, dados do dashboard
  - `/chat` — POST, agente IA
  - `/citylar/upload` — POST, upload de planilha (.xlsx ou .csv)

### Nodes relevantes (workflow de upload)
- Webhook: `43175e72-5954-4677-a9c3-5bfe482c2ff2`
- IF "Detecta Tipo de Arquivo": `if-detect-type-001` — detecta `.xlsx` via mimeType contains "spreadsheet"
- Extract from File (CSV): `fb023d43-bee6-41c9-8ce6-9743262bbf01` — delimiter `;`
- Extract from File (XLSX): `extract-xlsx-001`
- Edit Fields: `3c10d20a-3fc0-4dfd-b2be-5f06ed2b85f1`

---

## Convenções

- Idioma: português BR em todo o código (variáveis, funções, UI)
- Moeda: `R$ X,XX` (Real brasileiro)
- Datas: `dayfirst=True` (formato DD/MM/YY)
- n8n workflow JSON files versionados por data (ex: `Citylar - 14fev2026.json`)
- Commit + push após cada alteração

---

## Problemas Resolvidos / Soluções

### Recorde Histórico incluía o mês atual (2026-04-20)
- **Correção:** Filtrar `df['Periodo'] < periodo_selecionado` antes do `.max()`
- `Periodo` é `pandas.Period` gerado via `df['Data'].dt.to_period('M')` — comparação `<` funciona nativamente
- Aplicado em `app.py` e `app_light.py`

### Excel serializa datas como inteiros
- Ex: `46109` em vez de `30/04/2026`
- Usar `$json.Periodo` (já formatado) em vez de `$json.Data` quando não contém "/"

### Expressões n8n com texto literal + expressão
- Precisam do prefixo `=` — auto-fix disponível via `n8n_autofix_workflow`

### addConnection no MCP
- Usa 4 parâmetros separados: `source`, `target`, `sourcePort`, `targetPort`
- IF nodes requerem parâmetro adicional `branch: "true"` ou `branch: "false"`

---

## Histórico de Sessões

| Data | Descrição |
|---|---|
| 2026-04-20 | Correção do Recorde Histórico + criação do sistema de registro: skill /registrar, Stop hook e arquivos log.md/MEMORY.md |
| 2026-02-25 | Workflow n8n "Citylar - Tool de Edição" — upload de planilha XLSX/CSV |
| 2026-02-14 | Versão inicial do workflow n8n |
| anterior | Criação do app.py (dark mode com IA) e app_light.py (light mode sem IA) |
