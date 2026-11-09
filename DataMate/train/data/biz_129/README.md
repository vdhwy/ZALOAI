# Dữ liệu biz_129

Dữ liệu bán hàng của tiệm, gồm vài file nối với nhau qua mã.

## File
- `don_hang.csv` (csv)
- `chi_tiet_don.csv` (csv)
- `san_pham.csv` (csv)
- `khach_hang.csv` (csv)
- `thanh_toan.csv` (csv)

## Cột trong `don_hang.csv`
- **Hình thức thanh toán**: hình thức thanh toán của đơn: cash tiền mặt, transfer chuyển khoản, ewallet ví điện tử, cod giao hàng thu tiền, debt ghi nợ
- **Dư nợ**: còn nợ
- **Thanh toán**: đã thanh toán
- **Tình trạng đơn**: trạng thái đơn
- **Số phiếu**: mã đơn
- **Mã khách mua**: mã khách (trống nếu khách lẻ)
- **Phải thu**: tổng tiền đơn
- **Ngày bán**: ngày bán

## Cột trong `chi_tiet_don.csv`
- **Tiền bán**: thành tiền sau giảm
- **TT dòng**: số thứ tự dòng trong đơn
- **S.L**: số lượng
- **Mã hàng bán**: mã hàng
- **Quy ra ĐV lẻ**: số lượng đã đổi ra đơn vị cơ bản
- **Số CT**: mã đơn
- **Giảm giá**: giảm giá
- **Giá 1 đv**: đơn giá
- **ĐV tính**: đơn vị tính

## Cột trong `san_pham.csv`
- **Giá hiện tại**: giá bán hiện tại
- **Đơn vị tính**: đơn vị cơ bản
- **Tên sản phẩm**: tên
- **Nhom hang**: nhóm hàng
- **Mã HH**: mã hàng

## Cột trong `khach_hang.csv`
- **Nhóm**: nhóm khách
- **KH**: tên
- **Số điện thoại**: số điện thoại
- **Mã khách lẻ/sỉ**: mã khách

## Cột trong `thanh_toan.csv`
- **Mã GD**: mã phiếu thu
- **PTTT**: hình thức thanh toán
- **Tiền**: số tiền
- **Mã giao dịch**: mã đơn
- **Thời điểm**: thời điểm thu

## Quy ước
- Dữ liệu có đến hết 14/08/2026.
- **Công nợ**: mỗi lần khách trả tiền cho một đơn là một dòng, **Tiền** là số tiền trả lần đó; **Phải thu** là số khách phải trả cho cả đơn.
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
