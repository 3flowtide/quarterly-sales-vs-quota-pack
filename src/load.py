from pathlib import Path

import pandas as pd

from src.config import CACHE_DIR, RAW_DATA_DIR, TABLE_FILES

COLUMNS = {
    "fact_reseller_sales": [
        "ProductKey", "OrderDateKey", "DueDateKey", "ShipDateKey", "ResellerKey",
        "EmployeeKey", "PromotionKey", "CurrencyKey", "SalesTerritoryKey",
        "SalesOrderNumber", "SalesOrderLineNumber", "RevisionNumber", "OrderQuantity",
        "UnitPrice", "ExtendedAmount", "UnitPriceDiscountPct", "DiscountAmount",
        "ProductStandardCost", "TotalProductCost", "SalesAmount", "TaxAmt", "Freight",
        "CarrierTrackingNumber", "CustomerPONumber", "OrderDate", "DueDate", "ShipDate",
    ],
    "fact_sales_quota": [
        "SalesQuotaKey", "EmployeeKey", "DateKey", "CalendarYear", "CalendarQuarter",
        "SalesAmountQuota", "QuotaDate",
    ],
    "dim_product": [
        "ProductKey", "ProductAlternateKey", "ProductSubcategoryKey",
        "WeightUnitMeasureCode", "SizeUnitMeasureCode", "EnglishProductName",
        "SpanishProductName", "FrenchProductName", "StandardCost", "FinishedGoodsFlag",
        "Color", "SafetyStockLevel", "ReorderPoint", "ListPrice", "Size", "SizeRange",
        "Weight", "DaysToManufacture", "ProductLine", "DealerPrice", "Class", "Style",
        "ModelName", "LargePhoto", "EnglishDescription", "FrenchDescription",
        "ChineseDescription", "ArabicDescription", "HebrewDescription", "ThaiDescription",
        "GermanDescription", "JapaneseDescription", "TurkishDescription", "StartDate",
        "EndDate", "Status",
    ],
    "dim_product_subcategory": [
        "ProductSubcategoryKey", "ProductSubcategoryAlternateKey",
        "EnglishProductSubcategoryName", "SpanishProductSubcategoryName",
        "FrenchProductSubcategoryName", "ProductCategoryKey",
    ],
    "dim_product_category": [
        "ProductCategoryKey", "ProductCategoryAlternateKey", "EnglishProductCategoryName",
        "SpanishProductCategoryName", "FrenchProductCategoryName",
    ],
    "dim_sales_territory": [
        "SalesTerritoryKey", "SalesTerritoryAlternateKey", "SalesTerritoryRegion",
        "SalesTerritoryCountry", "SalesTerritoryGroup", "SalesTerritoryImage",
    ],
    "dim_employee": [
        "EmployeeKey", "ParentEmployeeKey", "EmployeeNationalIDAlternateKey",
        "ParentEmployeeNationalIDAlternateKey", "SalesTerritoryKey", "FirstName",
        "LastName", "MiddleName", "NameStyle", "Title", "HireDate", "BirthDate",
        "LoginID", "EmailAddress", "Phone", "MaritalStatus", "EmergencyContactName",
        "EmergencyContactPhone", "SalariedFlag", "Gender", "PayFrequency", "BaseRate",
        "VacationHours", "SickLeaveHours", "CurrentFlag", "SalesPersonFlag",
        "DepartmentName", "StartDate", "EndDate", "Status", "EmployeePhoto",
    ],
    "dim_date": [
        "DateKey", "FullDateAlternateKey", "DayNumberOfWeek", "EnglishDayNameOfWeek",
        "SpanishDayNameOfWeek", "FrenchDayNameOfWeek", "DayNumberOfMonth",
        "DayNumberOfYear", "WeekNumberOfYear", "EnglishMonthName", "SpanishMonthName",
        "FrenchMonthName", "MonthNumberOfYear", "CalendarQuarter", "CalendarYear",
        "CalendarSemester", "FiscalQuarter", "FiscalYear", "FiscalSemester",
    ],
}


class SalesDataLoader:
    def __init__(self, raw_data_dir: Path = RAW_DATA_DIR):
        self.raw_data_dir = Path(raw_data_dir)

    def read_table(self, name: str) -> pd.DataFrame:
        path = self.raw_data_dir / TABLE_FILES[name]
        # NA is literal
        return pd.read_csv(path, sep="|", header=None, names=COLUMNS[name],
                            keep_default_na=False, na_values=[""])

    def load_reseller_sales(self) -> pd.DataFrame:
        sales = self.read_table("fact_reseller_sales")
        sales["OrderDate"] = pd.to_datetime(sales["OrderDate"])

        product = self.read_table("dim_product")[
            ["ProductKey", "ProductSubcategoryKey", "EnglishProductName"]
        ]
        subcategory = self.read_table("dim_product_subcategory")[
            ["ProductSubcategoryKey", "EnglishProductSubcategoryName", "ProductCategoryKey"]
        ]
        category = self.read_table("dim_product_category")[
            ["ProductCategoryKey", "EnglishProductCategoryName"]
        ]
        territory = self.read_table("dim_sales_territory")[
            ["SalesTerritoryKey", "SalesTerritoryRegion", "SalesTerritoryCountry"]
        ]
        employee = self.read_table("dim_employee")[
            ["EmployeeKey", "FirstName", "LastName"]
        ]
        date = self.read_table("dim_date")[["DateKey", "CalendarYear", "CalendarQuarter"]]

        sales = sales.merge(product, on="ProductKey", how="left")
        sales = sales.merge(subcategory, on="ProductSubcategoryKey", how="left")
        sales = sales.merge(category, on="ProductCategoryKey", how="left")
        sales = sales.merge(territory, on="SalesTerritoryKey", how="left")
        sales = sales.merge(employee, on="EmployeeKey", how="left")
        sales = sales.merge(date, left_on="OrderDateKey", right_on="DateKey", how="left")

        sales["employee_name"] = sales["FirstName"] + " " + sales["LastName"]
        return sales

    def load_sales_quota(self) -> pd.DataFrame:
        quota = self.read_table("fact_sales_quota")
        employee = self.read_table("dim_employee")[
            ["EmployeeKey", "FirstName", "LastName", "SalesTerritoryKey"]
        ]
        territory = self.read_table("dim_sales_territory")[
            ["SalesTerritoryKey", "SalesTerritoryRegion"]
        ]
        quota = quota.merge(employee, on="EmployeeKey", how="left")
        quota = quota.merge(territory, on="SalesTerritoryKey", how="left")
        quota["employee_name"] = quota["FirstName"] + " " + quota["LastName"]
        return quota

    def cache_parquet(self, df: pd.DataFrame, name: str) -> Path:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CACHE_DIR / f"{name}.parquet"
        df.to_parquet(path, index=False)
        return path
