"""
LangGraph Agent Core for DocFlow.
Connects local vLLM, uses Pydantic for structured outputs,
and integrates with the MCP server tools, reading from a real PDF invoice.
"""
import os
import asyncio
from typing import TypedDict
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from pypdf import PdfReader

# Define the state of our LangGraph agent
class AgentState(TypedDict):
    messages: list

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text content from a given PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

async def run_docflow_agent():
    """
    Main asynchronous function to run the agent workflow:
    1. Reads invoice text from 'sample_data/invoice.pdf'.
    2. Connects to the local MCP server via stdio.
    3. Loads MCP tools into LangChain format.
    4. Initializes vLLM local model with tool calling support.
    5. Compiles and executes the LangGraph agent workflow.
    """
    pdf_file_path = Path("sample_data/google202604.pdf")

    if not pdf_file_path.exists():
        print(f"Error: The file {pdf_file_path} was not found. Please place an invoice.pdf inside the sample_data/ folder.")
        return

    print(f"Reading invoice from {pdf_file_path}...")
    invoice_text = extract_text_from_pdf(str(pdf_file_path))

    # 1. Configure connection to the local MCP server script
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with asyncio.timeout(30):
            from mcp import ClientSession
            async with ClientSession(read, write) as session:
                # Initialize session
                await session.initialize()

                # Load tools exposed by the MCP server automatically
                mcp_tools = await load_mcp_tools(session)

                # 2. Initialize local LLM via vLLM (OpenAI-compatible local endpoint in Docker)
                llm = ChatOpenAI(
                    model="qwen2.5-7b-instruct",
                    openai_api_base="http://localhost:8000/v1",
                    openai_api_key="not-needed-for-local",
                    temperature=0.0
                ).bind_tools(mcp_tools)

                # 3. Define LangGraph nodes
                def call_model(state: AgentState):
                    messages = state["messages"]
                    response = llm.invoke(messages)
                    return {"messages": messages + [response]}

                # Define the tool execution node using LangGraph's prebuilt ToolNode
                tool_node = ToolNode(mcp_tools)

                # Check whether to continue or end the graph
                def should_continue(state: AgentState):
                    messages = state["messages"]
                    last_message = messages[-1]
                    if last_message.tool_calls:
                        return "tools"
                    return END

                # 4. Build the State Graph
                workflow = StateGraph(AgentState)
                workflow.add_node("agent", call_model)
                workflow.add_node("tools", tool_node)
                workflow.set_entry_point("agent")
                workflow.add_conditional_edges("agent", should_continue)
                workflow.add_edge("tools", "agent")
                app = workflow.compile()

                # 5. Run the agent with the text extracted from the PDF
                initial_message = HumanMessage(
                    content=f"Please process this invoice, extract its structured details, and save the data to Excel using the available tool:\n\n{invoice_text}"
                )

                print("--- Running DocFlow Agent Workflow ---")
                async for event in app.astream({"messages": [initial_message]}):
                    for value in event.values():
                        print("Step output:", value["messages"][-1])

if __name__ == "__main__":
    asyncio.run(run_docflow_agent())