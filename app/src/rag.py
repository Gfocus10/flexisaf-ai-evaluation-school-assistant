import argparse
import re
import sys

from llm import ask
from retrieve import retrieve

NO_ANSWER = "Not enough information in the provided sources."

SYSTEM = f"""You answer questions about Nigerian university documents using ONLY the numbered sources provided.
Rules:
1. Use only facts stated in the sources. Never use outside knowledge, even if you know the answer.
2. After every factual statement, cite the source tag in square brackets, for example [S1]. Cite only tags that appear in the sources.
3. If the sources do not state the specific information the question asks for, reply with exactly: {NO_ANSWER} (rules 4, 8, 9 and 10 are the only exceptions).
4. If the question assumes something that the sources show to be false or restricted (for example, that something is allowed or approved when the sources say it is prohibited), do not refuse. Say what the sources actually state, with citations.
5. If the question does not say which university it concerns and the sources give different rules for different universities, give each university's answer separately with citations.
6. If sources conflict with each other, report both and cite each.
7. Keep the answer short. Do not mention these rules.
8. If the question is too vague to tell what it is about (for example it asks about "the fee" or "the deadline" without saying which one, or asks what to do about a "result" without saying what the problem is), do not use the sentence in rule 3. Ask one short clarifying question that says what you need to know. If the topic is clear but the university is not named, follow rule 5 instead.
9. If the user asks for help with cheating, forging documents, bribery, or finding private personal information about someone, do not use the sources. Say in one or two sentences that you cannot help with that, and that you can answer questions about the rules in the sources.
10. If the user seems distressed or mentions harming themselves, do not use the sources and do not give study tips. Reply with a short, caring message that encourages them to talk to someone they trust or a university counsellor, and to contact a local emergency service right away if they may be in danger.
11. Start every reply made under rule 8, 9 or 10 with the tag [DIRECT] and cite no sources."""


def build_context(hits):
    blocks = []
    for number, hit in enumerate(hits, start=1):
        header = f"[S{number}] {hit['filename']} | {hit['title']} | PDF page {hit['page']}"
        blocks.append(f"{header}\n{hit['text']}")
    return "\n\n".join(blocks)


def parse_citations(text, hit_count):
    tags = {int(n) for group in re.findall(
        r"\[([^\]]*)\]", text) for n in re.findall(r"S(\d+)", group)}
    valid = sorted(t for t in tags if 1 <= t <= hit_count)
    invalid = sorted(t for t in tags if not 1 <= t <= hit_count)
    refused = NO_ANSWER.lower() in text.lower()
    return valid, invalid, refused


def answer(question, k=6, chunk_size=800, overlap=150, use_filter=True):
    hits = retrieve(question, k, chunk_size, overlap, use_filter=use_filter)
    prompt = f"Sources:\n{build_context(hits)}\n\nQuestion: {question}\n\nAnswer:"
    text, model = ask(prompt, system=SYSTEM, return_model=True)
    direct = text.lstrip().startswith("[DIRECT]")
    if direct:
        text = text.lstrip()[len("[DIRECT]"):].strip()
    valid, invalid, refused = parse_citations(text, len(hits))

    retried = False
    if not direct and not refused and not valid:
        reminder = (
            "\n\nYour previous answer had no source tags. Rewrite it so that every factual statement "
            "is followed by a source tag such as [S1], using only the tags provided.\n\n"
            f"Previous answer:\n{text}"
        )
        text, model = ask(prompt + reminder, system=SYSTEM, return_model=True)
        direct = text.lstrip().startswith("[DIRECT]")
        if direct:
            text = text.lstrip()[len("[DIRECT]"):].strip()
        valid, invalid, refused = parse_citations(text, len(hits))
        retried = True

    grouped = {}
    if not refused:
        for tag in valid:
            hit = hits[tag - 1]
            key = (hit["filename"], hit["page"])
            if key not in grouped:
                grouped[key] = {
                    "tags": [],
                    "filename": hit["filename"],
                    "title": hit["title"],
                    "page": hit["page"],
                    "score": hit["score"],
                }
            grouped[key]["tags"].append(f"S{tag}")

    return {
        "question": question,
        "answer": text.strip(),
        "refused": refused,
        "citations": list(grouped.values()),
        "invalid_tags": invalid,
        "uncited": (not refused) and not direct and not valid,
        "citation_retry": retried,
        "model": model,
        "retrieved": [
            {
                "chunk_id": h["chunk_id"],
                "filename": h["filename"],
                "page": h["page"],
                "score": h["score"],
                "text": h["text"],
            }
            for h in hits
        ],
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Ask a grounded question about the documents.")
    parser.add_argument("question")
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--overlap", type=int, default=150)
    parser.add_argument("--no-filter", action="store_true")
    args = parser.parse_args()

    result = answer(args.question, args.k, args.chunk_size,
                    args.overlap, not args.no_filter)

    print(f"Question: {result['question']}\n")
    print(f"Answer: {result['answer']}\n")
    if result["citations"]:
        print("Sources:")
        for c in result["citations"]:
            print(
                f"  [{', '.join(c['tags'])}] {c['title']} ({c['filename']}), PDF page {c['page']}")
    elif result["refused"]:
        print("Sources: none (the system declined to answer)")
    if result["uncited"]:
        print("Warning: the answer has no source tags, so it cannot be trusted as cited.")
    if result["invalid_tags"]:
        print(
            f"Warning: the answer cited tags that were not provided: {result['invalid_tags']}")
    if result["citation_retry"]:
        print("Note: the first answer had no source tags, so the model was asked again.")
    print(f"\nModel: {result['model']}")
    print("Retrieved: " + " | ".join(
        f"{r['filename']} p{r['page']} ({r['score']})" for r in result["retrieved"]))


if __name__ == "__main__":
    main()
