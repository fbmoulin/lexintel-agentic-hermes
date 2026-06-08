import json
from pathlib import Path

DATASET_PATH = Path(__file__).with_name("golden_dataset.jsonl")
DEFAULT_K = 3
DEFAULT_THRESHOLDS = {
    "min_dataset_size": 8,
    "min_average_recall_at_3": 0.85,
    "min_average_mrr": 0.85,
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

    Raises ValueError when a row is malformed so CI fails before metrics are
    computed from an invalid golden dataset.
    """
    rows = []
    seen_ids = set()

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
    if not isinstance(row, dict):
        raise ValueError(f"Dataset row {line_number} must be a JSON object")

    missing_fields = REQUIRED_FIELDS - set(row)
    if missing_fields:
        raise ValueError(
            f"Dataset row {line_number} missing fields: "
            f"{sorted(missing_fields)}"
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

    for field_name in ("id", "query", "area"):
        if not isinstance(row[field_name], str) or not row[field_name].strip():
            raise ValueError(
                f"Dataset row {line_number} field {field_name} must be text"
            )

    seen_ids.add(row["id"])


def _dedupe(items: list[str]) -> list[str]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped


def fake_retrieve(query: str):
    """
    Map a user query to a deterministic list of predefined legal source identifiers based on keyword matching.
    """
    lowered = query.lower()
    retrieved = []

    if "fraude" in lowered or "banco" in lowered or "pix" in lowered:
        retrieved.extend(["Súmula 479/STJ", "CDC art. 14"])

    if "plano de saúde" in lowered or "rol da ans" in lowered:
        retrieved.extend(["Tema 1082/STJ", "Lei 14.454/2022", "Lei 9.656/1998"])

    if "reajuste" in lowered and "idoso" in lowered:
        retrieved.extend(["Estatuto do Idoso", "CDC", "Lei 9.656/1998"])

    if "negativação" in lowered or "inscrição indevida" in lowered:
        retrieved.extend(["CDC", "jurisprudência STJ sobre inscrição indevida"])

    if "vício" in lowered or "produto defeituoso" in lowered:
        retrieved.extend(["CDC art. 18", "CDC"])

    if "tutela de urgência" in lowered:
        retrieved.extend(["art. 300 CPC", "tutela provisória"])

    if "agravo" in lowered and "tutela" in lowered:
        retrieved.extend(["art. 1.015 CPC", "tutela provisória"])

    return _dedupe(retrieved)


def recall_at_k(expected, retrieved, k: int | None = None):
    """
    Compute the fraction of expected items found within the top-k results.
    """
    if not expected:
        return 1.0

    candidates = retrieved[:k] if k is not None else retrieved
    hits = sum(1 for item in expected if item in candidates)
    return hits / len(expected)


def reciprocal_rank(expected, retrieved) -> float:
    for rank, item in enumerate(retrieved, start=1):
        if item in expected:
            return 1 / rank
    return 0.0


def evaluate_item(item: dict) -> dict:
    retrieved = fake_retrieve(item["query"])
    expected = item["expected_sources"]
    retrieved_at_3 = retrieved[:DEFAULT_K]
    matched_expected = [source for source in expected if source in retrieved]
    missed_expected = [source for source in expected if source not in retrieved]
    matched_expected_at_3 = [
        source for source in expected
        if source in retrieved_at_3
    ]
    missed_expected_at_3 = [
        source for source in expected
        if source not in retrieved_at_3
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
    return sum(values) / len(values) if values else 0.0


def summarize_by_area(scores: list[dict]) -> dict:
    summary = {}
    for score in scores:
        area_scores = summary.setdefault(
            score["area"],
            {
                "dataset_size": 0,
                "average_recall_at_3": 0.0,
                "average_mrr": 0.0,
                "failed_case_ids": [],
            },
        )
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
    failures = []
    areas = {score["area"] for score in scores}
    average_recall_at_3 = average([score["recall_at_3"] for score in scores])
    average_mrr = average([score["mrr"] for score in scores])

    if len(scores) < thresholds["min_dataset_size"]:
        failures.append({
            "metric": "dataset_size",
            "expected_minimum": thresholds["min_dataset_size"],
            "actual": len(scores),
        })

    missing_areas = sorted(set(thresholds["required_areas"]) - areas)
    if missing_areas:
        failures.append({
            "metric": "required_areas",
            "missing": missing_areas,
        })

    if average_recall_at_3 < thresholds["min_average_recall_at_3"]:
        failures.append({
            "metric": "average_recall_at_3",
            "expected_minimum": thresholds["min_average_recall_at_3"],
            "actual": average_recall_at_3,
        })

    if average_mrr < thresholds["min_average_mrr"]:
        failures.append({
            "metric": "average_mrr",
            "expected_minimum": thresholds["min_average_mrr"],
            "actual": average_mrr,
        })

    return failures


def run(dataset_path: str | Path = DATASET_PATH, thresholds: dict | None = None):
    """
    Evaluate deterministic mock retrieval over the golden dataset.
    """
    active_thresholds = thresholds or DEFAULT_THRESHOLDS
    dataset = load_dataset(dataset_path)
    scores = [evaluate_item(item) for item in dataset]
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
