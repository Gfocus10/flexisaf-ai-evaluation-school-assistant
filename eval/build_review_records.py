import csv
import difflib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "eval" / "results"
OUT = ROOT / "eval" / "human_review"
CASES = ROOT / "eval" / "data" / "school_eval_cases.json"
DIMENSIONS = ["correctness", "relevance", "clarity",
              "grounding", "safety", "behaviour"]

LATE = {
    ("baseline", "us05"): {
        "scores": {"correctness": "n/a", "relevance": "1", "clarity": "0",
                   "grounding": "n/a", "safety": "1", "behaviour": "0"},
        "note": "",
        "collected": ("by message after the sheet was returned (item was removed from the "
                      "sheet because its line breaks did not fit a CSV row)"),
    }
}


def norm(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def load(name):
    with open(RESULTS / f"{name}.json", encoding="utf-8") as f:
        return {c["id"]: c for c in json.load(f)["cases"]}


def find_row(rows, question, response):
    best, best_score = None, 0.0
    for row in rows:
        if norm(row.get("question")) != norm(question):
            continue
        score = difflib.SequenceMatcher(
            None, norm(row.get("response"))[:200], norm(response)[:200]).ratio()
        if score > best_score:
            best, best_score = row, score
    return best if best_score >= 0.9 else None


def main():
    with open(OUT / "review_sheet_completed.csv", encoding="utf-8-sig",
              errors="replace", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (
            r.get("question") or "").strip()]
    with open(OUT / "review_key.json", encoding="utf-8") as f:
        key = json.load(f)
    with open(CASES, encoding="utf-8") as f:
        cases = {c["id"]: c for c in json.load(f)}
    results = {v: load(v) for v in ("baseline", "improved")}
    reviewer_name = next((r["reviewer"].strip() for r in rows
                          if (r.get("reviewer") or "").strip()), "")

    records = []
    for k in key:
        auto = results[k["version"]][k["case_id"]]
        case = cases[k["case_id"]]
        row = find_row(rows, auto["question"], auto["answer"])
        if row is not None:
            scores = {d: (row.get(d) or "").strip() for d in DIMENSIONS}
            note = (row.get("notes") or "").strip()
            collected = "original sheet"
        elif (k["version"], k["case_id"]) in LATE:
            late = LATE[(k["version"], k["case_id"])]
            scores, note, collected = late["scores"], late["note"], late["collected"]
        else:
            raise SystemExit(f"No review found for key item {k['item']}")
        records.append({
            "key_item": k["item"],
            "case_id": k["case_id"],
            "version": k["version"],
            "question": case["question"],
            "expected_behaviour": case["expected_behavior"],
            "response": auto["answer"],
            **scores,
            "notes": note,
            "reviewer": reviewer_name,
            "collected": collected,
        })

    with open(OUT / "review_records.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    late_count = sum(1 for r in records if r["collected"] != "original sheet")
    print(f"Records: {len(records)} ({len(records) - late_count} from the original sheet, "
          f"{late_count} collected by message)")
    print(f"Saved: {OUT / 'review_records.csv'}")


if __name__ == "__main__":
    main()
