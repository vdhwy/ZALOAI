# Dữ liệu biz_114

Một file phẳng, mỗi dòng một bản ghi (một dòng hàng trong đơn).

## File
- `ban_hang.csv` (csv)

## Cột trong `ban_hang.csv`
- **Giá bán lẻ**: đơn giá
- **Đơn vị tính**: đơn vị tính
- **Mã GD**: mã đơn
- **Quy ra ĐV lẻ**: số lượng đã đổi ra đơn vị cơ bản
- **Sluong**: số lượng
- **Sản phẩm**: tên hàng
- **Tổng**: thành tiền sau giảm
- **Tên khách**: tên khách (Khách lẻ nếu không lưu)
- **Ngày**: ngày bán
- **trang_thai**: trạng thái đơn

## Quy ước
- Dữ liệu có đến hết 21/06/2026.
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
