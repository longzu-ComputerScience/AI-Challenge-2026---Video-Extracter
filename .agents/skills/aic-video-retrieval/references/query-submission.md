# Query, review and submission contract

## Official query types

| Type | Submission row | Condition for relevance |
|---|---|---|
| KIS | `video_id,frame_idx` | Correct video and frame inside the supplied event interval |
| QA | `video_id,frame_idx,answer` | Correct video, answer-bearing frame interval and semantic answer |
| TRAKE | `video_id,frame_event_1,...,frame_event_N` | Correct one video; each event frame is scored separately |

TRAKE's semantic keyframe is a meaningful content moment. It is not a compression I-frame and it is not automatically one of BTC's sparse keyframe images.

## Why rank matters

Each query permits at most 100 rows. The official score averages the best relevance in the first 1, 5, 20, 50 and 100 rows. One verified row at rank 1 improves every cutoff; a correct row near 100 helps only the last cutoff. This is why a visually confirmed row should lead automatic candidates.

## Review choices

### KIS

Split the description into distinctive atomic facts. Search/aggregate across those facts, inspect the leading videos, and select an original `frame_idx` inside the actual event rather than merely a visually similar image. Keep early fallback rows diverse across plausible videos.

### QA

Retrieval and answering are separate:

1. Verify the candidate video/scene.
2. Find a frame that contains the information asked about.
3. Read it from image/video context using visual inspection, crop/OCR or counting.
4. Confirm the requested form, particularly numbers and units.

CLIP cannot reliably read small text or exact counts. A correct answer paired with the wrong video/frame does not score.

### TRAKE

First establish the correct video; an incorrect video yields zero. Then find events chronologically. Use sparse keyframes as coarse anchors and scan a selected official MP4 with smaller steps around each transition. Ground-truth event intervals are often shorter than ten video frames. Event frames must be strictly increasing for the provided notebook validator.

## Submission contract

The ZIP contains no header rows and includes files only at paths such as:

```text
submission/query-p2-1-kis.csv
submission/query-p2-7-qa.csv
submission/query-p2-8-trake.csv
```

- Exactly one CSV per official query; each has 1–100 rows.
- CSV is comma-separated UTF-8 with no header.
- `video_id` has the official form `Lxx_Vxxx` without `.mp4`.
- Each submitted frame is a nonnegative integer `frame_idx`.
- QA answer is nonempty.
- TRAKE has one column for each event after `video_id` and frame IDs are strictly increasing.
- The ZIP must retain `submission/` as the internal directory and pass CRC validation.

The `FINALIZE-...` confirmation token hashes the ordered payload, preventing an accidental package after edits. It is not a secret. Any changed QA answer, override, or candidate payload needs a fresh token.

## Do not repeat these failures

- Submit `keyframe_n` or `npy_row` instead of `frame_idx`.
- Describe a candidate score as proof of correctness.
- Fill top ranks with duplicate frames from one wrong video.
- Guess a QA answer without ensuring its submitted frame belongs to the answer event.
- Use a sparse keyframe directly for exact TRAKE alignment.
- Run Colab mount/retrieval cells in a local VS Code kernel.
- Carry static P1/P2 query banks into a new official round.
