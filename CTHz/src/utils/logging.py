import logging
from pythonjsonlogger import jsonlogger

_LOGGER_CONFIGURED = False


def configure_logging() -> None:
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    log_handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    log_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [log_handler]

    _LOGGER_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name) 