# Dữ liệu dev_013

Sổ sách Excel của tiệm mẹ và bé. `BanHang_<năm>.xlsx`: sổ bán hàng, mỗi tháng một sheet, header gộp 2 dòng (nhóm Hàng hoá, Tiền ở dòng trên). Mỗi dòng một mặt hàng khách mua; một hoá đơn nhiều dòng cùng số HĐ. Ngay sau các dòng hàng của một hoá đơn có thể có dòng không phải hàng, chỉ ghi HĐ, tên và TT: "Voucher" (tiền giảm của hoá đơn từ các chương trình ở sheet KhuyenMai, TT ghi số âm), "Dùng <n> điểm" (khách dùng n điểm thành viên, mỗi điểm trừ 100đ, TT ghi số âm), "Phí ship" (phí giao hàng khách trả thêm). `QuanLy.xlsx`: danh mục hàng (DanhMuc), khách thành viên (KhachHang), sổ nhập hàng (NhapHang), chương trình khuyến mãi (KhuyenMai), mỗi danh sách một sheet. Sổ không có mã hàng, mã khách: nối qua tên hàng, tên khách.

## File
- `BanHang_2025.xlsx` (xlsx)
- `BanHang_2026.xlsx` (xlsx)
- `QuanLy.xlsx` (xlsx)

## Cột trong `BanHang_2025.xlsx`
- **ĐG**: đơn giá
- **TT**: thành tiền của dòng; Voucher, Dùng điểm ghi số âm (trừ vào hoá đơn), Phí ship ghi phí giao
- **SL**: số lượng (trống ở dòng không phải hàng)
- **ĐVT**: đơn vị tính
- **Tên hàng**: tên hàng; dòng không phải hàng ghi Voucher, Dùng <n> điểm hoặc Phí ship
- **HĐ**: số hoá đơn, ghi ở mọi dòng của hoá đơn kể cả dòng Voucher / Dùng điểm / Phí ship
- **Ngày**: ngày bán (dòng Voucher / Dùng điểm / Phí ship để trống)
- **Khách**: tên khách thành viên (Khách lẻ nếu không lưu); dòng không phải hàng để trống
- **Kênh**: kênh bán: Tại tiệm, Zalo (khách nhắn đặt, tiệm giao), Sàn TMĐT (bán trên sàn thương mại điện tử); dòng không phải hàng để trống
- **Ghi chú**: ghi chú của đơn; đơn huỷ hoặc đang giao được ghi ở đây, không có cột trạng thái riêng

## Cột trong `BanHang_2026.xlsx`
- **ĐG**: đơn giá
- **TT**: thành tiền của dòng; Voucher, Dùng điểm ghi số âm (trừ vào hoá đơn), Phí ship ghi phí giao
- **SL**: số lượng (trống ở dòng không phải hàng)
- **ĐVT**: đơn vị tính
- **Tên hàng**: tên hàng; dòng không phải hàng ghi Voucher, Dùng <n> điểm hoặc Phí ship
- **HĐ**: số hoá đơn, ghi ở mọi dòng của hoá đơn kể cả dòng Voucher / Dùng điểm / Phí ship
- **Ngày**: ngày bán (dòng Voucher / Dùng điểm / Phí ship để trống)
- **Khách**: tên khách thành viên (Khách lẻ nếu không lưu); dòng không phải hàng để trống
- **Kênh**: kênh bán: Tại tiệm, Zalo (khách nhắn đặt, tiệm giao), Sàn TMĐT (bán trên sàn thương mại điện tử); dòng không phải hàng để trống
- **Ghi chú**: ghi chú của đơn; đơn huỷ hoặc đang giao được ghi ở đây, không có cột trạng thái riêng

## Cột trong `QuanLy.xlsx`, sheet `DanhMuc`
- **Tên hàng**: tên hàng
- **Tên gọi khác**: tên gọi khác hay dùng (sữa, bỉm), nhiều cách cách nhau dấu phẩy
- **Nhóm**: nhóm hàng
- **Hãng**: hãng
- **Số / Size**: số của sữa (theo tuổi) hoặc size (bỉm, núm ti); trống nếu không có
- **ĐVT**: đơn vị cơ bản
- **Quy đổi**: quy đổi đơn vị lớn ra ĐVT, vd "1 thùng = 4 bịch"; trống nếu chỉ bán theo ĐVT

## Cột trong `QuanLy.xlsx`, sheet `KhachHang`
- **Tên KH**: tên khách
- **SĐT**: số điện thoại
- **Tên bé**: tên ở nhà của bé
- **Ngày đăng ký**: ngày đăng ký thành viên; chỉ hoá đơn từ ngày này mới tích, dùng điểm
- **Điểm hiện có**: điểm còn đến hết ngày cuối dữ liệu

## Cột trong `QuanLy.xlsx`, sheet `NhapHang`
- **Ngày**: ngày nhập
- **Số phiếu**: mã phiếu nhập
- **Nhà cung cấp**: nhà cung cấp
- **Hàng**: tên hàng
- **SL**: số lượng nhập
- **ĐVT**: đơn vị nhập
- **Đơn giá**: giá nhập một đơn vị (theo đơn vị nhập của dòng)
- **Thành tiền**: tiền nhập của cả dòng
- **Ghi chú**: ghi chú

## Cột trong `QuanLy.xlsx`, sheet `KhuyenMai`
- **Chương trình**: tên chương trình
- **Hàng áp dụng**: hàng áp dụng (Tất cả: mọi hoá đơn đủ điều kiện ghi ở tên)
- **Từ ngày**: từ ngày
- **Đến ngày**: đến ngày (tính cả ngày này)

## Quy ước
- Dữ liệu có đến hết 30/06/2026.
- **Nhập hàng**: **Đơn giá** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Thành tiền** là tiền nhập của cả dòng.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `QuanLy.xlsx`.
