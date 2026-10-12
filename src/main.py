import argparse
import sys

from src.config import DEFAULT_QUARTER, TOP_N_PRODUCTS
from src.excel_writer import PackWriter
from src.load import SalesDataLoader
from src.metrics import QuarterlyMetrics


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--quarter", default=DEFAULT_QUARTER)
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    loader = SalesDataLoader(raw_data_dir=args.input)
    sales = loader.load_reseller_sales()
    quota = loader.load_sales_quota()

    metrics = QuarterlyMetrics(sales, quota, args.quarter)
    quota_by_salesperson = metrics.quota_by_salesperson()
    quota_by_territory = metrics.quota_by_territory()
    margin_by_category = metrics.margin_by_category()
    prior_year_comparison = metrics.prior_year_comparison()
    top_bottom_products = metrics.top_bottom_products(TOP_N_PRODUCTS)
    quota_trend = metrics.quota_trend()
    reconciliation = metrics.reconcile()

    recon = reconciliation.set_index("stage")
    assert recon.loc["used", "n_rows"] + recon.loc["excluded", "n_rows"] == recon.loc["raw", "n_rows"]
    assert abs(margin_by_category["sales"].sum() - recon.loc["used", "total_value"]) < 0.01

    pack = PackWriter(args.output)
    pack.write_summary(args.quarter, prior_year_comparison, quota_trend, quota_by_salesperson)
    pack.write_quota_performance(quota_by_salesperson, quota_by_territory)
    pack.write_product_margin(margin_by_category, top_bottom_products)
    pack.write_reconciliation(reconciliation)
    pack.write_notes(args.quarter)
    pack.close()

    print(f"Wrote {args.output} for {args.quarter}")


def main(argv=None) -> None:
    run(parse_args(argv))


if __name__ == "__main__":
    main(sys.argv[1:])
