# Phân tích & Ý tưởng cải tiến cho Đợt 3 AIC 2026

## 🔴 TÌNH HUỐNG KHẨN CẤP

**Đợt 3 mở lúc 19:30 tối nay (04/09), đóng 22:30 — chỉ có 3 tiếng.** Bạn chỉ được nộp tối đa **3 lần**, và lần nộp **cuối cùng** mới được tính điểm. Public leaderboard chỉ chấm 50% đáp án.

---

## 📊 Bức tranh hiện tại & Nguyên nhân điểm thấp

### Kết quả 2 đợt trước
| Đợt | Queries | Kết quả | Vấn đề chính |
|------|---------|---------|-------------|
| P1 | 25 (20 KIS, 4 QA, 1 TRAKE) | ~2.5 điểm, rank ~250/300 | Candidates tự động chưa verify, rank 1 không chính xác |
| P2 | 30 (19 KIS, 9 QA, 2 TRAKE) | Thấp (chưa rõ điểm) | QA nhập tay, `FINAL_ROWS_OVERRIDE` trống, TRAKE dùng draft fallback |

### 5 Nguyên nhân gốc rễ

#### 1. ❌ Không visual verification → rank 1 sai
Hệ thống chấm lấy best relevance ở rank 1, 5, 20, 50, 100. Một row đúng ở rank 1 cải thiện **mọi** cutoff. Pipeline hiện tại chạy batch → dump candidates → nộp nguyên bản draft mà không xác nhận bằng mắt video/frame nào đúng.

#### 2. ❌ CLIP ViT-B/32 quá yếu cho nội dung tiếng Việt
- Queries mô tả ẩm thực Việt: "dồi trường", "bông hẹ", "bánh màu tím", "cá sòng" — CLIP ViT-B/32 **không hiểu** tiếng Việt và cũng khó khớp với ngữ cảnh văn hóa Việt.
- Prompt phải dịch sang tiếng Anh, nhưng nhiều khái niệm không có equivalent tốt ("dâu bòn bon" → "langsat"?)
- CLIP ViT-B/32 là model cũ, embedding chỉ 512-dim, thường bị model mới như **SigLIP**, **OpenCLIP ViT-L/14**, hay **BLIP-2** vượt xa.

#### 3. ❌ QA answers thiếu OCR/VLM tự động
- Câu QA yêu cầu đọc text từ video (số trên xe, tên loài cá, đếm vật thể).
- Pipeline hiện tại: dùng CLIP tìm frame → **người** đọc đáp án bằng mắt. Không có VLM (Vision-Language Model) hay OCR pipeline tự động.
- Trong 3 tiếng, không thể thủ công verify 9+ câu QA.

#### 4. ❌ TRAKE alignment quá thô
- `best_ordered_sequence()` chỉ tìm trên sparse keyframes (177K frames cho 873 video ≈ 200 frame/video), nhưng ground-truth event intervals thường < 10 original frames.
- Không download MP4 và scan frame-by-frame quanh keyframe candidate.
- `USE_DRAFT_TRAKE_SEQUENCE = True` → nộp bản draft không verify.

#### 5. ❌ Thiếu đa dạng video ở top ranks
- Nếu top-1 video sai → toàn bộ các row từ video đó đều 0 điểm.
- `max_per_video = 5` nghĩa là 5 slots đầu có thể bị cùng 1 video sai chiếm.
- Cần chiến lược hedging: đặt diverse video hypotheses ở top ranks.

---

## 💡 Ý tưởng cải tiến — Phân loại theo mức đầu tư

### 🟢 A. LÀM ĐƯỢC NGAY TRONG ĐÊM NAY (trước 19:30)

#### A1. Nâng cấp model retrieval → OpenCLIP ViT-L/14 hoặc SigLIP
**Tác động: +++** | **Công sức: Trung bình (1-2 giờ)**

```python
# Thay thế CLIP ViT-B/32 bằng OpenCLIP hoặc SigLIP
import open_clip
model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-L-14', pretrained='datacomp_xl_s13b_b90k'
)
tokenizer = open_clip.get_tokenizer('ViT-L-14')
```

Vấn đề: **Cần reindex 177K keyframes** vì embedding dimension thay đổi (512→768). Trên Colab GPU T4/V100 mất ~20-30 phút.

> **THỰC TẾ**: Không kịp nếu đợt 3 mở tối nay. Giải pháp: dùng **multilingual CLIP** (XLM-Roberta) chỉ thay text encoder, giữ nguyên image embeddings. Hoặc dùng **sentence-transformers** để encode query tiếng Việt → map sang CLIP space.

#### A2. Dùng VLM (GPT-4o / Gemini) để verify top candidates + trả lời QA
**Tác động: ++++** | **Công sức: Thấp (cell mới ~30 phút)**

Đây là cải tiến ROI cao nhất. Sau khi CLIP trả về top 5-10 video/frame cho mỗi query:

```python
import google.generativeai as genai

def verify_candidate_with_vlm(keyframe_image, query_text, query_type):
    """Dùng Gemini 1.5 Flash để verify frame + trả lời QA"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if query_type == 'qa':
        prompt = f"""Nhìn ảnh này và trả lời câu hỏi sau bằng tiếng Việt.
        Mô tả: {query_text['description']}
        Câu hỏi: {query_text['question']}
        Chỉ trả lời ngắn gọn, chính xác."""
    elif query_type == 'kis':
        prompt = f"""So sánh mô tả sau với nội dung ảnh:
        "{query_text}"
        Ảnh này có khớp với mô tả không? Trả lời YES/NO và confidence 0-100."""
    
    response = model.generate_content([prompt, keyframe_image])
    return response.text
```

**Lợi ích:**
- Tự động verify KIS candidates → đẩy row đúng lên rank 1
- Tự động trả lời QA → không cần đọc bằng mắt
- Gemini 1.5 Flash: rẻ, nhanh, hiểu tiếng Việt, đọc được text trong ảnh (OCR ngầm)

#### A3. Multilingual query expansion — dịch + prompt engineering tốt hơn
**Tác động: ++** | **Công sức: Thấp (15 phút)**

Hiện tại prompt dịch tay từ Việt sang Anh, có thể miss context. Cải tiến:

```python
# Dùng nhiều biến thể prompt cho mỗi query
PROMPT_VARIANTS = [
    "original English translation",
    "simplified version focusing on visual features",
    "detailed version with colors, numbers, objects",
    "Vietnamese caption translated by GPT-4",
]
# Aggregate scores across variants → robust hơn
```

#### A4. Cải thiện ranking strategy — hedging & diversity
**Tác động: +++** | **Công sức: Thấp (20 phút sửa code)**

```python
# Thay vì max_per_video=5, dùng tiered strategy:
# Rank 1: Best verified candidate
# Rank 2-5: Top candidates từ 4 video KHÁC NHAU  
# Rank 6-20: Mix giữa top-1 video và diverse videos
# Rank 21-100: Fill từ batch candidates

TIER1_VERIFIED = 1          # 1 row đã VLM-verify
TIER2_DIVERSE_VIDEOS = 4    # 1 row từ mỗi video khác nhau  
TIER3_MAX_PER_VIDEO = 3     # max 3 rows/video cho phần còn lại
```

#### A5. Title/metadata matching mạnh hơn
**Tác động: ++** | **Công sức: Thấp**

Nhiều query đề cập tên món ăn, tên chương trình. Video metadata có `title` và `author`. Hiện tại dùng `rapidfuzz.partial_ratio` nhưng `title_weight = 0.12` quá thấp.

```python
# Nâng title weight khi match score > 80%
title_weight = 0.25 if max_title_score > 0.8 else 0.12

# Thêm: search title bằng regex/substring match trước
# → pre-filter videos có title chứa keyword Việt
import re
def title_contains_keywords(title, keywords_vi):
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in keywords_vi)
```

---

### 🟡 B. CẢI TIẾN CHO ĐỢT 3+ (làm trước ngày thi)

#### B1. Hybrid retrieval: CLIP + VLM re-ranking pipeline
**Tác động: +++++** | **Công sức: 2-3 giờ**

Pipeline 3 giai đoạn:
1. **Recall**: CLIP/FAISS top-500 frames per query (fast, broad)
2. **Re-rank**: VLM (Gemini Flash) score top-50 frames vs query (precise)
3. **Verify**: VLM verify top-5 → push confirmed lên rank 1

```
Query → CLIP encode → FAISS top-500 → VLM re-rank top-50 → VLM verify top-5 → Submission
         (0.5s)         (instant)       (30s/query)          (10s/query)
```

Tổng thời gian cho 30 queries: ~20 phút thay vì 3 tiếng thủ công.

#### B2. OCR pipeline cho QA
**Tác động: +++** | **Công sức: 1 giờ**

```python
# Thay Tesseract bằng EasyOCR hoặc PaddleOCR (hỗ trợ tiếng Việt)
import easyocr
reader = easyocr.Reader(['vi', 'en', 'ch_sim'])

# Hoặc dùng Gemini Vision trực tiếp — ưu điểm: context-aware OCR
def read_text_from_frame(frame_image, what_to_read):
    response = vlm.generate_content([
        f"Đọc chính xác {what_to_read} xuất hiện trong ảnh này. Chỉ trả lời giá trị.",
        frame_image
    ])
    return response.text
```

#### B3. Frame-level alignment cho TRAKE
**Tác động: +++** | **Công sức: 1-2 giờ**

```python
def precise_trake_alignment(video_path, events, keyframe_anchors):
    """Scan MP4 frame-by-frame quanh keyframe anchors"""
    cap = cv2.VideoCapture(video_path)
    for event_name, anchor_frame in keyframe_anchors.items():
        # Scan ±50 frames quanh anchor
        best_frame, best_score = scan_window(
            cap, anchor_frame - 50, anchor_frame + 50,
            event_prompt=events[event_name],
            step=5  # check every 5th frame first, then narrow
        )
    cap.release()
    return aligned_frames
```

#### B4. Dịch queries bằng LLM trước khi encode CLIP
**Tác động: ++** | **Công sức: 30 phút**

```python
def translate_and_expand_query(query_vi, task_type):
    """Dùng GPT-4 / Gemini dịch + phân rã query thành atomic visual facts"""
    prompt = f"""Dịch mô tả video sau sang tiếng Anh, tập trung vào:
    - Hành động cụ thể (động từ mạnh)
    - Đối tượng nhìn thấy được (màu sắc, hình dạng, số lượng)
    - Bối cảnh không gian
    
    Tạo 3-5 sub-queries ngắn, mỗi sub-query tập trung 1 fact riêng biệt.
    
    Vietnamese: {query_vi}"""
    # → Trả về list of focused English prompts
```

---

### 🔴 C. CẢI TIẾN DÀI HẠN (nếu vào vòng trong)

| Ý tưởng | Mô tả |
|---------|-------|
| **C1. Reindex bằng SigLIP/InternVL** | Embedding mạnh hơn, cần GPU |
| **C2. Video-level understanding** | Dùng VideoLLM (Qwen-VL, InternVL-Chat) phân tích đoạn video thay vì keyframe rời |
| **C3. Agentic retrieval** | Agent tự lặp: tìm → verify → refine query → tìm lại nếu confident thấp |
| **C4. Fine-tune CLIP trên dataset Việt** | Không khả thi trong sơ tuyển, nhưng useful cho chung kết |
| **C5. Ensemble nhiều model** | Kết hợp CLIP + BLIP-2 + SigLIP scores |

---

## 🎯 Chiến lược tối ưu cho TỐI NAY — Thứ tự ưu tiên

> [!IMPORTANT]
> Bạn chỉ có ~1 tiếng trước khi đợt 3 mở. Tập trung vào ROI cao nhất.

### Bước 0 (NGAY BÂY GIỜ — trước 19:30)
1. **Copy notebook P2 → P3**, update query bank cho đợt 3 (khi đề ra)
2. **Thêm cell Gemini VLM** vào notebook để verify candidates + trả lời QA
3. **Chuẩn bị API key** Gemini (free tier: 15 RPM / 1M tokens/day đủ dùng)
4. **Sửa ranking strategy**: max 2 row/video ở top-10, diverse video hedging

### Bước 1 (19:30 — khi đề ra)
1. Download đề P3, parse queries, phân loại KIS/QA/TRAKE
2. **LLM-assist translate** queries → English atomic prompts (dùng Gemini)
3. Chạy batch retrieval (5-10 phút)

### Bước 2 (19:45 — sau batch)
1. **VLM verify** top-5 candidates cho MỖI query (~20 phút cho 25-30 queries)
2. QA: Gemini đọc frame → trả lời tự động
3. TRAKE: Identify đúng video → download MP4 → align events

### Bước 3 (20:30 — nộp lần 1)
1. Nộp submission lần 1 với candidates đã VLM-verified
2. Xem public leaderboard (50% đáp án) → biết query nào sai

### Bước 4 (21:00 — refine)  
1. Focus sửa queries mà leaderboard cho 0 điểm
2. Re-search với modified prompts
3. VLM re-verify
4. Nộp lần 2

### Bước 5 (22:00 — nộp cuối)
1. Final polish, kiểm tra format
2. Nộp lần 3 (CUỐI CÙNG) trước 22:30

---

## 📋 Checklist kỹ thuật cần chuẩn bị

- [ ] Gemini API key (hoặc OpenAI API key cho GPT-4o)
- [ ] `pip install google-generativeai` trong Colab
- [ ] Cell VLM verify + QA answer
- [ ] Cell translate query bằng LLM
- [ ] Sửa ranking: diverse video hedging
- [ ] Copy notebook P2 → `AIC_2026_P3_Enhanced.ipynb`
- [ ] Test pipeline end-to-end với 1 query P2 cũ

---

## ⚠️ Lưu ý quan trọng

1. **Không reindex** — giữ nguyên FAISS index ViT-B/32. Reindex mất 30+ phút, không kịp.
2. **VLM là multiplier** — CLIP tìm candidates, VLM verify & answer. Kết hợp = mạnh hơn nhiều so với dùng riêng.
3. **Ranking quan trọng hơn recall** — tìm được video đúng nhưng để ở rank 50 thì chỉ giúp 1 cutoff. Đưa lên rank 1 giúp cả 5 cutoffs.
4. **3 lần nộp = 3 cơ hội** — nộp sớm, xem feedback, sửa, nộp lại.
