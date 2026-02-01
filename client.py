import asyncio
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

LLM_API_KEY = "dummy" 
LLM_BASE_URL = "http://localhost:11434/v1"
LLM_MODEL = "qwen2.5:3b"

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"], 
        env=os.environ
    )

    # Connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            await session.initialize()
            tools = await session.list_tools()
            print(f"Client connected. Found tools: {[t.name for t in tools.tools]}")

            # Format the tools for Qwen/Ollama
            openai_tools = [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            } for tool in tools.tools]

            user_query = "Can you do 1000 + 200 for me?"
            print(f"\nUser: {user_query}")
            
            messages = [{"role": "user", "content": user_query}]

            client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
            response = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=openai_tools
            )

            # Check if Qwen wants to use a tool
            tool_calls = response.choices[0].message.tool_calls

            if tool_calls:
                messages.append(response.choices[0].message)

                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    func_args = tool_call.function.arguments
                    
                    print(f"Qwen wants to use tool: '{func_name}' with args {func_args}")

                    try:
                        args_dict = json.loads(func_args)
                        
                        # We ask the server to run the code
                        result = await session.call_tool(func_name, arguments=args_dict)
                        tool_output = result.content[0].text
                        
                        print(f"🔧 Server Result: {tool_output}")

                        # Send the result back to Qwen
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_output
                        })
                    except Exception as e:
                        print(f" Error: {e}")

                # Get the final natural language answer
                final_response = await client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=messages
                )
                print(f"\nFinal Answer: {final_response.choices[0].message.content}")
            else:
                print("LLM did not use any tools.")

if __name__ == "__main__":
    asyncio.run(main())