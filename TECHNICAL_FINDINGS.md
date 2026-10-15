# PLN-RAG vs. Vector RAG: Logical Reasoning Benchmark and Comparative Evaluation

Technical findings from the three finalized native GLM runs. This document is the evidence base for a future standalone report, not publication-ready narrative.

## 1. Executive Findings

The experiment compared four complete question-answering architectures on the same frozen 20-world, 40-question logical reasoning benchmark. Each configuration was repeated three times, producing 120 scored decisions per system.

| System | Run 1 | Run 2 | Run 3 | Pooled correct | Pooled accuracy |
|---|---:|---:|---:|---:|---:|
| PLN-RAG | 40/40 | 40/40 | 40/40 | 120/120 | **100.0%** |
| One-shot vector RAG | 31/40 | 31/40 | 31/40 | 93/120 | **77.5%** |
| Iterative vector RAG | 34/40 | 35/40 | 33/40 | 102/120 | **85.0%** |
| Full context | 39/40 | 39/40 | 39/40 | 117/120 | **97.5%** |

The observed pooled differences were 22.5 percentage points between PLN-RAG and one-shot RAG, 15 points between PLN-RAG and iterative RAG, and 2.5 points between PLN-RAG and full context. These are descriptive pooled differences. The artifacts contain run-level Wilson intervals and run-level paired world-cluster bootstrap intervals, but no pooled confidence interval; none is manufactured here.

The strongest result is not simply that PLN-RAG obtained the highest label accuracy. It is that its persistent symbolic representation and proof-based decision path handled all tested proof depths and rule families while top-four vector retrieval repeatedly omitted necessary premises. Full context nearly closed the gap, showing that much of the vector-RAG deficit came from evidence selection rather than an absolute inability of the language model to execute these small deductions.

The result requires two major qualifications:

- This is a native architecture comparison, not a controlled test of symbolic and neural reasoning under identical evidence. PLN-RAG had a persistent knowledge base and a retrieval limit of 12; one-shot and iterative RAG had at most four sentences; full context received all 12 sentences.
- One PLN-RAG success, `bench-15-supported` in Run 2, depended on a rule added during query parsing rather than solely on the learned world. The implemented scorer correctly records the returned proof as `SUPPORTED`, but this case is not a clean source-only proof. Consequently, the measured label result is 120/120, while the clean-proof interpretation must disclose one potentially contaminated observation.

Resource use also differed substantially. PLN-RAG made 300 audited HTTP requests and consumed approximately 3.98 million measured tokens per run. Each baseline made 40 answer requests per run and consumed roughly 12,000 to 19,000 tokens. Accuracy gains therefore should not be interpreted as efficiency gains.

## 2. Research Motivation

Conventional vector RAG is effective when the sentences most similar to a question are also the sentences needed to answer it. Logical reasoning introduces a different requirement: a correct answer may depend on several premises whose individual wording is only weakly related to the final question. Missing any required premise can make a valid conclusion unreachable, while fluent generation can still produce a confident but unsupported label.

PLN-RAG addresses the task through a different architecture. Natural-language sentences are parsed into symbolic statements, persisted in a world-specific knowledge base, and queried through a reasoner that returns a proof or an empty proof set. The benchmark therefore investigates four practical questions:

1. Can a symbolic RAG pipeline preserve and combine multi-step evidence more reliably than a standard top-k vector pipeline?
2. Does iterative vector retrieval recover proof premises missed by a single retrieval pass?
3. How much of the observed gap disappears when the language model receives the complete world and retrieval is removed as a bottleneck?
4. Do proof and evidence diagnostics reveal failures that label-only accuracy hides?

The experiment targets end-to-end behavior. It includes ingestion, representation, retrieval, reasoning, output parsing, and scoring. It does not isolate a reasoner behind an identical upstream retrieval stage. This makes the results relevant to deployed architecture behavior, but it also limits causal attribution.

## 3. Systems Compared

All systems received the same frozen English worlds and questions. They used the same GLM model profile for LLM-facing operations: `z-ai/glm-5.3` through the pinned `inference-net` provider, temperature 0, medium reasoning effort, a 4096-token output allowance, no provider fallback, no automatic retries, and no response cache. Their evidence-access and decision paths differed by design.

### 3.1 PLN-RAG

PLN-RAG learned each 12-sentence world once. Each English sentence was separately parsed into PLN statements and stored in a world-specific persistent knowledge base. The resulting knowledge-base snapshot was hashed, made read-only, and restored into a fresh process for each question. This preserved learned world state while preventing one question from silently changing the starting state of the next.

At question time, PLN-RAG parsed the natural-language question into a symbolic query, searched the persistent world representation with a retrieval limit of 12, and ran the configured symbolic reasoner. The benchmark label did not come from the fluent answer text. A valid nonempty proof list produced `SUPPORTED`; a valid empty list produced `NOT_ESTABLISHED`; malformed or failed execution produced `ERROR`. Proof symbols were then mapped back to source sentence IDs by exact token equality for diagnostics.

This system was included as the target architecture: a pipeline intended to turn natural-language evidence into a persistent logical representation and answer through explicit proof search.

### 3.2 One-Shot Vector RAG

“One-shot” means that retrieval occurs once from the original question:

1. The 12 English sentences in a world are embedded with `nomic-embed-text` and normalized.
2. The resulting immutable world index is reused for the world's two questions.
3. The question is embedded and normalized.
4. Cosine similarity, implemented as the dot product of normalized vectors, ranks all sentences.
5. The top four sentences are passed to the LLM with the question.
6. One final LLM request returns strict JSON containing a label and cited sentence IDs.

Stable sorting resolves score ties using frozen sentence order. There is no reranker, query decomposition, query rewriting, recursive search, repair request, or LLM-based retrieval expansion.

One-shot RAG was included as the conventional minimal retrieval baseline. It tests whether direct semantic similarity between the final question and individual source sentences is enough to assemble a complete proof context.

### 3.3 Iterative Vector RAG

Iterative RAG uses the same sentence embeddings and final answer contract but performs two deterministic retrieval rounds:

1. Round 1 ranks sentences against the question embedding and selects the top two unseen sentences.
2. For each round-1 sentence, its vector is added to the original question vector and renormalized.
3. Round 2 scores every unseen sentence against those question-plus-frontier vectors.
4. The highest score over the frontier sources becomes each candidate's round-2 score.
5. The top two unseen candidates are added, preserving discovery order.
6. The four distinct retrieved sentences are sent to the LLM in one final answer request.

The iterative retriever does not call an LLM to generate queries. It uses one question embedding, deterministic vector arithmetic, and one final LLM classification call. Every round records its source vectors, candidates, scores, selected IDs, and stopping reason.

This comparator asks whether following semantic links from initially retrieved sentences can recover intermediate proof steps that have low direct similarity to the final question. Its maximum evidence remains four sentences, matching one-shot RAG, so the comparison changes retrieval strategy without also increasing final context capacity.

### 3.4 Full Context

Full context skips embedding and retrieval. All 12 frozen English sentences are placed in the same baseline classification prompt with the question, and the LLM returns the same strict JSON label and citation structure.

This is a retrieval ablation, not a deployable retrieval strategy. Its purpose is diagnostic:

- One-shot or iterative failure followed by full-context success points toward evidence-selection failure.
- Full-context failure despite a valid proof in the supplied world points toward downstream reasoning or classification failure.
- A PLN-RAG advantage over full context is more informative about the symbolic decision path than an advantage over a top-four retriever alone.

## 4. Benchmark Design and Dataset

### 4.1 Actual provenance

The benchmark is not imported or adapted from an external corpus. Its source is the authored Python construction in `b1/dataset.py`. That code directly defines logical facts, rules, supported targets, paired controls, repair facts, and canonical proof positions. `b1/language.py` supplies the closed name and predicate vocabulary and deterministically renders each logical clause into controlled English.

The construction process is:

1. Five template families are crossed with depths 0 through 3 to create 20 worlds.
2. Depth 0 produces direct-fact worlds. At depths 1 through 3, the family determines whether the proof uses a unary chain, conjunction, relational composition, or mixed relational/unary reasoning.
3. Every supported target receives an explicitly constructed proof.
4. A paired control replaces the target entity or endpoint so that the claim is not derivable under open-world semantics.
5. Unrelated facts and rules are generated from unused vocabulary until each world contains exactly 12 sentences.
6. English text is rendered from the logical representation, not independently paraphrased.
7. Each world is shuffled deterministically with seeds `4001` through `4020`. Shuffling is retried until the order differs from construction order and a proof-critical sentence is not last.
8. Post-shuffle sentence IDs are used to write the expected proof annotations.

The final fixtures are frozen in `data/benchmark/worlds.json` and `data/benchmark/hand_expected.json`. The earlier eight-world pilot is separate and is not part of these results.

### 4.2 Size and balance

- 20 worlds.
- 12 sentences per world, for 240 sentence entries.
- 150 fact entries and 90 rule entries.
- Two questions per world: one `SUPPORTED` target and one paired `NOT_ESTABLISHED` control.
- 40 questions per system per run.
- Five supported/control pairs in each depth bucket 0, 1, 2, and 3.
- Supported proof sizes range from one to six source sentences.

Supported proof-size distribution:

| Canonical proof size | Supported worlds |
|---:|---:|
| 1 sentence | 5 |
| 2 sentences | 3 |
| 3 sentences | 4 |
| 4 sentences | 5 |
| 5 sentences | 2 |
| 6 sentences | 1 |

Across the 20 canonical supported proofs, 59 of the 240 sentence entries are proof members. The other 181 entries act as distractors relative to those canonical proofs. Three targets necessarily exceed a four-sentence evidence window: `bench-12-supported` has a six-sentence proof, while `bench-16-supported` and `bench-20-supported` have five-sentence proofs.

### 4.3 Answer-key validation

Expected labels and proof annotations originate from explicit construction positions, not model predictions. Two independent solvers then validate them:

- A forward solver performs bottom-up saturation using immutable per-round snapshots.
- A backward solver performs top-down goal matching, grounding, cycle control, and memoization.

Dataset admission requires exact agreement on labels, depths, and proof frontiers. Validation also checks unique IDs, 12 sentences per world, English/logical-form agreement, supported/control pairing, reconstruction of each proof from its cited subset, and successful repair of each control with its designated missing fact. The generated validated answer key is preserved at `artifacts/oracle/benchmark.answer_key.json`.

## 5. Logical Reasoning Capabilities Covered

The categories below describe the complete worlds used in the experiment. Each world contributes one supported question and one paired control, so the question count is twice the world count per run.

| Capability family | Worlds | Questions per run | Construction |
|---|---:|---:|---|
| Direct factual retrieval | 5 | 10 | The target is an explicit ground fact. |
| Implication chaining | 6 | 12 | A ground fact flows through one to three unary implications. |
| Conjunction/multi-premise inference | 3 | 6 | The final conclusion requires two independently established unary premises. |
| Relational composition | 3 | 6 | Two binary relations are joined through a shared intermediate entity, optionally followed by another relational rule. |
| Mixed relational and unary inference | 3 | 6 | A relational derivation produces a unary conclusion, optionally followed by another unary implication. |
| **Total** | **20** | **40** | **One supported target and one control per world.** |

The controls test evidence-sensitive abstention across all five categories. A control is not the negation of its paired target. It is a claim for which the world lacks a complete proof, so the correct open-world response is `NOT_ESTABLISHED`.

Proof depth is defined structurally. Facts have depth 0. A rule application has depth `1 + max(depth of each premise proof)`. This definition allows a conjunction with unequal branch lengths to have the depth of its longest branch plus one.

## 6. Benchmark Implementation

### 6.1 Frozen inputs and answer-key isolation

Before any selected subset is evaluated, the runner loads and validates the complete frozen dataset. Systems receive public sentence IDs, English text, and the English question. They do not receive logical forms, expected labels, proof depths, canonical proof IDs, or repair facts.

The semantic dataset fingerprint shared by all three runs is:

`8d4bc9726a01284833a09acade4476e885022efcace94c8a6d5b38e98f38fba8`

This fingerprint is computed from canonical serialization of the logical world objects. It is therefore intentionally different from a raw byte hash of the formatted JSON file.

### 6.2 PLN-RAG execution

Each world uses a unique collection and is learned once. The ingestion record retains parser output, accepted and rejected statements, latency, and any parse failure for every source sentence. The final runs recorded zero sentence parse failures.

The learned atom state is snapshotted and hashed. Every question runs in a fresh process restored from that immutable snapshot. Before and after hashes, query-added statements, retrieval calls, parser calls, reasoner calls, and audited LLM calls are retained. This design distinguishes world learning from query execution and makes cross-question state changes observable.

The configured query path used a 12-item retrieval limit, up to five query candidates, 100 reasoning steps, and a 30-second reasoning timeout per candidate. External knowledge was disabled.

### 6.3 Baseline execution

One-shot and iterative vector indexes are built once per world and reused for both questions. Question embeddings and answer calls remain per-question operations. Full context does not build an index. All three baselines share one system prompt, which instructs the LLM to use only the supplied sentences, return `SUPPORTED` only when they prove the claim, use `NOT_ESTABLISHED` for missing proof, and emit exactly one two-field JSON object.

The parser rejects duplicate fields, nonfinite JSON values, additional output fields, unknown labels, malformed citation lists, and non-JSON output. There are no hidden repair calls.

### 6.4 Request auditing and completion gates

Each run reserved 420 requests under a shared 500-call cap and completed all 160 expected records. The audited distribution was 300 PLN-RAG requests and 40 requests for each baseline. Request numbers were contiguous, all observed statuses were HTTP 200, providers and models matched the manifest, and no driver error or truncation prevented scoring.

Run completion means every expected record exists and was attempted. It does not mean every answer was correct.

## 7. Evaluation Metrics and Scoring

### 7.1 Primary score

The primary metric is strict end-to-end label accuracy over all selected questions. `SUPPORTED` and `NOT_ESTABLISHED` must exactly match the authored expected label. `ERROR` is always incorrect, and errors or explicitly unattempted questions remain in the denominator. There is no partial credit.

PLN-RAG and the baselines reach their labels differently:

- PLN-RAG is scored from proof existence after successful query execution.
- Baselines are scored from the strictly parsed LLM JSON label.

The benchmark does not use an LLM judge, semantic similarity grading, or the fluent natural-language answer to assign correctness.

### 7.2 Diagnostic measurements

Accuracy is reported by depth, supported depth, canonical proof size, rule family, and expected label. Additional diagnostics include:

- Whether retrieved evidence contains every sentence in the canonical proof.
- Whether the retrieved subset can prove the claim, allowing any valid proof rather than only the canonical proof.
- Whether the displayed context can prove the claim.
- Whether baseline citations alone can prove the claim.
- Whether PLN-RAG's available evidence can prove the claim.
- Query-time knowledge-base mutations and potential contamination.
- Invalid citations, parse failures, timeouts, request counts, token use, answer latency, PLN learning time, and vector-index construction time.

These diagnostics do not alter the label score. A baseline can receive credit for a correct label even if its citations do not constitute a proof, and a PLN proof can receive credit under the implemented proof-existence scorer even if a query-added statement requires later methodological review.

PLN proof-source mapping is diagnostic rather than a second formal proof checker. The scorer maps exact proof symbols to learned sentence IDs and preserves the raw proof, but does not independently replay the returned native proof object.

### 7.3 Uncertainty reporting

Each run contains descriptive Wilson 95% intervals for system and subgroup accuracies. Because questions are paired within worlds and templates repeat, they should not be read as intervals from independent random samples.

Pairwise comparisons use 10,000 deterministic bootstrap replicates with seed 1729 and the world as the resampling unit, preserving each supported/control pair. These intervals are stored per run. No pooled interval over the three repetitions is present in the artifacts.

## 8. Experimental Runs and Quantitative Results

### 8.1 Overall results

All three finalized runs used the complete 20-world dataset, all four systems, the same model/provider profile, and the native evidence policy. There were no scored `ERROR` labels.

| System | Pooled supported | Pooled controls | Pooled overall |
|---|---:|---:|---:|
| PLN-RAG | 60/60 | 60/60 | 120/120 |
| One-shot vector RAG | 33/60 | 60/60 | 93/120 |
| Iterative vector RAG | 43/60 | 59/60 | 102/120 |
| Full context | 60/60 | 57/60 | 117/120 |

One-shot RAG's result was perfectly stable across runs. Iterative RAG varied by two questions around its mean, showing that deterministic retrieval does not make the final LLM decision deterministic. Full context's sole run-level error was also stable.

### 8.2 Results by reasoning family

| Capability | Worlds | Questions across three runs | PLN-RAG | One-shot | Iterative | Full context |
|---|---:|---:|---:|---:|---:|---:|
| Direct facts | 5 | 30 | 30/30 | 30/30 | 30/30 | 30/30 |
| Implication chains | 6 | 36 | 36/36 | 24/36 | 35/36 | 36/36 |
| Conjunction | 3 | 18 | 18/18 | 12/18 | 12/18 | 15/18 |
| Relational composition | 3 | 18 | 18/18 | 12/18 | 10/18 | 18/18 |
| Mixed relational/unary | 3 | 18 | 18/18 | 15/18 | 15/18 | 18/18 |

All systems handled direct facts. Differences emerged when the answer depended on multiple premises. Iterative retrieval nearly eliminated chain errors but did not consistently improve conjunction or relational composition. Full context solved all supported questions across every family, while its three pooled errors came from the same conjunction control.

### 8.3 Retrieval and evidence sufficiency

For one-shot RAG, 33 of 60 supported retrieval contexts could prove the target and 27 could not. These 27 insufficient contexts correspond exactly to the nine unique supported misses repeated in all three runs. Thus every one-shot supported error is explained by insufficient retrieved evidence in this benchmark.

Iterative RAG produced proving contexts for 42 of 60 supported observations, compared with 33 for one-shot. It achieved 43 correct supported labels because one Run 2 answer was labeled `SUPPORTED` even though neither its context nor its citations proved the claim. Iterative retrieval always completed two rounds and returned four distinct sentences.

The four-sentence cap is a hard limitation for the three canonical proofs containing five or six sentences. Even perfect ranking cannot place those complete canonical proofs in the allowed context. Smaller proofs can still fail when an intermediate rule or premise ranks below unrelated but lexically similar sentences.

Full context supplied a proving context for all 60 supported observations, establishing that the complete 12-sentence worlds contain sufficient evidence and that the LLM can usually execute the intended reasoning when no retrieval loss occurs. However, complete evidence did not guarantee calibrated abstention: the same unsupported control was labeled `SUPPORTED` in all three runs.

### 8.4 Pairwise run-level comparisons

PLN-RAG exceeded one-shot RAG by 22.5 points in every run. The world-cluster bootstrap interval was `[12.5, 32.5]` percentage points in each run. PLN-RAG exceeded iterative RAG by 15.0, 12.5, and 17.5 points; corresponding intervals were `[5.0, 25.0]`, `[5.0, 22.5]`, and `[7.5, 27.5]` points.

PLN-RAG exceeded full context by 2.5 points in each run, with `[0.0, 7.5]` point bootstrap intervals. The lower bound of zero and the single unique disagreement emphasize that this comparison is much less decisive than the top-four RAG comparisons.

### 8.5 Requests, tokens, and latency

| System | HTTP requests per run | Pooled measured tokens | Pooled mean answer time |
|---|---:|---:|---:|
| PLN-RAG | 300 | 11,942,245 | 4.24 s |
| One-shot vector RAG | 40 | 35,741 | 1.30 s |
| Iterative vector RAG | 40 | 35,947 | 1.33 s |
| Full context | 40 | 56,771 | 1.17 s |

PLN-RAG also required 1,351.64 seconds of world-learning time across the three runs. One-shot and iterative index construction totaled approximately 33.98 and 33.25 seconds respectively. These stages are not directly equivalent: PLN learning includes natural-language parsing and persistent symbolic ingestion, while vector index construction is local embedding work. Answer latency also excludes PLN learning and excludes the one-time vector index build.

No monetary-cost metric is reported because cost was not a defined aggregate benchmark metric. Token and request counts are the auditable resource indicators.

## 9. Representative Case Analysis

### 9.1 `bench-01-supported`: direct fact control case

The target is directly asserted in `S01`, so the canonical proof contains one sentence. PLN-RAG, one-shot RAG, iterative RAG, and full context all answered correctly in every run. The case confirms basic ingestion, retrieval, label parsing, and fact recognition, but it does not discriminate multi-step reasoning ability.

### 9.2 `bench-03-supported`: proof fits top four, but one-shot omits a premise

The canonical proof requires `S03`, `S08`, and `S09`. A three-sentence proof fits the top-four capacity in principle. Nevertheless, one-shot RAG omitted required sentence `S03` in every run, its retrieved subset could not prove the claim, and it returned `NOT_ESTABLISHED`. Iterative retrieval recovered a sufficient chain and answered correctly.

This case isolates ranking failure rather than capacity failure. Direct question similarity did not surface every intermediate rule, while a second retrieval round following initially selected evidence did.

### 9.3 `bench-12-supported`: proof exceeds the vector context cap

The canonical proof requires six sentences: `S02`, `S03`, `S04`, `S05`, `S06`, and `S11`. Both vector systems are limited to four distinct evidence sentences, so the full proof cannot fit. One-shot and iterative RAG returned `NOT_ESTABLISHED` in all three runs. PLN-RAG and full context answered correctly.

This is the clearest capacity case. It does not show that vector similarity ranked a feasible proof incorrectly; the configured evidence window made a complete six-sentence proof impossible.

### 9.4 Run 2 `bench-14-supported`: correct iterative label without proving evidence

The canonical proof requires `S05`, `S06`, and `S09`. Iterative retrieval returned `S06`, `S05`, `S02`, and `S12`, omitting `S09`. The LLM nevertheless returned `SUPPORTED` and cited only `S06` and `S05`. Independent diagnostics found that neither the retrieved context nor the citations proved the target.

The label is correct under strict classification scoring, but the case demonstrates why label accuracy and evidence-grounded correctness must be reported separately.

### 9.5 Run 3 `bench-04-control`: unsupported iterative false positive

The control has no valid proof in the world. Iterative RAG returned `SUPPORTED` and cited `S02`, `S11`, `S01`, and `S07`; the citation subset does not prove the claim. This was the only pooled iterative control error.

The case shows that adding retrieval rounds can increase recall without guaranteeing conservative open-world behavior.

### 9.6 `bench-12-control`: stable full-context false positive

The control requires a conjunction whose one branch is missing for the target entity. Full context received all 12 sentences but returned `SUPPORTED` in all three runs. This single unique case accounts for all three full-context errors. The model appears to have accepted partial support while overlooking the missing conjunct.

PLN-RAG returned `NOT_ESTABLISHED` with an empty proof in every run. This is a meaningful benefit of proof-existence scoring: incomplete support does not become a positive label merely because related facts are present.

### 9.7 Run 2 `bench-15-supported`: query-added bridge

The learned world supports a mentoring composition that derives `CanTrain hana aster`, while the target asks for `CanGuide hana aster`. During query parsing, PLN-RAG added:

```text
(: train_guide_bridge
   (Implication
     (Premises (CanTrain $person $other))
     (Conclusions (CanGuide $person $other)))
   (STV 1.0 1.0))
```

The returned proof explicitly uses this bridge. The benchmark records `query_mutated_state=true`, one added statement, and `potential_query_contamination=true`. The result is correct under the implemented rule that a nonempty proof yields `SUPPORTED`, but it is not evidence that the source world alone produced that proof. This is the only detected query-state mutation across the three finalized runs and must accompany any claim of perfect PLN-RAG performance.

## 10. Engineering Decisions and Iterations

### 10.1 Formal ambiguity risk: independent oracle agreement

The expected answers were authored from explicit clause positions, then checked by structurally independent forward and backward solvers. Admission requires exact proof-frontier agreement, not only agreement on the final label. This reduces the risk that a mistake in one inference algorithm silently defines the benchmark truth.

### 10.2 Cross-question state risk: immutable snapshots

PLN-RAG learns a world once, but each question starts from a restored read-only snapshot in a fresh process. Unique world collections and before/after state hashes make mutation detectable. The Run 2 bridge demonstrates the value of retaining this telemetry: aggregate accuracy alone would not expose the added rule.

### 10.3 Provider and model drift risk: audited requests

The runs pin model, provider, temperature, reasoning effort, output allowance, retry behavior, fallback behavior, and cache policy. The harness records all 420 HTTP requests per run and verifies reported provider/model identities and HTTP outcomes. This turns configuration claims into inspectable run evidence.

### 10.4 Weak-comparator risk: three baseline roles

One-shot RAG represents a standard direct semantic retriever. Iterative RAG tests whether a deterministic second retrieval stage can follow intermediate concepts without increasing evidence capacity. Full context removes retrieval entirely. Together they separate three increasingly strong conditions rather than comparing PLN-RAG only against the weakest baseline.

### 10.5 Retrieval/reasoning ambiguity: independent sufficiency checks

After each answer, the benchmark uses its logical oracle to test whether retrieved, displayed, or cited sentence subsets can prove the target. These checks are independent of the model's label and make it possible to distinguish missing evidence from a reasoning error over sufficient evidence.

### 10.6 Run variability: three finalized repetitions

Repeating the full matrix three times revealed which outcomes were stable and which depended on the final language-model decision. One-shot retrieval and its nine misses were stable; iterative accuracy varied from 82.5% to 87.5%; full context repeated the same control error; PLN-RAG repeated every label but showed one query mutation in one repetition.

## 11. Key Research Findings

1. **Native PLN-RAG achieved the highest measured label accuracy.** It scored 120/120, compared with 117/120 for full context, 102/120 for iterative RAG, and 93/120 for one-shot RAG.
2. **The largest vector-RAG failure mode was incomplete evidence retrieval.** All 27 pooled one-shot supported errors occurred with contexts that could not prove the target.
3. **Iterative retrieval materially improved proof recovery, but not uniformly.** It raised supported accuracy from 33/60 to 43/60 and retrieved proving evidence in 42/60 supported observations. Gains were strongest for implication chains; relational and conjunction results remained weaker.
4. **A fixed top-four evidence budget imposes a structural ceiling.** Three supported targets require five or six canonical proof sentences. No top-four ranking strategy can include those complete canonical proofs.
5. **Full context shows that most top-four failures are retrieval failures.** With all 12 sentences, the same baseline LLM solved all 60 supported observations.
6. **Complete context does not guarantee correct open-world abstention.** Full context repeatedly false-positived on `bench-12-control`, where one required conjunction branch was absent.
7. **Explicit proof paths provide stronger diagnostics than fluent labels or citations.** The iterative `bench-14-supported` result was label-correct without proving context; `bench-04-control` was confidently wrong with non-proving citations; PLN-RAG's empty proof correctly represented insufficient evidence on `bench-12-control`.
8. **The PLN-RAG advantage over full context is small and qualified.** It is one question per run, with a run-level paired bootstrap lower bound of zero, and one separate PLN observation contains a query-added bridge. The results support further study, not a broad claim of universal symbolic superiority.
9. **PLN-RAG's accuracy came with much greater computation.** Its pooled token use was over 200 times the full-context baseline's measured token use and over 300 times either retrieval baseline's use. Native accuracy and resource efficiency answer different research questions.

## 12. Interpretation Limitations

- **Small authored benchmark.** Twenty worlds and 40 questions are enough for detailed error analysis but not broad generalization.
- **Template dependence.** Worlds share a controlled vocabulary and construction patterns. Wilson intervals are descriptive because question outcomes are not independent samples from a natural task distribution.
- **Native evidence is unequal.** PLN-RAG and full context can access 12 sentences; both vector systems expose at most four. The comparison evaluates complete native architectures rather than reasoners under identical evidence.
- **Compute is unequal.** PLN-RAG performs parsing, persistence, retrieval, proof search, and substantially more LLM calls. No conclusion about cost efficiency follows from accuracy alone.
- **Controlled English reduces language ambiguity.** Results principally test evidence assembly and formal reasoning in a constrained language, not robust parsing of unconstrained prose.
- **Paired controls are constructed missing-premise cases.** They are useful for open-world abstention but do not cover the full diversity of naturally occurring unanswerable questions.
- **Canonical proof coverage is not exhaustive proof identity.** Sufficiency diagnostics correctly allow any proof from a subset, but proof-size reporting uses the canonical smallest minimum-depth proof.
- **PLN source mapping is diagnostic.** Returned proof traces are mapped to source IDs but are not independently replayed by the scorer as native proof objects.
- **One PLN observation is potentially contaminated.** Run 2 `bench-15-supported` depends on a query-added bridge and prevents an unqualified claim that all 120 PLN labels were supported solely by learned source statements.
- **External runtime details are incomplete.** Manifests identify the Docker image, source hashes, model profile, service URLs, and embedding model name, but not every host hardware, operating-system, service-version, or embedding-runtime detail.
- **No monetary-cost analysis.** Request and token counts are measured; a normalized monetary cost comparison was not defined.

## 13. Reproducibility and Evidence Index

### 13.1 Fixed run configuration

| Item | Value |
|---|---|
| Dataset semantic SHA-256 | `8d4bc9726a01284833a09acade4476e885022efcace94c8a6d5b38e98f38fba8` |
| Model | `openrouter/z-ai/glm-5.3` for PLN-RAG; `z-ai/glm-5.3` baseline request model |
| Provider | `inference-net` |
| Temperature | `0` |
| Reasoning effort | `medium` |
| Maximum output | `4096` tokens |
| Provider fallbacks | Disabled |
| Retries | Disabled |
| Cache | Disabled |
| One-shot evidence limit | 4 sentences |
| Iterative retrieval | 2 rounds, 2 new sentences per round, maximum 4 distinct sentences |
| PLN retrieval limit | 12 |
| Full-context evidence | All 12 sentences |
| Docker image digest | `sha256:67c7afed08a4359ef016609a5642dff2b9ca2b8ed3d30b2d2fb041eb58bf7284` |
| Audited HTTP requests | 420 per run |

The authoritative implementation identity for these results is the per-file SHA-256 inventory in each run manifest plus the Docker image digest. The present working files should not be assumed to reproduce an earlier image merely because paths match; use the recorded hashes and preserved artifacts.

### 13.2 Final run artifacts

- Run 1: `artifacts/benchmark/full-glm-native-r1/`
- Run 2: `artifacts/benchmark/full-glm-native-r2/`
- Run 3: `artifacts/benchmark/full-glm-native-r3/`

For each run:

- `manifest.json`: model, provider, evidence limits, dataset fingerprint, image digest, deadlines, system order, and source hashes.
- `summary.json`: aggregate and subgroup scores, descriptive intervals, paired bootstrap comparisons, requests, tokens, timing, and sufficiency diagnostics.
- `records.json`: all per-question labels, evidence, citations, proofs, mutations, expected values, and correctness fields.
- `report.md`, `oracle.json`, `worlds.json`, and `hand_expected.json`: human-readable results plus the frozen input and validated answer-key evidence.
- `docker.launch.json` and `docker.doctor.json`: recorded launch configuration and runtime readiness checks.
- `pln_rag/manifest.json`: detailed PLN runtime and source-hash inventory.
- `pln_rag/gate.json`: PLN completion and failed-question checks.

The Git branch intentionally retains this compact evidence set rather than the complete 345 MB generated run trees. Full request streams, repeated learning payloads, per-question native outputs, and private runtime traces remain local under the corresponding artifact directories and `runtime/runs/full-glm-native-r1/`, `runtime/runs/full-glm-native-r2/`, and `runtime/runs/full-glm-native-r3/`. Credentials must remain outside report artifacts.

### 13.3 Dataset and oracle evidence

- `b1/dataset.py`: authored 20-world construction.
- `b1/language.py`: deterministic controlled-English renderer and vocabulary.
- `data/benchmark/worlds.json`: frozen worlds and questions.
- `data/benchmark/hand_expected.json`: construction-derived expected labels, depths, and proof IDs.
- `b1/forward.py`: independent forward solver.
- `b1/backward.py`: independent backward solver.
- `b1/oracle.py`: consensus and dataset-admission rules.
- `artifacts/oracle/benchmark.answer_key.json`: validated answer key.

### 13.4 Implementation evidence

- `b1/comparison.py`: orchestration, annotations, sufficiency checks, metrics, intervals, and reporting.
- `b1/pln_runner.py`: world ingestion, snapshots, isolation, and native execution.
- `b1/pln_worker.py`: PLN parser/reasoner adapter and query-state auditing.
- `b1/records.py`: proof-derived PLN labels, source mapping, and record validation.
- `b1/baseline.py`: baseline adapter and request accounting.
- `../normal-rag/normal_rag/core.py`: prompts, embeddings, one-shot retrieval, iterative retrieval, full-context assembly, and strict parsing.
- `BENCHMARK_PROTOCOL.md`: native comparison contract and reporting requirements.

### 13.5 Reproduction entry point

From `rule-chain-depth`, a fresh native run uses:

```bash
python3 -m b1 benchmark \
  --systems pln_rag rag iterative_rag full_context \
  --track native \
  --container pln-rag-pln-rag-1 \
  --run-id <new-unique-run-id>
```

Before paid execution, regenerate and validate the oracle and run both test suites as specified in `BENCHMARK_PROTOCOL.md`. Reproduction also requires the recorded model/provider availability, embedding service, vector service, and Docker image.

## 14. Proposed Standalone Report Structure

The future report can be shorter and more argumentative than this evidence document while retaining the essential qualifications.

1. **Abstract:** Research question, four systems, 20 worlds, three runs, principal accuracies, and the native-comparison caveat.
2. **Introduction:** Why multi-premise logical reasoning stresses similarity-based retrieval and why explicit proofs matter.
3. **Research Questions:** End-to-end accuracy, retrieval versus reasoning failures, evidence-grounding quality, and resource tradeoffs.
4. **Systems:** PLN-RAG, one-shot RAG, iterative RAG, and full context, including the reason each comparator is necessary.
5. **Dataset:** Authored Python provenance, controlled-English rendering, 20-world construction, category/world counts, depth balance, proof sizes, distractors, and paired controls.
6. **Methodology:** Frozen inputs, oracle consensus, native evidence policy, model controls, state isolation, strict scoring, and three-run design.
7. **Results:** Run-level and pooled accuracy, supported/control split, category table, retrieval sufficiency, pairwise intervals, requests, tokens, and stage-aware timing.
8. **Case Studies:** `bench-03-supported`, `bench-12-supported`, `bench-14-supported`, `bench-12-control`, and the Run 2 `bench-15-supported` qualification.
9. **Discussion:** Retrieval bottlenecks, iterative gains, full-context behavior, proof diagnostics, and the difference between accuracy and efficiency.
10. **Threats to Validity:** Authored templates, small sample, unequal native evidence, controlled language, runtime reproducibility gaps, and query-added proof contamination.
11. **Conclusion:** Narrow evidence that persistent symbolic reasoning is robust on this benchmark, alongside the need for larger independently constructed evaluations and controlled evidence experiments.
12. **Appendices:** Complete configuration, source-hash inventory, per-case results, oracle details, prompts, retrieval traces, and artifact index.

The report should lead with the empirical result but frame the strongest defensible conclusion narrowly: on this authored controlled-English benchmark, native PLN-RAG was more accurate and more diagnostically explicit than top-four vector RAG, while full-context performance showed that most of the vector gap was attributable to retrieval and while compute inequality and one query-added proof materially qualify the comparison.
