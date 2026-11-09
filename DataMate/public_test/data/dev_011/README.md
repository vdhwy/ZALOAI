# Dữ liệu dev_011

Sổ bán hàng của cửa hàng điện thoại, chủ tiệm tự ghi trên Excel: sheet `Ghi tắt` (cách ghi tắt tên hàng và loại hàng) và sheet `Sổ bán hàng` cả kỳ, mỗi dòng một mặt hàng của một đơn.

## File
- `SoBanHang.xlsx` (xlsx)

## Cột trong `SoBanHang.xlsx`
- **Ngày**: ngày bán
- **STT**: số thứ tự đơn (hoá đơn) trong sổ
- **Khách**: tên khách (khách không lưu: khách lẻ)
- **Hàng**: hàng bán, có thể ghi tắt (tra ở sheet Ghi tắt)
- **IMEI**: IMEI của máy bán (máy mới, máy cũ), dòng 2 máy ghi 2 số cách nhau " / "; phụ kiện để trống
- **SL**: số lượng
- **Giá**: đơn giá một máy / một cái
- **Thành tiền**: thành tiền của dòng
- **Bớt**: tiền bớt cho cả đơn (trống: không bớt)
- **Thu máy cũ**: tiền thu máy cũ của khách, trừ vào tiền đơn (trống: không thu máy)
- **Khách trả**: số tiền khách trả cho cả đơn, đã trừ bớt và thu máy cũ
- **Ghi chú**: ghi chú của đơn; đơn khách trả lại hàng ghi ở đây

## Quy ước
- Dữ liệu có đến hết 31/07/2026.
- **Đơn khách trả lại**: **Ghi chú** của đơn ghi khách trả lại.
- **Tiền khách trả**: **Khách trả** là số tiền khách trả cho cả đơn (không phải của dòng), đã bớt và đã trừ tiền thu máy cũ; ô bớt, thu máy cũ để trống là không có khoản đó.
- **Ghi tắt, loại hàng**: sheet `Ghi tắt` cho tên đầy đủ và loại hàng (máy mới, máy cũ, phụ kiện) của từng cách ghi tắt. Máy có IMEI (**IMEI**), phụ kiện không.
