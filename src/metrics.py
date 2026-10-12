import pandas as pd


class QuarterlyMetrics:
    def __init__(self, sales: pd.DataFrame, quota: pd.DataFrame, quarter: str):
        self.sales = sales
        self.quota = quota
        self.quarter = quarter
        self.year, self.q = self._parse_quarter(quarter)

    @staticmethod
    def _parse_quarter(quarter: str) -> tuple[int, int]:
        year, q = quarter.split("Q")
        return int(year), int(q)

    def _sales_in_quarter(self, year=None, q=None) -> pd.DataFrame:
        year = self.year if year is None else year
        q = self.q if q is None else q
        return self.sales[(self.sales["CalendarYear"] == year) & (self.sales["CalendarQuarter"] == q)]

    def _quota_in_quarter(self) -> pd.DataFrame:
        return self.quota[(self.quota["CalendarYear"] == self.year) & (self.quota["CalendarQuarter"] == self.q)]

    def quota_by_salesperson(self) -> pd.DataFrame:
        quota_q = self._quota_in_quarter()[
            ["EmployeeKey", "employee_name", "SalesTerritoryRegion", "SalesAmountQuota"]
        ].rename(columns={"SalesTerritoryRegion": "territory", "SalesAmountQuota": "quota"})

        actual = (
            self._sales_in_quarter()
            .groupby("EmployeeKey", as_index=False)["SalesAmount"]
            .sum()
            .rename(columns={"SalesAmount": "actual_sales"})
        )

        result = quota_q.merge(actual, on="EmployeeKey", how="left")
        result["actual_sales"] = result["actual_sales"].fillna(0.0)
        result["variance"] = result["actual_sales"] - result["quota"]
        result["attainment_pct"] = result["actual_sales"] / result["quota"]
        result = result.rename(columns={"EmployeeKey": "employee_id"})
        return result[
            ["employee_id", "employee_name", "territory", "actual_sales", "quota", "variance", "attainment_pct"]
        ]

    def quota_by_territory(self) -> pd.DataFrame:
        by_person = self.quota_by_salesperson()
        result = by_person.groupby("territory", as_index=False).agg(
            actual_sales=("actual_sales", "sum"), quota=("quota", "sum")
        )
        result["variance"] = result["actual_sales"] - result["quota"]
        result["attainment_pct"] = result["actual_sales"] / result["quota"]
        return result

    def margin_by_category(self) -> pd.DataFrame:
        result = (
            self._sales_in_quarter()
            .groupby(["EnglishProductCategoryName", "EnglishProductSubcategoryName"], as_index=False)
            .agg(sales=("SalesAmount", "sum"), cost=("TotalProductCost", "sum"))
            .rename(columns={
                "EnglishProductCategoryName": "category",
                "EnglishProductSubcategoryName": "subcategory",
            })
        )
        result["gross_margin"] = result["sales"] - result["cost"]
        result["margin_pct"] = result["gross_margin"] / result["sales"]
        return result.sort_values(["category", "subcategory"]).reset_index(drop=True)

    def prior_year_comparison(self) -> pd.DataFrame:
        current = self._sales_in_quarter()
        prior = self._sales_in_quarter(year=self.year - 1, q=self.q)
        rows = []
        for period, df in [("current", current), ("prior_year", prior)]:
            sales = df["SalesAmount"].sum()
            cost = df["TotalProductCost"].sum()
            margin = sales - cost
            rows.append({
                "period": period, "sales": sales, "cost": cost,
                "gross_margin": margin, "margin_pct": margin / sales if sales else None,
            })
        result = pd.DataFrame(rows)
        current_sales = result.loc[result["period"] == "current", "sales"].iloc[0]
        prior_sales = result.loc[result["period"] == "prior_year", "sales"].iloc[0]
        result["sales_pct_change_vs_prior"] = (current_sales - prior_sales) / prior_sales if prior_sales else None
        return result

    def top_bottom_products(self, top_n: int) -> pd.DataFrame:
        by_product = (
            self._sales_in_quarter()
            .groupby("EnglishProductName", as_index=False)
            .agg(sales=("SalesAmount", "sum"), cost=("TotalProductCost", "sum"))
            .rename(columns={"EnglishProductName": "product"})
        )
        by_product["gross_margin"] = by_product["sales"] - by_product["cost"]
        top = by_product.sort_values("gross_margin", ascending=False).head(top_n).assign(rank_group="top")
        bottom = by_product.sort_values("gross_margin", ascending=True).head(top_n).assign(rank_group="bottom")
        return pd.concat([top, bottom], ignore_index=True)

    def quota_trend(self) -> pd.DataFrame:
        actual = (
            self.sales.groupby(["CalendarYear", "CalendarQuarter"], as_index=False)["SalesAmount"]
            .sum()
            .rename(columns={"SalesAmount": "actual_sales"})
        )
        quota = (
            self.quota.groupby(["CalendarYear", "CalendarQuarter"], as_index=False)["SalesAmountQuota"]
            .sum()
            .rename(columns={"SalesAmountQuota": "quota"})
        )
        result = actual.merge(quota, on=["CalendarYear", "CalendarQuarter"], how="outer").fillna(0.0)
        result["period"] = result["CalendarYear"].astype(int).astype(str) + "Q" + result["CalendarQuarter"].astype(int).astype(str)
        return result.sort_values(["CalendarYear", "CalendarQuarter"]).reset_index(drop=True)

    def reconcile(self) -> pd.DataFrame:
        used = self._sales_in_quarter()
        raw_rows, raw_value = len(self.sales), self.sales["SalesAmount"].sum()
        used_rows, used_value = len(used), used["SalesAmount"].sum()
        return pd.DataFrame([
            {"stage": "raw", "n_rows": raw_rows, "total_value": raw_value},
            {"stage": "used", "n_rows": used_rows, "total_value": used_value},
            {"stage": "excluded", "n_rows": raw_rows - used_rows, "total_value": raw_value - used_value},
        ])
