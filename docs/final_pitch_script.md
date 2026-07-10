# Final Pitch Script

## 15-second opening

ODA public data is open, but turning it into a country-sector project plan still requires expert interpretation. K-ODA Compass RAG converts diplomatic CPS documents, KOICA project evidence, WDI indicators, and risk proxies into explainable ODA recommendations and citation-backed proposal drafts.

## 90-second demo

1. Open `개요`: show the problem and public-data pipeline.
2. Open `순위`: show Top50 country opportunity scores.
3. Open `AI Builder`: choose `CSO 탄자니아 공공행정`.
4. Click `RAG형 AI 사업기획서 생성`.
5. Open `근거 Citation`: show CPS PDF, KOICA, WDI, policy/risk evidence IDs.
6. Open `원문`: show `CPS 정책 정합성 근거` and citation-backed proposal.
7. Open `AI검증`: show RAG document count, score reproducibility, sensitivity analysis.
8. Open `심사모드`: show why it fits judging criteria.
9. Open `배포`: show GitHub/Streamlit QR plan.

## Closing

This is not just a dashboard and not just a chatbot. It is an evidence-grounded AI workflow that makes diplomatic public data actionable for CSOs, local governments, companies, and policy teams.

## Expected Q&A

**Q. Is this really AI?**  
Yes. It uses retrieval-augmented generation over CPS PDF chunks, KOICA project records, WDI indicators, and policy/risk proxy rows. If an OpenAI key is configured, the same Evidence Pack is sent to the LLM; without a key, the local RAG generator still works.

**Q. How do you prevent hallucination?**  
The system retrieves a fixed Evidence Pack first and inserts citation IDs such as `[E01]` into generated text. The app also exposes the citation table and AI validation tab.

**Q. Why is this useful?**  
It reduces the gap between raw public data and actual ODA planning outputs: country selection, sector rationale, policy alignment, risks, KPIs, and exportable briefs.
