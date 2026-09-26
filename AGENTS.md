# AIC 2026 workspace instructions

Use Vietnamese when assisting the user unless they ask otherwise. Give one concrete next action at a time when the task is time-sensitive.

## Start here

- Read [README.md](README.md) for the project state and which notebook fits the task.
- For AIC retrieval, review or submission work, read [.agents/skills/aic-video-retrieval/SKILL.md](.agents/skills/aic-video-retrieval/SKILL.md) and the reference it routes to.
- Source-of-truth order: current official query text → official rules/PDF and dataset sheet → BTC maps/metadata → notebooks and chat history. Re-inventory every new query folder; never reuse P1/P2 counts or IDs by assumption.

## Non-negotiable data rules

- Submit `frame_idx` only. `n`, `keyframe_n`, `npy_row`, `pts_time`, and `faiss_id` are lookup aids, never submission values.
- Candidate retrieval is a shortlist, not an answer. Mark outputs as verified, inferred, or unverified.
- KIS rows are `video_id,frame_idx`; QA rows are `video_id,frame_idx,answer`; TRAKE rows are a single `video_id` followed by one frame for every ordered event.
- A correct, visually verified row belongs ahead of unverified candidates. Ranking is part of the official scoring.
- Use the existing OpenAI CLIP ViT-B/32 / FAISS index if its source checks pass. Do not train or rebuild the index by default.
- Do not bulk-extract all keyframe ZIPs or download every MP4. Narrow candidates first, then inspect ZIP keyframes or a selected official video.

## Preserve history

This workspace is not a Git repository. Never erase user outputs, QA values, finalization tokens, submission logs, or earlier-round notebooks without explicit approval. Make a versioned notebook copy for substantial changes.

`AIC_2026_P2_Enhanced.ipynb` is an executed historical artifact: it embeds manual QA strings and a successful final ZIP log, but has no verified frame overrides. It is not a clean template or ground-truth answer key.

## Colab versus local

The retrieval notebooks mount Google Drive and are designed for Google Colab. A VS Code `Python 3 (ipykernel)` / `Work locally` kernel is not a valid replacement for Colab. The FiftyOne baseline is only a local visualisation demo and contains legacy hard-coded paths.

- Durable data: `/content/drive/MyDrive/AIC2026`.
- Temporary runtime data: `/content/aic_work`; it disappears on runtime reset.

## Required validation

Run from the workspace root after changing query files, docs, or notebooks:

```powershell
python .agents/skills/aic-video-retrieval/scripts/audit_repository.py
```

For a submission ZIP:

```powershell
python .agents/skills/aic-video-retrieval/scripts/audit_repository.py --submission "PATH_TO_ZIP"
```

When editing a notebook, also verify JSON parsing, compile non-magic code cells, assert query inventory/types, and run a synthetic CSV/ZIP/CRC test. Do not silently clear output from the user's executed notebook.

## Handoff standard

- Refer to cells by their heading, for example `# 14) CẤU HÌNH REVIEW P2`, not only a UI number.
- Distinguish a finished batch from a semantically verified answer.
- When a ZIP is ready, name its exact location and say to submit the ZIP unchanged, without extraction.
