from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DateTimeTools")

import logging
logging.getLogger("mcp.server").setLevel(logging.WARNING)

@mcp.tool()
def current_datetime() -> str:
    """
    Use this tool to fetch the current date and time from the system clock.

    This is the only reliable way for the assistant to provide the real-time 
    date and time. It should be used whenever the user asks about the 
    current date, time, or timestamp.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool()
def days_until(date_str: str) -> int:
    """
    Calculates the number of days from today until a future date.

    Use this tool when the user asks something like "how many days until 2025-12-31?"
    or wants to know the number of days between today and a specific future date.

    Args:
        date_str: A date in 'YYYY-MM-DD' format
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    delta = target_date - datetime.now()
    return max(delta.days, 0)

if __name__ == "__main__":
    mcp.run(transport="stdio")