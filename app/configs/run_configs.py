import os
import logging
from dataclasses import dataclass

env = os.environ.get("ENV", "local")
log_level = os.environ.get("LOG_LEVEL", "debug").upper()


# https://www.uvicorn.org/deployment/
# server settings options


def get_log_level():
    match log_level:
        case "ERROR":
            return logging.ERROR
        case "INFO":
            return logging.INFO
        case _:
            return logging.DEBUG


@dataclass(repr=False)
class BaseConfig:
    reload: bool = True
    use_colors: bool = True
    log_level = logging.getLevelName(logging.INFO)


@dataclass
class LocalConfig(BaseConfig):
    host: str = "localhost"
    port: int = 83
    log_level = logging.getLevelName(logging.DEBUG)


@dataclass
class DevConfig(BaseConfig):
    host: str = "foobar"
    log_level = logging.getLevelName(get_log_level())


@dataclass
class StagingConfig(BaseConfig):
    # workers: int = multiprocessing.cpu_count()
    log_level = logging.getLevelName(get_log_level())


@dataclass
class ProdConfig(BaseConfig):
    #workers: int = multiprocessing.cpu_count()
    log_level = logging.getLevelName(get_log_level())


configs = {
    "local": LocalConfig(),
    "dev": DevConfig(),
    "staging": StagingConfig(),
    "prod": ProdConfig()
}

run_config = configs[env]
