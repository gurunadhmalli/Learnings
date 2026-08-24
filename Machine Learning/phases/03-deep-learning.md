# Phase 3 — Deep Learning

**Weeks 20–26 · ~300 hours**

The engine under everything modern. Learn PyTorch — it is the production standard and the research standard. Don't split attention across frameworks.

---

## 3.1 Neural network fundamentals (Week 20, ~45h)

- Perceptron → multilayer perceptron; the universal approximation theorem (and why it's less useful than it sounds)
- Forward pass as composed affine transforms + nonlinearities
- **Activation functions:** sigmoid, tanh, ReLU, LeakyReLU, ELU, GELU, SiLU/Swish — the dying ReLU problem, why GELU dominates in transformers
- **Loss functions:** MSE, MAE, Huber, binary/categorical cross-entropy, focal loss, contrastive/triplet loss; each as a maximum-likelihood statement
- Softmax and the log-sum-exp trick for numerical stability
- **Backpropagation** — derive it by hand for a 2-layer network. Chain rule through the computational graph. Do this on paper.
- Vanishing and exploding gradients; why depth was hard before 2012
- **Weight initialization:** why zeros fail, Xavier/Glorot, **He/Kaiming**, and the variance argument behind each

⚙️ **From scratch:** a full MLP in NumPy — forward, backward, SGD — trained on MNIST to >95% accuracy. No frameworks. This single exercise is worth more than a month of tutorials.

---

## 3.2 PyTorch (Week 21, ~45h)

- Tensors: creation, dtypes, devices, `.to()`, indexing, broadcasting (same rules as NumPy)
- **Autograd:** `requires_grad`, the dynamic graph, `.backward()`, `grad_fn`, `no_grad()`, `detach()`, gradient accumulation
- `nn.Module`: `__init__`/`forward`, parameter registration, `state_dict`, buffers vs parameters
- `Dataset`, `DataLoader`, `Sampler`, `collate_fn`, `num_workers`, pinned memory
- Optimizers, `optim.lr_scheduler`, `zero_grad(set_to_none=True)`
- The canonical training loop — write it 20 times until it's muscle memory
- Checkpointing, resuming, reproducibility (seeds, `deterministic` flags)
- `torch.compile`, TorchScript, `torch.export`
- **Mixed precision** (`torch.amp`), bf16 vs fp16, GradScaler
- Multi-GPU: `DataParallel` (avoid) vs **DistributedDataParallel**; FSDP for large models
- Debugging: shape errors, NaN hunting, `torch.autograd.set_detect_anomaly`
- Profiling: `torch.profiler`, finding the dataloader bottleneck (it's usually the dataloader)
- **PyTorch Lightning** — adopt it after you can write raw loops, not before

---

## 3.3 Training deep networks well (Week 22, ~45h)

This is the practical craft that separates people who *can* train models from people who watch loss curves diverge.

### Normalization
- **Batch norm** — what it actually does, train vs eval mode, why batch size matters, and the internal-covariate-shift myth
- **Layer norm** (the transformer choice), RMSNorm, group norm, instance norm
- Pre-norm vs post-norm placement and training stability

### Regularization
- **Dropout** — inverted dropout, train/eval behavior, and why it's less used in transformers
- Weight decay vs L2 (and why AdamW separates them)
- Early stopping, label smoothing, gradient clipping
- Data augmentation: image (flip, crop, color jitter, **Mixup**, **CutMix**, RandAugment), text (back-translation, EDA), audio (SpecAugment)
- Stochastic depth, DropPath

### Optimization in practice
- Learning rate as the single most important hyperparameter; **LR range test**
- Schedules: step, cosine annealing, warmup, one-cycle, cosine with restarts
- Batch size effects; linear scaling rule; gradient accumulation for big effective batches
- Optimizer choice: AdamW default; SGD+momentum for CNNs; Lion, Sophia as alternatives
- Gradient checkpointing to trade compute for memory

### Diagnosing failure
- Loss is NaN → LR too high, bad init, log(0), fp16 overflow
- Train loss won't drop → too small model, LR too low, bug in the loss, labels shuffled
- Train drops, val doesn't → overfitting or leakage
- Both flat → data pipeline bug; **always overfit a single batch first** as a sanity check
- Val better than train → dropout/augmentation active in train only (usually fine)

**Read:** Karpathy, ["A Recipe for Training Neural Networks"](http://karpathy.github.io/2019/04/25/recipe/). Read it three times across this phase.

---

## 3.4 Computer vision (Weeks 23–24, ~85h)

- **Convolution:** kernels, stride, padding, dilation, receptive field, parameter sharing, translation equivariance
- Pooling (max/avg/global), and the trend toward strided convolutions instead
- Architectures in historical order — each solves the previous one's problem:
  - LeNet → **AlexNet** (ReLU, dropout, GPUs) → **VGG** (3×3 stacks) → **Inception** (multi-scale, 1×1 bottlenecks) → **ResNet** (skip connections solve degradation) → DenseNet → **EfficientNet** (compound scaling) → ConvNeXt
- **Vision Transformers (ViT)** — patch embedding, why they need more data, DeiT distillation, Swin's hierarchical windows
- **Transfer learning** — feature extraction vs fine-tuning, layer freezing, discriminative learning rates. This is what you'll actually do 90% of the time.
- **Object detection:** two-stage (R-CNN → Fast → Faster R-CNN, RPN, anchors, RoI pooling) vs one-stage (SSD, **YOLO** family, RetinaNet + focal loss); IoU, NMS, mAP
- **Segmentation:** semantic (FCN, **U-Net**, DeepLab + atrous convolution), instance (Mask R-CNN), panoptic; SAM for promptable segmentation
- Self-supervised vision: SimCLR, MoCo, BYOL, **DINOv2**, MAE
- **CLIP** — contrastive image-text pretraining, zero-shot classification, the bridge to multimodal
- Generative vision: autoencoders, **VAEs** (ELBO, reparameterization trick), **GANs** (minimax, mode collapse, DCGAN, StyleGAN), and **diffusion models** (forward/reverse process, DDPM, DDIM, classifier-free guidance, latent diffusion / Stable Diffusion, ControlNet)

**Projects:** fine-tune a ResNet and a ViT on a custom dataset you photograph yourself; train YOLO on a small labeled set; implement a U-Net for segmentation; implement a VAE and a DDPM from scratch on MNIST/CIFAR.

---

## 3.5 Sequences before transformers (Week 25, ~40h)

Historically important and still occasionally the right tool.

- RNN: hidden state, BPTT, vanishing gradients over time
- **LSTM** — the three gates and the cell state highway; trace the equations by hand
- **GRU** — the simplification, and when it's enough
- Bidirectional and stacked RNNs
- Seq2seq encoder-decoder; the fixed-size bottleneck problem
- **Bahdanau/Luong attention** — invented specifically to fix that bottleneck. Understanding this makes the transformer obvious rather than magical.
- Teacher forcing and exposure bias
- Beam search
- 1D CNNs and temporal convolutional networks for sequences

---

## 3.6 Beyond the mainline (Week 26, ~40h)

Pick depth based on interest, but know that each exists and roughly how it works.

- **Graph Neural Networks** — message passing, GCN, GraphSAGE, GAT; use cases (fraud, recommendations, molecules); PyTorch Geometric
- **Recommender systems** — collaborative filtering, matrix factorization, ALS, neural CF, two-tower retrieval, candidate generation → ranking → re-ranking architecture, implicit feedback, cold start
- **Reinforcement learning** — MDPs, Bellman equations, value vs policy methods, Q-learning, **DQN**, policy gradients, REINFORCE, actor-critic, A2C/A3C, **PPO** (you need PPO for RLHF in Phase 5), reward shaping, exploration/exploitation
- Multimodal architectures: fusion strategies, CLIP-style dual encoders, cross-attention fusion
- Model compression: **quantization** (PTQ, QAT, int8/int4), **pruning** (structured/unstructured, magnitude, lottery ticket hypothesis), **knowledge distillation** (teacher-student, soft targets), low-rank factorization
- Efficient inference: ONNX, TensorRT, operator fusion, batching

---

## Phase 3 deliverables

1. **NumPy MLP** — from scratch, >95% on MNIST, with a written derivation of the backward pass.
2. **Autodiff engine** extended from Phase 0 to support tensors and a small `nn` module API.
3. **CV project** — a real problem with a dataset you collected or curated: baseline → transfer learning → augmentation → error analysis, with an ablation table showing what each change contributed.
4. **Generative project** — implement a DDPM diffusion model from scratch and generate samples. Write up the math.
5. **A training-diagnostics writeup** — deliberately break your training four ways (bad LR, bad init, leaked labels, wrong loss reduction) and document the symptom → diagnosis → fix for each.

---

## Phase 3 exit checklist

- [ ] Derive backprop for a 2-layer MLP on paper
- [ ] Explain why ResNet skip connections enable depth (in terms of gradient flow)
- [ ] Explain batch norm's train vs eval behavior and why it matters at inference
- [ ] Explain the reparameterization trick and why a VAE needs it
- [ ] Explain the forward and reverse diffusion process
- [ ] Compute the receptive field of a 3-layer CNN
- [ ] Explain LSTM gates from memory
- [ ] Debug: loss goes to NaN at step 300 — list five hypotheses in priority order
- [ ] Explain why you should overfit a single batch before a full training run
- [ ] Explain mixed precision training and why bf16 is preferred over fp16
