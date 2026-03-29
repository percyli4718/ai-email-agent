# AI Email Agent

AI-powered email processing system for pharmaceutical distribution.

## Architecture

```
非结构化邮件 → Layer 1 分类 → Layer 2 检索 → Layer 3 生成 → 业务动作
```

### Three-Layer AI Architecture

1. **Layer 1: Classification (Sonnet)**
   - Email type identification
   - Priority scoring
   - Language detection
   - Routing decision

2. **Layer 2: Context Retrieval (ChromaDB + Ollama)**
   - Vector search for similar emails
   - Customer history lookup
   - Pricing policy matching
   - Compliance requirements

3. **Layer 3: Analysis & Generation (Opus/Sonnet Router)**
   - Intelligent model routing (80% Sonnet)
   - Structured quote generation
   - Multi-language reply drafting

### Agent Contract System

- **CEO Agent**: Decomposes goals into dependency graphs
- **Sub-Agents**: Price, Compliance, Logistics, Reply
- **Sandbox Execution**: Budget hard kill, write isolation
- **CEO Review**: Promote/Redelegate/Reject decisions

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama running locally

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your API keys

# Run the server
python -m email_agent.main
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## API Endpoints

- `GET /api/emails` - List emails
- `GET /api/emails/{id}` - Get email detail
- `POST /api/emails/{id}/process` - Process email
- `GET /api/metrics` - Observability metrics
- `GET /api/traces` - Distributed traces
- `GET /api/health` - Health check

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=email_agent
```

## Project Structure

```
├── src/email_agent/
│   ├── layer1/          # Classification
│   ├── layer2/          # Retrieval
│   ├── layer3/          # Generation
│   ├── agents/          # Agent contract system
│   ├── observability/   # Metrics, tracing, budget
│   ├── storage/         # Database models
│   └── api/             # FastAPI routes
├── frontend/            # React UI
└── tests/               # Test suite
```

## License

MIT
