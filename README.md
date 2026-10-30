# DocFlow MCP Agent 📄📊

An intelligent, fully autonomous local document management agent designed to process real invoice PDFs, extract structured financial metadata using a locally hosted LLM, and update an Excel report via custom Model Context Protocol (MCP) tools.

## 🏗️ System Architecture

The project leverages a decoupled, local-first architecture built across three main layers:

```
[ PDF Ingestion ] 
       │
       ▼
[ agent_core/agent.py (LangGraph) ] ◄──► [ mcp_server/server.py (MCP Tool) ] ──► [ Excel Output ]
       │
       ▼
[ Docker Container: vLLM + Qwen2.5-7B ]
```

## 🧩 Core Components & Design

### 1. Model Layer (vLLM Engine)

* **Containerized Inference:** Runs inside a Docker container configured with GPU passthrough to leverage local hardware (such as NVIDIA RTX series).
* **Model:** `Qwen/Qwen2.5-7B-Instruct`, optimized for instruction following and structured outputs.
* **API Compatibility:** Exposes an OpenAI-compatible HTTP interface at `http://localhost:8000/v1`.
* **Tool Calling:** Configured with `--enable-auto-tool-choice` and `--tool-call-parser hermes` to support standard function calling.

### 2. Tools Layer (MCP Server)

* **Model Context Protocol (MCP):** Implements the official Python MCP SDK (`FastMCP`) to expose standard executable tools.
* **Decoupled Logic:** The agent discovers tools dynamically over standard input/output (`stdio`) without hardcoded tool implementations inside the agent script.
* **Excel Writer:** The `append_invoice_to_excel` tool parses incoming structured parameters (Provider, Tax ID, Date, Subtotal, VAT, Total) using `pandas` and `openpyxl`, maintaining persistent record logs.

### 3. Orchestration Layer (LangGraph & LangChain)

* **State Machine:** Uses `StateGraph` to define a deterministic loop (*Agent Reasoning* ➔ *Tool Execution* ➔ *Response Synthesis*).
* **PDF Extraction:** Integrates `pypdf` to extract raw text content from PDF invoices placed in `sample_data/invoice.pdf`.
* **Pydantic Validation:** Formats extracted details cleanly before passing them to the tool call.

## 📁 Repository Structure

```
docflow-mcp-agent/
├── docker-compose.yml       # Docker configuration for vLLM container
├── requirements.txt         # Lightweight Python dependencies
├── README.md                # Project documentation
├── LICENSE                  # Apache 2.0 License
├── mcp_server/
│   └── server.py            # FastMCP server exposing Excel append tool
├── agent_core/
│   ├── schemas.py           # Pydantic models for structured outputs
│   └── agent.py             # Main LangGraph agent execution script
├── sample_data/             # Folder for input documents (invoice.pdf)
└── output/                  # Generated Excel reports (processed_invoices.xlsx)
```

## 🚀 Getting Started

### Prerequisites

* Docker Desktop with NVIDIA Container Toolkit enabled
* Python 3.10+
* Git

### 1. Clone & Set Up Python Environment

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/docflow-mcp-agent.git
cd docflow-mcp-agent

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # On Windows PowerShell
# source venv/bin/activate # On Linux/macOS

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Start vLLM Local Server via Docker

```bash
docker compose up -d
```

Verify that the local server is running by querying the available models:

```bash
curl.exe http://localhost:8000/v1/models
```

### 3. Run the Agent

Place an invoice named `invoice.pdf` inside the `sample_data/` directory and execute the main agent script:

```bash
python agent_core/agent.py
```

The processed data will be automatically appended to `./output/processed_invoices.xlsx`.

## 🛡️ License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.