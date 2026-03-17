# LangChain Import Options - Quick Reference

## Current Implementation (Recommended) ✅

**What we're using:**
```python
from langchain.agents import initialize_agent, AgentType

agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    agent_kwargs={"system_message": SYSTEM_PROMPT}
)
```

**Why it works:**
- ✅ Stable since LangChain 0.0.x
- ✅ Works across all versions (0.0.x, 0.1.x, 0.2.x, 1.x)
- ✅ No import path changes
- ✅ Simple and reliable

---

## Alternative Stable Options

### Option 1: `create_openai_tools_agent` (Also Stable)

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

**When to use:**
- Need more control over prompt structure
- Want explicit prompt templates
- Building complex multi-step agents

### Option 2: Using `load_tools` (For Built-in Tools)

```python
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.agents import initialize_agent, AgentType

# Load built-in tools (e.g., "serpapi", "llm-math")
tools = load_tools(["serpapi", "llm-math"], llm=llm)

# Add custom tools
tools.append(get_city_weather_forecast)

agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS
)
```

**When to use:**
- Combining our custom tools with LangChain's built-in tools
- Need search, math, or other standard capabilities

---

## Import Compatibility Matrix

| Import | LangChain 0.0.x | LangChain 0.1.x | LangChain 0.2.x | LangChain 1.x |
|--------|----------------|-----------------|-----------------|---------------|
| `initialize_agent` | ✅ | ✅ | ✅ | ✅ |
| `create_openai_tools_agent` | ✅ | ✅ | ✅ | ✅ |
| `create_openai_functions_agent` | ✅ | ✅ | ❌ Deprecated | ❌ Removed |
| `create_tool_calling_agent` | ❌ | ⚠️ Varies | ⚠️ Varies | ✅ |

**Legend:**
- ✅ Stable and available
- ⚠️ Import path varies by version
- ❌ Not available or removed

---

## What's Currently in agent.py

The code includes:

1. **Active Implementation:**
   ```python
   from langchain.agents import initialize_agent, AgentType
   # Using initialize_agent (bulletproof approach)
   ```

2. **Commented Alternative:**
   ```python
   # Alternative implementation using create_openai_tools_agent (also stable):
   # from langchain.agents import AgentExecutor, create_openai_tools_agent
   # ... (see code for full example)
   ```

3. **Reference Imports:**
   ```python
   # Alternative stable imports (all work with current LangChain versions):
   # from langchain.agents import AgentExecutor, create_openai_tools_agent
   # from langchain_community.agent_toolkits.load_tools import load_tools
   ```

---

## To Switch Implementations

### If you want to try `create_openai_tools_agent`:

1. Uncomment the alternative implementation in `create_travel_agent()`
2. Comment out the current `initialize_agent` call
3. Add the required prompt imports at the top:
   ```python
   from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
   ```

Both approaches produce identical results!

---

## Recommended Approach

**Stick with `initialize_agent`** unless you need:
- Custom prompt engineering beyond system messages
- Fine-grained control over agent scratchpad
- Complex multi-turn conversations with memory

For our Travel Assistant use case, `initialize_agent` is perfect! ✅

---

## Troubleshooting

### Still getting import errors?

```bash
# Ensure all packages are up to date
pip install --upgrade langchain langchain-openai langchain-core langchain-community

# Or install fresh
pip uninstall langchain langchain-openai langchain-core langchain-community -y
pip install -r requirements.txt
```

### Check your versions:

```bash
pip show langchain langchain-openai langchain-core langchain-community
```

All should be >= 0.1.0 for best compatibility.

---

**Current Status**: ✅ Using the most stable, battle-tested approach!
