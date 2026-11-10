
# FinAgent — AI-Powered Stock Analytics

FinAgent is a Python-based financial analytics application that combines natural-language AI with a predefined financial analysis engine. It allows users to analyze and compare publicly traded stocks simply by describing what they want to examine in everyday language.

The application retrieves historical market data, calculates 19 financial performance and risk metrics, displays the results through an interactive dashboard, and generates downloadable Excel reports with editable financial formulas.

## Demo

**Video demonstration:** [https://drive.google.com/file/d/1t4hDjI3Y2uxLKXfdZ0QgjrjdtccmWiq4/view?usp=drive_link]

## How It Works

FinAgent separates natural-language interpretation from financial computation.

1. **User Input:** A user enters a request, such as "Compare Apple, Microsoft, and Nvidia over the past five years using monthly data."

2. **AI Interpretation:** Google's Gemini model interprets the request and extracts structured parameters, including stock tickers, analysis period, data frequency, and risk-free rate.

3. **Data Retrieval:** The application retrieves historical adjusted stock prices from Yahoo Finance using the `yfinance` Python library.

4. **Financial Analysis:** A Python analytics engine calculates financial statistics using predefined formulas. The AI does not generate or calculate the financial results.

5. **Validation:** A separate Python module independently recalculates the financial metrics and checks the structure of the generated Excel workbook.

6. **Visualization:** Streamlit presents the results through an interactive dashboard with financial tables and performance charts.

7. **Excel Reporting:** The application produces a downloadable Excel workbook containing financial calculations, editable formulas, and supporting data.

### Application Architecture

```text
Natural-Language User Request
             |
             v
     Google Gemini AI
     (Request Interpretation)
             |
             v
    Structured Parameters
    (Tickers, Period, Frequency)
             |
             v
     Yahoo Finance API
      via yfinance
             |
             v
    Python Analytics Engine
      (19 Financial Metrics)
             |
             v
      Validation Module
             |
             v
     Streamlit Dashboard
             |
             v
    Downloadable Excel Report
```

## Financial Analytics

FinAgent currently calculates 19 financial metrics across four categories.

### Return Analysis
- Total Return
- Compound Annual Growth Rate (CAGR)
- Average Periodic Return
- Annualized Arithmetic Return
- Best Period
- Worst Period

### Risk Analysis
- Annualized Volatility
- Maximum Drawdown
- Average Drawdown
- Downside Deviation
- Historical Value at Risk (95%)
- Historical Conditional Value at Risk (95%)

### Risk-Adjusted Performance
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio

### Market Behavior
- Skewness
- Excess Kurtosis
- Percentage of Positive Return Periods
- Longest Losing Streak

### Additional Stock Comparisons
- Correlation Matrix
- Periodic and Annualized Covariance Matrices
- Growth of an Initial $100 Investment
- Cumulative Returns
- Historical Drawdown Charts

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Core application and financial calculations |
| Google Gemini | Natural-language request interpretation |
| yfinance | Historical stock market data retrieval |
| pandas | Data manipulation and financial time series |
| NumPy | Numerical calculations |
| Streamlit | Interactive web dashboard |
| openpyxl | Excel report generation and formulas |
| Pydantic | Structured AI output validation |

## Project Structure

```text
FinAgent/
|
|-- app.py                  # Streamlit dashboard
|-- main.py                 # Application workflow
|-- agent.py                # Gemini AI request interpreter
|-- data.py                 # Stock market data retrieval
|-- analytics.py            # Financial analytics engine
|-- excel.py                # Excel report generator
|-- finagent_validators.py  # Financial calculation validation
|-- requirements.txt        # Python dependencies
|-- README.md               # Project documentation
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/kbwalya17/FinAgent.git
cd FinAgent
```

### 2. Install dependencies

Python 3.11 or newer is recommended.

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Google Gemini

Obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

Create a `.env` file in the project directory:

```env
GEMINI_API_KEY=your_api_key_here
```

Keep this file private. Do not upload API keys to GitHub.

### 4. Launch the application

```bash
python -m streamlit run app.py
```

Streamlit will display a local URL, typically:

```text
http://localhost:8501
```

Open the URL in your browser.

## Example Request

> Compare Apple, Microsoft, and Nvidia over the past five years using monthly data.

FinAgent interprets the request, retrieves the historical data, calculates the financial metrics, and presents the results in the dashboard.

Users can then download the Excel report for further analysis.

## Validation and Reliability

FinAgent includes a dedicated validation module that independently recalculates the 19 financial metrics and checks correlation and covariance matrices.

The module also verifies the presence of expected worksheets and formulas in the Excel report.

The financial calculations are implemented in Python rather than generated by the language model, improving consistency and reproducibility.


## Limitations

- The application analyzes historical prices and does not predict future stock returns.
- Results depend on the availability and quality of Yahoo Finance data.
- Annualization assumes standard daily, weekly, or monthly observation frequencies.
- The most recent trading period may be incomplete.
- Historical VaR and CVaR are descriptive risk estimates, not guarantees of future losses.
- Benchmark-relative analytics and technical indicators are not included in this version.

## Author

**Kabungo Bwalya**


[GitHub Profile](https://github.com/kbwalya17)

## Disclaimer

FinAgent is an independent project developed for educational, research, and financial analytics purposes. It does not provide personalized investment advice or recommendations.
