# Docs Index

Study notes for LangChain / LangGraph, numbered in the order they're meant to be read. Files are self-contained but build on each other — later ones assume earlier ones.

## Reading order

**Foundations**
1. [01_LangChain_V1_vs_Older_Versions_Explanation.md](01_LangChain_V1_vs_Older_Versions_Explanation.md) — V1 vs legacy LangChain, why the API changed
2. [02_LangChain_V1_Architecture_and_Runnables_Notes.md](02_LangChain_V1_Architecture_and_Runnables_Notes.md) — the Runnable interface, the core abstraction everything else builds on
3. [03_pipe_operator.md](03_pipe_operator.md) — the `|` operator, minimal LCEL example

**Building blocks**
4. [04_LangChain_Prompt_Templates_Notes.md](04_LangChain_Prompt_Templates_Notes.md) — ChatPromptTemplate, message types, few-shot prompting
5. [05_messages.md](05_messages.md) — SystemMessage/HumanMessage/AIMessage/ToolMessage, message history
6. [06_LLM_Model_Configuration_Notes.md](06_LLM_Model_Configuration_Notes.md) — temperature, model_kwargs, streaming, cost
7. [07_Chains.md](07_Chains.md) — full LCEL: composition patterns, parallel/sequential, debugging
8. [08_langchain_output_parsers.md](08_langchain_output_parsers.md) — quick-reference: parsers + `with_structured_output()`
9. [09_output_parser.md](09_output_parser.md) — output parsers deep dive (companion to 08)

**Data pipeline (RAG prep)**
10. [10_LangChain_Document_Loaders_Complete_Notes.md](10_LangChain_Document_Loaders_Complete_Notes.md) — loading PDFs, text, web pages, directories
11. [11_LangChain_Chunking_Complete_Reference.md](11_LangChain_Chunking_Complete_Reference.md) — text splitters, chunk size/overlap
12. [12_vectors.md](12_vectors.md) — embeddings & vector theory (distance metrics, cosine similarity)
13. [13_vector_stor.md](13_vector_stor.md) — vector stores in practice (Chroma, FAISS, Pinecone, retriever API)

**RAG**
14. [14_rag_overview.md](14_rag_overview.md) — hands-on: building a basic RAG chain, code walkthrough
15. [15_rag_own.md](15_rag_own.md) — library analogy, good vs bad chunking, RAG vs fine-tuning
16. [16_rag.md](16_rag.md) — **master reference**: the full RAG pipeline end to end, all fundamentals live here
17. [17_advanced_rag_reference.md](17_advanced_rag_reference.md) — advanced techniques, production architecture, evaluation metrics

**Memory & agents**
18. [18_langchain_memory_guide.md](18_langchain_memory_guide.md) — conversation memory, trimming, persistent + vector memory
19. [19_langgraph-complete-beginner-guide.md](19_langgraph-complete-beginner-guide.md) — StateGraph, nodes, edges
20. [20_langgraph_conditional_edges_and_routing.md](20_langgraph_conditional_edges_and_routing.md) — deep dive: direct vs conditional edges, `add_conditional_edges` syntax, `Literal`-typed routers, multi-way branching
21. [21_LangGraph_Accumulated_State_Explanation.md](21_LangGraph_Accumulated_State_Explanation.md) — reducers and `Annotated` state
22. [22_LangGraph_Cycles_and_Loops_Deep_Dive.md](22_LangGraph_Cycles_and_Loops_Deep_Dive.md) — deep dive: anatomy of a loop, 5 loop types (retry-until-valid, iterative-deepening, counted for-N, agentic/ReAct, human-in-the-loop), exit-condition design, `recursion_limit`/`GraphRecursionError` safety
23. [23_LangGraph_Human_in_the_Loop_Deep_Dive.md](23_LangGraph_Human_in_the_Loop_Deep_Dive.md) — deep dive: expands 22 §7 into full HITL coverage — `MemorySaver`/checkpointer, `thread_id`, `interrupt()` + `Command(resume=...)`, full email-assistant walkthrough
24. [24_LangGraph_Tool_Calling_and_Agents.md](24_LangGraph_Tool_Calling_and_Agents.md) — deep dive: `@tool`, `bind_tools`, reading/executing `tool_calls`, `ToolNode`, wiring the ReAct loop by hand vs. `create_react_agent` (no local code yet — see Gaps)
25. [25_LangGraph_Advanced_Checkpointer_Patterns.md](25_LangGraph_Advanced_Checkpointer_Patterns.md) — deep dive: walks through `checkpoint.py`/`human_in_loop.py` — `interrupt_before`+`update_state()` (the static pause, vs. 23's dynamic `interrupt()`), `SqliteSaver` durability, `get_state_history()` time travel, checkpoint anatomy, branching, rewinding
26. [26_LangGraph_MultiAgent_Handoff_Pattern.md](26_LangGraph_MultiAgent_Handoff_Pattern.md) — deep dive: walks through `agent_handsoff.py` — triage/router agent + specialist agents, `with_structured_output()` + `Literal` as a routing decision, shared context across agents, contrasted with the ReAct loop (24)

## What changed in this pass

- All files renamed with `NN_` prefixes to reflect the order above (content/filenames otherwise unchanged, just reordered).
- Added **20_langgraph_conditional_edges_and_routing.md**, a deep dive on direct vs conditional edges, `add_conditional_edges` syntax, `Literal`-typed routers, and multi-way branching (from course slides). It builds on 19's Edges section rather than replacing it. 20 (Accumulated State) was renumbered to 21 to make room.
- Added **22_LangGraph_Cycles_and_Loops_Deep_Dive.md**, covering the loop anatomy (loop body + progress field + router + exit) and five loop shapes, walking through the two working loops in `condtional_edges.py::demo_conditional_loop` and `cyclic_loop.py` (`demo_self_correcting_code`, `demo_iterative_research`), plus two loop types not yet present in the codebase (agentic/ReAct tool-calling loop, human-in-the-loop pause/resume) documented conceptually so the doc covers the full loop taxonomy, not just what's been coded so far. Builds on 20's `add_conditional_edges` mechanics and 21's `Annotated`/reducer state.
- Removed cross-file duplication in three overlapping clusters, keeping each file's unique content and adding pointers where material now lives elsewhere:
  - **08 ↔ 09** (output parsers): 08 trimmed to a quick-reference pointing to 09 for the deep dive.
  - **12 ↔ 13** (vectors): 13 trimmed of repeated theory (distance metrics, RAG flow diagram) now owned by 12.
  - **14 / 15 / 16 / 17** (RAG): 16 is now the canonical fundamentals + full-pipeline reference; 14 and 15 trimmed down to their unique hands-on code and analogies/comparisons respectively; 17 (advanced techniques) was already distinct and left untouched.

## What changed in this pass (round 2)

- Added **24_LangGraph_Tool_Calling_and_Agents.md**, **25_LangGraph_Advanced_Checkpointer_Patterns.md**, and **26_LangGraph_MultiAgent_Handoff_Pattern.md** to close the gaps below (except tool-calling, which is still doc-only — see Gaps).
- `checkpoint.py` and `human_in_loop.py` were added to the repo root since the last pass, closing the "no working code" half of the checkpointer/HITL gap — 25 documents what they actually demonstrate (SqliteSaver, time travel, branching, the older `interrupt_before`+`update_state` pause style), which goes beyond 23's `interrupt()`/`Command(resume=...)` coverage.
- `agent_handsoff.py`'s triage/specialist routing pattern (structured-output-based multi-agent handoff) now has a dedicated doc (26) instead of no coverage at all.

## Gaps — not yet covered by any doc

- **Tool-calling / agents proper** (`bind_tools`, `@tool`, `ToolNode`, `create_react_agent`) is now documented in **24_LangGraph_Tool_Calling_and_Agents.md**, but it's still notes-only — grep confirms no file in the repo (`agent_handsoff.py` included) actually calls `bind_tools` or defines a `@tool`. `agent_handsoff.py`'s "handoff" is LLM-persona routing via structured output (see 26), not function/tool calling. A small demo (e.g. a calculator or weather-lookup ReAct agent) would close this for real.
- `recursion_limit` / `GraphRecursionError` (the framework-level loop safety net, 22 §9) still isn't exercised by any current code — every existing loop (including the new checkpointed ones in `human_in_loop.py`) relies solely on its own state-level iteration cap or a human's decision to stop looping.
- `PostgresSaver` (named as the other production checkpointer alongside `SqliteSaver` in 23 and 25) has no local code either — only `MemorySaver` and `SqliteSaver` are exercised.
