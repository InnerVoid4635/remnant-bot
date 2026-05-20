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
# SQLITE HANDLER
# =============================================================================
def _build_sqlite_handler() -> SQLiteHandler:
    h = SQLiteHandler("bot.db")
    h.setLevel(logging.INFO)
    return h

_cmd    = _get_logger("CMD",    "commands.log",  "36")
_event  = _get_logger("EVENT",  "events.log",    "32")
_error  = _get_logger("ERROR",  "errors.log",    "31")
_system = _get_logger("SYSTEM", "system.log",    "33")

for _logger in (_cmd, _event, _error, _system):
    if not any(isinstance(h, SQLiteHandler) for h in _logger.handlers):
        _logger.addHandler(_build_sqlite_handler())

# =============================================================================
# FUNÇÕES PÚBLICAS
# =============================================================================

def log_command(user: object, command: str, guild: object = "DM", channel: object = ""):
    """
    Registra um comando executado por um usuário.
    Aceita tanto strings quanto objetos do Discord (Guild, Member, TextChannel, etc).
    Formato gravado no banco: "[Guild] #channel | user usou: /comando"
    """
    _cmd.info(f"[{guild}] #{channel} | {user} usou: {command}")

def log_event(event: str, detail: str = ""):
    """Registra um evento do Discord (ban, kick, entrada, saída, etc)."""
    _event.info(f"{event} | {detail}" if detail else event)

def log_error(location: str, error: Exception | str):
    """
    Registra um erro ou exceção com localização.
    Aceita tanto uma Exception quanto uma string descritiva.
    """
    if isinstance(error, Exception):
        _error.error(f"[{location}] {type(error).__name__}: {error}")
    else:
        _error.error(f"[{location}] {error}")

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