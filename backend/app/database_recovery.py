"""SQLite integrity checks and best-effort recovery for local deployments."""
from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sqlite3
import struct
from typing import Any

from sqlalchemy.engine import make_url


SQLITE_HEADER = b"SQLite format 3\x00"


class DatabaseRecoveryError(RuntimeError):
    """Raised when a corrupt database cannot be recovered automatically."""


@dataclass(frozen=True)
class RecoveryReport:
    database_path: str
    backup_path: str
    recovered_rows: dict[str, int]
    restored_from_activity: dict[str, int]
    skipped_rows: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ensure_sqlite_database(
    database_uri: str,
    *,
    relative_to: str | None = None,
) -> RecoveryReport | None:
    """Recover a corrupt file-backed SQLite database before SQLAlchemy opens it."""
    database_path = _sqlite_path(database_uri, relative_to=relative_to)
    if not database_path or not os.path.exists(database_path):
        return None

    if _quick_check(database_path):
        return None

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = _available_path(f"{database_path}.corrupt-{timestamp}.bak")
    recovered_path = _available_path(f"{database_path}.recovering")
    salvage_path = _available_path(f"{database_path}.salvage")
    shutil.copy2(database_path, backup_path)

    try:
        shutil.copy2(backup_path, salvage_path)
        _normalize_truncated_header(salvage_path)
        recovered_rows, restored_from_activity, skipped_rows = _copy_readable_data(
            salvage_path,
            recovered_path,
        )
        if not _quick_check(recovered_path):
            raise DatabaseRecoveryError("recovered database failed PRAGMA quick_check")
        os.replace(recovered_path, database_path)
    except Exception as exc:
        _remove_if_exists(recovered_path)
        raise DatabaseRecoveryError(
            f"SQLite database is corrupt and automatic recovery failed. "
            f"Original backup: {backup_path}. Error: {exc}"
        ) from exc
    finally:
        _remove_if_exists(salvage_path)

    return RecoveryReport(
        database_path=database_path,
        backup_path=backup_path,
        recovered_rows=recovered_rows,
        restored_from_activity=restored_from_activity,
        skipped_rows=skipped_rows,
    )


def _sqlite_path(database_uri: str, *, relative_to: str | None) -> str | None:
    url = make_url(database_uri)
    if not url.drivername.startswith("sqlite") or not url.database:
        return None
    if url.database == ":memory:":
        return None

    database_path = os.path.expanduser(url.database)
    if not os.path.isabs(database_path):
        database_path = os.path.join(relative_to or os.getcwd(), database_path)
    return os.path.abspath(database_path)


def _quick_check(database_path: str) -> bool:
    try:
        with closing(_connect_readonly(database_path)) as connection:
            row = connection.execute("PRAGMA quick_check(1)").fetchone()
            return row == ("ok",)
    except sqlite3.DatabaseError:
        return False


def _connect_readonly(database_path: str) -> sqlite3.Connection:
    uri = Path(database_path).resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.execute("PRAGMA query_only=ON")
    return connection


def _normalize_truncated_header(database_path: str) -> None:
    """Make a truncated copy readable enough for table-by-table export."""
    with open(database_path, "r+b") as database_file:
        header = database_file.read(100)
        if len(header) < 100 or header[:16] != SQLITE_HEADER:
            raise DatabaseRecoveryError("file does not have a valid SQLite header")

        encoded_page_size = struct.unpack(">H", header[16:18])[0]
        page_size = 65536 if encoded_page_size == 1 else encoded_page_size
        if page_size < 512 or page_size > 65536 or page_size & (page_size - 1):
            raise DatabaseRecoveryError(f"invalid SQLite page size: {page_size}")

        file_size = os.fstat(database_file.fileno()).st_size
        actual_pages = file_size // page_size
        if actual_pages < 1:
            raise DatabaseRecoveryError("SQLite file does not contain a complete page")

        complete_size = actual_pages * page_size
        if complete_size != file_size:
            database_file.truncate(complete_size)

        declared_pages = struct.unpack(">I", header[28:32])[0]
        if declared_pages != actual_pages:
            database_file.seek(28)
            database_file.write(struct.pack(">I", actual_pages))
            database_file.flush()
            os.fsync(database_file.fileno())


def _copy_readable_data(
    source_path: str,
    destination_path: str,
) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    recovered_rows: dict[str, int] = {}
    skipped_primary_keys: dict[str, list[tuple[Any, ...]]] = {}
    source = _connect_readonly(source_path)
    destination = sqlite3.connect(destination_path)
    try:
        destination.execute("PRAGMA foreign_keys=OFF")
        destination.execute("PRAGMA journal_mode=DELETE")
        destination.execute("PRAGMA synchronous=FULL")

        schema_rows = source.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE name NOT LIKE 'sqlite_%' AND sql IS NOT NULL
            ORDER BY
                CASE type
                    WHEN 'table' THEN 0
                    WHEN 'index' THEN 1
                    WHEN 'view' THEN 2
                    WHEN 'trigger' THEN 3
                    ELSE 4
                END,
                name
            """
        ).fetchall()
        tables = [row for row in schema_rows if row[0] == "table"]
        deferred_schema = [row for row in schema_rows if row[0] != "table"]

        destination.execute("BEGIN")
        for _object_type, _name, sql in tables:
            destination.execute(sql)

        for _object_type, table_name, _sql in tables:
            quoted_table = _quote_identifier(table_name)
            row_count, skipped_keys = _copy_table_rows(
                source,
                destination,
                table_name,
                quoted_table,
            )
            recovered_rows[table_name] = row_count
            if skipped_keys:
                skipped_primary_keys[table_name] = skipped_keys

        restored_from_activity = _restore_from_activity_snapshots(
            destination,
            skipped_primary_keys,
        )
        for table_name, restored_count in restored_from_activity.items():
            recovered_rows[table_name] += restored_count

        for _object_type, _name, sql in deferred_schema:
            destination.execute(sql)

        destination.commit()
    except Exception:
        destination.rollback()
        raise
    finally:
        source.close()
        destination.close()

    skipped_rows = {
        table_name: len(keys) - restored_from_activity.get(table_name, 0)
        for table_name, keys in skipped_primary_keys.items()
        if len(keys) - restored_from_activity.get(table_name, 0) > 0
    }
    return recovered_rows, restored_from_activity, skipped_rows


def _copy_table_rows(
    source: sqlite3.Connection,
    destination: sqlite3.Connection,
    table_name: str,
    quoted_table: str,
) -> tuple[int, list[tuple[Any, ...]]]:
    cursor = source.execute(f"SELECT * FROM {quoted_table}")
    column_count = len(cursor.description or ())
    placeholders = ",".join("?" for _ in range(column_count))
    insert_sql = f"INSERT INTO {quoted_table} VALUES ({placeholders})"

    destination.execute("SAVEPOINT copy_table")
    row_count = 0
    try:
        while True:
            rows = cursor.fetchmany(500)
            if not rows:
                break
            destination.executemany(insert_sql, rows)
            row_count += len(rows)
        destination.execute("RELEASE copy_table")
        return row_count, []
    except sqlite3.DatabaseError:
        destination.execute("ROLLBACK TO copy_table")
        destination.execute("RELEASE copy_table")

    primary_key = _primary_key_index(source, table_name, quoted_table)
    if primary_key is None:
        raise DatabaseRecoveryError(
            f"table {table_name!r} is damaged and has no readable primary-key index"
        )

    index_name, columns = primary_key
    quoted_index = _quote_identifier(index_name)
    quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
    key_cursor = source.execute(
        f"SELECT {quoted_columns} FROM {quoted_table} "
        f"INDEXED BY {quoted_index} ORDER BY {quoted_columns}"
    )

    keys: list[tuple[Any, ...]] = []
    while True:
        rows = key_cursor.fetchmany(500)
        if not rows:
            break
        keys.extend(tuple(row) for row in rows)

    predicates = " AND ".join(
        f"{_quote_identifier(column)} IS ?" for column in columns
    )
    select_sql = (
        f"SELECT * FROM {quoted_table} INDEXED BY {quoted_index} "
        f"WHERE {predicates}"
    )
    skipped_keys: list[tuple[Any, ...]] = []
    row_count = 0
    for key in keys:
        try:
            row = source.execute(select_sql, key).fetchone()
        except sqlite3.DatabaseError:
            skipped_keys.append(key)
            continue
        if row is None:
            skipped_keys.append(key)
            continue
        destination.execute(insert_sql, row)
        row_count += 1

    return row_count, skipped_keys


def _primary_key_index(
    source: sqlite3.Connection,
    table_name: str,
    quoted_table: str,
) -> tuple[str, list[str]] | None:
    indexes = source.execute(f"PRAGMA index_list({quoted_table})").fetchall()
    primary_index = next((row for row in indexes if row[3] == "pk"), None)
    if primary_index is None:
        return None

    index_name = primary_index[1]
    quoted_index = _quote_identifier(index_name)
    columns = [
        row[2]
        for row in source.execute(f"PRAGMA index_info({quoted_index})").fetchall()
        if row[2] is not None
    ]
    if not columns:
        return None
    return index_name, columns


def _restore_from_activity_snapshots(
    destination: sqlite3.Connection,
    skipped_primary_keys: dict[str, list[tuple[Any, ...]]],
) -> dict[str, int]:
    if "activities" not in {
        row[0]
        for row in destination.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }:
        return {}

    action_tables = {
        "project_created": "projects",
        "project_updated": "projects",
        "node_created": "nodes",
        "node_updated": "nodes",
        "node_moved": "nodes",
        "node_deleted": "nodes",
        "status_changed": "nodes",
        "evidence_added": "evidences",
        "artifact_added": "artifacts",
        "checkpoint_created": "checkpoints",
    }
    snapshots: dict[tuple[str, str], dict[str, Any]] = {}
    activity_rows = destination.execute(
        """
        SELECT action_type, before_json, after_json, created_at
        FROM activities
        ORDER BY created_at, rowid
        """
    ).fetchall()
    for action_type, before_json, after_json, created_at in activity_rows:
        table_name = action_tables.get(action_type)
        if not table_name:
            continue

        raw_snapshot = after_json
        deleted_at = None
        if action_type == "node_deleted":
            raw_snapshot = before_json
            deleted_at = created_at
        if not raw_snapshot:
            continue
        try:
            snapshot = json.loads(raw_snapshot)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(snapshot, dict) or not snapshot.get("id"):
            continue
        if deleted_at:
            snapshot["deleted_at"] = deleted_at
        snapshots[(table_name, str(snapshot["id"]))] = snapshot

    restored: dict[str, int] = {}
    for table_name, keys in skipped_primary_keys.items():
        if table_name not in {"projects", "nodes", "evidences", "artifacts", "checkpoints"}:
            continue
        for key in keys:
            if len(key) != 1:
                continue
            snapshot = snapshots.get((table_name, str(key[0])))
            if not snapshot:
                continue
            if _insert_snapshot(destination, table_name, snapshot):
                restored[table_name] = restored.get(table_name, 0) + 1
    return restored


def _insert_snapshot(
    destination: sqlite3.Connection,
    table_name: str,
    snapshot: dict[str, Any],
) -> bool:
    values = dict(snapshot)
    if table_name == "nodes" and isinstance(values.get("tags"), list):
        values["tags"] = ",".join(str(tag) for tag in values["tags"])
    if table_name == "checkpoints":
        for source_name, column_name in (
            ("completed", "completed_json"),
            ("in_progress", "in_progress_json"),
            ("next", "next_json"),
            ("blockers", "blockers_json"),
            ("risks", "risks_json"),
            ("related_node_ids", "related_node_ids_json"),
        ):
            if source_name in values:
                values[column_name] = json.dumps(values.pop(source_name), ensure_ascii=False)

    quoted_table = _quote_identifier(table_name)
    table_columns = {
        row[1]
        for row in destination.execute(f"PRAGMA table_info({quoted_table})").fetchall()
    }
    columns = [column for column in values if column in table_columns]
    if "id" not in columns:
        return False

    quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
    placeholders = ", ".join("?" for _ in columns)
    cursor = destination.execute(
        f"INSERT OR IGNORE INTO {quoted_table} ({quoted_columns}) "
        f"VALUES ({placeholders})",
        [values[column] for column in columns],
    )
    return cursor.rowcount == 1


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _available_path(preferred_path: str) -> str:
    if not os.path.exists(preferred_path):
        return preferred_path
    counter = 1
    while True:
        candidate = f"{preferred_path}.{counter}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def _remove_if_exists(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
