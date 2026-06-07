import json
from pathlib import Path

DATASET_PATH = Path(__file__).with_name("golden_dataset.jsonl")


def load_dataset(path: str | Path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def fake_retrieve(query: str):
    lowered = query.lower()

    if "fraude" in lowered or "banco" in lowered:
        return ["Súmula 479/STJ"]

    if "plano de saúde" in lowered or "rol da ans" in lowered:
        return ["Tema 1082/STJ"]

    if "tutela de urgência" in lowered:
        return ["art. 300 CPC"]

    return []


def recall_at_k(expected, retrieved):
    if not expected:
        return 1.0

    hits = sum(1 for item in expected if item in retrieved)
    return hits / len(expected)


def run(dataset_path: str | Path = DATASET_PATH):
    dataset = load_dataset(dataset_path)
    scores = []

    for item in dataset:
        retrieved = fake_retrieve(item["query"])
        score = recall_at_k(item["expected_sources"], retrieved)

        scores.append({
            "id": item["id"],
            "query": item["query"],
            "expected": item["expected_sources"],
            "retrieved": retrieved,
            "recall": score
        })

    average = sum(s["recall"] for s in scores) / len(scores)

    return {
        "dataset_size": len(dataset),
        "average_recall": average,
        "results": scores
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
