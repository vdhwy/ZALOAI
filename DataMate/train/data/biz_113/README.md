# Dữ liệu biz_113

Sổ bán hàng chủ tiệm tự ghi trên Excel, một sheet: mỗi dòng một mặt hàng khách mua, không ghi mã đơn, không ghi tên khách.

## File
- `SoBanHang.xlsx` (xlsx)

## Cột trong `SoBanHang.xlsx`
- **DonVi**: đơn vị tính
- **Ngày mua**: ngày bán
- **Số lượng lẻ**: số lượng đã đổi ra đơn vị cơ bản
- **thanh_tien**: thành tiền sau giảm
- **Đơn giá bán**: đơn giá
- **SL bán**: số lượng
- **Ghi chú TT**: trạng thái đơn
- **Mặt hàng**: tên hàng

## Quy ước
- Dữ liệu có đến hết 09/08/2026.
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
