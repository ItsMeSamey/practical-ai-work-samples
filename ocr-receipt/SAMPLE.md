# Validate receipt totals after local OCR

OCR turns pixels into text. A useful receipt workflow also needs a decision: can this extraction proceed, or does it need review? Start by defining what you can verify independently of the OCR model.

This small Python example generates a synthetic receipt image, reads it using RapidOCR locally, then validates its subtotal, tax, currency, and total. The input is labeled as a test receipt and contains no customer data. You can inspect the image, every recognized line, its confidence, and the final JSON.

## Give the tutorial a known answer

The receipt generator draws two items, a subtotal of USD 12.50, tax of USD 1.00, and a total of USD 13.50. That reference comes from the fixture, so the OCR result can be compared with an independently specified expectation. Keeping the source fixture matters: a plausible-looking transcription is difficult to assess without the original image.

The executable example is in `receipt_demo.py`. It uses Pillow to generate the PNG and `rapidocr_onnxruntime.RapidOCR` to recognize it. The package includes OCR models; no API key is needed. Package installation downloads dependencies, while the demonstration processes the image locally.

Run the pinned environment and example as described in README.md. The output includes:

```json
{
  "currency": "USD",
  "subtotal": "12.50",
  "tax": "1.00",
  "total": "13.50"
}
```

## Define the acceptance boundary

For this deliberately narrow input format, each monetary line must contain exactly one supported label and a number with two fractional digits. The parser rejects missing fields and duplicate labels. A recognized label with an ambiguous amount, such as `TOTAL 13.5O`, also fails; the code never silently changes the letter `O` into a zero.

Currency must appear exactly once and be explicitly USD. That constraint is part of the tutorial's input contract, rather than a claim that all receipts use this format.

The final check adds `Decimal` values:

```python
if Decimal(values['subtotal']) + Decimal(values['tax']) != Decimal(values['total']):
    raise ValueError('subtotal plus tax does not equal total')
```

Constructing decimals from the recognized strings preserves decimal arithmetic for these amounts. The test suite includes `0.10 + 0.20 = 0.30`, along with missing, duplicated, malformed, inconsistent, and conflicting-currency cases.

## Preserve evidence before making a decision

The example writes `ocr.txt` and `ocr-lines.json` before extraction. If validation fails, those files help explain what the model saw. Confidence remains attached to each line, but this example does not choose a confidence threshold: a threshold would need calibration against representative labeled inputs.

On the recorded run, the three monetary fields and currency matched the single synthetic fixture. All twelve validation tests passed. That is enough to show this tutorial works in the recorded environment; it does not estimate accuracy on photographed receipts or compare OCR engines.

For a real deployment, collect a separately labeled evaluation set with representative languages, layouts, image quality, and currencies. Measure field-level correctness and the rate at which invalid extractions escape validation. An arithmetic check can still accept a wrong but internally consistent transcription. Tips, discounts, refunds, and line-item totals also need explicit rules. Keep those cases out of automatic posting until the input contract and tests cover them.

References: [RapidOCR package](https://pypi.org/project/rapidocr-onnxruntime/), [upstream project](https://github.com/RapidAI/RapidOCR), [Python decimal arithmetic](https://docs.python.org/3/library/decimal.html).

*Original sample created with AI assistance and reviewed by AI agents. Code execution is recorded in the accompanying artifacts; no human editing or client publication is claimed.*
