# Pipe Operator (`|`) in LangChain

## Introduction

In **LangChain Expression Language (LCEL)**, the **pipe operator (`|`)** is used to connect multiple components together into a single workflow or **chain**. It works similarly to a pipeline in Unix/Linux, where the output of one component becomes the input of the next component.

Instead of manually calling each step, the pipe operator allows us to compose them in a clean and readable way.

---

## Basic Syntax

```python
chain = component1 | component2 | component3
```

The data flows from **left to right**:

```
Input → component1 → component2 → component3 → Output
```

Each component receives the output of the previous component.

---

## Example: Prompt → Model → Parser

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

# Step 1: Create a prompt template
prompt = ChatPromptTemplate.from_template(
    "You are a helpful assistant. Write about {question}."
)

# Step 2: Initialize the LLM
model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=1.0,
    max_tokens=500
)

# Step 3: Create an output parser
parser = StrOutputParser()

# Step 4: Combine everything using the pipe operator
chain = prompt | model | parser

# Step 5: Invoke the chain
result = chain.invoke({"question": "Artificial Intelligence"})
print(result)
```

---

## How the Pipe Operator Works

Consider the following chain:

```python
chain = prompt | model | parser
```

The execution happens in this order:

### Step 1: Input

```python
{"question": "Artificial Intelligence"}
```

This dictionary is passed to the `prompt`.

---

### Step 2: Prompt Template

The `ChatPromptTemplate` replaces the placeholder `{question}` with the user input.

Template:

```text
You are a helpful assistant. Write about {question}.
```

Generated prompt:

```text
You are a helpful assistant. Write about Artificial Intelligence.
```

This formatted prompt is passed to the model.

---

### Step 3: Language Model

The model receives the formatted prompt and generates a response.

Example raw output:

```text
Artificial Intelligence (AI) is a branch of computer science that focuses on creating systems capable of performing tasks that typically require human intelligence...
```

The model's response is then passed to the parser.

---

### Step 4: Output Parser

`StrOutputParser()` extracts the text content from the model response and converts it into a plain Python string.

Final output:

```python
"Artificial Intelligence (AI) is a branch of computer science..."
```

---

## Visual Representation

```
                  User Input
                       │
                       ▼
        {"question": "Artificial Intelligence"}
                       │
                       ▼
          ┌────────────────────────┐
          │  ChatPromptTemplate    │
          │ "Write about {question}"│
          └───────────┬────────────┘
                      │
                      ▼
          ┌────────────────────────┐
          │   Gemini LLM Model     │
          │ Generates AI response  │
          └───────────┬────────────┘
                      │
                      ▼
          ┌────────────────────────┐
          │   StrOutputParser()    │
          │ Converts to string     │
          └───────────┬────────────┘
                      │
                      ▼
                Final Output
               (Python string)
```

---

## Equivalent Code Without the Pipe Operator

The following code performs the same operations manually:

```python
# Create the prompt
formatted_prompt = prompt.invoke({
    "question": "Artificial Intelligence"
})

# Call the model
model_response = model.invoke(formatted_prompt)

# Parse the output
final_output = parser.invoke(model_response)

print(final_output)
```

The pipe operator simplifies this to:

```python
chain = prompt | model | parser
result = chain.invoke({
    "question": "Artificial Intelligence"
})
```

---

## Why Use the Pipe Operator?

### 1. Cleaner Code

Instead of writing multiple function calls, you define the workflow once.

**Without pipe operator:**

```python
formatted_prompt = prompt.invoke(data)
response = model.invoke(formatted_prompt)
output = parser.invoke(response)
```

**With pipe operator:**

```python
chain = prompt | model | parser
output = chain.invoke(data)
```

---

### 2. Better Readability

The pipeline clearly shows the order of execution:

```
Prompt → Model → Parser
```

Anyone reading the code can immediately understand the flow.

---

### 3. Easy to Extend

Suppose you want to add another processing step.

Without pipe operator:

```python
formatted_prompt = prompt.invoke(data)
response = model.invoke(formatted_prompt)
processed = custom_step.invoke(response)
output = parser.invoke(processed)
```

With pipe operator:

```python
chain = prompt | model | custom_step | parser
```

---

## Data Flow Example

Given:

```python
chain = prompt | model | parser
```

and

```python
chain.invoke({
    "question": "Machine Learning"
})
```

The data flows like this:

```
{"question": "Machine Learning"}
               │
               ▼
ChatPromptTemplate
               │
               ▼
"You are a helpful assistant. Write about Machine Learning."
               │
               ▼
ChatGoogleGenerativeAI
               │
               ▼
AI-generated response
               │
               ▼
StrOutputParser()
               │
               ▼
Plain Python string
```

---

## Pipe Operator and Input/Output Schemas

Every component in the chain has an input type and an output type.

For example:

| Component                | Input                            | Output            |
| ------------------------ | -------------------------------- | ----------------- |
| `ChatPromptTemplate`     | Dictionary (`{"question": ...}`) | `ChatPromptValue` |
| `ChatGoogleGenerativeAI` | `ChatPromptValue`                | `AIMessage`       |
| `StrOutputParser`        | `AIMessage`                      | `str`             |

The pipe operator automatically connects compatible input and output types.

For the chain:

```python
chain = prompt | model | parser
```

The input schema is:

```python
{
    "properties": {
        "question": {
            "title": "Question",
            "type": "string"
        }
    },
    "required": ["question"],
    "title": "PromptInput",
    "type": "object"
}
```

The output schema is:

```python
{
    "title": "StrOutputParserOutput",
    "type": "string"
}
```

This means:

* **Input:** A dictionary containing a required string field called `question`.
* **Output:** A plain Python string.

---

## Key Points to Remember

* The **pipe operator (`|`)** is used to combine LangChain components into a single workflow.
* Data always flows **from left to right**.
* The output of one component automatically becomes the input of the next component.
* It makes code **cleaner, more readable, and easier to maintain**.
* A typical LangChain pipeline is:

```python
chain = prompt | model | parser
```

which represents:

```
User Input → Prompt Template → LLM → Output Parser → Final Result
```

---

## Summary

The LangChain pipe operator (`|`) is the foundation of the **LangChain Expression Language (LCEL)**. It allows developers to build AI workflows by chaining together prompts, models, parsers, retrievers, and other components in a simple, declarative manner.

A pipeline like:

```python
chain = prompt | model | parser
```

is equivalent to saying:

> "Take the user's input, format it using the prompt template, send it to the language model, parse the model's response into a string, and return the final result."

This design makes LangChain applications modular, reusable, and easy to understand.
