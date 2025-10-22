from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# this is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Base and ensure all models are imported for metadata
from src.database.connection import Base
from src.auth import models as auth_models  # noqa: F401
from src.groups import models as group_models  # noqa: F401
from src.stations import models as station_models  # noqa: F401
from src.devices import models as device_models  # noqa: F401
from src.policies import models as policy_models  # noqa: F401
from src.monitoring import models as monitoring_models  # noqa: F401
from src.storage import models as storage_models  # noqa: F401
from src.integrations import models as integrations_models  # noqa: F401

target_metadata = Base.metadata

# Override DB URL from env if provided
url = os.getenv("CTHZ_DATABASE_URL")
if url:
    config.set_main_option("sqlalchemy.url", url)


def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 