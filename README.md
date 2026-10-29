# real-estate-performance

Project Python phục vụ tiểu luận môn Nhập môn khoa học dữ liệu: khảo sát và
làm sạch dữ liệu bất động sản, tạo các tập dữ liệu có quy mô khác nhau.

## Cài đặt và kiểm thử

Chạy các lệnh từ thư mục gốc project trong môi trường Python của bạn:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

Các test cho script tạo dataset sử dụng dữ liệu giả, không kết nối Internet.
Test hồi quy mẫu 5.000 dòng chạy khi có `data/raw/sample_5000.csv` tại máy.

## Dữ liệu mẫu 5.000 dòng

```powershell
python -X utf8 -m scripts.clean_data
```

- Nguồn tại máy: `data/raw/sample_5000.csv`; script không sửa dữ liệu nguồn.
- Kết quả: `data/processed/cleaned_5000.csv`.
- Báo cáo: `results/cleaning_report_5000.csv`.
- Kết quả mẫu hiện tại: 5.000 dòng nguồn, loại 3 dòng thiếu trường bắt buộc,
  còn 4.997 dòng. `id` của mẫu giữ vị trí dòng nguồn, có thể có khoảng trống.

## Tạo các dataset lớn trong một lượt đọc stream

Nguồn: [Phuscca/vietnam-real-estates](https://huggingface.co/datasets/Phuscca/vietnam-real-estates),
split `train`. Script dùng `load_dataset(..., split="train", streaming=True)`
và `shuffle(seed=42, buffer_size=10000)` theo
[tài liệu streaming của Hugging Face](https://huggingface.co/docs/datasets/stream).
Chỉ giữ một batch xử lý và buffer shuffle trong bộ nhớ, không nạp toàn bộ dataset.

```powershell
python -X utf8 -m scripts.build_large_dataset --targets 50000,200000,500000
```

Ví dụ tùy chỉnh toàn bộ tham số:

```powershell
python -X utf8 -m scripts.build_large_dataset --targets 50000,200000,500000 --seed 42 --batch-size 2000 --shuffle-buffer 10000 --revision <commit-hash>
```

Thay `<commit-hash>` bằng revision thực tế, hoặc bỏ `--revision` để dùng revision
mặc định của nguồn. Có thể chạy trực tiếp `python -X utf8 scripts/build_large_dataset.py`
với cùng các tham số. `-X utf8` giúp hiển thị tiếng Việt trên terminal Windows.

| Tham số | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `--targets` | `50000,200000,500000` | Số dòng hợp lệ cần xuất; số nguyên dương, phân cách bằng dấu phẩy; tự sắp tăng và bỏ target lặp |
| `--seed` | `42` | Seed shuffle, số nguyên không âm |
| `--batch-size` | `2000` | Số dòng nguồn tối đa trong mỗi batch làm sạch |
| `--shuffle-buffer` | `10000` | Số dòng trong buffer shuffle |
| `--revision` | Không chỉ định | Commit, tag hoặc branch của dataset |
| `--progress-interval` | `10` | Khoảng cách tối thiểu giữa các log tiến độ theo giây, số hữu hạn lớn hơn 0 |

Script in thông báo khi bắt đầu kết nối và đọc stream. Shuffle buffer có thể
cần nạp trước khi xuất hiện batch đầu tiên. Sau đó tiến độ được cập nhật tại
ranh giới batch theo `--progress-interval`, gồm số dòng đã đọc, hợp lệ, bị loại,
đã xuất và thời gian xử lý; log được flush ngay. Luôn có trạng thái ban đầu
và trạng thái khi đạt target hoặc hết dữ liệu. Khi đang chờ mạng hoặc một
batch chưa hoàn tất, chưa có cập nhật bộ đếm mới. Có thể dùng
`--progress-interval 5` để cập nhật thường xuyên hơn. Bộ đếm đã xuất trong
log tính số dòng ghi vào file tạm; chỉ công bố kết quả sau khi hoàn tất.

Shuffle dùng buffer, không phải hoán vị ngẫu nhiên toàn bộ nguồn trong RAM.
Để tái lập dữ liệu, giữ cùng revision (nên dùng commit hash), seed, kích thước
buffer, batch size và môi trường thư viện.

Lệnh mặc định tạo:

| File | Số dòng dữ liệu, không tính header |
| --- | ---: |
| `data/processed/properties_50000.csv` | 50.000 |
| `data/processed/properties_200000.csv` | 200.000 |
| `data/processed/properties_500000.csv` | 500.000 |
| `results/build_report_500000.json` | Báo cáo của cả lượt chạy |

Mỗi file nhỏ là prefix theo hàng của file lớn hơn trong cùng lượt chạy, cùng
thứ tự và cùng ID. ID được cấp **sau khi lọc**, liên tục từ 1 đến target.
Theo danh sách thuộc tính đã thống nhất, CSV có **9 cột**:

```text
id,name,property_type_name,province_name,district_name,ward_name,price,area,published_at
```

CSV dùng UTF-8 có BOM, NULL là trường rỗng, timestamp có định dạng
`YYYY-MM-DD HH:MM:SS.ffffff`. CSV có thể chứa dấu phẩy hoặc xuống dòng trong
tên bất động sản; hãy dùng trình đọc CSV để đếm bản ghi.

Mọi quy tắc làm sạch đều dùng lại `scripts.cleaning.clean_dataframe()`:
chuẩn hóa khoảng trắng, giữ NULL ở địa chỉ tùy chọn; giá thiếu/không hữu hạn/
không dương trở thành NULL và không làm mất dòng. Chỉ loại dòng thiếu trường
bắt buộc, diện tích không hữu hạn/không dương hoặc ngày đăng không hợp lệ.
Không tự xóa trùng hoặc lọc ngoại lệ.

Báo cáo JSON ghi nguồn, revision được yêu cầu (`null` nếu không chỉ định),
seed, targets, cấu hình batch/shuffle, số dòng nguồn đã xử lý, số dòng bị loại
và nguyên nhân, số dòng hợp lệ đã gặp, số dòng thực xuất, NULL theo từng cột
cho từng file và thời gian xử lý bằng giây. `invalid_price_values` đếm giá
không hữu hạn/không dương theo báo cáo của module làm sạch; giá thiếu hoặc
không phân tích được không tăng bộ đếm này, nhưng vẫn được tính trong NULL.

- `source_rows_read` tính số bản ghi đã nhận từ stream shuffle và đưa vào
  làm sạch; không tính các bản ghi còn nằm trong buffer shuffle của thư viện.
- Batch cuối có thể dư dòng hợp lệ: `valid_rows_not_exported` ghi số dư đó.
- `invalid_rows` đếm mỗi dòng bị loại một lần; các bộ đếm nguyên nhân có thể
  trùng nhau khi một dòng vi phạm nhiều điều kiện.
- `exported_rows` là số dòng hợp lệ khác nhau đã xuất, bằng target lớn nhất;
  `total_csv_rows_written` là tổng số dòng ghi vào tất cả CSV.
- `null_counts` ở cấp ngoài là thống kê file lớn nhất; `outputs` ghi đường
  dẫn, số dòng và NULL của từng file. `elapsed_seconds` tính từ lúc bắt đầu
  xây dựng file đến khi ghi xong CSV, trước khi xuất JSON và đổi tên file.

Script ghi từng batch vào file `.part` rồi đóng và đổi tên khi **tất cả**
target đã đủ dòng; JSON với `status="completed"` được công bố cuối cùng.
Khi nguồn không đủ, lỗi mạng, lỗi ghi hoặc ngắt bằng Ctrl+C, script báo lỗi,
dọn file tạm và không công bố CSV đang dở. Lỗi đổi tên thông thường sẽ gỡ
các file vừa công bố trong lượt chạy đó. Cleanup thử từng file độc lập;
lỗi xóa file không che ngoại lệ ban đầu và không ngăn dọn các file còn lại.
File bị khóa hoặc thiếu quyền xóa được báo riêng bằng đường dẫn trên stderr;
cần dọn lại sau khi có quyền truy cập. Nếu rollback gặp lỗi quyền, một CSV
đã đủ dòng có thể còn lại nhưng không có báo cáo hoàn tất. Đổi tên từng file là thao tác riêng;
nếu tiến trình bị cưỡng bức dừng hoặc mất điện, có thể còn `.part` hoặc CSV
đã đủ dòng nhưng chưa có báo cáo hoàn tất.

Script từ chối ghi đè CSV hoặc báo cáo đã tồn tại. Trước khi chạy lại cùng
target, di chuyển các kết quả cũ sang nơi lưu trữ khác. Không chạy đồng thời
nhiều lượt có đường dẫn đầu ra trùng nhau. Các thư mục `data/raw/` và
`data/processed/` được Git bỏ qua theo cấu hình hiện tại.
