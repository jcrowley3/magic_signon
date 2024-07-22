import os
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from app.configs.database_configs import db_config

# create the database url using values from db_config
DATABASE_URL = f"postgresql://{db_config.USER}:{db_config.PASSWD}@{db_config.HOST}:{db_config.PORT}/{db_config.DB}"

echo_sql_output: bool = os.environ.get("ENV", "local").lower() == "local"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=echo_sql_output)
# engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

Session = sessionmaker(bind=engine)


def get_session():
    with Session() as session:
        yield session
