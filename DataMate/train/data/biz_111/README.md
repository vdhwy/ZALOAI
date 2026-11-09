# Dữ liệu biz_111

Dữ liệu bán hàng của tiệm, gồm vài file nối với nhau qua mã.

## File
- `don_hang.csv` (csv)
- `chi_tiet_don.csv` (csv)
- `san_pham.csv` (csv)
- `khach_hang.csv` (csv)
- `thanh_toan.csv` (csv)

## Cột trong `don_hang.csv`
- **Số KH**: mã khách (trống nếu khách lẻ)
- **Xử lý**: trạng thái đơn
- **NgayBan**: ngày bán
- **Bán qua**: kênh bán
- **Còn lại**: còn nợ
- **Khách trả**: đã thanh toán
- **Tổng bill**: tổng tiền đơn
- **Phương thức TT**: hình thức thanh toán của đơn: cash tiền mặt, transfer chuyển khoản, ewallet ví điện tử, cod giao hàng thu tiền, debt ghi nợ
- **Mã chứng từ**: mã đơn

## Cột trong `chi_tiet_don.csv`
- **SL quy đổi**: số lượng đã đổi ra đơn vị cơ bản
- **Thứ tự**: số thứ tự dòng trong đơn
- **Giá đơn vị**: đơn giá
- **SL**: số lượng
- **T.Tiền**: thành tiền sau giảm
- **ID SP**: mã hàng
- **Ma don**: mã đơn
- **Đơn vị (tính)**: đơn vị tính

## Cột trong `san_pham.csv`
- **SKU**: mã hàng
- **Giá**: giá bán hiện tại
- **Đơn vị**: đơn vị cơ bản
- **Nhom hang**: nhóm hàng
- **Sản phẩm**: tên

## Cột trong `khach_hang.csv`
- **ma_kh**: mã khách
- **Nhóm**: nhóm khách
- **Phone**: số điện thoại
- **Addr**: địa chỉ
- **Khách lẻ/sỉ**: tên

## Cột trong `thanh_toan.csv`
- **Thời gian thu**: thời điểm thu
- **Phương thức**: hình thức thanh toán
- **Tiền**: số tiền
- **Mã phiếu thu**: mã phiếu thu
- **Số HĐ**: mã đơn

## Quy ước
- Dữ liệu có đến hết 19/08/2026.
- **Công nợ**: mỗi lần khách trả tiền cho một đơn là một dòng, **Tiền** là số tiền trả lần đó; **Tổng bill** là số khách phải trả cho cả đơn.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng:
  - Bánh croissant: 1 hộp = 6 cái
  - Bánh tiramisu: 1 hộp = 6 cái
