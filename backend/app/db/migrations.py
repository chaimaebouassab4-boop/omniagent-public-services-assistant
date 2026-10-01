"""Additive migrations for existing SQLite/PostgreSQL installations."""
from sqlalchemy import inspect, text


def migrate(engine):
    additions = {
        "chat_messages": {"conversation_state": "JSON"},
        "users": {"profile_data": "JSON"},
        "cases": {"workflow_data": "JSON"},
        "documents": {"analysis": "JSON", "source_profile_document_id": "VARCHAR"},
    }
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR PRIMARY KEY)"))
        for table, columns in additions.items():
            existing = {column["name"] for column in inspect(connection).get_columns(table)}
            for column, kind in columns.items():
                if column not in existing:
                    connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {kind}'))
        if not connection.execute(text("SELECT version FROM schema_migrations WHERE version='20260927_real_workflow'")).first():
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES ('20260927_real_workflow')"))
