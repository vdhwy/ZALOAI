# Dữ liệu dev_004

Sổ bán hàng ghi tay chuyển sang Excel, mỗi tháng một sheet.

## File
- `SoBanHang.xlsx` (xlsx)
- `DanhMuc.xlsx` (xlsx)
- `TonKho.xlsx` (xlsx)
- `SoGiaoHang.xlsx` (xlsx)
- `SoHanNo.xlsx` (xlsx)
- `SoNhapHang.xlsx` (xlsx)
- `BangGia.xlsx` (xlsx)

## Cột trong `SoBanHang.xlsx`
- **Khách hàng (tên)**: tên khách (Khách lẻ nếu không lưu)
- **Giờ**: giờ đặt đơn (dòng trả hàng: lúc trả)
- **Thời gian**: ngày bán
- **Ma don**: mã đơn
- **SL bán**: số lượng
- **dvt**: đơn vị tính
- **Hàng bán**: tên hàng
- **Trạng thái xử lý**: trạng thái đơn
- **Giá 1 đv**: đơn giá
- **Amount**: thành tiền sau giảm
- **Tổng phiếu**: tổng tiền của cả phiếu

## Cột trong `DanhMuc.xlsx`
- **Hàng**: tên hàng (file chỉ có mặt hàng có đơn vị lớn)
- **Hệ số**: hệ số: số đơn vị cơ bản trong 1 đơn vị lớn
- **ĐV gốc**: đơn vị cơ bản
- **Loại ĐV**: đơn vị lớn (thùng, hộp, tấn...)

## Cột trong `TonKho.xlsx`
- **Tồn cuối**: tồn kho (đơn vị cơ bản)
- **ĐV gốc**: đơn vị cơ bản
- **Tên sản phẩm**: tên hàng

## Cột trong `SoGiaoHang.xlsx`
- **Số lượng giao**: số lượng đã đổi ra đơn vị cơ bản
- **Biển số xe**: biển số xe
- **Lượt giao**: đợt giao (1, 2, 3)
- **Số đơn**: mã đơn
- **Thời gian giao**: ngày giao
- **Hàng hóa**: tên hàng
- **Lái xe**: tài xế
- **ĐV gốc**: đơn vị cơ bản

## Cột trong `SoHanNo.xlsx`
- **Mã đơn hàng**: mã đơn
- **Kỳ hạn**: số ngày được nợ
- **Ngày phải trả**: hạn thanh toán

## Cột trong `SoNhapHang.xlsx`
- **Product**: tên hàng
- **ĐVT**: đơn vị nhập
- **Số phiếu**: mã phiếu nhập
- **Ghi chú**: ghi chú
- **Nhà cung cấp**: nhà cung cấp
- **Thành tiền**: tiền nhập của cả dòng
- **Giá nhập**: giá nhập một đơn vị (theo đơn vị nhập của dòng)
- **Ngày nhập**: ngày nhập
- **SL nhập**: số lượng nhập

## Cột trong `BangGia.xlsx`
- **Giá cũ**: giá trước lần đổi (trống ở dòng đầu mỗi mặt hàng)
- **Ngày áp dụng**: ngày bắt đầu áp dụng giá
- **Giá mới**: giá bán áp dụng từ ngày đó (đơn vị cơ bản)
- **Diễn giải**: tên hàng

## Quy ước
- Dữ liệu có đến hết 10/06/2026.
- **Trả hàng**: hàng trả ghi số lượng âm, cùng mã đơn với đơn đã bán: đơn có dòng số lượng âm là đơn có trả hàng.
- **Tồn kho**: **Tồn cuối** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
- **Hạn thanh toán**: chỉ đơn bán nợ có hạn. **Ngày phải trả** là ngày khách phải trả hết đơn; **Kỳ hạn** là số ngày được nợ, tính từ ngày đặt.
- **Giao hàng**: đơn không huỷ có ít nhất một mặt hàng nhóm cát đá, gạch, sắt thép, xi măng thì được giao tận nơi mọi mặt hàng của đơn, 1–3 đợt (**Lượt giao**); đơn khác khách tự chở, không có trong sổ giao; đơn đặt mấy ngày cuối dữ liệu có thể chưa giao. **Số lượng giao** tính theo đơn vị cơ bản.
- **Nhập hàng**: **Giá nhập** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Thành tiền** là tiền nhập của cả dòng.
- **Giá bán**: **Giá mới** (theo đơn vị cơ bản) áp dụng từ **Ngày áp dụng** đến trước lần đổi giá sau của cùng mặt hàng; dòng đầu mỗi mặt hàng là giá lúc bắt đầu dữ liệu (**Giá cũ** trống).
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `DanhMuc.xlsx`.
- **Hàng theo bó**: Ống PVC Bình Minh D32 cây 4m, Ống PVC Bình Minh D50 cây 4m, Ống PVC Bình Minh D90 cây 4m bán theo bó, 1 bó = 10 cây; khách lấy nguyên bó thì sổ ghi số bó.
