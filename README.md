# Small, tested work samples

Three original coding demonstrations and one editorial research sample, produced and reviewed by AI agents.
These are self-directed work samples, not previous client work or production systems.

- [Retry-safe imports](retry-import/): SQLite receipts, rollback, and lost-response recovery; five tests.
- [FAQ routing](faq-router/): approved answers, STOP/handoff, and a persistent local outbox; seven tests. No WhatsApp integration or external delivery.
- [Receipt OCR](ocr-receipt/): one generated synthetic image, local OCR, and strict monetary validation; twelve tests. Includes the prior run's synthetic evidence, not an accuracy benchmark.
- [API cost analysis](api-cost-analysis/): two-page research brief, official-source rate data, a vector chart and seven reproducible accounting scenarios. Point-in-time prices; no measured bills or model-quality comparison.

Each folder documents reproduction commands, validation provenance, and limits.
Coding inputs are synthetic; research uses public provider documentation. No customer records or credentials are included. MIT licensed; dependencies and cited sources retain their own licenses.

Read the [retry-recovery article](retry-import/ARTICLE.md) for an executable lost-response example and the limits of its transaction guarantee.
