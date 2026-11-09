# Dữ liệu dev_009

Danh sách hoá đơn, một file CSV: mỗi dòng một đơn hàng (hoá đơn), không có chi tiết mặt hàng trong đơn.

## File
- `danh_sach_hoa_don.csv` (csv)

## Cột trong `danh_sach_hoa_don.csv`
- **Ngày tháng**: ngày bán
- **Trạng thái đơn**: trạng thái đơn
- **TongTien**: số khách phải trả cho cả đơn (đã tính giảm giá của đơn và phí giao)
- **Mã hóa đơn**: mã đơn
- **Nợ**: số khách còn nợ của đơn (đơn huỷ: 0)
- **Đã thu**: đã thanh toán
- **Đối tác**: tên khách (Khách lẻ nếu không lưu)
- **Giá trị hàng**: tiền hàng của đơn: cộng thành tiền các mặt hàng, trước giảm giá của đơn, chưa gồm phí giao

## Quy ước
- Dữ liệu có đến hết 24/06/2026.
- **Còn nợ**: **Nợ** là số khách còn nợ của đơn, tính đến hết ngày cuối dữ liệu.
