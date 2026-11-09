# Dữ liệu biz_124

Chủ tiệm gửi dữ liệu từ ba nguồn: file Excel xuất từ phần mềm bán hàng (tên file bắt đầu BanHang_, mỗi danh sách một file, danh sách dài tách thành nhiều file đánh số _1, _2…), sổ chủ tiệm tự ghi trên Excel (SoTay_), và file tồn kho CSV. Các file nối với nhau qua mã hoá đơn, mã hàng; sổ tay không có mã hàng, nối qua tên hàng. Tên cột mỗi file đặt theo cách của tiệm.

## File
- `BanHang_HoaDon.xlsx` (xlsx)
- `BanHang_ChiTietHoaDon.xlsx` (xlsx)
- `BanHang_PhieuThu.xlsx` (xlsx)
- `BanHang_HangHoa.xlsx` (xlsx)
- `BanHang_KhachHang.xlsx` (xlsx)
- `BanHang_DonViQuyDoi.xlsx` (xlsx)
- `BanHang_LichSuGia.xlsx` (xlsx)
- `BanHang_LoHang.xlsx` (xlsx)
- `BanHang_BanTheoLo.xlsx` (xlsx)
- `BanHang_Thuoc.xlsx` (xlsx)
- `SoTay_NhapHang.xlsx` (xlsx)
- `SoTay_ChiPhi.xlsx` (xlsx)
- `ton_kho.csv` (csv)

## Quy ước
- Dữ liệu có đến hết 25/05/2026.
- **Công nợ**: mỗi lần khách trả tiền cho một đơn là một dòng, **Số tiền thu** là số tiền trả lần đó; **Tong tien** là số khách phải trả cho cả đơn; **Còn nợ** là số tiền của đơn chưa thu, tính đến hết ngày cuối dữ liệu.
- **Giá vốn**: **Giá vốn lúc bán** là giá vốn một đơn vị bán.
- **Sổ chi phí**: các khoản chi vận hành theo tháng (tiền **So tien**).
- **Tồn kho**: **Ton kho** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
- **Lô, hạn dùng**: mỗi dòng nhập là một lô, số lô không trùng. Một dòng bán có thể lấy từ nhiều lô. Hàng khách trả về lại lô đã bán.
- **Nhập hàng**: **Giá nhập** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Thành tiền** là tiền nhập của cả dòng.
- **Giá bán**: **Giá mới** (theo đơn vị cơ bản) áp dụng từ **Ngày áp dụng** đến trước lần đổi giá sau của cùng mặt hàng; dòng đầu mỗi mặt hàng là giá lúc bắt đầu dữ liệu (**Giá cũ** trống).
- **Thuốc**: **Kê đơn** đúng (TRUE/1) là thuốc kê đơn. Hoạt chất ghi không kèm hàm lượng (hàm lượng ở tên hàng); nhiều chất nối bằng " + ".
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `BanHang_DonViQuyDoi.xlsx`.
