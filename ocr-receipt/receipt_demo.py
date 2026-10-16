"""Synthetic receipt -> local OCR -> strict, narrow monetary validation."""
from decimal import Decimal
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / 'artifacts'
FIELDS = ('SUBTOTAL', 'TAX', 'TOTAL')
EXPECTED = {'currency': 'USD', 'subtotal': '12.50', 'tax': '1.00', 'total': '13.50'}


def extract(text):
    """Accept only this tutorial's explicit labels; never repair ambiguous digits."""
    values = {}
    for line in text.splitlines():
        line = line.strip()
        match = re.fullmatch(r'(SUBTOTAL|TAX|TOTAL)\s*:?\s+(?:USD\s+)?([0-9]+\.[0-9]{2})', line, re.I)
        if re.match(r'^(SUBTOTAL|TAX|TOTAL)\b', line, re.I) and not match:
            raise ValueError('malformed monetary field')
        if match:
            name, value = match.group(1).lower(), match.group(2)
            if name in values:
                raise ValueError(f'duplicate field: {name}')
            values[name] = value
    if set(values) != {'subtotal', 'tax', 'total'}:
        raise ValueError('missing or malformed monetary fields')
    currencies = [line.strip() for line in text.splitlines() if re.match(r'^CURRENCY\b', line.strip(), re.I)]
    if len(currencies) != 1 or not re.fullmatch(r'CURRENCY\s*:?\s+USD', currencies[0], re.I):
        raise ValueError('one explicit USD currency is required')
    if Decimal(values['subtotal']) + Decimal(values['tax']) != Decimal(values['total']):
        raise ValueError('subtotal plus tax does not equal total')
    return {'currency': 'USD', **values}


def create_receipt():
    from PIL import Image, ImageDraw, ImageFont
    ARTIFACTS.mkdir(exist_ok=True)
    image = Image.new('RGB', (1100, 1000), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=38)
    lines = [
        'SYNTHETIC TEST RECEIPT', 'NOT A REAL TRANSACTION', '',
        'Receipt: DEMO-001', 'Currency: USD', '',
        'Notebook: 7.50', 'Pen set: 5.00', '',
        'SUBTOTAL 12.50', 'TAX 1.00', 'TOTAL 13.50',
    ]
    for index, line in enumerate(lines):
        draw.text((70, 60 + index * 65), line, font=font, fill='black')
    path = ARTIFACTS / 'synthetic-receipt.png'
    image.save(path)
    return path


def main():
    from rapidocr_onnxruntime import RapidOCR
    from importlib.metadata import version
    path = create_receipt()
    # Bound native thread pools so a small tutorial cannot consume every CPU.
    engine = RapidOCR(intra_op_num_threads=1, inter_op_num_threads=1)
    result, _ = engine(str(path))
    if not result:
        raise RuntimeError('OCR returned no text')
    # RapidOCR returns detected lines with boxes, text, and confidence.
    # Preserve its original reading order and record every line for inspection.
    text = '\n'.join(row[1] for row in result)
    (ARTIFACTS / 'ocr.txt').write_text(text + '\n')
    (ARTIFACTS / 'ocr-lines.json').write_text(json.dumps([
        {'box': row[0], 'text': row[1], 'confidence': row[2]} for row in result
    ], indent=2))
    extracted = extract(text)
    if extracted != EXPECTED:
        raise AssertionError(f'known synthetic truth differs: {extracted}')
    (ARTIFACTS / 'extracted.json').write_text(json.dumps(extracted, indent=2) + '\n')
    manifest = {
        'input': 'generated synthetic fixture; no personal or customer data',
        'python': sys.version.split()[0],
        'packages': {name: version(name) for name in ['rapidocr-onnxruntime', 'onnxruntime', 'pillow']},
        'image_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'expected': EXPECTED, 'observed': extracted,
        'claim': 'one synthetic fixture passed; no real-world accuracy or throughput claim',
    }
    (ARTIFACTS / 'run.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
