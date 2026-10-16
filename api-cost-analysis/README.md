# API cost comparison sample

Original AI-produced editorial research, dated 16 October 2026. Three ways a headline per-token price can mislead: tokenizer changes, effective dates and output mix. No claim of equivalent model quality, measured bills or real-world savings.

- api-cost-analysis.pdf: two-page brief.
- cost-comparison.svg: standalone vector figure.
- rates.csv: five official rate observations, units, effective periods and sources.
- scenarios.csv: seven aggregate-token accounting scenarios.
- provenance.json: verification window, sources, assumptions and time basis.
- reproduce.py: Python standard library only; rebuilds PDF, SVG and CSVs and checks seven calculations using Decimal.

Run python reproduce.py in this directory. PDF and SVG use the same drawing records. Chart panels use separate scales; compare lengths only within a panel.

No paid API requests, tokenization or model-quality benchmarks were run. A separate AI agent checked source interpretation and arithmetic; this is not a claim of human review. This is a work sample, not commissioned client work. Prices and availability can change; recheck primary sources before reuse.
