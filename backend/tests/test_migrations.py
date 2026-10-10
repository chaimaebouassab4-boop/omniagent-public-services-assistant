"""Regression tests for additive migrations on existing databases."""

from sqlalchemy import create_engine, inspect, text

from app.db.migrations import migrate


def test_existing_chat_table_receives_all_columns_without_losing_messages():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE chat_messages (id VARCHAR PRIMARY KEY, message TEXT)"))
        connection.execute(text("INSERT INTO chat_messages (id, message) VALUES ('1', 'existing')"))
        connection.execute(text("CREATE TABLE users (id VARCHAR PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE cases (id VARCHAR PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE documents (id VARCHAR PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE schema_migrations (version VARCHAR PRIMARY KEY)"))
        connection.execute(text(
            "INSERT INTO schema_migrations (version) VALUES ('20260927_real_workflow')"
        ))

    migrate(engine)
    migrate(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("chat_messages")}
    assert {"conversation_state", "procedure_id", "suggested_questions"} <= columns
    with engine.connect() as connection:
        assert connection.execute(text("SELECT message FROM chat_messages WHERE id='1'")).scalar_one() == "existing"
