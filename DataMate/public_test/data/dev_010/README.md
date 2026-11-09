# Dữ liệu dev_010

Dữ liệu bán hàng của tiệm, gồm vài file nối với nhau qua mã.

## File
- `don_hang.csv` (csv)
- `chi_tiet_don.csv` (csv)
- `san_pham.csv` (csv)
- `khach_hang.csv` (csv)
- `thanh_toan.csv` (csv)

## Cột trong `don_hang.csv`
- **Kênh đặt**: kênh bán
- **Thành tiền**: tổng tiền đơn
- **Số CT**: mã đơn
- **Con no**: còn nợ
- **Date**: ngày bán
- **Phương thức TT**: hình thức thanh toán của đơn: cash tiền mặt, transfer chuyển khoản, ewallet ví điện tử, cod giao hàng thu tiền, debt ghi nợ
- **Tiền giảm**: giảm giá
- **Phí vận chuyển**: phí giao hàng
- **Khách trả**: đã thanh toán
- **Mã thẻ**: mã khách (trống nếu khách lẻ)
- **Xử lý**: trạng thái đơn

## Cột trong `chi_tiet_don.csv`
- **Mã bill**: mã đơn
- **Cộng**: thành tiền sau giảm
- **CK**: giảm giá
- **SoLuong**: số lượng
- **Mã H.hóa**: mã hàng
- **SL quy đổi**: số lượng đã đổi ra đơn vị cơ bản
- **No.**: số thứ tự dòng trong đơn
- **Đơn giá (đ)**: đơn giá
- **dvt**: đơn vị tính

## Cột trong `san_pham.csv`
- **Đơn vị tính**: đơn vị cơ bản
- **Nhóm hàng**: nhóm hàng
- **ten_hang**: tên
- **Giá bán**: giá bán hiện tại
- **Mã vạch**: mã hàng

## Cột trong `khach_hang.csv`
- **Khách lẻ/sỉ**: tên
- **Loại khách**: nhóm khách
- **Mã khách**: mã khách
- **Phone**: số điện thoại

## Cột trong `thanh_toan.csv`
- **Loại TT**: hình thức thanh toán
- **Ngay thu**: thời điểm thu
- **So tien**: số tiền
- **Mã đơn**: mã đơn
- **Mã TT**: mã phiếu thu

## Quy ước
- Dữ liệu có đến hết 06/09/2026.
- **Công nợ**: mỗi lần khách trả tiền cho một đơn là một dòng, **So tien** là số tiền trả lần đó; **Thành tiền** là số khách phải trả cho cả đơn.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng:
  - Tã dán Bobby size M 76 miếng: 1 thùng = 4 gói
  - Tã quần Huggies Dry size L 68 miếng: 1 thùng = 4 gói
  - Tã dán Merries size M 64 miếng: 1 thùng = 4 gói
  - Miếng lót sơ sinh Bobby Newborn 1 108 miếng: 1 thùng = 6 gói
  - Bột ăn dặm Ridielac Gold gạo sữa 200g: 1 thùng = 12 hộp
  - Khăn ướt Bobby không mùi 100 tờ: 1 lốc = 4 gói
  - Khăn ướt Bobby không mùi 100 tờ: 1 thùng = 24 gói
  - Sữa tắm gội Johnson's Baby 500ml: 1 thùng = 12 chai
  - Sữa tắm Lactacyd BB 250ml: 1 thùng = 12 chai
  - Nước giặt xả D-nee 3000ml: 1 thùng = 4 can
  - Váng sữa Monte vani vỉ 4 hộp 55g: 1 thùng = 6 vỉ
  - Phấn rôm Johnson's Baby 200g: 1 thùng = 24 chai
  - Tắm gội toàn thân D-nee Pure 380ml: 1 thùng = 12 chai
  - Nước rửa bình sữa D-nee 620ml: 1 thùng = 12 chai
  - Tã quần Moony size L 44 miếng: 1 thùng = 4 gói
  - Tã dán Huggies Dry Newborn 60 miếng: 1 thùng = 6 gói
  - Tã quần Bobby size XL 62 miếng: 1 thùng = 4 gói
  - Cháo tươi SG Food Baby gà cà rốt 240g: 1 thùng = 30 gói
  - Tăm bông trẻ em Sakura hộp 180 que: 1 lốc = 12 hộp
  - Phô mai Con Bò Cười hộp 8 miếng: 1 thùng = 24 hộp
  - Sữa pha sẵn GrowPLUS+ đỏ 110ml lốc 4: 1 thùng = 12 lốc
