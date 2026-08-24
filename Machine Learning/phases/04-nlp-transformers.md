# Phase 4 — NLP & Transformers

**Weeks 27–31 · ~210 hours**

The single highest-leverage architecture of the era. The goal of this phase is that transformers stop being magic. You should be able to draw the whole forward pass on a whiteboard.

---

## 4.1 Classical NLP (Week 27, ~35h)

Short but necessary — it explains why the modern stack looks the way it does.

- Text normalization: lowercasing, Unicode normalization, stemming vs lemmatization, stopwords (and when removing them destroys meaning)
- Tokenization evolution: whitespace → word → subword → byte-level
- **Bag of words, TF-IDF** — still an excellent baseline; always run it first
- N-gram language models, Markov assumption, smoothing (Laplace, Kneser-Ney), perplexity
- **Word embeddings:** Word2Vec (CBOW vs skip-gram, negative sampling, hierarchical softmax), GloVe (co-occurrence factorization), FastText (subword n-grams → OOV handling)
- Embedding geometry: cosine similarity, analogies, and the bias encoded in them
- Classic tasks: NER, POS tagging, dependency parsing, coreference, sentiment
- Sequence labeling with CRFs
- Evaluation: BLEU, ROUGE, METEOR, perplexity — and their well-documented weaknesses
- Tools: spaCy, NLTK, Gensim

---

## 4.2 The Transformer — deeply (Weeks 28–29, ~85h)

Read **"Attention Is All You Need"** and Jay Alammar's *Illustrated Transformer* and Karpathy's *Let's build GPT* video. Then build it.

### Attention mechanics
- Query, Key, Value — the retrieval analogy, and why it's a soft dictionary lookup
- **Scaled dot-product attention:** $\text{softmax}(QK^T/\sqrt{d_k})V$ — and *why* the $\sqrt{d_k}$ scaling exists (variance of dot products grows with dimension → softmax saturates → gradients vanish)
- **Multi-head attention** — parallel subspaces, head concatenation, output projection
- Self-attention vs cross-attention
- **Causal masking** for autoregressive decoding
- Padding masks and attention masks
- Complexity: O(n²) in sequence length — the constraint that drives everything after

### Architecture
- Token embeddings + **positional encodings**: sinusoidal, learned, **RoPE** (rotary — the modern default), ALiBi; why permutation-invariance requires them
- Position-wise feed-forward network, expansion ratio, SwiGLU/GeGLU gating
- Residual connections and layer norm; **pre-norm vs post-norm** and training stability
- Encoder-decoder vs encoder-only vs **decoder-only**, and which tasks each suits
- Weight tying between embedding and output projection

### Efficiency (this is production-critical)
- **KV caching** — why generation is memory-bandwidth-bound, not compute-bound
- **Multi-Query Attention (MQA)** and **Grouped-Query Attention (GQA)** — shrinking the KV cache
- **FlashAttention** (1/2/3) — IO-aware tiling, no materialized attention matrix; the reason long context is affordable
- PagedAttention / vLLM's memory management
- Sparse and linear attention variants: Longformer, BigBird, Performer, Linformer
- Sliding-window attention (Mistral); **Mixture-of-Experts** (sparse FFN routing, load balancing)
- **State-space models** — Mamba/SSM as the leading non-attention alternative; know the tradeoffs

⚙️ **From scratch — the centerpiece of this phase:**
Build a decoder-only GPT in PyTorch: BPE tokenizer → embeddings → RoPE → multi-head causal attention → FFN → residual/norm → LM head. Train it on a small corpus (TinyShakespeare, then a few hundred MB of text). Implement KV caching for generation. Follow Karpathy's `nanoGPT` — but write it yourself first, then diff against his.

---

## 4.3 Tokenization (Week 29, part of above)

Underrated. Half of weird LLM behavior is tokenizer behavior.

- Why character-level and word-level both fail
- **BPE** — merge rules learned from frequency; implement it yourself
- WordPiece (BERT), Unigram LM / SentencePiece (T5, Llama), byte-level BPE (GPT)
- Vocabulary size tradeoffs; special tokens; chat templates
- Practical consequences: why LLMs can't count letters in "strawberry", why numbers tokenize badly, why non-English costs more tokens, why trailing whitespace changes outputs

---

## 4.4 Pretrained model families (Week 30, ~45h)

- **Encoder-only (BERT family)** — masked language modeling, next sentence prediction (and why RoBERTa dropped it), `[CLS]` pooling; RoBERTa, ALBERT, DeBERTa (disentangled attention), ELECTRA (replaced-token detection), DistilBERT. **Still the right choice for classification, NER, and retrieval encoders.**
- **Decoder-only (GPT family)** — causal LM objective, in-context learning, scaling laws (Kaplan → **Chinchilla** compute-optimal ratios); GPT-2/3/4, Llama, Mistral, Qwen, Gemma, DeepSeek
- **Encoder-decoder** — T5's text-to-text framing, BART's denoising objectives; strong for translation and summarization
- **Embedding models** — sentence-transformers, contrastive training, hard negative mining; E5, BGE, GTE, Nomic; the MTEB benchmark
- **Cross-encoders vs bi-encoders** — accuracy vs scalability; the retrieve-then-rerank pattern
- Multimodal: CLIP, BLIP-2, LLaVA, Flamingo-style cross-attention, native multimodal models

### Hugging Face ecosystem
- `transformers`: `AutoModel`/`AutoTokenizer`, pipelines, config objects, `generate()` and its parameters
- `datasets`: streaming, memory-mapping, `map` with batching
- `tokenizers`: training your own
- `accelerate`, `peft`, `trl`, `evaluate`
- The Hub: model cards, licensing (know which models you can use commercially), pushing your own

---

## 4.5 Fine-tuning & adaptation (Week 31, ~45h)

- Full fine-tuning: memory math (params + gradients + optimizer states ≈ 16 bytes/param for AdamW fp32) — this is why you'll rarely do it
- Feature extraction vs full fine-tune vs parameter-efficient
- **LoRA** — low-rank decomposition $\Delta W = BA$; rank $r$, alpha, target modules, why it works (updates are intrinsically low-rank). This is Phase 0's SVD paying off.
- **QLoRA** — 4-bit NF4 quantization + LoRA; double quantization, paged optimizers
- Other PEFT: adapters, prefix tuning, prompt tuning, IA³, DoRA
- Catastrophic forgetting and mitigation
- Instruction tuning; dataset formats (Alpaca, ShareGPT, ChatML); chat templates
- Data quality > data quantity for instruction tuning (LIMA's finding)
- Alignment: **RLHF** (reward model → PPO), **DPO** (direct preference optimization — simpler, now dominant), ORPO, KTO, constitutional AI
- Hyperparameters that matter: LR (much lower than pretraining), epochs (usually 1–3), packing, masking the prompt tokens from the loss

---

## Phase 4 deliverables

1. **`mygpt`** — your own decoder-only transformer, from scratch, with your own BPE tokenizer, RoPE, KV caching, and a training script. Train it to produce coherent text on a small domain corpus. Publish with a written architecture walkthrough.
2. **Attention visualizer** — a tool that renders attention weights per head/layer for a real model, with commentary on what different heads appear to do.
3. **Fine-tuned specialist** — take a 7B open model, QLoRA fine-tune it on a domain task, and evaluate it against the base model and against a prompted frontier model on a held-out set you built yourself.
4. **Embedding-model comparison** — benchmark 4 embedding models on a retrieval task in your own domain; report recall@k and latency; write up the tradeoff.

---

## Phase 4 exit checklist

- [ ] Write scaled dot-product attention in PyTorch from memory
- [ ] Explain the $\sqrt{d_k}$ scaling with the variance argument
- [ ] Explain KV caching, and compute the cache size for a 7B model at 4k context
- [ ] Explain why GQA exists and what it trades away
- [ ] Explain what FlashAttention changes (hint: not the math)
- [ ] Explain RoPE's advantage over learned positional embeddings
- [ ] Explain BPE, and why "strawberry" letter-counting fails
- [ ] Explain LoRA's rank decomposition and estimate its parameter savings
- [ ] Explain DPO vs RLHF-PPO in terms of what each optimizes
- [ ] Explain when you'd choose a BERT-family encoder over an LLM
