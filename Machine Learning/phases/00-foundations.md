# Phase 0 — Foundations: Python, Math, CS

**Weeks 1–7 · ~300 hours**

The goal is *fluency*, not mastery. You need enough Python to build anything, and enough math to read notation without freezing. You'll return to both repeatedly with better motivation later.

---

## 0.1 Python — real Python, not script Python (Weeks 1–3, ~130h)

### Core language
- Data model: `list`, `dict`, `set`, `tuple` — and their **time complexity** (know why dict lookup is O(1))
- Mutability, references, shallow vs deep copy, the mutable-default-argument trap
- Comprehensions, generators, `yield`, lazy evaluation, `itertools`
- Functions: `*args`/`**kwargs`, closures, decorators, `functools.lru_cache`, `partial`
- OOP: classes, inheritance vs composition, `__init__`, `__repr__`, `__eq__`, `__hash__`, properties, `@classmethod`/`@staticmethod`, dataclasses, ABCs
- Context managers (`with`, `__enter__`/`__exit__`, `contextlib`)
- Exceptions: custom exception classes, `try/except/else/finally`, when *not* to catch
- Typing: `list[int]`, `Optional`, `Union`, `Protocol`, generics, `TypedDict` — and run `mypy`
- Modules, packages, `__init__.py`, absolute vs relative imports, `if __name__ == "__main__"`

### Engineering practice (this is what separates you)
- `uv` (fast, modern — the current default) or `poetry` for dependency management; understand virtualenvs
- `pyproject.toml`, packaging your own installable module
- `ruff` (lint + format, replaces black/flake8/isort), `mypy` for types
- `pytest`: fixtures, parametrize, mocking, `conftest.py`, coverage
- Logging (never `print` in library code), `argparse`/`typer` for CLIs
- Debugging: `pdb`/`breakpoint()`, reading tracebacks properly
- Profiling: `cProfile`, `line_profiler`, `memory_profiler`, `timeit`
- Concurrency concepts: threads vs processes vs asyncio, the GIL, when each matters
- Git: branching, rebase vs merge, interactive rebase, resolving conflicts, PR workflow

### NumPy (this is the one that pays off forever)
- ndarray, dtype, shape, strides, views vs copies
- **Broadcasting rules** — internalize these; 80% of your future shape bugs are here
- Vectorization: replacing loops, `np.where`, boolean masking, fancy indexing
- Axis semantics (`axis=0` vs `axis=1` — draw it out until it's automatic)
- `einsum`, matrix ops, `reshape`/`transpose`/`stack`/`concatenate`
- Random: `default_rng`, seeding, sampling distributions
- Numerical stability: catastrophic cancellation, log-sum-exp trick, float32 vs float64

**Drill:** solve 100 NumPy problems ([nphard/100-numpy-exercises](https://github.com/rougier/numpy-100)) without loops.

### Resources
- *Fluent Python* (Ramalho, 2nd ed.) — the definitive book. Read chapters 1–12 now, rest later.
- [Real Python](https://realpython.com) for targeted topics
- *Python Testing with pytest* (Okken)
- [Learn Git Branching](https://learngitbranching.js.org) — interactive, do the whole thing

### Deliverable
A pip-installable CLI tool of your own design (e.g. a personal finance categorizer, a file organizer, a scraper). Requirements: type hints throughout, >80% test coverage, `ruff` clean, GitHub Actions CI that runs tests on push, README with install instructions.

---

## 0.2 Linear Algebra (Week 4, ~45h)

Learn it *geometrically first*, then algebraically.

- Vectors: spans, linear combinations, basis, dimension, linear independence
- Matrices as **linear transformations** (not grids of numbers)
- Matrix multiplication as composition of transformations
- Determinant = signed volume scaling; singular matrices
- Inverse, rank, null space, column space, rank-nullity theorem
- Dot product (projection + similarity), cosine similarity, orthogonality, orthonormal bases
- **Eigenvalues & eigenvectors** — the directions a transformation only stretches. Characteristic polynomial, diagonalization.
- **SVD** — the most important decomposition in ML. Understand $A = U\Sigma V^T$ geometrically: rotate, scale, rotate. Low-rank approximation. (This *is* LoRA, later.)
- Positive definite matrices, quadratic forms
- Norms: L1, L2, Frobenius, and why L1 induces sparsity
- Matrix calculus basics: $\nabla_x (a^Tx)$, $\nabla_x (x^TAx)$, the Jacobian, the chain rule in matrix form

### Resources
- **3Blue1Brown, *Essence of Linear Algebra*** — watch all 15 videos. Non-negotiable. This builds the geometric intuition everything else rests on.
- Gilbert Strang, MIT 18.06 (lectures + *Introduction to Linear Algebra*) — for rigor
- *Mathematics for Machine Learning* (Deisenroth, Faisal, Ong) — free PDF, Part I

### Deliverable
NumPy notebook implementing: PCA from scratch via eigendecomposition of the covariance matrix, then again via SVD; verify they match; apply to MNIST and visualize the reconstruction at k = 5, 20, 50 components.

---

## 0.3 Calculus & Optimization (Week 5, ~45h)

- Derivatives, partial derivatives, gradients (direction of steepest ascent — know *why*)
- Chain rule — deeply. Multivariate. This **is** backpropagation.
- Jacobian and Hessian; what the Hessian tells you about curvature
- Taylor expansion (1st and 2nd order) and its role in optimization
- Convexity: convex sets/functions, why convexity means global optima, why deep nets aren't convex
- Gradient descent: batch, stochastic, mini-batch; learning rate effects
- Momentum, Nesterov, AdaGrad, RMSProp, **Adam / AdamW** — know the update rule for each
- Learning rate schedules: step, cosine, warmup, one-cycle
- Lagrange multipliers and constrained optimization (needed for SVMs)
- Automatic differentiation: forward vs reverse mode, computational graphs

### Resources
- 3Blue1Brown, *Essence of Calculus*
- *Mathematics for Machine Learning*, Chapters 5 & 7
- Sebastian Ruder, ["An overview of gradient descent optimization algorithms"](https://www.ruder.io/optimizing-gradient-descent/)

### Deliverable
Build a tiny reverse-mode autodiff engine in pure Python (~150 lines) that supports `+`, `*`, `tanh`, and `.backward()`. Then train a 2-layer MLP on a toy dataset with it. (Karpathy's *micrograd* is the reference — write it yourself first, then compare.)

---

## 0.4 Probability & Statistics (Week 6, ~45h)

- Sample spaces, events, conditional probability, independence
- **Bayes' theorem** — and its intuition (base rates, the medical-test problem)
- Random variables, PMF/PDF/CDF, expectation, variance, covariance, correlation
- Key distributions and *when each arises*: Bernoulli, Binomial, Poisson, Uniform, Normal, Exponential, Beta, Dirichlet, Multinomial
- Joint/marginal/conditional distributions; the law of total probability
- Law of Large Numbers, **Central Limit Theorem** (and its limits)
- Maximum Likelihood Estimation; MAP estimation; why MSE = MLE under Gaussian noise, why cross-entropy = MLE under Bernoulli
- Information theory: entropy, cross-entropy, **KL divergence**, mutual information
- Sampling: inverse transform, rejection sampling, intro to MCMC
- Estimators: bias, variance, consistency, efficiency
- Confidence intervals, hypothesis testing, p-values (and what they are *not*), Type I/II error, power
- Bootstrap and permutation tests
- Multiple comparisons: Bonferroni, FDR

### Resources
- *Introduction to Probability* (Blitzstein & Hwang) + his Harvard Stat 110 lectures — the best probability course available free
- StatQuest (Josh Starmer) for intuition on any confusing topic
- *Think Stats* (Downey) — free, computational approach
- *Mathematics for Machine Learning*, Chapter 6

### Deliverable
Simulation notebook: demonstrate the CLT empirically across 4 source distributions; implement bootstrap CIs and compare to analytic ones; simulate the p-hacking effect by running 1000 tests at α=0.05 and showing the false discovery rate; implement Bayes' rule for a disease-testing scenario and plot posterior vs prior.

---

## 0.5 CS Fundamentals & Environment (Week 7, ~35h)

- Big-O: time and space; analyze your own code
- Core data structures: arrays, linked lists, hash maps, heaps, trees, graphs
- Core algorithms: sorting, binary search, BFS/DFS, basic dynamic programming
- ~50 LeetCode easy/medium (arrays, strings, hash maps, two pointers) — enough for ML interviews, don't overinvest
- **Linux/CLI:** navigation, pipes, `grep`/`awk`/`sed`, permissions, `ssh`, `tmux`, process management, editing in `vim` (survival level)
- **Docker:** images vs containers, Dockerfile, layers/caching, volumes, `docker compose`
- Cloud basics: pick one (AWS/GCP/Azure), learn compute + object storage + IAM
- GPU landscape: CUDA, VRAM constraints, what fits where; use Google Colab / Kaggle free tiers now

### Deliverable
Dockerize your Phase 0.1 CLI tool. Push the image to a registry. Write a `docker-compose.yml` that runs it plus a Postgres container. Get it running on a free cloud VM via SSH.

---

## Phase 0 exit checklist

Answer without notes:

- [ ] Why is a Python `dict` lookup O(1), and when is it not?
- [ ] Explain broadcasting; predict the shape of `np.ones((3,1)) + np.ones((1,4))`
- [ ] What does an eigenvector mean geometrically?
- [ ] Explain SVD in two sentences to a non-mathematician
- [ ] Derive $\partial/\partial w$ of $\frac{1}{n}\sum (y - Xw)^2$
- [ ] Why does Adam usually converge faster than plain SGD?
- [ ] Explain KL divergence and why it's asymmetric
- [ ] A test is 99% accurate for a disease affecting 1 in 10,000. You test positive. Probability you have it?
- [ ] What does a p-value of 0.03 mean — precisely?
- [ ] Write a Dockerfile from memory
- [ ] 4 shipped repos on GitHub with CI passing

If more than two of these are shaky, spend another week here. Foundations debt compounds worse than any other kind.
