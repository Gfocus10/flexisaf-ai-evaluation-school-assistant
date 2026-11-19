import csv
import difflib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "eval" / "results"
OUT = ROOT / "eval" / "human_review"
DIMENSIONS = ["correctness", "relevance", "clarity",
              "grounding", "safety", "behaviour"]


def norm(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def parse(value):
    value = (value or "").strip()
    return int(value) if value in ("0", "1") else None


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
    return (best, best_score) if best_score >= 0.9 else (None, best_score)


def main():
    with open(OUT / "review_sheet_completed.csv", encoding="utf-8-sig",
              errors="replace", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (
            r.get("question") or "").strip()]
    with open(OUT / "review_key.json", encoding="utf-8") as f:
        key = json.load(f)
    results = {v: load(v) for v in ("baseline", "improved")}
    reviewers = sorted({(r.get("reviewer") or "").strip()
                       for r in rows} - {""})

    items, missing = [], []
    compared = agreed = case_agreed = 0
    for k in key:
        auto = results[k["version"]][k["case_id"]]
        row, _ = find_row(rows, auto["question"], auto["answer"])
        if row is None:
            missing.append(k)
            continue
        diffs, human_vals = [], []
        for d in DIMENSIONS:
            if auto[d] == "":
                continue
            h = parse(row.get(d))
            if h is None:
                continue
            human_vals.append(h)
            compared += 1
            if h == auto[d]:
                agreed += 1
            else:
                diffs.append(f"{d} (automatic {auto[d]}, human {h})")
        applicable = sum(1 for d in DIMENSIONS if auto[d] != "")
        human_pass = int(len(human_vals) == applicable and all(
            v == 1 for v in human_vals))
        case_agreed += int(human_pass == auto["case_pass"])
        items.append({
            "key_item": k["item"], "reviewer_item": row.get("item", ""),
            "case": k["case_id"], "version": k["version"],
            "auto": "PASS" if auto["case_pass"] else "FAIL",
            "human": "PASS" if human_pass else "FAIL",
            "diffs": "; ".join(diffs) or "none",
            "note": (row.get("notes") or "").replace("|", "/").replace("\n", " ").strip(),
        })

    lines = ["# Human review summary", ""]
    lines.append(f"Reviewer: {', '.join(reviewers) or 'not recorded'}. "
                 f"Items scored: {len(items)} of {len(key)} in the sheet.")
    lines.append("")
    lines.append("The reviewer removed the first item of the sheet and renumbered the rest, so "
                 "reviewer item numbers are one lower than the key numbers. Rows were matched "
                 "to responses by question and response text, not by item number. Dimensions "
                 "that the automatic scoring marks as not applicable were ignored, even where "
                 "the reviewer entered a value.")
    lines.append("")
    lines.append("## Agreement")
    lines.append("")
    pct = round(100 * agreed / compared) if compared else 0
    lines.append(
        f"Dimension level: {agreed} of {compared} scores agree ({pct} percent).")
    lines.append(
        f"Case level (pass or fail): {case_agreed} of {len(items)} items agree.")
    lines.append("")
    lines.append("## Item by item")
    lines.append("")
    lines.append(
        "| Key item | Reviewer item | Case | Version | Automatic | Human | Dimension disagreements | Reviewer note |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for i in items:
        lines.append(f"| {i['key_item']} | {i['reviewer_item']} | {i['case']} | {i['version']} | "
                     f"{i['auto']} | {i['human']} | {i['diffs']} | {i['note']} |")
    lines.append("")
    lines.append("## Items not reviewed")
    lines.append("")
    if missing:
        for k in missing:
            lines.append(f"Key item {k['item']} ({k['version']} response for {k['case_id']}) "
                         f"has no matching row in the reviewer's file.")
    else:
        lines.append("None.")
    lines.append("")

    report = "\n".join(lines)
    (OUT / "agreement_report.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved: {OUT / 'agreement_report.md'}")


if __name__ == "__main__":
    main()
