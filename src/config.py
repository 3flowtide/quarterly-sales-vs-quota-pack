from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = ROOT / "data" / "raw"
CACHE_DIR = ROOT / "data" / "cache"
OUTPUT_DIR = ROOT / "output"

TABLE_FILES = {
    "fact_reseller_sales": "FactResellerSales.csv",
    "fact_sales_quota": "FactSalesQuota.csv",
    "dim_product": "DimProduct.csv",
    "dim_product_subcategory": "DimProductSubcategory.csv",
    "dim_product_category": "DimProductCategory.csv",
    "dim_sales_territory": "DimSalesTerritory.csv",
    "dim_employee": "DimEmployee.csv",
    "dim_date": "DimDate.csv",
}

DEFAULT_QUARTER = "2013Q3"
TOP_N_PRODUCTS = 10
