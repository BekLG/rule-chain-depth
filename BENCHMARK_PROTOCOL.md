# PLN-RAG versus vector-RAG protocol

The primary comparison evaluates each architecture in its documented native
configuration. It does not force a symbolic system and vector retriever to have
identical internals. Fairness comes from the same frozen source corpus,
questions, model profile, scoring, and explicit resource accounting. Custom
capacity ablations are secondary diagnostics and must not be presented as the
primary architecture result.

## Model profiles

Run the complete matrix separately for each model profile. Do not mix model
families within one shared invocation.

| Family | OpenRouter model | Pinned provider |
|---|---|---|
| GLM, primary | `z-ai/glm-5.3` | `inference-net` |
| Kimi, replication | `moonshotai/kimi-k3` | `inference-net` |

Both endpoints must support `temperature`, `reasoning`, `max_tokens`, and
`response_format`. Provider fallback and automatic retries remain disabled.
Use `B1_LLM_REASONING_EFFORT=medium`, `B1_LLM_TIMEOUT=180`, temperature zero,
and a 4096-token output allowance for every selected system. Use distinct run
IDs for each profile and prepare a new manifest after switching profiles.

## Systems and tracks

| System | Native evidence access | Role |
|---|---|---|
| PLN-RAG | Persistent world KB; retrieval limit 12 | Symbolic architecture |
| One-shot vector RAG | Top 4 question-similar sentences | Retrieval baseline |
| Iterative vector RAG | Two deterministic rounds, two new sentences per round, at most four distinct sentences | Multi-hop retrieval baseline |
| Full context | All 12 world sentences | Retrieval ablation |

Use `--track native` for the primary comparison. It requires one-shot top-4 and
PLN top-12 defaults. `--track custom` permits explicit capacity ablations and
labels the artifact accordingly. Retrieval limits and iterative round traces
are recorded in manifests and question records.

Use `--track shared_iterative` for the controlled reasoning diagnostic. The
iterative retriever selects four ordered sentence IDs for each question. Every
host baseline receives exactly those sentences, while PLN-RAG learns a fresh
per-question KB containing only those IDs. Records fail closed if used,
retrieved, shown, or cited IDs escape that evidence contract. This track tests
reasoning after a common retrieval stage; it is not the primary native result.

The iterative retriever uses one question embedding and one final answer call.
It does not use LLM query expansion. Round one ranks by question cosine. Later
rounds rank unseen sentences against normalized question-plus-frontier vectors.
Evidence IDs remain unique and final context preserves discovery order.

The shared answer contract requires an empty citation list for
`NOT_ESTABLISHED`. Vector indexes are built once per world and reused by its two
questions. Query embeddings and answer calls remain per-question operations.

## Dataset use

The current 20-world fixture has been used during development and must not be
described as an untouched external test set. The frozen
`reasoning_holdout_v1` manifest creates prospective development and held-out
partitions while retaining supported/control pairs. Its historical-exposure
note must accompany held-out results. A future independently authored dataset
is still required for a stronger confirmatory claim.

Named splits cannot be combined with `--world-limit`. The runner verifies the
split's dataset hash, disjointness, full coverage, and frozen order before
creating an artifact.

## Offline validation

Run both suites before any paid calls:

```bash
cd ../normal-rag
python3 -m unittest discover -s tests -v

cd ../rule-chain-depth
python3 -m unittest discover -s tests -v
python3 -m b1 oracle \
  --worlds data/benchmark/worlds.json \
  --expected data/benchmark/hand_expected.json \
  --output artifacts/oracle/benchmark.answer_key.json
```

## Preparation and diagnostic gate

Prepare a four-world run spanning depths 0 through 3:

```bash
python3 -m b1 benchmark \
  --systems pln_rag rag iterative_rag full_context \
  --track native \
  --world-limit 4 \
  --container pln-rag-pln-rag-1 \
  --run-id diagnostic-glm-native-plan \
  --prepare-only
```

Remove `--prepare-only` and use a fresh run ID only after checking the manifest,
Docker image, provider, model, service URLs, and request cap. The diagnostic gate
requires every question to be attempted, no fallback/model mismatch/truncation,
at most 5% sentence parse failures, no query contamination, and no exhausted
request budget. Inspect any nonzero query-state mutation even if it did not
produce a supported answer.

## Full study

```bash
# Primary native architecture comparison
python3 -m b1 benchmark \
  --systems pln_rag rag iterative_rag full_context \
  --track native \
  --container pln-rag-pln-rag-1 \
  --run-id full-glm-native-r1

# Prospective held-out subset
python3 -m b1 benchmark \
  --systems pln_rag rag iterative_rag full_context \
  --track native \
  --split reasoning_holdout_v1:heldout \
  --container pln-rag-pln-rag-1 \
  --run-id holdout-glm-native-r1

# Secondary equal-top-k capacity diagnostic
python3 -m b1 benchmark \
  --systems pln_rag rag full_context \
  --track custom --rag-top-k 4 --pln-top-k 4 \
  --container pln-rag-pln-rag-1 \
  --run-id full-glm-top4-diagnostic-r1

# Secondary shared-evidence reasoning diagnostic
python3 -m b1 benchmark \
  --systems pln_rag rag iterative_rag full_context \
  --track shared_iterative \
  --container pln-rag-pln-rag-1 \
  --run-id full-glm-shared-iterative-r1
```

Repeat stochastic conditions at least three times. Rotate system order or use
independently sufficient budgets so an earlier system cannot exhaust calls
needed by a later system.

## Required reporting

Report strict end-to-end accuracy, supported accuracy by depth and proof size,
unsupported accuracy, errors, parse failures, retrieval and citation proof
sufficiency, query-state mutations, latency by stage, request count, token use,
and estimated cost.

Primary pairwise differences use the deterministic world-cluster bootstrap in
`summary.json`, which preserves each supported/control pair. Wilson intervals
remain descriptive because templates repeat and questions are not independent.

Native-track differences describe complete architectures. They must not be
attributed solely to symbolic reasoning because retrieval, persistence, and
context construction differ. Custom capacity runs are diagnostic only.
