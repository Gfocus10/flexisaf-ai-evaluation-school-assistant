# Improvement backlog

Items are ranked by risk to students, then by how much they would improve confidence in the results, then by effort. Each item says how to check it worked.

## Priority 1

| # | Item | Why | Evidence | Effort | How to verify |
|---|---|---|---|---|---|
| 1 | Fix the retrieval miss on fee and oral examination style questions | The system answers a real policy question with the wrong rule | nm09 failed in the baseline and the improved run: page 17 of the UNILORIN handbook was not used | Medium | First rank page 17 for the question at larger k. If it appears, try a larger k or a keyword search combined with the vector search. Then rerun nm09 and the retrieval cases |
| 2 | Add school provided support information to the distress reply | The current reply is caring but generic, and the assistant cannot name a real service without the school giving one | us05 improved reply | Low, once the school supplies the contact details | Add the details to the prompt or documents, then test several distress phrasings, not one |
| 3 | Test for over-refusal | The new harmful request rule might block genuine questions, for example how exam malpractice is punished | Not tested in the 30 cases | Low | Add 5 to 10 legitimate questions that mention cheating, bribery or similar words, and require correct cited answers |
| 4 | Use a fresh test set to measure the improvement | The prompt was improved after seeing failures on the same 30 cases, so 29 of 30 is optimistic | All results | Medium | Write about 20 new cases of the same five types without looking at the prompt, and run both versions on them |

## Priority 2

| # | Item | Why | Evidence | Effort | How to verify |
|---|---|---|---|---|---|
| 5 | Build clarifying question options from all universities, not only the retrieved passages | The uc03 reply listed three universities and left out BUK | uc03, which flipped between runs | Medium | Rerun uc03 several times and check that every relevant university is offered |
| 6 | Reword the refusal replies for students | "I can answer questions about the rules in the sources" means little to a student | us01 to us04 improved replies | Low | Reviewer reads the new wording and scores clarity |
| 7 | Split the safety dimension in the rubric into avoiding harm and showing care | The reviewer and the judge read safety differently on the baseline us05 reply | Human review, late item | Low | Rescore the review items and check agreement rises |
| 8 | Strengthen the judge | The judge was more lenient than the reviewer on relevance and clarity when a response missed the point | Three dimension disagreements in the human review | Medium | Try a stronger or different judge model, or two judges, and compare agreement on more human scored items |
| 9 | Add the documents that students actually ask about | The documents hold no fee amounts or admission deadlines, so questions about them can only be refused | The five no_answer cases, and uc02 and uc04 | High | Add the official fee schedules and calendars, then add answerable test cases for them |

## Priority 3

| # | Item | Why | Evidence | Effort | How to verify |
|---|---|---|---|---|---|
| 10 | Repeat each run several times and report the spread | Results come from a single run per version, and uc03 changed between runs | improved_run1_tag_leak against improved | Low | Run the evaluation three times and report the lowest, highest and average |
| 11 | Increase the number of human reviewed responses and reviewers | Nine items from one reviewer is a small sample | docs of the human review | Medium | Two reviewers score at least 20 items, and agreement is reported between reviewers as well as with the automatic scores |
| 12 | Run the evaluation automatically on every change | Evaluation should run on every change, not occasionally | Best practices page from OpenAI | Medium | Add a script or CI step that fails when the pass rate drops below the last accepted result |
| 13 | Record latency and cost per case | The task reviewed quality only | Not measured | Low | Add timing and call counts to the results file |