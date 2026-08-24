# Principles — read this before Week 1

Ten minutes here saves you months of drifting.

---

## 1. Tutorial hell is the default outcome, not a risk

The failure mode is not "too hard." It's completing 40 hours of video, feeling productive, and being unable to start a blank file. The antidote is a fixed ratio: **for every hour of instruction, one hour of building something the instruction didn't ask for.**

Concretely: finish a lesson on logistic regression → immediately apply it to a dataset the course never mentioned, with no scaffolding. Struggle for 90 minutes before looking anything up. That struggle *is* the learning; the lecture was just setup.

## 2. Depth beats breadth, but breadth-first beats depth-first

Contradiction? No. **Sequence** breadth-first: get a shallow working model of the whole landscape early, then deepen. Do not spend 6 weeks perfecting measure-theoretic probability before you've ever trained a model. Learn just enough math to move, build something, then return to the math with a reason to care.

Rule of thumb: *learn it when it blocks you.* You'll learn eigenvectors properly the week PCA confuses you, and it'll stick forever.

## 3. From scratch exactly once

Implement these by hand, once, in NumPy, then never again:

linear regression · logistic regression · k-means · decision tree split · backprop for an MLP · a BPE tokenizer · scaled dot-product attention · a training loop

After that, use scikit-learn and PyTorch. Reimplementing things libraries do better is a hobby, not a skill. The one-time pass is what lets you debug them later.

## 4. Your metric is usually wrong

Accuracy on imbalanced data is a lie. F1 hides which error you care about. AUC-ROC is optimistic when positives are rare (use PR-AUC). Offline metrics diverge from online outcomes. **Before you train anything, write down: what decision does this model drive, and what does a mistake cost in each direction?** Half of applied ML is answering that question well.

## 5. Data quality dominates model choice

A better dataset beats a better architecture, almost always, in industry. The highest-leverage hours are spent on labeling, deduplication, leakage hunting, and distribution checks — not on hyperparameter search. Andrew Ng's "data-centric AI" framing is correct and most learners ignore it because cleaning data feels less like real work.

## 6. Leakage is the #1 silent killer

If your validation score looks great, assume leakage until proven otherwise. Common sources: scaling before splitting, target-derived features, time-ordered data split randomly, duplicate rows across splits, group identity spanning splits. Build the habit: **split first, then do everything else inside a pipeline.**

## 7. Baselines are sacred

Always establish: (a) predict the majority class / mean, (b) a simple linear or tree model, (c) the existing rule-based system if one exists. If your transformer beats the mean predictor by 2%, you have not built an ML system — you've built an expensive random number generator. Report lift over baseline, always.

## 8. Reproducibility is a feature you build, not luck

Seed everything. Pin versions. Log the exact config that produced each number. Commit the notebook *and* the exported script. Future you, six weeks from now, trying to reproduce a result for an interview, will be a different person with no memory.

## 9. Read papers early, badly

Start reading papers in Phase 3, before you're "ready." Three-pass method: (1) title/abstract/figures/conclusion — 10 min, decide if it matters; (2) read for the main idea, skip the proofs — 1 hour; (3) reimplement the core idea — only for papers you truly need. You will understand 20% of your first ten papers. That's the correct rate.

## 10. Ship it or it didn't happen

A model on your laptop is a hobby. A model behind an endpoint, with a health check, logs, and a README, is engineering. From Phase 2 onward, *every* project gets deployed somewhere — even a free tier. The deployment is where you learn the 80% of the job that courses skip.

## 11. Learn in public

Write a short post per phase. Post the repo. It compounds: it forces clarity, it builds the portfolio, and it's how opportunities find you. Nobody cares that it's beginner content — they care that it's clear.

## 12. Prompting an LLM is not a substitute for knowing

Use AI assistants aggressively for boilerplate, docs lookup, and debugging — that's a real productivity skill. But if you let it write the parts you don't understand, you will build a career-shaped hole. Rule: **you may generate any code you could have written yourself.** Everything else, write by hand until you can.

---

## Anti-patterns to name and avoid

| Anti-pattern | What it looks like | Fix |
|---|---|---|
| Course collector | 6 courses at 30% completion | One course at a time, to 100%, with projects |
| Kaggle tourist | Copying public notebooks for medals | Enter one comp, build your own pipeline, accept a bad rank |
| Math avoidance | "I'll just use the library" | Learn it when blocked (Principle 2) — but do learn it |
| Math over-indulgence | 4 months on real analysis first | You're procrastinating with rigor |
| Framework hopping | TF → PyTorch → JAX in a month | PyTorch. Decide once. Move on. |
| Notebook-only | Everything in `Untitled3.ipynb` | Notebooks explore; `.py` modules ship |
| Skipping to LLMs | RAG demo, no fundamentals | You'll plateau in ~8 weeks and can't debug |
| No evaluation | "It looks good in my testing" | Build the eval set *first* |

---

## Weekly operating rhythm

**Monday** — plan the week against the phase file; pick the one deliverable.
**Tue–Fri** — 60% build, 40% learn. Commit daily.
**Saturday** — hard drills: math derivations, coding problems, paper reading.
**Sunday** — review (Anki), write the weekly note, update `tracker.html`, rest properly.

Take one full day off per week. At 40+ hrs, burnout is a bigger threat than any technical topic. A tired month is worse than a rested three weeks.

---

## How to know you're on track

At any point, you should be able to answer: *"What did I build in the last two weeks, and what broke?"* If you can't name something that broke, you're not building at the edge of your ability.
