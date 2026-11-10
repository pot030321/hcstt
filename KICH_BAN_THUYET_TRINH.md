# Kịch bản thuyết trình và demo

**Thời lượng:** 8–10 phút trình bày, 3 phút demo. Mở [slide](Slide_do_an_HCSTT.pptx), [báo cáo](Bao_cao_do_an_HCSTT.docx) và chạy `py -3.11 app.py`.

## Câu chuyện cần nói rõ

Một người nói bằng tiếng Anh: “I have a runny nose, chills, and a sore throat.” Phần mềm chép lời, nhận **sổ mũi, ớn lạnh, đau họng**, rồi tra cơ sở tri thức. Trong bảng quan hệ bệnh–triệu chứng, cả ba triệu chứng đều liên kết với **Influenza (cúm)**. Cúm đứng đầu với điểm khớp 1,00. Điểm này là mức khớp dữ kiện đã nhập, **không phải xác suất mắc cúm**.

## Nói theo slide

1. **Vấn đề:** Người dùng kể triệu chứng bằng giọng nói, nhưng máy cần mã triệu chứng chuẩn để tra bệnh. Mục tiêu là gợi ý bệnh có liên quan và giải thích vì sao.
2. **Cơ sở tri thức:** SQLite chứa 49 bệnh, 223 dữ kiện, 605 quan hệ `has_symptom`, 283 quan hệ `has_antecedent` và nguồn DDXPlus v2. Chỉ quan hệ `has_symptom` tham gia phép xếp hạng hiện tại.
3. **Mô hình học:** Whisper biến audio thành text. Mô hình học tương phản ghép câu mô tả với mã triệu chứng. Đồ án học tương phản ở **bước văn bản**, sau nhận dạng giọng nói; chưa học trực tiếp trên cặp audio–text.
4. **Suy luận:** Từ mã triệu chứng, hệ thống tìm các liên kết trong KB, tính điểm theo tỷ lệ triệu chứng khớp có trọng số và hiện từng liên kết làm căn cứ.
5. **Thực nghiệm:** Trên 15 câu test tự viết, Top-1 ánh xạ tăng từ 66,7% TF-IDF lên 86,7% tương phản. Trên 1.000 ca DDXPlus mô phỏng, Recall@5 đạt 96,1%. Mẫu nhỏ và dữ liệu mô phỏng nên chưa suy ra hiệu quả lâm sàng.
6. **Kết luận:** Có một luồng audio → text → mã triệu chứng → KB → bệnh gợi ý có thể kiểm tra lại từng bước.

## Demo trực tiếp

1. Mở `http://127.0.0.1:8765/`; bấm **Chạy audio mẫu: sổ mũi, ớn lạnh, đau họng**. Đây là giọng tổng hợp tiếng Anh.
2. Chỉ vào bản chép lời và ba mã `E_181`, `E_94`, `E_97`. Nói tên bệnh **cúm (Influenza)** ngay khi kết quả xuất hiện.
3. Mở phần giải thích: cả ba quan hệ `has_symptom` có trong KB. Cho thấy điểm 1,00 đo mức khớp của ba dữ kiện, không phải chẩn đoán.
4. Mở **Khám phá cơ sở tri thức**, chọn Influenza để xem dữ kiện và nguồn DDXPlus.
5. Nếu cần minh họa sự mơ hồ, thử `I have a fever and a cough`: nhiều bệnh đồng điểm; hệ thống yêu cầu thêm dữ kiện.

Nếu trình duyệt lỗi, chạy `py -3.11 kb.py audio samples/influenza_demo.mp3` để xem cùng luồng trên terminal.

## Trả lời câu hỏi thường gặp

- **JSON hay database mới là cơ sở tri thức?** JSON là nguồn dữ liệu DDXPlus. Cơ sở tri thức vận hành là các thực thể và quan hệ đã nhập vào SQLite, có nguồn, khóa ngoại và bộ suy luận. SQLite là phương tiện lưu; tri thức nằm ở bệnh, triệu chứng và quan hệ có nghĩa giữa chúng.
- **Cúm có chắc đúng không?** Không. Đây là bệnh đứng đầu theo ba triệu chứng đã nhận trong KB. Các bệnh khác có thể liên quan; điểm 1,00 không phải xác suất.
- **Đa phương thức ở đâu?** Đầu vào có audio và text; audio được chuyển sang text bằng Whisper. Thí nghiệm học tương phản chỉ thực hiện trên text, vì DDXPlus không có audio gốc.
- **Audio thật đã được kiểm chưa?** Chưa đánh giá có hệ thống. Audio mẫu là giọng tổng hợp; muốn đánh giá thực tế cần nhiều người nói, nhiễu và nhãn độc lập.
