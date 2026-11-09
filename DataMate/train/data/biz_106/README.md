# Dữ liệu biz_106

File máy POS xuất ra.

## File
- `DanhSachHoaDon.xlsx` (xlsx)
- `DanhSachHoaDonChiTiet_1.xlsx` (xlsx)
- `DanhSachHoaDonChiTiet_2.xlsx` (xlsx)
- `DanhSachSanPham.xlsx` (xlsx)
- `DanhSachKhachHang.xlsx` (xlsx)
- `BaoCaoTonKho.xlsx` (xlsx)
- `DanhSachNhapHang.xlsx` (xlsx)
- `DanhSachChiTietNhapHang.xlsx` (xlsx)
- `SoQuy.xlsx` (xlsx)
- `DanhSachDonViTinh.xlsx` (xlsx)

## Quy ước
- Dữ liệu có đến hết 14/09/2026.
- **Công nợ**: mỗi lần khách trả tiền cho một đơn là một dòng, **Giá trị** là số tiền trả lần đó; **Tổng sau giảm giá** là số khách phải trả cho cả đơn.
- **Giá vốn**: **Giá vốn** là giá vốn một đơn vị bán.
- **Tồn kho**: **Tồn cuối kỳ** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
- **Nhập hàng**: **Đơn giá** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Cần trả NCC** là tổng tiền của cả phiếu nhập.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `DanhSachDonViTinh.xlsx`.
