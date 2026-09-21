from config import normalize_database_url


def test_normalize_postgres_provider_urls():
    assert normalize_database_url(
        "postgres://user:secret@localhost:5432/rambutan"
    ) == "postgresql+psycopg://user:secret@localhost:5432/rambutan"
    assert normalize_database_url(
        "postgresql://user:secret@localhost:5432/rambutan"
    ) == "postgresql+psycopg://user:secret@localhost:5432/rambutan"


def test_sqlite_url_is_unchanged():
    value = "sqlite:///instance/test.sqlite3"
    assert normalize_database_url(value) == value
