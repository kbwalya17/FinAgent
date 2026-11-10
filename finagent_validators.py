
import numpy as np
import pandas as pd
from pathlib import Path
from openpyxl import load_workbook

from data import get_stock_prices
from analytics import analyze_stocks


# ==================================================
# 1. HISTORICAL DATA VALIDATION
# ==================================================

def validate_prices(prices):
    """Check historical price data quality."""

    errors = []

    if not isinstance(prices, pd.DataFrame):
        return ["Prices must be a pandas DataFrame."]

    if prices.empty:
        return ["Historical price data is empty."]

    if len(prices) < 3:
        errors.append("Insufficient price observations.")

    if prices.columns.duplicated().any():
        errors.append("Duplicate ticker columns detected.")

    if prices.index.has_duplicates:
        errors.append("Duplicate dates detected.")

    if not prices.index.is_monotonic_increasing:
        errors.append("Dates are not sorted chronologically.")

    if prices.isna().any().any():
        errors.append("Missing price observations detected.")

    try:
        numeric = prices.to_numpy(dtype=float)

        if not np.isfinite(numeric).all():
            errors.append("Non-finite prices detected.")

        if (numeric <= 0).any():
            errors.append("Prices must be positive.")

    except (ValueError, TypeError):
        errors.append("Non-numeric prices detected.")

    return errors


# ==================================================
# 2. FINANCIAL ANALYTICS VALIDATION — ALL 19 METRICS
# ==================================================

def validate_analytics(
    prices,
    results,
    frequency="monthly",
    risk_free_rate=0.04,
    tolerance=1e-8
):
    """Recalculate and verify all financial metrics."""

    errors = []

    factors = {
        "daily": 252,
        "weekly": 52,
        "monthly": 12
    }

    if frequency not in factors:
        return ["Unsupported frequency."]

    if risk_free_rate <= -1:
        return ["Risk-free rate must exceed -100%."]

    N = factors[frequency]

    returns = prices.pct_change().iloc[1:]
    summary = results["summary"]

    periodic_rf = (1 + risk_free_rate) ** (1 / N) - 1

    for ticker in prices.columns:

        p = prices[ticker].to_numpy(dtype=float)
        r = returns[ticker].to_numpy(dtype=float)

        # ------------------------------
        # RETURN METRICS
        # ------------------------------

        total_return = p[-1] / p[0] - 1

        cagr = (p[-1] / p[0]) ** (N / len(r)) - 1

        average_return = np.mean(r)

        annual_arithmetic = average_return * N

        best_period = np.max(r)
        worst_period = np.min(r)

        # ------------------------------
        # RISK METRICS
        # ------------------------------

        volatility = np.std(r, ddof=1) * np.sqrt(N)

        running_peak = np.maximum.accumulate(p)

        drawdown = p / running_peak - 1

        max_drawdown = np.min(drawdown)

        average_drawdown = np.mean(drawdown)

        downside = np.minimum(r, 0)

        downside_deviation = np.sqrt(
            np.mean(downside ** 2) * N
        )

        # Historical one-period VaR and CVaR
        threshold = np.quantile(r, 0.05)

        var_95 = -threshold

        cvar_95 = -np.mean(r[r <= threshold])

        # ------------------------------
        # RISK-ADJUSTED METRICS
        # ------------------------------

        excess = r - periodic_rf

        sharpe = (
            np.mean(excess) * N / volatility
            if volatility > 0 else np.nan
        )

        downside_excess = np.minimum(excess, 0)

        downside_rf = np.sqrt(
            np.mean(downside_excess ** 2) * N
        )

        sortino = (
            np.mean(excess) * N / downside_rf
            if downside_rf > 0 else np.nan
        )

        calmar = (
            cagr / abs(max_drawdown)
            if max_drawdown < 0 else np.nan
        )

        # ------------------------------
        # MARKET BEHAVIOR
        # ------------------------------

        skewness = pd.Series(r).skew()

        excess_kurtosis = pd.Series(r).kurt()

        positive_pct = np.mean(r > 0)

        longest_streak = 0
        current_streak = 0

        for value in r:
            if value < 0:
                current_streak += 1
                longest_streak = max(
                    longest_streak,
                    current_streak
                )
            else:
                current_streak = 0

        # ------------------------------
        # EXPECTED RESULTS
        # ------------------------------

        expected = {
            "Total Return": total_return,
            "Annualized Return": cagr,
            "Average Periodic Return": average_return,
            "Annualized Arithmetic Return": annual_arithmetic,
            "Annualized Volatility": volatility,
            "Best Period": best_period,
            "Worst Period": worst_period,
            "Maximum Drawdown": max_drawdown,
            "Average Drawdown": average_drawdown,
            "Downside Deviation": downside_deviation,
            "Historical VaR (95%)": var_95,
            "Historical CVaR (95%)": cvar_95,
            "Sharpe Ratio": sharpe,
            "Sortino Ratio": sortino,
            "Calmar Ratio": calmar,
            "Skewness": skewness,
            "Excess Kurtosis": excess_kurtosis,
            "Positive Period Percentage": positive_pct,
            "Longest Losing Streak": longest_streak
        }

        for metric, expected_value in expected.items():

            try:
                actual = float(summary.loc[ticker, metric])

            except (KeyError, ValueError, TypeError):
                errors.append(
                    f"Missing metric: {ticker} - {metric}"
                )
                continue

            if not np.isclose(
                actual,
                expected_value,
                rtol=tolerance,
                atol=tolerance,
                equal_nan=True
            ):
                errors.append(
                    f"{ticker} - {metric}: "
                    f"expected {expected_value:.6f}, "
                    f"got {actual:.6f}"
                )

    # ------------------------------
    # MATRIX VALIDATION
    # ------------------------------

    expected_matrices = {
        "correlation": returns.corr(),
        "covariance": returns.cov(),
        "annualized_covariance": returns.cov() * N
    }

    for name, expected_matrix in expected_matrices.items():

        if name not in results:
            errors.append(f"Missing matrix: {name}")
            continue

        actual_matrix = results[name]

        if not expected_matrix.index.equals(actual_matrix.index):
            errors.append(f"{name}: index mismatch.")
            continue

        if not expected_matrix.columns.equals(actual_matrix.columns):
            errors.append(f"{name}: column mismatch.")
            continue

        if not np.allclose(
            expected_matrix.to_numpy(),
            actual_matrix.to_numpy(),
            rtol=tolerance,
            atol=tolerance,
            equal_nan=True
        ):
            errors.append(f"{name}: incorrect values.")

    return errors


# ==================================================
# 3. EXCEL WORKBOOK VALIDATION
# ==================================================

def validate_excel(filename, tickers):
    """Check workbook sheets, inputs, and formulas."""

    errors = []

    path = Path(filename)

    if not path.exists():
        return [f"Excel file not found: {path}"]

    required_sheets = [
        "Assumptions",
        "Historical Prices",
        "Periodic Returns",
        "Performance Summary",
        "Correlations",
        "Drawdowns",
        "Growth of 100",
        "Methodology"
    ]

    wb = load_workbook(path, data_only=False)

    try:
        for sheet in required_sheets:
            if sheet not in wb.sheetnames:
                errors.append(
                    f"Missing Excel sheet: {sheet}"
                )

        if errors:
            return errors

        assumptions = wb["Assumptions"]
        summary = wb["Performance Summary"]
        returns = wb["Periodic Returns"]
        drawdowns = wb["Drawdowns"]

        if not isinstance(
            assumptions["B3"].value, (int, float)
        ):
            errors.append(
                "Invalid annualization factor."
            )

        if not isinstance(
            assumptions["B4"].value, (int, float)
        ):
            errors.append(
                "Invalid risk-free rate."
            )

        # Current Excel version contains 8 metrics.
        # We will expand it to all 19 next.

        for col_index, ticker in enumerate(
            tickers, start=2
        ):

            if summary.cell(1, col_index).value != ticker:
                errors.append(
                    f"Incorrect summary header: {ticker}"
                )

            if returns.cell(1, col_index).value != ticker:
                errors.append(
                    f"Incorrect returns header: {ticker}"
                )

            for row in range(2, 10):
                formula = summary.cell(
                    row, col_index
                ).value

                if (
                    not isinstance(formula, str)
                    or not formula.startswith("=")
                ):
                    errors.append(
                        f"Missing summary formula: "
                        f"{ticker}, row {row}"
                    )

            for row in range(
                3, returns.max_row + 1
            ):
                formula = returns.cell(
                    row, col_index
                ).value

                if (
                    not isinstance(formula, str)
                    or not formula.startswith("=")
                ):
                    errors.append(
                        f"Missing return formula: "
                        f"{ticker}, row {row}"
                    )

            for row in range(
                2, drawdowns.max_row + 1
            ):
                formula = drawdowns.cell(
                    row, col_index
                ).value

                if (
                    not isinstance(formula, str)
                    or not formula.startswith("=")
                ):
                    errors.append(
                        f"Missing drawdown formula: "
                        f"{ticker}, row {row}"
                    )

        first_drawdown = drawdowns["B2"].value or ""

        if "'Historical Prices'!" not in first_drawdown:
            errors.append(
                "Drawdown formula has incorrect references."
            )

    finally:
        wb.close()

    return errors


# ==================================================
# 4. COMPLETE VALIDATION PIPELINE
# ==================================================

def run_validation(
    prices,
    results,
    excel_path,
    frequency="monthly",
    risk_free_rate=0.04
):
    """Run all FinAgent quality assurance checks."""

    print("\nFinAgent — Quality Assurance Report")
    print("=" * 45)

    data_errors = validate_prices(prices)

    if data_errors:
        checks = {"Historical Data": data_errors}
    else:
        checks = {
            "Historical Data": [],

            "All 19 Financial Metrics & Matrices":
                validate_analytics(
                    prices,
                    results,
                    frequency,
                    risk_free_rate
                ),

            "Excel Workbook":
                validate_excel(
                    excel_path,
                    list(prices.columns)
                )
        }

    all_passed = True

    for category, errors in checks.items():

        if errors:
            all_passed = False
            print(f"\nFAIL — {category}")

            for error in errors:
                print("  -", error)

        else:
            print(f"\nPASS — {category}")

    print("\n" + "=" * 45)

    if all_passed:
        print("All FinAgent validation checks passed!")
    else:
        print("FinAgent validation FAILED.")

    return all_passed


# ==================================================
# 5. STANDALONE TEST
# ==================================================

if __name__ == "__main__":

    from excel import create_excel_report

    prices = get_stock_prices(
        ["AAPL", "MSFT", "NVDA"],
        period="5y",
        frequency="monthly"
    )

    results = analyze_stocks(
        prices,
        frequency="monthly",
        risk_free_rate=0.04
    )

    output_path = (
        Path(__file__).resolve().parent
        / "FinAgent_Validation_Test.xlsx"
    )

    create_excel_report(
        prices,
        frequency="monthly",
        risk_free_rate=0.04,
        filename=str(output_path)
    )

    success = run_validation(
        prices,
        results,
        output_path,
        frequency="monthly",
        risk_free_rate=0.04
    )

    if not success:
        raise SystemExit(1)
