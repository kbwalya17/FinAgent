
import streamlit as st
import pandas as pd

from pathlib import Path

from main import run_finagent


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="FinAgent | AI Stock Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# STYLING
# ==================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.4px;
    }

    div[data-testid="stMetric"] {
        background-color: rgba(128,128,128,0.06);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.15);
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# FINANCIAL METRIC GROUPS
# ==================================================

RETURN_METRICS = [
    "Total Return",
    "Annualized Return",
    "Average Periodic Return",
    "Annualized Arithmetic Return",
    "Best Period",
    "Worst Period"
]

RISK_METRICS = [
    "Annualized Volatility",
    "Maximum Drawdown",
    "Average Drawdown",
    "Downside Deviation",
    "Historical VaR (95%)",
    "Historical CVaR (95%)"
]

RISK_ADJUSTED_METRICS = [
    "Sharpe Ratio",
    "Sortino Ratio",
    "Calmar Ratio"
]

MARKET_METRICS = [
    "Skewness",
    "Excess Kurtosis",
    "Positive Period Percentage",
    "Longest Losing Streak"
]

PERCENTAGE_METRICS = set(
    RETURN_METRICS
    + RISK_METRICS
    + ["Positive Period Percentage"]
)


# ==================================================
# FORMATTING FUNCTIONS — FIXED
# ==================================================

def format_metric(value, metric):
    """
    Format metrics according to their financial units.
    """

    if pd.isna(value):
        return "N/A"

    if metric == "Longest Losing Streak":
        return str(int(value))

    if metric in PERCENTAGE_METRICS:
        return f"{value:.2%}"

    return f"{value:.3f}"


def format_table(summary, metrics):
    """
    Build a formatted table using strings directly.

    FIX:
    Avoid assigning strings such as '100.82%'
    into pandas float64 columns.
    """

    available = [
        metric
        for metric in metrics
        if metric in summary.columns
    ]

    formatted = {
        ticker: [
            format_metric(
                summary.loc[ticker, metric],
                metric
            )
            for metric in available
        ]
        for ticker in summary.index
    }

    display = pd.DataFrame(
        formatted,
        index=available,
        dtype=str
    )

    display.index.name = "Financial Metric"

    return display


def show_metric_section(summary, metrics):
    """Display a formatted financial metrics table."""

    st.dataframe(
        format_table(summary, metrics),
        use_container_width=True
    )


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.title("📈 FinAgent")

    st.caption(
        "AI-powered financial analytics and reporting"
    )

    st.divider()

    st.subheader("Analysis Guide")

    st.markdown(
        """
        Describe the stocks you want to analyze
        using ordinary language.

        **Example requests:**

        - Compare Apple and Microsoft over 5 years.
        - Analyze Tesla and Nvidia using weekly data.
        - Compare Amazon, Google, and Meta over 3 years.

        FinAgent interprets your request and
        generates financial analytics automatically.
        """
    )

    st.divider()

    st.caption(
        "Data: Yahoo Finance | AI: Google Gemini"
    )


# ==================================================
# MAIN HEADER
# ==================================================

st.title("FinAgent")

st.markdown(
    "### AI-Powered Stock Analytics"
)

st.write(
    "Analyze stocks, compare financial performance, "
    "measure investment risk, and generate "
    "editable Excel reports."
)


# ==================================================
# USER INPUT
# ==================================================

user_request = st.text_area(
    "What would you like to analyze?",
    placeholder=(
        "Compare Apple, Microsoft, and Nvidia "
        "over the past five years using monthly data."
    ),
    height=110
)

analyze_button = st.button(
    "Analyze Stocks",
    type="primary",
    use_container_width=True
)


# ==================================================
# RUN ANALYSIS
# ==================================================

if analyze_button:

    if not user_request.strip():

        st.warning(
            "Please enter an analysis request."
        )

    else:

        with st.spinner(
            "FinAgent is analyzing the market..."
        ):

            try:

                analysis = run_finagent(
                    user_request
                )

                st.session_state[
                    "analysis"
                ] = analysis

                st.success(
                    "Financial analysis completed successfully!"
                )

            except Exception as error:

                st.error(
                    f"Analysis failed: {error}"
                )


# ==================================================
# DISPLAY RESULTS
# ==================================================

if "analysis" in st.session_state:

    analysis = st.session_state["analysis"]

    instructions = analysis["instructions"]
    prices = analysis["prices"]
    results = analysis["results"]
    report_path = analysis["report_path"]

    summary = results["summary"]

    st.divider()

    st.header("Financial Analysis Dashboard")

    # ------------------------------------------
    # ANALYSIS OVERVIEW
    # ------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Stocks Analyzed",
        len(prices.columns)
    )

    col2.metric(
        "Analysis Period",
        instructions["period"]
    )

    col3.metric(
        "Frequency",
        instructions["frequency"].capitalize()
    )

    col4.metric(
        "Financial Metrics",
        len(summary.columns)
    )

    st.caption(
        "Tickers: " + ", ".join(prices.columns)
    )

    # ------------------------------------------
    # PERFORMANCE OVERVIEW
    # ------------------------------------------

    st.subheader("Performance Overview")

    overview_metrics = [
        "Total Return",
        "Annualized Return",
        "Annualized Volatility",
        "Sharpe Ratio"
    ]

    st.dataframe(
        format_table(
            summary,
            overview_metrics
        ),
        use_container_width=True
    )

    # ------------------------------------------
    # ANALYTICS TABS
    # ------------------------------------------

    tabs = st.tabs([
        "Returns",
        "Risk",
        "Risk-Adjusted",
        "Market Behavior",
        "Stock Comparison"
    ])

    # ==========================================
    # TAB 1 — RETURNS
    # ==========================================

    with tabs[0]:

        st.subheader("Return Analysis")

        show_metric_section(
            summary,
            RETURN_METRICS
        )

        st.markdown(
            "#### Growth of Initial $100"
        )

        st.line_chart(
            results["growth"],
            use_container_width=True
        )

        st.markdown(
            "#### Cumulative Returns"
        )

        st.line_chart(
            results["cumulative_returns"] * 100,
            use_container_width=True
        )

        st.caption(
            "Cumulative returns are displayed "
            "as percentages."
        )

    # ==========================================
    # TAB 2 — RISK
    # ==========================================

    with tabs[1]:

        st.subheader("Risk Analysis")

        show_metric_section(
            summary,
            RISK_METRICS
        )

        st.markdown(
            "#### Historical Drawdowns"
        )

        st.line_chart(
            results["drawdown"] * 100,
            use_container_width=True
        )

        st.caption(
            "Drawdowns measure percentage declines "
            "from previous price peaks. "
            "VaR and CVaR are historical "
            "one-period estimates, not forecasts."
        )

    # ==========================================
    # TAB 3 — RISK-ADJUSTED
    # ==========================================

    with tabs[2]:

        st.subheader(
            "Risk-Adjusted Performance"
        )

        show_metric_section(
            summary,
            RISK_ADJUSTED_METRICS
        )

        st.info(
            "Sharpe measures excess return relative "
            "to total volatility. Sortino focuses "
            "on downside risk, while Calmar compares "
            "annualized growth with maximum drawdown."
        )

    # ==========================================
    # TAB 4 — MARKET BEHAVIOR
    # ==========================================

    with tabs[3]:

        st.subheader("Market Behavior")

        show_metric_section(
            summary,
            MARKET_METRICS
        )

        st.markdown(
            """
            **Skewness:** Measures asymmetry in
            the return distribution.

            **Excess Kurtosis:** Measures tail
            behavior relative to a normal distribution.

            **Positive Period Percentage:** Share
            of periods with positive returns.

            **Longest Losing Streak:** Largest
            number of consecutive negative-return
            periods.
            """
        )

    # ==========================================
    # TAB 5 — STOCK COMPARISON
    # ==========================================

    with tabs[4]:

        st.subheader("Stock Comparison")

        st.markdown(
            "#### Correlation Matrix"
        )

        st.dataframe(
            results["correlation"].style.format(
                "{:.3f}"
            ),
            use_container_width=True
        )

        st.markdown(
            "#### Periodic Covariance"
        )

        st.dataframe(
            results["covariance"].style.format(
                "{:.5f}"
            ),
            use_container_width=True
        )

        st.markdown(
            "#### Annualized Covariance"
        )

        st.dataframe(
            results[
                "annualized_covariance"
            ].style.format("{:.5f}"),
            use_container_width=True
        )

        st.caption(
            "Correlation measures the direction "
            "and strength of linear relationships. "
            "Covariance measures how returns "
            "move together."
        )

    # ------------------------------------------
    # HISTORICAL DATA
    # ------------------------------------------

    st.divider()

    with st.expander(
        "View Historical Stock Prices"
    ):

        st.dataframe(
            prices.style.format("{:.2f}"),
            use_container_width=True
        )

    with st.expander(
        "View Periodic Returns"
    ):

        st.dataframe(
            results["returns"].style.format(
                "{:.2%}"
            ),
            use_container_width=True
        )

    # ------------------------------------------
    # DOWNLOAD EXCEL REPORT
    # ------------------------------------------

    st.divider()

    st.subheader(
        "Download Financial Report"
    )

    st.write(
        "Download the complete Excel workbook "
        "with 19 financial metrics, historical "
        "prices, correlations, covariance matrices, "
        "drawdowns, and editable formulas."
    )

    path = Path(report_path)

    if path.exists():

        with open(path, "rb") as file:

            st.download_button(
                label="Download Excel Report",
                data=file,
                file_name=path.name,
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
                use_container_width=True
            )

    else:

        st.warning(
            "Excel report file could not be found."
        )

    st.caption(
        "FinAgent provides historical financial "
        "analytics for research and educational "
        "purposes. Results are not investment advice."
    )

else:

    st.info(
        "Enter a stock analysis request above "
        "to get started."
    )
