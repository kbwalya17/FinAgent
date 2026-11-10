
from pathlib import Path

import pandas as pd
import numpy as np

from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.workbook.properties import CalcProperties

from data import get_stock_prices


METRICS = [
    "Total Return",
    "Annualized Return",
    "Average Periodic Return",
    "Annualized Volatility",
    "Best Period",
    "Worst Period",
    "Maximum Drawdown",
    "Sharpe Ratio",
    "Annualized Arithmetic Return",
    "Average Drawdown",
    "Downside Deviation",
    "Historical VaR (95%)",
    "Historical CVaR (95%)",
    "Sortino Ratio",
    "Calmar Ratio",
    "Skewness",
    "Excess Kurtosis",
    "Positive Period Percentage",
    "Longest Losing Streak"
]


def create_excel_report(
    prices,
    frequency="monthly",
    risk_free_rate=0.04,
    filename="FinAgent_Stock_Analysis.xlsx"
):
    """
    Generate a formula-driven financial analysis workbook.

    All 19 metrics are calculated using Excel formulas.
    """

    factors = {
        "daily": 252,
        "weekly": 52,
        "monthly": 12
    }

    if frequency not in factors:
        raise ValueError("Unsupported frequency.")

    if risk_free_rate <= -1:
        raise ValueError("Invalid risk-free rate.")

    if not isinstance(prices, pd.DataFrame):
        raise ValueError("Prices must be a DataFrame.")

    if prices.empty or len(prices) < 3:
        raise ValueError("Insufficient historical prices.")

    if prices.isna().any().any():
        raise ValueError("Missing prices detected.")

    values = prices.to_numpy(dtype=float)

    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Prices must be finite and positive.")

    prices = prices.sort_index()

    tickers = list(prices.columns)
    n = len(prices)
    last = n + 1

    # -----------------------------------------
    # CREATE WORKBOOK
    # -----------------------------------------

    wb = Workbook()

    wb.calculation = CalcProperties(
        calcMode="auto",
        fullCalcOnLoad=True,
        forceFullCalc=True
    )

    assumptions = wb.active
    assumptions.title = "Assumptions"

    ws_prices = wb.create_sheet("Historical Prices")
    ws_returns = wb.create_sheet("Periodic Returns")
    ws_summary = wb.create_sheet("Performance Summary")
    ws_corr = wb.create_sheet("Correlations")
    ws_cov = wb.create_sheet("Covariance")
    ws_dd = wb.create_sheet("Drawdowns")
    ws_growth = wb.create_sheet("Growth of 100")
    ws_cumulative = wb.create_sheet("Cumulative Returns")
    ws_streaks = wb.create_sheet("Losing Streaks")
    ws_method = wb.create_sheet("Methodology")

    # -----------------------------------------
    # 1. ASSUMPTIONS
    # -----------------------------------------

    assumptions.append(["Parameter", "Value"])
    assumptions.append(["Frequency", frequency])
    assumptions.append(["Periods Per Year", factors[frequency]])
    assumptions.append(["Annual Risk-Free Rate", risk_free_rate])
    assumptions.append(["Initial Investment", 100])
    assumptions.append(["Data Source", "Yahoo Finance / yfinance"])
    assumptions.append(["VaR Confidence Level", 0.95])
    assumptions.append([
        "Periodic Risk-Free Rate",
        "=(1+B4)^(1/B3)-1"
    ])

    assumptions["B4"].number_format = "0.00%"
    assumptions["B7"].number_format = "0.00%"
    assumptions["B8"].number_format = "0.0000%"

    # -----------------------------------------
    # 2. HISTORICAL PRICES
    # -----------------------------------------

    ws_prices.append(["Date"] + tickers)

    for date, row in prices.iterrows():

        excel_date = pd.Timestamp(date).to_pydatetime()
        excel_date = excel_date.replace(tzinfo=None)

        ws_prices.append(
            [excel_date] + [float(x) for x in row]
        )

    # -----------------------------------------
    # 3. PERIODIC RETURNS
    # -----------------------------------------

    ws_returns.append(["Date"] + tickers)

    for r in range(2, last + 1):

        ws_returns.cell(
            r, 1,
            f"='Historical Prices'!A{r}"
        )

        for c in range(2, len(tickers) + 2):

            if r == 2:
                continue

            L = get_column_letter(c)

            ws_returns.cell(
                r, c,
                f"='Historical Prices'!{L}{r}/"
                f"'Historical Prices'!{L}{r-1}-1"
            )

    # -----------------------------------------
    # 4. DRAWDOWNS, GROWTH, CUMULATIVE RETURNS
    # -----------------------------------------

    ws_dd.append(["Date"] + tickers)
    ws_growth.append(["Date"] + tickers)
    ws_cumulative.append(["Date"] + tickers)

    for r in range(2, last + 1):

        for ws in [ws_dd, ws_growth, ws_cumulative]:
            ws.cell(
                r, 1,
                f"='Historical Prices'!A{r}"
            )

        for c in range(2, len(tickers) + 2):

            L = get_column_letter(c)

            price = f"'Historical Prices'!{L}{r}"
            first = f"'Historical Prices'!{L}$2"

            # Growth of an editable initial investment
            ws_growth.cell(
                r, c,
                f"={price}/{first}*Assumptions!$B$5"
            )

            # Cumulative return since first observation
            ws_cumulative.cell(
                r, c,
                f"={price}/{first}-1"
            )

            # Drawdown from running price peak
            ws_dd.cell(
                r, c,
                f"={price}/MAX('Historical Prices'!"
                f"{L}$2:{L}{r})-1"
            )

    # -----------------------------------------
    # 5. LOSING STREAKS
    # -----------------------------------------

    ws_streaks.append(["Date"] + tickers)

    for r in range(2, last + 1):

        ws_streaks.cell(
            r, 1,
            f"='Historical Prices'!A{r}"
        )

        for c in range(2, len(tickers) + 2):

            L = get_column_letter(c)

            if r == 2:
                ws_streaks.cell(r, c, 0)
                continue

            ws_streaks.cell(
                r, c,
                f'=IF(\'Periodic Returns\'!{L}{r}<0,'
                f'{L}{r-1}+1,0)'
            )

    # -----------------------------------------
    # 6. ALL 19 FINANCIAL METRICS
    # -----------------------------------------

    ws_summary.append(["Metric"] + tickers)

    for metric in METRICS:
        ws_summary.append([metric])

    for c, ticker in enumerate(tickers, start=2):

        L = get_column_letter(c)

        first = f"'Historical Prices'!{L}2"
        final = f"'Historical Prices'!{L}{last}"

        R = f"'Periodic Returns'!{L}3:{L}{last}"
        D = f"'Drawdowns'!{L}2:{L}{last}"
        S = f"'Losing Streaks'!{L}2:{L}{last}"

        N = "Assumptions!$B$3"
        RF = "Assumptions!$B$8"
        Q = "(1-Assumptions!$B$7)"

        mean = f"AVERAGE({R})"
        vol = f"STDEV.S({R})*SQRT({N})"

        cagr = (
            f"({final}/{first})^"
            f"({N}/COUNT({R}))-1"
        )

        excess_mean = f"({mean}-{RF})"

        downside_zero = (
            f"SQRT(SUMPRODUCT("
            f"({R}<0)*({R}^2))"
            f"/COUNT({R})*{N})"
        )

        downside_rf = (
            f"SQRT(SUMPRODUCT("
            f"({R}<{RF})*(({R}-{RF})^2))"
            f"/COUNT({R})*{N})"
        )

        var_threshold = f"PERCENTILE.INC({R},{Q})"

        formulas = {
            "Total Return":
                f"={final}/{first}-1",

            "Annualized Return":
                f"={cagr}",

            "Average Periodic Return":
                f"={mean}",

            "Annualized Volatility":
                f"={vol}",

            "Best Period":
                f"=MAX({R})",

            "Worst Period":
                f"=MIN({R})",

            "Maximum Drawdown":
                f"=MIN({D})",

            "Sharpe Ratio":
                f"=IFERROR({excess_mean}*{N}/{vol},NA())",

            "Annualized Arithmetic Return":
                f"={mean}*{N}",

            "Average Drawdown":
                f"=AVERAGE({D})",

            "Downside Deviation":
                f"={downside_zero}",

            "Historical VaR (95%)":
                f"=-{var_threshold}",

            "Historical CVaR (95%)":
                f'=-AVERAGEIF({R},"<="&{var_threshold},{R})',

            "Sortino Ratio":
                f"=IFERROR({excess_mean}*{N}/{downside_rf},NA())",

            "Calmar Ratio":
                f"=IFERROR(({cagr})/-MIN({D}),NA())",

            "Skewness":
                f"=SKEW({R})",

            "Excess Kurtosis":
                f"=KURT({R})",

            "Positive Period Percentage":
                f'=COUNTIF({R},">0")/COUNT({R})',

            "Longest Losing Streak":
                f"=MAX({S})"
        }

        for row_num, metric in enumerate(METRICS, start=2):

            cell = ws_summary.cell(
                row_num, c,
                formulas[metric]
            )

            if metric == "Longest Losing Streak":
                cell.number_format = "0"

            elif metric in [
                "Sharpe Ratio",
                "Sortino Ratio",
                "Calmar Ratio",
                "Skewness",
                "Excess Kurtosis"
            ]:
                cell.number_format = "0.000"

            else:
                cell.number_format = "0.00%"

    # -----------------------------------------
    # 7. CORRELATION MATRIX
    # -----------------------------------------

    ws_corr.append(["Ticker"] + tickers)

    for i, ticker in enumerate(tickers, start=2):

        ws_corr.cell(i, 1, ticker)

        for j in range(2, len(tickers) + 2):

            A = get_column_letter(i)
            B = get_column_letter(j)

            range_a = f"'Periodic Returns'!{A}3:{A}{last}"
            range_b = f"'Periodic Returns'!{B}3:{B}{last}"

            ws_corr.cell(
                i, j,
                f"=CORREL({range_a},{range_b})"
            )

    # -----------------------------------------
    # 8. COVARIANCE MATRICES
    # -----------------------------------------

    ws_cov.append(["Periodic Covariance"] + tickers)

    for i, ticker in enumerate(tickers, start=2):

        ws_cov.cell(i, 1, ticker)

        for j in range(2, len(tickers) + 2):

            A = get_column_letter(i)
            B = get_column_letter(j)

            ra = f"'Periodic Returns'!{A}3:{A}{last}"
            rb = f"'Periodic Returns'!{B}3:{B}{last}"

            ws_cov.cell(
                i, j,
                f"=COVARIANCE.S({ra},{rb})"
            )

    annual_start = len(tickers) + 5

    ws_cov.cell(
        annual_start, 1,
        "Annualized Covariance"
    )

    for j, ticker in enumerate(tickers, start=2):
        ws_cov.cell(annual_start, j, ticker)

    for i, ticker in enumerate(tickers, start=1):

        row = annual_start + i
        ws_cov.cell(row, 1, ticker)

        for j in range(2, len(tickers) + 2):

            periodic_cell = (
                f"{get_column_letter(j)}{i+1}"
            )

            ws_cov.cell(
                row, j,
                f"={periodic_cell}*Assumptions!$B$3"
            )

    # -----------------------------------------
    # 9. METHODOLOGY
    # -----------------------------------------

    notes = [
        ["Metric / Topic", "Definition"],
        ["Data", "Yahoo Finance adjusted closing prices"],
        ["Total Return", "Final price / initial price - 1"],
        ["CAGR", "(Final / Initial)^(periods per year / observations) - 1"],
        ["Arithmetic Return", "Mean periodic return * periods per year"],
        ["Volatility", "Sample standard deviation * SQRT(periods per year)"],
        ["Downside Deviation", "Annualized root mean square of negative returns"],
        ["VaR (95%)", "Negative fifth percentile of periodic returns"],
        ["CVaR (95%)", "Negative mean of returns at or below fifth percentile"],
        ["Sharpe", "Annualized arithmetic excess return / volatility"],
        ["Sortino", "Annualized excess return / downside deviation vs risk-free rate"],
        ["Calmar", "CAGR / absolute maximum drawdown"],
        ["Skewness", "Excel SKEW of periodic returns"],
        ["Excess Kurtosis", "Excel KURT of periodic returns"],
        ["Losing Streak", "Maximum consecutive negative-return periods"],
        ["Correlation", "Pearson correlation of aligned periodic returns"],
        ["Covariance", "Sample covariance of aligned periodic returns"],
        ["Risk-Free Rate", "Editable annual effective rate"],
        ["VaR Convention", "One-period historical loss; positive denotes loss"],
        ["Annualization", "252 daily, 52 weekly, 12 monthly"],
        ["Period Warning", "Latest trading period may be incomplete"],
        ["Calculation", "Excel recalculates formulas when workbook opens"]
    ]

    for item in notes:
        ws_method.append(item)

    # -----------------------------------------
    # 10. PERFORMANCE CHART
    # -----------------------------------------

    chart = LineChart()

    chart.title = "Growth of Initial Investment"
    chart.y_axis.title = "Investment Value"
    chart.x_axis.title = "Date"

    chart.width = 20
    chart.height = 10

    chart_data = Reference(
        ws_growth,
        min_col=2,
        max_col=len(tickers) + 1,
        min_row=1,
        max_row=last
    )

    chart_dates = Reference(
        ws_growth,
        min_col=1,
        min_row=2,
        max_row=last
    )

    chart.add_data(
        chart_data,
        titles_from_data=True
    )

    chart.set_categories(chart_dates)

    ws_growth.add_chart(chart, "F3")

    # -----------------------------------------
    # 11. PROFESSIONAL FORMATTING
    # -----------------------------------------

    navy = "17365D"
    light_blue = "EAF1F8"

    for ws in wb.worksheets:

        ws.freeze_panes = "B2"
        ws.sheet_view.showGridLines = False

        ws.column_dimensions["A"].width = 31

        for c in range(2, max(ws.max_column, 2) + 1):
            ws.column_dimensions[
                get_column_letter(c)
            ].width = 21

        for cell in ws[1]:

            cell.font = Font(
                bold=True,
                color="FFFFFF"
            )

            cell.fill = PatternFill(
                fill_type="solid",
                fgColor=navy
            )

            cell.alignment = Alignment(
                horizontal="center"
            )

        # Alternating row backgrounds
        for r in range(2, ws.max_row + 1):

            if r % 2 == 0:

                for cell in ws[r]:

                    cell.fill = PatternFill(
                        fill_type="solid",
                        fgColor=light_blue
                    )

    ws_method.column_dimensions["B"].width = 80
    assumptions.column_dimensions["B"].width = 40

    # Date formatting
    for ws in [
        ws_prices,
        ws_returns,
        ws_dd,
        ws_growth,
        ws_cumulative,
        ws_streaks
    ]:

        for r in range(2, ws.max_row + 1):
            ws.cell(r, 1).number_format = "yyyy-mm-dd"

    # Percentage formatting
    for ws in [ws_returns, ws_dd, ws_cumulative]:

        for row in ws.iter_rows(
            min_row=2,
            min_col=2
        ):
            for cell in row:
                cell.number_format = "0.00%"

    # Price and investment formatting
    for ws in [ws_prices, ws_growth]:

        for row in ws.iter_rows(
            min_row=2,
            min_col=2
        ):
            for cell in row:
                cell.number_format = '"$"#,##0.00'

    for ws in [ws_corr, ws_cov]:

        for row in ws.iter_rows(
            min_row=2,
            min_col=2
        ):
            for cell in row:

                if cell.data_type == "f":
                    cell.number_format = "0.0000"

    # -----------------------------------------
    # 12. SAVE WORKBOOK
    # -----------------------------------------

    output = Path(filename)

    if not output.is_absolute():
        output = Path(__file__).resolve().parent / output

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    wb.save(output)

    return output


# ---------------------------------------------
# STANDALONE TEST
# ---------------------------------------------

if __name__ == "__main__":

    prices = get_stock_prices(
        ["AAPL", "MSFT", "NVDA"],
        period="5y",
        frequency="monthly"
    )

    report = create_excel_report(
        prices,
        frequency="monthly",
        risk_free_rate=0.04,
        filename="FinAgent_Stock_Analysis.xlsx"
    )

    print("\nFinAgent — Expanded Excel Report")
    print("=" * 45)

    print("Report created:", report)
    print("Stocks analyzed:", len(prices.columns))
    print("Financial metrics:", len(METRICS))
    print("Workbook sheets: 11")
