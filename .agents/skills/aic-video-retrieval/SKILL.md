---
name: aic-video-retrieval
description: "Operate and improve this repository's AIC video-retrieval workflow: parse KIS, QA, and TRAKE query sets; run CLIP/FAISS candidate retrieval; visually verify keyframes or video frames; and validate submission ZIPs. Use when running, debugging, reviewing, or extending the AIC notebooks; do not use for unrelated ML projects."
---

# AIC video retrieval

Use this skill to turn official AIC text queries into a traceable, rank-aware and structurally valid submission. CLIP retrieval narrows the search; a person or an evidence-based visual process still verifies the final video/frame/answer.

## Read the right detail

- Read [references/project-map.md](references/project-map.md) for notebooks, Drive paths, dataset artifacts, schemas, current historical state, and known implementation hazards.
- Read [references/query-submission.md](references/query-submission.md) for KIS/QA/TRAKE interpretation, official scoring, review choices and final archive rules.
- For a new round, changed archive or changed query set, read both before editing anything.

## Workflow

1. Inventory the current official query files:

   ```powershell
   python .agents/skills/aic-video-retrieval/scripts/audit_repository.py
   ```

2. Choose the smallest necessary operation: Drive setup, retrieval, candidate review, exact video alignment, or packaging. Do not rerun a full batch when only a review cell is needed.
3. Reuse the validated CLIP ViT-B/32 index when its manifest/fingerprint/checkpoint match. Do not train/reindex as a default response to a new query.
4. Retrieve broadly; then verify according to task type:

   - KIS: verify the described event and a frame inside the relevant interval.
   - QA: verify the event frame and obtain the answer from the image, OCR, counting or nearby video context.
   - TRAKE: verify the one video first, then align every event against original video frames in order.

5. Put confirmed rows first; keep distinct fallback hypotheses early rather than consuming the first ranks with duplicates from a single unconfirmed video.
6. Validate every final ZIP before handoff:

   ```powershell
   python .agents/skills/aic-video-retrieval/scripts/audit_repository.py --submission "PATH_TO_ZIP"
   ```

## Decision rules

- Always submit `frame_idx`, never a keyframe ordinal, NPY row, FAISS ID, or timestamp.
- Similarity/title/temporal scores are inspection evidence, not ground truth.
- Never fabricate QA answers or describe a row as verified without visual/video evidence. Include confidence and evidence source when passing work to another agent.
- Inspect ZIP keyframes without bulk extraction; download an official MP4 only after narrowing the candidate video.
- FiftyOne is an optional visual review UI. It does not replace retrieval, OCR, or exact frame alignment.
- Colab-specific cells must run in Colab. A local VS Code kernel cannot mount Google Drive through `google.colab`.
- A batch-complete message says candidate files exist. A ZIP-complete message says format validation passed. Neither proves semantic correctness.

## Editing safety

There is no Git rollback in this workspace. Preserve prior notebooks and user results; make versioned copies for substantial revisions. After notebook edits, parse JSON, compile non-magic cells, assert query inventory/schema and run a synthetic CSV/ZIP/CRC test. Never erase executed output from the user's notebook without explicit consent.
