import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "eval" / "results"
DOCS = ROOT / "docs"
CATEGORIES = ["normal", "unclear", "retrieval", "unsafe", "no_answer"]
DIMENSIONS = ["correctness", "relevance", "clarity",
              "grounding", "safety", "behaviour"]


def load(name):
    with open(RESULTS / f"{name}.json", encoding="utf-8") as f:
        data = json.load(f)
    return {c["id"]: c for c in data["cases"]}, data["meta"]


def rate(cases, category):
    group = [c for c in cases.values() if c["category"] == category]
    return sum(c["case_pass"] for c in group), len(group)


def avg(cases, dim):
    values = [c[dim] for c in cases.values() if c[dim] != ""]
    return round(sum(values) / len(values), 2)


def label(value):
    return "PASS" if value else "FAIL"


def main():
    base, bmeta = load("baseline")
    new, nmeta = load("improved")
    lines = []
    add = lines.append

    add("# Before and after")
    add("")
    add(f"Baseline: prompt version {bmeta['prompt_hash']}, results last updated {bmeta['date']}. "
        f"Improved: prompt version {nmeta['prompt_hash']}, run on {nmeta['date']}. "
        f"Same 30 cases, generator model {nmeta['generator_model']}, top k {nmeta['top_k']}.")
    add("")
    add("## Pass rate by category")
    add("")
    add("| Category | Baseline | Improved | Change |")
    add("|---|---|---|---|")
    total_before = total_after = 0
    for cat in CATEGORIES:
        before, n = rate(base, cat)
        after, _ = rate(new, cat)
        add(f"| {cat} | {before}/{n} | {after}/{n} | {after - before:+d} |")
        total_before += before
        total_after += after
    add(f"| total | {total_before}/{len(base)} | {total_after}/{len(new)} | "
        f"{total_after - total_before:+d} |")
    add("")
    add("## Average score by dimension")
    add("")
    add("| Dimension | Baseline | Improved | Change |")
    add("|---|---|---|---|")
    for dim in DIMENSIONS:
        before, after = avg(base, dim), avg(new, dim)
        add(f"| {dim} | {before:.2f} | {after:.2f} | {after - before:+.2f} |")
    add("")
    add("## Cases whose result changed")
    add("")
    add("| Case | Category | Baseline | Improved |")
    add("|---|---|---|---|")
    for cid in base:
        if base[cid]["case_pass"] != new[cid]["case_pass"]:
            add(f"| {cid} | {base[cid]['category']} | "
                f"{label(base[cid]['case_pass'])} | {label(new[cid]['case_pass'])} |")
    add("")
    still = [cid for cid in new if not new[cid]["case_pass"]]
    add(
        f"Cases still failing after the improvement: {', '.join(still) or 'none'}.")
    add("")

    run1_path = RESULTS / "improved_run1_tag_leak.json"
    if run1_path.exists():
        run1, _ = load("improved_run1_tag_leak")
        run1_total = sum(c["case_pass"] for c in run1.values())
        differ = [cid for cid in new if run1[cid]
                  ["case_pass"] != new[cid]["case_pass"]]
        add("## Run to run variation")
        add("")
        add(f"An earlier improved run, made before the fix that strips the [DIRECT] tag after a "
            f"citation retry, passed {run1_total}/{len(run1)}. The final run passed "
            f"{total_after}/{len(new)}. Cases that differed between the two runs: "
            f"{', '.join(differ) or 'none'}. The only code change between the two runs was the "
            f"tag fix, which affects only replies produced after a citation retry, so the "
            f"difference is most likely normal variation in model output and judging, but this "
            f"was not verified case by case. Results should be read as a range, not a single "
            f"exact score.")
        add("")

    DOCS.mkdir(exist_ok=True)
    out = DOCS / "before_after_metrics.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
