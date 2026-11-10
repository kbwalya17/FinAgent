
import yfinance as yf
import pandas as pd


def get_stock_prices(
    tickers,
    period="5y",
    frequency="monthly"
):
    """
    Retrieve adjusted historical closing prices
    for one or multiple stocks.
    """

    frequency_map = {
        "daily": "1d",
        "weekly": "1wk",
        "monthly": "1mo"
    }

    if frequency not in frequency_map:
        raise ValueError(
            "Frequency must be daily, weekly, or monthly."
        )

    if isinstance(tickers, str):
        tickers = [tickers]

    if not tickers:
        raise ValueError("Provide at least one ticker.")

    raw_data = yf.download(
        tickers=tickers,
        period=period,
        interval=frequency_map[frequency],
        auto_adjust=True,
        progress=False
    )

    if raw_data.empty:
        raise ValueError("No stock data retrieved.")

    prices = raw_data["Close"]

    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])

    # Keep dates where all selected stocks have prices
    prices = prices.dropna()

    if len(prices) < 3:
        raise ValueError(
            "Not enough overlapping price observations."
        )

    return prices.sort_index()


if __name__ == "__main__":
    prices = get_stock_prices(
        ["AAPL", "MSFT", "NVDA"],
        period="5y",
        frequency="monthly"
    )

    print("\nFinAgent — Historical Prices")
    print(prices.head())
    print("\nObservations:", len(prices))
    print("Date range:", prices.index.min(), "to", prices.index.max())
