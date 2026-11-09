# Dữ liệu dev_006

File máy POS xuất ra.

## File
- `pos.sqlite` (sqlite)

## Bảng
`chi_nhanh`, `nhan_vien`, `khach_hang`, `nha_cung_cap`, `san_pham`, `don_vi_sp`, `phieu_nhap`, `chi_tiet_nhap`, `don_hang`, `chi_tiet_don`, `thanh_toan`, `tra_hang`, `the_kho`, `lich_su_gia`, `lo_hang`, `chi_tiet_don_lo`, `thong_tin_thuoc`

Mã đơn nối `don_hang` với `chi_tiet_don`. Ngày giờ dạng text.

## Quy ước
- Dữ liệu có đến hết 08/08/2026.
- **Dòng hàng**: `chi_tiet_don.TriGia` là thành tiền của dòng (đã trừ giảm giá dòng); `chi_tiet_don.SLQuyDoi` là số lượng đã đổi ra đơn vị cơ bản.
- **Mã tham chiếu**: `don_hang.MaCaLam` là mã ca bán hàng; `don_hang.MaKhuyenMai` là mã khuyến mãi áp cho đơn (trống: không áp); `the_kho.KieuChungTu`, `the_kho.MaChungTu` là loại và số của chứng từ gốc của dòng thẻ kho (đơn bán, phiếu nhập hoặc phiếu khách trả).
- **Công nợ**: mỗi lần khách trả tiền cho một đơn là một dòng, `thanh_toan.SoTienThu` là số tiền trả lần đó; `don_hang.TongThanhToan` là số khách phải trả cho cả đơn.
- **Giá vốn**: `chi_tiet_don.GiaVonLucBan` là giá vốn một đơn vị bán.
- **Tồn kho**: mỗi dòng `the_kho.TonCuoi` là tồn sau lần nhập/bán/trả đó, theo đơn vị cơ bản; tồn tại một thời điểm là tồn ở dòng cuối của sản phẩm tính đến thời điểm đó.
- **Lô, hạn dùng**: mỗi dòng nhập là một lô, số lô không trùng. Một dòng bán có thể lấy từ nhiều lô. Hàng khách trả về lại lô đã bán.
- **Nhập hàng**: `chi_tiet_nhap.DonGiaNhap` là giá nhập một đơn vị, theo đơn vị nhập của dòng; `phieu_nhap.TongGiaTriNhap` là tổng tiền của cả phiếu nhập.
- **Giá bán**: `lich_su_gia.GiaBanLe` (theo đơn vị cơ bản) áp dụng từ `lich_su_gia.NgayApDung` đến trước lần đổi giá sau của cùng mặt hàng; dòng đầu mỗi mặt hàng là giá lúc bắt đầu dữ liệu.
- **Thuốc**: `thong_tin_thuoc.BanTheoDon` đúng (TRUE/1) là thuốc kê đơn. Hoạt chất ghi không kèm hàm lượng (hàm lượng ở tên hàng); nhiều chất nối bằng " + ".
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở bảng `don_vi_sp`.
