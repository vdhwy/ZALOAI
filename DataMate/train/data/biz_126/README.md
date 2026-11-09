# Dữ liệu biz_126

Sổ bán hàng chủ tiệm tự ghi trên Excel, một sheet: mỗi dòng một mặt hàng khách mua, không ghi mã đơn, không ghi tên khách.

## File
- `SoBanHang.xlsx` (xlsx)

## Cột trong `SoBanHang.xlsx`
- **Đơn vị tính**: đơn vị tính
- **Số lượng bán**: số lượng
- **Thành tiền (đ)**: thành tiền sau giảm
- **Ten hang**: tên hàng
- **SL lẻ**: số lượng đã đổi ra đơn vị cơ bản
- **Trạng thái đơn**: trạng thái đơn
- **Ngày tháng**: ngày bán
- **Price**: đơn giá

## Quy ước
- Dữ liệu có đến hết 06/06/2026.
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
