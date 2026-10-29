"""
LangGraph Agent Core for DocFlow.
Connects local vLLM, uses Pydantic for structured outputs,
and integrates with the MCP server tools.
"""

import os
from typing import TypedDict, Annotated
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from agent_core.schemas import InvoiceSchema


# Define the state of our LangGraph agent
class AgentState(TypedDict):
    messages: list


async def run_docflow_agent(invoice_text: str):
    """
    Main asynchronous function to run the agent workflow:
    1. Connects to the local MCP server via stdio.
    2. Loads MCP tools into LangChain format.
    3. Initializes vLLM local model with structured output support.
    4. Compiles and executes the LangGraph agent workflow.
    """
    # 1. Configure connection to the local MCP server script
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()

            # Load tools exposed by the MCP server automatically
            mcp_tools = await load_mcp_tools(session)

            # 2. Initialize local LLM via vLLM (OpenAI-compatible local endpoint)
            llm = ChatOpenAI(
                model="Qwen/Qwen2.5-7B-Instruct",  # Or your loaded local model in vLLM
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

            # 5. Run the agent with the user input (simulated invoice text)
            initial_message = HumanMessage(
                content=f"Please process this invoice and save the data to Excel using the available tool:\n\n{invoice_text}"
            )

            print("--- Running DocFlow Agent Workflow ---")
            async for event in app.astream({"messages": [initial_message]}):
                for value in event.values():
                    print("Step output:", value["messages"][-1])


if __name__ == "__main__":
    import asyncio

    # Sample raw invoice text for testing
    sample_invoice = """
    INVOICE #2026-100
    Provider: Office Supplies Madrid S.L.
    Tax ID: B87654321
    Date: 2026-10-29
    Items:
    - Ergonomic Desk Chair: Subtotal 200.00 EUR
    VAT (21%): 42.00 EUR
    Total Due: 242.00 EUR
    """

    asyncio.run(run_docflow_agent(sample_invoice))
