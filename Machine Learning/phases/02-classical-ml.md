# Phase 2 — Classical Machine Learning

**Weeks 13–19 · ~300 hours**

Most real business problems on tabular data are still best solved here. Gradient boosting beats deep learning on tabular data more often than the internet admits. This phase builds your *modeling instinct*.

---

## 2.1 The framing (Week 13, ~40h)

- Supervised vs unsupervised vs semi-supervised vs self-supervised vs reinforcement learning
- The learning problem: hypothesis space, loss function, optimization, generalization
- **Bias–variance decomposition** — derive it, draw it, live it
- Overfitting/underfitting; learning curves and how to read them
- Train/validation/test discipline; why the test set is touched once
- Cross-validation: k-fold, stratified, group, **time-series split** (never randomly split time-ordered data)
- Nested CV for honest performance estimates when tuning
- The curse of dimensionality
- No Free Lunch theorem — why "best algorithm" is a meaningless question
- Regularization as a prior: L1 (sparsity), L2 (shrinkage), elastic net

### Evaluation — get religious about this
- **Classification:** accuracy, precision, recall, F1, F-beta, specificity, MCC, balanced accuracy, ROC-AUC vs **PR-AUC** (use PR-AUC when positives are rare), log loss, Brier score
- Confusion matrix reasoning: which error costs more, and what threshold follows from that
- **Calibration** — reliability diagrams, Platt scaling, isotonic regression. A model can rank well and still lie about probabilities.
- **Regression:** MSE, RMSE, MAE, MAPE (and its blow-up near zero), SMAPE, R², Huber loss, quantile loss
- **Ranking:** MAP, NDCG, MRR
- **Clustering:** silhouette, Davies-Bouldin, adjusted Rand index
- Metric selection driven by the decision the model serves

---

## 2.2 Supervised algorithms — theory + from scratch (Weeks 14–16, ~130h)

For each: the intuition, the objective function, the optimization, the assumptions, when it fails, and the key hyperparameters.

### Linear family
- **Linear regression** — normal equation vs gradient descent; when the closed form is infeasible
- Ridge / Lasso / Elastic Net — geometric picture of why L1 hits corners and zeroes coefficients
- **Logistic regression** — sigmoid, log-odds, cross-entropy loss, decision boundary; multinomial/softmax
- Polynomial features and the bias-variance dial
- ⚙️ *From scratch:* linear + logistic regression with gradient descent, in NumPy

### Distance & margin
- **k-NN** — lazy learning, distance metrics, curse of dimensionality, KD-trees/ball-trees
- **SVM** — maximum margin, hinge loss, the dual formulation, support vectors, the **kernel trick** (linear, poly, RBF), soft margin C, and why SVMs scale badly
- ⚙️ *From scratch:* k-NN with your own distance function

### Probabilistic
- **Naive Bayes** — Gaussian/Multinomial/Bernoulli, the independence assumption, Laplace smoothing, why it works well for text despite being "wrong"
- Discriminant analysis: LDA, QDA
- Gaussian Mixture Models + the EM algorithm

### Trees & ensembles (your workhorse)
- **Decision trees** — splitting criteria (Gini, entropy, information gain, MSE), greedy recursive partitioning, pruning, max depth, min samples
- **Bagging** and **Random Forests** — bootstrap, feature subsampling, OOB error, why decorrelation reduces variance
- Extremely Randomized Trees
- **Boosting** — AdaBoost, then **Gradient Boosting** as gradient descent in function space
- **XGBoost** — second-order approximation, regularized objective, sparsity-aware split finding, approximate quantile sketch
- **LightGBM** — leaf-wise growth, GOSS, EFB, histogram binning (usually your fastest strong baseline)
- **CatBoost** — ordered boosting, native categorical handling (best when you have high-cardinality categoricals)
- Stacking and blending; out-of-fold predictions as meta-features
- ⚙️ *From scratch:* a decision tree (fit + predict) and a small gradient boosting implementation

### Imbalanced data
- Resampling: random over/under, **SMOTE**, ADASYN, Tomek links
- Class weights and cost-sensitive learning
- Threshold moving driven by the cost matrix
- Anomaly detection framing: Isolation Forest, One-Class SVM, Local Outlier Factor

---

## 2.3 Unsupervised learning (Week 17, ~45h)

- **k-means** — Lloyd's algorithm, k-means++, elbow and silhouette for choosing k, its assumptions (spherical, equal-variance clusters) and failure modes
- Hierarchical clustering — agglomerative, linkage criteria, dendrograms
- **DBSCAN** and HDBSCAN — density-based, handles arbitrary shapes and noise
- Gaussian Mixture Models — soft assignment, covariance types
- **PCA** — variance maximization, explained variance ratio, whitening, kernel PCA
- **t-SNE** — perplexity, and its severe caveats (distances between clusters are meaningless; never use for anything but visualization)
- **UMAP** — faster, better global structure preservation
- Matrix factorization: NMF, SVD for recommendations
- Association rules: Apriori, FP-Growth, support/confidence/lift
- ⚙️ *From scratch:* k-means and PCA

---

## 2.4 The practitioner's toolkit (Week 18, ~45h)

### scikit-learn mastery
- The estimator API: `fit`/`transform`/`predict`; writing custom transformers via `BaseEstimator`/`TransformerMixin`
- `Pipeline` and `ColumnTransformer` — everything goes in the pipeline, always
- `GridSearchCV`, `RandomizedSearchCV`, `HalvingGridSearchCV`
- `cross_val_score`, `cross_validate`, custom scorers
- `FunctionTransformer`, `TargetEncoder`, imputers
- Persistence with `joblib`; version-pinning your artifacts

### Hyperparameter optimization
- Grid vs random (random wins in high dimensions — know why)
- **Bayesian optimization** — Gaussian processes, TPE; use **Optuna** (pruning, study persistence, visualization)
- Hyperband / ASHA for early stopping of bad trials
- Defining a sensible search space; log-uniform for learning rates

### Interpretability
- Coefficient interpretation and its limits
- Tree feature importance (gain vs split vs **permutation importance** — the first two are biased toward high-cardinality features)
- **SHAP** — Shapley values, TreeSHAP, summary/dependence/force plots, and correct interpretation
- LIME, partial dependence plots (PDP), ICE plots
- Counterfactual explanations
- Global vs local explanation; interpretability vs explainability

### Fairness & responsible ML
- Fairness metrics: demographic parity, equalized odds, equal opportunity — and their mathematical incompatibility
- Bias sources: historical, representation, measurement, aggregation
- Mitigation: pre-processing, in-processing, post-processing
- Model cards and datasheets for datasets

---

## 2.5 Time series (Week 19, ~40h)

Its own discipline; you need working competence.

- Components: trend, seasonality, cyclicality, noise; additive vs multiplicative decomposition
- Stationarity, differencing, ADF/KPSS tests
- ACF/PACF and how to read them
- Classical models: AR, MA, ARMA, **ARIMA**, SARIMA, SARIMAX
- Exponential smoothing: simple, Holt, Holt-Winters, ETS
- **Validation:** rolling-origin / expanding-window backtesting — never a random split
- Feature-based approach: lags, rolling stats, Fourier terms, then LightGBM (often the winner)
- Prophet / NeuralProphet; when they help and when they mislead
- Multivariate: VAR; hierarchical forecasting and reconciliation
- Metrics: MASE, sMAPE, pinball loss for quantile forecasts
- Intermittent demand (Croston's method)

---

## Phase 2 deliverables

**Project A — Tabular competition, done properly.** Enter an active Kaggle competition or use a large public dataset. Build your own pipeline (no copied notebooks). Deliver: a leakage-free `sklearn` pipeline, honest CV that correlates with the leaderboard, a LightGBM/CatBoost model with Optuna tuning, SHAP-based analysis, and a **written error analysis** — where does the model fail and why? Rank is irrelevant; the analysis is the point.

**Project B — From-scratch library.** A small `myml` package implementing linear regression, logistic regression, a decision tree, random forest, k-means, and PCA — with an sklearn-compatible API, tests comparing outputs against sklearn, and docs.

**Project C — Deployed model.** Take Project A's model, wrap it in a **FastAPI** service with input validation (Pydantic), health checks, structured logging, and a Dockerfile. Deploy it to a free tier (Render/Fly/HF Spaces). This is your first taste of Phase 7.

---

## Phase 2 exit checklist

- [ ] Derive the bias-variance decomposition
- [ ] Explain why L1 produces sparse solutions (geometrically)
- [ ] Explain what XGBoost's second-order approximation buys you
- [ ] Explain the difference between bagging and boosting in terms of bias and variance
- [ ] Choose the right metric for fraud detection at 0.2% positive rate, and justify it
- [ ] Explain why a well-ranked model can be badly calibrated, and how to fix it
- [ ] Explain the kernel trick without writing the dual
- [ ] Explain why t-SNE cluster distances are meaningless
- [ ] Set up correct cross-validation for grouped, time-ordered data
- [ ] Interpret a SHAP summary plot correctly, including what it does *not* say
