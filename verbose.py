import logging
import inspect
import sqlite3
from pathlib import Path

LOGS_DIR = Path("./logs")
LOGS_DIR.mkdir(exist_ok=True)

# =============================================================================
# SQLITE HANDLER
# =============================================================================
class SQLiteHandler(logging.Handler):
    def __init__(self, db_path: str = "bot.db"):
        super().__init__()
        self._db_path = db_path
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level     TEXT NOT NULL,
                    logger    TEXT NOT NULL,
                    message   TEXT NOT NULL
                )
            """)

    def emit(self, record: logging.LogRecord):
        try:
            with sqlite3.connect(self._db_path, timeout=3) as conn:
                conn.execute(
                    "INSERT INTO logs (timestamp, level, logger, message) VALUES (?, ?, ?, ?)",
                    (
                        self.formatTime(record, "%Y-%m-%d %H:%M:%S"), # type: ignore
                        record.levelname,
                        record.name,
                        # CORRIGIDO: usa record.getMessage() em vez de self.format(record)
                        # Isso grava apenas a mensagem limpa, sem prefixo extra do formatter.
                        # Resultado no banco: "[Fazbear] #geral | User usou: /help"
                        # (compatível com o regex do painel.py)
                        record.getMessage(),
                    )
                )
        except Exception:
            pass

# =============================================================================
# LOGGERS INDIVIDUAIS
# =============================================================================
def _get_logger(name: str, filename: str, color_code: str = "") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # guard contra duplicação no reload

    logger.setLevel(logging.DEBUG)

    # Desativa propagação para o root — o SQLiteHandler já está
    # em cada logger individualmente (adicionado abaixo).
    # Isso evita duplicatas no banco se o módulo for reimportado.
    logger.propagate = False

    file_handler = logging.FileHandler(LOGS_DIR / filename, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        f"\033[{color_code}m[%(asctime)s] [%(name)s] %(message)s\033[0m",
        datefmt="%H:%M:%S"
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

# =============================================================================
# SQLITE HANDLER — adicionado uma única vez via guard no root
# Com propagate=False nos loggers filhos, o root NÃO recebe as mensagens.
# Por isso adicionamos o SQLiteHandler diretamente em cada logger em vez do root.
# O guard `if logger.handlers` em _get_logger já previne duplicatas no reload.
# =============================================================================
def _build_sqlite_handler() -> SQLiteHandler:
    h = SQLiteHandler("bot.db")
    h.setLevel(logging.INFO)  # DEBUG seria verboso demais para o J1800
    # Sem formatter: usamos record.getMessage() diretamente no emit()
    return h

_cmd    = _get_logger("CMD",    "commands.log",  "36")
_event  = _get_logger("EVENT",  "events.log",    "32")
_error  = _get_logger("ERROR",  "errors.log",    "31")
_system = _get_logger("SYSTEM", "system.log",    "33")

# Adiciona o SQLiteHandler a cada logger individualmente.
# O guard abaixo evita adicionar novamente se o módulo for recarregado
# (ex: reload de cog que reimporta verbose).
for _logger in (_cmd, _event, _error, _system):
    if not any(isinstance(h, SQLiteHandler) for h in _logger.handlers):
        _logger.addHandler(_build_sqlite_handler())

# =============================================================================
# FUNÇÕES PÚBLICAS
# =============================================================================

def log_command(user: str, command: str, guild: str = "DM", channel: str = ""):
    """
    Registra um comando executado por um usuário.
    Formato gravado no banco: "[Guild] #channel | user usou: /comando"
    O painel.py faz parsing desse formato para exibir servidor/usuário/comando.
    """
    _cmd.info(f"[{guild}] #{channel} | {user} usou: {command}")

def log_event(event: str, detail: str = ""):
    """Registra um evento do Discord (ban, kick, entrada, saída, etc)."""
    _event.info(f"{event} | {detail}" if detail else event)

def log_error(location: str, error: Exception):
    """Registra um erro ou exceção com localização."""
    _error.error(f"[{location}] {type(error).__name__}: {error}")

def log_system(message: str):
    """
    Registra mensagens internas do sistema (startup, reload, banco, etc).
    O painel.py conta linhas com 'Módulo carregado:' para o card de cogs.
    """
    _system.info(message)

def log_trace(label: str):
    """
    Loga de onde a função foi chamada — útil para debugar duplicatas.
    Não grava no banco (nível DEBUG é filtrado pelo SQLiteHandler).

    Uso:
        log_trace("on_command")

    Remove após resolver o bug.
    """
    stack = inspect.stack()
    _system.debug(f"[TRACE] {label}")
    for frame in stack[1:4]:
        filename = Path(frame.filename).name
        _system.debug(f"  → {filename}:{frame.lineno} em {frame.function}")