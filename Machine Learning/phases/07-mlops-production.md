# Phase 7 — MLOps & Production Engineering

**Weeks 42–47 · ~250 hours**

This is the phase that turns "someone who knows ML" into "someone companies hire." Most candidates can train a model. Very few can operate one.

---

## 7.1 The production mindset (Week 42, ~40h)

- Read **"Hidden Technical Debt in Machine Learning Systems"** (Sculley et al.) — the ML code is the small box in the middle
- ML system design: the full lifecycle — problem framing → data → training → evaluation → deployment → monitoring → retraining
- Requirements engineering for ML: latency budget, throughput, availability SLO, accuracy floor, cost ceiling
- Batch vs streaming vs real-time vs edge inference — pick deliberately
- The offline/online metric gap; proxy metrics and their dangers
- Feedback loops and degenerate loops (a recommender that trains on its own outputs)
- **Read: *Designing Machine Learning Systems* (Chip Huyen)** — the single best book for this phase. Also *Machine Learning Design Patterns* and *Reliable Machine Learning* (Google SRE).

---

## 7.2 Data engineering for ML (Week 43, ~40h)

- Storage: data lake vs warehouse vs **lakehouse**; Parquet, Delta Lake, Iceberg
- Batch pipelines: **Airflow**, Dagster, Prefect — DAGs, idempotency, backfills, retries, SLAs
- Transformation: **dbt**, medallion architecture (bronze/silver/gold)
- Streaming: Kafka, Flink, Spark Structured Streaming; exactly-once semantics; watermarks and late data
- Distributed compute: Spark/PySpark, Ray, Dask — when you actually need them (usually later than you think)
- **Data versioning:** DVC, lakeFS, Delta time travel
- **Data validation:** Great Expectations, Pandera, `deepchecks` — schema, range, distribution, and referential checks that fail the pipeline loudly
- Data contracts between producers and consumers
- **Feature stores** — Feast, Tecton; online/offline consistency and the **training-serving skew** problem they exist to solve
- Point-in-time correctness for training data (the #1 source of silent leakage in production)
- Labeling: Label Studio, Argilla, weak supervision, active learning, inter-annotator agreement

---

## 7.3 Experiment management & reproducibility (Week 44, ~35h)

- **MLflow** — tracking, projects, model registry, model signatures; or **Weights & Biases** (better UX, sweeps, artifacts, reports)
- What to log: params, metrics, artifacts, code SHA, data version, environment, hardware, random seeds
- Experiment hygiene: one variable at a time; ablation tables
- Model registry: staging → production promotion, approval workflow, lineage
- Reproducible environments: Docker, `uv`/`poetry` lockfiles, `conda-lock`, base image pinning
- Configuration management: **Hydra**, OmegaConf; config as code, no magic numbers
- Distributed and multi-node training: DDP, FSDP, DeepSpeed ZeRO stages, Ray Train
- Cost tracking per experiment (spot instances, checkpoint-and-resume)

---

## 7.4 Deployment & serving (Week 45, ~45h)

- Packaging: `pickle`/`joblib` risks, ONNX, TorchScript, `torch.export`, safetensors
- **Serving frameworks:** FastAPI (start here), BentoML, Ray Serve, NVIDIA Triton, KServe, TorchServe, Seldon
- API design for ML: request/response schemas, Pydantic validation, versioned endpoints, idempotency, timeouts
- Async, batching (dynamic and adaptive), connection pooling
- Model optimization for serving: quantization, distillation, pruning, operator fusion, TensorRT/OpenVINO, compilation
- **Kubernetes** for ML: deployments, services, ingress, HPA, resource requests/limits, GPU scheduling, node pools; Helm; Kubeflow/KServe
- Serverless inference: Lambda/Cloud Run limits, cold starts, SageMaker/Vertex endpoints, Modal/Replicate/Baseten
- Edge deployment: ONNX Runtime, TFLite, Core ML, WebAssembly/WebGPU
- **Deployment strategies:** shadow mode, canary, blue-green, A/B, progressive rollout, **feature flags**, instant rollback
- Load testing: Locust, k6; establishing p50/p95/p99 latency budgets

---

## 7.5 Monitoring & operations (Week 46, ~45h)

The part that separates a deployed model from a *maintained* one.

### What to monitor, in layers
1. **Infrastructure** — CPU/GPU utilization, memory, disk, network
2. **Service** — request rate, error rate, latency percentiles, saturation (the RED/USE methods)
3. **Data** — schema violations, null rate spikes, range violations, volume anomalies, freshness
4. **Model** — prediction distribution, confidence distribution, feature drift, segment-level performance
5. **Business** — the metric the model actually serves

### Drift
- **Data drift** (covariate shift) vs **concept drift** (P(y|x) changes) vs **label shift** — different causes, different responses
- Detection: PSI, KL/JS divergence, KS test, Wasserstein distance, MMD, domain classifier
- Univariate vs multivariate drift detection
- Delayed ground truth: proxy metrics, sampling for human labeling
- Tools: **Evidently AI**, NannyML (performance estimation without labels), WhyLabs, Arize, Fiddler

### Operations
- Retraining strategy: scheduled vs triggered; the training-serving loop; automated validation gates before promotion
- Alerting design: symptom-based, actionable, low false-positive rate; on-call runbooks
- Incident response for ML: rollback first, diagnose second
- Postmortems and the blameless culture
- Stack: Prometheus + Grafana, OpenTelemetry, structured logging (Loki/ELK), Sentry
- **Continuous training (CT)** pipelines; the full CI/CD/CT triad

### CI/CD for ML
- CI: lint, type-check, unit tests, **data validation tests**, model tests (invariance, directional expectation, minimum functionality — see *Behavioral Testing of NLP Models / CheckList*)
- Testing pyramid for ML: unit → integration → data → model → end-to-end
- CD: automated build, model packaging, staged rollout, smoke tests
- GitHub Actions / GitLab CI; CML for model reports in PRs
- Infrastructure as code: **Terraform**, Pulumi; environment parity

---

## 7.6 Cost, scale & governance (Week 47, ~45h)

- Cost modeling: training cost, inference cost per 1k requests, storage, egress
- FinOps for ML: spot/preemptible instances, right-sizing, autoscaling to zero, caching, batching
- GPU economics: reserved vs on-demand vs serverless; utilization as the key metric
- Multi-tenancy and quota management
- Security: secrets management (Vault, cloud KMS), network isolation, model theft/extraction attacks, adversarial robustness, supply-chain security for model artifacts (pickle deserialization is remote code execution — use safetensors)
- Privacy: differential privacy, federated learning, PII handling, GDPR right-to-erasure implications for trained models
- Governance: model inventory, model cards, audit trails, approval workflows, EU AI Act obligations
- Documentation as a deliverable: architecture diagrams, runbooks, on-call guides, ADRs

---

## Phase 7 deliverables

**The full platform project.** Build one end-to-end system that demonstrates every layer. Suggested shape:

```
data source → Airflow/Dagster ingestion → Great Expectations validation
   → dbt transforms → feature store → training pipeline (MLflow tracked)
   → automated eval gate → model registry → containerized FastAPI/BentoML service
   → Kubernetes deploy with canary → Prometheus/Grafana + Evidently monitoring
   → drift alert → triggered retraining → back to training pipeline
```

Requirements:
- Everything in git; infrastructure in Terraform
- CI runs lint, tests, data validation, and model behavioral tests
- CD deploys to a canary, runs smoke tests, promotes or rolls back automatically
- A dashboard showing service health, data drift, and model performance
- A **runbook** describing what to do when each alert fires
- An **architecture diagram** and a written design doc with the tradeoffs you chose and rejected

Deploy it for real on a cloud free tier or cheap VMs. Then deliberately break it — corrupt the input data, spike the latency, drift the distribution — and show the system detecting each one.

---

## Phase 7 exit checklist

- [ ] Explain training-serving skew and three ways it happens
- [ ] Explain point-in-time correctness and why naive joins leak
- [ ] Distinguish data drift, concept drift, and label shift, with an example of each
- [ ] Design a monitoring plan for a model with 30-day delayed labels
- [ ] Explain shadow deployment vs canary vs blue-green, and when to use each
- [ ] Write a Kubernetes deployment manifest with GPU resource limits
- [ ] Name four ML-specific tests that belong in CI
- [ ] Explain why pickle is a security risk for model artifacts
- [ ] Estimate monthly inference cost for a given traffic and model size
- [ ] Take an existing notebook model to a monitored endpoint in under a day
