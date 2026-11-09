# Dữ liệu biz_125

Một file phẳng, mỗi dòng một bản ghi (một dòng hàng trong đơn).

## File
- `ban_hang.csv` (csv)

## Cột trong `ban_hang.csv`
- **dvt**: đơn vị tính
- **Hàng bán**: tên hàng
- **Khách hàng (tên)**: tên khách (Khách lẻ nếu không lưu)
- **Số lượng lẻ**: số lượng đã đổi ra đơn vị cơ bản
- **Amount**: thành tiền sau giảm
- **Trạng thái xử lý**: trạng thái đơn
- **SL bán**: số lượng
- **Ngày bán**: ngày bán
- **Số phiếu**: mã đơn
- **Giá 1 đv**: đơn giá

## Quy ước
- Dữ liệu có đến hết 11/05/2026.
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
