"""Run identical questions through Docker/local PLN-RAG and host baselines."""

from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
import re
import subprocess
import uuid

from .baseline import load_baseline, matched_settings, run_question
from .dataset import validate_full
from .docker_runtime import prepare_benchmark
from .environment import configured_environment, file_sha256, redact, secret_values
from .io import read_worlds, write_json
from .llm_control import LLMSettings
from .oracle import consensus, validate
from .pln_runner import public_sentences, run_pln

SYSTEMS = ("pln_rag", "rag", "iterative_rag", "full_context")
DEFAULT_SYSTEMS = SYSTEMS
UNMEASURED = "unmeasured"


def comparison_environment(root, *, qdrant_url=None, ollama_url=None, pln_runtime="docker",
                           pln_top_k=12):
    env = configured_environment(root)
    llm = LLMSettings.from_env(env)
    # Materialize defaults so the Docker image and host cannot select different ones.
    defaults = {"OPENROUTER_BASE_URL": llm.api_base,
                 "B1_LLM_TEMPERATURE": str(llm.temperature), "B1_LLM_MAX_TOKENS": str(llm.max_tokens),
                 "B1_LLM_REASONING_EFFORT": llm.reasoning_effort or "",
                 "B1_MAX_LLM_CALLS": str(llm.max_calls), "B1_LLM_MIN_INTERVAL": str(llm.minimum_interval),
                "B1_LLM_TIMEOUT": "60", "B1_QUERY_TIMEOUT": "180", "B1_LEARN_TIMEOUT": "900",
                "B1_REASONING_TIMEOUT": "30", "B1_EMBEDDING_TIMEOUT": "30"}
    for key, value in defaults.items():
        env.setdefault(key, value)
    env["B1_QDRANT_URL"] = qdrant_url or env.get("B1_QDRANT_URL", "http://127.0.0.1:6333" if pln_runtime == "docker" else "http://127.0.0.1:16333")
    if ollama_url:
        env["OLLAMA_URL"] = ollama_url
    env["B1_PLN_TOP_K"] = str(pln_top_k)
    for key in ("B1_LLM_TIMEOUT", "B1_QUERY_TIMEOUT", "B1_LEARN_TIMEOUT", "B1_REASONING_TIMEOUT", "B1_EMBEDDING_TIMEOUT"):
        # PLN's worker uses integer LLM/reasoning seconds; validate before spending calls.
        value = int(env[key])
        if value <= 0:
            raise ValueError(f"{key} must be a positive integer number of seconds")
    if env["PARSER"] != "canonical_pln":
        raise ValueError("The comparison requires PARSER=canonical_pln")
    return env, llm


def skipped_record(system, kind, detail):
    return {"schema_version": 1, "system": system, "mode": system,
            "label": "ERROR", "attempted": False, "error_kind": kind, "error_detail": detail,
            "answer_seconds": UNMEASURED, "index_build_seconds": UNMEASURED,
            "retrieved": [], "cited": [], "retrieved_sentence_ids": [], "used_sentence_ids": [],
            "invalid_citation_count": 0, "raw_model_output": None,
            "model": UNMEASURED, "provider": UNMEASURED,
            "usage": {key: UNMEASURED for key in ("prompt_tokens", "completion_tokens", "total_tokens")},
            "llm_http_calls": []}


def annotate(record, system, world, question, oracle_answer):
    """Called only after the system returned or the operation was explicitly skipped."""
    record.update(system=system, world_id=world.id, question_id=question.id,
                  question=question.text, expected_label=question.expected_label,
                   depth_bucket=question.depth_bucket, rule_kind=question.rule_kind,
                   proof_size=oracle_answer.get("proof_size"),
                   correct=record["label"] == question.expected_label)
    record.setdefault("attempted", True)
    required = oracle_answer["proof_sentence_ids"] or None
    retrieved = (record.get("retrieved_sentence_ids", []) if system == "pln_rag"
                 else [r["id"] for r in record.get("retrieved", [])])
    context = [s["id"] for s in record.get("context", [])]
    measured = record["attempted"] and bool(required)
    record["proof_coverage"] = {
        "required_ids": required,
        "retrieved_contains_required": (set(required) <= set(retrieved)
            if measured and ((system == "pln_rag" and bool(record.get("retrieval_calls"))) or
                             (record.get("mode", system) in ("rag", "iterative_rag") and
                              bool(record.get("context")))) else UNMEASURED),
        "context_contains_required": (set(required) <= set(context)
            if measured and system != "pln_rag" and context else UNMEASURED),
        "required_sentence_count": len(required) if required else UNMEASURED,
        "fits_top_four": len(required) <= 4 if required else UNMEASURED,
        "retrieval_top_k": record.get("retrieval_top_k", UNMEASURED),
        "fits_retrieval_limit": (len(required) <= record["retrieval_top_k"]
            if required and type(record.get("retrieval_top_k")) is int else UNMEASURED),
    }
    # Supplied-proof coverage and logical sufficiency are different measurements.
    # The oracle accepts any proof from the retrieved subset, after the answer.
    retrieval_measured = record["proof_coverage"]["retrieved_contains_required"] != UNMEASURED
    context_measured = record["proof_coverage"]["context_contains_required"] != UNMEASURED
    for name, ids, available in (("retrieved_proves_claim", retrieved, retrieval_measured),
                                  ("context_proves_claim", context, context_measured)):
        record["proof_coverage"][name] = (consensus(tuple(s for s in world.sentences if s.id in ids), question.goal).label == "SUPPORTED"
                                               if available else UNMEASURED)
    cited = record.get("cited", [])
    record["proof_coverage"]["citation_proves_claim"] = (
        consensus(tuple(s for s in world.sentences if s.id in cited), question.goal).label == "SUPPORTED"
        if system != "pln_rag" and record["attempted"] and bool(cited) else UNMEASURED)
    evidence_access = record.get("evidence_access_ids", [])
    record["proof_coverage"]["evidence_access_proves_claim"] = (
        consensus(tuple(sentence for sentence in world.sentences if sentence.id in evidence_access),
                  question.goal).label == "SUPPORTED"
        if record["attempted"] and bool(required) and evidence_access else UNMEASURED)
    added = record.get("query_added_statements", [])
    record["potential_query_contamination"] = bool(
        system == "pln_rag" and record.get("label") == "SUPPORTED" and added)
    return record


def score(rows):
    count = len(rows)
    correct = sum(r["correct"] for r in rows)
    times = [r["answer_seconds"] for r in rows if type(r.get("answer_seconds")) in (int, float)]
    if count:
        z = 1.959963984540054
        p = correct / count
        center = (p + z * z / (2 * count)) / (1 + z * z / count)
        margin = z * math.sqrt(p * (1 - p) / count + z * z / (4 * count * count)) / (1 + z * z / count)
        interval = [max(0.0, center - margin), min(1.0, center + margin)]
    else:
        interval = UNMEASURED
    return {"questions": count, "correct": correct,
            "errors": sum(r["label"] == "ERROR" for r in rows),
            "not_attempted": sum(not r["attempted"] for r in rows),
            "accuracy": correct / count if count else UNMEASURED,
            "accuracy_wilson_95": interval,
            "timeouts": sum("timeout" in (r.get("error_kind") or "") for r in rows),
            "mean_answer_seconds": sum(times) / len(times) if times else UNMEASURED,
             "timed_questions": len(times)}


def paired_comparison(records, system_a, system_b, *, replicates=10000, seed=1729):
    left = {(r["world_id"], r["question_id"]): r for r in records if r["system"] == system_a}
    right = {(r["world_id"], r["question_id"]): r for r in records if r["system"] == system_b}
    keys = sorted(left.keys() & right.keys())
    worlds = sorted({world for world, _ in keys})
    outcomes = Counter()
    world_differences = {}
    for key in keys:
        a, b = bool(left[key]["correct"]), bool(right[key]["correct"])
        outcomes[(a, b)] += 1
    for world in worlds:
        world_keys = [key for key in keys if key[0] == world]
        world_differences[world] = sum(int(left[key]["correct"]) - int(right[key]["correct"])
                                       for key in world_keys) / len(world_keys)
    rng = random.Random(seed)
    boot = []
    if worlds:
        for _ in range(replicates):
            sampled = [world_differences[rng.choice(worlds)] for _ in worlds]
            boot.append(sum(sampled) / len(sampled))
        boot.sort()
        interval = [boot[int(0.025 * replicates)], boot[min(replicates - 1, int(0.975 * replicates))]]
    else:
        interval = UNMEASURED
    world_outcomes = Counter("a_wins" if value > 0 else "b_wins" if value < 0 else "ties"
                             for value in world_differences.values())
    return {
        "system_a": system_a, "system_b": system_b,
        "matched_worlds": len(worlds), "matched_questions": len(keys),
        "accuracy_difference_a_minus_b": (
            sum(int(left[key]["correct"]) - int(right[key]["correct"]) for key in keys) / len(keys)
            if keys else UNMEASURED),
        "question_outcomes": {"both_correct": outcomes[(True, True)],
                              "a_only_correct": outcomes[(True, False)],
                              "b_only_correct": outcomes[(False, True)],
                              "neither_correct": outcomes[(False, False)]},
        "world_score_outcomes": {name: world_outcomes[name] for name in ("a_wins", "ties", "b_wins")},
        "world_cluster_bootstrap_95": interval,
        "bootstrap_unit": "world", "bootstrap_replicates": replicates, "bootstrap_seed": seed,
    }


def build_summary(records, systems, worlds, calls, learning, budget, *, track="custom", split="all"):
    by_system = {}
    for system in systems:
        rows = [r for r in records if r["system"] == system]
        observed = calls.get(system, [])
        world_index_seconds = {}
        for row in rows:
            if system in ("rag", "iterative_rag") and type(row.get("index_build_seconds")) in (int, float):
                world_index_seconds.setdefault(row["world_id"], row["index_build_seconds"])
        by_system[system] = {
            **score(rows),
            "by_depth": {str(d): score([r for r in rows if r["depth_bucket"] == d]) for d in range(4)},
            "supported_by_depth": {str(d): score([r for r in rows if r["depth_bucket"] == d and r["expected_label"] == "SUPPORTED"]) for d in range(4)},
            "supported_by_proof_size": {str(size): score([r for r in rows if r.get("proof_size") == size])
                                        for size in sorted({r["proof_size"] for r in rows if type(r.get("proof_size")) is int})},
            "by_rule_kind": {k: score([r for r in rows if r["rule_kind"] == k]) for k in sorted({r["rule_kind"] for r in rows})},
            "by_expected_label": {k: score([r for r in rows if r["expected_label"] == k]) for k in ("SUPPORTED", "NOT_ESTABLISHED")},
            "providers_reported": sorted({c.get("provider", UNMEASURED) for c in observed}),
            "models_reported": sorted({c.get("model", UNMEASURED) for c in observed}),
            "http_attempts_observed": len(observed),
            "usage": {key: {
                "measured_sum": sum(c["usage"][key] for c in observed if type(c.get("usage", {}).get(key)) is int)
                    if any(type(c.get("usage", {}).get(key)) is int for c in observed) else UNMEASURED,
                "unmeasured_calls": sum(type(c.get("usage", {}).get(key)) is not int for c in observed),
            } for key in ("prompt_tokens", "completion_tokens", "total_tokens")},
            "invalid_citations": sum(r.get("invalid_citation_count", 0) for r in rows) if system != "pln_rag" else UNMEASURED,
            "retrieval_coverage": dict(Counter(str(r["proof_coverage"]["retrieved_contains_required"]) for r in rows)),
            "retrieval_sufficiency": dict(Counter(str(r["proof_coverage"]["retrieved_proves_claim"]) for r in rows)),
            "citation_sufficiency": dict(Counter(str(r["proof_coverage"]["citation_proves_claim"]) for r in rows)),
            "evidence_access_sufficiency": dict(Counter(
                str(r["proof_coverage"]["evidence_access_proves_claim"]) for r in rows)),
            "query_state_mutations": sum(bool(r.get("query_added_statements")) for r in rows) if system == "pln_rag" else UNMEASURED,
            "potential_query_contamination": sum(bool(r.get("potential_query_contamination")) for r in rows) if system == "pln_rag" else UNMEASURED,
            "world_index_build_seconds": sum(world_index_seconds.values()) if world_index_seconds else UNMEASURED,
            "retrieval_top_k": next((r["retrieval_top_k"] for r in rows
                                     if type(r.get("retrieval_top_k")) is int),
                                     next((r["retrieval_max_evidence"] for r in rows
                                           if type(r.get("retrieval_max_evidence")) is int), UNMEASURED)),
        }
        if system == "iterative_rag":
            by_system[system]["retrieval_stop_reasons"] = dict(Counter(
                r.get("retrieval_trace", {}).get("stop_reason", UNMEASURED) for r in rows))
            by_system[system]["mean_retrieval_rounds"] = (
                sum(len(r.get("retrieval_trace", {}).get("rounds", [])) for r in rows) / len(rows) if rows else UNMEASURED)
            by_system[system]["mean_distinct_evidence"] = (
                sum(len(r.get("retrieved", [])) for r in rows) / len(rows) if rows else UNMEASURED)
    total = sum(len(w.questions) for w in worlds) * len(systems)
    learned_count = sum(r.get("sentence_count", len(r.get("sentences", []))) for r in learning)
    failures = sum(r.get("parse_failure_count", 0) for r in learning)
    rag = {r["question_id"]: r for r in records if r["system"] == "rag" and r["expected_label"] == "SUPPORTED"}
    full = {r["question_id"]: r for r in records if r["system"] == "full_context"}
    comparisons = [{"question_id": qid, "rag_label": r["label"], "full_context_label": full[qid]["label"],
                    "retrieval_proves_claim": r["proof_coverage"]["retrieved_proves_claim"]} for qid, r in rag.items() if qid in full]
    pairs = [paired_comparison(records, systems[i], systems[j])
             for i in range(len(systems)) for j in range(i + 1, len(systems))]
    return {"schema_version": 2, "artifact_type": "benchmark_summary",
            "comparison_track": track, "dataset_split": split,
            "status": "COMPLETE_WITH_ERRORS" if any(r["label"] == "ERROR" for r in records) else "COMPLETE",
            "complete": len(records) == total, "execution_complete": len(records) == total and all(r["attempted"] for r in records),
            "world_count": len(worlds), "questions_per_system": total // len(systems),
            "record_count": len(records), "expected_records": total,
            "requests_reserved": json.loads(budget.read_text())["calls"] if budget.exists() else 0,
             "systems": by_system,
            "paired_system_comparisons": pairs,
            "pln_learning_seconds": sum(r["learning_seconds"] for r in learning if type(r.get("learning_seconds")) in (int, float)) if learning else UNMEASURED,
            "pln_sentence_parse_failures": sum(r.get("parse_failure_count", 0) for r in learning) if learning else UNMEASURED,
            "pln_sentence_parse_failure_share": failures / learned_count if learned_count else UNMEASURED,
            "supported_baseline_comparisons": comparisons,
            "interval_note": "Wilson 95% binomial intervals are descriptive; paired questions and repeated templates are not independent samples.",
            "accuracy_denominator": "All selected questions, including ERROR and explicitly unattempted records",
            "timing_note": "Answer time includes LLM calls and pacing. PLN learning is separate; RAG index time is in each record."}


def render_report(out, summary, records):
    lines = ["# Shared rule-chain-depth results", "", f"Track: **{summary['comparison_track']}**; split: **{summary['dataset_split']}**", "",
             f"Status: **{summary['status']}**", "",
             f"{summary['world_count']} worlds; {summary['questions_per_system']} questions per selected system.", "",
             "Accuracy includes errors and unattempted questions in its denominator. COMPLETE describes execution, not perfect accuracy.", "",
             "| System | Correct / total | Errors | Not attempted | Accuracy |", "|---|---:|---:|---:|---:|"]
    for system, row in summary["systems"].items():
        lines.append(f"| {system} | {row['correct']} / {row['questions']} | {row['errors']} | {row['not_attempted']} | {row['accuracy']:.1%} |")
    lines += ["", "## Accuracy by depth", "", "| System | Depth | Correct / total | Errors |", "|---|---:|---:|---:|"]
    for system, row in summary["systems"].items():
        for depth, group in row["by_depth"].items():
            lines.append(f"| {system} | {depth} | {group['correct']} / {group['questions']} | {group['errors']} |")
    lines += ["", "## Supported accuracy by proof size", "",
              "| System | Proof sentences | Correct / total | Accuracy |", "|---|---:|---:|---:|"]
    for system, row in summary["systems"].items():
        for size, group in row["supported_by_proof_size"].items():
            lines.append(f"| {system} | {size} | {group['correct']} / {group['questions']} | {group['accuracy']:.1%} |")
    lines += ["", "## Paired comparisons", "",
              "Intervals resample whole worlds and retain each world's supported/control pair.", "",
              "| System A | System B | Difference | A-only | B-only | World-clustered 95% interval |",
              "|---|---|---:|---:|---:|---:|"]
    for pair in summary["paired_system_comparisons"]:
        interval = pair["world_cluster_bootstrap_95"]
        rendered = (f"[{interval[0]:.1%}, {interval[1]:.1%}]" if isinstance(interval, list)
                    else str(interval))
        lines.append(f"| {pair['system_a']} | {pair['system_b']} | {pair['accuracy_difference_a_minus_b']:.1%} | "
                     f"{pair['question_outcomes']['a_only_correct']} | {pair['question_outcomes']['b_only_correct']} | {rendered} |")
    lines += ["", "Unsupported questions are grouped by their supported pair's depth; their actual proof depth is null.", "",
              "See [summary.json](summary.json) for per-kind scores, providers, tokens, and timing; [records.json](records.json) for every result.", "",
              "Top-four retrieval cannot contain a supplied proof needing more than four sentences. Coverage records disclose this limit.", "",
              "## Per-question records", "", "| System | Question | Label | Expected | Record |", "|---|---|---|---|---|"]
    for r in records:
        path = f"{r['system']}/{r['world_id']}/{r['question_id']}/record.json"
        lines.append(f"| {r['system']} | {r['question_id']} | {r['label']} | {r['expected_label']} | [record]({path}) |")
    lines += ["", "PLN-RAG's `pln_rag/raw.md` shows learned atoms and proofs when its runner started. Baseline operation folders contain exact requests, response bytes, raw model text, and the retrieved/shown sentences in each record."]
    (out / "report.md").write_text("\n".join(lines) + "\n")


def run_comparison(root: Path, *, systems=DEFAULT_SYSTEMS, dataset_kind="benchmark", worlds_path=None,
                   expected_path=None, world_limit=None, normal_repo=None, pln_runtime="docker",
                   container=None, repo=None, python=None, qdrant_url=None, ollama_url=None,
                   rag_top_k=4, pln_top_k=12, track="native", split="all",
                   max_rounds=2, round_top_k=2, max_evidence=4,
                   prepare_only=False, run_id=None) -> Path:
    root = root.resolve()
    systems = tuple(systems)
    if not systems or len(set(systems)) != len(systems) or not set(systems) <= set(SYSTEMS):
        raise ValueError("Choose unique systems from pln_rag, rag, iterative_rag, full_context")
    if dataset_kind not in ("pilot", "benchmark") or pln_runtime not in ("docker", "local"):
        raise ValueError("Invalid dataset or PLN runtime")
    for name, value in (("rag-top-k", rag_top_k), ("pln-top-k", pln_top_k),
                        ("max-rounds", max_rounds), ("round-top-k", round_top_k),
                        ("max-evidence", max_evidence)):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if track not in ("native", "shared_iterative", "custom"):
        raise ValueError("track must be native, shared_iterative, or custom")
    if track == "native" and (rag_top_k, pln_top_k) != (4, 12):
        raise ValueError("The native track requires rag-top-k=4 and pln-top-k=12")
    if track == "shared_iterative" and ("iterative_rag" not in systems or max_evidence != 4):
        raise ValueError("The shared_iterative track requires iterative_rag and max-evidence=4")
    if split != "all" and world_limit is not None:
        raise ValueError("A named split cannot be combined with world-limit")
    data = root / "data" / dataset_kind
    worlds_path, expected_path = Path(worlds_path or data / "worlds.json"), Path(expected_path or data / "hand_expected.json")
    dataset_dir = worlds_path.parent
    all_worlds = read_worlds(worlds_path)
    if any(not re.fullmatch(r"[A-Za-z0-9_-]+", identifier)
           for w in all_worlds for identifier in (w.id, *(q.id for q in w.questions))):
        raise ValueError("World and question IDs must be safe directory names")
    expected = json.loads(expected_path.read_text())
    oracle = validate_full(all_worlds, expected) if dataset_kind == "benchmark" else validate(all_worlds, expected)
    if dataset_kind == "pilot" and len(all_worlds) != 8:
        raise ValueError("Pilot comparison requires the eight-world dataset")
    split_metadata = None
    if split != "all":
        split_id, partition = split.split(":", 1)
        split_path = dataset_dir / "splits" / f"{split_id}.json"
        split_metadata = json.loads(split_path.read_text(encoding="utf-8"))
        if split_metadata["base_dataset_sha256"] != oracle["dataset_sha256"]:
            raise ValueError("Split manifest does not match the frozen dataset")
        selected = split_metadata[f"{partition}_world_ids"]
        if set(split_metadata["development_world_ids"]) & set(split_metadata["heldout_world_ids"]):
            raise ValueError("Split partitions overlap")
        if set(split_metadata["development_world_ids"]) | set(split_metadata["heldout_world_ids"]) != {w.id for w in all_worlds}:
            raise ValueError("Split partitions do not cover the frozen dataset")
        worlds = tuple(w for w in all_worlds if w.id in selected)
        if [w.id for w in worlds] != selected:
            raise ValueError("Split IDs are missing or not in frozen dataset order")
        limit = len(worlds)
    else:
        limit = len(all_worlds) if world_limit is None else world_limit
        worlds = all_worlds[:limit]
    if not 1 <= limit <= len(all_worlds):
        raise ValueError(f"world-limit must be between 1 and {len(all_worlds)}")
    env, llm = comparison_environment(root, qdrant_url=qdrant_url, ollama_url=ollama_url,
                                      pln_runtime=pln_runtime, pln_top_k=pln_top_k)
    normal_repo = Path(normal_repo or root.parent / "normal-rag").resolve()
    # Loading only these stdlib modules also validates the common settings for PLN-only runs.
    core, config = load_baseline(normal_repo)
    settings = matched_settings(config, env, llm)
    if "pln_rag" in systems and pln_runtime == "docker" and not container:
        raise ValueError("Supply --container for the Docker PLN-RAG runtime")
    repo = Path(repo or root.parent / "PLN-RAG").resolve()
    python = Path(python or root / ".venv/bin/python").absolute()
    if "pln_rag" in systems and pln_runtime == "local" and (not repo.is_dir() or not python.is_file()):
        raise ValueError("The local PLN-RAG repo and Python interpreter must exist")
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Unsafe run ID")
    out = root / "artifacts/benchmark" / run_id
    out.mkdir(parents=True, exist_ok=False)
    budget = root / "runtime/runs" / run_id / "request_budget.json"
    if budget.parent.exists():
        raise ValueError("Run ID already has runtime state; use a fresh ID")
    write_json(out / "worlds.json", {"schema_version": 1, "worlds": [w.to_dict() for w in all_worlds]})
    write_json(out / "hand_expected.json", expected)
    write_json(out / "oracle.json", oracle)
    job = {"run_id": run_id, "world_limit": limit, "selected_world_ids": [w.id for w in worlds],
           "dataset_kind": dataset_kind,
            "worlds_path": str(out / "worlds.json"), "expected_path": str(out / "hand_expected.json"),
            "output_dir": str(out / "pln_rag"), "request_budget_path": str(budget),
            "evidence_ids_by_question": None,
            "controlled_evidence_pending": track == "shared_iterative"}
    plan = prepare_benchmark(root, container, job, env) if "pln_rag" in systems and pln_runtime == "docker" else None
    baseline_settings = {**settings.public(), "top_k": rag_top_k}
    manifest = {"schema_version": 2, "artifact_type": "benchmark_manifest",
                 "stage": "prepared_only" if prepare_only else "live_benchmark",
                 "dataset_kind": dataset_kind, "dataset_sha256": oracle["dataset_sha256"],
                 "comparison_track": track,
                 "track_definition": ("Native system architectures and documented defaults" if track == "native"
                                      else "Identical iterative top-4 evidence supplied per question" if track == "shared_iterative"
                                      else "Explicit custom system configuration"),
                 "evidence_policy": ("native_per_system" if track != "shared_iterative" else
                                     "iterative_rag selects four unique sentence IDs; every system receives only those IDs"),
                 "evidence_materialization": ("not_applicable" if track != "shared_iterative" else
                                              "runtime_after_iterative_selector; unresolved preparation jobs fail closed"),
                 "dataset_split": split,
                 "split_manifest_sha256": (file_sha256(dataset_dir / "splits" / f"{split.split(':', 1)[0]}.json")
                                            if split_metadata else None),
                "selected_world_ids": [w.id for w in worlds], "questions_per_system": 2 * limit,
                 "full_dataset_selected": limit == len(all_worlds), "systems": systems,
                 "system_order": systems, "llm_settings": llm.public(), "baseline_settings": baseline_settings,
                  "retrieval_limits": {
                      **{"rag": rag_top_k, "pln_rag": pln_top_k},
                      **({"iterative_rag": {"max_rounds": max_rounds,
                           "round_top_k": round_top_k, "max_distinct_evidence": max_evidence}}
                         if "iterative_rag" in systems else {}),
                  },
                "pln_runtime": pln_runtime, "docker_image": plan["image"] if plan else None,
                "service_urls": {"qdrant": env["B1_QDRANT_URL"], "ollama": env["OLLAMA_URL"]},
                "deadlines": {k: env[k] for k in env if k.startswith("B1_") and k.endswith("TIMEOUT")},
                "request_budget_scope": "One shared cap across all selected systems, including PLN ingestion",
                "source_sha256": {str(p.relative_to(root)): file_sha256(p) for p in sorted((root / "b1").glob("*.py"))},
                "normal_rag_source_sha256": {p.name: file_sha256(p) for p in sorted((normal_repo / "normal_rag").glob("*.py"))}}
    write_json(out / "manifest.json", manifest)
    print(f"{'Prepared' if prepare_only else 'Starting'} {2 * limit} questions × {len(systems)} systems; shared cap {llm.max_calls or 'unlimited'}.", flush=True)
    estimate = limit * (15 * ("pln_rag" in systems) + 2 * ("rag" in systems)
                        + 2 * ("iterative_rag" in systems) + 2 * ("full_context" in systems))
    print(f"Planning estimate: about {estimate} chat calls before extra PLN parsing calls; the cap is not raised automatically.", flush=True)
    print(f"Artifacts: {out}", flush=True)
    if prepare_only:
        return out

    answers = {a["question_id"]: a for a in oracle["answers"]}
    records, calls, learning, driver_errors = [], {}, [], []
    shared_evidence = {}
    execution_systems = (("iterative_rag",) + tuple(system for system in systems if system != "iterative_rag")
                         if track == "shared_iterative" else systems)
    for system in execution_systems:
        print(f"SYSTEM {system}", flush=True)
        calls[system] = []
        if system == "pln_rag":
            try:
                if track == "shared_iterative":
                    expected_questions = {question.id for world in worlds for question in world.questions}
                    if set(shared_evidence) != expected_questions:
                        raise RuntimeError("The iterative selector did not produce evidence for every question")
                    job.update(evidence_ids_by_question=shared_evidence, controlled_evidence_pending=False)
                    if plan:
                        write_json(out / "pln_job.json", job)
                if plan:
                    code = subprocess.run(plan["command"], env=env, check=False).returncode
                    if code:
                        driver_errors.append({"system": system, "kind": "docker_exit", "exit_code": code})
                else:
                    run_pln(root, repo, python, out / "worlds.json", out / "hand_expected.json", run_id, limit,
                            dataset_kind=dataset_kind, output_dir=out / system, request_budget_path=budget,
                            environment=env, selected_world_ids=[w.id for w in worlds],
                            evidence_ids_by_question=(shared_evidence if track == "shared_iterative" else None))
            except Exception as exc:
                driver_errors.append({"system": system, "kind": type(exc).__name__,
                                      "detail": redact(str(exc), secret_values(env))})
            def saved(name, default):
                path = out / system / name
                return json.loads(path.read_text()) if path.exists() else default
            pln_records = {r["question_id"]: r for r in saved("records.json", [])}
            learning = saved("learning.json", [])
            calls[system] = saved("llm_requests.json", [])
        fatal = None
        for world in worlds:
            prepared_index = (core.prepare_index(public_sentences(world), settings)
                              if system == "iterative_rag" or
                              (system == "rag" and track != "shared_iterative") else None)
            for question in world.questions:
                operation = out / system / world.id / question.id
                if system == "pln_rag":
                    record = pln_records.get(question.id) or skipped_record(system, "pln_not_run", "No PLN question record was produced; see driver_errors and PLN logs")
                elif fatal:
                    record = skipped_record(system, fatal, "No call made after a previous transport/API/budget failure in this system")
                else:
                    try:
                        supplied = public_sentences(world)
                        answer_mode = system
                        if track == "shared_iterative" and system != "iterative_rag":
                            by_id = {sentence["id"]: sentence for sentence in supplied}
                            supplied = [by_id[sentence_id] for sentence_id in shared_evidence[question.id]]
                            answer_mode = "full_context"
                        record = run_question(core, settings, llm, budget, supplied,
                                               question.text, answer_mode, operation,
                                               top_k=rag_top_k, prepared_index=prepared_index,
                                               max_rounds=max_rounds, round_top_k=round_top_k,
                                               max_evidence=max_evidence)
                    except Exception as exc:
                        detail = redact(str(exc), secret_values(env))
                        driver_errors.append({"system": system, "question_id": question.id, "kind": type(exc).__name__, "detail": detail})
                        record = skipped_record(system, "baseline_worker_error", detail)
                        record["attempted"] = True
                        fatal = "baseline_worker_error"
                    calls[system].extend(record["llm_http_calls"])
                    if record.get("error_kind") in ("request_budget_exceeded", "api_error", "network_error", "timeout", "embedding_api_error", "provider_pin_lost"):
                        fatal = record["error_kind"]
                if track == "shared_iterative" and system == "iterative_rag" and record.get("attempted", True):
                    selected_ids = [row["id"] for row in record.get("context", [])]
                    if not selected_ids:
                        record.update(label="ERROR", error_kind="empty_shared_evidence",
                                      error_detail="The iterative selector returned no evidence")
                    else:
                        shared_evidence[question.id] = selected_ids
                if track == "shared_iterative":
                    record["evidence_policy"] = "shared_iterative_top4"
                    record["evidence_access_ids"] = shared_evidence.get(question.id, [])
                    accessed = ({*record.get("used_sentence_ids", []),
                                 *record.get("retrieved_sentence_ids", [])} if system == "pln_rag" else
                                {row["id"] for row in record.get("context", [])} |
                                set(record.get("cited", [])))
                    if not accessed <= set(record["evidence_access_ids"]):
                        record.update(label="ERROR", error_kind="evidence_policy_violation",
                                      error_detail="The system accessed sentence IDs outside shared evidence")
                record = annotate(record, system, world, question, answers[question.id])
                write_json(operation / "record.json", record)
                records.append(record)
                write_json(out / "records.json", records)
                write_json(out / "llm_requests.json", calls)
        write_json(out / system / "comparison_records.json", [r for r in records if r["system"] == system])
    summary = build_summary(records, systems, worlds, calls, learning, budget, track=track, split=split)
    summary.update(driver_errors=driver_errors, full_dataset_selected=limit == len(all_worlds))
    if driver_errors:
        summary["status"] = "COMPLETE_WITH_ERRORS"
    write_json(out / "summary.json", summary)
    render_report(out, summary, records)
    print(f"Report: {out / 'report.md'}", flush=True)
    return out
