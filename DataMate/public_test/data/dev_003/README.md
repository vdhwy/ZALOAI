# Dữ liệu dev_003

Chủ tiệm gửi dữ liệu từ bốn nguồn: file Excel xuất từ phần mềm bán hàng (tên file bắt đầu BanHang_), sổ chủ tiệm tự ghi trên Excel (SoTay_), file tồn kho CSV, và báo cáo tiền mặt theo ca. Các file nối với nhau qua mã hoá đơn, mã hàng; sổ tay không có mã hàng, nối qua tên hàng. Tên cột mỗi file đặt theo cách của tiệm.

Hóa đơn và chi tiết hóa đơn gộp chung sheet `BanHang`: mỗi dòng là một dòng hàng, thông tin hóa đơn lặp lại trên mọi dòng của cùng hóa đơn. Cột **SĐT** lấy theo danh sách khách hàng. Sheet bán hàng dài quá một file nên tách theo năm, mỗi năm một file. File và sheet: `BanHang_TongHop_2025.xlsx`: sheet `BanHang`, `BanHang_HangHoa`, `BanHang_KhachHang`, `BanHang_DonViQuyDoi`, `BanHang_LichSuGia`; `BanHang_TongHop_2026.xlsx`: sheet `BanHang`. Danh sách không có trong các file này nằm ở file riêng: `BanHang_PhieuThu.xlsx`, `SoTay_NhapHang.xlsx`, `SoTay_ChiPhi.xlsx`, `ton_kho.csv`.

## File
- `BanHang_TongHop_2025.xlsx` (xlsx)
- `BanHang_TongHop_2026.xlsx` (xlsx)
- `BanHang_PhieuThu.xlsx` (xlsx)
- `SoTay_NhapHang.xlsx` (xlsx)
- `SoTay_ChiPhi.xlsx` (xlsx)
- `ton_kho.csv` (csv)
- `BaoCaoCa.xlsx` (xlsx): báo cáo tiền mặt thu trong từng ca, mỗi ca một dòng: ngày, ca, mã nhân viên đứng ca, tiền mặt khách trả trong ca (gồm tiền trả nợ), tiền mặt trả lại khách trả hàng, tiền mặt ròng của ca (tiền mặt thu trừ tiền mặt hoàn khách; không gồm các khoản chi của cửa hàng).

## Quy ước
- Dữ liệu có đến hết 21/08/2026.
- **Công nợ**: mỗi lần khách trả tiền cho một đơn là một dòng, **Tiền thu** là số tiền trả lần đó; **Tổng thanh toán** là số khách phải trả cho cả đơn; **Công nợ** là số tiền của đơn chưa thu, tính đến hết ngày cuối dữ liệu.
- **Giá vốn**: **Giá vốn lúc bán** là giá vốn một đơn vị bán.
- **Sổ chi phí**: các khoản chi vận hành theo tháng (tiền **Tiền chi**).
- **Tồn kho**: **Ton kho** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
- **Nhập hàng**: **Giá nhập** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Thành tiền** là tiền nhập của cả dòng.
- **Giá bán**: **Giá mới** (theo đơn vị cơ bản) áp dụng từ **Ngày áp dụng** đến trước lần đổi giá sau của cùng mặt hàng; dòng đầu mỗi mặt hàng là giá lúc bắt đầu dữ liệu (**Giá cũ** trống).
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `BanHang_TongHop_2025.xlsx`.
