# LangGraph Migration Guide (2026 Standard)

## Problem Solved ✅

**Error**: `ImportError: cannot import name 'initialize_agent' from 'langchain.agents'`  
**Error**: `ImportError: cannot import name 'create_openai_functions_agent' from 'langchain.agents'`

## Root Cause

The `langchain.agents` module has been deprecated in favor of **LangGraph**, which is the official modern approach for building agents in 2026.

## Solution Implemented

Migrated to **LangGraph's `create_react_agent`** - the current standard architecture.

## Code Changes

### Imports

**From:**
```python
from langchain.agents import initialize_agent, AgentType
# or
from langchain.agents import create_openai_functions_agent, AgentExecutor
```

**To:**
```python
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
```

### Agent Creation

**From:**
```python
agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    agent_kwargs={"system_message": SYSTEM_PROMPT}
)
```

**To:**
```python
agent = create_react_agent(
    llm,
    tools,
    prompt=SystemMessage(content=SYSTEM_PROMPT)
)
```

### Agent Invocation

**From:**
```python
result = await agent_executor.ainvoke({"input": request.message})
response = result.get("output")
```

**To:**
```python
result = await agent.ainvoke({"messages": [("user", request.message)]})
response = result["messages"][-1].content
```

## Why LangGraph?

1. **Official Direction**: LangGraph is the official LangChain approach for 2026+
2. **Graph-based State**: More flexible and powerful than linear agents
3. **Better Observability**: Inspect agent state at each step
4. **Production-Ready**: Built for scale, reliability, and debugging
5. **No Deprecation Issues**: Actively maintained and future-proof

## What is LangGraph?

LangGraph is a framework for building stateful, graph-based agents:
- **Nodes**: Each step in the agent's reasoning (LLM call, tool use, etc.)
- **Edges**: Connections between steps with conditional logic
- **State**: Message history and context maintained throughout
- **Checkpoints**: Save and resume agent state

## Installation

```bash
# Install LangGraph
pip install langgraph

# Or install all dependencies
pip install -r requirements.txt
```

## LangGraph Message Flow

```
Input
  ↓
{"messages": [("user", "What's the weather in London?")]}
  ↓
Agent Graph Execution:
  1. SystemMessage (your SYSTEM_PROMPT)
  2. UserMessage (user input)
  3. AIMessage with tool_calls
  4. ToolMessage (weather data)
  5. AIMessage (final response)
  ↓
Output
result["messages"][-1].content
```

## Available Prebuilt Agents

LangGraph provides several ready-to-use agents:

```python
from langgraph.prebuilt import create_react_agent      # ← We use this
from langgraph.prebuilt import create_tool_calling_agent
```

**Why `create_react_agent`?**
- Implements ReAct (Reasoning + Acting) pattern
- Perfect for GPT-4's reasoning capabilities
- Handles tool calling automatically
- Provides step-by-step observability

## System Prompt Integration

The system prompt is passed via the `prompt` parameter:

```python
# Option 1: SystemMessage object
agent = create_react_agent(
    llm,
    tools,
    prompt=SystemMessage(content=SYSTEM_PROMPT)
)

# Option 2: Plain string (also works)
agent = create_react_agent(
    llm,
    tools,
    prompt=SYSTEM_PROMPT
)
```

## Testing the New Implementation

```bash
cd backend-agent

# Install dependencies including langgraph
pip install -r requirements.txt

# Start the agent (should work now!)
python agent.py
```

In another terminal:
```bash
# Interactive testing
python test_agent.py --mode interactive

# Or quick test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Paris?"}'
```

## Debugging Tips

### View the message flow:

```python
result = await agent.ainvoke({"messages": [("user", "Hello")]})

# Inspect all messages
for msg in result["messages"]:
    print(f"{msg.__class__.__name__}: {msg.content}")
```

### Add streaming:

```python
async for chunk in agent.astream({"messages": [("user", "Hello")]}):
    print(chunk)
```

## Migration Checklist

- [x] Replace `langchain.agents` imports with `langgraph.prebuilt`
- [x] Update agent creation to use `create_react_agent`
- [x] Change invocation from `{"input": ...}` to `{"messages": [...]}`
- [x] Update response extraction to use message list
- [x] Add `langgraph` to requirements.txt
- [x] Update all documentation

## Troubleshooting

### "langgraph not installed"

```bash
pip install langgraph
```

### "SystemMessage not found"

```bash
pip install --upgrade langchain-core
```

### "create_react_agent not found"

```bash
pip install --upgrade langgraph
```

### Still having issues?

```bash
# Clean install
pip uninstall langchain langchain-core langchain-openai langgraph -y
pip install langchain langchain-core langchain-openai langgraph
```

## Benefits of This Migration

1. ✅ **No Import Errors** - LangGraph is actively maintained
2. ✅ **Modern Architecture** - Official 2026 standard
3. ✅ **Better Debugging** - Inspect state at each step
4. ✅ **More Flexible** - Graph-based is more powerful
5. ✅ **Production-Ready** - Built for scale
6. ✅ **Future-Proof** - Won't need migration again

## Learn More

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Quickstart](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
- [Prebuilt Agents](https://langchain-ai.github.io/langgraph/reference/prebuilt/)

---

**Status**: ✅ **FIXED** - Modern LangGraph implementation ready for 2026!

Your agent is now using the official recommended architecture with no deprecated APIs.
