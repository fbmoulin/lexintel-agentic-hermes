from app.services.fusion import reciprocal_rank_fusion


def _ctx(chunk_id):
    return {"chunk_id": chunk_id, "score": 0.0, "text": chunk_id, "metadata": {}}


def test_fuses_two_rankings_by_reciprocal_rank():
    a = [_ctx("x"), _ctx("y"), _ctx("z")]  # ranks 1,2,3
    b = [_ctx("y"), _ctx("x")]  # ranks 1,2
    fused = reciprocal_rank_fusion([a, b], k=60)
    # y: 1/62 + 1/61 ; x: 1/61 + 1/62  -> equal score, tie-break by chunk_id -> x before y
    assert [c["chunk_id"] for c in fused[:2]] == ["x", "y"]


def test_records_fusion_detail_per_ranker():
    a = [_ctx("x")]
    b = [_ctx("x")]
    fused = reciprocal_rank_fusion([a, b], k=60)
    detail = fused[0]["metadata"]["fusion_detail"]
    assert len(detail) == 2
    assert {d["ranker"] for d in detail} == {0, 1}
    assert all(d["rank"] == 1 for d in detail)


def test_chunk_in_single_ranking_still_ranked():
    a = [_ctx("x"), _ctx("only_a")]
    b = [_ctx("x")]
    fused = reciprocal_rank_fusion([a, b], k=60)
    ids = [c["chunk_id"] for c in fused]
    assert set(ids) == {"x", "only_a"}
    assert ids[0] == "x"  # x appears in both -> higher fused score


def test_empty_rankings_return_empty():
    assert reciprocal_rank_fusion([[], []], k=60) == []


def test_does_not_mutate_input_rankings_and_rounds_score():
    src = {"chunk_id": "x", "score": 0.0, "text": "x", "metadata": {"keep": 1}}
    fused = reciprocal_rank_fusion([[src]], k=60)
    # Output score is the fused value rounded to 6 places...
    assert fused[0]["score"] == round(1.0 / 61, 6)
    assert fused[0]["metadata"]["fusion_detail"][0]["ranker"] == 0
    # ...and the caller's input dict is untouched (deepcopy isolation).
    assert src["score"] == 0.0
    assert "fusion_detail" not in src["metadata"]
    assert src["metadata"] == {"keep": 1}
