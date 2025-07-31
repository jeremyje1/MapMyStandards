# 04 – AutoGen agent assembly

```python
from autogen import Agent, GroupChat, AssistantAgent, UserProxyAgent

mapper = AssistantAgent(name="Mapper", llm_config={"model": "claude-sonnet-4"})
narrator = AssistantAgent(name="Narrator", llm_config={"model": "gpt-4o"})
gap_finder = AssistantAgent(name="GapFinder", llm_config={"model": "gpt-4o"})
verifier = AssistantAgent(name="Verifier", llm_config={"model": "claude-sonnet-4"})

chat = GroupChat(
    agents=[UserProxyAgent(...), mapper, gap_finder, narrator, verifier],
    messages=[]
)
```

**Agent roles:**

* **Mapper** – returns JSON `{standard_id: [evidence_ids]}`
* **GapFinder** – compares required vs mapped; outputs RYG matrix.
* **Narrator** – crafts markdown narrative blocks with inline `[source]` tags.
* **Verifier** – re‑queries vector DB to confirm citations; rewrites if ≤ 0.85.

**Critic loop**—`GroupChat.run(max_rounds=3)` ensures converged answer.

Unit tests (`pytest agents/`) run in CI; accuracy target 92 %.
