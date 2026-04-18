import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import base64
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Citylar Executivo", layout="wide", initial_sidebar_state="expanded")

# --- IMPORTAÇÃO DE ÍCONES ---
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">', unsafe_allow_html=True)

# --- CSS LIGHT MODE ---
st.markdown("""
    <style>
    /* 1. SIDEBAR */
    section[data-testid="stSidebar"] {
        width: 250px !important;
        background-color: #1f1f1f !important;
    }
    [data-testid="stSidebar"] * {
        color: #b8c7ce !important;
    }

    /* 2. BOTÕES DE NAVEGAÇÃO */
    .nav-btn {
        display: block; padding: 12px 15px; background-color: transparent;
        color: #b8c7ce !important; text-decoration: none !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px;
        transition: all 0.3s ease; margin: 7px 8px; border-radius: 6px;
    }
    .nav-btn:hover {
        background-color: #1e282c; color: #ffffff !important;
        text-decoration: none !important;
    }
    .nav-btn.active {
        background-color: #1e282c; color: #ffffff !important;
    }
    .nav-icon { margin-right: 10px; width: 20px; text-align: center; display: inline-block; }

    /* 3. KPI CARDS */
    .kpi-card {
        background: #ffffff; border-radius: 8px; padding: 16px 20px;
        text-align: center; border: 1px solid #e0e0e0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .kpi-label { font-size: 1rem; color: #666666; margin-bottom: 6px; text-align: center; }
    .kpi-value { font-size: 26px; font-weight: bold; color: #1a1a1a; }

    /* 4. SELECTBOX LABEL E CHART TITLE */
    [data-testid="stSelectbox"] label,
    .chart-title {
        font-size: 1.5rem !important;
        color: #444444 !important;
    }

    /* 5. HEADER PRINCIPAL */
    .main-header {
        border-bottom: 1px solid #e0e0e0; padding-bottom: 15px; margin-bottom: 20px;
        display: flex; justify-content: space-between; align-items: center;
    }

    /* 6. SIDEBAR HEADER (remove espaço, mantém botão collapse) */
    [data-testid="stSidebarHeader"] {
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        overflow: visible !important;
    }
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        z-index: 9999 !important;
        display: flex !important;
    }
    [data-testid="stSidebarCollapseButton"] svg { fill: #b8c7ce !important; }
    [data-testid="stExpandSidebarButton"] {
        visibility: visible !important;
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        z-index: 9999 !important;
        display: flex !important;
    }
    [data-testid="stExpandSidebarButton"] svg { fill: #b8c7ce !important; }

    /* 7. ESPAÇAMENTO */
    .block-container { padding-top: 3.5rem; padding-bottom: 50px; }

    /* 8. FOOTER */
    .fixed-footer {
        position: fixed; bottom: 0; left: 0; right: 0; height: 50px;
        background: #f5f6fa; border-top: 2px solid #e0e0e0;
        display: flex; align-items: center; justify-content: right; padding: 0 5.75rem;
        font-size: 16px; color: #555555; z-index: 1000;
    }

    /* 9. OCULTAR HEADER DO STREAMLIT */
    header { visibility: hidden !important; height: 0 !important; min-height: 0 !important; overflow: visible !important; }
    .block-container > [data-testid="stVerticalBlock"] { gap: 0 !important; }

    /* 10. FULLSCREEN NOS GRÁFICOS */
    [data-testid="StyledFullScreenButton"] {
        opacity: 1 !important;
        visibility: visible !important;
        display: flex !important;
    }

    </style>
""", unsafe_allow_html=True)

# 2. URL DOS DADOS
URL_DADOS = "https://workflows-mvp.clockdesign.com.br/webhook/dados-dashboard"

# 3. PÁGINA ATUAL (via query param)
current_page = st.query_params.get("page", "pontuacao")

# 4. SIDEBAR
with open("logo-citylar.png", "rb") as _f:
    _LOGO_B64 = base64.b64encode(_f.read()).decode()

with st.sidebar:
    # LOGO
    st.markdown(f"""
        <div style="height: 180px; margin: 15px -1rem 20px -1rem; overflow: hidden;">
            <img src="data:image/png;base64,{_LOGO_B64}" style="width: 100%; height: 100%; object-fit: cover; display: block;">
        </div>
    """, unsafe_allow_html=True)

    # MENU
    st.markdown(f"""
        <a class="nav-btn {'active' if current_page == 'pontuacao' else ''}" href="?page=pontuacao" target="_self"><i class="nav-icon fa-solid fa-trophy"></i> Pontuação</a>
        <a class="nav-btn {'active' if current_page == 'dashboard' else ''}" href="?page=dashboard" target="_self"><i class="nav-icon fa-solid fa-chart-line"></i> Data Viz</a>
    """, unsafe_allow_html=True)

# 5. CARREGAMENTO E DADOS
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        response = requests.get(URL_DADOS, timeout=10)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            df['Ticket Médio'] = pd.to_numeric(df['Ticket Médio'].replace('[R$,]', '', regex=True), errors='coerce')
            df['Data'] = pd.to_datetime(df['Data'], format='mixed', dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            return df
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
    return None

def formatar_evolucao(valor):
    if valor > 0: return f"+{valor:.1f}% ▲"
    elif valor < 0: return f"{valor:.1f}% ▼"
    return "0.0%"

def truncar_nome(nome):
    return (nome[:18] + '..') if len(nome) > 18 else nome

def color_evolucao(val):
    color = '#11e00d' if '▲' in val else 'red' if '▼' in val else 'gray'
    return f'color: {color}; font-weight: bold'

PLOTLY_CONFIG = {'displayModeBar': False}

# 6. LAYOUT PRINCIPAL
df_raw = carregar_dados()

if df_raw is not None:
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    df_raw['Ano'] = df_raw['Data'].dt.year
    df_raw['Periodo'] = df_raw['Data'].dt.to_period('M')
    periodos_disponiveis = sorted(df_raw['Periodo'].unique(), reverse=True)
    anos_disponiveis = ["Todos"] + sorted(df_raw['Ano'].unique().astype(str).tolist(), reverse=True)
    colaboradores = sorted(df_raw['Nome'].unique())

    # HEADER PRINCIPAL
    _page_titles = {
        "pontuacao": ("Pontuação", "Ranking e evolução por período"),
        "dashboard": ("Storytelling", "Visão consolidada de performance"),
    }
    _title, _subtitle = _page_titles.get(current_page, ("Citylar", ""))
    st.markdown(f"""
        <div class="main-header">
            <h2 style="margin:0; font-weight: 400; color: #1a1a1a;">{_title}</h2>
            <div style="font-size: 14px; color: #888888;">{_subtitle}</div>
        </div>
    """, unsafe_allow_html=True)

    def periodo_para_texto(periodo: pd.Period) -> str:
        meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
        return f"{meses[periodo.month - 1]} de {periodo.year}"

    periodo_atual = pd.Period(datetime.now(), freq="M")
    periodo_default = periodo_atual if periodo_atual in periodos_disponiveis else periodos_disponiveis[0]

    @st.fragment
    def renderizar_pontuacao(df):
        periodo_selecionado = st.selectbox(
            "Mês",
            periodos_disponiveis,
            index=periodos_disponiveis.index(periodo_default),
            key="periodo_resultado"
        )
        st.subheader(f"Resultado {periodo_para_texto(periodo_selecionado)}")

        recordes = df.groupby('Nome')['Ticket Médio'].max().rename('Recorde Histórico')
        df_atual = df[df['Periodo'] == periodo_selecionado].copy()
        df_atual = df_atual.merge(recordes, on='Nome', how='left').fillna(0)
        df_atual['Evolução %'] = df_atual.apply(lambda r: ((r['Ticket Médio'] - r['Recorde Histórico']) / r['Recorde Histórico'] * 100) if r['Recorde Histórico'] > 0 else 0, axis=1)

        df_vis = df_atual[['Nome', 'Ticket Médio', 'Recorde Histórico', 'Evolução %']].copy()
        df_vis['Evolução %'] = df_vis['Evolução %'].apply(formatar_evolucao)

        table_height = len(df_vis) * 36 + 42
        st.dataframe(
            df_vis.style.map(color_evolucao, subset=['Evolução %']),
            use_container_width=True,
            hide_index=True,
            height=table_height,
            column_config={
                "Ticket Médio": st.column_config.NumberColumn(format="R$ %.2f"),
                "Recorde Histórico": st.column_config.NumberColumn(format="R$ %.2f")
            }
        )

    @st.fragment
    def renderizar_dashboard(df):
        st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

        # --- KPI CARDS ---
        periodo_kpi = pd.Period(datetime.now(), freq="M")
        df_mes_kpi = df[df['Periodo'] == periodo_kpi]
        media_mes = df_mes_kpi['Ticket Médio'].mean() if not df_mes_kpi.empty else 0
        ultimos_12 = sorted(df['Periodo'].unique(), reverse=True)[:12]
        media_12m = df[df['Periodo'].isin(ultimos_12)]['Ticket Médio'].mean()
        maior_ticket = df['Ticket Médio'].max()
        mesmo_mes_ano_passado = periodo_kpi - 12
        df_mesmo_mes_ap = df[df['Periodo'] == mesmo_mes_ano_passado]
        media_mesmo_mes_ap = df_mesmo_mes_ap['Ticket Médio'].mean() if not df_mesmo_mes_ap.empty else None

        c1, c2, c3, c4 = st.columns(4)
        meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        label_ap = f"Média de {meses[mesmo_mes_ano_passado.month - 1]} {mesmo_mes_ano_passado.year}"
        valor_ap = f'R$ {media_mesmo_mes_ap:,.2f}' if media_mesmo_mes_ap is not None else 'Não há dados'

        with c1:
            st.markdown('<div class="kpi-label">Média do Mês Atual</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">R$ {media_mes:,.2f}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="kpi-label">{label_ap}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">{valor_ap}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="kpi-label">Média dos últimos 12 Meses</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">R$ {media_12m:,.2f}</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown('<div class="kpi-label">Maior Ticket Médio</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">R$ {maior_ticket:,.2f}</div></div>', unsafe_allow_html=True)

        st.markdown('<div style="height:40px"></div>', unsafe_allow_html=True)

        # --- LINHA 1 ---
        g1, g2 = st.columns(2)
        with g1:
            s_mes = st.selectbox("Ranking do Mês", periodos_disponiveis, key="f_mes")
            df_g1 = df[df['Periodo'] == s_mes].sort_values('Ticket Médio')
            st.plotly_chart(px.bar(df_g1, x='Ticket Médio', y=df_g1['Nome'].apply(truncar_nome), orientation='h', color_discrete_sequence=['#800020']).update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0,r=0,t=0,b=0), height=450), use_container_width=True, config=PLOTLY_CONFIG)

        with g2:
            s_ano = st.selectbox("Recordes por Ano", anos_disponiveis, key="f_ano")
            df_a = df if s_ano == "Todos" else df[df['Ano'] == int(s_ano)]
            df_g2 = df_a.groupby('Nome')['Ticket Médio'].max().reset_index().sort_values('Ticket Médio')
            st.plotly_chart(px.bar(df_g2, x='Ticket Médio', y=df_g2['Nome'].apply(truncar_nome), orientation='h', color_discrete_sequence=['#800020']).update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0,r=0,t=0,b=0), height=450), use_container_width=True, config=PLOTLY_CONFIG)

        st.markdown('<div style="height:30px"></div>', unsafe_allow_html=True)

        # --- LINHA 2 ---
        g3, g4 = st.columns(2)
        with g3:
            s_col = st.selectbox("Evolução Individual", colaboradores, key="f_col")
            df_c = df[df['Nome'] == s_col].sort_values('Data').tail(12)
            st.plotly_chart(px.bar(df_c, x=df_c['Data'].dt.strftime('%b/%y'), y='Ticket Médio', color_discrete_sequence=['#800020']).update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0,r=0,t=0,b=0), height=450), use_container_width=True, config=PLOTLY_CONFIG)

        with g4:
            st.markdown('<div class="chart-title">Evolução da Média Geral</div>', unsafe_allow_html=True)
            st.markdown('<div style="height:40px"></div>', unsafe_allow_html=True)
            df_avg = df.groupby('Periodo')['Ticket Médio'].mean().reset_index().sort_values('Periodo')
            df_avg['Mes'] = df_avg['Periodo'].dt.strftime('%b/%y')
            st.plotly_chart(px.bar(df_avg, x='Mes', y='Ticket Médio', color_discrete_sequence=['#800020']).update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0,r=0,t=0,b=0), height=450), use_container_width=True, config=PLOTLY_CONFIG)

    if current_page == "pontuacao":
        renderizar_pontuacao(df_raw)
    elif current_page == "dashboard":
        renderizar_dashboard(df_raw)

    st.markdown('<div class="fixed-footer">© 2026 Jogo do Trabalho Intelligence • Citylar Theme</div>', unsafe_allow_html=True)
