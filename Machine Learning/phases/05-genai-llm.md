# Phase 5 — GenAI / LLM Engineering

**Weeks 32–37 · ~250 hours**

Everything before this was so that this phase is engineering rather than guesswork. The differentiator here is **evaluation and cost discipline** — anyone can build a demo.

---

## 5.1 Working with LLMs (Week 32, ~40h)

### Decoding and generation
- Greedy, beam search, sampling; **temperature**, top-k, top-p (nucleus), min-p, typical sampling
- Repetition penalty, frequency/presence penalty
- Stop sequences, max tokens, logit bias
- **Constrained decoding / structured outputs** — JSON schema enforcement, grammars (GBNF), Outlines/Guidance; function-calling APIs
- Speculative decoding, self-speculative, Medusa heads
- Logprobs and using them for confidence estimation

### Prompt engineering (as a real discipline)
- Zero-shot, few-shot, and how example selection changes results
- **Chain-of-thought**, self-consistency (sample k, majority vote), least-to-most, ReAct, Tree-of-Thoughts
- Role/system prompts, delimiters, output format specification
- Prompt chaining and decomposition — smaller, verifiable steps beat one giant prompt
- Self-critique and reflexion loops
- Context ordering: **the lost-in-the-middle effect** — put critical content at the start or end
- Prompt versioning and templating (Jinja); treat prompts as code, in git, with tests
- Automatic prompt optimization: DSPy, APE

### Model economics
- Token accounting; input vs output pricing asymmetry
- **Prompt/KV caching** for repeated prefixes — often a 5–10× cost reduction
- Model routing: cheap model first, escalate on low confidence
- Batching, async concurrency, rate limits, exponential backoff
- Latency: TTFT (time to first token) vs TPOT (time per output token); streaming for perceived latency
- Build vs buy: API vs self-hosted break-even math

---

## 5.2 RAG — Retrieval-Augmented Generation (Weeks 33–34, ~85h)

The dominant enterprise pattern. Naive RAG is a weekend; *good* RAG is this whole section.

### Ingestion
- Parsing: PDF (layout-aware — `unstructured`, LlamaParse, Docling), HTML, DOCX, tables, scanned docs + OCR
- **Chunking strategies:** fixed-size, recursive character, sentence/paragraph, semantic (embedding-similarity boundaries), **structure-aware** (by heading), late chunking
- Chunk size and overlap — measure, don't guess
- Metadata extraction and enrichment; contextual retrieval (prepend a document-level summary to each chunk — large measured gains)
- Handling tables and images; multimodal embedding

### Retrieval
- Dense retrieval with embeddings; **vector databases** — pgvector, Qdrant, Weaviate, Milvus, Chroma, LanceDB; managed vs self-hosted
- ANN indexes: HNSW (M, ef_construction, ef_search), IVF-PQ, ScaNN — the recall/latency/memory triangle
- **Sparse retrieval:** BM25 — still beats embeddings on keyword/rare-term queries
- **Hybrid search** + Reciprocal Rank Fusion — nearly always better than either alone
- **Reranking** with a cross-encoder (Cohere Rerank, BGE-reranker) — usually the single biggest quality win per unit effort
- Query transformation: rewriting, HyDE, multi-query expansion, step-back prompting
- Metadata filtering and pre/post-filtering tradeoffs
- Parent-document / small-to-big retrieval; sentence-window retrieval
- **GraphRAG** — entity/relation graphs for multi-hop and global questions
- Agentic RAG — the model decides whether and what to retrieve
- Recursive/iterative retrieval for multi-hop questions

### Generation & grounding
- Context assembly, ordering, and token budgeting
- Citation and attribution; span-level grounding
- Refusal when context is insufficient — design for "I don't know"
- Hallucination mitigation and detection

### RAG evaluation — build this before you build features
- **Retrieval metrics:** recall@k, precision@k, MRR, NDCG, hit rate
- **Generation metrics:** faithfulness/groundedness, answer relevance, context precision/recall
- Frameworks: **RAGAS**, TruLens, DeepEval, Promptfoo
- Building a golden dataset: synthetic question generation from your corpus + human review
- LLM-as-judge: rubric design, pairwise vs pointwise, position bias, self-preference bias, and calibrating the judge against human labels
- **Failure taxonomy** — memorize this diagnostic ladder:
  1. Content missing from corpus
  2. Retrieved but ranked below the cutoff
  3. In context but lost in consolidation
  4. Extracted but wrong format
  5. Correct but incomplete
  6. Correct but unfaithful/hallucinated
  Each has a *different* fix. Diagnose before you tune.

---

## 5.3 Fine-tuning in practice (Week 35, ~40h)

- **The decision framework:** prompt engineering → few-shot → RAG → fine-tuning. Fine-tune for *form, style, format, and latency/cost*; use RAG for *knowledge*. Fine-tuning is the wrong tool for injecting facts.
- Dataset construction: size (often 500–5,000 good examples beats 100k mediocre), diversity, deduplication, decontamination against your eval set
- Synthetic data generation and distillation from a stronger model (check licenses)
- Training with `trl`: SFTTrainer, DPOTrainer, packing, response-only loss masking
- Axolotl / Unsloth / LLaMA-Factory for practical training configs
- Continued pretraining for domain adaptation
- Merging: model soup, SLERP, TIES, DARE; `mergekit`
- Evaluating a fine-tune: against base, against a prompted frontier model, on your held-out set — plus a regression check on general capability

---

## 5.4 Serving & inference infrastructure (Week 36, ~45h)

- **vLLM** — PagedAttention, continuous batching, prefix caching; the default self-hosted choice
- Alternatives: TGI, SGLang (RadixAttention), TensorRT-LLM, llama.cpp/Ollama for local/edge
- **Quantization for inference:** GPTQ, AWQ, GGUF, FP8, bitsandbytes; the quality/throughput curve
- Throughput vs latency tuning: batch size, max sequence length, tensor parallelism, KV cache memory budgeting
- GPU sizing: estimating VRAM = weights + KV cache + activations; picking hardware
- Autoscaling, cold starts, and why LLM serving is different from normal web serving
- Gateways: LiteLLM, provider fallback, retries, budget enforcement
- Semantic caching
- Observability: LangSmith, Langfuse, Phoenix, W&B Weave — trace every call, log every prompt/response pair

---

## 5.5 Safety, security & governance (Week 37, ~40h)

Non-optional for production. This is what makes you employable at a serious company.

- **Prompt injection** — direct and **indirect** (via retrieved documents, tool outputs, web pages). There is no complete fix; defense is layered: input/output filtering, privilege separation, human-in-the-loop for consequential actions, sandboxing, never trusting model output as a command.
- Jailbreaking taxonomy and mitigation
- Data exfiltration via markdown image URLs and tool calls
- PII: detection, redaction, tokenization, data residency
- Guardrails: input/output classifiers, NeMo Guardrails, Llama Guard, moderation APIs
- Hallucination detection: self-consistency, retrieval verification, entailment checking
- Copyright, licensing, and training-data provenance
- Regulation awareness: EU AI Act risk tiers and obligations, NIST AI RMF, ISO/IEC 42001
- Red-teaming your own system before someone else does

---

## Phase 5 deliverables

1. **Production RAG system** over a real, non-trivial corpus (your company docs, a large open dataset, a technical library). Must include: layout-aware parsing, ≥2 chunking strategies compared, hybrid search + reranking, citation output, a golden eval set of ≥100 questions, and a **written ablation table** showing measured quality at each stage. This is the single most portfolio-valuable project in the roadmap.
2. **Eval harness** — a reusable library that runs your prompts against multiple models, scores with both deterministic checks and LLM-as-judge, tracks results over time, and fails CI on regression.
3. **Self-hosted inference benchmark** — serve an open model with vLLM, measure TTFT/TPOT/throughput across batch sizes and quantization levels, and produce a cost-per-1M-tokens comparison against API pricing.
4. **Red-team report** — attack your own RAG system with indirect prompt injection via poisoned documents; document what worked and the mitigations you added.

---

## Phase 5 exit checklist

- [ ] Recite the six-level RAG failure taxonomy and the fix for each
- [ ] Explain why hybrid search beats pure vector search
- [ ] Explain what a reranker does and why it's a cross-encoder
- [ ] Explain HNSW's ef_search parameter and its tradeoff
- [ ] Decide correctly between RAG and fine-tuning for three given scenarios
- [ ] Calculate VRAM needed to serve a 13B model at 8k context, batch 16
- [ ] Explain continuous batching vs static batching
- [ ] Design an LLM-as-judge rubric and name three of its biases
- [ ] Explain indirect prompt injection with a concrete attack chain
- [ ] Explain the lost-in-the-middle effect and how you'd mitigate it
