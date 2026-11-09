# Dữ liệu biz_119

File Excel xuất từ phần mềm bán hàng, mỗi danh sách một file (danh sách dài tách thành nhiều file, tên thêm đuôi _1, _2… hoặc đuôi năm _2025, _2026…), nối với nhau qua mã. Ngày dạng dd/mm/yyyy.

File `DanhSachHoaDon.xlsx` chia mỗi tháng một sheet, tên sheet ghi tháng và năm.

## File
- `DanhSachHoaDon.xlsx` (xlsx)
- `DanhSachHoaDonChiTiet.xlsx` (xlsx)
- `DanhSachSanPham.xlsx` (xlsx)
- `DanhSachKhachHang.xlsx` (xlsx)
- `BaoCaoTonKho.xlsx` (xlsx)
- `DanhSachNhapHang.xlsx` (xlsx)
- `DanhSachLoHang.xlsx` (xlsx)
- `DanhSachHoaDonChiTietLo.xlsx` (xlsx)
- `DanhSachThuoc.xlsx` (xlsx)
- `DanhSachChiTietNhapHang.xlsx` (xlsx)

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

## Cột trong `DanhSachKhachHang.xlsx`
- **Mã khách hàng**: mã khách
- **Tên khách hàng**: tên
- **Điện thoại**: số điện thoại
- **Địa chỉ**: địa chỉ

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

## Cột trong `DanhSachLoHang.xlsx`
- **Mã nhập hàng**: mã phiếu nhập
- **Mã hàng**: mã hàng
- **Lô**: số lô
- **Hạn sử dụng**: hạn sử dụng
- **Số lượng (ĐVT cơ bản)**: số lượng nhập (đơn vị cơ bản)

## Cột trong `DanhSachHoaDonChiTietLo.xlsx`
- **Mã hóa đơn**: mã đơn
- **STT**: số thứ tự dòng trong đơn
- **Lô**: số lô
- **Số lượng (ĐVT cơ bản)**: số lượng bán lấy từ lô (đơn vị cơ bản)
- **Số lượng trả (ĐVT cơ bản)**: số lượng khách trả lại (đơn vị cơ bản); lớn hơn 0: đơn đó có trả hàng

## Cột trong `DanhSachThuoc.xlsx`
- **Mã hàng**: mã hàng
- **Hoạt chất**: hoạt chất (trống với thực phẩm chức năng, vật tư)
- **Thuốc kê đơn**: thuốc kê đơn

## Cột trong `DanhSachChiTietNhapHang.xlsx`
- **Mã nhập hàng**: mã phiếu nhập
- **STT**: số thứ tự dòng trong phiếu nhập
- **Mã hàng**: mã hàng
- **ĐVT**: đơn vị tính
- **Số lượng**: số lượng
- **Đơn giá**: giá nhập một đơn vị (theo đơn vị nhập của dòng)
- **Lô**: số lô
- **Hạn sử dụng**: hạn sử dụng

## Quy ước
- Dữ liệu có đến hết 13/07/2026.
- **Còn nợ**: **Còn nợ** là số khách còn nợ của đơn, tính đến hết ngày cuối dữ liệu.
- **Tồn kho**: **Tồn cuối kỳ** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
- **Lô, hạn dùng**: mỗi dòng nhập là một lô, số lô không trùng. Một dòng bán có thể lấy từ nhiều lô. Hàng khách trả về lại lô đã bán.
- **Nhập hàng**: **Đơn giá** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Cần trả NCC** là tổng tiền của cả phiếu nhập.
- **Thuốc**: **Thuốc kê đơn** đúng (TRUE/1) là thuốc kê đơn. Hoạt chất ghi không kèm hàm lượng (hàm lượng ở tên hàng); nhiều chất nối bằng " + ".
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng:
  - Panadol Extra hộp 15 vỉ x 12 viên: 1 vỉ = 12 viên
  - Panadol Extra hộp 15 vỉ x 12 viên: 1 hộp = 180 viên
  - Hapacol 250 hộp 24 gói: 1 hộp = 24 gói
  - Panadol 500mg hộp 10 vỉ x 12 viên: 1 vỉ = 12 viên
  - Panadol 500mg hộp 10 vỉ x 12 viên: 1 hộp = 120 viên
  - Tiffy Dey hộp 25 vỉ x 4 viên: 1 vỉ = 4 viên
  - Tiffy Dey hộp 25 vỉ x 4 viên: 1 hộp = 100 viên
  - Berberin 100mg Mekophar chai 100 viên: 1 chai = 100 viên
  - Oresol 245 DHG hộp 20 gói: 1 hộp = 20 gói
  - Amoxicillin 500mg Domesco hộp 10 vỉ x 10 viên: 1 vỉ = 10 viên
  - Amoxicillin 500mg Domesco hộp 10 vỉ x 10 viên: 1 hộp = 100 viên
  - Salonpas cao dán hộp 24 gói x 10 miếng: 1 hộp = 24 gói
  - Decolgen Forte hộp 30 vỉ x 4 viên: 1 vỉ = 4 viên
  - Decolgen Forte hộp 30 vỉ x 4 viên: 1 hộp = 120 viên
  - Khẩu trang y tế 4 lớp Khánh An hộp 50 cái: 1 hộp = 50 cái
  - Smecta hộp 30 gói: 1 hộp = 30 gói
  - Efferalgan 500mg viên sủi hộp 4 vỉ x 4 viên: 1 vỉ = 4 viên
  - Efferalgan 500mg viên sủi hộp 4 vỉ x 4 viên: 1 hộp = 16 viên
  - Phosphalugel hộp 26 gói: 1 hộp = 26 gói
  - Strepsils Cool hộp 2 vỉ x 12 viên: 1 vỉ = 12 viên
  - Strepsils Cool hộp 2 vỉ x 12 viên: 1 hộp = 24 viên
  - Clorpheniramin 4mg DHG hộp 10 vỉ x 20 viên: 1 hộp = 10 vỉ
  - Yumangel hộp 20 gói: 1 hộp = 20 gói
  - Cefuroxim 500mg Vidipha hộp 10 vỉ x 10 viên: 1 vỉ = 10 viên
  - Cefuroxim 500mg Vidipha hộp 10 vỉ x 10 viên: 1 hộp = 100 viên
  - Băng cá nhân Urgo Transparent hộp 100 miếng: 1 hộp = 100 miếng
  - Hapacol 150 hộp 24 gói: 1 hộp = 24 gói
  - Eugica hộp 10 vỉ x 10 viên nang: 1 vỉ = 10 viên
  - Eugica hộp 10 vỉ x 10 viên nang: 1 hộp = 100 viên
  - UPSA-C 1g viên sủi tuýp 10 viên: 1 tuýp = 10 viên
  - Lorastad 10mg Stella hộp 10 vỉ x 10 viên: 1 vỉ = 10 viên
  - Lorastad 10mg Stella hộp 10 vỉ x 10 viên: 1 hộp = 100 viên
  - Cetirizin 10mg Domesco hộp 10 vỉ x 10 viên: 1 vỉ = 10 viên
  - Cetirizin 10mg Domesco hộp 10 vỉ x 10 viên: 1 hộp = 100 viên
  - Amlodipin 5mg Domesco hộp 3 vỉ x 10 viên: 1 vỉ = 10 viên
  - Amlodipin 5mg Domesco hộp 3 vỉ x 10 viên: 1 hộp = 30 viên
  - Panadol Cảm Cúm hộp 15 vỉ x 12 viên: 1 vỉ = 12 viên
  - Panadol Cảm Cúm hộp 15 vỉ x 12 viên: 1 hộp = 180 viên
  - Alaxan hộp 25 vỉ x 4 viên: 1 vỉ = 4 viên
  - Alaxan hộp 25 vỉ x 4 viên: 1 hộp = 100 viên
  - Gofen 400 hộp 5 vỉ x 10 viên nang: 1 vỉ = 10 viên
  - Gofen 400 hộp 5 vỉ x 10 viên nang: 1 hộp = 50 viên
  - Acemuc Kids 200mg hộp 30 gói: 1 hộp = 30 gói
  - Gaviscon hộp 24 gói x 10ml: 1 hộp = 24 gói
  - Enterogermina 2 tỷ/5ml hộp 20 ống: 1 hộp = 20 ống
  - Omeprazol 20mg DHG hộp 3 vỉ x 10 viên: 1 vỉ = 10 viên
  - Omeprazol 20mg DHG hộp 3 vỉ x 10 viên: 1 hộp = 30 viên
  - Vitamin C 500mg Quapharco hộp 10 vỉ x 10 viên: 1 vỉ = 10 viên
  - Vitamin C 500mg Quapharco hộp 10 vỉ x 10 viên: 1 hộp = 100 viên
  - Efticol 0,9% lốc 10 lọ x 10ml: 1 lốc = 10 lọ
  - Magne-B6 Corbière hộp 5 vỉ x 10 viên: 1 vỉ = 10 viên
  - Magne-B6 Corbière hộp 5 vỉ x 10 viên: 1 hộp = 50 viên
  - Loperamid 2mg Domesco hộp 5 vỉ x 10 viên: 1 vỉ = 10 viên
  - Loperamid 2mg Domesco hộp 5 vỉ x 10 viên: 1 hộp = 50 viên
  - Metformin Stella 500mg hộp 6 vỉ x 10 viên: 1 vỉ = 10 viên
  - Metformin Stella 500mg hộp 6 vỉ x 10 viên: 1 hộp = 60 viên
  - Clarityne 10mg hộp 1 vỉ x 10 viên: 1 hộp = 10 viên
  - Zyrtec 10mg hộp 1 vỉ x 10 viên: 1 hộp = 10 viên
  - Telfast HD 180mg hộp 3 vỉ x 10 viên: 1 vỉ = 10 viên
  - Telfast HD 180mg hộp 3 vỉ x 10 viên: 1 hộp = 30 viên
  - Hagifen 400mg DHG hộp 10 vỉ x 10 viên: 1 vỉ = 10 viên
  - Hagifen 400mg DHG hộp 10 vỉ x 10 viên: 1 hộp = 100 viên
  - Enervon hộp 10 vỉ x 10 viên: 1 vỉ = 10 viên
  - Enervon hộp 10 vỉ x 10 viên: 1 hộp = 100 viên
  - Savi Losartan 50mg hộp 3 vỉ x 10 viên: 1 vỉ = 10 viên
  - Savi Losartan 50mg hộp 3 vỉ x 10 viên: 1 hộp = 30 viên
  - Air-X 80mg viên nhai hộp 10 vỉ x 10 viên: 1 vỉ = 10 viên
  - Air-X 80mg viên nhai hộp 10 vỉ x 10 viên: 1 hộp = 100 viên
  - Biosubtyl-II hộp 25 gói: 1 hộp = 25 gói
  - Berocca Performance viên sủi tuýp 10 viên: 1 tuýp = 10 viên
  - Prednisolon 5mg Boston chai 500 viên: 1 chai = 500 viên
  - Bio-acimin Gold men vi sinh hộp 30 gói: 1 hộp = 30 gói
  - Boganic Traphaco hộp 5 vỉ x 20 viên: 1 vỉ = 20 viên
  - Boganic Traphaco hộp 5 vỉ x 20 viên: 1 hộp = 100 viên
  - Calcium Corbière Extra 10ml hộp 30 ống: 1 hộp = 30 ống
  - Bisolvon 8mg hộp 3 vỉ x 10 viên: 1 vỉ = 10 viên
  - Bisolvon 8mg hộp 3 vỉ x 10 viên: 1 hộp = 30 viên
