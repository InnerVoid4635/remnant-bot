"""
REMNANT - Security Monitor
Dashboard Administrativo para Bot Discord
Tema: Dark Industrial/FNAF

Para rodar: streamlit run painel.py
Instalar dependências: pip install streamlit plotly pandas psutil
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import sqlite3
import psutil
from collections import deque
import time
import os
import re

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="REMNANT - Security Monitor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# HISTÓRICO DE CPU/RAM (deque persistido via session_state)
# =============================================================================
HISTORY_LEN = 30

if "cpu_history" not in st.session_state:
    st.session_state.cpu_history = deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN)
if "ram_history" not in st.session_state:
    st.session_state.ram_history = deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN)

def update_resource_history():
    """Atualiza as deques de CPU e RAM com valores reais do psutil."""
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    st.session_state.cpu_history.append(cpu)
    st.session_state.ram_history.append(ram)
    return cpu, ram

# =============================================================================
# CAMINHO DO BANCO DE DADOS
# Ajuste o caminho abaixo para onde o bot.db realmente está,
# ou defina a variável de ambiente REMNANT_DB_PATH.
# =============================================================================
DB_PATH = os.environ.get("REMNANT_DB_PATH", "bot.db")

def get_db_connection():
    """
    Retorna uma conexão SQLite em modo read-only para não bloquear o bot.
    Fallback para memória vazia se o ficheiro não existir ainda.
    """
    uri = f"file:{DB_PATH}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

# =============================================================================
# FUNÇÕES DE DADOS REAIS
# Todas baseadas nas tabelas reais do bot.py: `logs` e `chat_logs`
# Esquema de `logs`: id, timestamp, level, logger, message
# =============================================================================

@st.cache_data(ttl=30)
def get_member_count() -> int:
    """
    Conta usuários únicos que já executaram comandos.
    Extrai o nome de usuário da coluna `message` nos logs de CMD.
    Formato da mensagem: "[GuildName] #channel | UserName usou: /cmd"
    """
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                "SELECT message FROM logs WHERE logger = 'CMD'"
            )
            rows = cur.fetchall()

        user_ids = set()
        for row in rows:
            msg = row[0] or ""
            # Tenta extrair ID numérico entre parênteses: "Nome (123456789) usou:"
            match = re.search(r'\((\d{10,20})\)', msg)
            if match:
                user_ids.add(match.group(1))
            else:
                # Fallback: usa o trecho entre "| " e " usou:"
                m_user = re.search(r'\|\s*(.+?)\s+usou:', msg)
                if m_user:
                    user_ids.add(m_user.group(1).strip())

        return len(user_ids) if user_ids else 0
    except Exception:
        return 0

@st.cache_data(ttl=10)
def get_recent_commands(limit: int = 50) -> pd.DataFrame:
    """
    Retorna os últimos comandos executados a partir da tabela `logs`.
    Filtra por logger = 'CMD'.
    Formato da mensagem gravada pelo verbose.py:
        "[GuildName] #channel | UserName usou: /comando"
    """
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query(
                """
                SELECT timestamp AS horário,
                       message   AS detalhe
                FROM   logs
                WHERE  logger = 'CMD'
                ORDER  BY id DESC
                LIMIT  ?
                """,
                conn,
                params=(limit,)
            )

        if df.empty:
            return pd.DataFrame(columns=["horário", "servidor", "usuario", "comando"])

        # Parseia a mensagem: "[Guild] #channel | User usou: /cmd"
        def parse_cmd(row):
            msg = row["detalhe"] or ""
            servidor, usuario, comando = "—", "—", "—"

            m_guild = re.match(r'\[([^\]]+)\]', msg)
            if m_guild:
                servidor = m_guild.group(1)

            if "usou:" in msg:
                comando = msg.split("usou:")[-1].strip()

            m_user = re.search(r'\|\s*(.+?)\s+usou:', msg)
            if m_user:
                usuario = m_user.group(1)

            return pd.Series({
                "horário":  row["horário"],
                "servidor": servidor,
                "usuario":  usuario,
                "comando":  comando,
            })

        return df.apply(parse_cmd, axis=1)[["horário", "servidor", "usuario", "comando"]]

    except Exception:
        return pd.DataFrame(columns=["horário", "servidor", "usuario", "comando"])

@st.cache_data(ttl=10)
def get_log_entries(limit: int = 50, log_type_filter: str = "Todos") -> list:
    """
    Lê entradas de log da tabela `logs`.
    Colunas: id, timestamp, level, logger, message
    """
    css_map = {
        "DEBUG":    "log-info",
        "INFO":     "log-success",
        "WARNING":  "log-warning",
        "ERROR":    "log-error",
        "CRITICAL": "log-error",
    }
    try:
        with get_db_connection() as conn:
            if log_type_filter == "Todos":
                df = pd.read_sql_query(
                    "SELECT level, logger, message, timestamp FROM logs ORDER BY id DESC LIMIT ?",
                    conn, params=(limit,)
                )
            else:
                df = pd.read_sql_query(
                    "SELECT level, logger, message, timestamp FROM logs WHERE level = ? ORDER BY id DESC LIMIT ?",
                    conn, params=(log_type_filter, limit)
                )

        entries = []
        for _, row in df.iterrows():
            lvl = str(row.get("level",   "INFO")).upper()
            msg = str(row.get("message", ""))
            ts  = str(row.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            entries.append((lvl, msg, css_map.get(lvl, "log-info"), ts))
        return entries

    except Exception:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [
            ("INFO",    "Aguardando conexão com bot.db...", "log-info",    ts),
            ("WARNING", "Verifica o caminho do banco na sidebar.", "log-warning", ts),
        ]

@st.cache_data(ttl=60)
def get_cog_stats() -> dict:
    """
    Conta cogs carregadas a partir dos logs do SYSTEM.
    O bot.py grava: "Módulo carregado: cogs.xxx"
    """
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                "SELECT COUNT(*) FROM logs WHERE logger = 'SYSTEM' AND message LIKE '%Módulo carregado:%'"
            )
            total = cur.fetchone()[0] or 0

        with get_db_connection() as conn:
            cur = conn.execute(
                "SELECT COUNT(*) FROM logs WHERE logger = 'ERROR' AND message LIKE '%bot.setup_hook.cog%'"
            )
            erros = cur.fetchone()[0] or 0

        ativas = max(0, total - erros)
        return {"ativas": ativas, "total": total}
    except Exception:
        return {"ativas": 0, "total": 0}

def get_system_stats() -> dict:
    """Retorna CPU, RAM e uptime reais via psutil."""
    cpu, ram = update_resource_history()

    boot_time   = psutil.boot_time()
    uptime_secs = time.time() - boot_time
    days        = int(uptime_secs // 86400)
    hours       = int((uptime_secs % 86400) // 3600)
    minutes     = int((uptime_secs % 3600) // 60)

    return {
        "cpu":    cpu,
        "ram":    ram,
        "uptime": f"{days}d {hours}h {minutes}m",
    }

# =============================================================================
# CSS CUSTOMIZADO - TEMA FNAF INDUSTRIAL (preservado integralmente)
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    .stApp { background-color: #0a0a0a !important; }

    [data-testid="stSidebar"] {
        background-color: #0d0d0d !important;
        border-right: 1px solid #1a1a1a !important;
    }
    [data-testid="stSidebar"] .stMarkdown { color: #a3a3a3 !important; }

    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        color: #FFD700 !important;
    }

    p, span, label, .stMarkdown {
        color: #d4d4d4 !important;
        font-family: 'Inter', sans-serif !important;
    }

    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        color: #FFD700 !important;
        font-size: 2rem !important;
    }

    [data-testid="stMetricLabel"] {
        color: #a3a3a3 !important;
        font-family: 'Inter', sans-serif !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em !important;
    }

    .terminal-container {
        background-color: #0d0d0d;
        border: 1px solid #262626;
        border-radius: 8px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        max-height: 400px;
        overflow-y: auto;
    }

    .terminal-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #262626;
    }

    .terminal-dot { width: 12px; height: 12px; border-radius: 50%; }
    .dot-red    { background-color: #ef4444; }
    .dot-yellow { background-color: #eab308; }
    .dot-green  { background-color: #22c55e; }

    .log-line { padding: 4px 0; font-family: 'JetBrains Mono', monospace; }
    .log-success { color: #22c55e; }
    .log-error   { color: #ef4444; }
    .log-warning { color: #eab308; }
    .log-info    { color: #3b82f6; }
    .log-time    { color: #525252; }

    .led-container {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px;
        background-color: #0a0a0a;
        border: 1px solid #1a1a1a;
        border-radius: 8px;
        margin-top: 20px;
    }

    .led-pulse {
        width: 10px;
        height: 10px;
        background-color: #22c55e;
        border-radius: 50%;
        animation: pulse 2s infinite;
        box-shadow: 0 0 10px #22c55e;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 10px #22c55e; }
        50%       { opacity: 0.5; box-shadow: 0 0 5px #22c55e; }
    }

    .security-header {
        background: linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 100%);
        border: 1px solid #262626;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .header-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        color: #FFD700;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
        letter-spacing: 0.1em;
    }

    .header-clock {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.25rem;
        color: #FFD700;
        background-color: #0a0a0a;
        padding: 8px 16px;
        border: 1px solid #262626;
        border-radius: 4px;
    }

    .dataframe {
        background-color: #0d0d0d !important;
        color: #d4d4d4 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px !important;
    }

    .dataframe th {
        background-color: #1a1a1a !important;
        color: #FFD700 !important;
        border-bottom: 1px solid #262626 !important;
    }

    .dataframe td { border-bottom: 1px solid #1a1a1a !important; }

    .metric-card {
        background: linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 100%);
        border: 1px solid #262626;
        border-radius: 8px;
        padding: 20px;
    }

    .stButton > button {
        background-color: #1a1a1a !important;
        color: #FFD700 !important;
        border: 1px solid #262626 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    .stButton > button:hover {
        background-color: #262626 !important;
        border-color: #FFD700 !important;
    }

    .stSelectbox > div > div {
        background-color: #1a1a1a !important;
        border-color: #262626 !important;
        color: #d4d4d4 !important;
    }

    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: #FFD700; font-family: 'JetBrains Mono', monospace; margin: 0;">
            🤖 REMNANT
        </h2>
        <p style="color: #525252; font-size: 12px; margin-top: 8px;">
            Security Monitor v2.0
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    pagina = st.radio(
        "Navegação",
        ["📊 Dashboard", "📜 Logs", "⚡ Comandos", "⚙️ Configurações"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    sys_stats = get_system_stats()

    st.markdown("""
    <div class="led-container">
        <div class="led-pulse"></div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 12px;">
            <span style="color: #22c55e;">J1800</span>
            <span style="color: #525252;"> Online</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top: 12px; padding: 12px; background-color: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 8px;">
        <p style="color: #525252; font-size: 10px; margin: 0; text-transform: uppercase;">Uptime do Sistema</p>
        <p style="color: #FFD700; font-family: 'JetBrains Mono', monospace; font-size: 14px; margin: 4px 0 0 0;">
            {sys_stats['uptime']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    db_path_input = st.text_input(
        "Caminho do bot.db",
        value=DB_PATH,
        help="Caminho absoluto ou relativo para o ficheiro SQLite do bot."
    )
    if db_path_input != DB_PATH:
        os.environ["REMNANT_DB_PATH"] = db_path_input
        st.cache_data.clear()
        st.rerun()

# =============================================================================
# HEADER PRINCIPAL
# =============================================================================
current_time = datetime.now().strftime("%H:%M:%S")
current_date = datetime.now().strftime("%d/%m/%Y")

st.markdown(f"""
<div class="security-header">
    <div>
        <div class="header-title">REMNANT - SECURITY MONITOR</div>
        <p style="color: #525252; font-size: 12px; margin-top: 4px;">
            Sistema de Monitoramento do Bot Discord · Celeron J1800
        </p>
    </div>
    <div class="header-clock">
        <div>{current_time}</div>
        <div style="font-size: 10px; color: #525252;">{current_date}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# PÁGINAS
# =============================================================================

if "📊 Dashboard" in pagina:

    sys_stats = get_system_stats()
    cog_stats = get_cog_stats()
    members   = get_member_count()
    cpu_val   = sys_stats["cpu"]
    ram_val   = sys_stats["ram"]

    # ---- CARDS DE MÉTRICAS ----
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <p style="color: #525252; font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; margin: 0;">
                Usuários Únicos
            </p>
            <p style="color: #FFD700; font-family: 'JetBrains Mono', monospace; font-size: 2.5rem; margin: 8px 0;">
                {members}
            </p>
            <p style="color: #22c55e; font-size: 12px; margin: 0;">
                ↑ Contagem real dos logs
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        cpu_color = "#22c55e" if cpu_val < 60 else "#eab308" if cpu_val < 85 else "#ef4444"
        st.markdown(f"""
        <div class="metric-card">
            <p style="color: #525252; font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; margin: 0;">
                CPU (Real)
            </p>
            <p style="color: {cpu_color}; font-family: 'JetBrains Mono', monospace; font-size: 2.5rem; margin: 8px 0;">
                {cpu_val:.1f}%
            </p>
            <p style="color: #525252; font-size: 12px; margin: 0;">
                Celeron J1800 · {psutil.cpu_count()} cores
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        ram_info  = psutil.virtual_memory()
        ram_used  = ram_info.used  // (1024 ** 2)
        ram_total = ram_info.total // (1024 ** 2)
        ram_color = "#22c55e" if ram_val < 70 else "#eab308" if ram_val < 90 else "#ef4444"
        st.markdown(f"""
        <div class="metric-card">
            <p style="color: #525252; font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; margin: 0;">
                RAM (Real)
            </p>
            <p style="color: {ram_color}; font-family: 'JetBrains Mono', monospace; font-size: 2.5rem; margin: 8px 0;">
                {ram_val:.1f}%
            </p>
            <p style="color: #a3a3a3; font-size: 12px; margin: 0;">
                {ram_used} MB / {ram_total} MB
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        cog_color = "#22c55e" if cog_stats["ativas"] == cog_stats["total"] and cog_stats["total"] > 0 else "#eab308"
        cog_label = "Todas operacionais" if cog_stats["ativas"] == cog_stats["total"] and cog_stats["total"] > 0 else "Verificar logs"
        st.markdown(f"""
        <div class="metric-card">
            <p style="color: #525252; font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; margin: 0;">
                Cogs Carregadas
            </p>
            <p style="color: #FFD700; font-family: 'JetBrains Mono', monospace; font-size: 2.5rem; margin: 8px 0;">
                {cog_stats['ativas']}/{cog_stats['total']}
            </p>
            <p style="color: {cog_color}; font-size: 12px; margin: 0;">
                ✓ {cog_label}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- TERMINAL DE LOGS + GRÁFICOS ----
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("""
        <h3 style="color: #FFD700; font-family: 'JetBrains Mono', monospace; font-size: 14px; margin-bottom: 16px;">
            📜 TERMINAL DE LOGS
        </h3>
        """, unsafe_allow_html=True)

        log_entries = get_log_entries(limit=20)
        log_html = """
        <div class="terminal-container">
            <div class="terminal-header">
                <div class="terminal-dot dot-red"></div>
                <div class="terminal-dot dot-yellow"></div>
                <div class="terminal-dot dot-green"></div>
                <span style="color: #525252; font-size: 12px; margin-left: 8px;">remnant.log</span>
            </div>
        """
        for log_type, message, css_class, ts in log_entries:
            log_html += f"""
            <div class="log-line">
                <span class="log-time">[{ts}]</span>
                <span class="{css_class}">&nbsp;[{log_type}]&nbsp;</span>
                <span style="color: #d4d4d4;">{message}</span>
            </div>
            """
        log_html += '<div class="log-line"><span style="color: #FFD700;">▌</span></div></div>'
        st.markdown(log_html, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <h3 style="color: #FFD700; font-family: 'JetBrains Mono', monospace; font-size: 14px; margin-bottom: 16px;">
            📈 USO DE RECURSOS (Tempo Real)
        </h3>
        """, unsafe_allow_html=True)

        cpu_hist = list(st.session_state.cpu_history)
        fig_cpu = go.Figure()
        fig_cpu.add_trace(go.Scatter(
            y=cpu_hist,
            mode='lines',
            fill='tozeroy',
            line=dict(color='#FFD700', width=2),
            fillcolor='rgba(255, 215, 0, 0.1)'
        ))
        fig_cpu.update_layout(
            title=dict(text=f'CPU % — atual: {cpu_val:.1f}%', font=dict(color='#a3a3a3', size=12)),
            height=150,
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor='#0d0d0d',
            plot_bgcolor='#0d0d0d',
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=True, gridcolor='#1a1a1a', tickfont=dict(color='#525252', size=10), range=[0, 100]),
        )
        st.plotly_chart(fig_cpu, use_container_width=True)

        ram_hist = list(st.session_state.ram_history)
        fig_ram = go.Figure()
        fig_ram.add_trace(go.Scatter(
            y=ram_hist,
            mode='lines',
            fill='tozeroy',
            line=dict(color='#3b82f6', width=2),
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))
        fig_ram.update_layout(
            title=dict(text=f'RAM % — atual: {ram_val:.1f}%', font=dict(color='#a3a3a3', size=12)),
            height=150,
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor='#0d0d0d',
            plot_bgcolor='#0d0d0d',
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=True, gridcolor='#1a1a1a', tickfont=dict(color='#525252', size=10), range=[0, 100]),
        )
        st.plotly_chart(fig_ram, use_container_width=True)

        disk      = psutil.disk_usage('/')
        disk_pct  = disk.percent
        disk_color = "#22c55e" if disk_pct < 70 else "#eab308" if disk_pct < 90 else "#ef4444"
        st.markdown(f"""
        <div style="padding: 10px; background-color: #0d0d0d; border: 1px solid #262626; border-radius: 6px; margin-top: -10px;">
            <p style="color: #525252; font-size: 10px; text-transform: uppercase; margin: 0;">Disco</p>
            <p style="color: {disk_color}; font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; margin: 4px 0 0 0;">
                {disk_pct:.1f}%
                <span style="color: #525252; font-size: 10px;">
                    &nbsp;{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB
                </span>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- TABELA DE ÚLTIMOS COMANDOS ----
    st.markdown("""
    <h3 style="color: #FFD700; font-family: 'JetBrains Mono', monospace; font-size: 14px; margin-bottom: 16px;">
        ⚡ ÚLTIMOS COMANDOS EXECUTADOS
    </h3>
    """, unsafe_allow_html=True)

    df_commands = get_recent_commands(limit=10)

    if df_commands.empty:
        st.markdown("""
        <div style="padding: 20px; background-color: #0d0d0d; border: 1px solid #262626; border-radius: 8px; text-align: center;">
            <span style="color: #525252; font-family: 'JetBrains Mono', monospace; font-size: 12px;">
                Nenhum comando encontrado. Aguardando o bot gravar os primeiros logs...
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_cfg = {col: st.column_config.TextColumn(col.capitalize(), width="medium") for col in df_commands.columns}
        st.dataframe(df_commands, use_container_width=True, hide_index=True, column_config=col_cfg)

    # Auto-refresh a cada 10 segundos
    time.sleep(0.5)
    st.rerun()

# =============================================================================
elif "📜 Logs" in pagina:

    st.markdown("""
    <h2 style="color: #FFD700;">Logs Completos</h2>
    <p style="color: #a3a3a3;">Tabela <code>logs</code> do banco de dados — gravada em tempo real pelo bot.</p>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        filtro_tipo = st.selectbox("Filtrar por nível", ["Todos", "INFO", "WARNING", "ERROR", "DEBUG"])
    with col2:
        busca = st.text_input("Buscar nos logs", placeholder="Digite para buscar...")

    logs = get_log_entries(limit=200, log_type_filter=filtro_tipo)
    if busca:
        logs = [(t, m, c, ts) for t, m, c, ts in logs if busca.lower() in m.lower()]

    log_html = '<div class="terminal-container" style="max-height: 600px;">'
    for log_type, message, css_class, ts in logs:
        log_html += f"""
        <div class="log-line">
            <span class="log-time">[{ts}]</span>
            <span class="{css_class}">&nbsp;[{log_type}]&nbsp;</span>
            <span style="color: #d4d4d4;">{message}</span>
        </div>
        """
    if not logs:
        log_html += '<div class="log-line"><span style="color: #525252;">Nenhum log encontrado.</span></div>'
    log_html += '</div>'
    st.markdown(log_html, unsafe_allow_html=True)

# =============================================================================
elif "⚡ Comandos" in pagina:

    st.markdown("""
    <h2 style="color: #FFD700;">Histórico de Comandos</h2>
    <p style="color: #a3a3a3;">Todos os comandos registados pelo logger <code>CMD</code>.</p>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        busca_cmd = st.text_input("Filtrar por comando", placeholder="/help, /ban...")
    with col2:
        busca_user = st.text_input("Filtrar por usuário", placeholder="Nome do usuário")

    df_all = get_recent_commands(limit=500)

    if busca_cmd:
        df_all = df_all[df_all["comando"].str.contains(busca_cmd, case=False, na=False)]
    if busca_user:
        df_all = df_all[df_all["usuario"].str.contains(busca_user, case=False, na=False)]

    if df_all.empty:
        st.markdown("""
        <div style="padding: 20px; background-color: #0d0d0d; border: 1px solid #262626; border-radius: 8px; text-align: center;">
            <span style="color: #525252; font-family: 'JetBrains Mono', monospace; font-size: 12px;">
                Nenhum resultado encontrado.
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.dataframe(df_all, use_container_width=True, hide_index=True)

# =============================================================================
elif "⚙️ Configurações" in pagina:

    st.markdown("""
    <h2 style="color: #FFD700;">Configurações</h2>
    <p style="color: #a3a3a3;">Configurações do painel de monitoramento.</p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="padding: 20px; background-color: #0d0d0d; border: 1px solid #262626; border-radius: 8px; margin-bottom: 16px;">
        <h3 style="color: #FFD700; font-size: 14px; font-family: 'JetBrains Mono', monospace;">🗄️ Banco de Dados</h3>
        <p style="color: #a3a3a3; font-size: 12px;">
            Conexão SQLite em modo <strong>read-only</strong> — nunca bloqueia o bot.<br>
            Tabelas usadas: <code>logs</code> e <code>chat_logs</code> (esquema real do bot.py).<br>
            Altera o caminho na sidebar para apontar para o teu <code>bot.db</code>.
        </p>
    </div>

    <div style="padding: 20px; background-color: #0d0d0d; border: 1px solid #262626; border-radius: 8px; margin-bottom: 16px;">
        <h3 style="color: #FFD700; font-size: 14px; font-family: 'JetBrains Mono', monospace;">⚡ Cache e Performance</h3>
        <p style="color: #a3a3a3; font-size: 12px;">
            • Comandos / logs: cache de 10s<br>
            • Membros / cogs: cache de 30–60s<br>
            • CPU / RAM / Disco: tempo real via psutil (sem cache)<br>
            • Dashboard auto-atualiza a cada ~10s
        </p>
    </div>

    <div style="padding: 20px; background-color: #0d0d0d; border: 1px solid #262626; border-radius: 8px;">
        <h3 style="color: #FFD700; font-size: 14px; font-family: 'JetBrains Mono', monospace;">🔧 Variável de Ambiente</h3>
        <p style="color: #a3a3a3; font-size: 12px;">
            <code>export REMNANT_DB_PATH=/caminho/completo/bot.db</code><br>
            streamlit run painel.py
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <h3 style="color: #FFD700; font-family: 'JetBrains Mono', monospace; font-size: 14px;">
        🖥️ Informações do Sistema
    </h3>
    """, unsafe_allow_html=True)

    cpu_freq = psutil.cpu_freq()
    net_io   = psutil.net_io_counters()

    info_data = {
        "Parâmetro": [
            "CPU Cores (lógicos)", "CPU Frequência",
            "RAM Total", "RAM Disponível",
            "Disco Total", "Disco Livre",
            "Bytes Enviados (rede)", "Bytes Recebidos (rede)",
        ],
        "Valor": [
            str(psutil.cpu_count()),
            f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A",
            f"{psutil.virtual_memory().total // (1024**2)} MB",
            f"{psutil.virtual_memory().available // (1024**2)} MB",
            f"{psutil.disk_usage('/').total // (1024**3)} GB",
            f"{psutil.disk_usage('/').free // (1024**3)} GB",
            f"{net_io.bytes_sent // (1024**2)} MB",
            f"{net_io.bytes_recv // (1024**2)} MB",
        ]
    }
    st.dataframe(pd.DataFrame(info_data), use_container_width=True, hide_index=True)