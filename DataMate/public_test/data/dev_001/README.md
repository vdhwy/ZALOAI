# Dữ liệu dev_001

File Excel xuất từ phần mềm bán hàng. Sổ chi tiết bán hàng: mỗi dòng một dòng hàng, thông tin đơn lặp lại ở mọi dòng.

## File
- `So_chi_tiet_ban_hang.xlsx` (xlsx)
- `Danh sách hàng hóa.xlsx` (xlsx)

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
- **Giá bán**: giá bán hiện tại
- **Giá vốn**: giá vốn

## Quy ước
- Dữ liệu có đến hết 08/07/2026.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng:
  - Coca Cola 330ml: 1 lốc = 6 lon
  - Coca Cola 330ml: 1 thùng = 24 lon
  - Pepsi 330ml: 1 lốc = 6 lon
  - Pepsi 330ml: 1 thùng = 24 lon
  - Sting dâu 330ml: 1 lốc = 6 chai
  - Sting dâu 330ml: 1 thùng = 24 chai
  - Red Bull 250ml: 1 lốc = 6 lon
  - Red Bull 250ml: 1 thùng = 24 lon
  - Trà xanh 0 độ 455ml: 1 lốc = 6 chai
  - Trà xanh 0 độ 455ml: 1 thùng = 24 chai
  - Nước suối Aquafina 500ml: 1 lốc = 6 chai
  - Nước suối Aquafina 500ml: 1 thùng = 24 chai
  - Nước suối Lavie 1.5L: 1 lốc = 6 chai
  - Nước suối Lavie 1.5L: 1 thùng = 12 chai
  - Bia Tiger 330ml: 1 lốc = 6 lon
  - Bia Tiger 330ml: 1 thùng = 24 lon
  - Bia Sài Gòn Special 330ml: 1 lốc = 6 lon
  - Bia Sài Gòn Special 330ml: 1 thùng = 24 lon
  - Bia Heineken 330ml: 1 lốc = 6 lon
  - Bia Heineken 330ml: 1 thùng = 24 lon
  - Sữa tươi Vinamilk 180ml: 1 lốc = 4 hộp
  - Sữa tươi Vinamilk 180ml: 1 thùng = 48 hộp
  - Sữa TH true MILK 180ml: 1 lốc = 4 hộp
  - Sữa TH true MILK 180ml: 1 thùng = 48 hộp
  - Sữa đặc Ông Thọ 380g: 1 thùng = 48 hộp
  - Sữa chua Vinamilk có đường: 1 lốc = 4 hộp
  - Sữa chua Vinamilk có đường: 1 thùng = 48 hộp
  - Yakult 65ml: 1 lốc = 5 chai
  - Yakult 65ml: 1 thùng = 50 chai
  - Mì Hảo Hảo tôm chua cay: 1 thùng = 30 gói
  - Mì Omachi sườn hầm: 1 thùng = 30 gói
  - Mì 3 Miền tôm hùm: 1 thùng = 30 gói
  - Phở Vifon bò: 1 thùng = 30 gói
  - Gạo ST25: 1 bao = 5 kg
  - Gạo ST25: 1 bao 25kg = 25 kg
  - Gạo thơm Jasmine: 1 bao = 5 kg
  - Gạo thơm Jasmine: 1 bao 25kg = 25 kg
  - Đường Biên Hòa 1kg: 1 thùng = 12 gói
  - Muối I-ốt 500g: 1 thùng = 20 gói
  - Bột ngọt Ajinomoto 400g: 1 thùng = 20 gói
  - Hạt nêm Knorr 400g: 1 thùng = 20 gói
  - Nước mắm Nam Ngư 750ml: 1 thùng = 12 chai
  - Nước tương Maggi 700ml: 1 thùng = 12 chai
  - Dầu ăn Tường An 1L: 1 thùng = 12 chai
  - Dầu ăn Simply 2L: 1 thùng = 6 chai
  - Tương ớt Chinsu 250g: 1 thùng = 24 chai
  - Trứng gà so: 1 vỉ = 10 quả
  - Trứng gà so: 1 hộp 30 = 30 quả
  - Xúc xích Vissan 5 cây: 1 thùng = 20 gói
  - Cá hộp 3 Cô Gái 155g: 1 lốc = 10 hộp
  - Đậu phộng rang muối 200g: 1 thùng = 20 gói
  - Snack Oishi tôm cay 40g: 1 thùng = 50 gói
  - Snack Lay's vị tự nhiên 56g: 1 thùng = 32 gói
  - Bánh Oreo 133g: 1 lốc = 12 gói
  - Bánh Chocopie 12 cái: 1 thùng = 8 hộp
  - Bánh quy Cosy 200g: 1 thùng = 20 gói
  - Kẹo Alpenliebe 100g: 1 thùng = 40 gói
  - Kẹo cao su Doublemint: 1 lốc = 20 vỉ
  - Hạt hướng dương 200g: 1 thùng = 20 gói
  - Bột giặt OMO 3kg: 1 thùng = 4 gói
  - Nước giặt Ariel 3.2L: 1 thùng = 4 chai
  - Nước rửa chén Sunlight 750g: 1 thùng = 12 chai
  - Nước lau sàn Sunlight 1L: 1 thùng = 12 chai
  - Kem đánh răng P/S 180g: 1 thùng = 36 hộp
  - Bàn chải Colgate: 1 lốc = 12 cái
  - Dầu gội Clear 630g: 1 thùng = 6 chai
  - Sữa tắm Lifebuoy 850g: 1 thùng = 6 chai
  - Xà bông Lifebuoy 90g: 1 lốc = 6 cục
  - Xà bông Lifebuoy 90g: 1 thùng = 72 cục
  - Giấy vệ sinh Pulppy 10 cuộn: 1 thùng = 6 lốc
  - Khăn giấy Tempo 10 gói: 1 thùng = 12 lốc
  - Băng vệ sinh Diana 8 miếng: 1 thùng = 48 gói
  - Tã Bobby M 32 miếng: 1 thùng = 4 gói
  - Thuốc lá Vinataba: 1 cây = 10 gói
  - Thuốc lá Jet: 1 cây = 10 gói
  - Pin Panasonic AA: 1 hộp = 12 vỉ
  - Nhang Quảng Trí bó: 1 thùng = 20 bó
