# Đồ án Hệ cơ sở tri thức

**Đề tài:** Ứng dụng học tương phản trong hệ cơ sở tri thức tra cứu bệnh từ mô tả triệu chứng bằng giọng nói.

## File nộp và demo

- [Báo cáo Word](Bao_cao_do_an_HCSTT.docx)
- [Slide thuyết trình](Slide_do_an_HCSTT.pptx)
- [Kịch bản nói và demo](KICH_BAN_THUYET_TRINH.md)
- [Đề cương và phương pháp](DE_CUONG_DO_AN.md)
- [Phân tích bài báo nền iKnow-audio](BAI_BAO_NEN_iKnow_audio.md) · [PDF gốc](papers/iKnow_audio_EMNLP_2025.pdf)
- [Giao diện web cục bộ](web/index.html) (chạy bằng [app.py](app.py))

Thư mục [iknow_audio](iknow_audio/README.md) là **thí nghiệm âm thanh môi trường riêng** theo bài iKnow-audio. Demo tra bệnh ở thư mục gốc không dùng số liệu hay mô hình của thí nghiệm đó.

## Chạy trên Windows

Trong thư mục này, dùng Python 3.11. SQLite, mô hình ánh xạ, audio mẫu và Word/slide của **demo tra bệnh** đã có sẵn; để chạy demo chỉ cần:

```powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 app.py
```

Mở `http://127.0.0.1:8765/` nếu trình duyệt chưa tự mở. Bấm **Chạy audio mẫu** để nghe `samples/influenza_demo.mp3`: giọng tổng hợp nói “I have a runny nose, chills, and a sore throat.” Giao diện tự chép lời, nhận sổ mũi/ớn lạnh/đau họng và gợi ý **cúm (Influenza)**, kèm 3 quan hệ trong cơ sở tri thức. Có thể tải file MP3/WAV của bạn; hệ thống hiện bản chép lời để sửa rồi tra cứu lại. Lần đầu Whisper có thể cần tải trọng số `tiny.en`.

## Cơ sở tri thức có thể kiểm chứng

`kb_store.py` nhập hai JSON nguồn vào [data/knowledge_base.sqlite3](data/knowledge_base.sqlite3), gồm bốn bảng `source`, `disease`, `evidence`, `disease_evidence`. Bảng quan hệ có khóa ngoại và phân biệt `has_symptom` với `has_antecedent`. Bảng `source` giữ phiên bản DDXPlus, URL và SHA-256 của hai tệp nguồn. Bản nhập hiện có 49 bệnh, 223 dữ kiện, 605 quan hệ triệu chứng và 283 quan hệ tiền sử; lỗi tham chiếu mã hoặc sai số hàng sẽ làm bước nhập thất bại.

Ứng dụng đọc KB từ SQLite, nạp quan hệ vào bộ nhớ để xếp hạng và truy vết. Mục **Khám phá cơ sở tri thức** trên giao diện cho phép chọn bệnh, xem từng quan hệ và nguồn. Phép xếp hạng hiện chỉ dùng `has_symptom`; tiền sử được lưu để nghiên cứu tiếp, chưa dùng trong suy luận. Chạy kiểm tra: `py -3.11 test_kb_store.py` và `py -3.11 test_web_app.py`.

Có thể chạy không cần giao diện:

```powershell
py -3.11 kb.py text I have a runny nose, chills, and a sore throat
py -3.11 kb.py audio samples/influenza_demo.mp3
```

Để xây lại KB và mô hình từ dữ liệu gốc: `py -3.11 kb_store.py`, `py -3.11 symptom_model.py`. Nếu thiếu dữ liệu gốc, tải bằng `py -3.11 download_data.py`. Để tính lại số liệu và tạo lại tài liệu: `py -3.11 evaluate_kb.py`, `py -3.11 evaluate_audio.py`, `py -3.11 make_report.py`, `py -3.11 make_slides.py`.

**Nguồn:** [DDXPlus English](https://mila-iqia.github.io/ddxplus/), bản v2; hai JSON là nguồn để nhập KB SQLite và tập test dùng để đánh giá. DDXPlus phát hành theo CC-BY và chứa ca bệnh mô phỏng.

**Phạm vi:** 15 triệu chứng tiếng Anh được ánh xạ bằng mô hình văn bản học tương phản sau ASR. Điểm xếp hạng không phải xác suất mắc bệnh. Phần mềm chỉ dùng để học và minh họa, không dùng để chẩn đoán.

**Tài nguyên lớn của nhánh iKnow-audio:** Checkpoint CLAP 1,86 GB và ESC-50 được dẫn nguồn, kèm SHA-256 trong [hướng dẫn nhánh](iknow_audio/README.md). GitHub từ chối upload Git LFS vì repo đã vượt hạn mức LFS của tài khoản, nên hai tệp này và WAV giải nén chưa có trên repo. Các kết quả, mã nguồn và tài liệu của nhánh vẫn được đưa lên; cần tải tài nguyên theo liên kết nguồn trước khi chạy lại thí nghiệm đó.
