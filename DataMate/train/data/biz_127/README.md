# Dữ liệu biz_127

Dữ liệu bán hàng của tiệm, gồm vài file nối với nhau qua mã.

## File
- `don_hang.csv` (csv)
- `chi_tiet_don.csv` (csv)
- `san_pham.csv` (csv)
- `khach_hang.csv` (csv)
- `thanh_toan.csv` (csv)

## Cột trong `don_hang.csv`
- **Còn nợ**: còn nợ
- **Diễn giải**: cột trống, không có dữ liệu
- **Tổng đơn**: tổng tiền đơn
- **Loại bán**: kênh bán
- **Ngày**: ngày bán
- **Mã chứng từ**: mã đơn
- **Customer ID**: mã khách (trống nếu khách lẻ)
- **Khách trả**: đã thanh toán
- **Trả bằng**: hình thức thanh toán của đơn: cash tiền mặt, transfer chuyển khoản, ewallet ví điện tử, cod giao hàng thu tiền, debt ghi nợ
- **Tình trạng**: trạng thái đơn

## Cột trong `chi_tiet_don.csv`
- **Mã đơn hàng**: mã đơn
- **SoLuong**: số lượng
- **No.**: số thứ tự dòng trong đơn
- **DVT**: đơn vị tính
- **Amount**: thành tiền sau giảm
- **Số lượng lẻ**: số lượng đã đổi ra đơn vị cơ bản
- **Mã mặt hàng**: mã hàng
- **Đơn giá (đ)**: đơn giá

## Cột trong `san_pham.csv`
- **Giá niêm yết**: giá bán hiện tại
- **Danh mục**: nhóm hàng
- **Mã sản phẩm bán**: mã hàng
- **Tên SP**: tên
- **Đơn vị cơ bản**: đơn vị cơ bản

## Cột trong `khach_hang.csv`
- **Di động**: số điện thoại
- **Mã KH**: mã khách
- **Khách hàng (tên)**: tên

## Cột trong `thanh_toan.csv`
- **Số CT**: mã đơn
- **Ngày thu**: thời điểm thu
- **Mã GD**: mã phiếu thu
- **Giá trị**: số tiền
- **HTTT**: hình thức thanh toán

## Quy ước
- Dữ liệu có đến hết 28/07/2026.
- **Công nợ**: mỗi lần khách trả tiền cho một đơn là một dòng, **Giá trị** là số tiền trả lần đó; **Tổng đơn** là số khách phải trả cho cả đơn.
- **Phí phục vụ**: đơn ngồi phòng lạnh (không huỷ, không ghi nợ) có thêm dòng hàng "Phí phục vụ": phí phục vụ phòng lạnh của đơn, tính theo tiền món, đã ghi sẵn thành tiền.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng:
  - Bia Tiger lon: 1 thùng = 24 lon
  - Bia Sài Gòn Special lon: 1 thùng = 24 lon
  - Coca-Cola lon: 1 thùng = 24 lon
  - Bia Tiger Bạc lon: 1 thùng = 24 lon
  - Nước suối: 1 thùng = 24 chai
  - Bia Heineken lon: 1 thùng = 24 lon
  - Bia Sài Gòn Lager chai: 1 két = 20 chai
  - 7Up lon: 1 thùng = 24 lon
