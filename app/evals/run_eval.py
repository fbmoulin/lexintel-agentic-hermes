import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.services.vector_store import MockVectorStore

DATASET_PATH = Path(__file__).with_name("golden_dataset.jsonl")
CORPUS_PATH = Path(__file__).with_name("golden_corpus.jsonl")
DEFAULT_K = 3
# Search depth handed to the served retriever; recall@k slices this ordered list.
SEARCH_K = 10
DEFAULT_THRESHOLDS = {
    "min_dataset_size": 24,
    "min_average_recall_at_3": 0.85,
    "min_average_mrr": 0.85,
    # Per-area floor: a strong area must not mask a broken one behind the global
    # average. Each required area must clear this recall@3 on its own.
    "min_per_area_recall_at_3": 0.85,
    "required_areas": [
        "bancario",
        "consumidor",
        "processual_civil",
        "saude",
    ],
}
REQUIRED_FIELDS = {"id", "query", "expected_sources", "area"}


def load_dataset(path: str | Path):
    """
    Load and validate JSONL evaluation rows in file order.

    Each non-empty line of the file at `path` is parsed as JSON and validated; validated rows are returned in the same order they appear in the file.

    Parameters:
        path (str | Path): Path to a UTF-8 encoded JSONL file containing dataset rows.

    Returns:
        list[dict]: A list of validated dataset rows (one dict per JSONL line).

    Raises:
        ValueError: If a line contains malformed JSON (message includes line number)
                    or if a row fails schema/validation checks.
    """
    rows = []
    seen_ids: set[str] = set()

    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSONL row at line {line_number}: {exc.msg}"
            ) from exc

        validate_dataset_row(row, line_number, seen_ids)
        rows.append(row)

    return rows


def validate_dataset_row(row: dict, line_number: int, seen_ids: set[str]) -> None:
    """
    Validate a single dataset row for required schema and value constraints.

    Checks that the row is a mapping containing the required fields, that `id`,
    `query`, and `area` are non-empty strings, and that `expected_sources` is a
    non-empty list of strings. Detects duplicate `id` values using `seen_ids`.

    Parameters:
        row (dict): Parsed JSON object for a single dataset row.
        line_number (int): Line number in the source file used for error messages.
        seen_ids (set[str]): Set of previously seen `id` values; this set is mutated
            to include `row["id"]` on successful validation.

    Raises:
        ValueError: If `row` is not a dict; if any required fields are missing; if
            `id`, `query`, or `area` are empty or not strings; if `id` is a duplicate;
            if `expected_sources` is missing, empty, not a list, or contains
            non-string elements.
    """
    if not isinstance(row, dict):
        raise ValueError(f"Dataset row {line_number} must be a JSON object")

    missing_fields = REQUIRED_FIELDS - set(row)
    if missing_fields:
        raise ValueError(
            f"Dataset row {line_number} missing fields: {sorted(missing_fields)}"
        )

    for field_name in ("id", "query", "area"):
        if not isinstance(row[field_name], str) or not row[field_name].strip():
            raise ValueError(
                f"Dataset row {line_number} field {field_name} must be text"
            )

    if row["id"] in seen_ids:
        raise ValueError(f"Duplicate dataset id at line {line_number}: {row['id']}")

    if not isinstance(row["expected_sources"], list) or not row["expected_sources"]:
        raise ValueError(
            f"Dataset row {line_number} must define non-empty expected_sources"
        )

    if not all(isinstance(source, str) for source in row["expected_sources"]):
        raise ValueError(
            f"Dataset row {line_number} expected_sources must contain strings"
        )

    seen_ids.add(row["id"])


def _dedupe(items: list[str]) -> list[str]:
    """
    Produce a list of the input items with duplicates removed while preserving the original order.

    Parameters:
        items (list[str]): Sequence of items to deduplicate.

    Returns:
        list[str]: Items from `items` with duplicates removed, in their first-seen order.
    """
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped


def load_corpus(path: str | Path = CORPUS_PATH) -> list[dict]:
    """Load the seedable golden corpus (chunks) used to build the eval store."""
    chunks = []
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid corpus row at line {line_number}: {exc.msg}"
            ) from exc
        if not isinstance(row, dict):
            raise ValueError(f"Corpus row {line_number} must be a JSON object")
        chunks.append(row)
    return chunks


def build_eval_store(corpus: list[dict] | None = None) -> MockVectorStore:
    """Build an eval store on the same retrieval code path the API serves.

    Uses the same `MockVectorStore` class (and therefore the same `_tokenize`
    + scoring the `/rag/search` endpoint runs), but a *separate instance* seeded
    with the golden corpus — the eval needs known ground truth, so it cannot
    reuse the API singleton's `DEFAULT_MOCK_CHUNKS`. A regression in retrieval
    logic (tokenizer/scoring/ranking) is caught here; a regression purely in
    the API's singleton wiring/seed is covered by the API tests, not the eval.
    """
    return MockVectorStore(seed_chunks=corpus if corpus is not None else load_corpus())


def retrieve_sources(
    store: MockVectorStore, query: str, top_k: int = SEARCH_K
) -> list[str]:
    """Run the real retriever and map each retrieved chunk to its source identifier."""
    retrieved = []
    for result in store.search(query, top_k=top_k):
        metadata = result.get("metadata", {})
        source_ref = metadata.get("source_ref") or result.get("source")
        if source_ref:
            retrieved.append(source_ref)
    return _dedupe(retrieved)


def _smoke_retrieve(query: str) -> list[str]:
    """Harness smoke test ONLY — a hardcoded keyword map, NOT the served retriever.

    Kept for quick offline sanity of the metric helpers; it does not measure
    retrieval quality. The real eval path uses `retrieve_sources()` over the
    served `MockVectorStore`.
    """
    lowered = query.lower()
    retrieved = []
    if "fraude" in lowered or "banco" in lowered or "pix" in lowered:
        retrieved.extend(["Súmula 479/STJ", "CDC art. 14"])
    if "rol" in lowered or "ans" in lowered:
        retrieved.extend(["Tema 1082/STJ", "Lei 14.454/2022"])
    return _dedupe(retrieved)


def recall_at_k(expected, retrieved, k: int | None = None):
    """
    Compute recall of expected items within the top-k retrieved results.

    Parameters:
        expected (Iterable): Expected items (e.g., list of identifiers) to be found.
        retrieved (Iterable): Retrieved items ordered by rank.
        k (int | None): If provided, consider only the top `k` retrieved items; if `None`, consider all retrieved items.

    Returns:
        float: Fraction of `expected` items present among the considered retrieved items. Returns 1.0 when `expected` is empty.
    """
    if not expected:
        return 1.0

    candidates = retrieved[:k] if k is not None else retrieved
    hits = sum(1 for item in expected if item in candidates)
    return hits / len(expected)


def reciprocal_rank(expected, retrieved) -> float:
    """
    Compute the reciprocal rank of the first expected item that appears in the retrieved list.

    Parameters:
        expected (Iterable): Collection of expected item identifiers.
        retrieved (Sequence): Ranked sequence of retrieved item identifiers (first item is rank 1).

    Returns:
        float: `1 / rank` for the first retrieved item that is present in `expected`, or `0.0` if none match.
    """
    for rank, item in enumerate(retrieved, start=1):
        if item in expected:
            return 1 / rank
    return 0.0


def evaluate_item(item: dict, store: MockVectorStore) -> dict:
    """
    Evaluate a single dataset item by retrieving sources for its query and computing match diagnostics and metrics.

    Parameters:
        item (dict): A dataset row containing at least the keys:
            - "id" (str): Unique identifier for the item.
            - "query" (str): The text query to retrieve sources for.
            - "expected_sources" (list[str]): List of expected source identifiers.
            - "area" (str): The legal area/category for the item.

    Returns:
        dict: A dictionary with per-item results and diagnostics:
            - "id": item id.
            - "area": item area.
            - "query": original query string.
            - "expected": the expected_sources list from the item.
            - "retrieved": list of retrieved source identifiers for the query.
            - "matched_expected": expected sources present in the retrieved list.
            - "missed_expected": expected sources not present in the retrieved list.
            - "matched_expected_at_3": expected sources present within the top-DEFAULT_K retrieved.
            - "missed_expected_at_3": expected sources not present within the top-DEFAULT_K retrieved.
            - "recall": recall over the full retrieved list.
            - "recall_at_1": recall considering only the top-1 retrieved.
            - "recall_at_3": recall considering only the top-DEFAULT_K retrieved.
            - "mrr": mean reciprocal rank (reciprocal of the rank of the first retrieved expected source, or 0.0 if none).
    """
    retrieved = retrieve_sources(store, item["query"])
    expected = item["expected_sources"]
    retrieved_at_3 = retrieved[:DEFAULT_K]
    matched_expected = [source for source in expected if source in retrieved]
    missed_expected = [source for source in expected if source not in retrieved]
    matched_expected_at_3 = [source for source in expected if source in retrieved_at_3]
    missed_expected_at_3 = [
        source for source in expected if source not in retrieved_at_3
    ]

    return {
        "id": item["id"],
        "area": item["area"],
        "query": item["query"],
        "expected": expected,
        "retrieved": retrieved,
        "matched_expected": matched_expected,
        "missed_expected": missed_expected,
        "matched_expected_at_3": matched_expected_at_3,
        "missed_expected_at_3": missed_expected_at_3,
        "recall": recall_at_k(expected, retrieved),
        "recall_at_1": recall_at_k(expected, retrieved, 1),
        "recall_at_3": recall_at_k(expected, retrieved, DEFAULT_K),
        "mrr": reciprocal_rank(expected, retrieved),
    }


def average(values: list[float]) -> float:
    """
    Compute the arithmetic mean of the given list of numbers.

    Returns:
        The arithmetic mean of `values`, or 0.0 if `values` is empty.
    """
    return sum(values) / len(values) if values else 0.0


def summarize_by_area(scores: list[dict]) -> dict:
    """
    Aggregate per-area metrics from a list of per-item score dictionaries.

    Parameters:
        scores (list[dict]): List of score dictionaries (one per dataset item). Each score must include the keys
            "area", "recall_at_3", "mrr", "missed_expected_at_3", and "id".

    Returns:
        dict: Mapping from area name to a summary dictionary with keys:
            - "dataset_size" (int): Number of items in that area.
            - "average_recall_at_3" (float): Mean of `recall_at_3` across the area's items.
            - "average_mrr" (float): Mean of `mrr` across the area's items.
            - "failed_case_ids" (list[str]): List of item IDs that missed any expected source within the top-3.
    """
    summary: dict[str, dict[str, Any]] = {}
    for score in scores:
        area = score["area"]
        if area not in summary:
            summary[area] = {
                "dataset_size": 0,
                "average_recall_at_3": 0.0,
                "average_mrr": 0.0,
                "failed_case_ids": [],
            }
        area_scores = summary[area]
        area_scores["dataset_size"] += 1
        area_scores["average_recall_at_3"] += score["recall_at_3"]
        area_scores["average_mrr"] += score["mrr"]
        if score["missed_expected_at_3"]:
            area_scores["failed_case_ids"].append(score["id"])

    for area_scores in summary.values():
        size = area_scores["dataset_size"]
        area_scores["average_recall_at_3"] = area_scores["average_recall_at_3"] / size
        area_scores["average_mrr"] = area_scores["average_mrr"] / size

    return dict(sorted(summary.items()))


def evaluate_thresholds(scores: list[dict], thresholds: dict) -> list[dict]:
    """
    Evaluate scores against configured thresholds and return any threshold violations.

    Parameters:
        scores (list[dict]): Per-item evaluation dictionaries. Each dict must include at least the keys
            `"area"`, `"recall_at_3"`, and `"mrr"`.
        thresholds (dict): Threshold configuration with keys:
            - `min_dataset_size` (int): Minimum required number of scored items.
            - `required_areas` (iterable[str]): Areas that must be present in `scores`.
            - `min_average_recall_at_3` (float): Minimum required average recall@3.
            - `min_average_mrr` (float): Minimum required average MRR.

    Returns:
        list[dict]: A list of failure records. Each record describes a violated threshold and may take one of:
            - `{"metric": "dataset_size", "expected_minimum": int, "actual": int}`
            - `{"metric": "required_areas", "missing": list[str]}`
            - `{"metric": "average_recall_at_3", "expected_minimum": float, "actual": float}`
            - `{"metric": "average_mrr", "expected_minimum": float, "actual": float}`
    """
    failures = []
    areas = {score["area"] for score in scores}
    average_recall_at_3 = average([score["recall_at_3"] for score in scores])
    average_mrr = average([score["mrr"] for score in scores])

    if len(scores) < thresholds["min_dataset_size"]:
        failures.append(
            {
                "metric": "dataset_size",
                "expected_minimum": thresholds["min_dataset_size"],
                "actual": len(scores),
            }
        )

    missing_areas = sorted(set(thresholds["required_areas"]) - areas)
    if missing_areas:
        failures.append(
            {
                "metric": "required_areas",
                "missing": missing_areas,
            }
        )

    if average_recall_at_3 < thresholds["min_average_recall_at_3"]:
        failures.append(
            {
                "metric": "average_recall_at_3",
                "expected_minimum": thresholds["min_average_recall_at_3"],
                "actual": average_recall_at_3,
            }
        )

    if average_mrr < thresholds["min_average_mrr"]:
        failures.append(
            {
                "metric": "average_mrr",
                "expected_minimum": thresholds["min_average_mrr"],
                "actual": average_mrr,
            }
        )

    # Read fail-LOUD (KeyError) like every sibling gate above, not `.get`: a
    # partial thresholds dict must not silently disable this floor.
    per_area_floor = thresholds["min_per_area_recall_at_3"]
    if per_area_floor is not None:
        recall_by_area: dict[str, list[float]] = {}
        for score in scores:
            recall_by_area.setdefault(score["area"], []).append(score["recall_at_3"])
        for area in sorted(recall_by_area):
            area_recall_at_3 = average(recall_by_area[area])
            if area_recall_at_3 < per_area_floor:
                failures.append(
                    {
                        "metric": "per_area_recall_at_3",
                        "area": area,
                        "expected_minimum": per_area_floor,
                        "actual": area_recall_at_3,
                    }
                )

    return failures


def run(
    dataset_path: str | Path = DATASET_PATH,
    thresholds: dict | None = None,
    corpus: list[dict] | None = None,
):
    """
    Run the evaluation pipeline for the deterministic mock retriever against a golden dataset.

    Loads and validates the dataset, scores each item using the deterministic retriever and scoring helpers, evaluates configured thresholds, and aggregates overall and per-area metrics.

    Parameters:
        dataset_path (str | Path): Path to the JSONL golden dataset to load and evaluate.
        thresholds (dict | None): Optional overrides for evaluation thresholds (merged onto defaults).

    Returns:
        result (dict): A dictionary containing:
            - dataset_size: number of evaluated items
            - areas: sorted list of areas present in the dataset
            - average_recall: average recall@3
            - average_recall_at_1: average recall@1
            - average_recall_at_3: average recall@3 (same as `average_recall`)
            - average_mrr: mean reciprocal rank across items
            - thresholds: the thresholds used for evaluation
            - passed: `True` if no threshold failures were found, `False` otherwise
            - threshold_failures: list of threshold failure records
            - area_summary: per-area aggregated metrics and failed case ids
            - results: list of per-item score dictionaries
    """
    active_thresholds = deepcopy(DEFAULT_THRESHOLDS)
    if thresholds:
        active_thresholds.update(deepcopy(thresholds))
    dataset = load_dataset(dataset_path)
    store = build_eval_store(corpus)
    scores = [evaluate_item(item, store) for item in dataset]
    threshold_failures = evaluate_thresholds(scores, active_thresholds)
    average_recall_at_3 = average([score["recall_at_3"] for score in scores])
    average_mrr = average([score["mrr"] for score in scores])

    result = {
        "dataset_size": len(dataset),
        "areas": sorted({score["area"] for score in scores}),
        "average_recall": average_recall_at_3,
        "average_recall_at_1": average([score["recall_at_1"] for score in scores]),
        "average_recall_at_3": average_recall_at_3,
        "average_mrr": average_mrr,
        "thresholds": active_thresholds,
        "passed": not threshold_failures,
        "threshold_failures": threshold_failures,
        "area_summary": summarize_by_area(scores),
        "results": scores,
    }

    return result


if __name__ == "__main__":
    evaluation_result = run()
    print(json.dumps(evaluation_result, ensure_ascii=False, indent=2))
    if not evaluation_result["passed"]:
        raise SystemExit(1)
