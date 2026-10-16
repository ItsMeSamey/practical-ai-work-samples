"""Synthetic local FAQ state machine. No network or external delivery."""
import json
import sqlite3
from contextlib import contextmanager


class PayloadConflict(ValueError):
    pass


class Router:
    def __init__(self, path, approved):
        self.approved = dict(approved)
        if not all(isinstance(k, str) and isinstance(v, str) and k.strip() and v.strip()
                   for k, v in self.approved.items()):
            raise ValueError("FAQ keys and answers must be nonempty strings")
        self.db = sqlite3.connect(path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS contacts (
            sender TEXT PRIMARY KEY, state TEXT NOT NULL
            CHECK(state IN ('active','handoff','stopped')));
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY, payload TEXT NOT NULL, outcome TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY, message_id TEXT NOT NULL UNIQUE
            REFERENCES messages(id), sender TEXT NOT NULL REFERENCES contacts(sender),
            answer TEXT NOT NULL, state TEXT NOT NULL
            CHECK(state IN ('pending','processing','done','cancelled')));
        """)

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def ingest(self, event):
        if not isinstance(event, dict) or set(event) != {'id', 'sender', 'text'}:
            raise ValueError("Expected exactly id, sender, text")
        if not all(isinstance(v, str) and v.strip() for v in event.values()):
            raise ValueError("Fields must be nonempty strings")
        if any(len(v) > 4096 for v in event.values()):
            raise ValueError("Field exceeds local demo limit")
        payload = json.dumps(event, sort_keys=True, separators=(',', ':'))
        with self.transaction():
            old = self.db.execute("SELECT * FROM messages WHERE id=?", (event['id'],)).fetchone()
            if old:
                if old['payload'] != payload:
                    raise PayloadConflict("Message ID reused with changed payload")
                return {'duplicate': True, 'outcome': old['outcome']}
            sender, text = event['sender'], event['text'].strip().casefold()
            self.db.execute("INSERT OR IGNORE INTO contacts VALUES (?, 'active')", (sender,))
            state = self.db.execute("SELECT state FROM contacts WHERE sender=?", (sender,)).fetchone()[0]
            answer = None
            if text == 'stop':
                outcome, state = 'stopped', 'stopped'
            elif state != 'active':
                outcome = 'suppressed_' + state
            elif text in self.approved:
                outcome, answer = 'queued', self.approved[text]
            else:
                outcome, state = 'handoff', 'handoff'
            self.db.execute("UPDATE contacts SET state=? WHERE sender=?", (state, sender))
            if state != 'active':
                self.db.execute("UPDATE outbox SET state='cancelled' WHERE sender=? AND state='pending'", (sender,))
            self.db.execute("INSERT INTO messages VALUES (?,?,?)", (event['id'], payload, outcome))
            if answer is not None:
                self.db.execute("INSERT INTO outbox(message_id,sender,answer,state) VALUES (?,?,?,'pending')",
                                (event['id'], sender, answer))
            return {'duplicate': False, 'outcome': outcome}

    def take(self):
        """Claim one local item atomically; caller never sends it externally here."""
        with self.transaction():
            row = self.db.execute("SELECT o.* FROM outbox o JOIN contacts c ON c.sender=o.sender "
                                  "WHERE o.state='pending' AND c.state='active' ORDER BY o.id LIMIT 1").fetchone()
            if row is None:
                return None
            self.db.execute("UPDATE outbox SET state='processing' WHERE id=?", (row['id'],))
            return dict(row) | {'state': 'processing'}

    def acknowledge_local(self, item_id):
        with self.transaction():
            changed = self.db.execute("UPDATE outbox SET state='done' WHERE id=? AND state='processing'", (item_id,)).rowcount
            if changed != 1:
                raise ValueError("Item is not processing")

    def snapshot(self):
        return {table: [dict(r) for r in self.db.execute('SELECT * FROM ' + table)]
                for table in ('contacts', 'messages', 'outbox')}
