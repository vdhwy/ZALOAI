# Dữ liệu biz_102

File Excel xuất từ phần mềm bán hàng, mỗi danh sách một file (danh sách dài tách thành nhiều file, tên thêm đuôi _1, _2… hoặc đuôi năm _2025, _2026…). File đơn hàng mỗi dòng một sản phẩm, thông tin đơn lặp lại ở mọi dòng của đơn; file này không có mã sản phẩm, nối với các danh sách sản phẩm qua tên sản phẩm. Ngày dạng dd/mm/yyyy.

File `DonHang_ChiTiet.xlsx` chia mỗi tháng một sheet, tên sheet ghi tháng và năm.

## File
- `DonHang_ChiTiet.xlsx` (xlsx)
- `DanhSachQuyDoi.xlsx` (xlsx)

## Cột trong `DonHang_ChiTiet.xlsx`
- **Mã đơn hàng**: mã đơn
- **Ngày đặt hàng**: ngày bán
- **Trạng thái đơn hàng**: trạng thái đơn
- **Tên khách hàng**: tên khách (Khách lẻ nếu không lưu)
- **Tên sản phẩm**: tên hàng
- **Số lượng sản phẩm**: số lượng
- **Giá sản phẩm**: đơn giá
- **Tổng tiền**: thành tiền sau giảm
- **Đơn vị tính**: đơn vị tính

## Cột trong `DanhSachQuyDoi.xlsx`
- **Tên sản phẩm**: tên hàng (file chỉ có mặt hàng có đơn vị lớn)
- **Đơn vị quy đổi**: đơn vị lớn (thùng, hộp, tấn...)
- **Tỉ lệ quy đổi**: hệ số: số đơn vị cơ bản trong 1 đơn vị lớn
- **Đơn vị cơ bản**: đơn vị cơ bản

## Quy ước
- Dữ liệu có đến hết 16/06/2026.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `DanhSachQuyDoi.xlsx`.
