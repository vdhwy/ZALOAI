# Dữ liệu biz_110

Danh sách hoá đơn, một file CSV: mỗi dòng một đơn hàng (hoá đơn), không có chi tiết mặt hàng trong đơn.

## File
- `danh_sach_hoa_don.csv` (csv)

## Cột trong `danh_sach_hoa_don.csv`
- **Tien hang**: tiền hàng của đơn: cộng thành tiền các mặt hàng, trước giảm giá của đơn, chưa gồm phí giao
- **TongTien**: số khách phải trả cho cả đơn (đã tính giảm giá của đơn và phí giao)
- **Mã bill**: mã đơn
- **Bên mua**: tên khách (Khách lẻ nếu không lưu)
- **Ngày giao dịch**: ngày bán
- **Status**: trạng thái đơn
- **Da tra**: đã thanh toán
- **Chưa trả**: số khách còn nợ của đơn (đơn huỷ: 0)

## Quy ước
- Dữ liệu có đến hết 03/07/2026.
- **Còn nợ**: **Chưa trả** là số khách còn nợ của đơn, tính đến hết ngày cuối dữ liệu.
