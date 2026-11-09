# Dữ liệu biz_121

File Excel xuất từ phần mềm bán hàng. File đơn hàng mỗi dòng một sản phẩm.

Các danh sách `DanhSachQuyDoi`, `DanhSachSanPham`, `DonNhapHang`, `DonNhapHang_ChiTiet`, `DonHang_Lo`, `DanhSachThuoc` nằm chung file `DuLieuXuat.xlsx`, mỗi danh sách một sheet.

## File
- `DonHang_ChiTiet.xlsx` (xlsx)
- `DuLieuXuat.xlsx` (xlsx)

## Cột trong `DonHang_ChiTiet.xlsx`
- **Mã đơn hàng**: mã đơn
- **Ngày đặt hàng**: ngày bán
- **Trạng thái đơn hàng**: trạng thái đơn
- **Tên khách hàng**: tên khách (Khách lẻ nếu không lưu)
- **Tên sản phẩm**: tên hàng
- **Số lượng sản phẩm**: số lượng
- **Giá sản phẩm**: đơn giá
- **Tổng tiền**: thành tiền sau giảm
- **Đơn vị tính**: đơn vị tính

## Cột trong `DuLieuXuat.xlsx`, sheet `DanhSachQuyDoi`
- **Tên sản phẩm**: tên hàng (file chỉ có mặt hàng có đơn vị lớn)
- **Đơn vị quy đổi**: đơn vị lớn (thùng, hộp, tấn...)
- **Tỉ lệ quy đổi**: hệ số: số đơn vị cơ bản trong 1 đơn vị lớn
- **Đơn vị cơ bản**: đơn vị cơ bản

## Cột trong `DuLieuXuat.xlsx`, sheet `DanhSachSanPham`
- **Mã SKU**: mã hàng
- **Tên sản phẩm**: tên
- **Đơn vị**: đơn vị cơ bản
- **Loại sản phẩm**: nhóm hàng

## Cột trong `DuLieuXuat.xlsx`, sheet `DonNhapHang`
- **Mã đơn nhập**: mã phiếu nhập
- **Ngày nhập**: ngày nhập
- **Mã nhà cung cấp**: mã nhà cung cấp

## Cột trong `DuLieuXuat.xlsx`, sheet `DonNhapHang_ChiTiet`
- **Mã đơn nhập**: mã phiếu nhập
- **Mã SKU**: mã hàng
- **Mã lô**: số lô
- **Hạn sử dụng**: hạn sử dụng
- **Số lượng nhập**: số lượng nhập (đơn vị cơ bản)

## Cột trong `DuLieuXuat.xlsx`, sheet `DonHang_Lo`
- **Mã đơn hàng**: mã đơn
- **Mã lô**: số lô
- **Số lượng**: số lượng bán lấy từ lô (đơn vị cơ bản)
- **Số lượng trả**: số lượng khách trả lại (đơn vị cơ bản); lớn hơn 0: đơn đó có trả hàng

## Cột trong `DuLieuXuat.xlsx`, sheet `DanhSachThuoc`
- **Mã SKU**: mã hàng
- **Hoạt chất**: hoạt chất (trống với thực phẩm chức năng, vật tư)
- **Thuốc kê đơn**: thuốc kê đơn

## Quy ước
- Dữ liệu có đến hết 20/09/2026.
- **Lô, hạn dùng**: mỗi dòng nhập là một lô, số lô không trùng. Một dòng bán có thể lấy từ nhiều lô. Hàng khách trả về lại lô đã bán.
- **Thuốc**: **Thuốc kê đơn** đúng (TRUE/1) là thuốc kê đơn. Hoạt chất ghi không kèm hàm lượng (hàm lượng ở tên hàng); nhiều chất nối bằng " + ".
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `DuLieuXuat.xlsx`.
