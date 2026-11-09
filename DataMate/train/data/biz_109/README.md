# Dữ liệu biz_109

File máy POS xuất ra.

Các danh sách `DanhSachHoaDon`, `DanhSachSanPham`, `DanhSachKhachHang`, `BaoCaoTonKho`, `DanhSachNhapHang`, `DanhSachChiTietNhapHang`, `SoQuy`, `DanhSachDonViTinh` nằm chung file `DuLieuBanHang.xlsx`, mỗi danh sách một sheet.

## File
- `DuLieuBanHang.xlsx` (xlsx)
- `DanhSachHoaDonChiTiet.xlsx` (xlsx)

## Quy ước
- Dữ liệu có đến hết 05/08/2026.
- **Công nợ**: mỗi lần khách trả tiền cho một đơn là một dòng, **Giá trị** là số tiền trả lần đó; **Tổng sau giảm giá** là số khách phải trả cho cả đơn.
- **Giá vốn**: **Giá vốn** là giá vốn một đơn vị bán.
- **Tồn kho**: **Tồn cuối kỳ** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
- **Nhập hàng**: **Đơn giá** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Cần trả NCC** là tổng tiền của cả phiếu nhập.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `DuLieuBanHang.xlsx`.
