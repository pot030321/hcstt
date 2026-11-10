"""Generate the Vietnamese course report from measured experiment files."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from kb_store import summary


ROOT = Path(__file__).parent
ARTIFACTS = ROOT / "artifacts"
MODEL = json.loads((ARTIFACTS / "metrics.json").read_text(encoding="utf-8"))
KB = json.loads((ARTIFACTS / "kb_eval.json").read_text(encoding="utf-8"))
AUDIO = json.loads((ARTIFACTS / "audio_demo.json").read_text(encoding="utf-8"))
KB_META = summary()


def charts():
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    positions = [0, 1]
    ax.bar([x - 0.18 for x in positions], [MODEL[s]["tfidf"]["top1"] for s in ("val", "test")], width=0.36, label="TF-IDF", color="#8099b7")
    ax.bar([x + 0.18 for x in positions], [MODEL[s]["contrastive"]["top1"] for s in ("val", "test")], width=0.36, label="Contrastive", color="#0a8791")
    ax.set_xticks(positions, ["Validation (15)", "Test (15)"])
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Top-1 accuracy")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "model_metrics.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    labels = ["Top-1", "Recall@5", "MRR"]
    values = [KB["idf_weighted_overlap"][key] for key in ("top1", "recall_at_5", "mrr")]
    ax.bar(labels, values, color=["#31567b", "#0a8791", "#79a8aa"])
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Score on 1,000 synthetic test cases")
    ax.grid(axis="y", alpha=0.2)
    for i, value in enumerate(values):
        ax.text(i, value + 0.02, f"{value:.3f}", ha="center")
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "kb_metrics.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 2.2))
    ax.axis("off")
    boxes = [
        ("Audio → ASR\nText trực tiếp", 0.10),
        ("Tách câu, phủ định", 0.38),
        ("Học tương phản", 0.65),
        ("KB + suy luận", 0.89),
    ]
    for label, center in boxes:
        ax.text(center, 0.5, label, ha="center", va="center", fontsize=11, color="white",
                bbox={"boxstyle": "round,pad=0.55", "facecolor": "#31567b" if center < 0.65 else "#0a8791", "edgecolor": "none"})
    for left, right in ((0.10, 0.38), (0.38, 0.65), (0.65, 0.89)):
        ax.annotate("", xy=(right - 0.10, 0.5), xytext=(left + 0.10, 0.5), arrowprops={"arrowstyle": "->", "color": "#49576a", "lw": 2})
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "pipeline.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 3.1))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.1)
    ax.axis("off")
    nodes = [
        ("source\nid · dataset · version\nURL · SHA-256", 0.2, 1.3, "#31567b"),
        ("disease\nname (PK) · ICD-10\nseverity · source_id (FK)", 3.0, 2.1, "#0a8791"),
        ("evidence\ncode (PK) · question_en\ndata_type · source_id (FK)", 3.0, 0.45, "#0a8791"),
        ("disease_evidence\ndisease_name (FK) · evidence_code (FK)\nrelation · source_id (FK)", 6.6, 1.3, "#31567b"),
    ]
    for label, x, y, color in nodes:
        ax.text(x, y, label, color="white", fontsize=10, va="center", ha="left",
                bbox={"boxstyle": "round,pad=0.65", "facecolor": color, "edgecolor": "none"})
    for start, end in [((2.3, 1.55), (2.9, 2.1)), ((2.3, 1.4), (2.9, 0.65)),
                       ((5.45, 2.1), (6.5, 1.65)), ((5.45, 0.65), (6.5, 1.3))]:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "color": "#637d8c", "lw": 1.7})
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "kb_schema.png", dpi=170)
    plt.close(fig)


def paragraph(doc, text="", style=None):
    p = doc.add_paragraph(style=style)
    p.add_run(text)
    return p


def table(doc, headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Shading Accent 1"
    for cell, value in zip(t.rows[0].cells, headers):
        cell.text = str(value)
    for row in rows:
        for cell, value in zip(t.add_row().cells, row):
            cell.text = str(value)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.first_line_indent = Cm(0)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    run.font.size = Pt(9)
    doc.add_paragraph()
    return t


def caption(doc, text):
    p = paragraph(doc, text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:
        run.italic = True
        run.font.size = Pt(10)


def toc(doc):
    p = doc.add_paragraph()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = ' TOC \\o "1-2" \\h \\z \\u '
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for item in (begin, instruction, separate):
        p.add_run()._r.append(item)
    p.add_run("Nhấn Ctrl+A rồi F9 trong Word để cập nhật mục lục và số trang.")
    p.add_run()._r.append(end)
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    doc.settings.element.append(update)


def main():
    charts()
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin, section.bottom_margin = Cm(2.5), Cm(2)
    section.left_margin = section.right_margin = Cm(2.5)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.first_line_indent = Cm(0.6)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for name, size in (("Title", 20), ("Heading 1", 15), ("Heading 2", 13)):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(20, 53, 78)
        style.paragraph_format.first_line_indent = Cm(0)
        style.paragraph_format.keep_with_next = True
        if name == "Heading 1":
            style.paragraph_format.page_break_before = True
    for line in ("BỘ GIÁO DỤC VÀ ĐÀO TẠO", "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ TP.HCM"):
        p = paragraph(doc, line)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].bold = True
    doc.add_paragraph()
    for line in ("BÀI TIỂU LUẬN HỌC PHẦN", "HỆ CƠ SỞ TRI THỨC"):
        p = paragraph(doc, line)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(17)
    doc.add_paragraph()
    p = paragraph(doc, "ĐỀ TÀI: ỨNG DỤNG HỌC TƯƠNG PHẢN TRONG HỆ CƠ SỞ TRI THỨC TRA CỨU BỆNH TỪ MÔ TẢ TRIỆU CHỨNG BẰNG GIỌNG NÓI")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].bold = True
    p.runs[0].font.size = Pt(17)
    p.runs[0].font.color.rgb = RGBColor(10, 115, 125)
    doc.add_paragraph()
    table(doc, ["Thông tin", "Nội dung"], [
        ["Học viên", "Nguyễn Thái Hoàng Phong"],
        ["Mã học viên", "2541862025"],
        ["Giảng viên", "GS. TSKH. Nguyen Hung Son"],
    ])
    p = paragraph(doc, "Thành phố Hồ Chí Minh, tháng 11 năm 2026")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    body_section = doc.add_section(WD_SECTION_START.NEW_PAGE)
    body_section.top_margin = body_section.bottom_margin = Cm(2)
    body_section.left_margin, body_section.right_margin = Cm(3), Cm(1.5)
    body_section.footer.is_linked_to_previous = False
    footer = body_section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    page_number = OxmlElement("w:pgNumType")
    page_number.set(qn("w:start"), "1")
    body_section._sectPr.append(page_number)

    p = paragraph(doc, "MỤC LỤC")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].bold = True
    p.runs[0].font.size = Pt(16)
    toc(doc)
    doc.add_heading("DANH MỤC HÌNH ẢNH", level=1)
    for line in ("Hình 3.1. Lược đồ quan hệ của KB SQLite.", "Hình 3.2. Luồng xử lý audio/text đến cơ sở tri thức.", "Hình 4.1. Kết quả ánh xạ triệu chứng.", "Hình 4.2. Kết quả suy luận trên KB.", "Hình 4.3. Giao diện web với kết quả tra cứu mẫu."):
        paragraph(doc, line)
    doc.add_heading("DANH MỤC TỪ VIẾT TẮT", level=1)
    table(doc, ["Từ viết tắt", "Ý nghĩa"], [
        ["ASR", "Automatic Speech Recognition – nhận dạng tiếng nói"],
        ["KB", "Knowledge Base – cơ sở tri thức"],
        ["IDF", "Inverse Document Frequency – trọng số nghịch tần suất"],
        ["MRR", "Mean Reciprocal Rank – hạng nghịch đảo trung bình"],
        ["TF-IDF", "Term Frequency – Inverse Document Frequency"],
    ])
    doc.add_heading("ĐỌC NHANH: HỆ THỐNG ĐANG LÀM GÌ?", level=1)
    paragraph(doc, "Người dùng đưa một đoạn giọng nói kể triệu chứng. Máy chép lại câu nói, gạch ra những triệu chứng hiểu được, rồi tra bảng liên kết bệnh–triệu chứng. Kết quả là tên bệnh được xếp đầu cùng các liên kết dùng để xếp hạng. Người xem có thể kiểm tra lại từng bước thay vì chỉ nhận một tên bệnh từ mô hình hộp đen.")
    paragraph(doc, "Ví dụ trong demo: “I have a runny nose, chills, and a sore throat” → sổ mũi, ớn lạnh, đau họng → ba mã E_181, E_94, E_97 → ba quan hệ has_symptom của Influenza trong SQLite → cúm đứng đầu. Cơ sở tri thức là danh sách bệnh, dữ kiện, quan hệ và nguồn; SQLite lưu chúng, còn hàm xếp hạng dùng chúng để suy luận. Mô hình học tương phản chỉ giúp hiểu câu mô tả triệu chứng.")
    doc.add_heading("TÓM TẮT", level=1)
    paragraph(doc, "Đồ án xây dựng hệ cơ sở tri thức (KB) để tra cứu các bệnh có quan hệ với triệu chứng được mô tả bằng văn bản hoặc giọng nói tiếng Anh. Audio được Whisper tiny.en chép lời; một bộ mã hóa văn bản nhỏ học bằng mục tiêu tương phản ánh xạ từng cụm mô tả sang mã triệu chứng. Hai JSON DDXPlus là nguồn nhập; tri thức được lưu trong SQLite với thực thể bệnh, dữ kiện, quan hệ và nguồn gốc. Bộ suy luận xếp hạng bệnh bằng mức độ khớp các triệu chứng và giải thích từng liên kết được sử dụng. Hệ thống chỉ phục vụ minh họa học thuật, không chẩn đoán.")
    paragraph(doc, f"Ca minh họa: audio nói “{AUDIO['transcript']}” được chép lời, ánh xạ sang ba triệu chứng và tra quan hệ trong KB; bệnh đứng đầu là cúm (Influenza), điểm khớp {AUDIO['top_score']:.2f}. Trên {MODEL['test']['contrastive']['count']} câu test tự biên soạn, ánh xạ tương phản đạt Top-1 {MODEL['test']['contrastive']['top1']:.1%}, so với TF-IDF {MODEL['test']['tfidf']['top1']:.1%}. Trên {KB['sample_size']:,} ca DDXPlus mô phỏng, Recall@5 là {KB['idf_weighted_overlap']['recall_at_5']:.1%}. Điểm khớp chỉ đo quan hệ trong KB, không phải xác suất mắc bệnh.")
    doc.add_heading("CHƯƠNG 1. ĐẶT VẤN ĐỀ", level=1)
    doc.add_heading("1.1. Bối cảnh và vấn đề đặt ra", level=2)
    paragraph(doc, "Tên đề tài cũ ghi “contractive learning in multiple modal data with voice and text”. Thuật ngữ phù hợp với mục tiêu ghép cặp biểu diễn là “contrastive learning” (học tương phản). Sau góp ý của giảng viên, đồ án chọn một bài toán có cơ sở tri thức rõ ràng: từ mô tả triệu chứng, truy vết các bệnh có quan hệ với triệu chứng đó và nêu lý do tra cứu.")
    paragraph(doc, "Câu hỏi nghiên cứu gồm: (1) biểu diễn văn bản được học tương phản có ánh xạ lời nói tự nhiên sang mã triệu chứng tốt hơn TF-IDF trên tập câu giữ lại hay không; (2) cơ sở tri thức và bộ suy luận có truy vết được kết quả xếp hạng hay không; (3) audio làm phát sinh những lỗi gì so với đầu vào text.")
    paragraph(doc, "Phạm vi: bản demo tiếng Anh, 15 loại triệu chứng được chọn để học ánh xạ, 49 bệnh trong KB DDXPlus. Đầu ra là danh sách bệnh có quan hệ phù hợp, không phải kết luận bệnh của người dùng. Khi chỉ có một triệu chứng hoặc câu bị phủ định/không ánh xạ được, hệ thống yêu cầu thêm dữ kiện.")

    doc.add_heading("CHƯƠNG 2. CƠ SỞ LÝ THUYẾT", level=1)
    doc.add_heading("2.1. Hệ cơ sở tri thức", level=2)
    paragraph(doc, "Một hệ cơ sở tri thức gồm kho tri thức có cấu trúc, bộ suy luận và cơ chế giải thích. Đồ án dùng SQLite để lưu Disease, Evidence, DiseaseEvidence và Source. Hai quan hệ has_symptom và has_antecedent tách triệu chứng khỏi tiền sử; mỗi hàng quan hệ có khóa ngoại và tham chiếu tới nguồn DDXPlus v2. Bộ suy luận hiện dùng quan hệ has_symptom để chấm điểm, còn phần giải thích trả lại các mã và câu hỏi chuẩn đã khớp. Mạng nơ-ron chỉ ánh xạ câu nói sang mã triệu chứng, không dự đoán bệnh trực tiếp.")
    doc.add_heading("2.2. Mạng nơ-ron và học tương phản", level=2)
    paragraph(doc, "Câu mô tả và câu hỏi chuẩn của triệu chứng được biến thành vector TF-IDF ký tự 2–4 gram. Một lớp tuyến tính có thể học (PyTorch Linear) chiếu mỗi vector xuống 64 chiều; sau đó chuẩn hóa L2 và so bằng tích vô hướng, tương đương cosine similarity. Tham số được cập nhật bằng Adam và lan truyền ngược.")
    paragraph(doc, "Với câu q có mã triệu chứng đúng s+, ta tối thiểu hóa L = -log[ exp(sim(q,s+)/τ) / Σs exp(sim(q,s)/τ) ], trong đó τ = 0,1. Mẫu dương là câu và nhãn đúng; các nhãn triệu chứng khác là mẫu âm. Đây là học tương phản có giám sát trên văn bản, không phải huấn luyện trực tiếp cặp audio–text. Tư tưởng so khớp biểu diễn hai phía tham khảo từ CLIP [3], còn cấu hình 64 chiều và dữ liệu nhỏ là thiết kế của đồ án.")
    doc.add_heading("2.3. Nghiên cứu liên quan: iKnow-audio", level=2)
    paragraph(doc, "Olvera và cộng sự [6] kết hợp CLAP, mô hình học tương phản audio–text trực tiếp, với đồ thị tri thức âm thanh AKG và RotatE để làm giàu prompt rồi xếp hạng lại nhãn âm thanh. Bài báo đánh giá trên sáu bộ dữ liệu âm thanh môi trường và công bố mã/AKG. Đây là tham chiếu phương pháp gần với đề tài nhưng khác miền ứng dụng: bài này không tra bệnh từ giọng nói; bản demo của đồ án dùng ASR rồi mới học tương phản trên văn bản. Do đó không xem kết quả của iKnow-audio là kết quả thực nghiệm của đồ án.")
    doc.add_heading("2.4. Nhận dạng giọng nói", level=2)
    paragraph(doc, "Whisper tiny.en chuyển waveform audio sang câu tiếng Anh [4]. Hệ thống kiểm tra audio dài tối đa 60 giây, đọc bằng soundfile, chuyển về mono và lấy mẫu lại 16 kHz nếu cần. Bản chép lời đi vào cùng một pipeline text, nên có thể phân tích riêng lỗi ASR và lỗi ánh xạ triệu chứng.")

    doc.add_heading("CHƯƠNG 3. DỮ LIỆU VÀ THIẾT KẾ HỆ THỐNG", level=1)
    doc.add_heading("3.1. Dữ liệu và biểu diễn tri thức", level=2)
    paragraph(doc, f"DDXPlus English v2 [1, 2] được công bố theo giấy phép CC-BY, chứa {KB_META['counts']['disease']} bệnh, {KB_META['counts']['evidence']} loại dữ kiện và tập ca bệnh mô phỏng. Hai tệp release_conditions.json và release_evidences.json là nguồn để xây KB SQLite. Bản nhập có {KB_META['counts']['has_symptom']} quan hệ bệnh–triệu chứng và {KB_META['counts']['has_antecedent']} quan hệ bệnh–tiền sử. Tập test có 134.529 ca. Dữ liệu không có audio và không đại diện cho người bệnh thật.")
    table(doc, ["Tệp / trường", "Vai trò"], [
        ["release_evidences.json", "Mã E_*, câu hỏi tiếng Anh, loại triệu chứng/tiền sử, các giá trị tùy chọn."],
        ["release_conditions.json", "Tên bệnh, ICD-10, tập mã symptoms và antecedents."],
        ["release_test_patients.zip", "Nhãn PATHOLOGY và các mã EVIDENCES của ca mô phỏng để đánh giá."],
        ["data/phrases.csv", "75 câu do nhóm viết: train 45, validation 15, test 15; thuộc 15 mã triệu chứng."],
    ])
    doc.add_heading("3.2. Lược đồ lưu trữ, nguồn gốc và kiểm tra toàn vẹn", level=2)
    table(doc, ["Bảng", "Khóa và thuộc tính", "Vai trò"], [
        ["source", "id; dataset; version; url; SHA-256 của hai JSON", "Truy vết phiên bản và tệp nguồn của mọi bản ghi."],
        ["disease", "name (PK); icd10; severity; source_id (FK)", "Thực thể bệnh."],
        ["evidence", "code (PK); question_en; data_type; is_antecedent; source_id (FK)", "Từ điển dữ kiện chuẩn."],
        ["disease_evidence", "disease_name (FK); evidence_code (FK); relation; source_id (FK)", "Quan hệ has_symptom hoặc has_antecedent."],
    ])
    paragraph(doc, "Quy trình nhập: kiểm tra MD5 và kích thước khi tải DDXPlus v2; tính SHA-256 của hai JSON; tạo SQLite tạm; thêm nguồn, bệnh, dữ kiện rồi quan hệ; chạy foreign_key_check và integrity_check; so số hàng với dữ liệu gốc; cuối cùng thay thế tệp DB bằng thao tác nguyên tử. Nếu một mã tham chiếu không tồn tại, khóa ngoại chặn việc nhập. Suy luận đọc KB từ SQLite rồi giữ bản chụp trong bộ nhớ; DB là nơi lưu trữ có phiên bản, còn hàm rank là bộ suy luận riêng.")
    doc.add_picture(str(ARTIFACTS / "kb_schema.png"), width=Cm(16))
    caption(doc, "Hình 3.1. Lược đồ KB SQLite: thực thể, quan hệ và nguồn gốc dữ liệu.")
    doc.add_heading("3.3. Quy tắc suy luận và cài đặt", level=2)
    paragraph(doc, "Ví dụ xuyên suốt: audio nói “I have a runny nose, chills, and a sore throat.” Whisper chép câu này; bộ ánh xạ nhận E_181 (sổ mũi), E_94 (ớn lạnh) và E_97 (đau họng). Trong bảng disease_evidence, cả ba mã đều có quan hệ has_symptom với Influenza. Vì vậy cúm đứng đầu danh sách; người xem có thể mở từng liên kết và nguồn DDXPlus để kiểm tra. Đây là phép tra quan hệ, không phải bằng chứng người nói mắc cúm.")
    doc.add_picture(str(ARTIFACTS / "pipeline.png"), width=Cm(16))
    caption(doc, "Hình 3.2. Luồng audio/text đến cơ sở tri thức và bộ suy luận.")

    paragraph(doc, "Pipeline text tách câu tại “and”, “but” hoặc dấu câu. Cụm chứa phủ định đơn giản (“no”, “not”, “without”, “don't”) bị bỏ qua. Với cụm còn lại, mô hình tương phản trả tối đa ba nhãn; chỉ nhận nhãn có cosine từ 0,4 và có từ nội dung giao với câu hỏi/phrase huấn luyện. Bước neo từ vựng hạn chế các câu ngoài chủ đề được mô hình gán điểm cao. Giới hạn của luật này được ghi rõ trong Chương 5.")
    paragraph(doc, "Với tập triệu chứng dương tính Q và tập triệu chứng của bệnh d là S(d), điểm xếp hạng: score(d) = Σ[s∈Q∩S(d)] IDF(s) / Σ[s∈Q] IDF(s), trong đó IDF(s) = 1 + log[(N+1)/(df(s)+1)]. N = 49; df(s) là số bệnh gắn với s. Điểm nằm trong [0,1], không phải xác suất mắc bệnh. Nếu có nhiều bệnh cùng điểm cao, demo báo số lượng đồng điểm và yêu cầu thêm triệu chứng.")
    table(doc, ["Thành phần", "Chức năng"], [
        ["download_data.py", "Tải dữ liệu DDXPlus v2 và kiểm tra kích thước, MD5."],
        ["kb_store.py", "Nhập SQLite, kiểm tra khóa ngoại/toàn vẹn, lưu SHA-256 và truy vấn quan hệ có nguồn."],
        ["symptom_model.py", "Huấn luyện projection tương phản, lưu mô hình, đo TF-IDF/contrastive."],
        ["kb.py", "Tra từ khóa, nhận audio/text, ánh xạ mã, xếp hạng và in liên kết KB."],
        ["evaluate_kb.py", "Đánh giá xếp hạng trên 1.000 ca test chọn bằng reservoir sampling, seed 7."],
        ["app.py; web/index.html", "Giao diện web cục bộ để nhập text hoặc tải audio, kiểm tra bản chép lời và xem giải thích."],
    ])
    paragraph(doc, "Giao diện chạy trên trình duyệt tại 127.0.0.1. Người dùng tải audio, xem và sửa bản chép lời trước khi tra cứu. Kết quả hiện mã triệu chứng, số ứng viên, bệnh đồng điểm và các liên kết giải thích. Mục Khám phá cơ sở tri thức cho phép chọn bệnh để xem trực tiếp quan hệ has_symptom/has_antecedent và nguồn trong SQLite. File audio tạm được xóa sau khi chép lời.")

    doc.add_heading("CHƯƠNG 4. DEMO VÀ KẾT QUẢ THỰC NGHIỆM", level=1)
    doc.add_heading("4.1. Ánh xạ câu mô tả sang triệu chứng", level=2)
    paragraph(doc, "Tập 75 câu được tự biên soạn từ 15 mã triệu chứng DDXPlus; với mỗi mã có 3 câu train, 1 câu validation và 1 câu test. TF-IDF và mô hình tương phản dùng cùng 15 nhãn ứng viên. Chọn checkpoint ở epoch 5 theo Top-1 validation; tập test không dùng để chọn epoch.")
    table(doc, ["Tập", "Phương pháp", "Số câu", "Top-1", "Top-3"], [
        ["Validation", "TF-IDF", 15, f"{MODEL['val']['tfidf']['top1']:.1%}", f"{MODEL['val']['tfidf']['top3']:.1%}"],
        ["Validation", "Tương phản", 15, f"{MODEL['val']['contrastive']['top1']:.1%}", f"{MODEL['val']['contrastive']['top3']:.1%}"],
        ["Test", "TF-IDF", 15, f"{MODEL['test']['tfidf']['top1']:.1%}", f"{MODEL['test']['tfidf']['top3']:.1%}"],
        ["Test", "Tương phản", 15, f"{MODEL['test']['contrastive']['top1']:.1%}", f"{MODEL['test']['contrastive']['top3']:.1%}"],
    ])
    doc.add_picture(str(ARTIFACTS / "model_metrics.png"), width=Cm(15.5))
    caption(doc, "Hình 4.1. Top-1 ánh xạ triệu chứng; mẫu test nhỏ nên chỉ có giá trị minh họa.")
    paragraph(doc, "Hai lỗi Top-1 của mô hình thuần: “throat soreness” bị chọn là khó thở; từ “experiencing” trùng với câu hỏi chuẩn của nhãn này có thể góp phần gây sai. “I think I might vomit” bị chọn là nôn nhiều lần thay vì buồn nôn. Bước neo từ vựng sửa được lỗi thứ nhất, không sửa được lỗi thứ hai. Đây là lý do cần cho người dùng xem và chỉnh kết quả.")
    doc.add_heading("4.2. Xếp hạng bệnh trên DDXPlus", level=2)
    paragraph(doc, f"Từ {KB['total_test_rows']:,} ca test, lấy mẫu ngẫu nhiên đều {KB['sample_size']:,} ca bằng reservoir sampling với seed {KB['seed']}. Chỉ dùng mã triệu chứng dương tính trong EVIDENCES; các giá trị phân loại chi tiết không được sử dụng. Nhãn PATHOLOGY của bộ dữ liệu được dùng làm mốc đánh giá, không phải chân lý lâm sàng.")
    table(doc, ["Cách xếp hạng", "Top-1", "Recall@5", "MRR"], [
        ["Đếm khớp", f"{KB['unweighted_overlap']['top1']:.1%}", f"{KB['unweighted_overlap']['recall_at_5']:.1%}", f"{KB['unweighted_overlap']['mrr']:.4f}"],
        ["IDF có trọng số", f"{KB['idf_weighted_overlap']['top1']:.1%}", f"{KB['idf_weighted_overlap']['recall_at_5']:.1%}", f"{KB['idf_weighted_overlap']['mrr']:.4f}"],
    ])
    doc.add_picture(str(ARTIFACTS / "kb_metrics.png"), width=Cm(15.5))
    caption(doc, "Hình 4.2. Kết quả bộ suy luận có trọng số trên 1.000 ca mô phỏng.")
    paragraph(doc, "Hai cách xếp hạng cho cùng các chỉ số trên mẫu này. Do đó không có bằng chứng rằng thêm IDF cải thiện kết quả ở thiết lập hiện tại. Top-1 chỉ là vị trí trong danh sách 49 bệnh và bị ảnh hưởng bởi quy tắc phá hòa theo tên bệnh.")
    doc.add_heading("4.3. Thử đường audio và giao diện", level=2)
    paragraph(doc, f"Tệp {AUDIO['file']} là giọng tổng hợp tiếng Anh. Khi tải lên, Whisper chép “{AUDIO['transcript']}”, khớp câu tạo mẫu; bộ ánh xạ nhận {', '.join(AUDIO['mapped_codes'])}. Có {AUDIO['disease_candidates']} bệnh khớp ít nhất một triệu chứng. Influenza (cúm) đứng đầu duy nhất, điểm {AUDIO['top_score']:.2f}, vì KB ghi nhận cả ba quan hệ has_symptom. Điểm này chỉ nói 3/3 triệu chứng đầu vào có liên kết với bệnh trong KB. Các bệnh khác vẫn có thể liên quan; một clip tổng hợp không đủ đánh giá ASR trên người thật.")
    doc.add_picture(str(ARTIFACTS / "web_demo.png"), width=Cm(15.5))
    caption(doc, "Hình 4.3. Demo ca sổ mũi, ớn lạnh, đau họng: cúm đứng đầu và ba liên kết KB làm căn cứ.")
    doc.add_heading("4.4. Kiểm chứng cơ sở tri thức", level=2)
    paragraph(doc, "Phép kiểm tra tự động tái nhập SQLite từ JSON, so danh sách triệu chứng của một bệnh với nguồn, kiểm số hàng theo từng loại quan hệ và thử chèn liên kết tới bệnh không tồn tại để xác nhận khóa ngoại từ chối. Phép đánh giá xếp hạng trên 1.000 ca được chạy lại sau khi chuyển sang SQLite; Top-1, Recall@5 và MRR giữ nguyên. Điều này kiểm chứng tính tương đương của đường đọc KB mới ở mức các chỉ số đã đo, không chứng minh hệ thống có giá trị chẩn đoán lâm sàng.")

    doc.add_heading("CHƯƠNG 5. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", level=1)
    doc.add_heading("5.1. Kết luận", level=2)
    paragraph(doc, "Đồ án đã có KB bệnh–triệu chứng có thể truy vết, bộ suy luận giải thích được liên kết, mô hình ánh xạ văn bản được học bằng loss tương phản, đầu vào text/audio và giao diện demo. Kết quả trên tập câu tự biên soạn cho thấy mô hình tương phản tốt hơn TF-IDF ở Top-1 test, nhưng mẫu chỉ có 15 câu. Kết quả KB chỉ đo trên ca DDXPlus mô phỏng.")
    doc.add_heading("5.2. Hạn chế và hướng phát triển", level=2)
    paragraph(doc, "Giới hạn quan trọng: (1) audio mẫu là giọng tổng hợp; chưa đánh giá nhiều người nói, tiếng ồn hoặc giọng Việt; (2) bộ học chỉ biết 15 mã triệu chứng; (3) tách phủ định và tách câu còn đơn giản; (4) câu nhiều nghĩa có thể ánh xạ sai; (5) dữ liệu gốc mô phỏng và chỉ bao phủ 49 bệnh; (6) mô hình tương phản hoạt động sau ASR, chưa học trực tiếp từ cặp audio–text. Hướng mở rộng là thêm audio tự ghi có nhãn, phân loại phủ định tốt hơn, mở rộng mã triệu chứng và thử mô hình tương phản audio–text trực tiếp.")
    paragraph(doc, "Vì những giới hạn trên, phần mềm luôn hiện cảnh báo: kết quả chỉ để minh họa tra cứu tri thức, không dùng để chẩn đoán hoặc tư vấn điều trị.")

    doc.add_heading("TÀI LIỆU THAM KHẢO", level=1)
    refs = [
        "[1] Fansi Tchango et al. (2022), DDXPlus: A New Dataset For Automatic Medical Diagnosis, NeurIPS. https://proceedings.neurips.cc/paper_files/paper/2022/hash/cae73a974390c0edd95ae7aeae09139c-Abstract.html",
        "[2] Mila, DDXPlus official dataset and schema. https://mila-iqia.github.io/ddxplus/ ; https://github.com/mila-iqia/ddxplus/blob/main/README.md",
        "[3] Radford et al. (2021), Learning Transferable Visual Models From Natural Language Supervision. https://arxiv.org/abs/2103.00020",
        "[4] Radford et al. (2022), Robust Speech Recognition via Large-Scale Weak Supervision. https://arxiv.org/abs/2212.04356",
        "[5] Class Notebook, Hệ cơ sở tri thức, GS. TSKH. Nguyen Hung Son. https://docs.google.com/document/d/178WxWWl8ii-IhaX_OsyYahE6RBi8wMpceHipnPVwz_c/edit",
        "[6] Olvera, M., et al. (2025). iKnow-audio: Integrating Knowledge Graphs with Audio-Language Models. EMNLP 2025, 34683–34700. https://doi.org/10.18653/v1/2025.emnlp-main.1759",
    ]
    for ref in refs:
        paragraph(doc, ref)

    doc.add_heading("PHỤ LỤC: HƯỚNG DẪN CHẠY", level=1)
    for command in [
        "py -3.11 -m pip install -r requirements.txt",
        "py -3.11 download_data.py",
        "py -3.11 kb_store.py",
        "py -3.11 symptom_model.py",
        "py -3.11 evaluate_kb.py",
        "py -3.11 evaluate_audio.py",
        "py -3.11 app.py",
        "py -3.11 kb.py audio samples/influenza_demo.mp3",
    ]:
        paragraph(doc, command, "List Bullet")
    paragraph(doc, "Chạy trong thư mục dự án. Lần đầu Whisper có thể cần tải trọng số tiny.en. Tệp mẫu dùng giọng tổng hợp; khi thuyết trình nên ghi âm giọng người thật để minh họa thêm.")

    output = ROOT / "Bao_cao_do_an_HCSTT.docx"
    doc.save(output)
    print(output)


if __name__ == "__main__":
    main()
