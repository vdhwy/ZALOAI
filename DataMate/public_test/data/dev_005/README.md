# Dữ liệu dev_005

File Excel xuất từ phần mềm bán hàng. File đơn hàng mỗi dòng một sản phẩm.

Dữ liệu bán hàng xuất theo tháng, mỗi tháng một file (tách theo tháng, không theo năm): từ `BanHang_Thang01_2025.xlsx` đến `BanHang_Thang05_2026.xlsx` (17 file), các tháng cùng cột; mỗi file có sheet `DonHang_ChiTiet`.

## File
- `BanHang_Thang<tháng>_<năm>.xlsx` (xlsx)
- `DanhSachQuyDoi.xlsx` (xlsx)
- `DanhSachSanPham.xlsx` (xlsx)
- `DonNhapHang.xlsx` (xlsx)
- `DonNhapHang_ChiTiet.xlsx` (xlsx)
- `DonHang_Lo.xlsx` (xlsx)
- `DanhSachThuoc.xlsx` (xlsx)

## Cột trong `BanHang_Thang<tháng>_<năm>.xlsx`, sheet `DonHang_ChiTiet`
- **Mã đơn hàng**: mã đơn
- **Ngày đặt hàng**: ngày bán
- **Trạng thái đơn hàng**: trạng thái đơn
- **Tên khách hàng**: tên khách (Khách lẻ nếu không lưu)
- **Tên sản phẩm**: tên hàng
- **Số lượng sản phẩm**: số lượng
- **Giá sản phẩm**: đơn giá
- **Tổng tiền**: thành tiền sau giảm
- **Đơn vị tính**: đơn vị tính

## Cột trong `DanhSachQuyDoi.xlsx`
- **Tên sản phẩm**: tên hàng (file chỉ có mặt hàng có đơn vị lớn)
- **Đơn vị quy đổi**: đơn vị lớn (thùng, hộp, tấn...)
- **Tỉ lệ quy đổi**: hệ số: 1 đơn vị lớn bằng bấy nhiêu đơn vị ngay dưới nó; số kèm tên đơn vị là tính theo đơn vị đó, chỉ có số là tính theo đơn vị cơ bản
- **Đơn vị cơ bản**: đơn vị cơ bản

## Cột trong `DanhSachSanPham.xlsx`
- **Mã SKU**: mã hàng
- **Tên sản phẩm**: tên
- **Đơn vị**: đơn vị cơ bản
- **Loại sản phẩm**: nhóm hàng

## Cột trong `DonNhapHang.xlsx`
- **Mã đơn nhập**: mã phiếu nhập
- **Ngày nhập**: ngày nhập
- **Mã nhà cung cấp**: mã nhà cung cấp

## Cột trong `DonNhapHang_ChiTiet.xlsx`
- **Mã đơn nhập**: mã phiếu nhập
- **Mã SKU**: mã hàng
- **Mã lô**: số lô
- **Hạn sử dụng**: hạn sử dụng
- **Số lượng nhập**: số lượng nhập (đơn vị cơ bản)

## Cột trong `DonHang_Lo.xlsx`
- **Mã đơn hàng**: mã đơn
- **Mã lô**: số lô
- **Số lượng**: số lượng bán lấy từ lô (đơn vị cơ bản)
- **Số lượng trả**: số lượng khách trả lại (đơn vị cơ bản); lớn hơn 0: đơn đó có trả hàng

## Cột trong `DanhSachThuoc.xlsx`
- **Mã SKU**: mã hàng
- **Hoạt chất**: hoạt chất (trống với thực phẩm chức năng, vật tư)
- **Thuốc kê đơn**: thuốc kê đơn

## Quy ước
- Dữ liệu có đến hết 10/05/2026.
- **Lô, hạn dùng**: mỗi dòng nhập là một lô, số lô không trùng. Một dòng bán có thể lấy từ nhiều lô. Hàng khách trả về lại lô đã bán.
- **Thuốc**: **Thuốc kê đơn** đúng (TRUE/1) là thuốc kê đơn. Hoạt chất ghi không kèm hàm lượng (hàm lượng ở tên hàng); nhiều chất nối bằng " + ".
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `DanhSachQuyDoi.xlsx`; sản phẩm có nhiều đơn vị lớn thì hệ số ghi theo đơn vị ngay dưới.
