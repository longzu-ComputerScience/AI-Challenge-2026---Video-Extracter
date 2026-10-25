# AI Challenge 2026 — video retrieval workspace

**Portfolio:** [GitHub](https://github.com/longzu-ComputerScience) · [LinkedIn](https://www.linkedin.com/in/vuz-long-7b4744393/)

This workspace contains official preliminary query text, Colab notebooks for CLIP/FAISS retrieval, keyframe/video review helpers, and submission validation for AIC 2026.

## Current snapshot

- **Problem:** Given a natural-language query or question, locate the correct video and precise moment within a large multimedia dataset. The competition includes Known-Item Search (KIS), Question Answering (QA), and temporal event retrieval (TRAKE).
- **P1 baseline:** 25 queries (20 KIS, 4 QA, 1 TRAKE). A CLIP/FAISS-based candidate retrieval workflow produced ranked search results. Crucially, retrieval similarity alone is not enough to verify the exact target frame or event.
- **P2 iteration:** 30 queries (19 KIS, 9 QA, 2 TRAKE). `AIC_2026_P2_Enhanced.ipynb` was run on 28/08/2026 and recorded a successful ZIP build. Its QA answers were manually entered; `FINAL_ROWS_OVERRIDE` was empty, and TRAKE fallback drafts were used. These artifacts document the workflow, **not** verified ground-truth answers.

## Retrieval methodology

1. **Index the collection:** maintain video/frame metadata and extracted CLIP embeddings; build a FAISS vector index for approximate similarity search.
2. **Generate candidates:** encode text queries, retrieve relevant visual candidates, and inspect ranked results instead of assuming the top vector match is correct.
3. **Verify visually:** inspect contact sheets and selected original video segments to check whether an event actually appears in the proposed frame/time window.
4. **Resolve task-specific output:** use frame-level verification for KIS, evidence-informed answers for QA, and tight timing checks for TRAKE.
5. **Validate submissions:** apply explicit review and a final confirmation step before packaging the competition-format ZIP.

## Known limitations and lessons

- **Semantic similarity is not ground truth.** CLIP scores can rank visually related scenes while missing the exact event, so manual verification remains essential.
- **Sparse keyframes are only anchors.** Their timestamps are useful for navigation but may not coincide with the required original video frame.
- **Temporal localization is especially fragile.** TRAKE windows may be only a few frames wide; inspect the official MP4 near each candidate timestamp.
- **Review provenance matters.** Distinguish model-generated candidate drafts, human-confirmed selections, manually entered QA answers, and fallbacks. Do not present unverified drafts as validated submissions.
- **Reproducibility requires external assets.** Datasets and feature archives are held outside GitHub; the notebooks are not entirely self-contained.


- The original video dataset, core archives, keyframe ZIPs, indices, candidates and final ZIPs are on Google Drive. They are not stored in this local folder; confirm their current availability before relying on a notebook output.

## Project map

| File or folder | Role |
|---|---|
| `Thong tin vong So tuyen AIC2026.pdf` | Official local brief: query types, evaluation, data overview |
| `rules.txt`, `dataset.txt` | Official rules and dataset-sheet URLs |
| `SOTUYEN1-bo-de-thi/`, `SOTUYEN2-bo-de-thi/` | Official P1/P2 query files |
| `AIC_2026_Baseline_v1.ipynb` | BTC FiftyOne browsing baseline, not a full submission pipeline |
| `AIC_2026_Drive_Setup.ipynb` | Drive bootstrap for three core archives |
| `AIC_2026_Keyframes_Download.ipynb` | Resumable download of 14 keyframe ZIPs to Drive |
| `AIC_2026_CLIP_Search.ipynb` | P1 CLIP/FAISS retrieval and submission workflow |
| `AIC_2026_P2_Enhanced.ipynb` | P2 hybrid retrieval, visual review and final packaging |
| `AGENTS.md` | Always-on guardrails for coding agents |
| `.agents/skills/aic-video-retrieval/` | Detailed AIC workflow skill and validation utility |

`SKILL.md` in the root is a generic coding-guidelines skill. It is not the project operating manual. Do not create a duplicate `SKILLS.md` catalog; agents discover the project instructions through `AGENTS.md` and the project skill.

## Standard Colab workflow

Use the P2 notebook as a reference only for the P2 data/query bank. For a new round, copy it to a new versioned notebook and replace the query bank after re-reading the new official files.

1. Open the relevant `.ipynb` in Google Colab and mount the Drive account containing `MyDrive/AIC2026`.
2. Run setup/retrieval cells until the batch completion marker appears. For P2 it is `BATCH P2 COMPLETE — 30 DRAFTS, CHƯA TẠO SUBMISSION`.
3. Change `REVIEW_QUERY_ID` and rerun `# 13b)` to inspect ranked video and frame candidates.
4. Use `# 13c)` for keyframe contact sheets. For exact QA/TRAKE timing, use `# 13d)` to fetch one selected official MP4 and scan an increasingly narrow frame window.
5. Put only visual/video-confirmed rows in `FINAL_ROWS_OVERRIDE`; put QA answers in the review configuration.
6. Run the final cell once to obtain a `FINALIZE-...` token, copy it into `FINAL_CONFIRMATION`, rerun configuration and finalization, and submit the resulting ZIP unchanged.

Do not run the Colab retrieval notebook in VS Code's local kernel. It needs `google.colab` to mount Drive.

## Drive layout

```text
MyDrive/AIC2026/
├── raw/                 # CLIP features, keyframe map, media-info ZIPs
├── indices/             # FAISS index, frame/video CSVs, manifest
├── models/              # ViT-B-32 checkpoint
├── keyframe_zips/       # review images; keep compressed
├── candidates/          # saved candidate tables by batch run
├── selected_videos/     # only videos fetched for close inspection
└── submission/          # final ZIPs and manifests
```

`/content/aic_work` is a fast but ephemeral Colab work directory. Restarting Colab clears it, but never the Drive tree.

## Frame terms

| Field | Meaning | Submit? |
|---|---|---|
| `frame_idx` | Frame index in original video | Yes |
| `pts_time` | Approximate seconds for navigation | No |
| `n` / `keyframe_n` | BTC keyframe sequence, normally 1-based | No |
| `npy_row` | 0-based row in feature/image ordering | No |

Keyframes are sparse visual anchors, not necessarily the exact semantic event frame. This matters most for TRAKE, whose scoring windows are often fewer than ten original video frames.

## Validation

```powershell
python .agents/skills/aic-video-retrieval/scripts/audit_repository.py
python .agents/skills/aic-video-retrieval/scripts/audit_repository.py --submission "C:\path\submission.zip"
```

See [the project skill](.agents/skills/aic-video-retrieval/SKILL.md) for the rank-aware retrieval and submission workflow.
