# Dữ liệu biz_105

Sổ bán hàng ghi tay chuyển sang Excel, mỗi tháng một sheet.

## File
- `SoBanHang_1.xlsx` (xlsx)
- `SoBanHang_2026.xlsx` (xlsx)
- `DanhMuc.xlsx` (xlsx)
- `TonKho.xlsx` (xlsx)
- `SoNhapHang.xlsx` (xlsx)
- `BangGia.xlsx` (xlsx)

## Cột trong `SoBanHang_1.xlsx`
- **Hàng**: tên hàng
- **so_luong**: số lượng
- **Unit**: đơn vị tính
- **Trị giá**: thành tiền sau giảm
- **Status**: trạng thái đơn
- **Giá lẻ**: đơn giá
- **Giờ**: giờ đặt đơn (dòng trả hàng: lúc trả)
- **Mã hóa đơn**: mã đơn
- **Ngày giao dịch**: ngày bán
- **Khách**: tên khách (Khách lẻ nếu không lưu)

## Cột trong `SoBanHang_2026.xlsx`
- **Hàng**: tên hàng
- **so_luong**: số lượng
- **Unit**: đơn vị tính
- **Trị giá**: thành tiền sau giảm
- **Status**: trạng thái đơn
- **Giá lẻ**: đơn giá
- **Giờ**: giờ đặt đơn (dòng trả hàng: lúc trả)
- **Mã hóa đơn**: mã đơn
- **Ngày giao dịch**: ngày bán
- **Khách**: tên khách (Khách lẻ nếu không lưu)

## Cột trong `DanhMuc.xlsx`
- **Tên món**: tên hàng (file chỉ có mặt hàng có đơn vị lớn)
- **Đơn vị gốc**: đơn vị cơ bản
- **ĐV nhập**: đơn vị lớn (thùng, hộp, tấn...)
- **Hệ số**: hệ số: số đơn vị cơ bản trong 1 đơn vị lớn

## Cột trong `TonKho.xlsx`
- **Hàng hóa**: tên hàng
- **Đơn vị tính**: đơn vị cơ bản
- **Tồn cuối**: tồn kho (đơn vị cơ bản)

## Cột trong `SoNhapHang.xlsx`
- **Số phiếu**: mã phiếu nhập
- **Ngày nhập**: ngày nhập
- **Ghi chu**: ghi chú
- **Thành tiền**: tiền nhập của cả dòng
- **Nhà cung cấp**: nhà cung cấp
- **Tên mặt hàng**: tên hàng
- **Giá nhập**: giá nhập một đơn vị (theo đơn vị nhập của dòng)
- **ĐVT**: đơn vị nhập
- **SL nhập**: số lượng nhập

## Cột trong `BangGia.xlsx`
- **Ngày áp dụng**: ngày bắt đầu áp dụng giá
- **ten_hang**: tên hàng
- **Giá mới**: giá bán áp dụng từ ngày đó (đơn vị cơ bản)
- **Giá cũ**: giá trước lần đổi (trống ở dòng đầu mỗi mặt hàng)

## Quy ước
- Dữ liệu có đến hết 24/06/2026.
- **Trả hàng**: hàng trả ghi số lượng âm, cùng mã đơn với đơn đã bán: đơn có dòng số lượng âm là đơn có trả hàng.
- **Tồn kho**: **Tồn cuối** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
- **Nhập hàng**: **Giá nhập** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Thành tiền** là tiền nhập của cả dòng.
- **Giá bán**: **Giá mới** (theo đơn vị cơ bản) áp dụng từ **Ngày áp dụng** đến trước lần đổi giá sau của cùng mặt hàng; dòng đầu mỗi mặt hàng là giá lúc bắt đầu dữ liệu (**Giá cũ** trống).
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `DanhMuc.xlsx`.
