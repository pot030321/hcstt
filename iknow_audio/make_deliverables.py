"""Generate a report and slide deck from measured ESC-50 results."""

import csv
import json
import sqlite3
from collections import defaultdict
from math import comb
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor as DocColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt as SlidePt

from graph import DB, ROOT


RESULTS = ROOT / "results"
NAVY = RGBColor(17, 46, 57)
TEAL = RGBColor(7, 111, 91)
PALE = RGBColor(235, 247, 242)


def pct(x):
    return f"{100*x:.2f}%"


def paired_test(rows, k):
    gains = sum(int(row["baseline_rank"]) > k >= int(row["kg_rank"]) for row in rows)
    losses = sum(int(row["kg_rank"]) > k >= int(row["baseline_rank"]) for row in rows)
    n = gains + losses
    p = min(1.0, 2 * sum(comb(n, i) for i in range(min(gains, losses) + 1)) / 2**n) if n else 1.0
    return gains, losses, p


def chart(summary, name):
    labels = ["Hit@1", "Hit@3", "Hit@5", "MRR"]
    base = [summary["baseline"][key] for key in ("hit1", "hit3", "hit5", "mrr")]
    kg = [summary["kg"][key] for key in ("hit1", "hit3", "hit5", "mrr")]
    fig, ax = plt.subplots(figsize=(8, 3.7))
    xs = range(len(labels))
    ax.bar([x-.18 for x in xs], base, width=.36, label="CLAP", color="#31566a")
    ax.bar([x+.18 for x in xs], kg, width=.36, label="CLAP + AKG", color="#08715b")
    ax.set_xticks(list(xs), labels)
    ax.set_ylim(0, 1.08)
    ax.grid(axis="y", alpha=.18)
    ax.legend(frameon=False)
    ax.set_ylabel("Score")
    fig.tight_layout()
    out = RESULTS / f"metrics_{name}.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def table(doc, headers, rows):
    tab = doc.add_table(rows=1, cols=len(headers))
    tab.style = "Light Shading Accent 1"
    for cell, value in zip(tab.rows[0].cells, headers):
        cell.text = str(value)
    for values in rows:
        for cell, value in zip(tab.add_row().cells, values):
            cell.text = str(value)
    doc.add_paragraph()


def heading(doc, title, body):
    doc.add_heading(title, level=1)
    doc.add_paragraph(body)


def build_report(summary, predictions, name, kge=None):
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = sec.bottom_margin = Cm(2.2)
    sec.left_margin = Cm(3.0)
    sec.right_margin = Cm(2.0)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(13)
    normal.paragraph_format.line_spacing = 1.35
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("Hệ cơ sở tri thức  |  ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    cover = doc.add_paragraph()
    cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for value, size in [("BỘ GIÁO DỤC VÀ ĐÀO TẠO", 13), ("TRƯỜNG ĐẠI HỌC CÔNG NGHỆ TP. HỒ CHÍ MINH", 14),
                        ("BÁO CÁO ĐỒ ÁN MÔN HỌC", 18), ("HỆ CƠ SỞ TRI THỨC", 18),
                        ("PHÂN LOẠI ÂM THANH MÔI TRƯỜNG BẰNG HỌC TƯƠNG PHẢN AUDIO–TEXT VÀ ĐỒ THỊ TRI THỨC", 20)]:
        run = cover.add_run(value + "\n\n")
        run.bold = True
        run.font.size = Pt(size)
        run.font.color.rgb = DocColor(12, 86, 75)
    doc.add_paragraph("Hướng nghiên cứu dựa trên iKnow-audio (EMNLP 2025)")
    doc.add_paragraph("Học viên: ....................................................    Lớp: ........................")
    doc.add_paragraph("Giảng viên hướng dẫn: ...............................................................")
    doc.add_paragraph("TP. Hồ Chí Minh, tháng 11 năm 2026")
    doc.add_page_break()

    heading(doc, "TÓM TẮT", "Đồ án khảo sát liệu tri thức dạng bộ ba từ Audio-centric Knowledge Graph (AKG) có cải thiện phân loại âm thanh môi trường zero-shot của mô hình học tương phản CLAP hay không. Hệ thống nhận trực tiếp tệp audio, tạo embedding âm thanh, so khớp với văn bản nhãn ESC-50, rồi thử bổ sung một quan hệ AKG vào prompt. Kết quả dưới đây là đo đạc của bản triển khai này trên mẫu ESC-50; không sao chép chỉ số trong bài báo iKnow-audio. Đây là thí nghiệm về âm thanh môi trường, không phải tra bệnh từ giọng nói.")
    doc.add_paragraph("Từ khóa: hệ cơ sở tri thức; đồ thị tri thức; học tương phản; đa phương thức; CLAP; ESC-50.")
    heading(doc, "MỤC LỤC", "1. Đặt vấn đề  ·  2. Cơ sở lý thuyết  ·  3. Dữ liệu và cơ sở tri thức  ·  4. Thiết kế hệ thống  ·  5. Thực nghiệm  ·  6. Kết quả và thảo luận  ·  7. Kết luận  ·  Tài liệu tham khảo  ·  Phụ lục.")

    heading(doc, "1. ĐẶT VẤN ĐỀ", "Mô hình audio–text như CLAP biểu diễn âm thanh và mô tả bằng vector trong cùng không gian, nhưng có thể nhầm các âm thanh gần nhau. Câu hỏi nghiên cứu: bổ sung ngữ cảnh được truy xuất từ AKG có thay đổi độ chính xác phân loại và khả năng giải thích hay không? Đóng góp của đồ án là triển khai đường đi audio thật → CLAP → truy vấn AKG → xếp hạng và đánh giá có đối chứng. SQLite là phương tiện lưu, truy vấn và truy vết tri thức; bản thân việc dùng SQLite không được coi là đóng góp khoa học.")
    doc.add_heading("1.1. Vấn đề và giả thuyết", level=2)
    doc.add_paragraph("Âm thanh môi trường có nhiều lớp dễ chồng lấp về phổ tần và bối cảnh, ví dụ tiếng máy, phương tiện hoặc chuông báo. CLAP học liên kết audio–văn bản từ dữ liệu lớn nên có thể nhận lớp mới mà không cần huấn luyện trực tiếp trên ESC-50. Tuy nhiên, prompt chỉ chứa tên lớp thường thiếu thông tin về nguồn phát, bối cảnh và đặc tính âm học. AKG cung cấp những quan hệ đó dưới dạng có cấu trúc. Giả thuyết H1: vector văn bản có ngữ cảnh AKG làm tăng thứ hạng nhãn đúng so với prompt tên lớp. H0: việc thêm ngữ cảnh không cải thiện, hoặc làm giảm, thứ hạng. Phép đo trên cùng một tập audio được dùng để kiểm tra hai giả thuyết.")
    doc.add_paragraph("Phạm vi được giới hạn ở phân loại âm thanh môi trường bằng audio trực tiếp. Một bài toán khác của thư mục dự án là tra cứu bệnh từ lời nói bệnh nhân; pipeline đó cần ASR và dữ liệu triệu chứng, nên không được dùng để minh họa hoặc cộng gộp kết quả của iKnow-audio. Sự tách biệt này giữ đúng ý nghĩa học tương phản đa phương thức audio–text trong đề tài mới.")
    table(doc, ["Thành phần", "Vai trò"], [
        ("CLAP", "Audio encoder và text encoder đã được huấn luyện tương phản; tạo điểm tương đồng cosine."),
        ("AKG", "Lưu bộ ba (head, relation, tail), tra ngữ cảnh và dẫn nguồn theo tệp/dòng."),
        ("ESC-50", "2.000 clip 5 giây, 50 nhãn, 5 fold; dùng làm bộ kiểm tra phân loại."),
        ("Giao diện", "Tải WAV/FLAC/MP3/OGG, nghe lại và xem nhãn, điểm, bộ ba được dùng."),
    ])

    heading(doc, "2. CƠ SỞ LÝ THUYẾT", "CLAP tối ưu mục tiêu tương phản trên cặp audio–văn bản: embedding đúng cặp được kéo gần, cặp sai được đẩy xa. Với audio a và các nhãn c, baseline dự đoán argmax_c cos(f_audio(a), f_text(p_c)). Trong đồ án, p_c = ‘The sound of {c}.’. Cấu hình AKG chọn tối đa một bộ ba train cho mỗi nhãn, tạo p'_c = ‘The sound of {c}. {h} {r} {t}.’. Vector lớp là chuẩn hóa(0,75 f_text(p_c) + 0,25 f_text(p'_c)); lớp không có bộ ba giữ nguyên baseline. Hệ số được cố định trước khi kiểm tra, không tối ưu trên tập test.")
    doc.add_heading("2.1. Học tương phản audio–text", level=2)
    doc.add_paragraph("Cho batch gồm N cặp đúng (a_i, t_i). Hai encoder tạo vector đã chuẩn hóa z_i^a và z_i^t. Ma trận điểm S_ij = (z_i^a · z_j^t)/τ, với τ là nhiệt độ học được hoặc cố định khi huấn luyện. Mất mát InfoNCE hai chiều trung bình âm log xác suất cặp đúng theo hàng audio và cột văn bản. Mô hình LAION-CLAP đã được huấn luyện sẵn bằng nguyên lý này; đồ án không nhận đã huấn luyện lại mô hình. Khi suy luận, cosine giữa audio và prompt là điểm xếp hạng; điểm này không phải xác suất bệnh hay xác suất đã hiệu chuẩn.")
    doc.add_heading("2.2. Tri thức có cấu trúc và suy luận", level=2)
    doc.add_paragraph("Một bộ ba (h,r,t) là một phát biểu: h là thực thể đầu, r là quan hệ, t là thực thể cuối. Ví dụ một nguồn âm có thể ‘produces’ một kiểu âm, hoặc một sự kiện âm thanh ‘occurs in’ một bối cảnh. Trong hệ thống này, quan hệ không chỉ được lưu để hiển thị: nó được chuyển thành văn bản cho text encoder, nhờ đó có thể thay đổi vector biểu diễn của lớp và thứ hạng dự đoán. Vì các phát biểu AKG có thể nhiễu, mọi prompt được giữ liên kết đến tệp và dòng nguồn để người xem kiểm tra.")
    doc.add_paragraph("RotatE biểu diễn quan hệ như phép quay trong không gian phức: h ⊙ r ≈ t. Hàm điểm dùng khoảng cách giữa h ⊙ r và t; một bộ ba phù hợp có khoảng cách thấp. Bản RotatE-style của đồ án học từ bộ ba dương và tail âm lấy mẫu ngẫu nhiên, sau đó xếp hạng toàn bộ thực thể tail đã thấy ở train. Đây là phép đánh giá suy luận tri thức riêng, khác với bảng độ chính xác phân loại audio.")
    doc.add_heading("2.3. Công trình liên quan", level=2)
    doc.add_paragraph("LAION-CLAP cung cấp mô hình audio–text tiền huấn luyện và checkpoint để dùng zero-shot. iKnow-audio của Olvera và cộng sự (EMNLP 2025) nghiên cứu cách gắn AKG với mô hình audio–language và đánh giá trên nhiều tập âm thanh. Đồ án chọn đúng nguồn AKG công bố của họ để có thể truy vết tri thức, nhưng hiện thực prompt và huấn luyện RotatE-style gọn của riêng mình. Vì mã công khai không cung cấp một pipeline suy luận CLAP → KG hoàn chỉnh có thể chạy nguyên xi, các con số của đồ án không được trình bày như kết quả tái lập chính xác của bài báo.")
    doc.add_paragraph("Trong iKnow-audio gốc, đồ thị còn được học bằng RotatE để dự đoán quan hệ chưa quan sát. Bản này đánh giá RotatE-style như thí nghiệm riêng, nhưng nhánh phân loại audio chỉ dùng bộ ba quan sát ở train; chưa tích hợp thực thể do RotatE dự đoán vào prompt. Không nhận là tái lập đầy đủ iKnow-audio hay các chỉ số của bài báo.")

    heading(doc, "3. DỮ LIỆU VÀ CƠ SỞ TRI THỨC", "AKG do nhóm tác giả công bố được nạp từ hai tệp TSV vào SQLite. Bảng triple lưu head, relation, tail, label_name, split, source_file và source_row. Chỉ split=train được truy vấn để tạo prompt; test được giữ riêng cho thí nghiệm suy luận đồ thị. Mỗi bộ ba trả về trên giao diện có thể tra lại dòng nguồn. Nhãn ESC-50 được đổi dấu gạch dưới thành khoảng trắng và ghép với head không phân biệt hoa/thường; không tạo alias thủ công.")
    doc.add_heading("3.1. Thu nhận và kiểm tra nguồn", level=2)
    doc.add_paragraph("Dữ liệu AKG được cố định theo commit 2123229f4046146b732b77d9020e55abaedc4336 của kho tác giả; archive, ESC-50 và checkpoint được ghi SHA-256 trong README. Khi nhập, chương trình chỉ nhận các dòng có response = ‘Yes.’, gắn lại tên tệp và số dòng, tạo chỉ mục theo (head, split) để tra cứu, và assert chính xác số dòng của train/test. CSV ESC-50 được giữ nguyên filename, category và fold để kết quả từng clip có thể đối chiếu với metadata gốc.")
    doc.add_heading("3.2. Tách tập và độ phủ", level=2)
    doc.add_paragraph("Tách tập AKG phục vụ hai mục đích khác nhau. Prompt phân loại chỉ truy vấn AKG_pruned.tsv (train), tránh đưa quan hệ trong AKG_test.tsv vào quá trình xây prompt. Thí nghiệm link prediction huấn luyện trên cùng train và chấm trên test. Với ESC-50, không có bước fit theo nhãn nên cả 5 fold đều là tập kiểm tra zero-shot; bảng fold dùng để thấy biến thiên giữa các nhóm clip, không phải cross-validation của một mô hình được huấn luyện trên bốn fold còn lại.")
    with sqlite3.connect(DB) as db:
        counts = dict(db.execute("SELECT split, count(*) FROM triple GROUP BY split"))
    table(doc, ["Nguồn", "Số bộ ba", "Cách dùng"], [("AKG_pruned.tsv", counts["train"], "Tra ngữ cảnh"),
                                                         ("AKG_test.tsv", counts["test"], "Giữ riêng"),
                                                         ("ESC-50", 2000, "Đánh giá audio")])
    doc.add_paragraph(f"Độ phủ thực nghiệm: {summary['kg_covered_classes']}/50 nhãn có ít nhất một quan hệ được chọn. Các nhãn còn lại không nhận thêm tri thức, do đó điểm AKG bằng baseline ở các lớp này.")

    heading(doc, "4. THIẾT KẾ HỆ THỐNG", "Luồng xử lý: tệp audio → giải mã và chuẩn hóa trong LAION-CLAP → audio embedding → so với 50 text embedding → dự đoán baseline; song song, truy vấn AKG train → prompt có bộ ba → text embedding bổ sung → dự đoán AKG. Kết quả lưu theo từng clip trong CSV và số liệu tổng hợp trong JSON để kiểm tra lại. Giao diện HTTP chỉ mở trên 127.0.0.1:8766, giới hạn 20 MB/tệp và xóa tệp upload sau khi phân tích.")
    doc.add_heading("4.1. Tạo prompt từ đồ thị", level=2)
    doc.add_paragraph("Quy tắc chọn bộ ba được viết cố định theo thứ tự ưu tiên: produces, is sound of, emitted by, generated by, transcribed as, has timbre, has pitch, event composed of, associated with event, occurs in. Trong cùng quan hệ, chọn tail đứng đầu theo thứ tự từ điển. Chỉ chọn một bộ ba để tránh lớp có nhiều quan hệ được ưu ái do nhiều prompt hơn. Quy tắc đơn giản có thể chọn quan hệ không đại diện; đây là biến cần kiểm tra trong nghiên cứu tiếp theo, không phải một cơ chế chọn tri thức tối ưu.")
    doc.add_heading("4.2. Xếp hạng và giao diện", level=2)
    doc.add_paragraph("Embedding văn bản của 50 lớp được tạo một lần và cache; audio embedding được cache theo filename cho chạy lại thí nghiệm. Mọi phép xếp hạng dùng vector đơn vị và tích vô hướng tương đương cosine, với thứ tự nhãn cố định để xử lý điểm bằng nhau. Giao diện người dùng hiển thị nhãn baseline, top-5 của nhánh AKG, điểm cosine và bộ ba có nguồn. Upload chỉ phục vụ phiên phân tích, không lưu hồ sơ người dùng; các kết quả thử trên ESC-50 được lưu riêng theo tên clip trong CSV.")
    screenshot = RESULTS / "ui.png"
    if screenshot.exists():
        doc.add_picture(str(screenshot), width=Cm(15))
        caption = doc.add_paragraph("Hình 1. Giao diện tải audio và xem kết quả CLAP + AKG trên localhost.")
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER

    heading(doc, "5. THIẾT KẾ THỰC NGHIỆM", f"Mô hình: LAION-CLAP non-fusion, checkpoint 630k-audioset-best.pt, CPU. Bộ thử: {summary['sample_rule']} với {summary['baseline']['n']} clip. Cùng tệp audio, cùng 50 nhãn, cùng checkpoint và cùng thứ tự lớp cho hai cấu hình; khác biệt duy nhất là embedding văn bản có thêm bộ ba AKG. Hit@k là tỷ lệ nhãn đúng nằm trong k hạng đầu; MRR là trung bình 1/rank. Đây là đánh giá zero-shot, không huấn luyện lại CLAP trên ESC-50.")
    doc.add_paragraph("Mẫu per-class chọn round-robin theo fold và filename; khi chạy full thì dùng toàn bộ 2.000 clip. Báo cáo ghi đúng cỡ mẫu đang được dùng, không suy diễn từ 250 clip sang toàn bộ ESC-50. Baseline và biến thể AKG được chấm đồng thời cho từng clip nên có thể xem trực tiếp clip nào tăng hoặc giảm thứ hạng. Kết quả chênh lệch nhỏ cần đọc cùng phân tích theo clip, thay vì chỉ xem một chỉ số tổng hợp.")
    doc.add_paragraph("Công thức: Hit@k = (1/N) Σ_i 1[rank_i ≤ k], MRR = (1/N) Σ_i 1/rank_i. Fold mean và độ lệch giữa fold có thể được tính từ các bảng riêng; vì mỗi fold trong phép đo full có 400 clip, bảng fold cung cấp kiểm tra phân bố kết quả. Thời gian được tính cho vòng xử lý clip sau khi nạp mô hình, nên không đại diện cho độ trễ khởi động UI lần đầu.")
    table(doc, ["Cấu hình", "Hit@1", "Hit@3", "Hit@5", "MRR"], [
        ("CLAP gốc", pct(summary["baseline"]["hit1"]), pct(summary["baseline"]["hit3"]), pct(summary["baseline"]["hit5"]), f"{summary['baseline']['mrr']:.3f}"),
        ("CLAP + AKG", pct(summary["kg"]["hit1"]), pct(summary["kg"]["hit3"]), pct(summary["kg"]["hit5"]), f"{summary['kg']['mrr']:.3f}"),
    ])
    figure = doc.add_picture(str(chart(summary, name)), width=Cm(15))
    figure._inline.docPr.set("descr", "Biểu đồ so sánh CLAP và CLAP cộng AKG trên cùng tập ESC-50")
    caption = doc.add_paragraph("Hình 2. So sánh bốn chỉ số phân loại trên cùng bộ audio.")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fold_rows = [(fold, value["baseline"]["n"], pct(value["baseline"]["hit1"]), pct(value["kg"]["hit1"]))
                 for fold, value in summary["folds"].items()]
    table(doc, ["Fold", "Số clip", "Hit@1 CLAP", "Hit@1 CLAP + AKG"], fold_rows)
    if len(summary["folds"]) > 1:
        import statistics
        for key in ("baseline", "kg"):
            values = [value[key]["hit1"] for value in summary["folds"].values()]
            doc.add_paragraph(f"Hit@1 theo fold của {key}: trung bình {pct(statistics.mean(values))}, độ lệch chuẩn mẫu {100*statistics.stdev(values):.2f} điểm phần trăm.")
    if kge:
        doc.add_heading("5.1. Đánh giá suy luận đồ thị", level=2)
        doc.add_paragraph(f"Mô hình RotatE-style dùng embedding phức {kge['dimension']} chiều, seed {kge['seed']}, {kge['epochs']} epoch. Điểm bộ ba là 12 − Σ|h ⊙ r − t|; học bằng một tail đúng và bốn tail âm ngẫu nhiên/bộ ba. Từ {kge['test_triples']} bộ ba test, {kge['test_seen_entities']} bộ ba có cả hai thực thể từng thấy ở train và được đánh giá theo xếp hạng tail lọc. {kge['test_excluded_unseen']} bộ ba có thực thể mới không thuộc bài toán transductive và được loại, không tính là dự đoán đúng.")
        table(doc, ["Cấu hình KG", "Hit@1", "Hit@3", "Hit@10", "MRR"], [
            ("Tần suất tail theo relation", pct(kge["relation_frequency_baseline"]["hit1"]), pct(kge["relation_frequency_baseline"]["hit3"]), pct(kge["relation_frequency_baseline"]["hit10"]), f"{kge['relation_frequency_baseline']['mrr']:.3f}"),
            ("RotatE-style", pct(kge["rotate_style"]["hit1"]), pct(kge["rotate_style"]["hit3"]), pct(kge["rotate_style"]["hit10"]), f"{kge['rotate_style']['mrr']:.3f}"),
        ])
        doc.add_paragraph("RotatE-style hiện thấp hơn baseline tần suất trên tập test transductive. Điều này cho thấy việc có embedding đồ thị chưa đủ để khẳng định suy luận tốt; cách lấy mẫu âm, số epoch và tính nhiễu của AKG cần được nghiên cứu thêm.")

    heading(doc, "6. KẾT QUẢ VÀ THẢO LUẬN", f"Chênh lệch Hit@1 của biến thể AKG so với baseline là {100*(summary['kg']['hit1']-summary['baseline']['hit1']):+.2f} điểm phần trăm trên mẫu đã chọn. Thời gian vòng đánh giá (không tính thời gian nạp mô hình) là {summary['seconds']:.1f} giây. Thay đổi kết quả có thể âm, bằng 0 hoặc dương; cần đọc theo số liệu thực tế và phân tích từng clip, không suy ra lợi ích tổng quát từ mẫu nhỏ.")
    doc.add_paragraph("Bảng kết quả cần đọc theo hai câu hỏi tách biệt. Hit@1 phản ánh khả năng đưa nhãn đúng lên đầu, còn Hit@3 cho biết có đưa nhãn đúng vào một danh sách gợi ý ngắn hay không. Nếu Hit@3 tăng nhưng Hit@1 giữ nguyên, tri thức có thể chỉ đẩy nhãn đúng từ vị trí 4 xuống 3 mà chưa đủ để thay quyết định cuối. Nếu một lớp không có bộ ba theo quy tắc hiện tại, vector của lớp đó giữ nguyên; nhưng thứ hạng của nó vẫn có thể đổi do điểm của lớp khác thay đổi.")
    changed = [row for row in predictions if row["baseline"] != row["kg"]][:8]
    improved = sum(int(row["kg_rank"]) < int(row["baseline_rank"]) for row in predictions)
    worsened = sum(int(row["kg_rank"]) > int(row["baseline_rank"]) for row in predictions)
    corrected = sum(row["baseline"] != row["truth"] and row["kg"] == row["truth"] for row in predictions)
    regressed = sum(row["baseline"] == row["truth"] and row["kg"] != row["truth"] for row in predictions)
    doc.add_paragraph(f"Phân tích theo clip: {improved} clip tăng thứ hạng nhãn đúng, {worsened} clip giảm; {corrected} clip được sửa đúng top-1 và {regressed} clip từ đúng thành sai top-1. Các thay đổi này giải thích vì sao chỉ số tổng hợp có thể gần như không đổi.")
    g1, l1, p1 = paired_test(predictions, 1)
    g3, l3, p3 = paired_test(predictions, 3)
    doc.add_paragraph(f"Kiểm định McNemar chính xác trên cặp dự đoán cùng clip: tại Hit@1 có {g1} ca mới đúng, {l1} ca từ đúng thành sai (p={p1:.4f}); tại Hit@3 có {g3} ca mới lọt top-3, {l3} ca rời top-3 (p={p3:.4f}). Giá trị p mô tả mức bất cân xứng của các cặp đổi trạng thái, không chứng minh hiệu quả ngoài tập ESC-50.")
    by_class = defaultdict(list)
    for row in predictions:
        by_class[row["truth"]].append(row)
    hardest = sorted(by_class.items(), key=lambda item: (sum(row["kg"] == item[0] for row in item[1])/len(item[1]), item[0]))[:8]
    table(doc, ["Lớp khó theo AKG", "Số clip", "Đúng CLAP", "Đúng AKG"], [
        (label, len(rows), sum(row["baseline"] == label for row in rows), sum(row["kg"] == label for row in rows))
        for label, rows in hardest
    ])
    if changed:
        table(doc, ["Clip", "Nhãn thật", "CLAP", "CLAP + AKG"],
              [(row["filename"], row["truth"], row["baseline"], row["kg"]) for row in changed])
    else:
        doc.add_paragraph("Không có clip nào đổi nhãn top-1 trong mẫu hiện tại. CSV kèm theo vẫn lưu thứ hạng và điểm từng clip để tiếp tục phân tích.")
    doc.add_paragraph("Giới hạn: chọn đúng một bộ ba cho mỗi lớp và trọng số cố định 0,25 có thể bỏ sót quan hệ hữu ích hoặc đưa vào quan hệ nhiễu. Độ phủ 33/50 lớp tạo bất cân xứng giữa lớp có và không có tri thức. RotatE-style chưa được dùng để mở rộng prompt; chưa có nhiều seed hoặc khoảng tin cậy. Do đó không so trực tiếp chỉ số với iKnow-audio gốc.")
    doc.add_paragraph("Các đe dọa tính hợp lệ gồm: (i) ESC-50 có các clip ngắn và nhãn cố định, chưa chắc đại diện cho ghi âm ngoài đời; (ii) phép ghép tên lớp bằng chuỗi bỏ sót biến thể ngôn ngữ; (iii) prompt được chọn theo thứ tự ưu tiên thủ công có thể kém phù hợp với từng lớp; (iv) checkpoint LAION-CLAP có thể đã gặp các kiểu âm thanh tương tự trong tiền huấn luyện, nên không thể khẳng định điều kiện ‘chưa từng thấy’ theo nghĩa tuyệt đối. Đồ án giữ nguyên các hạn chế này trong kết luận.")

    heading(doc, "7. KẾT LUẬN", "Đồ án đã hiện thực đầu vào audio thật, mô hình đối sánh audio–text trực tiếp, cơ sở tri thức AKG truy vấn được và một thí nghiệm có baseline, ablation và dữ liệu dự đoán từng clip. RotatE-style được đánh giá riêng trên bộ ba test có thực thể đã thấy. Hướng tiếp theo là chuẩn hóa alias nhãn có kiểm chứng, thử nhiều prompt theo quan hệ và đưa thực thể dự đoán từ RotatE vào nhánh audio để đo tác động thực sự.")
    heading(doc, "TÀI LIỆU THAM KHẢO", "[1] Olvera et al. (2025), iKnow-audio: Integrating Knowledge Graphs with Audio-Language Models, EMNLP, https://aclanthology.org/2025.emnlp-main.1759/\n[2] LAION-AI, CLAP, https://github.com/LAION-AI/CLAP\n[3] Piczak, ESC-50, https://github.com/karolpiczak/ESC-50\n[4] Olvera et al., AKG source and KGE training code, https://github.com/michelolzam/iknow-audio")
    heading(doc, "PHỤ LỤC: TÁI LẬP", "Từ thư mục iknow_audio: chạy python graph.py để nhập AKG; chạy python experiment.py evaluate --per-class 5 để đánh giá; chạy python web.py và mở http://127.0.0.1:8766 để demo. Dữ liệu gốc và checkpoint có checksum trong README.md. predictions_*.csv chứa từng dự đoán; summary_*.json chứa số liệu tổng hợp.")
    out = ROOT / f"Bao_cao_iKnow_audio_{name}.docx"
    doc.save(out)
    return out


def add_text(slide, value, x, y, w, h, size=22, color=NAVY, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.text = value
    for p in tf.paragraphs:
        p.font.name = "Arial"
        p.font.size = SlidePt(size)
        p.font.bold = bold
        p.font.color.rgb = color
    return box


def add_slide(prs, title, items):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(.14))
    band.fill.solid(); band.fill.fore_color.rgb = TEAL; band.line.fill.background()
    add_text(slide, title, .65, .4, 12, .75, 30, TEAL, True)
    for i, item in enumerate(items):
        y = 1.45 + i * (5.2/max(len(items), 1))
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(.65), Inches(y), Inches(12), Inches(min(1.1, 4.7/max(len(items), 1))))
        shape.fill.solid(); shape.fill.fore_color.rgb = PALE; shape.line.fill.background()
        add_text(slide, item, .9, y+.14, 11.5, min(.9, 4.4/max(len(items), 1)), 20)
    add_text(slide, f"Hệ cơ sở tri thức · ESC-50 · {len(prs.slides):02d}", .7, 7.15, 11, .2, 10)
    return slide


def build_slides(summary, name, kge=None):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    add_slide(prs, "Học tương phản audio–text và đồ thị tri thức", ["Đồ án Hệ cơ sở tri thức · Hướng nghiên cứu iKnow-audio", "Demo: audio thật → CLAP → AKG → giải thích", "Học viên: .................................. · 11/2026"])
    add_slide(prs, "Câu hỏi nghiên cứu", ["CLAP zero-shot phân loại âm thanh môi trường như thế nào?", "Bộ ba AKG có thay đổi Hit@1, Hit@3 và MRR không?", "Mỗi kết quả có thể truy về tri thức nguồn hay không?"])
    add_slide(prs, "Nền tảng: iKnow-audio", ["Olvera et al., EMNLP 2025: CLAP + Audio-centric Knowledge Graph + RotatE", "Đồ án tái lập thu gọn bằng bộ ba AKG đã quan sát; chưa huấn luyện RotatE", "Âm thanh môi trường, không phải giọng nói tra bệnh"])
    add_slide(prs, "Dữ liệu và cơ sở tri thức", ["ESC-50: 2.000 clip, 50 lớp, 5 fold", "AKG train: 18.348 bộ ba; test riêng: 2.039", f"Quan hệ có thể dùng: {summary['kg_covered_classes']}/50 nhãn; lưu trong SQLite kèm nguồn/dòng"])
    add_slide(prs, "Pipeline", ["Audio → encoder CLAP → vector a", "50 prompt nhãn → encoder CLAP → 50 vector văn bản", "AKG train → một bộ ba/nhãn → prompt mở rộng → xếp hạng và giải thích"])
    add_slide(prs, "Công thức và đối chứng", ["CLAP gốc: argmax cosine(audio, prompt nhãn)", "CLAP + AKG: chuẩn hóa(0,75 vector nhãn + 0,25 vector prompt có bộ ba)", "Giữ nguyên audio, 50 lớp, checkpoint và thứ tự lớp"])
    add_slide(prs, "Thiết kế thực nghiệm", [f"Mẫu: {summary['sample_rule']}; n = {summary['baseline']['n']}", "CLAP non-fusion, checkpoint 630k-audioset-best.pt; CPU", "Hit@1 / Hit@3 / Hit@5 / MRR; lưu từng dự đoán CSV"])
    add_slide(prs, "Kết quả đo trên máy", [f"CLAP gốc: Hit@1 {pct(summary['baseline']['hit1'])}; Hit@3 {pct(summary['baseline']['hit3'])}; MRR {summary['baseline']['mrr']:.3f}",
                                          f"CLAP + AKG: Hit@1 {pct(summary['kg']['hit1'])}; Hit@3 {pct(summary['kg']['hit3'])}; MRR {summary['kg']['mrr']:.3f}",
                                          f"Chênh lệch Hit@1: {100*(summary['kg']['hit1']-summary['baseline']['hit1']):+.2f} điểm phần trăm"])
    visual = add_slide(prs, "So sánh trên cùng audio", [])
    visual.shapes.add_picture(str(chart(summary, name)), Inches(1.3), Inches(1.2), width=Inches(10.7))
    add_slide(prs, "Đánh giá theo fold", [f"Fold {f}: n={v['baseline']['n']}; CLAP {pct(v['baseline']['hit1'])}; AKG {pct(v['kg']['hit1'])}" for f,v in summary["folds"].items()])
    if kge:
        add_slide(prs, "Suy luận tri thức: RotatE-style", [f"Train {kge['train_triples']} bộ ba; test transductive {kge['test_seen_entities']}/{kge['test_triples']}",
                                                       f"Baseline tần suất: Hit@10 {pct(kge['relation_frequency_baseline']['hit10'])}; MRR {kge['relation_frequency_baseline']['mrr']:.3f}",
                                                       f"RotatE-style: Hit@10 {pct(kge['rotate_style']['hit10'])}; MRR {kge['rotate_style']['mrr']:.3f}"])
    add_slide(prs, "Demo giao diện", ["Mở http://127.0.0.1:8766 và tải một WAV của ESC-50", "Nghe lại clip; xem top-5 nhãn và điểm", "Bấm vào quan hệ được dẫn nguồn: AKG_pruned.tsv:dòng"])
    screenshot = RESULTS / "ui.png"
    if screenshot.exists():
        preview = add_slide(prs, "Giao diện bản chạy", [])
        preview.shapes.add_picture(str(screenshot), Inches(1.05), Inches(1.2), width=Inches(11.2))
    add_slide(prs, "Giới hạn và hướng tiếp", ["33/50 nhãn có ngữ cảnh theo quy tắc quan hệ; bộ ba có thể nhiễu", "Trọng số 0,25 cố định; cần kiểm tra nhiều prompt và seed", "Tiếp theo: tích hợp dự đoán RotatE vào prompt rồi đánh giá audio"])
    add_slide(prs, "Kết luận", ["Đã chạy audio thật qua hai encoder CLAP và truy vấn AKG", "Có baseline, ablation, số liệu theo clip và khả năng truy vết", "Nguồn: Olvera et al. (EMNLP 2025), LAION-CLAP, ESC-50"])
    out = ROOT / f"Slide_iKnow_audio_{name}.pptx"
    prs.save(out)
    return out


if __name__ == "__main__":
    summaries = sorted(RESULTS.glob("summary_*.json"),
                       key=lambda p: 100 if p.stem == "summary_full" else int(p.stem.split("_")[1].replace("perclass", "")))
    if not summaries:
        raise SystemExit("Run experiment.py evaluate first; report must use measured data")
    source = summaries[-1]
    name = source.stem.removeprefix("summary_")
    summary = json.loads(source.read_text(encoding="utf-8"))
    with (RESULTS / f"predictions_{name}.csv").open(encoding="utf-8") as handle:
        predictions = list(csv.DictReader(handle))
    kge_file = RESULTS / "kge_metrics.json"
    kge = json.loads(kge_file.read_text(encoding="utf-8")) if kge_file.exists() else None
    print(build_report(summary, predictions, name, kge))
    print(build_slides(summary, name, kge))
