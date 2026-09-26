# Project map and artifact lineage

Read this when selecting notebooks, checking data paths/schemas, or interpreting historical state.

## Local artifacts

| Artifact | Purpose | Important note |
|---|---|---|
| `Thong tin vong So tuyen AIC2026.pdf` | Official brief | Defines KIS, QA, TRAKE and ranking-based evaluation |
| `SOTUYEN1-bo-de-thi/` | P1 source | 25 files: 20 KIS, 4 QA, 1 TRAKE |
| `SOTUYEN2-bo-de-thi/` | P2 source | 30 files: 19 KIS, 9 QA, 2 TRAKE, each with four events |
| `AIC_2026_Baseline_v1.ipynb` | BTC demo | Uses FiftyOne, hard-coded legacy `D:\AICBaseline` paths, not submission logic |
| `AIC_2026_Drive_Setup.ipynb` | Bootstrap | Downloads and validates core archives |
| `AIC_2026_Keyframes_Download.ipynb` | Image retrieval | Resumes the 14 official keyframe ZIP downloads |
| `AIC_2026_CLIP_Search.ipynb` | P1 pipeline | Historical output/finalization state, not a generic new-round template |
| `AIC_2026_P2_Enhanced.ipynb` | P2 pipeline | Main hybrid retrieval/review implementation; executed historical artifact |

## Core data and mapping

The notebooks expect these three raw ZIPs under `MyDrive/AIC2026/raw/`:

| Archive | Content |
|---|---|
| `clip-features-32-aic25-b1.zip` | One image-embedding `.npy` matrix per video |
| `map-keyframes-aic25-b1.zip` | Matching CSVs with `n`, `pts_time`, `fps`, `frame_idx` |
| `media-info-aic25-b1.zip` | Video JSON metadata including title/author and YouTube `watch_url` where available |

For the cached Batch 1 bundle, the notebook validates 873 videos and 177,321 512-dimensional keyframe vectors. Do not use those counts as a new-dataset contract.

```text
NPY row i ↔ mapping CSV row i ↔ sorted keyframe-image position i
n/keyframe_n = 1-based order
npy_row       = 0-based lookup position
frame_idx     = original video frame; submission value
```

Image features are supplied from OpenAI CLIP ViT-B/32. The P1/P2 notebooks load the pinned matching text encoder and use exact L2-normalized FAISS inner-product search; this is inference, not model training.

## Persistent vs temporary paths

```text
/content/drive/MyDrive/AIC2026/       persistent Drive
├── raw/
├── indices/
├── models/
├── keyframe_zips/
├── candidates/
├── selected_videos/
└── submission/

/content/aic_work/                    temporary Colab runtime
├── extracted core data
├── copied index/model
├── selected_videos/
└── isolated submission builds
```

The local workspace contains neither those archives nor proof they still exist on Drive. Notebook printouts only document a prior session.

## P2 cell map

Refer to the heading, because markdown cells shift visible numbering.

| Heading | Purpose |
|---|---|
| `# 1)` through `# 5)` | Dependency install, Drive mount, data restore, source validation, FAISS load/build |
| `# 6)` through `# 8)` | Static P2 query bank, pinned CLIP encoder, retrieval/ranking helpers |
| `# 13)` | Hybrid batch; completion marker `BATCH P2 COMPLETE — 30 DRAFTS` |
| `# 13b)` | Candidate/video review table with timed URLs |
| `# 13c)` | Keyframe ZIP contact sheet, crop and optional OCR |
| `# 13d)` | RemoteZip extraction of one selected official MP4 and frame-window viewer |
| `# 14)` | QA answers, verified overrides and finalization token |
| `# 15)` | CSV/ZIP validation, checksum and final manifest |

P2 uses weighted atomic English prompts, robust per-video aggregation, per-prompt percentiles, optional title prior and temporal reranking. It creates candidate artifacts before any final submission.

## Recorded P2 state

On 28/08/2026 P2 recorded batch directory `candidates/p2/20260828T142200Z-5ec3e9f7eb` and created a final ZIP named `submission_p2_20260828T151553786332Z-a382b40a1e29.zip`. The notebook currently embeds manual QA strings, an empty `FINAL_ROWS_OVERRIDE`, and `USE_DRAFT_TRAKE_SEQUENCE=True`. Its final records should not be treated as checked ground truth.

## Known hazards

- Keyframes are sparse. Use original MP4 frame scans for short TRAKE moments; YouTube seeking by rounded `pts_time` may drift.
- OCR is fallible and may lack Vietnamese language data even if the Tesseract binary exists.
- The P2 remote-video helper fetches one entire MP4, not an entire archive, but does not verify a cached MP4 beyond nonzero size.
- The current notebook expects Batch 1 dimensions/counts and a static P2 query bank. Update both validation and query parsing when BTC changes source data.
- Batch reruns create new timestamped candidate directories and can be slow due to temporal reranking. Do not rerun casually.
