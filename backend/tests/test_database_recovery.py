"""Tests for startup recovery of damaged SQLite files."""
import os
import sqlite3
import sys


HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from app.database_recovery import ensure_sqlite_database


def test_truncated_database_is_backed_up_and_recovered(tmp_path):
    database_path = tmp_path / "apc.sqlite3"
    connection = sqlite3.connect(database_path)
    connection.execute(
        "CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
    )
    connection.executemany(
        "INSERT INTO items (name) VALUES (?)",
        [(f"item-{index:05d}",) for index in range(5000)],
    )
    connection.execute("CREATE INDEX ix_items_name ON items (name)")
    connection.commit()
    page_size = connection.execute("PRAGMA page_size").fetchone()[0]
    connection.close()

    original_size = database_path.stat().st_size
    with database_path.open("r+b") as database_file:
        database_file.truncate(original_size - page_size)

    report = ensure_sqlite_database(f"sqlite:///{database_path.as_posix()}")

    assert report is not None
    assert os.path.exists(report.backup_path)
    assert report.recovered_rows == {"items": 5000}
    assert report.restored_from_activity == {}
    assert report.skipped_rows == {}

    recovered = sqlite3.connect(database_path)
    assert recovered.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert recovered.execute("SELECT count(*) FROM items").fetchone() == (5000,)
    assert recovered.execute(
        "SELECT name FROM items WHERE name = 'item-04999'"
    ).fetchone() == ("item-04999",)
    recovered.close()


def test_healthy_database_is_left_unchanged(tmp_path):
    database_path = tmp_path / "healthy.sqlite3"
    connection = sqlite3.connect(database_path)
    connection.execute("CREATE TABLE items (id INTEGER PRIMARY KEY)")
    connection.execute("INSERT INTO items DEFAULT VALUES")
    connection.commit()
    connection.close()
    original = database_path.read_bytes()

    report = ensure_sqlite_database(f"sqlite:///{database_path.as_posix()}")

    assert report is None
    assert database_path.read_bytes() == original
