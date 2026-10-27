from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import get_settings
from app.db.base import Base
from app.modules.catalog import models as catalog_models  # noqa: F401
from app.modules.customers import models as customers_models  # noqa: F401
from app.modules.inventory import models as inventory_models  # noqa: F401
from app.modules.memberships import models as memberships_models  # noqa: F401
from app.modules.orders import models as orders_models  # noqa: F401
from app.modules.platform_admin import models as platform_admin_models  # noqa: F401
from app.modules.stores import models as stores_models  # noqa: F401
from app.modules.subscriptions import models as subscription_models  # noqa: F401
from app.modules.users import models as users_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", str(get_settings().database_url))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
