# AudioGraph Lab — đồ án Hệ cơ sở tri thức

Đây là nhánh thí nghiệm **âm thanh môi trường** dựa trên hướng iKnow-audio. Bản tra bệnh từ lời nói ở thư mục cha được giữ riêng; hai bài toán không dùng chung dữ liệu hoặc kết quả.

## Cơ sở tri thức ở đâu?

`data/akg.sqlite3` chứa các bộ ba `(head, relation, tail)` của Audio-centric Knowledge Graph (AKG), cùng `split`, tệp nguồn và dòng nguồn. `graph.py` nhập từ AKG TSV của nhóm tác giả. `experiment.py` chỉ lấy bộ ba `train` để viết prompt có ngữ cảnh; `AKG_test.tsv` được giữ riêng cho đánh giá dự đoán liên kết của `kge.py`. Giao diện cho xem chính bộ ba và dòng nguồn đã tác động đến từng nhãn.

SQLite là lớp lưu trữ và truy vết. Phương pháp nghiên cứu là so sánh CLAP zero-shot với CLAP có bổ sung prompt từ AKG, và đánh giá riêng mô hình RotatE-style trên AKG test.

## Dữ liệu và nguồn

| Tài nguyên | Nguồn | Kích thước / SHA-256 |
|---|---|---|
| AKG | [iKnow-audio GitHub](https://github.com/michelolzam/iknow-audio), commit `2123229f4046146b732b77d9020e55abaedc4336` | `iknow_source.zip` 839.709 B; `7180e20d80909c3f527ca1b183c9c694815d95fec6b0a09e420bac4e12f1add7` |
| ESC-50 | [ESC-50 GitHub](https://github.com/karolpiczak/ESC-50) | `ESC-50.zip` 645.695.005 B; `805afc618aff80eff0641d51311647871fead5807da68bb18e43a27db47a79ce` |
| CLAP checkpoint | [LAION-CLAP checkpoint](https://huggingface.co/lukewys/laion_clap/blob/main/630k-audioset-best.pt) | `630k-audioset-best.pt` 1.863.587.645 B; `8053c9775516af2f4902e1e8281e356cc1bf7a85e8b761908170767b77c3f037` |

AKG có 18.348 bộ ba train và 2.039 bộ ba test. ESC-50 có 2.000 WAV, 50 lớp, 5 fold. 33/50 lớp có ít nhất một quan hệ thuộc bộ quy tắc prompt hiện tại. Không tạo alias thủ công.

## Kết quả đã chạy trên máy này

| ESC-50 đủ 2.000 clip | CLAP gốc | CLAP + AKG |
|---|---:|---:|
| Hit@1 | 91,95% | 92,40% |
| Hit@3 | 98,60% | 98,75% |
| Hit@5 | 99,70% | 99,70% |
| MRR | 0,95294 | 0,95544 |

Ở Hit@1, 11 clip được sửa đúng và 2 clip từ đúng thành sai; kiểm định McNemar chính xác p=0,02246. Mức tăng chỉ 0,45 điểm phần trăm và phụ thuộc prompt/AKG được chọn. Thí nghiệm RotatE-style trên 1.771/2.039 bộ ba test có thực thể từng thấy đạt Hit@10 18,97%, thấp hơn baseline tần suất 31,28%; đây là kết quả âm, không phải tái lập chỉ số của bài báo.

API upload đã nhận WAV ESC-50 thật và trả HTTP 200: clip `1-100032-A-0.wav` được xếp `dog`, kèm bộ ba nguồn `AKG_pruned.tsv:12096`. Lần nạp checkpoint đầu trên CPU mất khoảng 37 giây; lần đánh giá toàn bộ 2.000 clip mất 1.184 giây sau khi nạp mô hình. Số liệu chi tiết nằm trong `results/summary_full.json`, `results/predictions_full.csv` và `results/kge_metrics.json`.

## Chạy trên máy hiện tại

Tại thư mục gốc `hcstt`:

```powershell
py -3.11 iknow_audio/graph.py
.\iknow_audio\.venv\Scripts\python.exe iknow_audio\experiment.py evaluate --per-class 1
.\iknow_audio\.venv\Scripts\python.exe iknow_audio\experiment.py evaluate --per-class 5
.\iknow_audio\.venv\Scripts\python.exe iknow_audio\kge.py
.\iknow_audio\.venv\Scripts\python.exe iknow_audio\make_deliverables.py
.\iknow_audio\.venv\Scripts\python.exe iknow_audio\web.py
```

Mở <http://127.0.0.1:8766>, tải một clip trong `iknow_audio/data/ESC-50/audio`. Lần đầu cần nạp checkpoint 1,86 GB vào RAM. `--per-class 0` chạy toàn bộ 2.000 clip; `5` chọn một clip mỗi fold cho từng lớp (250 clip). Dự đoán từng clip ở `results/predictions_*.csv`; tổng hợp ở `results/summary_*.json`; Word/slide được tạo từ số đo mới nhất có sẵn.

Để cài môi trường mới: dùng Python 3.11, tạo venv và chạy `python -m pip install -r requirements.txt`. Các wheel trong `data/wheels` chỉ là cache cài đặt trên máy này. Trước khi chạy, tải checkpoint CLAP vào `data/630k-audioset-best.pt`, tải `ESC-50.zip` vào `data/` và giải nén để có `data/ESC-50/audio/*.wav`; các liên kết nguồn và SHA-256 ở bảng trên. GitHub đang từ chối upload Git LFS vì tài khoản vượt hạn mức, nên checkpoint, ZIP và WAV giải nén chưa có trong repo. Các kết quả đã đo vẫn được lưu ở `results/`.

## Phương pháp và giới hạn

CLAP gốc dùng prompt `The sound of {class}.`. Biến thể AKG thêm một câu `{head} {relation} {tail}` từ tập train, lấy theo thứ tự quan hệ cố định trong `experiment.py`; embedding lớp là chuẩn hóa của `0.75 × prompt gốc + 0.25 × prompt AKG`. Cùng 50 lớp và cùng audio dùng cho cả hai cấu hình. Trọng số không được chọn theo kết quả test.

Thí nghiệm RotatE-style trong `kge.py` là bản huấn luyện gọn để kiểm tra dự đoán tail, không phải mã huấn luyện RotatE đầy đủ của nhóm tác giả. Các bộ ba test chứa thực thể chưa thấy ở train được loại khỏi đánh giá transductive và đếm rõ. Chỉ số trong bài [iKnow-audio, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1759/) là kết quả của tác giả, không phải kết quả bản này.
