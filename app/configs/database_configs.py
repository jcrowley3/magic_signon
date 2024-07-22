import os
from dataclasses import dataclass


env = os.environ.get("ENV", "local")
if os.environ.get("TEST_MODE"):
    env = "local"


@dataclass
class Base:
    HOST: str
    USER: str
    PASSWD: str
    PORT: int
    DB: str


@dataclass
class LocalDB(Base):
    # these env vars are coming from docker-compose.yml
    HOST: str = os.environ.get("POSTGRES_HOSTNAME", "localhost")
    PORT: int = os.environ.get("POSTGRES_PORT", 5434)
    USER: str = os.environ.get("POSTGRES_USER", "root")
    PASSWD: str = os.environ.get("POSTGRES_PASSWORD", "password")
    DB: str = os.environ.get("POSTGRES_DB", "magic_signon_db")


# @dataclass
# class TestDB(Base):
#     # these env vars are coming from docker-compose.yml
#     HOST: str = os.environ.get("POSTGRES_HOSTNAME", "localhost")
#     PORT: int = os.environ.get("POSTGRES_PORT", 3310)
#     USER: str = os.environ.get("POSTGRES_USER", "root")
#     PASSWD: str = os.environ.get("POSTGRES_PASSWORD", "password")
#     DB: str = os.environ.get("POSTGRES_DB", "magic_signon_db")


@dataclass
class DevDB(Base):
    # these env vars are coming from docker-compose.yml
    HOST: str = os.environ.get("POSTGRES_HOSTNAME", "0.0.0.0")
    PORT: int = os.environ.get("POSTGRES_PORT", 5432)
    USER: str = os.environ.get("POSTGRES_USER", "root")
    PASSWD: str = os.environ.get("POSTGRES_PASSWORD", "password")
    DB: str = os.environ.get("POSTGRES_DB", "magic_signon_db")


@dataclass
class StagingDB(Base):
    # these env vars are coming from docker-compose.yml
    HOST: str = os.environ.get("POSTGRES_HOSTNAME", "localhost")
    PORT: int = os.environ.get("POSTGRES_PORT", 5432)
    USER: str = os.environ.get("POSTGRES_USER", "root")
    PASSWD: str = os.environ.get("POSTGRES_PASSWORD", "password")
    DB: str = os.environ.get("POSTGRES_DB", "magic_signon_db")


@dataclass
class ProdDB(Base):
    # these env vars are coming from docker-compose.yml
    HOST: str = os.environ.get("POSTGRES_HOSTNAME", "localhost")
    PORT: int = os.environ.get("POSTGRES_PORT", 5432)
    USER: str = os.environ.get("POSTGRES_USER", "root")
    PASSWD: str = os.environ.get("POSTGRES_PASSWORD", "password")
    DB: str = os.environ.get("POSTGRES_DB", "magic_signon_db")


configs = {
    "local": LocalDB(),
    # "test": TestDB(),
    "dev": DevDB(),
    "staging": StagingDB(),
    "prod": ProdDB()
}

if env == "dev":
    db_config = configs[env]
    dev_obj = " ".join(map(str, db_config.__dict__.values()))
    print(dev_obj)

db_config = configs[env]
