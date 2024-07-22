# This is a custom logging format for the sqs queue consumers and producers.

import logging
from colorlog import ColoredFormatter

PRODUCER_LEVEL = 25
MAGIC_SIGNON_LEVEL = 35
TREASURE_VAULT_LEVEL = 45

logging.addLevelName(PRODUCER_LEVEL, "PRODUCER")
logging.addLevelName(MAGIC_SIGNON_LEVEL, "MAGIC_SIGNON")
logging.addLevelName(TREASURE_VAULT_LEVEL, "TREASURE_VAULT")

class CustomLogger(logging.Logger):
    """Custom logger class with multiple `log` methods."""
    def producer(self, message, *args, **kws):
        """Log 'message % args' with severity 'PRODUCER'."""
        self._log(PRODUCER_LEVEL, message, args, **kws)

    def magic_signon(self, message, *args, **kws):
        """Log 'message % args' with severity 'MAGIC_SIGNON'."""
        self._log(MAGIC_SIGNON_LEVEL, message, args, **kws)

    def treasure_vault(self, message, *args, **kws):
        """Log 'message % args' with severity 'TREASURE_VAULT'."""
        self._log(TREASURE_VAULT_LEVEL, message, args, **kws)
# def producer(self, message, *args, **kws):
#     self._log(PRODUCER_LEVEL, message, args, **kws)


# def magic_signon(self, message, *args, **kws):
#     self._log(MAGIC_SIGNON_LEVEL, message, args, **kws)


# def treasure_vault(self, message, *args, **kws):
#     self._log(TREASURE_VAULT_LEVEL, message, args, **kws)


# logging.Logger.producer = producer
# logging.Logger.magic_signon = magic_signon
# logging.Logger.treasure_vault = treasure_vault


def init_logger(worker_name: str = None):
    """Initialize logger with custom logging format."""
    logger = CustomLogger(__name__)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    worker_id = worker_name if worker_name else "worker %(process)d"
    formatter = ColoredFormatter(
        f"%(log_color)s[%(levelname)s- {worker_id}]%(reset)s %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "purple",
            "INFO": "green",
            "PRODUCER": "purple",
            "MAGIC_SIGNON": "bold_blue",
            "TREASURE_VAULT": "bold_cyan",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red",
        }
    )

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
