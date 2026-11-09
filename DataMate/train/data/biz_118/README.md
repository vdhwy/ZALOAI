# Dữ liệu biz_118

File Excel xuất từ phần mềm bán hàng. Sổ chi tiết bán hàng: mỗi dòng một dòng hàng, thông tin đơn lặp lại ở mọi dòng.

File `So_chi_tiet_ban_hang.xlsx` chia mỗi tháng một sheet, tên sheet ghi tháng và năm.

## File
- `So_chi_tiet_ban_hang.xlsx` (xlsx)
- `Danh sách hàng hóa.xlsx` (xlsx)
- `Bảng kê phiếu giao hàng.xlsx` (xlsx)
- `Chi tiết công nợ theo hạn.xlsx` (xlsx)

## Cột trong `So_chi_tiet_ban_hang.xlsx`
- **Ngày**: ngày bán
- **Mã đơn hàng**: mã đơn
- **Tên hàng hóa**: tên hàng
- **Đơn vị tính**: đơn vị tính
- **Số lượng**: số lượng
- **Đơn giá**: đơn giá
- **Thành tiền**: thành tiền sau giảm
- **Trạng thái**: trạng thái đơn
- **Số lượng quy đổi**: số lượng đã đổi ra đơn vị cơ bản
- **Khách hàng**: tên khách (Khách lẻ nếu không lưu)

## Cột trong `Danh sách hàng hóa.xlsx`
- **Mã hàng hóa**: mã hàng
- **Tên hàng hóa**: tên
- **Nhóm hàng hóa**: nhóm hàng
- **Đơn vị tính**: đơn vị cơ bản

## Cột trong `Bảng kê phiếu giao hàng.xlsx`
- **Ngày giao hàng**: ngày giao
- **Mã đơn hàng**: mã đơn
- **Lần giao**: đợt giao (1, 2, 3)
- **Tên hàng hóa**: tên hàng
- **Đơn vị tính**: đơn vị cơ bản
- **Số lượng giao**: số lượng đã đổi ra đơn vị cơ bản
- **Biển số xe**: biển số xe
- **Người giao hàng**: tài xế

## Cột trong `Chi tiết công nợ theo hạn.xlsx`
- **Mã đơn hàng**: mã đơn
- **Số ngày được nợ**: số ngày được nợ
- **Hạn thanh toán**: hạn thanh toán

## Quy ước
- Dữ liệu có đến hết 10/09/2026.
- **Hạn thanh toán**: chỉ đơn bán nợ có hạn. **Hạn thanh toán** là ngày khách phải trả hết đơn; **Số ngày được nợ** là số ngày được nợ, tính từ ngày đặt.
- **Giao hàng**: đơn không huỷ có ít nhất một mặt hàng nhóm cát đá, gạch, sắt thép, xi măng thì được giao tận nơi mọi mặt hàng của đơn, 1–3 đợt (**Lần giao**); đơn khác khách tự chở, không có trong sổ giao; đơn đặt mấy ngày cuối dữ liệu có thể chưa giao. **Số lượng giao** tính theo đơn vị cơ bản.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng:
  - Xi măng Hà Tiên PCB40 bao 50kg: 1 tấn = 20 bao
  - Xi măng INSEE Power-S bao 50kg: 1 tấn = 20 bao
  - Cát xây tô: 1 xe 4m3 = 4 m3
  - Cát bê tông: 1 xe 4m3 = 4 m3
  - Cát san lấp: 1 xe 4m3 = 4 m3
  - Đá 1x2: 1 xe 4m3 = 4 m3
  - Đá 4x6: 1 xe 4m3 = 4 m3
  - Đá mi bụi: 1 xe 4m3 = 4 m3
  - Gạch ống 8x8x18 Tuynel: 1 thiên = 1000 viên
  - Gạch thẻ đặc 4x8x18: 1 thiên = 1000 viên
  - Băng keo điện Nano 20 yard: 1 cây = 10 cuộn
  - Lưới B40 mạ kẽm khổ 1.5m: 1 cuộn 10m = 10 m
  - Ngói Đồng Nai 22 viên/m2: 1 thiên = 1000 viên
  - Bạt xanh cam khổ 4m: 1 cuộn 4x50m = 200 m2
