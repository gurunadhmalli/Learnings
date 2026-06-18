# LangChain V1 Architecture & Runnables

## The V1 Architecture

    +----------------------------------------------+
    |              Your Application                |
    +----------------------------------------------+
    |         Chains & Agents (langchain)          |
    +----------------------------------------------+
    |   LCEL (LangChain Expression Language)       |
    +----------------------------------------------+
    |      Runnables (langchain-core)              |
    +----------------------------------------------+
    | Model Integrations (OpenAI, Claude, etc.)    |
    +----------------------------------------------+

### Your Application

The final AI solution you build, such as a chatbot, RAG application, or
AI assistant.

### Chains & Agents

-   **Chains:** Fixed sequence of steps (Prompt → Model → Output).
-   **Agents:** Dynamic workflows that decide which tool or action to
    use.

### LCEL (LangChain Expression Language)

The modern pipeline syntax introduced in V1.

Example:

``` python
chain = prompt | model | output_parser
```

Benefits: - Cleaner syntax. - Easy composition. - Supports streaming and
async execution.

### Runnables (`langchain-core`)

The foundation of LangChain V1. A Runnable is any component that accepts
input and produces output.

### Model Integrations

Connects LangChain to providers such as OpenAI, Anthropic, Gemini,
Cohere, and others.

### Common Runnable Methods

  Method        Description
  ------------- -------------------------------
  `invoke()`    Run one input.
  `batch()`     Run multiple inputs together.
  `stream()`    Return output token-by-token.
  `ainvoke()`   Async version of `invoke()`.

------------------------------------------------------------------------

## Runnables -- The Foundation

The main idea of the second slide is:

> **Everything in LangChain V1 is a Runnable.**

              Everything is Runnable
                        |
          +------+------+------+------+
          |             |             |
       Prompts       Models    Output Parsers
             \         |          /
              \        |         /
                  Chains
                        |
         invoke() | batch() | stream()

### Prompts are Runnables

Prompt templates accept variables and generate formatted prompts.

### Models are Runnables

LLMs receive prompts and generate responses.

### Output Parsers are Runnables

They convert raw model output into structured formats.

### Chains are Composed Runnables

A chain is simply multiple Runnable components connected together.

Example:

``` python
chain = prompt | model | parser
result = chain.invoke({"topic": "LangChain"})
```

## Why Runnables Matter

### Older Versions

Different objects had different methods like `.run()` and `.predict()`.

### LangChain V1

Everything uses a unified interface: - `invoke()` - `batch()` -
`stream()` - `ainvoke()`

This makes LangChain easier to learn, compose, and maintain.

------------------------------------------------------------------------

## Interview Summary

**LangChain V1 uses a layered architecture. Model integrations are
wrapped as Runnables in `langchain-core`. LCEL builds pipelines using
these Runnables, while Chains and Agents provide higher-level workflows.
The most important idea is that prompts, models, output parsers, and
chains all implement the same Runnable interface, exposing methods like
`invoke()`, `batch()`, and `stream()`.**
