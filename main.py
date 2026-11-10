
from pathlib import Path
from datetime import datetime

from agent import interpret_request
from data import get_stock_prices
from analytics import analyze_stocks
from excel import create_excel_report
from finagent_validators import run_validation


def run_finagent(user_request):
    """Run the complete FinAgent analysis workflow."""

    print("\nFinAgent — Starting Analysis")
    print("=" * 45)

    # 1. Interpret user request
    print("\n[1/5] Understanding your request...")

    instructions = interpret_request(user_request)

    tickers = instructions["tickers"]
    period = instructions["period"]
    frequency = instructions["frequency"]
    risk_free_rate = instructions["risk_free_rate"]

    print("Tickers:", ", ".join(tickers))
    print("Period:", period)
    print("Frequency:", frequency)
    print("Risk-free rate:", f"{risk_free_rate:.2%}")

    # 2. Retrieve historical market data
    print("\n[2/5] Retrieving historical prices...")

    prices = get_stock_prices(
        tickers,
        period=period,
        frequency=frequency
    )

    print("Observations:", len(prices))

    # 3. Calculate financial analytics
    print("\n[3/5] Calculating performance and risk...")

    results = analyze_stocks(
        prices,
        frequency=frequency,
        risk_free_rate=risk_free_rate
    )

    print("\nPerformance Summary:")
    print(results["summary"].round(4))

    # 4. Generate Excel workbook
    print("\n[4/5] Generating Excel workbook...")

    output_dir = Path(__file__).resolve().parent / "reports"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = output_dir / f"FinAgent_Report_{timestamp}.xlsx"

    report_path = create_excel_report(
        prices,
        frequency=frequency,
        risk_free_rate=risk_free_rate,
        filename=str(filename)
    )

    print("Workbook created:", report_path)

    # 5. Validate results
    print("\n[5/5] Validating analysis...")

    passed = run_validation(
        prices,
        results,
        report_path,
        frequency=frequency,
        risk_free_rate=risk_free_rate
    )

    if not passed:
        raise RuntimeError(
            "FinAgent validation failed. "
            "Do not use this report until errors are resolved."
        )

    print("\n" + "=" * 45)
    print("FinAgent analysis completed successfully!")
    print("Report:", report_path)

    return {
        "instructions": instructions,
        "prices": prices,
        "results": results,
        "report_path": report_path
    }


if __name__ == "__main__":

    print("\nWelcome to FinAgent!")

    request = input(
        "\nWhat would you like to analyze?\n> "
    )

    try:
        run_finagent(request)

    except Exception as error:
        print("\nFinAgent encountered an error:")
        print(error)
        raise SystemExit(1)
