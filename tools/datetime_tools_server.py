from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DateTimeTools")

import logging
logging.getLogger("mcp.server").setLevel(logging.WARNING)

@mcp.tool()
def current_datetime() -> str:
    """Returns the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool()
def days_until(date_str: str) -> int:
    """Returns the number of days from today until a future date.
    
    Args:
        date_str: A date in 'YYYY-MM-DD' format
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    delta = target_date - datetime.now()
    return max(delta.days, 0)

if __name__ == "__main__":
    mcp.run(transport="stdio")