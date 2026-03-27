import sqlite3

# conecta ao banco (usa o bot.db que você criou)
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

# cria tabela de logs
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    command TEXT,
    date TEXT
)
""")

conn.commit()

# função para salvar log
def salvar_log(user, command):
    cursor.execute(
        "INSERT INTO logs (user, command, date) VALUES (?, ?, datetime('now'))",
        (str(user), command)
    )
    conn.commit()