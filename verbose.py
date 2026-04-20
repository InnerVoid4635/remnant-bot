import logging
import inspect
from pathlib import Path

# --- CONFIGURAÇÃO DE PASTAS ---
LOGS_DIR = Path("./logs")
LOGS_DIR.mkdir(exist_ok=True)

def _get_logger(name: str, filename: str, color_code: str = "") -> logging.Logger:
    """Cria e configura um logger individual por categoria."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Evita duplicar handlers no reload

    logger.setLevel(logging.DEBUG)

    # Handler de arquivo (salva no disco)
    file_handler = logging.FileHandler(
        LOGS_DIR / filename,
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Handler de terminal (colorido)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        f"\033[{color_code}m[%(asctime)s] [%(name)s] %(message)s\033[0m",
        datefmt="%H:%M:%S"
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

# --- LOGGERS INDIVIDUAIS ---
_cmd    = _get_logger("CMD",    "commands.log",  "36")  # Ciano
_event  = _get_logger("EVENT",  "events.log",    "32")  # Verde
_error  = _get_logger("ERROR",  "errors.log",    "31")  # Vermelho
_system = _get_logger("SYSTEM", "system.log",    "33")  # Amarelo

# --- FUNÇÕES PÚBLICAS ---

def log_command(user: str, command: str, guild: str = "DM", channel: str = ""):
    """Registra um comando executado por um usuário."""
    _cmd.info(f"[{guild}] #{channel} | {user} usou: {command}")

def log_event(event: str, detail: str = ""):
    """Registra um evento do Discord (ban, kick, entrada, saída, etc)."""
    _event.info(f"{event} | {detail}" if detail else event)

def log_error(location: str, error: Exception):
    """Registra um erro ou exceção com localização."""
    _error.error(f"[{location}] {type(error).__name__}: {error}")

def log_system(message: str):
    """Registra mensagens internas do sistema (startup, reload, banco, etc)."""
    _system.info(message)

def log_trace(label: str):
    """Loga de onde a função foi chamada — útil para debugar duplicatas.
    
    Uso:
        log_trace("on_command")  # mostra arquivo, linha e função dos 3 níveis acima
    
    Remove após resolver o bug.
    """
    stack = inspect.stack()
    _system.debug(f"[TRACE] {label}")
    for frame in stack[1:4]:  # 3 níveis acima da chamada
        filename = Path(frame.filename).name
        _system.debug(f"  → {filename}:{frame.lineno} em {frame.function}")