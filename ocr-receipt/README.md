# Local OCR receipt validation demo

This original tutorial sample was produced with AI assistance and reviewed by AI agents. No human editing or prior client delivery/publication is claimed.

The example generates an obviously synthetic receipt, runs real local OCR, and extracts three monetary fields. It preserves raw OCR output and rejects missing, duplicated, malformed, or inconsistent values instead of guessing. No customer records, paid API, cloud account, or external OCR service are used. Installation requires package downloads.

## Reproduce

Validated on Python 3.12.15. Create an isolated environment with Python 3.12, then:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
.venv/bin/python -m unittest -v
.venv/bin/python receipt_demo.py
```

Generated evidence is under `artifacts/`: the input PNG, OCR text, OCR line boxes/confidences, extracted JSON, and a versioned run manifest. `tests.log` and `run.log` record the executed checks. The sample article is [SAMPLE.md](SAMPLE.md).

## Verified result and limits

The included logs record source-directory OCR and test execution after upgrading Pillow to 12.3.0 on 16 October 2026. The published copy preserves that evidence. One generated fixture produced subtotal `12.50`, tax `1.00`, and total `13.50`, matching its known reference. Twelve validation tests cover decimal arithmetic and rejection paths. These results establish a working tutorial example, not real-receipt accuracy, vendor superiority, production readiness, or throughput.

The parser intentionally supports one currency and three explicit line labels. It does not generalize to arbitrary layouts, line-item reconciliation, localized numbers, multi-page documents, credits, tips, discounts, or maliciously crafted receipts. The sum check cannot detect a wrong but internally consistent transcription. Those cases require a broader labeled corpus and separately specified validation rules.

Dependency/model files and caches are excluded from the public sample. The local working `.venv` is disposable and can be rebuilt from pinned requirements.

## License

Original sample code and prose are MIT licensed; see [LICENSE](LICENSE). Dependencies retain their own licenses.
