
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_revocation_columns(engine: Engine) -> None:
    """Add revocation columns to an existing SQLite recipients table."""

    inspector = inspect(engine)

    if "recipients" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("recipients")
    }

    with engine.begin() as connection:
        if "is_revoked" not in existing_columns:
            connection.execute(
                text(
                    "ALTER TABLE recipients "
                    "ADD COLUMN is_revoked BOOLEAN NOT NULL DEFAULT 0"
                )
            )

        if "revoked_at" not in existing_columns:
            connection.execute(
                text(
                    "ALTER TABLE recipients "
                    "ADD COLUMN revoked_at DATETIME"
                )
            )

        if "revocation_reason" not in existing_columns:
            connection.execute(
                text(
                    "ALTER TABLE recipients "
                    "ADD COLUMN revocation_reason VARCHAR(500)"
                )
            )
