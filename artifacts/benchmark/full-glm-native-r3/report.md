# Shared rule-chain-depth results

Track: **native**; split: **all**

Status: **COMPLETE**

20 worlds; 40 questions per selected system.

Accuracy includes errors and unattempted questions in its denominator. COMPLETE describes execution, not perfect accuracy.

| System | Correct / total | Errors | Not attempted | Accuracy |
|---|---:|---:|---:|---:|
| pln_rag | 40 / 40 | 0 | 0 | 100.0% |
| rag | 31 / 40 | 0 | 0 | 77.5% |
| iterative_rag | 33 / 40 | 0 | 0 | 82.5% |
| full_context | 39 / 40 | 0 | 0 | 97.5% |

## Accuracy by depth

| System | Depth | Correct / total | Errors |
|---|---:|---:|---:|
| pln_rag | 0 | 10 / 10 | 0 |
| pln_rag | 1 | 10 / 10 | 0 |
| pln_rag | 2 | 10 / 10 | 0 |
| pln_rag | 3 | 10 / 10 | 0 |
| rag | 0 | 10 / 10 | 0 |
| rag | 1 | 10 / 10 | 0 |
| rag | 2 | 6 / 10 | 0 |
| rag | 3 | 5 / 10 | 0 |
| iterative_rag | 0 | 10 / 10 | 0 |
| iterative_rag | 1 | 9 / 10 | 0 |
| iterative_rag | 2 | 8 / 10 | 0 |
| iterative_rag | 3 | 6 / 10 | 0 |
| full_context | 0 | 10 / 10 | 0 |
| full_context | 1 | 10 / 10 | 0 |
| full_context | 2 | 10 / 10 | 0 |
| full_context | 3 | 9 / 10 | 0 |

## Supported accuracy by proof size

| System | Proof sentences | Correct / total | Accuracy |
|---|---:|---:|---:|
| pln_rag | 1 | 5 / 5 | 100.0% |
| pln_rag | 2 | 3 / 3 | 100.0% |
| pln_rag | 3 | 4 / 4 | 100.0% |
| pln_rag | 4 | 5 / 5 | 100.0% |
| pln_rag | 5 | 2 / 2 | 100.0% |
| pln_rag | 6 | 1 / 1 | 100.0% |
| rag | 1 | 5 / 5 | 100.0% |
| rag | 2 | 3 / 3 | 100.0% |
| rag | 3 | 2 / 4 | 50.0% |
| rag | 4 | 1 / 5 | 20.0% |
| rag | 5 | 0 / 2 | 0.0% |
| rag | 6 | 0 / 1 | 0.0% |
| iterative_rag | 1 | 5 / 5 | 100.0% |
| iterative_rag | 2 | 3 / 3 | 100.0% |
| iterative_rag | 3 | 3 / 4 | 75.0% |
| iterative_rag | 4 | 3 / 5 | 60.0% |
| iterative_rag | 5 | 0 / 2 | 0.0% |
| iterative_rag | 6 | 0 / 1 | 0.0% |
| full_context | 1 | 5 / 5 | 100.0% |
| full_context | 2 | 3 / 3 | 100.0% |
| full_context | 3 | 4 / 4 | 100.0% |
| full_context | 4 | 5 / 5 | 100.0% |
| full_context | 5 | 2 / 2 | 100.0% |
| full_context | 6 | 1 / 1 | 100.0% |

## Paired comparisons

Intervals resample whole worlds and retain each world's supported/control pair.

| System A | System B | Difference | A-only | B-only | World-clustered 95% interval |
|---|---|---:|---:|---:|---:|
| pln_rag | rag | 22.5% | 9 | 0 | [12.5%, 32.5%] |
| pln_rag | iterative_rag | 17.5% | 7 | 0 | [7.5%, 27.5%] |
| pln_rag | full_context | 2.5% | 1 | 0 | [0.0%, 7.5%] |
| rag | iterative_rag | -5.0% | 2 | 4 | [-15.0%, 5.0%] |
| rag | full_context | -20.0% | 1 | 9 | [-30.0%, -10.0%] |
| iterative_rag | full_context | -15.0% | 1 | 7 | [-25.0%, -5.0%] |

Unsupported questions are grouped by their supported pair's depth; their actual proof depth is null.

See [summary.json](summary.json) for per-kind scores, providers, tokens, and timing; [records.json](records.json) for every result.

Top-four retrieval cannot contain a supplied proof needing more than four sentences. Coverage records disclose this limit.

## Per-question records

| System | Question | Label | Expected | Record |
|---|---|---|---|---|
| pln_rag | bench-01-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-01/bench-01-supported/record.json) |
| pln_rag | bench-01-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-01/bench-01-control/record.json) |
| pln_rag | bench-02-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-02/bench-02-supported/record.json) |
| pln_rag | bench-02-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-02/bench-02-control/record.json) |
| pln_rag | bench-03-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-03/bench-03-supported/record.json) |
| pln_rag | bench-03-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-03/bench-03-control/record.json) |
| pln_rag | bench-04-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-04/bench-04-supported/record.json) |
| pln_rag | bench-04-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-04/bench-04-control/record.json) |
| pln_rag | bench-05-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-05/bench-05-supported/record.json) |
| pln_rag | bench-05-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-05/bench-05-control/record.json) |
| pln_rag | bench-06-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-06/bench-06-supported/record.json) |
| pln_rag | bench-06-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-06/bench-06-control/record.json) |
| pln_rag | bench-07-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-07/bench-07-supported/record.json) |
| pln_rag | bench-07-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-07/bench-07-control/record.json) |
| pln_rag | bench-08-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-08/bench-08-supported/record.json) |
| pln_rag | bench-08-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-08/bench-08-control/record.json) |
| pln_rag | bench-09-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-09/bench-09-supported/record.json) |
| pln_rag | bench-09-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-09/bench-09-control/record.json) |
| pln_rag | bench-10-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-10/bench-10-supported/record.json) |
| pln_rag | bench-10-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-10/bench-10-control/record.json) |
| pln_rag | bench-11-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-11/bench-11-supported/record.json) |
| pln_rag | bench-11-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-11/bench-11-control/record.json) |
| pln_rag | bench-12-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-12/bench-12-supported/record.json) |
| pln_rag | bench-12-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-12/bench-12-control/record.json) |
| pln_rag | bench-13-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-13/bench-13-supported/record.json) |
| pln_rag | bench-13-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-13/bench-13-control/record.json) |
| pln_rag | bench-14-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-14/bench-14-supported/record.json) |
| pln_rag | bench-14-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-14/bench-14-control/record.json) |
| pln_rag | bench-15-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-15/bench-15-supported/record.json) |
| pln_rag | bench-15-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-15/bench-15-control/record.json) |
| pln_rag | bench-16-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-16/bench-16-supported/record.json) |
| pln_rag | bench-16-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-16/bench-16-control/record.json) |
| pln_rag | bench-17-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-17/bench-17-supported/record.json) |
| pln_rag | bench-17-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-17/bench-17-control/record.json) |
| pln_rag | bench-18-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-18/bench-18-supported/record.json) |
| pln_rag | bench-18-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-18/bench-18-control/record.json) |
| pln_rag | bench-19-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-19/bench-19-supported/record.json) |
| pln_rag | bench-19-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-19/bench-19-control/record.json) |
| pln_rag | bench-20-supported | SUPPORTED | SUPPORTED | [record](pln_rag/bench-20/bench-20-supported/record.json) |
| pln_rag | bench-20-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](pln_rag/bench-20/bench-20-control/record.json) |
| rag | bench-01-supported | SUPPORTED | SUPPORTED | [record](rag/bench-01/bench-01-supported/record.json) |
| rag | bench-01-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-01/bench-01-control/record.json) |
| rag | bench-02-supported | SUPPORTED | SUPPORTED | [record](rag/bench-02/bench-02-supported/record.json) |
| rag | bench-02-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-02/bench-02-control/record.json) |
| rag | bench-03-supported | NOT_ESTABLISHED | SUPPORTED | [record](rag/bench-03/bench-03-supported/record.json) |
| rag | bench-03-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-03/bench-03-control/record.json) |
| rag | bench-04-supported | NOT_ESTABLISHED | SUPPORTED | [record](rag/bench-04/bench-04-supported/record.json) |
| rag | bench-04-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-04/bench-04-control/record.json) |
| rag | bench-05-supported | SUPPORTED | SUPPORTED | [record](rag/bench-05/bench-05-supported/record.json) |
| rag | bench-05-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-05/bench-05-control/record.json) |
| rag | bench-06-supported | SUPPORTED | SUPPORTED | [record](rag/bench-06/bench-06-supported/record.json) |
| rag | bench-06-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-06/bench-06-control/record.json) |
| rag | bench-07-supported | NOT_ESTABLISHED | SUPPORTED | [record](rag/bench-07/bench-07-supported/record.json) |
| rag | bench-07-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-07/bench-07-control/record.json) |
| rag | bench-08-supported | NOT_ESTABLISHED | SUPPORTED | [record](rag/bench-08/bench-08-supported/record.json) |
| rag | bench-08-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-08/bench-08-control/record.json) |
| rag | bench-09-supported | SUPPORTED | SUPPORTED | [record](rag/bench-09/bench-09-supported/record.json) |
| rag | bench-09-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-09/bench-09-control/record.json) |
| rag | bench-10-supported | SUPPORTED | SUPPORTED | [record](rag/bench-10/bench-10-supported/record.json) |
| rag | bench-10-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-10/bench-10-control/record.json) |
| rag | bench-11-supported | NOT_ESTABLISHED | SUPPORTED | [record](rag/bench-11/bench-11-supported/record.json) |
| rag | bench-11-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-11/bench-11-control/record.json) |
| rag | bench-12-supported | NOT_ESTABLISHED | SUPPORTED | [record](rag/bench-12/bench-12-supported/record.json) |
| rag | bench-12-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-12/bench-12-control/record.json) |
| rag | bench-13-supported | SUPPORTED | SUPPORTED | [record](rag/bench-13/bench-13-supported/record.json) |
| rag | bench-13-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-13/bench-13-control/record.json) |
| rag | bench-14-supported | SUPPORTED | SUPPORTED | [record](rag/bench-14/bench-14-supported/record.json) |
| rag | bench-14-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-14/bench-14-control/record.json) |
| rag | bench-15-supported | NOT_ESTABLISHED | SUPPORTED | [record](rag/bench-15/bench-15-supported/record.json) |
| rag | bench-15-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-15/bench-15-control/record.json) |
| rag | bench-16-supported | NOT_ESTABLISHED | SUPPORTED | [record](rag/bench-16/bench-16-supported/record.json) |
| rag | bench-16-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-16/bench-16-control/record.json) |
| rag | bench-17-supported | SUPPORTED | SUPPORTED | [record](rag/bench-17/bench-17-supported/record.json) |
| rag | bench-17-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-17/bench-17-control/record.json) |
| rag | bench-18-supported | SUPPORTED | SUPPORTED | [record](rag/bench-18/bench-18-supported/record.json) |
| rag | bench-18-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-18/bench-18-control/record.json) |
| rag | bench-19-supported | SUPPORTED | SUPPORTED | [record](rag/bench-19/bench-19-supported/record.json) |
| rag | bench-19-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-19/bench-19-control/record.json) |
| rag | bench-20-supported | NOT_ESTABLISHED | SUPPORTED | [record](rag/bench-20/bench-20-supported/record.json) |
| rag | bench-20-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](rag/bench-20/bench-20-control/record.json) |
| iterative_rag | bench-01-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-01/bench-01-supported/record.json) |
| iterative_rag | bench-01-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-01/bench-01-control/record.json) |
| iterative_rag | bench-02-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-02/bench-02-supported/record.json) |
| iterative_rag | bench-02-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-02/bench-02-control/record.json) |
| iterative_rag | bench-03-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-03/bench-03-supported/record.json) |
| iterative_rag | bench-03-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-03/bench-03-control/record.json) |
| iterative_rag | bench-04-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-04/bench-04-supported/record.json) |
| iterative_rag | bench-04-control | SUPPORTED | NOT_ESTABLISHED | [record](iterative_rag/bench-04/bench-04-control/record.json) |
| iterative_rag | bench-05-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-05/bench-05-supported/record.json) |
| iterative_rag | bench-05-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-05/bench-05-control/record.json) |
| iterative_rag | bench-06-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-06/bench-06-supported/record.json) |
| iterative_rag | bench-06-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-06/bench-06-control/record.json) |
| iterative_rag | bench-07-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-07/bench-07-supported/record.json) |
| iterative_rag | bench-07-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-07/bench-07-control/record.json) |
| iterative_rag | bench-08-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-08/bench-08-supported/record.json) |
| iterative_rag | bench-08-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-08/bench-08-control/record.json) |
| iterative_rag | bench-09-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-09/bench-09-supported/record.json) |
| iterative_rag | bench-09-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-09/bench-09-control/record.json) |
| iterative_rag | bench-10-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-10/bench-10-supported/record.json) |
| iterative_rag | bench-10-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-10/bench-10-control/record.json) |
| iterative_rag | bench-11-supported | NOT_ESTABLISHED | SUPPORTED | [record](iterative_rag/bench-11/bench-11-supported/record.json) |
| iterative_rag | bench-11-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-11/bench-11-control/record.json) |
| iterative_rag | bench-12-supported | NOT_ESTABLISHED | SUPPORTED | [record](iterative_rag/bench-12/bench-12-supported/record.json) |
| iterative_rag | bench-12-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-12/bench-12-control/record.json) |
| iterative_rag | bench-13-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-13/bench-13-supported/record.json) |
| iterative_rag | bench-13-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-13/bench-13-control/record.json) |
| iterative_rag | bench-14-supported | NOT_ESTABLISHED | SUPPORTED | [record](iterative_rag/bench-14/bench-14-supported/record.json) |
| iterative_rag | bench-14-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-14/bench-14-control/record.json) |
| iterative_rag | bench-15-supported | NOT_ESTABLISHED | SUPPORTED | [record](iterative_rag/bench-15/bench-15-supported/record.json) |
| iterative_rag | bench-15-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-15/bench-15-control/record.json) |
| iterative_rag | bench-16-supported | NOT_ESTABLISHED | SUPPORTED | [record](iterative_rag/bench-16/bench-16-supported/record.json) |
| iterative_rag | bench-16-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-16/bench-16-control/record.json) |
| iterative_rag | bench-17-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-17/bench-17-supported/record.json) |
| iterative_rag | bench-17-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-17/bench-17-control/record.json) |
| iterative_rag | bench-18-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-18/bench-18-supported/record.json) |
| iterative_rag | bench-18-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-18/bench-18-control/record.json) |
| iterative_rag | bench-19-supported | SUPPORTED | SUPPORTED | [record](iterative_rag/bench-19/bench-19-supported/record.json) |
| iterative_rag | bench-19-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-19/bench-19-control/record.json) |
| iterative_rag | bench-20-supported | NOT_ESTABLISHED | SUPPORTED | [record](iterative_rag/bench-20/bench-20-supported/record.json) |
| iterative_rag | bench-20-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](iterative_rag/bench-20/bench-20-control/record.json) |
| full_context | bench-01-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-01/bench-01-supported/record.json) |
| full_context | bench-01-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-01/bench-01-control/record.json) |
| full_context | bench-02-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-02/bench-02-supported/record.json) |
| full_context | bench-02-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-02/bench-02-control/record.json) |
| full_context | bench-03-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-03/bench-03-supported/record.json) |
| full_context | bench-03-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-03/bench-03-control/record.json) |
| full_context | bench-04-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-04/bench-04-supported/record.json) |
| full_context | bench-04-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-04/bench-04-control/record.json) |
| full_context | bench-05-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-05/bench-05-supported/record.json) |
| full_context | bench-05-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-05/bench-05-control/record.json) |
| full_context | bench-06-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-06/bench-06-supported/record.json) |
| full_context | bench-06-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-06/bench-06-control/record.json) |
| full_context | bench-07-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-07/bench-07-supported/record.json) |
| full_context | bench-07-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-07/bench-07-control/record.json) |
| full_context | bench-08-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-08/bench-08-supported/record.json) |
| full_context | bench-08-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-08/bench-08-control/record.json) |
| full_context | bench-09-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-09/bench-09-supported/record.json) |
| full_context | bench-09-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-09/bench-09-control/record.json) |
| full_context | bench-10-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-10/bench-10-supported/record.json) |
| full_context | bench-10-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-10/bench-10-control/record.json) |
| full_context | bench-11-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-11/bench-11-supported/record.json) |
| full_context | bench-11-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-11/bench-11-control/record.json) |
| full_context | bench-12-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-12/bench-12-supported/record.json) |
| full_context | bench-12-control | SUPPORTED | NOT_ESTABLISHED | [record](full_context/bench-12/bench-12-control/record.json) |
| full_context | bench-13-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-13/bench-13-supported/record.json) |
| full_context | bench-13-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-13/bench-13-control/record.json) |
| full_context | bench-14-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-14/bench-14-supported/record.json) |
| full_context | bench-14-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-14/bench-14-control/record.json) |
| full_context | bench-15-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-15/bench-15-supported/record.json) |
| full_context | bench-15-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-15/bench-15-control/record.json) |
| full_context | bench-16-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-16/bench-16-supported/record.json) |
| full_context | bench-16-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-16/bench-16-control/record.json) |
| full_context | bench-17-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-17/bench-17-supported/record.json) |
| full_context | bench-17-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-17/bench-17-control/record.json) |
| full_context | bench-18-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-18/bench-18-supported/record.json) |
| full_context | bench-18-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-18/bench-18-control/record.json) |
| full_context | bench-19-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-19/bench-19-supported/record.json) |
| full_context | bench-19-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-19/bench-19-control/record.json) |
| full_context | bench-20-supported | SUPPORTED | SUPPORTED | [record](full_context/bench-20/bench-20-supported/record.json) |
| full_context | bench-20-control | NOT_ESTABLISHED | NOT_ESTABLISHED | [record](full_context/bench-20/bench-20-control/record.json) |

PLN-RAG's `pln_rag/raw.md` shows learned atoms and proofs when its runner started. Baseline operation folders contain exact requests, response bytes, raw model text, and the retrieved/shown sentences in each record.
