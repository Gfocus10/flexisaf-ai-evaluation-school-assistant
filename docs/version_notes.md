# Version notes

The application under test is the grounded question answering assistant in app/. Three states of it were evaluated. Each one is a git tag, so the exact code and prompt can be recovered with git checkout.

## Versions

| Version | Prompt name | Prompt fingerprint | Git tag | What changed |
|---|---|---|---|---|
| 1 baseline | prompt v1 | 86e00f58 | v1-baseline (commit 48f88c5) | Starting point, copied unchanged from the RAG module |
| 2 | prompt v2 | 36e04db8 | v2-prompt (commit 7a45874) | Prompt rules 8 to 11 added, rule 3 amended, citation retry skips replies tagged [DIRECT] |
| 2 final | prompt v2 | 36e04db8 | v2-final (commit f2a4dea) | Fix: the [DIRECT] tag is also removed after a citation retry |

Versions 2 and 2 final use the same prompt text. They differ only in the tag handling code.

The prompt fingerprint is the first 8 characters of a SHA-1 hash of the prompt text, computed by eval/run_eval.py and stored in every result file. It changes whenever the prompt text changes, so it shows which exact prompt produced a result. It covers the prompt only, which is why versions 2 and 2 final share one value even though the code differs. The git tags identify the code.

## Settings that did not change between versions

1. Generator model: gemini-3.5-flash-lite, with gemini-3.6-flash as the fallback after repeated temporary errors. Temperature 0.0.
2. Embeddings: all-MiniLM-L6-v2, run locally, stored in a Chroma collection (uni_docs_800_150).
3. Retrieval: chunks of up to 800 characters with 150 characters of overlap, top k of 6, and a filter that restricts search to a university's files when the question names it.
4. Documents: the 10 public PDFs in app/data/raw (ABU, BUK, UNILORIN, UNIZIK, UDUS, NOUN and two JAMB manuals).
5. Judge: gemini-3.5-flash-lite, the same model family as the generator. The scoring rubric is in eval/scoring_rubric.md.

Retrieval settings and the model were not changed in this round. Only the prompt and the response handling were changed.

## Prompt changes

Version 1 had seven rules: answer only from the sources, cite source tags, reply with "Not enough information in the provided sources." when the sources do not hold the answer, correct false assumptions, answer per university when none is named, report conflicting sources, and keep answers short.

Version 2 changes:
1. Rule 3 now lists rules 4, 8, 9 and 10 as exceptions to the refusal sentence.
2. Rule 8: ask one short clarifying question when the topic is too vague to tell what is being asked. If the topic is clear but no university is named, rule 5 still applies.
3. Rule 9: when asked for help with cheating, forging documents, bribery or private personal information, do not use the sources and say it cannot help.
4. Rule 10: when the user seems distressed, do not use the sources or give study tips, reply with a short caring message that points to someone they trust, a university counsellor and local emergency services.
5. Rule 11: replies under rules 8 to 10 start with [DIRECT] and cite no sources.

The full text of each prompt is in app/src/rag.py at the matching tag.

Code changes in app/src/rag.py:
1. v2-prompt: a reply that starts with [DIRECT] has the tag removed, is not treated as uncited, and does not trigger the citation retry.
2. v2-final: the tag is also removed from the reply produced after a citation retry. Before this, two answers in the first improved run showed the tag.

## Evaluation runs

| Run label | Code version | Date | Passed | Files |
|---|---|---|---|---|
| baseline | v1-baseline | 2026-11-16 to 2026-11-17 | 20 of 30 | eval/results/baseline.csv and .json |
| improved_run1_tag_leak | v2-prompt | 2026-11-18 16:08 | 28 of 30 | eval/results/improved_run1_tag_leak.csv and .json |
| improved | v2-final | 2026-11-18 21:11 | 29 of 30 | eval/results/improved.csv and .json |

The baseline results combine several runs, because network failures forced partial reruns. Most cases come from the first full run (2026-11-16 20:06). Cases nm01, uc05 and rt01 were rerun at 21:06 on the same day. Case us04 comes from the run at 18:21 on 2026-11-17, and cases nm03, nm09, us01, us02 and us03 from the run at 18:49 the same day. The raw first run, which has three network errors, is kept as baseline_first_run_network_errors.csv and .json. The tests for nm03, nm09 and the harmful request cases were corrected after the first baseline results were seen. The corrections are described in docs/failed_case_analysis.md.

The two improved runs differ only on uc03. Results should be read as a range of 28 to 29 out of 30, and each version was run once per label, so run to run variation is not measured beyond this one comparison.

## How to run an evaluation

HF_HUB_OFFLINE=1 python eval/run_eval.py --label <name>

The label names the output files. Setting HF_HUB_OFFLINE=1 stops the embedding model from contacting the internet. A run takes about 5 to 6 minutes because the script pauses 4 seconds between API calls.