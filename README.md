# Quarterly Sales vs Quota Reporting Pack

A one-command tool that builds a quarterly Excel pack (actual vs quota, product margin, reconciled to source) from AdventureWorks sample data. Simulated business scenario.

**Sample output:** [output/sample_quarterly_pack.xlsx](output/sample_quarterly_pack.xlsx)
![Summary sheet](docs/screenshots/summary.png)

## Key results (2013Q3)
- Reseller sales $7,644,680, 73.8% of quota, up 31.5% vs. the same quarter last year.
- Gross margin just 0.3%: Bikes are 86% of volume and ran at -1.1% margin this quarter.
- Best territory: Northeast (87.8% attainment). Worst: Germany (61.8%).

Full write-up: [docs/management_summary.md](docs/management_summary.md)

## Data
[AdventureWorksDW sample data](https://github.com/sripathikrishnan/adventureworks) (MIT licence). Place the CSVs in `data/raw/`.

## How to run
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.main --input data/raw --output output/quarterly_pack.xlsx --quarter 2013Q3
pytest
```

## Repository structure
```
quarterly-sales-vs-quota-pack/
├── README.md
├── requirements.txt
├── data/raw/                   (gitignored, put the CSV export here)
├── src/
│   ├── config.py
│   ├── load.py
│   ├── metrics.py
│   ├── excel_writer.py
│   └── main.py
├── tests/test_metrics.py
├── output/sample_quarterly_pack.xlsx
├── notebooks/01_exploration.ipynb
└── docs/
    ├── management_summary.md
    └── screenshots/
```
