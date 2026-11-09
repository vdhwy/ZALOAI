# Dữ liệu dev_014

Cửa hàng điện thoại gửi các sổ tự ghi trên Excel (mục File): sổ bán hàng (sheet `Ghi tắt` và mỗi tháng một sheet) và các sổ phụ: sổ thu máy cũ một file; sổ nợ, sổ góp, sổ bảo hành chung một file, mỗi sổ một sheet. Các sổ nối với nhau qua số thứ tự đơn trong sổ bán, IMEI và tên, số điện thoại của khách.

## File
- `SoBanHang.xlsx` (xlsx)
- `ThuMayCu.xlsx` (xlsx)
- `SoNo.xlsx` (xlsx)

## Quy ước
- Dữ liệu có đến hết 30/09/2026.
- **Đơn**: các dòng cùng **STT** là một đơn; khách, bớt, khách trả, ghi chú của đơn lặp lại ở mọi dòng của đơn.
- **Đơn khách trả lại**: **Ghi chú** của đơn ghi khách trả lại.
- **Tiền khách trả**: **Khách trả** là số tiền khách trả cho cả đơn (không phải của dòng), đã bớt và đã trừ tiền thu máy cũ; ô bớt, thu máy cũ để trống là không có khoản đó.
- **Ghi tắt, loại hàng**: sheet `Ghi tắt` cho tên đầy đủ và loại hàng (máy mới, máy cũ, phụ kiện) của từng cách ghi tắt. Máy có IMEI (**IMEI**), phụ kiện không.
- **Thu máy cũ**: sổ thu máy cũ ghi máy khách đưa, giá thu (**Giá thu**) trừ vào tiền đơn có số thứ tự **Trừ vào (STT sổ bán)** ở sổ bán; **Khách trả** ở sổ bán đã trừ khoản này.
- **Sổ nợ**: chỉ đơn khách còn nợ sau lúc mua, trừ đơn trả góp (ở sổ góp). Dòng đầu mỗi đơn ghi ngày mua, khách, **Nợ** là số còn nợ sau khi trả lúc mua. Các lần khách trả sau đó ghi ở **Đã trả**, **Ngày trả**: lần đầu ngay ở dòng đầu đơn, mỗi lần sau một dòng riêng. **Ghi chú** ghi số thứ tự đơn ở sổ bán. Đơn ghi nợ vẫn ghi đủ ở sổ bán, **Khách trả** là tiền cả đơn.
- **Sổ góp**: mỗi đơn trả góp có dòng đầu ghi ngày mua, số thứ tự đơn ở sổ bán, khách, máy, **Giá** là tiền cả đơn, **Trả trước** là tiền trả lúc mua, còn lại chia đều **Số kỳ** kỳ, mỗi kỳ **Góp/tháng**. Kỳ thứ nhất có hạn vào ngày **Hạn góp (ngày)** của tháng ngay sau tháng mua, hạn kỳ sau là cùng ngày tháng kế tiếp. Mỗi lần khách góp ghi **Ngày góp**, **Đã góp**: lần đầu ở dòng đầu đơn, mỗi lần sau một dòng có **STT**. Đơn trả góp vẫn ghi đủ giá ở sổ bán.
- **Sổ bảo hành**: mỗi lần khách mang máy tới bảo hành một dòng (**Ngày nhận**), máy nhận theo **IMEI**; một máy có thể tới nhiều lần. **Máy** ghi dòng máy (không ghi dung lượng, màu; máy mới và máy cũ cùng dòng ghi như nhau). Bảo hành không thu tiền, không phải đơn bán.
