"""
╔══════════════════════════════════════════════════════╗
║         REMNANT WEB DASHBOARD — dashboard.py         ║
║  Flask + autenticação + mobile-friendly              ║
║  Instalar: pip install flask psutil                  ║
║  Rodar:    python dashboard.py                       ║
║  Acesso:   http://SEU_IP:5000                        ║
╚══════════════════════════════════════════════════════╝
"""

import sqlite3
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

import psutil
from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify

# ══════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "remnant2024")
SECRET_KEY         = os.getenv("DASHBOARD_SECRET_KEY", "fallback-inseguro-troque")
DB_PATH            = Path("./bot.db")
PORT               = 5000
HOST               = "0.0.0.0"

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=12)

# ══════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════
# DB HELPERS
# ══════════════════════════════════════════════════════
def get_db():
    uri = f"file:{DB_PATH}?mode=ro"
    return sqlite3.connect(uri, uri=True)

def query(sql, params=()):
    if not DB_PATH.exists():
        return []
    try:
        with get_db() as conn:
            return conn.execute(sql, params).fetchall()
    except Exception:
        return []

def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


# ══════════════════════════════════════════════════════
# TEMPLATE BASE — mobile-first, limpo
# ══════════════════════════════════════════════════════
BASE_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<meta name="theme-color" content="#0f1117">
<title>Remnant Dashboard</title>
<style>
  :root {
    --bg:      #0f1117;
    --surface: #1a1d27;
    --border:  #2a2d3a;
    --text:    #e2e8f0;
    --muted:   #64748b;
    --accent:  #6366f1;
    --green:   #22c55e;
    --red:     #ef4444;
    --yellow:  #f59e0b;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 15px;
    min-height: 100vh;
  }
  nav {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 14px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  nav .brand { font-weight: 700; font-size: 17px; letter-spacing: 0.5px; }
  nav .brand span { color: var(--accent); }
  nav a { color: var(--muted); text-decoration: none; font-size: 13px; }
  nav a:hover { color: var(--text); }
  .container { max-width: 900px; margin: 0 auto; padding: 20px 16px 60px; }
  .cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 24px; }
  @media (min-width: 600px) { .cards { grid-template-columns: repeat(4, 1fr); } }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
  }
  .card .label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
  .card .value { font-size: 26px; font-weight: 700; }
  .card .sub   { font-size: 11px; color: var(--muted); margin-top: 2px; }
  .card.accent .value { color: var(--accent); }
  .card.green  .value { color: var(--green); }
  .card.yellow .value { color: var(--yellow); }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .dot.online  { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .dot.offline { background: var(--red); }
  .section { margin-bottom: 24px; }
  .section h2 {
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--muted);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }
  .table-wrap { overflow-x: auto; border-radius: 10px; border: 1px solid var(--border); }
  table { width: 100%; border-collapse: collapse; background: var(--surface); }
  th { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted);
       padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }
  td { padding: 10px 14px; border-bottom: 1px solid var(--border); font-size: 13px; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(99,102,241,0.04); }
  .badge {
    display: inline-block;
    background: rgba(99,102,241,0.15);
    color: var(--accent);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
  }
  .prog-wrap { margin-bottom: 14px; }
  .prog-label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 5px; }
  .prog-label .name { color: var(--muted); }
  .prog-bg { background: var(--border); border-radius: 4px; height: 6px; }
  .prog-fill { height: 6px; border-radius: 4px; background: var(--accent); transition: width 0.3s; }
  .prog-fill.warn   { background: var(--yellow); }
  .prog-fill.danger { background: var(--red); }
  .log-list { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
  .log-item { padding: 10px 14px; border-bottom: 1px solid var(--border); font-size: 12px; display: flex; gap: 10px; align-items: baseline; }
  .log-item:last-child { border-bottom: none; }
  .log-time { color: var(--muted); white-space: nowrap; flex-shrink: 0; }
  .log-user { color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .log-cmd  { color: var(--accent); font-weight: 600; margin-left: auto; flex-shrink: 0; }
  .login-wrap { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
  .login-box {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 32px 28px;
    width: 100%;
    max-width: 360px;
  }
  .login-box h1 { font-size: 22px; margin-bottom: 4px; }
  .login-box p  { color: var(--muted); font-size: 13px; margin-bottom: 24px; }
  input[type=password] {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    padding: 12px 14px;
    font-size: 15px;
    margin-bottom: 12px;
    outline: none;
  }
  input[type=password]:focus { border-color: var(--accent); }
  button[type=submit] {
    width: 100%;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 13px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
  }
  button[type=submit]:hover { opacity: 0.9; }
  .error { color: var(--red); font-size: 13px; margin-bottom: 12px; }
  .refresh-bar {
    background: var(--surface);
    border-top: 1px solid var(--border);
    padding: 10px 20px;
    font-size: 12px;
    color: var(--muted);
    text-align: center;
    position: fixed;
    bottom: 0; left: 0; right: 0;
  }
</style>
</head>
<body>
{% block body %}{% endblock %}
<script>
  setTimeout(() => location.reload(), 30000);
</script>
</body>
</html>
"""

LOGIN_HTML = BASE_HTML.replace("{% block body %}{% endblock %}", """
<div class="login-wrap">
  <div class="login-box">
    <h1>⚡ Remnant</h1>
    <p>Dashboard privado — faça login para continuar</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="POST">
      <input type="password" name="password" placeholder="Senha" autofocus>
      <button type="submit">Entrar</button>
    </form>
  </div>
</div>
""")

DASHBOARD_HTML = BASE_HTML.replace("{% block body %}{% endblock %}", """
<nav>
  <div class="brand">⚡ <span>Remnant</span> Dashboard</div>
  <a href="/logout">Sair</a>
</nav>

<div class="container">

  <div class="cards" style="margin-top:20px">
    <div class="card green">
      <div class="label">Status</div>
      <div class="value" style="font-size:16px; padding-top:4px">
        <span class="dot online"></span>Online
      </div>
      <div class="sub">{{ uptime }}</div>
    </div>
    <div class="card accent">
      <div class="label">CPU Freq.</div>
      <div class="value">{{ cpu_freq }}<span style="font-size:14px">MHz</span></div>
    </div>
    <div class="card">
      <div class="label">Membros</div>
      <div class="value">{{ members }}</div>
      <div class="sub">{{ servers }} servidor(es)</div>
    </div>
    <div class="card yellow">
      <div class="label">Comandos</div>
      <div class="value">{{ total_cmds }}</div>
      <div class="sub">{{ unique_users }} usuários</div>
    </div>
  </div>

  <div class="section">
    <h2>🖥️ Sistema</h2>
    <div class="card" style="padding:20px">
      <div class="prog-wrap">
        <div class="prog-label">
          <span class="name">CPU</span>
          <span>{{ cpu }}%</span>
        </div>
        <div class="prog-bg">
          <div class="prog-fill {% if cpu|int > 80 %}danger{% elif cpu|int > 60 %}warn{% endif %}"
               style="width:{{ cpu }}%"></div>
        </div>
      </div>
      <div class="prog-wrap">
        <div class="prog-label">
          <span class="name">RAM — {{ ram_used }} / {{ ram_total }}</span>
          <span>{{ ram_pct }}%</span>
        </div>
        <div class="prog-bg">
          <div class="prog-fill {% if ram_pct|int > 80 %}danger{% elif ram_pct|int > 60 %}warn{% endif %}"
               style="width:{{ ram_pct }}%"></div>
        </div>
      </div>
      <div class="prog-wrap" style="margin-bottom:0">
        <div class="prog-label">
          <span class="name">Disco — {{ disk_used }} / {{ disk_total }}</span>
          <span>{{ disk_pct }}%</span>
        </div>
        <div class="prog-bg">
          <div class="prog-fill {% if disk_pct|int > 80 %}danger{% elif disk_pct|int > 60 %}warn{% endif %}"
               style="width:{{ disk_pct }}%"></div>
        </div>
      </div>
    </div>
  </div>

  {% if top_cmds %}
  <div class="section">
    <h2>📊 Comandos Mais Usados</h2>
    <div class="table-wrap">
      <table>
        <tr><th>Comando</th><th>Usos</th></tr>
        {% for cmd, count in top_cmds %}
        <tr>
          <td><span class="badge">{{ cmd }}</span></td>
          <td>{{ count }}</td>
        </tr>
        {% endfor %}
      </table>
    </div>
  </div>
  {% endif %}

  {% if recent_logs %}
  <div class="section">
    <h2>📡 Atividade Recente</h2>
    <div class="log-list">
      {% for user, cmd, date in recent_logs %}
      <div class="log-item">
        <span class="log-time">{{ date[-8:] if date else '—' }}</span>
        <span class="log-user">{{ user[:25] }}</span>
        <span class="log-cmd">{{ cmd }}</span>
      </div>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  {% if guild_stats %}
  <div class="section">
    <h2>🌐 Servidores</h2>
    <div class="table-wrap">
      <table>
        <tr><th>Servidor</th><th>Membros</th><th>Atualizado</th></tr>
        {% for name, count, updated in guild_stats %}
        <tr>
          <td>{{ name }}</td>
          <td>{{ count }}</td>
          <td style="color:var(--muted); font-size:12px">{{ updated[:16] if updated else '—' }}</td>
        </tr>
        {% endfor %}
      </table>
    </div>
  </div>
  {% endif %}

</div>

<div class="refresh-bar">
  Atualização automática a cada 30s · {{ now }}
</div>
""")


# ══════════════════════════════════════════════════════
# ROTAS
# ══════════════════════════════════════════════════════
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASSWORD:
            session.permanent = True
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Senha incorreta."
    return render_template_string(LOGIN_HTML, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    cpu      = psutil.cpu_percent(interval=0.3)
    ram      = psutil.virtual_memory()
    disk     = psutil.disk_usage("/")
    freq     = psutil.cpu_freq()
    cpu_freq = round(freq.current) if freq else 0

    uptime_sec = time.time() - psutil.boot_time()
    uptime = str(timedelta(seconds=int(uptime_sec))).split(".")[0]

    members_row  = query_one("SELECT SUM(member_count) FROM guild_stats")
    servers_row  = query_one("SELECT COUNT(*) FROM guild_stats")
    total_row    = query_one("SELECT COUNT(*) FROM logs")
    users_row    = query_one("SELECT COUNT(DISTINCT user) FROM logs")
    top_cmds     = query("SELECT command, COUNT(*) as n FROM logs GROUP BY command ORDER BY n DESC LIMIT 8")
    recent_logs  = query("SELECT user, command, date FROM logs ORDER BY id DESC LIMIT 20")
    guild_stats  = query("SELECT guild_name, member_count, updated_at FROM guild_stats ORDER BY member_count DESC")

    return render_template_string(DASHBOARD_HTML,
        uptime       = uptime,
        cpu_freq     = cpu_freq,
        members      = members_row[0] if members_row and members_row[0] else "—",
        servers      = servers_row[0] if servers_row else 0,
        total_cmds   = f"{total_row[0]:,}" if total_row else 0,
        unique_users = users_row[0] if users_row else 0,
        cpu          = round(cpu, 1),
        ram_pct      = round(ram.percent, 1),
        ram_used     = f"{ram.used/1e9:.1f}GB",
        ram_total    = f"{ram.total/1e9:.1f}GB",
        disk_pct     = round(disk.percent, 1),
        disk_used    = f"{disk.used/1e9:.1f}GB",
        disk_total   = f"{disk.total/1e9:.1f}GB",
        top_cmds     = top_cmds,
        recent_logs  = recent_logs,
        guild_stats  = guild_stats,
        now          = datetime.now().strftime("%H:%M:%S"),
    )


@app.route("/api/status")
@login_required
def api_status():
    cpu     = psutil.cpu_percent(interval=0.3)
    ram     = psutil.virtual_memory()
    members = query_one("SELECT SUM(member_count) FROM guild_stats")
    return jsonify({
        "cpu":     cpu,
        "ram":     round(ram.percent, 1),
        "members": members[0] if members and members[0] else 0,
        "db":      DB_PATH.exists(),
        "time":    datetime.now().isoformat(),
    })


# ══════════════════════════════════════════════════════
# START
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"🌐 Dashboard rodando em http://0.0.0.0:{PORT}")
    print(f"📱 Acesse pelo celular: http://SEU_IP_LOCAL:{PORT}")
    print(f"📁 Banco: {DB_PATH.resolve()}")
    app.run(host=HOST, port=PORT, debug=False)