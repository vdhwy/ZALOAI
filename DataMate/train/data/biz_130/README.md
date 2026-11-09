# Dữ liệu biz_130

File Excel xuất từ phần mềm bán hàng. Sổ chi tiết bán hàng: mỗi dòng một dòng hàng, thông tin đơn lặp lại ở mọi dòng.

## File
- `So_chi_tiet_ban_hang_1.xlsx` (xlsx)
- `So_chi_tiet_ban_hang_2.xlsx` (xlsx)
- `Danh sách hàng hóa.xlsx` (xlsx)

## Cột trong `So_chi_tiet_ban_hang_1.xlsx`
- **Ngày**: ngày bán
- **Mã đơn hàng**: mã đơn
- **Tên hàng hóa**: tên hàng
- **Đơn vị tính**: đơn vị tính
- **Số lượng**: số lượng
- **Đơn giá**: đơn giá
- **Thành tiền**: thành tiền sau giảm
- **Trạng thái**: trạng thái đơn
- **Số lượng quy đổi**: số lượng đã đổi ra đơn vị cơ bản

## Cột trong `So_chi_tiet_ban_hang_2.xlsx`
- **Ngày**: ngày bán
- **Mã đơn hàng**: mã đơn
- **Tên hàng hóa**: tên hàng
- **Đơn vị tính**: đơn vị tính
- **Số lượng**: số lượng
- **Đơn giá**: đơn giá
- **Thành tiền**: thành tiền sau giảm
- **Trạng thái**: trạng thái đơn
- **Số lượng quy đổi**: số lượng đã đổi ra đơn vị cơ bản

## Cột trong `Danh sách hàng hóa.xlsx`
- **Mã hàng hóa**: mã hàng
- **Tên hàng hóa**: tên
- **Nhóm hàng hóa**: nhóm hàng
- **Đơn vị tính**: đơn vị cơ bản
- **Giá vốn**: giá vốn

## Quy ước
- Dữ liệu có đến hết 29/08/2026.
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
