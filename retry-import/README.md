# Retry-safe SQLite import demo

A small, original teaching example produced with AI assistance. It demonstrates
how an import can commit successfully while its response is lost, and how a
retry can return the stored result without inserting the rows again.

Python 3 standard library only. No network calls, external services, or dependencies.

```sh
python3 -B -m unittest -v
```

The five tests verify:

- An identical request key and ordered list returns the original receipt.
- A simulated lost response occurs after commit; retry preserves one import.
- Reusing a key with a changed payload raises a conflict.
- Failure before commit rolls back both imported rows and the receipt.
- A new Python process and SQLite connection can retrieve the stored receipt.

The importer stores rows and their receipt in one transaction. Test fault hooks
make the before/after commit boundary explicit. Temporary databases are created
inside the working directory and cleaned up by the tests.

## What this proves

These tests demonstrate the behavior above for a tiny local SQLite example.
They are not evidence of client deliveries, production use, performance,
concurrent-request qualification, or experience with a particular business system.
The response failure is simulated; no actual HTTP transport is implemented.

## Limits

Not production ready. Keys have no tenant scope or expiration policy. A different
key can repeat the same business import. List order is significant. SQLite writers
are serialized with BEGIN IMMEDIATE. There is no authentication, external side-effect
coordination, scheduling, crash/power-loss simulation, schema migration, or
production-database integration. A real service needs its own data contract,
backup/recovery plan, error handling and acceptance tests.

## Verification

Previously, the original teaching sample passed five tests. This curated copy was
freshly executed separately; all five tests passed (exit 0). The source files are
unchanged copies, and no additional implementation was built for this package.

MIT licensed; see LICENSE.
