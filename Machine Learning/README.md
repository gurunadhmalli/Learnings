# The Full Stack: Data Science → ML → Deep Learning → GenAI → Agents

**Your profile:** complete beginner · 40+ hrs/week · target = build production-grade systems, not notebooks.

**Honest timeline: 12 months (~52 weeks × 42 hrs ≈ 2,200 hours).**
Anyone selling you "ML in 3 months from zero" is selling a tutorial habit. At 40+ hrs/week you can genuinely reach hireable, production-capable in a year — that's fast. The math below is what it actually costs.

---

## The 9 phases

| # | Phase | Weeks | Hours | What you can do at the end |
|---|-------|-------|-------|----------------------------|
| 0 | [Foundations: Python, Math, CS](phases/00-foundations.md) | 7 | ~300 | Write clean Python; read a paper's math without panic |
| 1 | [Data Science & Analytics](phases/01-data-science.md) | 5 | ~210 | Own a dataset end-to-end; run a valid A/B test |
| 2 | [Classical Machine Learning](phases/02-classical-ml.md) | 7 | ~300 | Beat a strong baseline and explain *why* it works |
| 3 | [Deep Learning](phases/03-deep-learning.md) | 7 | ~300 | Implement backprop, CNNs, and training loops from scratch |
| 4 | [NLP & Transformers](phases/04-nlp-transformers.md) | 5 | ~210 | Build a GPT from zero; fine-tune real models |
| 5 | [GenAI / LLM Engineering](phases/05-genai-llm.md) | 6 | ~250 | Ship RAG, fine-tuning, evals, and inference serving |
| 6 | [Agentic AI](phases/06-agentic-ai.md) | 4 | ~170 | Build reliable multi-step agents with tools and memory |
| 7 | [MLOps & Production](phases/07-mlops-production.md) | 6 | ~250 | Deploy, monitor, retrain, and roll back safely |
| 8 | [Capstones & Career](phases/08-capstones-career.md) | 5 | ~210 | 3 portfolio systems + interview-ready |

Supporting files: [resources.md](resources.md) · [principles.md](principles.md) · **[tracker.html](tracker.html)** ← open in a browser

---

## The rule that decides whether this works

> **Every phase ends with a shipped artifact, not a finished course.**

A "shipped artifact" means: code in a public git repo, a README a stranger can follow, tests that run, and — from Phase 2 onward — a URL someone else can hit. Watching lectures produces the *feeling* of learning. Building produces the thing.

Budget your week roughly:

- **40%** building the phase project
- **30%** structured learning (course/book/paper)
- **20%** deliberate drills (exercises, LeetCode-style, re-deriving math)
- **10%** review + writing (see spaced repetition below)

## Non-negotiable habits

1. **Git from day one.** Every project, every day, real commit messages. By month 12 your GitHub *is* your résumé.
2. **Spaced repetition.** Anki, ~15 min/day. Every formula, every "why does this work" answer. Skip this and month 1 is gone by month 4.
3. **Write it down.** After each week, one short markdown note explaining what you learned to an imaginary junior. If you can't write it, you don't have it.
4. **From scratch, then use the library.** Implement linear regression, k-means, backprop, attention, and a tokenizer by hand *once*. Then never again — use scikit-learn and PyTorch like a professional.
5. **Read code, not just docs.** scikit-learn, PyTorch, and Hugging Face source are teaching material.
6. **Type hints + tests from Phase 1.** ML code that isn't tested is a rumor.

---

## Phase map (why this order)

```
        ┌──────────────────────────────────────────────┐
   P0   │  Python · Linear Algebra · Calculus · Prob    │  the language
        └──────────────────┬───────────────────────────┘
                           ▼
   P1   ┌──────────────────────────────────────────────┐
        │  SQL · pandas · EDA · Stats · Experiments     │  the data
        └──────────────────┬───────────────────────────┘
                           ▼
   P2   ┌──────────────────────────────────────────────┐
        │  Supervised · Unsupervised · Trees · Eval     │  the modeling instinct
        └──────────────────┬───────────────────────────┘
                           ▼
   P3   ┌──────────────────────────────────────────────┐
        │  Backprop · CNN · RNN · PyTorch · Training    │  the engine
        └──────────────────┬───────────────────────────┘
                           ▼
   P4   ┌──────────────────────────────────────────────┐
        │  Tokenizers · Attention · Transformer · BERT  │  the architecture
        └──────────────────┬───────────────────────────┘
                           ▼
   P5   ┌───────────────────────────┐   ┌──────────────┐
        │  RAG · PEFT · Evals · vLLM │──▶│ P6  Agents   │  the application layer
        └───────────────────────────┘   └──────┬───────┘
                           ▼                   ▼
   P7   ┌──────────────────────────────────────────────┐
        │  Docker · CI/CD · Serving · Monitoring · Drift│  the production layer
        └──────────────────┬───────────────────────────┘
                           ▼
   P8   ┌──────────────────────────────────────────────┐
        │  3 capstones · system design · interviews     │
        └──────────────────────────────────────────────┘
```

**Why not start with LLMs?** You can build a RAG demo in a weekend with zero fundamentals — and then be unable to debug it, evaluate it, cost-optimize it, or explain why retrieval is failing. The market is saturated with people who can call an API. It is starved for people who can tell you *why the recall@10 dropped* and fix it. Phases 0–4 are what make Phases 5–7 valuable.

---

## Checkpoints (be brutal with yourself)

Do not advance until you can do these **without looking anything up**:

- **End of P0** — Derive the gradient of MSE w.r.t. weights. Explain eigenvectors geometrically. Write a Python class with `__enter__`/`__exit__`.
- **End of P1** — Write a window-function SQL query. Explain p-values without saying "probability the hypothesis is true." Diagnose Simpson's paradox in a real table.
- **End of P2** — Explain bias-variance with a drawing. Say when you'd pick gradient boosting over a linear model *and* the reverse. Choose the right metric for a 1%-positive dataset.
- **End of P3** — Implement backprop for a 2-layer MLP in NumPy. Explain why batch norm helps. Debug a loss that goes to NaN.
- **End of P4** — Write scaled dot-product attention from memory. Explain KV caching. Explain why positional encodings exist.
- **End of P5** — Explain the full RAG failure taxonomy. Explain LoRA's rank decomposition. Build an eval set before building the feature.
- **End of P6** — Explain why your agent looped forever and how you bounded it.
- **End of P7** — Take a model from notebook to monitored endpoint with CI, in under a day.

---

## What "production-grade" actually means

Most learners stop at "the model works on my test set." Production-grade means you also own:

- **Reproducibility** — pinned deps, seeded runs, versioned data (DVC), tracked experiments (MLflow / W&B)
- **Serving** — latency budgets, batching, quantization, autoscaling, cost per 1k requests
- **Correctness under drift** — data validation, monitoring, alerting, scheduled retraining
- **Safety** — PII handling, prompt injection defense, bias auditing, red-teaming
- **Rollback** — shadow deploys, canaries, feature flags, and a plan for 3am

Phase 7 covers this properly, but start noticing it from Phase 2.

---

## Start here, today

1. Open `tracker.html` in your browser and bookmark it.
2. Read [principles.md](principles.md) (10 minutes — it will save you months).
3. Open [phases/00-foundations.md](phases/00-foundations.md) and begin Week 1.
4. Create a GitHub repo called `ml-journey`. First commit today.
