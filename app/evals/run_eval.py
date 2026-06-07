import json
from pathlib import Path

DATASET_PATH = Path(__file__).with_name("golden_dataset.jsonl")


def load_dataset(path: str | Path):
    """
    Load a JSON Lines (JSONL) file and return the parsed JSON objects.
    
    Empty lines and lines that fail JSON parsing are skipped silently.
    
    Parameters:
        path (str | Path): Filesystem path to the JSONL file to read.
    
    Returns:
        list: A list of parsed JSON objects (Python dicts/lists/values) in file order.
    """
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def fake_retrieve(query: str):
    """
    Map a user query to a deterministic list of predefined legal source identifiers based on keyword matching.
    
    Parameters:
        query (str): The input query (typically in Portuguese) used to determine relevant source identifiers.
    
    Returns:
        list[str]: A list of matched source identifier strings (e.g., "Súmula 479/STJ", "Tema 1082/STJ", "art. 300 CPC"); an empty list if no predefined keywords match.
    """
    lowered = query.lower()

    if "fraude" in lowered or "banco" in lowered:
        return ["Súmula 479/STJ"]

    if "plano de saúde" in lowered or "rol da ans" in lowered:
        return ["Tema 1082/STJ"]

    if "tutela de urgência" in lowered:
        return ["art. 300 CPC"]

    return []


def recall_at_k(expected, retrieved):
    """
    Compute the fraction of expected items that appear in the retrieved results.
    
    Parameters:
        expected (Iterable): Collection of expected source identifiers.
        retrieved (Iterable): Collection of retrieved source identifiers to compare against `expected`.
    
    Returns:
        float: Proportion of items in `expected` that are present in `retrieved` (value between 0.0 and 1.0). Returns 1.0 when `expected` is empty.
    """
    if not expected:
        return 1.0

    hits = sum(1 for item in expected if item in retrieved)
    return hits / len(expected)


def run(dataset_path: str | Path = DATASET_PATH):
    """
    Evaluate deterministic retrieval over a JSONL dataset and return aggregated recall results.
    
    Parameters:
        dataset_path (str | Path): Path to a JSON Lines file containing dataset items. Each row must be a JSON object with at least the keys `"id"`, `"query"`, and `"expected_sources"`.
    
    Returns:
        dict: Aggregated evaluation containing:
            - `dataset_size` (int): Number of parsed dataset rows.
            - `average_recall` (float): Mean recall across all items (0.0 if dataset is empty).
            - `results` (list[dict]): Per-item records with keys:
                - `id`: item identifier from the dataset.
                - `query`: the original query string.
                - `expected` (list): expected source identifiers from the dataset.
                - `retrieved` (list): sources returned by the retrieval stub.
                - `recall` (float): recall score for the item (hits / len(expected), or 1.0 when `expected` is empty).
    """
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

    average = sum(s["recall"] for s in scores) / len(scores) if scores else 0.0

    return {
        "dataset_size": len(dataset),
        "average_recall": average,
        "results": scores
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
