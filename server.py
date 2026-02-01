from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("MathServer")

# The LLM will use this to add numbers instead of guessing.
@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """
    Adds two numbers together. 
    Use this tool when the user asks for math or addition.
    """
    print(f"   [SERVER LOG] Calculating {a} + {b}...")
    return a + b

# The LLM can read this file if it needs app info.
@mcp.resource("config://app-config")
def get_config() -> str:
    """Returns the application configuration as a JSON string."""
    try:
        with open("config.json", "r") as f:
            data = json.load(f)
        return json.dumps(data)
    except FileNotFoundError:
        return json.dumps({"error": "Config file not found"})

if __name__ == "__main__":
    # This runs the server and listens for commands
    mcp.run(transport='stdio')