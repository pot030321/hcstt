"""Generate the Vietnamese presentation from measured experiment files."""

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt
from kb_store import summary


ROOT = Path(__file__).parent
ARTIFACTS = ROOT / "artifacts"
MODEL = json.loads((ARTIFACTS / "metrics.json").read_text(encoding="utf-8"))
KB = json.loads((ARTIFACTS / "kb_eval.json").read_text(encoding="utf-8"))
AUDIO = json.loads((ARTIFACTS / "audio_demo.json").read_text(encoding="utf-8"))
KB_META = summary()
NAVY = RGBColor(27, 56, 85)
TEAL = RGBColor(8, 137, 145)
PALE = RGBColor(236, 245, 246)
GRAY = RGBColor(80, 94, 105)
WHITE = RGBColor(255, 255, 255)


prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def box(slide, x, y, w, h, fill=PALE, rounded=True):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    return shape


def text(slide, value, x, y, w, h, size=20, color=NAVY, bold=False, align=PP_ALIGN.LEFT):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0)
    tf.margin_top = tf.margin_bottom = Inches(0)
    p = tf.paragraphs[0]
    p.text = value
    p.alignment = align
    p.font.name = "Arial"
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    return shape


def slide(title, section=None):
    s = prs.slides.add_slide(blank)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = WHITE
    box(s, 0, 0, 13.333, 0.16, TEAL, False)
    text(s, title, 0.65, 0.35, 12, 0.65, 28, NAVY, True)
    box(s, 0.65, 1.08, 12.05, 0.025, PALE, False)
    text(s, f"Hệ cơ sở tri thức  •  DDXPlus  •  {len(prs.slides):02d}", 0.68, 7.15, 10, 0.2, 10, GRAY)
    if section:
        text(s, section, 10.6, 7.15, 2.1, 0.2, 10, GRAY, align=PP_ALIGN.RIGHT)
    return s


def card(s, title, body, x, y, w, h, fill=PALE):
    box(s, x, y, w, h, fill)
    text(s, title, x + 0.2, y + 0.12, w - 0.4, 0.42, 19, TEAL, True)
    text(s, body, x + 0.2, y + 0.58, w - 0.4, h - 0.7, 17, NAVY)


def arrow(s, x, y, w=0.48):
    shape = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(0.28))
    shape.fill.solid()
    shape.fill.fore_color.rgb = TEAL
    shape.line.fill.background()


s = prs.slides.add_slide(blank)
s.background.fill.solid()
s.background.fill.fore_color.rgb = NAVY
box(s, 0.7, 0.8, 0.12, 5.7, TEAL, False)
text(s, "ĐỒ ÁN HỆ CƠ SỞ TRI THỨC", 1.15, 0.92, 10.8, 0.55, 19, RGBColor(144, 220, 221), True)
text(s, "TRA CỨU BỆNH TỪ TRIỆU CHỨNG\nBẰNG GIỌNG NÓI", 1.15, 1.85, 10.8, 2.0, 33, WHITE, True)
text(s, "Học tương phản để ánh xạ văn bản  •  Cơ sở tri thức để giải thích kết quả", 1.15, 4.1, 10.8, 0.85, 20, WHITE)
text(s, "Nguyễn Thái Hoàng Phong  |  11/2026", 1.15, 6.1, 10.8, 0.4, 17, RGBColor(198, 218, 226))

s = slide("1. Bài toán và câu hỏi nghiên cứu", "Mục tiêu")
card(s, "Người dùng nói", "I have a runny nose, chills, and a sore throat.", 0.75, 1.55, 3.8, 2.0)
card(s, "Máy hiểu", "Sổ mũi · ớn lạnh · đau họng; tra ba mã trong cơ sở tri thức.", 4.75, 1.55, 3.8, 2.0)
card(s, "Kết quả", "Cúm đứng đầu; hiện ba liên kết bệnh–triệu chứng làm lý do.", 8.75, 1.55, 3.8, 2.0)
text(s, "Câu hỏi chính: học tương phản có ánh xạ câu mô tả tốt hơn TF-IDF không?", 0.9, 4.15, 11.7, 0.8, 24, NAVY, True)
text(s, "Mục đích học thuật: tra cứu tri thức và giải thích, không chẩn đoán.", 0.9, 5.35, 11.7, 0.65, 20, TEAL)

s = slide("2. Cơ sở tri thức nằm ở đâu?", "KB")
s.shapes.add_picture(str(ARTIFACTS / "kb_schema.png"), Inches(0.75), Inches(1.45), width=Inches(11.8))
text(s, "Ví dụ trong bảng quan hệ: Influenza → has_symptom → E_97 (đau họng). Ba triệu chứng đầu vào đều có liên kết như vậy, nên cúm đứng đầu.", 0.85, 5.55, 11.8, 1.05, 19, NAVY)

s = slide("3. Dữ liệu DDXPlus", "Nguồn")
for title, body, x in [
    ("49", "bệnh trong KB", 0.9),
    ("223", "triệu chứng / tiền sử", 4.1),
    ("134.529", "ca trong tập test", 7.4),
]:
    box(s, x, 1.6, 2.9, 1.65, PALE)
    text(s, title, x + 0.2, 1.82, 2.5, 0.65, 31, TEAL, True, PP_ALIGN.CENTER)
    text(s, body, x + 0.1, 2.57, 2.7, 0.35, 16, NAVY, align=PP_ALIGN.CENTER)
text(s, "Hai JSON được nhập vào SQLite: 605 quan hệ triệu chứng + 283 quan hệ tiền sử; kiểm tra khóa ngoại, số hàng và SHA-256 nguồn.", 0.9, 3.85, 11.7, 0.95, 20, NAVY)
text(s, "Dữ liệu không có audio. Nhóm tạo file audio riêng để thử đường nhập giọng nói.", 0.9, 5.0, 11.7, 0.8, 19, TEAL)
text(s, "Nguồn: Mila / DDXPlus English v2, NeurIPS 2022", 0.9, 6.2, 11.7, 0.4, 14, GRAY)

s = slide("4. Học tương phản: vai trò và công thức", "Neural network")
card(s, "Biểu diễn", "TF-IDF ký tự 2–4 gram → lớp tuyến tính 64 chiều → chuẩn hóa L2.", 0.8, 1.5, 5.5, 2.05)
card(s, "Cặp huấn luyện", "Câu mô tả q + nhãn triệu chứng đúng s+ là cặp dương; nhãn khác là cặp âm.", 6.75, 1.5, 5.5, 2.05)
box(s, 0.8, 4.1, 11.45, 1.25, RGBColor(226, 241, 243))
text(s, "L = −log [ exp(sim(q,s+)/τ) / Σs exp(sim(q,s)/τ) ]", 1.1, 4.35, 10.85, 0.7, 22, NAVY, True, PP_ALIGN.CENTER)
text(s, "Contrastive ở bước text → mã triệu chứng; audio đi qua ASR trước.", 0.9, 5.75, 11.5, 0.65, 20, TEAL)

s = slide("5. Luồng phần mềm", "Thiết kế")
for title, x, w in [("Audio", 0.7, 1.55), ("Whisper", 2.75, 1.8), ("Tách câu", 5.05, 1.85), ("Học tương phản", 7.4, 2.2), ("KB", 10.15, 1.85)]:
    box(s, x, 2.3, w, 1.0, RGBColor(222, 240, 241) if x >= 7.4 else PALE)
    text(s, title, x + 0.07, 2.55, w - 0.14, 0.5, 19, NAVY, True, PP_ALIGN.CENTER)
for x in (2.35, 4.65, 7.0, 9.72):
    arrow(s, x, 2.66, 0.35)
box(s, 2.75, 4.1, 1.8, 0.85, PALE)
text(s, "Text", 2.85, 4.26, 1.6, 0.5, 19, NAVY, True, PP_ALIGN.CENTER)
text(s, "↗", 4.65, 3.75, 0.7, 0.7, 32, TEAL, True)
text(s, "Sau ASR, người dùng có thể sửa bản chép lời trước khi tra cứu.", 0.9, 5.65, 11.5, 0.7, 20, NAVY)

s = slide("6. Bộ suy luận và cơ chế giải thích", "Reasoning")
box(s, 0.8, 1.45, 11.55, 1.35, PALE)
text(s, "score(d) = Σ IDF(s) cho triệu chứng khớp / Σ IDF(s) của đầu vào", 1.1, 1.78, 10.9, 0.7, 23, NAVY, True, PP_ALIGN.CENTER)
card(s, "Quy tắc", "Chỉ dùng triệu chứng dương tính. Cần tối thiểu 2 mã khác nhau.", 0.85, 3.35, 5.45, 1.85)
card(s, "Giải thích", "Hiện mã E_*, câu hỏi chuẩn, quan hệ KB và nguồn; báo số bệnh đồng điểm.", 6.72, 3.35, 5.45, 1.85)
text(s, "Điểm khớp không phải xác suất mắc bệnh.", 0.95, 5.75, 11.5, 0.65, 21, TEAL, True)

s = slide("7. Kết quả ánh xạ triệu chứng", "Thực nghiệm")
s.shapes.add_picture(str(ARTIFACTS / "model_metrics.png"), Inches(0.7), Inches(1.35), width=Inches(7.8))
text(s, "75 câu tự biên soạn\n45 train / 15 val / 15 test\n15 mã triệu chứng", 8.75, 1.6, 3.7, 2.1, 19, NAVY)
box(s, 8.75, 4.05, 3.7, 1.15, RGBColor(226, 241, 243))
text(s, f"Test Top-1: {MODEL['test']['tfidf']['top1']:.1%} → {MODEL['test']['contrastive']['top1']:.1%}", 8.95, 4.3, 3.3, 0.65, 19, TEAL, True, PP_ALIGN.CENTER)
text(s, "Mẫu test nhỏ; kết quả chưa đại diện cho mô tả bệnh ngoài thực tế.", 0.95, 6.25, 11.5, 0.4, 16, GRAY)

s = slide("8. Kết quả suy luận trên KB", "Thực nghiệm")
s.shapes.add_picture(str(ARTIFACTS / "kb_metrics.png"), Inches(0.7), Inches(1.35), width=Inches(7.8))
text(s, "1.000 ca lấy ngẫu nhiên từ 134.529 ca test DDXPlus; seed = 7.", 8.75, 1.58, 3.75, 1.45, 18, NAVY)
box(s, 8.75, 3.45, 3.7, 1.45, RGBColor(226, 241, 243))
text(s, f"Recall@5\n{KB['idf_weighted_overlap']['recall_at_5']:.1%}", 9.05, 3.67, 3.1, 1.05, 26, TEAL, True, PP_ALIGN.CENTER)
text(s, "IDF và đếm khớp cho cùng kết quả trên mẫu này.", 8.75, 5.15, 3.7, 0.95, 17, GRAY)
text(s, "Đây là kết quả trên ca mô phỏng, không là độ chính xác chẩn đoán.", 0.95, 6.32, 11.5, 0.4, 16, GRAY)

s = slide("9. Từ lời kể đến bệnh gợi ý", "Demo")
card(s, "Audio đầu vào", "samples/influenza_demo.mp3\nGiọng nói tổng hợp tiếng Anh", 0.8, 1.5, 3.7, 1.85)
card(s, "Whisper chép lời", AUDIO["transcript"], 4.78, 1.5, 3.7, 1.85)
card(s, "Triệu chứng nhận ra", "E_181 = sổ mũi\nE_94 = ớn lạnh\nE_97 = đau họng", 8.75, 1.5, 3.7, 1.85)
box(s, 0.8, 4.05, 11.65, 1.2, RGBColor(226, 241, 243))
text(s, f"Gợi ý đầu: CÚM (INFLUENZA)  •  {len(AUDIO['top_evidence_codes'])}/3 liên kết triệu chứng  •  điểm {AUDIO['top_score']:.2f}", 1.0, 4.32, 11.15, 0.65, 22, NAVY, True, PP_ALIGN.CENTER)
text(s, "Cơ sở tri thức ghi nhận 3 quan hệ has_symptom; điểm khớp không phải xác suất mắc bệnh.", 0.95, 5.95, 11.5, 0.55, 17, GRAY)

s = slide("10. Cách demo trực tiếp", "Demo")
s.shapes.add_picture(str(ARTIFACTS / "web_demo.png"), Inches(0.75), Inches(1.35), width=Inches(7.05))
card(s, "01 · Chạy audio mẫu", "Bấm nút audio mẫu hoặc tải MP3 tiếng Anh.", 8.05, 1.45, 4.5, 1.38)
card(s, "02 · Xem bệnh và lý do", "Cúm đứng đầu; mở 3 liên kết triệu chứng trong KB.", 8.05, 3.02, 4.5, 1.38)
card(s, "03 · Thử ca mơ hồ", "Sốt + ho cho nhiều bệnh đồng điểm, nên cần thêm triệu chứng.", 8.05, 4.59, 4.5, 1.38)

s = slide("11. Kết luận và giới hạn", "Tổng kết")
card(s, "Đã làm", "KB có thể truy vết; mô hình tương phản; đường text/audio; bộ suy luận; demo web cục bộ; số liệu thật.", 0.8, 1.5, 5.6, 2.55)
card(s, "Giới hạn", "15 triệu chứng; tiếng Anh; audio demo tổng hợp; ca DDXPlus mô phỏng; phủ định còn đơn giản.", 6.75, 1.5, 5.6, 2.55)
text(s, "Hướng mở rộng: audio người thật có nhãn, thêm triệu chứng, học tương phản audio–text trực tiếp.", 0.9, 4.7, 11.55, 1.1, 21, TEAL, True)
text(s, "Chỉ dùng để học và tra cứu; không dùng để chẩn đoán hoặc điều trị.", 0.9, 6.15, 11.55, 0.5, 18, GRAY)

s = slide("12. Tài liệu tham khảo", "Nguồn")
refs = [
    "Fansi Tchango et al., DDXPlus, NeurIPS 2022 — proceedings.neurips.cc",
    "Mila, DDXPlus dataset English v2 — mila-iqia.github.io/ddxplus",
    "Radford et al., CLIP, 2021 — arxiv.org/abs/2103.00020",
    "Radford et al., Whisper, 2022 — arxiv.org/abs/2212.04356",
    "Olvera et al., iKnow-audio, EMNLP 2025 — aclanthology.org/2025.emnlp-main.1759",
    "Class Notebook, Hệ cơ sở tri thức — Google Docs của giảng viên",
]
for i, ref in enumerate(refs):
    box(s, 0.9, 1.35 + i * 0.88, 11.5, 0.72, PALE)
    text(s, ref, 1.15, 1.49 + i * 0.88, 10.95, 0.42, 16, NAVY)

output = ROOT / "Slide_do_an_HCSTT.pptx"
prs.save(output)
print(output)
