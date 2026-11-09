# Dữ liệu biz_128

File Excel xuất từ phần mềm bán hàng, mỗi danh sách một file (danh sách dài tách thành nhiều file, tên thêm đuôi _1, _2… hoặc đuôi năm _2025, _2026…), nối với nhau qua mã. Ngày dạng dd/mm/yyyy.

File `DanhSachHoaDon.xlsx` chia mỗi tháng một sheet, tên sheet ghi tháng và năm.

## File
- `DanhSachHoaDon.xlsx` (xlsx)
- `DanhSachHoaDonChiTiet.xlsx` (xlsx)
- `DanhSachSanPham.xlsx` (xlsx)
- `DanhSachKhachHang.xlsx` (xlsx)
- `BaoCaoTonKho.xlsx` (xlsx)
- `DanhSachNhapHang.xlsx` (xlsx)
- `DanhSachChiTietNhapHang.xlsx` (xlsx)
- `DanhSachHoaDonPhongBan.xlsx` (xlsx)

## Cột trong `DanhSachHoaDon.xlsx`
- **Mã hóa đơn**: mã đơn
- **Thời gian**: ngày bán
- **Mã KH**: mã khách (trống nếu khách lẻ)
- **Khách hàng**: tên khách (Khách lẻ nếu không lưu)
- **Tổng tiền hàng**: tổng tiền hàng của đơn (cộng thành tiền các dòng), trước giảm giá của đơn
- **Giảm giá**: giảm giá
- **Khách đã trả**: đã thanh toán
- **Trạng thái**: trạng thái đơn
- **Thời gian tạo**: thời điểm đặt đơn (ngày giờ)
- **Tổng sau giảm giá**: tổng tiền đơn
- **Còn nợ**: còn nợ

## Cột trong `DanhSachHoaDonChiTiet.xlsx`
- **Mã hóa đơn**: mã đơn
- **Mã hàng**: mã hàng
- **Tên hàng**: tên hàng
- **Số lượng**: số lượng
- **Đơn giá**: đơn giá
- **Giảm giá**: giảm giá
- **Thành tiền**: thành tiền sau giảm
- **Số lượng quy đổi**: số lượng đã đổi ra đơn vị cơ bản
- **STT**: số thứ tự dòng trong đơn

## Cột trong `DanhSachSanPham.xlsx`
- **Mã hàng**: mã hàng
- **Tên hàng**: tên
- **Nhóm hàng(3 Cấp)**: nhóm hàng
- **Giá bán**: giá bán hiện tại
- **ĐVT**: đơn vị cơ bản
- **Thời gian tạo**: ngày tạo mặt hàng trên phần mềm

## Cột trong `DanhSachKhachHang.xlsx`
- **Mã khách hàng**: mã khách
- **Tên khách hàng**: tên
- **Điện thoại**: số điện thoại
- **Nhóm khách hàng**: nhóm khách
- **Địa chỉ**: địa chỉ
- **Giới tính**: cột trống, không có dữ liệu

## Cột trong `BaoCaoTonKho.xlsx`
- **Mã hàng**: mã hàng
- **Tên hàng**: tên hàng
- **ĐVT**: đơn vị cơ bản
- **Tồn cuối kỳ**: tồn kho (đơn vị cơ bản)

## Cột trong `DanhSachNhapHang.xlsx`
- **Mã nhập hàng**: mã phiếu nhập
- **Thời gian**: ngày nhập
- **Mã NCC**: mã nhà cung cấp
- **Cần trả NCC**: tổng tiền phiếu nhập
- **Trạng thái**: trạng thái phiếu nhập
- **Ghi chú**: ghi chú

## Cột trong `DanhSachChiTietNhapHang.xlsx`
- **Mã nhập hàng**: mã phiếu nhập
- **STT**: số thứ tự dòng trong phiếu nhập
- **Mã hàng**: mã hàng
- **ĐVT**: đơn vị tính
- **Số lượng**: số lượng
- **Đơn giá**: giá nhập một đơn vị (theo đơn vị nhập của dòng)

## Cột trong `DanhSachHoaDonPhongBan.xlsx`
- **Mã hóa đơn**: mã đơn
- **Phòng/Bàn**: bàn
- **Khu vực**: khu vực của bàn
- **Số khách**: số khách của đơn

## Quy ước
- Dữ liệu có đến hết 07/09/2026.
- **Còn nợ**: **Còn nợ** là số khách còn nợ của đơn, tính đến hết ngày cuối dữ liệu.
- **Tồn kho**: **Tồn cuối kỳ** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
- **Bàn**: đơn ăn tại quán có đúng một bàn (**Phòng/Bàn**), kể cả đơn huỷ; đơn giao đi không có bàn. **Số khách** là số khách của đơn; một bàn có nhiều đơn trong ngày.
- **Phí phục vụ**: đơn ngồi phòng lạnh (không huỷ, không ghi nợ) có thêm dòng hàng "Phí phục vụ": phí phục vụ phòng lạnh của đơn, tính theo tiền món, đã ghi sẵn thành tiền.
- **Nhập hàng**: **Đơn giá** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Cần trả NCC** là tổng tiền của cả phiếu nhập.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng:
  - Bia Tiger lon: 1 thùng = 24 lon
  - Bia Sài Gòn Special lon: 1 thùng = 24 lon
  - Coca-Cola lon: 1 thùng = 24 lon
  - Bia Tiger Bạc lon: 1 thùng = 24 lon
  - Nước suối: 1 thùng = 24 chai
  - Bia Heineken lon: 1 thùng = 24 lon
  - Bia Sài Gòn Lager chai: 1 két = 20 chai
  - 7Up lon: 1 thùng = 24 lon
