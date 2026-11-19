# School AI Assistant Quality Review

A quality review of the grounded question answering assistant built in the RAG module. The assistant answers questions about Nigerian university documents (handbooks, examination regulations, hostel rules and JAMB manuals) and cites the source page. This repository tests it with 30 realistic cases, finds where it fails, improves one part of it, and reruns the same tests to compare before and after. A person reviewed a sample of the responses.

## Results at a glance

| Category | Cases | Baseline | Improved |
|---|---|---|---|
| normal questions | 10 | 9 | 9 |
| unclear or incomplete questions | 5 | 1 | 5 |
| questions needing source retrieval | 5 | 5 | 5 |
| unsafe or inappropriate requests | 5 | 0 | 5 |
| questions that should be refused with "not enough information" | 5 | 5 | 5 |
| total | 30 | 20 | 29 |

An earlier improved run passed 28 of 30 (the difference was case uc03), so the improved result is best read as 28 to 29 out of 30.

How to read these numbers:
1. The improvement was made after seeing failures on these same 30 cases, so the result is optimistic. It shows the change works on these cases, not that it will on new questions.
2. Each version was run once per label. Model output varies between runs.
3. The judge is a Gemini model scoring Gemini output, so it may favour its own style.
4. One person reviewed 10 responses. Pass or fail agreed with the automatic scoring on 10 of 10, and 40 of 46 individual dimension scores agreed (87 percent). That is a small sample.

## What was found and changed

The baseline was accurate on questions it could answer, but weak at knowing what kind of reply a message needs. It answered vague questions, harmful requests and a distressed student with the same "Not enough information" sentence or with exam study tips. The improvement is a new version of the system prompt with rules for vague questions, harmful requests and distressed users. One failure, a retrieval miss on a UNILORIN question (nm09), was not fixed and is in the backlog.

Details are in docs/failed_case_analysis.md, docs/version_notes.md and docs/improvement_backlog.md.

## Repository layout

```
README.md
.gitignore
app/                          the assistant under test
  src/                        rag.py, retrieve.py, llm.py and the index build scripts
  data/raw/                   the 10 source PDFs
  data/document_register.csv  source URLs, access dates and permission notes
  requirements.txt
  .env.example
eval/
  data/school_eval_cases.json the 30 test cases with expected answers or behaviours
  scoring_rubric.md           the six scoring dimensions and pass rules
  run_eval.py                 runs the cases, scores them, writes results
  compare_runs.py             builds the before and after table
  make_review_sheet.py        builds the human review sheet
  score_review.py             compares human scores with automatic scores
  build_review_records.py     combines all reviewed items into one file
  results/                    baseline, improved and earlier run results
  human_review/               review sheet, returned sheet, records and agreement report
docs/
  before_after_metrics.md
  failed_case_analysis.md
  version_notes.md
  improvement_backlog.md
```

## Setup (Windows, Git Bash, Python 3.13)

Run these from the repository root.

```
python -m venv .venv
source .venv/Scripts/activate
pip install -r app/requirements.txt
```

Copy app/.env.example to app/.env and fill in your own Gemini API key. Never commit .env, which is excluded by .gitignore.

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_FALLBACK_MODEL=gemini-3.6-flash
```

Check the connection:

```
python app/src/llm.py
```

Build the search index. The Chroma folder is not committed, so this step is needed once. The extracted page text and chunks are already committed in app/data, so the first two commands only regenerate them and can be skipped.

```
python app/src/extract_pages.py
python app/src/chunk_pages.py
python app/src/build_index.py
```

Expected: a Chroma collection named uni_docs_800_150 with 2,555 chunks.

Ask the assistant a question directly:

```
python app/src/rag.py "Can students cook in their hostel rooms at Nnamdi Azikiwe University?"
```

## Run the evaluation

```
python eval/run_eval.py --label my_run
```

It runs the 30 cases, It writes eval/results/my_run.csv and my_run.json. The JSON file also holds the retrieved passages and the judge's reasons. After the embedding model has been downloaded once, adding HF_HUB_OFFLINE=1 before the command avoids unnecessary network calls. Options: --k (retrieval top k, default 6), --pause (seconds between calls), and --ids (a comma separated list of case ids, merged into an existing result file with the same label).

To reproduce each version, check out its tag, run, and return to main:

```
git checkout v1-baseline
python eval/run_eval.py --label repro_v1
git checkout v2-final
python eval/run_eval.py --label repro_v2
git checkout main
```

Scores will not match the committed results exactly, because model output varies between runs. python eval/compare_runs.py reads the committed result files labelled baseline and improved. To compare your own runs, change those two names at the top of main() in that file.

## How responses are scored

Each response is scored 1 or 0 on correctness, relevance, clarity, grounding, safety and appropriate behaviour. A case passes only when every applicable dimension passes. Code checks the key facts, the cited pages and the refusal sentence. A Gemini judge scores the rest. The full rubric is in eval/scoring_rubric.md.

## Human review

A person reviewed responses without seeing the automatic scores or which version produced each one. The sheet had 10 items. The reviewer removed the first item (a baseline reply whose line breaks did not fit a CSV row) and renumbered the rest, so 9 items were scored in the sheet. The 10th was scored by message afterwards. Everything is combined in eval/human_review/review_records.csv, with a collected column that says which rows came from the sheet and which by message. The file as the reviewer returned it is kept unchanged as review_sheet_completed.csv. eval/human_review/agreement_report.md compares the human and automatic scores.



## Documents and permissions

The 10 public documents are listed with source URLs, access dates and permission notes in app/data/document_register.csv. No explicit reuse licence was found for them, so they are included only as sample documents for this assignment.

## Limitations

1. The improvement was measured on the same cases used to find the problems, so it is optimistic.
2. The judge is from the same model family as the assistant.
3. Human review covers 10 responses from one reviewer.
4. Over-refusal by the new rule for harmful requests was not tested.
5. The documents hold no fee schedules or admission deadlines, so those questions can only be refused.
6. The documents date from 2018 to 2026, and rules may have changed. Answers are not official guidance.

