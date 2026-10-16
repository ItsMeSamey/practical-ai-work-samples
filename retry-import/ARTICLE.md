# The import succeeded. The response disappeared. What should a retry do?

*An AI-authored teaching article prepared by Sanyam Singh’s AI assistant. The example is a local SQLite demonstration, not a client delivery or a production incident.*

A timeout tells a caller that it did not receive a result. It does not tell the caller whether the database accepted the work. That uncertainty makes a simple import surprisingly easy to duplicate: send two names, lose the success response, then send the same names again. If both attempts insert independently, the database now contains four rows.

The example here gives a request a stable key and stores its result alongside its imported rows. After the first commit, a retry with that key and the same ordered payload returns the saved result. It does not create a second import. A changed payload with the same key raises a conflict. Those are specific, testable behaviors; they do not establish universal exactly-once processing.

## Define the request before defining the retry

The complete request in this demo is a nonempty string key plus a Python list of strings. The key identifies the caller’s operation. The list supplies its content. Order matters: `["Ada", "Grace"]` and `["Grace", "Ada"]` are different requests, even though they contain the same names.

`importer.py` serializes the list using compact JSON with ASCII escaping. The receipt stores this serialized payload, rather than trusting the key alone. On a repeated key, the implementation compares the stored payload with the newly serialized list. If they differ, `KeyConflict` stops the call. This prevents accidental key reuse from silently returning the result of unrelated work.

The data contract remains deliberately small. It accepts an empty list, duplicate names, and empty strings. It has no maximum request size or business identity checks. A real importer must decide whether those inputs make sense before borrowing this pattern.

## Put the evidence of completion in the same transaction

The database contains two tables. `items` holds an import identifier, a position, and a name. `receipts` holds the request key, serialized payload, and serialized result. The result contains the generated import identifier and the number of names.

The function starts `BEGIN IMMEDIATE`, checks for a receipt, and either retrieves the saved result or writes a new import and receipt. It then commits. An exception inside that transaction triggers a rollback. The important boundary is that the receipt is not a second, later bookkeeping operation: the imported rows and the receipt are committed together.

Consider two weaker arrangements. Writing the rows first and the receipt in a later transaction leaves a gap in which rows exist without retry evidence. A repeated request could insert again. Saving a successful receipt first creates the opposite risk: a retry could report success even though the corresponding row writes never committed. These are failure scenarios to reason about, not additional implementations benchmarked by this demo.

SQLite documents that `BEGIN IMMEDIATE` starts a write transaction immediately and can fail when another writer is active. The demo does not implement a busy-retry policy or qualify concurrent workloads. Its test suite checks sequential calls and one subsequent process. See [SQLite transaction control](https://www.sqlite.org/lang_transaction.html) for the underlying behavior.

## Reproduce the ambiguous outcome

Use the accompanying [retry-import source directory](./) containing `importer.py` and `test_importer.py`. From that directory, run the following with Python 3 and its standard-library `sqlite3` module. No package installation or network service is required. The temporary database is created under the working directory and removed afterward.

```python
import tempfile
from pathlib import Path
from importer import connect, import_names, KeyConflict

with tempfile.TemporaryDirectory(dir=".") as work:
    db = connect(str(Path(work) / "demo.sqlite"))
    try:
        try:
            import_names(db, "batch-1", ["Ada", "Grace"],
                         lose_response=True)
        except TimeoutError:
            print("response lost after commit")
        receipt = import_names(db, "batch-1", ["Ada", "Grace"])
        print("receipt count:", receipt["count"])
        print("stored rows:", db.execute(
            "SELECT count(*) FROM items").fetchone()[0])
        try:
            import_names(db, "batch-1", ["Grace", "Ada"])
        except KeyConflict:
            print("changed payload rejected")
    finally:
        db.close()
```

The expected output is:

```text
response lost after commit
receipt count: 2
stored rows: 2
changed payload rejected
```

`lose_response=True` raises a `TimeoutError` after the commit. It is an explicit fault hook, not an HTTP client or a real dropped connection. The retry reads the receipt that already exists. The random import identifier is intentionally omitted from the printed output, so the observable example stays stable across runs.

## Test the other side of the boundary

A failure before commit must behave differently. The `before_commit` test hook runs after both tables have been written but before commit. The existing test raises there, verifies that neither table retains rows, checks that the connection has left the transaction, then retries successfully.

Run the accompanying suite with:

```sh
python3 -B -m unittest -v
```

Its five tests cover an ordinary identical retry, a simulated lost response, changed-payload rejection with the original request still retriable, rollback before commit, and receipt recovery from a new Python process and connection. The last test closes the original connection before the subprocess opens the database. It demonstrates that the saved receipt is not merely an in-memory cache. It does not simulate an operating-system crash or power loss.

## Keep the guarantee inside its actual boundary

The key is part of the caller’s recovery protocol. Generating a fresh key for every retry bypasses it: a different key creates another import even when the list is identical. Losing the original key also loses the caller’s straightforward way to retrieve that receipt.

The receipt table has no tenant namespace, expiry, retention limit, or access control. A service must define who owns a key and how long it remains retriable. The connection also needs to be outside an existing transaction when this function begins; SQLite does not allow nested `BEGIN` transactions.

An email, payment, or remote API call would sit outside this local transaction. Adding one between the SQL statements would not make that external action atomic with SQLite. Such a system needs a separate delivery and reconciliation design, with its own failure tests. This sample also makes no throughput, crash-durability, or production-readiness claim.

The useful lesson is concrete: keep the imported data and the durable answer to “did this request finish?” within one transaction, then test failures on both sides of commit. A caller can recover from an uncertain response when it preserves the request identity and the service preserves a matching receipt.
