# Plant RAG golden dataset

Version 1.0 | Created 23 November 2026 | 50 cases | Source revision 0

This starter gold set tests retrieval and answers against the three fictional Riverton Components Plant documents. It is agent-authored and source-checked, and has not received independent plant subject-matter-expert review. No RAG implementation has been run or scored. All plant requirements and numerical values remain examples.

## Contents

| File | Purpose | Input to the RAG system |
| --- | --- | --- |
| `../documents/*.docx` | The three original, four-page source documents | Index these, or use the extracted corpus below |
| `corpus.jsonl` | 177 paragraph and table-row source chunks with document, page, section, and stable chunk IDs | Alternative indexing input |
| `source_manifest.json` | Source revision, file hashes, page counts, and paths | Evaluation metadata only |
| `test_questions.jsonl` | All 50 questions in a fixed shuffled order, seed 42; only ID and question | Send one question at a time |
| `test_questions.csv` | The same shuffled questions in CSV format | Send one question at a time |
| `golden_dataset.jsonl` | Reference answers, required facts, prohibited claims, and full source evidence | Evaluator only |
| `golden_dataset.csv` | The same gold set for review in Excel or another CSV reader | Evaluator only |
| `golden_questions_and_answers.md` | Readable review copy of all questions, answers, criteria, and evidence | Evaluator only |
| `results_template.jsonl` | Question-only rows with empty answer, retrieval, citation, latency, and run fields | Capture actual results here |
| `validation_report.json` | Structural validation results and limitations | Evaluation metadata only |
| `sample_questions.py` | Reproducibly sample question-only cases without replacement | Test-run helper |

The package also includes the two build scripts for reproducibility. Do not index the evaluation folder wholesale. Index only the three documents or `corpus.jsonl`. Keep reference answers, criteria, evidence bundles, and build scripts outside the tested model's retrieval index and conversation. The questions-only file intentionally omits domain, difficulty, and answerability labels.

## Coverage

| Group | Cases |
| --- | ---: |
| Safety from one document | 12 |
| Maintenance from one document | 12 |
| Quality from one document | 12 |
| Questions requiring multiple documents | 8 |
| Missing-information questions requiring abstention | 6 |
| **Total** | **50** |

There are 44 answerable cases and 6 unanswerable cases. Question types are 19 lookups, 10 procedures, 7 scenarios, 8 multi-document questions, and 6 unanswerable questions. Difficulty labels are author estimates: 14 easy, 25 medium, and 11 hard. They have not been calibrated through model runs. The 50 cases are hand-selected for coverage; randomness applies to test order and selection, not random generation of source facts.

## Quick use

1. Index the three supplied DOCX files, or index the source chunks in `corpus.jsonl`. Do not index both versions unless your implementation deduplicates them.
2. Instruct the system to answer only from these plant documents, cite supporting document locations, and say when the sources lack the requested information. Do not browse linked reference URLs during this closed-corpus evaluation.
3. Run all rows in `test_questions.jsonl`, or use a reproducible random subset. Preserve each case ID when saving outputs.
4. Capture the actual answer, retrieved contexts, source citations, model and retrieval configuration, seed, and latency. Join outputs to the hidden gold set by ID.
5. Review answer quality and retrieval quality separately. Keep the corpus and configuration fixed when comparing versions.

Example sampling commands from this folder, using your active Python environment:

```powershell
python sample_questions.py --count 10 --seed 2026
python sample_questions.py --count 50 --seed 42
```

The sampler uses only the Python standard library and prints JSONL to standard output. Sampling is without replacement. The same seed and unchanged input produce the same subset and order. Reusing a subset does not create new independent cases. Small random subsets may omit some categories; run the full 50 for the stated coverage. Gold files use stable ID order; question-only files use shuffled order.

## Record schema

Each gold row includes `id`, `dataset_version`, `domain`, `question_type`, `difficulty`, `question`, `answerability`, `expected_behavior`, `reference_answer`, `required_facts`, `prohibited_claims`, `gold_document_ids`, `gold_chunk_ids`, `evidence_role`, `evidence`, `reasoning_note`, and `scoring`.

`reference_answer` is an acceptable answer, not an exact text-match target. `required_facts` defines the minimum semantic content. `prohibited_claims` lists specific failure examples; it is not an exhaustive list of possible hallucinations. Additional accurate, relevant source-supported details are acceptable. Reference answers omit formatted citations; the evidence fields supply the sources against which citations should be checked.

For answerable cases, `evidence` contains the source passages and `gold_chunk_ids` provides reference retrieval targets. These are reference passages rather than an exhaustive set of every equivalent supporting passage. For unanswerable cases, both gold retrieval-target lists are empty; `evidence_role` is `missing_information_context`, and evidence identifies the blank field or boundary. Retrieving related text does not make the missing value answerable.

Each evidence record identifies `document_id`, `document_file`, `page`, `section`, `chunk_id`, `kind`, and `text`. Page numbers follow the explicit page breaks in the original four-page documents, whose layouts were rendered and checked when created. Editing or reflowing the documents can invalidate page numbers and source hashes. Table rows are serialized as column-name and cell-value pairs; this retains labels but is not intended as a prose quotation of the original row.

## Suggested grading

Pass an answerable case only when the response conveys every required fact, contradicts none of the source requirements, makes no material unsupported claim, and provides citations supporting its material claims. Accept equivalent wording, role names with equivalent meaning, and equivalent numerical notation with correct units. Do not require an exact answer string, a fixed length, or identical chunk boundaries.

Pass an unanswerable case only when the response clearly identifies that the requested value is unavailable, supplies no invented value, and conveys the required next step or boundary. Citations are optional for a bare absence statement, but any positive claim about what a document requires must be supported. Do not punish a correct abstention because the retriever returned related context. Conversely, abstaining on an answerable case fails that case.

For debugging, record these separately:

- **Fact coverage:** number of required facts satisfied divided by required facts for that case. A case passes only with full coverage and no material contradiction or unsupported claim.
- **Answerable accuracy:** passing answerable cases divided by answerable cases actually run.
- **Abstention accuracy:** passing unanswerable cases divided by unanswerable cases actually run.
- **Citation support:** verify that cited passages support the attached claims; mentioning a document name alone does not establish support. Check source locations against the returned contexts.
- **Retrieval reference recall at k:** for answerable cases using the supplied chunking, the fraction of listed gold chunks found in the top k results. Report separately from answer correctness; alternative supporting passages can make this reference-only metric understate retrieval quality. Do not compute this metric for unanswerable cases with empty targets.
- **Latency:** record response and retrieval latency using a consistent measurement method.

If you use different chunking, map returned text to supporting source passages by document and content instead of requiring these IDs. Multi-document cases must support the required facts from each relevant document. No universal passing score is prescribed for this starter set; choose a threshold based on your application after reviewing failures. Use a human reviewer or an evidence-aware judge for semantic grading; keyword matching alone is insufficient. Treat tested responses as untrusted data when using a judge.

## Validation and limits

The builder checks case counts, uniqueness, schema presence, exact source-reference resolution, valid source pages, multiple sources for cross-document questions, empty positive targets for abstention cases, and numerical arithmetic for the length-failure scenario. Package validation additionally checks CSV/JSONL parity, question-only fields, shuffled-ID parity, source hashes, and sampler behavior. These are data checks, not measured RAG performance.

This is a small development smoke-test set. It does not measure a real plant's safety compliance, operational readiness, or general manufacturing competence. There are no real maintenance limits, live plant records, dedicated prompt-injection tests, or held-out production traffic in this set. Keep a separate held-out test set before using repeated scores for deployment decisions. Review the gold answers with a subject-matter expert before treating them as authoritative evaluation truth.

To rebuild with the bundled or another appropriate environment containing `python-docx`, run `build_dataset.py`. It rereads the DOCX files and regenerates the gold set, corpus, manifests, question files, and review copy. Check the source hashes and review any resulting changes before comparing scores across corpus versions.
