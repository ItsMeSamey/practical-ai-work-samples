"""Teaching example: atomically persist an import and its retry receipt."""
import json
import sqlite3
import uuid


class KeyConflict(ValueError):
    """The caller reused a key for a different request."""


def connect(path):
    db = sqlite3.connect(path, isolation_level=None)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS receipts (
            request_key TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            result TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS items (
            import_id TEXT NOT NULL,
            position INTEGER NOT NULL,
            name TEXT NOT NULL,
            PRIMARY KEY (import_id, position)
        );
    """)
    return db


def import_names(db, request_key, names, *, before_commit=None,
                 lose_response=False):
    """A list of names is the entire request; list order is significant.

    Fault hooks let tests distinguish failure before commit from lost delivery
    after commit. They are teaching aids, not application API features.
    """
    if not isinstance(request_key, str) or not request_key:
        raise ValueError("a nonempty string key is required")
    if not isinstance(names, list) or any(not isinstance(n, str) for n in names):
        raise ValueError("names must be a list of strings")
    payload = json.dumps(names, ensure_ascii=True, separators=(",", ":"))
    db.execute("BEGIN IMMEDIATE")
    try:
        prior = db.execute(
            "SELECT payload, result FROM receipts WHERE request_key = ?",
            (request_key,),
        ).fetchone()
        if prior:
            if prior[0] != payload:
                raise KeyConflict("key already belongs to a different request")
            result = json.loads(prior[1])
        else:
            result = {"import_id": uuid.uuid4().hex, "count": len(names)}
            db.executemany(
                "INSERT INTO items VALUES (?, ?, ?)",
                [(result["import_id"], i, name) for i, name in enumerate(names)],
            )
            db.execute("INSERT INTO receipts VALUES (?, ?, ?)",
                       (request_key, payload, json.dumps(result, sort_keys=True)))
            if before_commit is not None:
                before_commit()
        db.commit()
    except BaseException:
        db.rollback()
        raise
    # The transaction is already committed: this error cannot undo it.
    if lose_response:
        raise TimeoutError("simulated response lost after commit")
    return result
