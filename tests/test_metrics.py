import pandas as pd
import pytest

from src.metrics import QuarterlyMetrics


def make_sales(rows):
    return pd.DataFrame(rows)


def make_quota(rows):
    return pd.DataFrame(rows)


def test_gross_margin_is_sales_minus_cost():
    sales = make_sales([
        {"EmployeeKey": 1, "CalendarYear": 2013, "CalendarQuarter": 3,
         "SalesAmount": 100.0, "TotalProductCost": 60.0,
         "EnglishProductCategoryName": "Bikes", "EnglishProductSubcategoryName": "Road"},
    ])
    metrics = QuarterlyMetrics(sales, make_quota([]), "2013Q3")
    result = metrics.margin_by_category()
    assert result["gross_margin"].iloc[0] == 40.0  # 100-60
    assert result["margin_pct"].iloc[0] == pytest.approx(0.4)  # 40/100


def test_variance_is_actual_minus_quota():
    sales = make_sales([
        {"EmployeeKey": 1, "CalendarYear": 2013, "CalendarQuarter": 3, "SalesAmount": 1000.0},
    ])
    quota = make_quota([
        {"EmployeeKey": 1, "employee_name": "A B", "SalesTerritoryRegion": "Canada",
         "CalendarYear": 2013, "CalendarQuarter": 3, "SalesAmountQuota": 800.0},
    ])
    metrics = QuarterlyMetrics(sales, quota, "2013Q3")
    result = metrics.quota_by_salesperson()
    assert result["variance"].iloc[0] == 200.0  # 1000-800


def test_attainment_pct_is_actual_over_quota():
    sales = make_sales([
        {"EmployeeKey": 1, "CalendarYear": 2013, "CalendarQuarter": 3, "SalesAmount": 900.0},
    ])
    quota = make_quota([
        {"EmployeeKey": 1, "employee_name": "A B", "SalesTerritoryRegion": "Canada",
         "CalendarYear": 2013, "CalendarQuarter": 3, "SalesAmountQuota": 1000.0},
    ])
    metrics = QuarterlyMetrics(sales, quota, "2013Q3")
    result = metrics.quota_by_salesperson()
    assert result["attainment_pct"].iloc[0] == pytest.approx(0.9)  # 900/1000


def test_quarter_filter_excludes_other_quarters():
    sales = make_sales([
        {"EmployeeKey": 1, "CalendarYear": 2013, "CalendarQuarter": 3,
         "SalesAmount": 100.0, "TotalProductCost": 50.0,
         "EnglishProductCategoryName": "Bikes", "EnglishProductSubcategoryName": "Road"},
        {"EmployeeKey": 1, "CalendarYear": 2013, "CalendarQuarter": 2,
         "SalesAmount": 999.0, "TotalProductCost": 1.0,
         "EnglishProductCategoryName": "Bikes", "EnglishProductSubcategoryName": "Road"},
    ])
    metrics = QuarterlyMetrics(sales, make_quota([]), "2013Q3")
    result = metrics.margin_by_category()
    assert len(result) == 1  # only the Q3 row
    assert result["sales"].iloc[0] == 100.0


def test_reconciliation_rows_sum_to_raw():
    sales = make_sales([
        {"EmployeeKey": 1, "CalendarYear": 2013, "CalendarQuarter": 3, "SalesAmount": 100.0},
        {"EmployeeKey": 1, "CalendarYear": 2013, "CalendarQuarter": 3, "SalesAmount": 200.0},
        {"EmployeeKey": 1, "CalendarYear": 2013, "CalendarQuarter": 2, "SalesAmount": 50.0},
    ])
    metrics = QuarterlyMetrics(sales, make_quota([]), "2013Q3")
    result = metrics.reconcile().set_index("stage")
    assert result.loc["used", "n_rows"] + result.loc["excluded", "n_rows"] == result.loc["raw", "n_rows"]  # 2+1=3
    assert result.loc["used", "total_value"] == 300.0  # 100+200
