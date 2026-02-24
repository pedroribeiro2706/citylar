import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import base64
from streamlit_mic_recorder import mic_recorder
import uuid

# --- CONFIGURAÇÃO DE SESSÃO E ESTADO ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "last_processed_input_id" not in st.session_state:
    st.session_state.last_processed_input_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Citylar Executivo", layout="wide", initial_sidebar_state="expanded")

# --- IMPORTAÇÃO DE ÍCONES ---
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">', unsafe_allow_html=True)

# --- CSS DEFINITIVO ---
st.markdown("""
    <style>
    /* 1. SIDEBAR */
    section[data-testid="stSidebar"] {
        width: 250px !important;
    }

    /* 2. CONTRASTE DA CAIXA DE CHAT */
    /* Cria um fundo escuro diferenciado para o container de mensagens */
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > div {
        border: 1px solid #4b646f !important;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.2);
    }

    /* 3. BOTÃO DE GRAVAÇÃO (nativo do Streamlit, sem iframe) */
    [data-testid="stAudioInput"] button {
        border-radius: 8px !important;
    }

    [data-testid="stAudioInput"] button:hover {
        background-color: rgb(100 0 25) !important;
        border-color: rgb(100 0 25) !important;
        color: #ffffff !important;
    }

    /* 4. MENSAGENS TRANSPARENTES */
    [data-testid="stSidebar"] .stChatMessage {
        background-color: transparent !important;
    }

    /* 5. OUTROS ESTILOS */
    .nav-btn {
        display: block; padding: 12px 15px; background-color: transparent;
        color: #b8c7ce !important; text-decoration: none !important;
        border-left: 3px solid transparent; 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; 
        transition: all 0.3s ease;
    }
    .nav-btn:hover {
        background-color: #1e282c; color: #ffffff !important;
        border-left: 3px solid transparent; text-decoration: none !important;
    }
    .nav-icon { margin-right: 10px; width: 20px; text-align: center; display: inline-block; }
    
    .agent-title {
        font-size: 18px; font-weight: bold; font-family: 'Source Sans Pro', sans-serif;
        margin-bottom: 5px; display: block;
    }
    
    .sidebar-divider { height: 1px; background-color: #4b646f; margin: 20px 0; opacity: 0.5; }
    
    .main-header {
        border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 20px;
        display: flex; justify-content: space-between; align-items: center;
    }
    
    /* Sidebar: remove espaço do header mas mantém botão de collapse */
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
        color: #b8c7ce !important;
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
    
    .block-container { padding-top: 1.5rem; }
    .stAudio { display: none; }

    header { visibility: hidden !important; height: 0 !important; min-height: 0 !important; overflow: visible !important; }
    .block-container > [data-testid="stVerticalBlock"] { gap: 0 !important; }

    /* Fullscreen button nos gráficos: sempre visível (não só no hover) */
    [data-testid="StyledFullScreenButton"] {
        opacity: 1 !important;
        visibility: visible !important;
        display: flex !important;
    }

    [data-testid="stChatMessageAvatarUser"] {
    background: linear-gradient(135deg, #800020, #660019);
    color: white !important;
    border-radius: 10px !important;
    }

    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: rgba(255,255,255,0.08);
        color: white !important;
        border-radius: 10px !important;
    }

    </style>
""", unsafe_allow_html=True)

# 2. URLs DO n8n
BASE_URL = "https://workflows-mvp.clockdesign.com.br/webhook"
URL_DADOS = f"{BASE_URL}/dados-dashboard"
URL_CHAT = f"{BASE_URL}/chat"

# 3. SIDEBAR
with open("logo-citylar.png", "rb") as _f:
    _LOGO_B64 = base64.b64encode(_f.read()).decode()

with st.sidebar:
    # LOGO
    st.markdown(f"""
        <div style="height: 180px; margin: -1rem -1rem 10px -1rem; overflow: hidden;">
            <img src="data:image/png;base64,{_LOGO_B64}" style="width: 100%; height: 100%; object-fit: cover; display: block;">
        </div>
    """, unsafe_allow_html=True)
    
    # MENU
    st.markdown("""
        <a class="nav-btn" href="#"><i class="nav-icon fa-solid fa-chart-line"></i> Dashboard</a>
        <a class="nav-btn" href="#"><i class="nav-icon fa-solid fa-chart-pie"></i> Análise de Vendas</a>
        <a class="nav-btn" href="#"><i class="nav-icon fa-solid fa-gear"></i> Configurações</a>
        <a class="nav-btn" href="#"><i class="nav-icon fa-solid fa-file-lines"></i> Relatórios</a>
    """, unsafe_allow_html=True)
    
    # DIVISÓRIA
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    # TOGGLE
    uploaded_file = st.file_uploader("Upload planilha", type=["xlsx","csv"])

    if uploaded_file:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type
            )
        }

        res = requests.post("https://workflows-mvp.clockdesign.com.br/webhook/citylar/upload", files=files)
        st.write(res.text)

    # --- ÁREA DO AGENTE ---
    st.markdown('<div class="agent-title">Consultoria IA</div>', unsafe_allow_html=True)
    
    # CAIXA DE CHAT (Container com borda que recebe o fundo #2c3b41 via CSS)
    chat_container = st.container(height=300, border=True)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): 
                st.markdown(m["content"])

    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

    # INPUT DE CHAT (Volta o st.chat_input original com botão enviar)
    prompt = st.chat_input("Digite sua pergunta...")
    
    # BOTÃO DE ÁUDIO (nativo, estilizado por CSS sem iframe)
    audio_input = st.audio_input("Enviar Áudio", key="audio_sidebar") 
    
    # TOGGLE (De volta ao topo da área de IA)
    voz_ativa = st.toggle("Modo Voz", value=True)

    

# 4. LÓGICA DE PROCESSAMENTO (VERSÃO ESTÁVEL)

user_input = None
current_input_id = None

# --- TEXTO ---
if prompt:
    current_input_id = f"txt_{hash(prompt)}"

    if current_input_id != st.session_state.last_processed_input_id:
        user_input = prompt
        st.session_state.last_processed_input_id = current_input_id


# --- ÁUDIO ---
elif audio_input is not None:

    # Armazena o áudio apenas uma vez
    if "audio_buffer" not in st.session_state:
        st.session_state.audio_buffer = audio_input.getvalue()

    audio_bytes = st.session_state.audio_buffer
    current_input_id = f"aud_{hash(audio_bytes)}"

    if current_input_id != st.session_state.last_processed_input_id:
        user_input = "🎤 [Enviando áudio...]"
        st.session_state.last_processed_input_id = current_input_id


# --- ENVIO ---
if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

    with chat_container.chat_message("user"):
        st.markdown(user_input)

    with chat_container.chat_message("assistant"):

        try:
            if "🎤" in user_input:

                files = {"audio": ("audio.wav", st.session_state.audio_buffer, "audio/wav")}
                res = requests.post(
                    URL_CHAT,
                    files=files,
                    data={"sessionId": st.session_state.session_id}
                )

            else:

                res = requests.post(
                    URL_CHAT,
                    json={"chatInput": user_input, "sessionId": st.session_state.session_id}
                )

            if res.status_code == 200:

                data = res.json()
                ans = data.get("output", "Sem resposta.")

                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})

                # Limpa buffer após uso
                if "audio_buffer" in st.session_state:
                    del st.session_state.audio_buffer

                # Evita rerun agressivo imediato
                if any(x in ans.lower() for x in ["sucesso", "atualizado", "alterado"]):
                    st.cache_data.clear()

                if data.get("audio") and voz_ativa:
                    st.audio(
                        base64.b64decode(data.get("audio")),
                        format='audio/mp3',
                        autoplay=True
                    )

            else:
                st.error(f"Erro n8n: {res.status_code}")

        except Exception as e:
            st.error(f"Erro: {e}")

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
    color = 'green' if '▲' in val else 'red' if '▼' in val else 'gray'
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
    st.markdown("""
        <div class="main-header">
            <h2 style="margin:0; font-weight: 400; color: #fff;">Dashboard Executivo</h2>
            <div style="font-size: 14px; color: #777;">Visão consolidada de performance</div>
        </div>
    """, unsafe_allow_html=True)

    from datetime import datetime

    def periodo_para_texto(periodo: pd.Period) -> str:
        meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
        return f"{meses[periodo.month - 1]} de {periodo.year}"

    periodo_atual = pd.Period(datetime.now(), freq="M")
    periodo_default = periodo_atual if periodo_atual in periodos_disponiveis else periodos_disponiveis[0]

    @st.fragment
    def renderizar_visualizacoes(df):
        periodo_selecionado = st.selectbox(
            "Mês",
            periodos_disponiveis,
            index=periodos_disponiveis.index(periodo_default),
            key="periodo_resultado"
        )

        st.subheader(f"Resultado {periodo_para_texto(periodo_selecionado)}")
        
        df_atual = df[df['Periodo'] == periodo_selecionado ].copy()
        periodo_anterior = periodos_disponiveis[1] if len(periodos_disponiveis) > 1 else None
        
        recordes = df.groupby('Nome')['Ticket Médio'].max().rename('Recorde Histórico')
        mes_anterior = periodo_selecionado - 1
        val_ant = df[df['Periodo'] == mes_anterior].set_index('Nome')['Ticket Médio'] if mes_anterior in periodos_disponiveis else pd.Series()
        
        df_atual = df_atual.merge(recordes, on='Nome', how='left').fillna(0)
        df_atual['Evolução %'] = df_atual.apply(lambda r: ((r['Ticket Médio'] - val_ant.get(r['Nome'], 0)) / val_ant.get(r['Nome'], 1) * 100) if r['Nome'] in val_ant and val_ant.get(r['Nome'], 0) > 0 else 0, axis=1)
        
        df_vis = df_atual[['Nome', 'Ticket Médio', 'Recorde Histórico', 'Evolução %']].copy()
        df_vis['Evolução %'] = df_vis['Evolução %'].apply(formatar_evolucao)
        
        st.dataframe(
            df_vis.style.map(color_evolucao, subset=['Evolução %']), 
            use_container_width=True, 
            hide_index=True, 
            height=300,
            column_config={
                "Ticket Médio": st.column_config.NumberColumn(format="R$ %.2f"),
                "Recorde Histórico": st.column_config.NumberColumn(format="R$ %.2f")
            }
        )

        st.divider()
        
        # Gráficos
        g1, g2, g3 = st.columns(3)
        with g1:
            s_mes = st.selectbox("Ranking do Mês", periodos_disponiveis, key="f_mes")
            df_g1 = df[df['Periodo'] == s_mes].sort_values('Ticket Médio')
            st.plotly_chart(px.bar(df_g1, x='Ticket Médio', y=df_g1['Nome'].apply(truncar_nome), orientation='h', color_discrete_sequence=['#800020']).update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0,r=0,t=0,b=0), height=450), use_container_width=True, config=PLOTLY_CONFIG)
        
        with g2:
            s_ano = st.selectbox("Recordes por Ano", anos_disponiveis, key="f_ano")
            df_a = df if s_ano == "Todos" else df[df['Ano'] == int(s_ano)]
            df_g2 = df_a.groupby('Nome')['Ticket Médio'].max().reset_index().sort_values('Ticket Médio')
            st.plotly_chart(px.bar(df_g2, x='Ticket Médio', y=df_g2['Nome'].apply(truncar_nome), orientation='h', color_discrete_sequence=['#800020']).update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0,r=0,t=0,b=0), height=450), use_container_width=True, config=PLOTLY_CONFIG)
            
        with g3:
            s_col = st.selectbox("Evolução Individual", colaboradores, key="f_col")
            df_c = df[df['Nome'] == s_col].sort_values('Data').tail(12)
            st.plotly_chart(px.bar(df_c, x=df_c['Data'].dt.strftime('%b/%y'), y='Ticket Médio', color_discrete_sequence=['#800020']).update_layout(xaxis_title="", yaxis_title="", margin=dict(l=0,r=0,t=0,b=0), height=450), use_container_width=True, config=PLOTLY_CONFIG)

    renderizar_visualizacoes(df_raw)

    st.markdown('<div style="text-align: center; margin-top: 50px; color: #999; font-size: 12px;">© 2024 Citylar Intelligence • AdminLTE Theme</div>', unsafe_allow_html=True)