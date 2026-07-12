from __future__ import annotations

import pandas as pd

import app


def country_corpus(country: str):
    data = app.load_all_data()
    frames = {}
    for key in ("master", "wdi", "projects", "policy_risk", "sector_summary", "cps_pdf"):
        frames[key] = data[key].loc[data[key]["Country_KR"] == country].copy()
    corpus = app.build_rag_corpus(
        frames["master"],
        frames["wdi"],
        frames["projects"],
        frames["policy_risk"],
        frames["sector_summary"],
        frames["cps_pdf"],
    )
    row = frames["master"].iloc[0]
    return corpus, row


def test_app_lexical_mode_preserves_evidence_pack() -> None:
    corpus, row = country_corpus("르완다")
    docs, status = app.retrieve_rag_evidence_with_mode(
        corpus, "르완다", "기술환경에너지", "디지털 공공서비스", row, "lexical", 12
    )
    assert status["effective_mode"] == "lexical"
    assert docs["Citation_ID"].str.fullmatch(r"E\d{2}").all()
    assert set(docs["Retrieval_Mode"]) == {"lexical"}


def test_app_embedding_error_falls_back_without_losing_docs(monkeypatch) -> None:
    corpus, row = country_corpus("르완다")

    class BrokenEngine:
        def search(self, *args, **kwargs):
            raise RuntimeError("offline")

    monkeypatch.setattr(app, "load_optional_retrieval_engine", lambda: BrokenEngine())
    docs, status = app.retrieve_rag_evidence_with_mode(
        corpus, "르완다", "기술환경에너지", "디지털 공공서비스", row, "embedding", 12
    )
    assert status["fallback"] is True
    assert status["effective_mode"] == "lexical"
    assert not docs.empty


def test_app_filtered_hybrid_can_rerank_cps(monkeypatch) -> None:
    corpus, row = country_corpus("르완다")
    chunk_id = corpus.loc[corpus["Source_Type"] == "CPS PDF", "Chunk_ID"].iloc[0]

    class FakeEngine:
        def search(self, *args, **kwargs):
            return ([{"chunk_id": chunk_id}], {"effective_mode": "hybrid_filtered", "fallback": False, "fallback_reason": ""})

    monkeypatch.setattr(app, "load_optional_retrieval_engine", lambda: FakeEngine())
    docs, status = app.retrieve_rag_evidence_with_mode(
        corpus, "르완다", "기술환경에너지", "디지털 공공서비스", row, "hybrid_filtered", 12
    )
    assert status["effective_mode"] == "hybrid_filtered"
    assert chunk_id in set(docs["Chunk_ID"].dropna())
    assert "hybrid_filtered" in set(docs["Retrieval_Mode"])
