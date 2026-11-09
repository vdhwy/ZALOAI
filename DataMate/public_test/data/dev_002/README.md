# Dữ liệu dev_002

File Excel xuất từ phần mềm bán hàng. File đơn hàng mỗi dòng một sản phẩm, thông tin đơn lặp lại ở mọi dòng của đơn; file này không có mã sản phẩm, nối với các danh sách sản phẩm qua tên sản phẩm. Ngày dạng dd/mm/yyyy.

Dữ liệu bán hàng xuất theo tháng, mỗi tháng một file (tách theo tháng, không theo năm): từ `BanHang_T1_2025.xlsx` đến `BanHang_T5_2026.xlsx` (17 file), các tháng cùng cột; mỗi file có sheet `DonHang_ChiTiet`.

## File
- `BanHang_T<tháng>_<năm>.xlsx` (xlsx)
- `DanhSachQuyDoi.xlsx` (xlsx)

## Cột trong `BanHang_T<tháng>_<năm>.xlsx`, sheet `DonHang_ChiTiet`
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
- Dữ liệu có đến hết 24/05/2026.
- **Topping**: topping có thể ghi chung ô với món ở cột **Tên sản phẩm**, nối bằng " + ", tên topping không kèm chữ "Topping"; số đứng trước tên topping là số phần (không ghi số là 1 phần), tiền topping ghi trong ngoặc và đã cộng vào **Tổng tiền** của dòng đó. Số lượng, giá và đơn vị của dòng là của món.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `DanhSachQuyDoi.xlsx`.
