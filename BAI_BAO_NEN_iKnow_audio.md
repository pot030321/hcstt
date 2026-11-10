# Bài báo nền cho đồ án Hệ cơ sở tri thức

## 1. Bài báo được chọn

**Olvera, M., Wang, C., Stamatiadis, P., Richard, G., & Essid, S. (2025). _iKnow-audio: Integrating Knowledge Graphs with Audio-Language Models_. EMNLP 2025, 34683–34700. DOI: [10.18653/v1/2025.emnlp-main.1759](https://doi.org/10.18653/v1/2025.emnlp-main.1759).** [Bài báo/PDF chính thức](https://aclanthology.org/2025.emnlp-main.1759/); [mã nguồn và AKG](https://github.com/michelolzam/iknow-audio).

Đây là **bài báo nghiên cứu hoàn chỉnh, đã công bố tại EMNLP**, phù hợp với T10 – Neural Networks trong [Class Notebook](https://docs.google.com/document/d/178WxWWl8ii-IhaX_OsyYahE6RBi8wMpceHipnPVwz_c/edit). Bài báo có vấn đề, mô hình, lược đồ tri thức, công thức, 6 bộ dữ liệu đánh giá, baseline, thí nghiệm loại bỏ thành phần, phân tích lỗi và giới hạn. Nó gần nhất với yêu cầu “audio + text + học tương phản + cơ sở tri thức” trong các nguồn mình kiểm tra.

**Khác biệt quyết định:** iKnow-audio xử lý **âm thanh môi trường** (tiếng chó, còi xe, mưa…), không xử lý lời bệnh nhân và không tra bệnh. Muốn bám sát bài báo cần đổi bài toán ứng dụng. Không được đổi tên bài toán rồi giữ nguyên số liệu DDXPlus hiện có.

## 2. Cơ sở tri thức ở đâu trong bài báo?

AKG (*Audio-centric Knowledge Graph*) là tập các bộ ba **(thực thể đầu, quan hệ, thực thể cuối)**. Ví dụ `(dog, produces, barking)` hoặc `(siren, can be heard in, city)`. Các thực thể và quan hệ được tạo từ cây nhãn SALT và bổ sung bằng LLM, sau đó lọc tự động và kiểm tra thủ công. Bài báo báo cáo đồ thị thô 51.254 bộ ba và tập đã lọc 20.387 bộ ba; phụ lục tách 18.348 bộ ba dùng để huấn luyện và 2.039 bộ ba kiểm thử. [Mục 4 và phụ lục của bài báo](https://aclanthology.org/2025.emnlp-main.1759.pdf).

Kho tri thức này phục vụ hai mục đích: (1) truy vấn quan hệ có sẵn để giải thích ngữ cảnh âm thanh; (2) học embedding đồ thị bằng RotatE để dự đoán liên kết còn thiếu. Công thức chấm bộ ba của RotatE là `φ(h,r,t) = −‖h ∘ r − t‖₂`. Đây là phần **suy luận tri thức** của bài, khác với việc chỉ lưu nhãn âm thanh trong một file.

## 3. Mạng nơ-ron và học tương phản làm gì?

CLAP dùng **audio encoder** và **text encoder** đã được huấn luyện tương phản trên cặp âm thanh–mô tả, tạo hai vector trong cùng không gian. Với audio đầu vào `a` và nhãn chữ `c`, baseline xếp hạng theo `cos(φ_A(a), φ_T(c))`. Đây mới là học tương phản **đa phương thức trực tiếp**, không cần ASR. [Mục 3.2](https://aclanthology.org/2025.emnlp-main.1759.pdf).

iKnow-audio lấy vài nhãn CLAP đầu tiên, dùng AKG/RotatE tìm các thực thể liên quan, ghép chúng vào prompt chữ, rồi dùng text encoder của CLAP chấm lại với audio. Điểm gốc và điểm prompt mở rộng được gộp bằng log-sum-exp. Có thể hiển thị đường chứng minh: `audio → nhãn CLAP → bộ ba AKG/đuôi dự đoán → prompt mở rộng → điểm mới`. [Mục 3.3 và Algorithm 1](https://aclanthology.org/2025.emnlp-main.1759.pdf).

## 4. Thực nghiệm của bài báo để học cách viết đồ án

| Phép đo | Thiết kế của tác giả | Kết quả cần ghi đúng nguồn |
| --- | --- | --- |
| Dự đoán liên kết trên AKG | So TransE, TransH, TransR, ComplEx, R-GCN, RotatE; đồ thị thô và đã lọc | RotatE trên đồ thị đã lọc đạt MRR **56,1%** (bảng 1) |
| Nhận diện âm thanh zero-shot | So CLAP, CLAP + prompt tri thức không gộp, và CLAP + KG đầy đủ; 6 bộ dữ liệu | ESC-50 Hit@1 **93,2% → 95,4%**; TUT2017 **37,8% → 47,9%** (bảng 2) |
| Phân tích thành phần | Bỏ bước gộp điểm, so raw/pruned graph, phân tích từng loại quan hệ và từng lớp | Cho thấy tri thức giúp một số lớp nhưng làm giảm vài lớp khác; không chỉ chọn ví dụ tốt |

Các số trên là **kết quả của tác giả**, chưa phải kết quả tái lập của đồ án. Nguồn: [bảng 1–2 và phần phân tích](https://aclanthology.org/2025.emnlp-main.1759.pdf).

## 5. Kiểm tra khả năng tái lập

| Tài nguyên | Tình trạng đã kiểm tra | Ý nghĩa |
| --- | --- | --- |
| [Bài báo EMNLP](https://aclanthology.org/2025.emnlp-main.1759/) | Công khai toàn văn, phương pháp và kết quả | Đủ để viết nghiên cứu liên quan, công thức và thiết kế phép đo |
| [Repo iKnow-audio](https://github.com/michelolzam/iknow-audio) | Có `AKG_dataset` và `KGE_training` | Có thể kiểm tra bộ ba và huấn luyện KGE |
| Mã CLAP-KG end-to-end trong repo | **Chưa thấy** script suy luận/đánh giá CLAP-KG trong danh sách file công khai hiện tại; README nhắc `requirements.txt` nhưng cây file hiển thị không có | Không được hứa “chạy một lệnh tái lập toàn bộ bảng 2”; phần ghép CLAP–AKG cần tự cài đặt và ghi rõ |
| [ESC-50 chính thức](https://github.com/karolpiczak/ESC-50) | 2.000 clip WAV, 50 lớp, 5 fold | Bộ dữ liệu audio thật, nhỏ đủ để làm thí nghiệm đầu tiên; giấy phép phi thương mại |
| [LAION-CLAP](https://github.com/LAION-AI/CLAP) | Mã và checkpoint công khai; có ví dụ zero-shot ESC-50 | Có baseline audio–text thực sự để tái lập |

## 6. Hướng đồ án khả thi nếu chọn bài báo này

**Tên đề tài nên đổi:** “Kết hợp học tương phản audio–text và đồ thị tri thức để nhận diện âm thanh môi trường có giải thích”. Đây là hướng đúng cả T10 (mạng nơ-ron) lẫn học phần Hệ cơ sở tri thức (AKG, RotatE/suy luận quan hệ). Đầu vào audio là **âm thanh**, không phải câu nói về bệnh.

1. **Bài toán và dữ liệu:** dùng ESC-50 (2.000 clip, 50 lớp, 5 fold), AKG pruned của tác giả và mô hình LAION-CLAP có sẵn. Cố định phiên bản, checksum, cách ánh xạ 50 tên lớp ESC-50 với thực thể AKG. Nếu lớp không có trong AKG, báo độ phủ và cách xử lý; không tự gán quan hệ tùy tiện.
2. **Baseline:** CLAP zero-shot với cùng template chữ cho 50 lớp. Đo Hit@1, Hit@3, MRR theo từng fold, trung bình và độ lệch chuẩn. Lưu dự đoán từng clip để phân tích lỗi.
3. **Cơ sở tri thức:** nhập bộ ba AKG vào bảng `entity`, `relation`, `triple`, `source`; kiểm tra trùng, khóa ngoại, phân bố quan hệ và provenance. Demo xem được đường `nhãn âm thanh → quan hệ → thực thể liên quan`.
4. **Đề xuất/đối chứng:** (A) CLAP gốc; (B) CLAP + láng giềng AKG có sẵn; (C) CLAP + láng giềng do RotatE dự đoán. Giữ cùng clip và cùng fold. Nếu chưa huấn luyện được RotatE, chỉ công bố A–B và ghi C là chưa thực hiện.
5. **Đánh giá tri thức:** trên tập bộ ba test của AKG, đo Hit@1/3/10 và MRR theo bộ ba, có lọc các đuôi đúng khác khi đánh giá. Đừng trộn test triples vào graph huấn luyện.
6. **Phân tích:** báo lớp tăng/giảm, trường hợp tri thức sai hoặc không có, ảnh hưởng top-k, thời gian chạy, giới hạn của CLAP và KG. Demo một audio đúng, một audio sai và nguyên nhân trong graph.
7. **Tài liệu nộp:** câu hỏi nghiên cứu, tổng quan 3–5 công trình liên quan, lược đồ AKG, mô hình/công thức, quy trình dữ liệu, các bảng baseline/ablation có seed và môi trường, hình minh họa, phân tích sai, đe dọa tính hợp lệ, tài liệu tham khảo và video/giao diện demo.

## 7. Đối chiếu với bản đồ án tra bệnh hiện tại

Bản hiện tại đã có SQLite DDXPlus, luật xếp hạng và audio → Whisper → text → ánh xạ triệu chứng, nhưng **không tái lập iKnow-audio** và **không có học tương phản audio–text trực tiếp**. DDXPlus là ca mô phỏng, còn audio mẫu là giọng tổng hợp. Thêm SQLite là cải thiện lưu trữ/truy vết, chưa giải quyết thiếu sót khoa học của đề tài “đa phương thức”. Vì vậy, nếu chọn iKnow-audio làm bài báo nền, phải xây thí nghiệm mới trên ESC-50/AKG/CLAP và viết lại báo cáo, slide, demo theo thí nghiệm đó. Giữ nguyên biểu đồ/số liệu DDXPlus rồi đổi tên đề tài sẽ sai phương pháp.
