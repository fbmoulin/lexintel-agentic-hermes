from copy import deepcopy


def reciprocal_rank_fusion(rankings: list[list[dict]], k: int = 60) -> list[dict]:
    """Fuse N ranked RetrievedContext lists by Reciprocal Rank Fusion.

    Fused score of a chunk = sum over rankings of 1/(k + rank) (rank 1-indexed).
    Rank-based, so it is scale-independent across dense/sparse/lexical scorers.
    Deterministic; ties broken by chunk_id. Each fused item records
    metadata.fusion_detail = [{ranker, rank, contribution}, ...] as an audit trail.
    """
    fused_score: dict[str, float] = {}
    detail: dict[str, list[dict]] = {}
    representative: dict[str, dict] = {}

    for ranker_index, ranking in enumerate(rankings):
        for rank, ctx in enumerate(ranking, start=1):
            chunk_id = ctx["chunk_id"]
            contribution = 1.0 / (k + rank)
            fused_score[chunk_id] = fused_score.get(chunk_id, 0.0) + contribution
            detail.setdefault(chunk_id, []).append(
                {
                    "ranker": ranker_index,
                    "rank": rank,
                    "contribution": round(contribution, 6),
                }
            )
            if chunk_id not in representative:
                representative[chunk_id] = deepcopy(ctx)

    ordered = sorted(fused_score, key=lambda cid: (-fused_score[cid], cid))
    results = []
    for chunk_id in ordered:
        ctx = representative[chunk_id]
        ctx["score"] = round(fused_score[chunk_id], 6)
        ctx["metadata"] = {**ctx.get("metadata", {}), "fusion_detail": detail[chunk_id]}
        results.append(ctx)
    return results
