# Phase 1 — Data Science & Analytics

**Weeks 8–12 · ~210 hours**

This is where most people rush. Don't. The ability to interrogate a dataset — and to design an experiment whose result you can trust — outlives every framework you'll learn.

---

## 1.1 SQL — deeper than you think you need (Week 8, ~40h)

You will write more SQL than PyTorch in most jobs.

- `SELECT`/`WHERE`/`GROUP BY`/`HAVING`/`ORDER BY`, and the **logical execution order** (FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT)
- Joins: inner, left, right, full, cross, self-join, anti-join; join fan-out and how it silently duplicates rows
- Subqueries vs **CTEs** (`WITH`), recursive CTEs
- **Window functions** — `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`/`LEAD`, `SUM() OVER`, frames (`ROWS BETWEEN`). This is the dividing line between beginner and competent.
- Aggregations, `CASE WHEN`, pivoting, `COALESCE`/`NULLIF`, NULL semantics (three-valued logic)
- Date/time functions, time-bucketing, cohort queries
- Indexes: B-tree vs hash, covering indexes, why an index can be ignored
- `EXPLAIN`/query plans, reading a plan, common performance fixes
- Transactions, ACID, isolation levels
- Schema design: normalization vs star schema; fact and dimension tables
- Warehouse dialect awareness: Postgres vs BigQuery vs Snowflake vs DuckDB

**Practice:** [DataLemur](https://datalemur.com), [StrataScratch](https://stratascratch.com), [pgexercises](https://pgexercises.com). Do 60–80 problems. Install DuckDB locally — it's the fastest way to practice on real files.

---

## 1.2 pandas & the data stack (Week 9, ~40h)

- Series vs DataFrame; the Index (and why it bites you)
- Selection: `loc` vs `iloc`, boolean masks, `query`, and the **SettingWithCopyWarning** (understand chained assignment)
- `groupby` → split-apply-combine; `agg`, `transform`, `apply` — and their very different semantics
- Merging: `merge`, `join`, `concat`; validating join cardinality with `validate=`
- Reshaping: `pivot`, `pivot_table`, `melt`, `stack`/`unstack`, wide vs long
- Missing data: `NaN` vs `None` vs `pd.NA`; imputation strategies and their bias
- Time series: `DatetimeIndex`, `resample`, `rolling`, `shift`, timezone handling
- dtypes and memory: `category`, downcasting, why `object` columns are slow
- Method chaining and `pipe` for readable pipelines
- Performance: vectorize, avoid `iterrows`, when to escape to NumPy
- **Polars** — learn it too. Faster, lazy execution, better API. Increasingly the production choice.
- File formats: CSV vs **Parquet** vs Arrow; columnar storage and why it matters

### Visualization
- matplotlib: figure/axes model, subplots, full customization (learn this properly, not just `plt.plot`)
- seaborn: distributions, relationships, categorical plots, `FacetGrid`
- plotly for interactive; Altair for grammar-of-graphics thinking
- **Visualization principles:** chart choice by data type, data-ink ratio, colorblind-safe palettes, never truncate a bar-chart axis, avoid dual y-axes

---

## 1.3 EDA as an interrogation, not a ritual (Week 10, ~40h)

A checklist to run on every new dataset:

1. **Shape and provenance** — how was this collected? By whom? What's missing *because of how it was collected*?
2. **Per-column profile** — dtype, null rate, cardinality, min/max, distribution
3. **Target distribution** — imbalance, skew, outliers
4. **Univariate** — histograms, KDEs, box plots, log-transforms for skew
5. **Bivariate** — correlations (Pearson vs Spearman), scatter matrices, target-vs-feature plots
6. **Missingness pattern** — MCAR vs MAR vs MNAR; missingness heatmap; is missingness itself predictive?
7. **Outliers** — IQR, z-score, isolation forest; decide *keep / cap / drop* with a reason
8. **Duplicates** — exact and fuzzy; check across train/test
9. **Leakage hunt** — any feature that wouldn't exist at prediction time? Any target-derived column?
10. **Temporal drift** — plot key statistics over time; has the distribution shifted?
11. **Segment checks** — does the relationship hold within subgroups? (**Simpson's paradox**)

### Feature engineering
- Numeric: scaling (standard/min-max/robust), log/Box-Cox, binning, polynomial and interaction terms
- Categorical: one-hot, ordinal, **target/mean encoding with out-of-fold computation** (critical — naive target encoding leaks), frequency encoding, hashing
- Datetime: cyclical encoding (sin/cos), lags, rolling windows, holidays, time-since-event
- Text: TF-IDF, n-grams, char-grams
- Geospatial: haversine distance, geohashing
- Aggregation features across entities
- **Always inside `sklearn.Pipeline` / `ColumnTransformer`** so nothing leaks

---

## 1.4 Statistics for decisions & experimentation (Weeks 11–12, ~90h)

This is the highest-value, most-skipped section in the whole roadmap.

### Inference
- Sampling distributions, standard error, the difference between SD and SE
- Confidence intervals: interpretation, and the misinterpretations
- Hypothesis testing framework; null/alternative; test statistic; α and β
- t-test (one/two sample, paired), chi-square, ANOVA, Mann-Whitney, Kolmogorov-Smirnov
- **Effect size** (Cohen's d, lift) — statistical significance ≠ practical significance
- Power analysis and **sample size calculation before the experiment**
- Multiple testing: family-wise error, Bonferroni, Benjamini-Hochberg FDR
- Bootstrap and permutation tests (when assumptions fail, resample)
- Bayesian inference: priors, posteriors, credible intervals; Bayesian A/B testing and why "probability B beats A" is often the better business answer

### A/B testing end to end
- Hypothesis → metric definition → OEC (overall evaluation criterion) → guardrail metrics
- Randomization unit (user vs session vs request) and why it matters
- Sample size + minimum detectable effect, decided *up front*
- Sample ratio mismatch (SRM) as a validity check
- **Peeking problem** and sequential testing; why stopping when significant inflates false positives
- Novelty and primacy effects
- Network effects and interference; cluster randomization
- CUPED variance reduction
- Switchback tests for marketplace/logistics settings

### Causal inference (the differentiator)
- **Correlation vs causation** — confounders, colliders, mediators
- Potential outcomes framework; ATE, ATT
- DAGs and how to choose what to control for (controlling for a collider *creates* bias)
- Observational methods: propensity score matching, IPW, difference-in-differences, regression discontinuity, instrumental variables, synthetic control
- Uplift modeling / heterogeneous treatment effects; `EconML`, `DoWhy`

### Regression as statistics (not just prediction)
- OLS assumptions and what breaks when each is violated
- Interpreting coefficients, standard errors, R² vs adjusted R²
- Multicollinearity, VIF
- Residual diagnostics, heteroskedasticity, robust standard errors
- Logistic regression: odds ratios, interpretation
- GLMs: Poisson for counts, when to use each link function
- `statsmodels` (inference) vs `sklearn` (prediction) — know why both exist

### Resources
- *Trustworthy Online Controlled Experiments* (Kohavi, Tang, Xu) — the A/B testing bible
- *Practical Statistics for Data Scientists* (Bruce & Bruce)
- *The Book of Why* (Pearl) — causal intuition
- *Causal Inference: The Mixtape* (Cunningham) — free online
- Statistical Rethinking (McElreath) lectures — best Bayesian course anywhere

---

## Phase 1 deliverable

**End-to-end analytics project on a real, messy dataset** (find one on data.gov, Kaggle, or a public API — *not* Titanic/Iris).

Requirements:
1. Data loaded into a local Postgres or DuckDB database; all extraction in SQL including at least two window functions
2. A reproducible pipeline (`.py` modules, not just notebooks) that cleans and features the data
3. A written EDA report answering three specific business-style questions, with visualizations that follow good design principles
4. One causal or experimental analysis — either a real A/B test simulation with power analysis, or a diff-in-diff on observational data — including the assumptions you're making and how they could fail
5. A short "what I'd do differently with more data" section

Publish it as a blog post. This is the project that proves you can think, not just fit.

---

## Phase 1 exit checklist

- [ ] Write a query using `LAG` and a windowed running total, from memory
- [ ] Explain the difference between `groupby().transform()` and `groupby().apply()`
- [ ] Explain why target encoding must be computed out-of-fold
- [ ] Given a table, spot Simpson's paradox
- [ ] Compute required sample size for a 2% MDE at 80% power
- [ ] Explain why peeking at an A/B test inflates false positives
- [ ] Explain what happens if you control for a collider
- [ ] Explain a p-value to a product manager in one sentence, correctly
- [ ] Name three sources of data leakage you've personally checked for
