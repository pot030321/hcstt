# Đề cương đồ án Hệ cơ sở tri thức

## 1. Tên đề tài và ý tưởng

**Tên đề xuất:** Ứng dụng học tương phản trong hệ cơ sở tri thức tra cứu bệnh từ mô tả triệu chứng bằng giọng nói.

**Tên tiếng Anh:** Contrastive Text Representation for Voice-Based Symptom Retrieval over a Disease Knowledge Base.

Thuật ngữ cần sửa trong tên cũ là **contrastive learning** (học tương phản), không phải *contractive learning*. Sau khi nhận audio, hệ thống chuyển lời nói thành văn bản, ánh xạ các cụm mô tả của người dùng tới mã triệu chứng chuẩn, rồi dùng các quan hệ bệnh–triệu chứng trong cơ sở tri thức để trả về các bệnh liên quan cùng phần giải thích. Đây là hệ thống **tra cứu phục vụ học tập**, không kết luận chẩn đoán.

Đề tài được ghi trong mục **T10 – Neural Networks** của [Class Notebook](https://docs.google.com/document/d/178WxWWl8ii-IhaX_OsyYahE6RBi8wMpceHipnPVwz_c/edit). Vì vậy phần học tương phản và biểu diễn bằng mạng nơ-ron phải được giải thích rõ; cơ sở tri thức và bộ suy luận phải được trình bày thành thành phần riêng của hệ thống.

## 2. Câu hỏi nghiên cứu và mục tiêu

**Câu hỏi:** Một biểu diễn văn bản được huấn luyện theo học tương phản có giúp ánh xạ lời mô tả triệu chứng sang các triệu chứng chuẩn tốt hơn tìm kiếm từ khóa hay không? Sau bước ánh xạ đó, hệ thống dùng tri thức bệnh–triệu chứng như thế nào để xếp hạng và giải thích kết quả?

**Đầu ra phải có:**

1. Nhập câu mô tả triệu chứng bằng **audio hoặc văn bản**.
2. Hiện bản chép lời để người dùng kiểm tra và sửa nếu nhận dạng giọng nói sai.
3. Hiện các triệu chứng đã ánh xạ, mã triệu chứng và độ tương đồng.
4. Tra cứu tối đa 5 bệnh liên quan; mỗi bệnh kèm các triệu chứng khớp, các triệu chứng liên quan khác trong KB và nguồn dữ liệu.
5. Nếu không nhận ra triệu chứng hoặc độ tương đồng quá thấp, thông báo chưa đủ dữ kiện thay vì đoán bệnh.

## 3. Cơ sở tri thức ở đây là gì?

Cơ sở tri thức (knowledge base, KB) là tập **thực thể, thuộc tính và quan hệ đã được biểu diễn có cấu trúc**, để máy có thể truy vấn và giải thích. Trong đề tài này:

| Thành phần | Biểu diễn | Ví dụ minh họa |
| --- | --- | --- |
| Bệnh | `condition_id`, tên, mã ICD-10 nếu có, mức độ trong dữ liệu | `Myasthenia gravis` |
| Triệu chứng | `evidence_id`, câu hỏi/mô tả chuẩn, loại dữ kiện | `E_...` |
| Quan hệ | `condition_id -> has_symptom -> evidence_id` | bệnh A có triệu chứng X |
| Tiền sử/yếu tố liên quan | `condition_id -> has_antecedent -> evidence_id` | bệnh A có tiền sử Y |
| Truy vết | phiên bản dữ liệu, mã quan hệ, triệu chứng khớp | dùng để giải thích kết quả |

**Bộ suy luận** nhận tập triệu chứng đã chuẩn hóa, đi qua các quan hệ `has_symptom` và xếp hạng các bệnh theo mức độ khớp. Một cách chấm điểm đơn giản cho đồ án là:

`score(d) = sum(IDF(s) for s in symptoms_user ∩ symptoms_d) / sum(IDF(s) for s in symptoms_user)`

Trong đó `IDF(s) = 1 + log((N + 1) / (df(s) + 1))`: triệu chứng xuất hiện ở ít bệnh hơn sẽ có sức phân biệt cao hơn. `N` là số bệnh trong KB; `df(s)` là số bệnh có triệu chứng `s`. Đây là **điểm xếp hạng**, không phải xác suất mắc bệnh. Chỉ đưa triệu chứng *được nói là có* vào tử số; “không sốt” không được biến thành “có sốt”. Nếu muốn xét triệu chứng phủ định, phải xử lý riêng và chỉ dùng khi người dùng nói rõ.

Ví dụ dòng suy luận: `audio -> "I have a cough and fever" -> {cough, fever} -> bệnh có các quan hệ triệu chứng tương ứng -> top 5 + các quan hệ đã khớp`. Chính phần quan hệ và suy luận này làm đề tài thuộc **Hệ cơ sở tri thức**; mô hình học tương phản là bộ ánh xạ ngôn ngữ tự nhiên vào các mã tri thức.

## 4. Bộ dữ liệu đã chọn: DDXPlus

Chọn **[DDXPlus bản tiếng Anh](https://mila-iqia.github.io/ddxplus/)** của nhóm tác giả tại Mila. Bộ dữ liệu công bố khoảng **1,3 triệu ca bệnh mô phỏng, 49 bệnh và 223 loại dữ kiện** (triệu chứng hoặc tiền sử), có tệp train/validation/test. Bản công bố có giấy phép CC-BY và [bài báo gốc](https://arxiv.org/abs/2205.09148). Tải từ liên kết **English figshare** trên trang dự án hoặc DOI `10.6084/m9.figshare.22687585`.

| Tệp | Vai trò trong đồ án |
| --- | --- |
| `release_evidences.json` | Từ điển mã triệu chứng/tiền sử, câu hỏi tiếng Anh, loại nhị phân hoặc nhiều giá trị. |
| `release_conditions.json` | **Dữ liệu quan hệ để dựng KB:** bệnh, mã ICD-10, danh sách mã triệu chứng và tiền sử liên quan. |
| `release_train_patients.zip` | Ca mô phỏng để chọn ví dụ, thống kê và xây dựng baseline. |
| `release_validate_patients.zip` | Chọn ngưỡng ánh xạ/xếp hạng trên tập phát triển. |
| `release_test_patients.zip` | Đánh giá cuối cùng bằng các ca chưa dùng để chỉnh mô hình. |

**Điểm phải nói rõ khi báo cáo:** DDXPlus **không có audio** và không có câu người bệnh nói tự nhiên; đây là dữ liệu có cấu trúc và ca mô phỏng. Audio demo cần tự ghi âm một tập nhỏ từ các câu mô tả dựa trên ca test, có bản chép lời và nhãn triệu chứng để kiểm tra riêng bước nhận dạng. Vì dữ liệu tiếng Anh, bản đầu tiên nhận **giọng nói tiếng Anh**; chỉ thêm tiếng Việt khi đã xây dựng và kiểm tra bảng thuật ngữ song ngữ. Không coi kết quả trên DDXPlus là độ chính xác chẩn đoán trên người thật.

## 5. Nền tảng cần trình bày

### 5.1. Mạng nơ-ron và biểu diễn

Giải thích đầu vào văn bản được biến thành vector (*embedding*) bằng bộ mã hóa mạng nơ-ron. Các câu có cùng ý nghĩa được kỳ vọng nằm gần nhau trong không gian vector. Nêu vai trò của encoder, pooling, chuẩn hóa vector và cosine similarity.

### 5.2. Học tương phản

Với câu mô tả `q` và nhãn triệu chứng đúng `s+`, xem `(q, s+)` là cặp dương; các nhãn khác trong batch là cặp âm. Mục tiêu InfoNCE:

`L = -log[ exp(sim(q,s+)/tau) / sum_s exp(sim(q,s)/tau) ]`

`tau` là tham số nhiệt độ; `sim` là cosine similarity. Cách cài đặt hiện tại biến câu thành TF-IDF ký tự 2–4 gram, học một lớp chiếu tuyến tính xuống 64 chiều bằng loss tương phản với 15 nhãn triệu chứng, rồi so với TF-IDF trên cùng tập test. Bộ câu gồm 75 câu tiếng Anh tự biên soạn (45 train, 15 validation, 15 test); đây là thí nghiệm nhỏ, chưa phải mô hình y khoa tổng quát.

### 5.3. Biểu diễn tri thức và suy luận

Hai JSON DDXPlus là **nguồn nhập**; tri thức chạy thực tế được lưu trong SQLite `data/knowledge_base.sqlite3` qua bốn bảng `source`, `disease`, `evidence`, `disease_evidence`. Khóa ngoại kiểm tra mã liên kết, bảng nguồn lưu phiên bản/URL/SHA-256, hai loại quan hệ `has_symptom` và `has_antecedent` được tách rõ. Bộ suy luận hiện dùng quan hệ triệu chứng, nạp từ SQLite vào bộ nhớ rồi tính điểm; giao diện cho xem các quan hệ và nguồn. Xem [README](README.md) và [kb_store.py](kb_store.py).

### 5.4. Nhận dạng giọng nói

Audio được chuyển thành văn bản bằng mô hình ASR có sẵn. ASR chỉ là lớp nhập liệu; phần học tương phản ở bản này diễn ra **giữa văn bản lời nói đã chép và nhãn triệu chứng**. Không gọi đây là huấn luyện tương phản trực tiếp giữa audio và text. Nếu thầy yêu cầu đúng nghĩa *multimodal contrastive learning*, cần thêm một thí nghiệm encoder audio–encoder text trên các cặp audio–nhãn triệu chứng đã thu thập.

## 6. Kiến trúc và hướng cài đặt

```text
Audio -> ASR -> bản chép lời -> tách câu có/không có triệu chứng
                                  -> encoder văn bản -> mã triệu chứng DDXPlus
                                  -> KB bệnh–triệu chứng -> xếp hạng + giải thích
Text  ----------------------------^
```

**Thứ tự làm để có demo hoàn chỉnh:**

1. Nạp hai JSON DDXPlus, kiểm tra mọi mã triệu chứng của bệnh đều tồn tại trong từ điển. Tạo KB và trang xem bệnh/triệu chứng/quan hệ.
2. Làm nhánh nhập text trước: câu mô tả -> tìm mã triệu chứng bằng TF-IDF/từ khóa -> KB xếp hạng. Đây là baseline hoạt động được.
3. Thêm embedding học tương phản và đo cải thiện ở bước ánh xạ triệu chứng. Chỉ sau khi đo đạt yêu cầu mới chọn mô hình cho demo.
4. Thêm nhánh audio -> ASR -> cùng một pipeline text. Cho phép sửa bản chép lời.
5. Giao diện local đơn giản: một ô text, một nút ghi/tải audio, bảng triệu chứng nhận diện và bảng bệnh kèm lý do. Không cần sinh câu trả lời bằng LLM.

**Ví dụ cách giải thích trên màn hình:** “Bệnh A được xếp hạng vì KB DDXPlus liên kết bệnh này với triệu chứng X và Y; điểm khớp 0,74 theo công thức xếp hạng.” Không hiển thị điểm này như 74% khả năng mắc bệnh.

## 7. Thực nghiệm cần có trong bài thu hoạch

| Câu hỏi | Phép đo |
| --- | --- |
| Ánh xạ câu mô tả sang mã triệu chứng có đúng không? | Top-1 và Top-3 trên tập câu có nhãn; so TF-IDF với projection học tương phản. |
| Tra bệnh từ triệu chứng có đưa đúng bệnh của ca mô phỏng vào danh sách không? | Top-1, Recall@5, MRR trên tập test DDXPlus; nêu rõ đây là phép đo trên dữ liệu mô phỏng. |
| Audio làm giảm chất lượng bao nhiêu? | Chạy cùng câu qua text chuẩn và audio-ASR; so chênh lệch F1 ánh xạ triệu chứng và Recall@5. |
| Hệ thống giải thích được kết quả không? | Chọn 5 ca đúng, 5 ca sai; liệt kê mã triệu chứng, quan hệ KB và nguyên nhân sai. |

**Chia dữ liệu:** Giữ train/validation/test gốc của DDXPlus. Bộ câu mô tả/ghi âm tự tạo phải tách các câu hoặc người nói đã dùng để chỉnh mô hình khỏi bộ kiểm tra cuối. Không dùng nhãn bệnh trong test để thiết kế lại công thức sau khi xem kết quả.

**Giới hạn:** Ca DDXPlus là mô phỏng; mới thử một audio giọng tổng hợp, chưa có đánh giá giọng người thật; biểu thức triệu chứng tự nhiên, phủ định và mức độ nặng có thể bị nhận sai. Giao diện ghi “tra cứu tham khảo, không thay thế đánh giá y tế”.

## 8. Dàn ý báo cáo và slide

**Báo cáo:**

1. Mở đầu: vấn đề, mục tiêu, giới hạn tra cứu.
2. Cơ sở lý thuyết: mạng nơ-ron, embedding, học tương phản, ASR, KB, suy luận.
3. Dữ liệu và xây dựng KB: sơ đồ thực thể–quan hệ, trường dữ liệu, nguồn và phiên bản DDXPlus.
4. Thiết kế và cài đặt: pipeline, công thức xếp hạng, xử lý thiếu dữ kiện, giao diện.
5. Thực nghiệm: bộ đo, baseline, bảng số liệu, ví dụ đúng/sai, phân tích lỗi.
6. Kết luận: đã đạt gì, giới hạn trên dữ liệu mô phỏng, hướng mở rộng.

**Slide đã tạo (13 trang):** Bài toán; KB là gì; DDXPlus; mô hình học tương phản; pipeline; quy tắc suy luận; hai bảng kết quả; demo audio; kịch bản demo; giới hạn; tài liệu tham khảo.

**Demo 3 phút:** Nhập câu text -> hiện triệu chứng và bệnh có giải thích; mở audio cùng nội dung -> kiểm tra ASR -> so kết quả; nhập câu không đủ triệu chứng -> hệ thống từ chối đoán. Chuẩn bị sẵn audio dự phòng để demo ổn định.

## 9. Kế hoạch 4 tuần và tiêu chí hoàn thành

| Tuần | Việc phải xong | Minh chứng |
| --- | --- | --- |
| 1 | Đọc tài liệu nền, lấy DDXPlus, dựng schema KB và baseline text. | Sơ đồ quan hệ, truy vấn bệnh–triệu chứng chạy được. |
| 2 | Tạo câu mô tả có nhãn, thử ánh xạ từ khóa và embedding tương phản. | Bảng Precision/Recall/F1, lỗi điển hình. |
| 3 | Thêm ASR, audio demo, bộ xếp hạng và giải thích. | Giao diện chạy local, audio -> bệnh có nguồn. |
| 4 | Đánh giá tập test, viết báo cáo, làm slide và luyện demo. | Báo cáo đủ công thức/bảng/hình/tài liệu; slide và kịch bản. |

**Hoàn thành khi:** Hệ thống có KB biểu diễn được bệnh–triệu chứng; giải thích được kết quả qua quan hệ KB; có hai đường nhập text/audio; có so sánh baseline và mô hình học tương phản trên tập giữ lại; báo cáo và slide khớp với những gì demo thực sự làm được.

## 10. Tài liệu gốc

- [Class Notebook môn Hệ cơ sở tri thức](https://docs.google.com/document/d/178WxWWl8ii-IhaX_OsyYahE6RBi8wMpceHipnPVwz_c/edit): danh sách chủ đề và tiêu chí trình bày/bài thu hoạch.
- [DDXPlus project page](https://mila-iqia.github.io/ddxplus/) và [tài liệu cấu trúc dữ liệu](https://github.com/mila-iqia/ddxplus/blob/main/README.md).
- [DDXPlus paper](https://arxiv.org/abs/2205.09148): nguồn và giới hạn của dữ liệu mô phỏng.
- [CLIP paper](https://arxiv.org/abs/2103.00020): tham khảo công thức mục tiêu tương phản.
- [CLAP paper](https://arxiv.org/abs/2206.04769): tham khảo về học tương phản trực tiếp giữa audio và text nếu mở rộng đề tài.

## 11. Phần đã cài đặt

Đã tải hai tệp JSON và tập test bản tiếng Anh DDXPlus từ Figshare, cố định ở version 2. [download_data.py](download_data.py) kiểm tra kích thước và MD5 theo metadata trước khi lưu vào `data/raw/`. Dữ liệu đã tải có 49 bệnh, 223 dữ kiện, 605 liên kết bệnh–triệu chứng và 134.529 ca test.

Chạy trong thư mục dự án:

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 download_data.py
py -3.11 symptom_model.py
py -3.11 evaluate_kb.py
py -3.11 evaluate_audio.py
py -3.11 app.py
py -3.11 kb.py search fever
py -3.11 kb.py rank E_91 E_201
py -3.11 kb.py text I have a fever and a cough
py -3.11 kb.py audio samples/fever_cough.mp3
py -3.11 make_report.py
py -3.11 make_slides.py
```

`search` tìm mã triệu chứng qua một từ khóa tiếng Anh; `rank` nhận mã đã chọn thủ công; `text` và `audio` chạy toàn bộ đường ánh xạ mô hình → KB. `audio` nhận tệp tối đa 60 giây mà `soundfile` đọc được; Whisper `tiny.en` chép lời. `app.py` mở giao diện web cục bộ tại `http://127.0.0.1:8765/` để nhập text hoặc tải audio; có thể sửa bản chép lời trước khi tra cứu.

Kết quả đã đo: Top-1 ánh xạ trên 15 câu test là 10/15 (TF-IDF) và 13/15 (học tương phản). Trên 1.000 ca mô phỏng chọn ngẫu nhiên từ tập test, Top-1 bệnh là 77,6%, Recall@5 là 96,1%, MRR là 0,8544; IDF và đếm khớp cho cùng chỉ số trên mẫu này. Audio tổng hợp `samples/fever_cough.mp3` được chép đúng, ánh xạ `E_91` và `E_201`, cho 24 ứng viên với 11 bệnh đồng điểm cao nhất. Các kết quả được lưu trong `artifacts/` và trình bày trong [báo cáo Word](Bao_cao_do_an_HCSTT.docx), [slide](Slide_do_an_HCSTT.pptx).

Trước khi nộp cần thay audio tổng hợp bằng các bản ghi người thật và đánh giá trên chúng; hệ thống mới hỗ trợ 15 triệu chứng tiếng Anh và không dùng để chẩn đoán.
