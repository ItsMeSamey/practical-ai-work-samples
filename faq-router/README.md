# Approved FAQ router: synthetic local proof

An independently built portfolio demonstration, not previous client delivery or a production WhatsApp bot. Python standard library only; no network calls, Meta integration, external messages, credentials or customer data.

Run from this folder: `PYTHONDONTWRITEBYTECODE=1 python -m unittest -v`.

The approved FAQ table is passed to `Router`. Synthetic events contain exactly `id`, `sender`, `text`. Matching is exact after trimming/case-folding incoming text; approved keys must already be stripped and casefolded (`key.strip().casefold()`). Unknown questions move a sender to handoff. STOP disables automated answers. Both cancel pending answers and suppress subsequent FAQ events. Separate senders remain isolated. A repeated identical message ID reuses its original outcome; a changed payload with that ID is rejected without changing state.

SQLite persists contacts, inbound receipts and a local outbox. Each ingest/claim is an immediate transaction; the inbound ID and queue message ID have unique constraints. `take()` atomically marks one pending item processing. `acknowledge_local()` records local completion; it does NOT confirm any external delivery. No sender API exists.

## Limits

- No verified Meta webhook/signature, WhatsApp policy/session/template handling, authentication, hosting, monitoring, human operator UI, CRM, booking, payment or send adapter.
- No exactly-once external delivery claim. An item already taken may be in flight when STOP/handoff arrives; this demo cannot retract it. Only pending items are cancelled.
- An unacknowledged processing item stays processing across restart, requiring manual investigation. Automatic retries would risk duplicate external effects and are deliberately absent.
- Handoff and stopped states have no automatic reset or START mechanism. Configuration is caller supplied, not a managed FAQ approval/versioning product.
- Local synthetic tests establish transaction/state behavior, not remote service availability, production throughput or end-to-end delivery.

## Executed validation

On 2026-10-16, the author ran the seven-test suite successfully in 2.927 seconds. An independent AI reviewer inspected the code and limitations, then reran all seven tests successfully in 1.808 seconds. The reviewer also executed a bounded eight-thread duplicate-ingest check (one new receipt, seven duplicates, one outbox item) and eight simultaneous queue claims (one claimant). Those additional checks were executed inline, not retained as suite tests. No material issue was found within this local synthetic scope. These single-run checks are not a load or production guarantee.

## Minimal local example

```python
from faq import Router
r = Router("synthetic-state.sqlite", {"hours": "Mon-Fri 09:00-17:00"})
print(r.ingest({"id": "synthetic-1", "sender": "synthetic-alice", "text": "hours"}))
item = r.take()
print(item)  # inspect locally; no message is sent
r.acknowledge_local(item["id"])
r.close()
```

Keep this example database local. The tests create and remove their synthetic databases inside this folder.
