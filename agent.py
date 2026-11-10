
import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv(Path(__file__).resolve().parent / ".env")

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

MODEL = "gemini-3.5-flash-lite"


class AnalysisRequest(BaseModel):
    tickers: list[str] = Field(
        description="Stock ticker symbols, e.g. AAPL, MSFT"
    )

    period: str = Field(
        description="Historical period, e.g. 1y, 3y, 5y"
    )

    frequency: str = Field(
        description="daily, weekly, or monthly"
    )

    risk_free_rate: float = Field(
        description="Annual risk-free rate as a decimal"
    )


def interpret_request(user_request):
    """
    Convert a natural-language request into
    structured financial analysis instructions.
    """

    prompt = f"""
    You are the request interpreter for FinAgent.

    Extract financial analysis parameters from the
    user's request.

    Rules:
    - Convert company names into stock ticker symbols.
    - Use 5y if no historical period is specified.
    - Use monthly if no frequency is specified.
    - Use 0.04 if no risk-free rate is specified.
    - Only use daily, weekly, or monthly frequency.
    - Return valid ticker symbols.
    - Do not invent tickers for ambiguous companies.
    - Do not provide financial advice.

    User request:
    {user_request}
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": AnalysisRequest.model_json_schema()
        }
    )

    instructions = AnalysisRequest.model_validate_json(
        response.text
    )

    if not instructions.tickers:
        raise ValueError(
            "No recognizable stock tickers found."
        )

    if instructions.frequency not in [
        "daily", "weekly", "monthly"
    ]:
        raise ValueError("Unsupported frequency.")

    return instructions.model_dump()


if __name__ == "__main__":

    request = input(
        "\nWhat would you like FinAgent to analyze?\n> "
    )

    result = interpret_request(request)

    print("\nFinAgent — Interpreted Request")
    print(json.dumps(result, indent=4))
