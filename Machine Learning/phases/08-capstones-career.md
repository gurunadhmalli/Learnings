# Phase 8 — Capstones & Career

**Weeks 48–52 · ~210 hours**

By now you've built ~20 things. This phase converts them into a *portfolio that gets interviews* and a *skillset that passes them*.

---

## 8.1 The three capstones (Weeks 48–50, ~130h)

Three projects, deliberately different, each production-grade. Quality over quantity — three excellent projects beat fifteen tutorials, and hiring managers can tell the difference in 30 seconds.

### Capstone 1 — Classical ML, deployed and monitored
A tabular prediction problem with real business framing.
- Real messy data, not a cleaned Kaggle set
- Baseline → engineered features → tuned gradient boosting
- Honest CV that matches held-out performance
- SHAP-based interpretability and a fairness audit across a sensitive attribute
- Deployed API with monitoring and drift detection
- **Written business case:** what decision it drives, expected value, cost of errors in each direction

### Capstone 2 — Deep learning or GenAI system
Choose based on your target role.
- *DL path:* a CV or multimodal system — custom dataset, transfer learning, ablation study, optimized inference (quantized, benchmarked), deployed with latency SLO
- *GenAI path:* the production RAG system from Phase 5, extended — hybrid retrieval, reranking, structured citations, a 200+ question golden eval set, cost tracking, guardrails, and a public demo

### Capstone 3 — Agentic system
- Genuinely useful, multi-step, with real tools
- Human-in-the-loop approval on consequential actions
- Full tracing, cost caps, bounded loops
- Trajectory eval suite running in CI with a published success rate
- A written reliability report (before/after fixes)

### Every capstone needs
- [ ] A README with problem, approach, results table, architecture diagram, and setup instructions that actually work on a clean machine
- [ ] A live demo URL (HF Spaces, Streamlit, Render, Fly)
- [ ] A short demo video (2–3 min, no talking head needed)
- [ ] Tests + CI badge
- [ ] A blog post explaining a *hard decision* you made and why
- [ ] An honest "limitations and what I'd do next" section — this signals seniority more than any metric

---

## 8.2 Portfolio & presence (Week 51, ~35h)

- **GitHub** — pin your 6 best repos. Clean up abandoned ones. Every pinned repo has a real README with a screenshot/GIF at the top.
- **Blog** — 8–12 posts by now if you followed the phase deliverables. Publish on your own site + cross-post to Medium/Dev.to. The posts that get traction are specific and honest: "Why my RAG recall was 40% and the four things that fixed it."
- **Résumé** — one page. Bullets in the form *"Built X using Y, achieving Z"* with numbers. No "familiar with" lists. Lead with impact and scale, not tools.
- **LinkedIn** — headline stating what you build, not what you're looking for. Post your projects.
- **Open source** — make 3–5 real contributions. Start with documentation fixes in scikit-learn / Hugging Face / LangChain, then bug fixes. A merged PR into a known repo is a strong signal.
- **Kaggle** — one competition where you built your own pipeline; a written solution post regardless of rank.
- Network genuinely: local meetups, conference talks (lightning talks are easy to get), commenting substantively on others' work.

---

## 8.3 Interview preparation (Week 52, ~45h)

ML interviews are typically 5 distinct loops. Prepare each separately.

### 1. Coding
- 60–80 LeetCode easy/medium: arrays, strings, hash maps, two pointers, sliding window, binary search, BFS/DFS, basic DP
- Python-specific: writing clean, tested code under time pressure
- **ML-flavored coding:** implement k-means, k-NN, gradient descent, cross-entropy loss, an attention head, a data loader, a train/test split with grouping — from scratch, in 30 minutes

### 2. ML theory / breadth
- The exit checklists from every phase in this roadmap — those *are* the question bank
- Classic traps: bias-variance, why L1 sparsifies, ROC-AUC vs PR-AUC, how to handle imbalance, overfitting remedies, explain backprop, explain attention, explain LoRA, RAG vs fine-tuning
- Be ready to say "I don't know, but here's how I'd find out" — it scores better than bluffing

### 3. ML system design (the hardest and most differentiating)
Framework to use every time:
1. **Clarify** — business objective, users, scale (QPS, data volume), latency SLO, budget
2. **Define ML framing** — is it even ML? Supervised? What's the label? What's the prediction target?
3. **Metrics** — offline metric, online metric, guardrails
4. **Data** — sources, labeling, volume, sampling, splits, leakage risks
5. **Features** — availability at serving time, computation, feature store
6. **Model** — baseline first, then candidates with justification
7. **Evaluation** — offline eval, then online A/B design
8. **Serving** — batch vs real-time, latency budget, infrastructure
9. **Monitoring** — drift, performance, feedback loop, retraining
10. **Iterate** — what you'd do in v2, and the tradeoffs

Practice problems: design YouTube recommendations, a feed ranker, fraud detection, search ranking, ad CTR prediction, a RAG assistant over enterprise docs, an LLM agent for customer support, an ETA predictor.

Resources: *Machine Learning System Design Interview* (Aminian & Xu), Chip Huyen's interview book (free), Evidently's ML system design case collection.

### 4. Coding/project deep dive
Expect 45 minutes on one of your capstones. Be ready for: why this architecture, what you'd change, what broke, how you evaluated it, what the alternative was, and what it cost. **Know your own projects cold** — this is where fake portfolios collapse.

### 5. Behavioral
- STAR format, 8–10 prepared stories: a failure, a conflict, a technical disagreement, a project you drove, an ambiguous problem, a time you were wrong
- Have questions ready about their ML maturity: how do you deploy? how do you monitor? what's the offline/online gap? who owns retraining? — good questions signal seniority

---

## 8.4 Beyond month 12 — staying current

The field moves faster than any curriculum. Build a sustainable intake habit:

- **Weekly:** one paper (three-pass method), one newsletter skim
- **Monthly:** implement one new technique end-to-end
- **Quarterly:** a new project in an area you don't know
- **Sources worth the time:** arXiv cs.LG/cs.CL new submissions (skim titles), Hugging Face daily papers, Sebastian Raschka's *Ahead of AI*, The Batch (Andrew Ng), Simon Willison's blog (best practical LLM commentary), Lilian Weng's blog (best deep technical explainers), Chip Huyen's blog, Jay Alammar's visualizations
- **Communities:** relevant subreddits, EleutherAI and Hugging Face Discords, local meetups
- Follow the actual researchers and engineers, not the AI-influencer layer

### Depth directions after month 12
Pick one and go deep for the following year:
- **LLM research** — pretraining, architecture, scaling laws, interpretability
- **ML infrastructure** — distributed training, inference optimization, compilers, CUDA
- **Applied domain** — healthcare, finance, robotics, biology, climate
- **Agents/product** — reliability, evaluation, human-AI interaction
- **Safety & alignment** — interpretability, evals, red-teaming, policy

---

## Final exit checklist — are you production-grade?

- [ ] 3 capstones live on the internet, each with a README a stranger can follow
- [ ] 20+ repos, daily commit history, CI on the serious ones
- [ ] 8+ blog posts explaining real decisions
- [ ] 3+ merged open-source PRs
- [ ] Can implement attention, backprop, and k-means from scratch under time pressure
- [ ] Can whiteboard a full ML system design in 45 minutes
- [ ] Can take a model from notebook to monitored endpoint in a day
- [ ] Can diagnose a RAG quality problem by failure level
- [ ] Can explain the cost structure of every system you've built
- [ ] Can name what would break first at 100× scale — for each of your projects

When you can tick all ten, you are not a beginner who learned ML. You are an engineer who ships it.
