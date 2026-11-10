
import numpy as np
import pandas as pd

from data import get_stock_prices


def longest_losing_streak(returns):
    """Count the longest sequence of negative returns."""
    longest = 0
    current = 0

    for value in returns.dropna():
        if value < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return longest


def analyze_stocks(
    prices,
    frequency="monthly",
    risk_free_rate=0.04
):
    """
    Calculate stock performance and risk metrics.

    Prices must contain adjusted closing prices.

    risk_free_rate is an annual effective rate.

    VaR and CVaR are historical one-period loss
    measures at the 95% confidence level.
    """

    annualization = {
        "daily": 252,
        "weekly": 52,
        "monthly": 12
    }

    if frequency not in annualization:
        raise ValueError("Unsupported frequency.")

    if risk_free_rate <= -1:
        raise ValueError(
            "Risk-free rate must be greater than -100%."
        )

    if not isinstance(prices, pd.DataFrame):
        raise ValueError("Prices must be a DataFrame.")

    if prices.empty or len(prices) < 3:
        raise ValueError("Insufficient price observations.")

    if prices.isna().any().any():
        raise ValueError("Missing prices detected.")

    if not np.isfinite(prices.to_numpy(dtype=float)).all():
        raise ValueError("Non-finite prices detected.")

    if (prices <= 0).any().any():
        raise ValueError("Prices must be positive.")

    N = annualization[frequency]

    # ----------------------------------------------
    # PERIODIC RETURNS
    # ----------------------------------------------

    returns = prices.pct_change().iloc[1:]

    observations = len(returns)

    # ----------------------------------------------
    # RETURN ANALYSIS
    # ----------------------------------------------

    total_return = (
        prices.iloc[-1] / prices.iloc[0] - 1
    )

    annualized_return = (
        prices.iloc[-1] / prices.iloc[0]
    ) ** (N / observations) - 1

    average_return = returns.mean()

    annualized_arithmetic_return = (
        average_return * N
    )

    best_period = returns.max()
    worst_period = returns.min()

    cumulative_returns = (
        (1 + returns).cumprod() - 1
    )

    # ----------------------------------------------
    # RISK ANALYSIS
    # ----------------------------------------------

    volatility = (
        returns.std(ddof=1) * np.sqrt(N)
    )

    growth = prices / prices.iloc[0]

    running_peak = growth.cummax()

    drawdown = growth / running_peak - 1

    max_drawdown = drawdown.min()

    average_drawdown = drawdown.mean()

    # Downside deviation relative to zero return
    downside_returns = returns.clip(upper=0)

    downside_deviation = np.sqrt(
        (downside_returns ** 2).mean()
    ) * np.sqrt(N)

    # Historical Value at Risk and Expected Shortfall
    # Positive values indicate losses.
    var_95 = -returns.quantile(0.05)

    cvar_95 = pd.Series(index=returns.columns, dtype=float)

    for ticker in returns.columns:
        threshold = returns[ticker].quantile(0.05)

        tail_returns = returns.loc[
            returns[ticker] <= threshold,
            ticker
        ]

        cvar_95[ticker] = -tail_returns.mean()

    # ----------------------------------------------
    # RISK-ADJUSTED PERFORMANCE
    # ----------------------------------------------

    periodic_rf = (
        (1 + risk_free_rate) ** (1 / N) - 1
    )

    excess_returns = returns - periodic_rf

    sharpe = (
        excess_returns.mean() * N
    ) / volatility.replace(0, np.nan)

    # Sortino uses the risk-free rate as target.
    downside_excess = excess_returns.clip(upper=0)

    downside_deviation_rf = np.sqrt(
        (downside_excess ** 2).mean()
    ) * np.sqrt(N)

    sortino = (
        excess_returns.mean() * N
    ) / downside_deviation_rf.replace(0, np.nan)

    calmar = annualized_return / (
        -max_drawdown.replace(0, np.nan)
    )

    # ----------------------------------------------
    # MARKET BEHAVIOR
    # ----------------------------------------------

    skewness = returns.skew()

    excess_kurtosis = returns.kurt()

    positive_period_percentage = (
        (returns > 0).mean()
    )

    losing_streak = pd.Series({
        ticker: longest_losing_streak(
            returns[ticker]
        )
        for ticker in returns.columns
    })

    # ----------------------------------------------
    # STOCK COMPARISON
    # ----------------------------------------------

    correlation = returns.corr()

    covariance = returns.cov()

    annualized_covariance = covariance * N

    growth_100 = growth * 100

    # ----------------------------------------------
    # PERFORMANCE SUMMARY
    # ----------------------------------------------

    summary = pd.DataFrame({
        "Total Return": total_return,
        "Annualized Return": annualized_return,
        "Average Periodic Return": average_return,
        "Annualized Arithmetic Return":
            annualized_arithmetic_return,
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
        "Positive Period Percentage":
            positive_period_percentage,
        "Longest Losing Streak": losing_streak
    })

    return {
        "returns": returns,
        "summary": summary,
        "correlation": correlation,
        "covariance": covariance,
        "annualized_covariance": annualized_covariance,
        "growth": growth_100,
        "drawdown": drawdown,
        "cumulative_returns": cumulative_returns
    }


if __name__ == "__main__":

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

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 220)

    print("\nFinAgent — Expanded Financial Analytics")
    print("=" * 60)

    print("\nPerformance & Risk Summary:")
    print(results["summary"].round(4).T)

    print("\nCorrelation Matrix:")
    print(results["correlation"].round(3))

    print("\nAnnualized Covariance Matrix:")
    print(results["annualized_covariance"].round(4))

    print("\nMetrics per stock:",
          len(results["summary"].columns))
