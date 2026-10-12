import xlsxwriter


class PackWriter:
    def __init__(self, output_path: str):
        self.workbook = xlsxwriter.Workbook(output_path)
        self.currency_fmt = self.workbook.add_format({"num_format": "$#,##0"})
        self.pct_fmt = self.workbook.add_format({"num_format": "0.0%"})
        self.header_fmt = self.workbook.add_format({"bold": True, "bg_color": "#D9E1F2"})
        self.title_fmt = self.workbook.add_format({"bold": True, "font_size": 14})
        self.green_fmt = self.workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})
        self.red_fmt = self.workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})

    def _write_table(self, sheet, start_row, start_col, df, currency_cols=(), pct_cols=()):
        for j, col_name in enumerate(df.columns):
            sheet.write(start_row, start_col + j, col_name, self.header_fmt)
        for i, (_, row) in enumerate(df.iterrows()):
            for j, col_name in enumerate(df.columns):
                value = row[col_name]
                fmt = self.currency_fmt if col_name in currency_cols else self.pct_fmt if col_name in pct_cols else None
                sheet.write(start_row + 1 + i, start_col + j, value, fmt)
        sheet.set_column(start_col, start_col + len(df.columns) - 1, 18)
        return start_row + 1 + len(df)

    def write_summary(self, quarter, prior_year_comparison, quota_trend, quota_by_salesperson) -> None:
        sheet = self.workbook.add_worksheet("Summary")
        sheet.freeze_panes(1, 0)
        sheet.write(0, 0, f"Quarterly Summary -- {quarter}", self.title_fmt)

        current = prior_year_comparison[prior_year_comparison["period"] == "current"].iloc[0]
        prior = prior_year_comparison[prior_year_comparison["period"] == "prior_year"].iloc[0]
        total_actual = quota_by_salesperson["actual_sales"].sum()
        total_quota = quota_by_salesperson["quota"].sum()
        attainment = total_actual / total_quota if total_quota else None

        sheet.write(2, 0, "Reseller sales")
        sheet.write(2, 1, current["sales"], self.currency_fmt)
        sheet.write(3, 0, "Gross margin %")
        sheet.write(3, 1, current["margin_pct"], self.pct_fmt)
        sheet.write(4, 0, "Quota attainment %")
        sheet.write(4, 1, attainment, self.pct_fmt)
        sheet.write(5, 0, "Sales vs. same quarter last year")
        sheet.write(5, 1, current["sales"] - prior["sales"], self.currency_fmt)
        sheet.write(6, 0, "Sales % change vs. last year")
        sheet.write(6, 1, prior_year_comparison["sales_pct_change_vs_prior"].iloc[0], self.pct_fmt)

        chart_row = self._write_table(sheet, 9, 0, quota_trend[["period", "actual_sales", "quota"]],
                                       currency_cols=("actual_sales", "quota"))

        chart = self.workbook.add_chart({"type": "column"})
        n = len(quota_trend)
        chart.add_series({
            "name": "Actual",
            "categories": ["Summary", 10, 0, 9 + n, 0],
            "values": ["Summary", 10, 1, 9 + n, 1],
        })
        chart.add_series({
            "name": "Quota",
            "categories": ["Summary", 10, 0, 9 + n, 0],
            "values": ["Summary", 10, 2, 9 + n, 2],
        })
        chart.set_title({"name": "Actual vs quota by quarter"})
        sheet.insert_chart(chart_row + 1, 0, chart)

    def write_quota_performance(self, quota_by_salesperson, quota_by_territory) -> None:
        sheet = self.workbook.add_worksheet("Quota Performance")
        sheet.freeze_panes(1, 0)

        sheet.write(0, 0, "By salesperson", self.header_fmt)
        headers = ["employee_id", "employee_name", "territory", "actual_sales", "quota", "variance", "attainment_pct"]
        for j, name in enumerate(headers):
            sheet.write(1, j, name, self.header_fmt)
        actual_col, quota_col, variance_col, attainment_col = 3, 4, 5, 6
        for i, (_, row) in enumerate(quota_by_salesperson.iterrows()):
            r = 2 + i
            sheet.write(r, 0, row["employee_id"])
            sheet.write(r, 1, row["employee_name"])
            sheet.write(r, 2, row["territory"])
            sheet.write(r, actual_col, row["actual_sales"], self.currency_fmt)
            sheet.write(r, quota_col, row["quota"], self.currency_fmt)
            sheet.write_formula(r, variance_col, f"=D{r+1}-E{r+1}", self.currency_fmt, row["variance"])
            sheet.write_formula(r, attainment_col, f"=D{r+1}/E{r+1}", self.pct_fmt, row["attainment_pct"])
        last_row = 2 + len(quota_by_salesperson)
        sheet.conditional_format(2, attainment_col, last_row - 1, attainment_col,
                                  {"type": "cell", "criteria": ">=", "value": 1, "format": self.green_fmt})
        sheet.conditional_format(2, attainment_col, last_row - 1, attainment_col,
                                  {"type": "cell", "criteria": "<", "value": 1, "format": self.red_fmt})

        territory_row = last_row + 2
        sheet.write(territory_row, 0, "By territory", self.header_fmt)
        self._write_table(sheet, territory_row + 1, 0, quota_by_territory,
                           currency_cols=("actual_sales", "quota", "variance"), pct_cols=("attainment_pct",))
        sheet.set_column(0, 6, 16)

    def write_product_margin(self, margin_by_category, top_bottom_products) -> None:
        sheet = self.workbook.add_worksheet("Product Margin")
        sheet.freeze_panes(1, 0)
        sheet.write(0, 0, "By category / subcategory", self.header_fmt)
        next_row = self._write_table(sheet, 1, 0, margin_by_category,
                                      currency_cols=("sales", "cost", "gross_margin"), pct_cols=("margin_pct",))
        sheet.write(next_row + 1, 0, "Top / bottom products by margin", self.header_fmt)
        self._write_table(sheet, next_row + 2, 0, top_bottom_products,
                           currency_cols=("sales", "cost", "gross_margin"))

    def write_reconciliation(self, reconciliation) -> None:
        sheet = self.workbook.add_worksheet("Reconciliation")
        sheet.freeze_panes(1, 0)
        self._write_table(sheet, 0, 0, reconciliation, currency_cols=("total_value",))

    def write_notes(self, quarter) -> None:
        sheet = self.workbook.add_worksheet("Notes")
        sheet.write(0, 0, "Definitions, assumptions and data source", self.header_fmt)
        notes = [
            "Sales amount: gross reseller sales (SalesAmount) for the quarter.",
            "Cost: TotalProductCost (line-level, = ProductStandardCost x quantity).",
            "Gross margin: sales - cost. Margin %: gross margin / sales.",
            "Quota: FactSalesQuota amount, per salesperson per quarter, reseller sales only.",
            "Variance: actual - quota. Attainment %: actual / quota.",
            f"Reporting quarter: {quarter}.",
            "Source: AdventureWorksDW sample data (see README for licence and access date).",
        ]
        for i, line in enumerate(notes):
            sheet.write(2 + i, 0, line)
        sheet.set_column(0, 0, 90)

    def close(self) -> None:
        self.workbook.close()
