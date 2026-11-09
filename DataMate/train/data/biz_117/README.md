# Dữ liệu biz_117

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
- **Giờ**: giờ đặt đơn (dòng trả hàng: lúc trả)
- **Mã phiếu**: mã đơn
- **TenKH**: tên khách (Khách lẻ nếu không lưu)
- **Ngày lập**: ngày bán
- **Tiền**: thành tiền sau giảm
- **Ghi chú TT**: trạng thái đơn
- **Giá**: đơn giá
- **DonVi**: đơn vị tính
- **Số lượng hàng**: số lượng
- **Tên SP**: tên hàng

## Cột trong `DanhMuc.xlsx`
- **Hàng**: tên hàng (file chỉ có mặt hàng có đơn vị lớn)
- **ĐV lớn**: đơn vị lớn (thùng, hộp, tấn...)
- **ĐV nhỏ**: đơn vị cơ bản
- **Hệ số QĐ**: hệ số: số đơn vị cơ bản trong 1 đơn vị lớn

## Cột trong `TonKho.xlsx`
- **Tồn thực**: tồn kho (đơn vị cơ bản)
- **Đơn vị**: đơn vị cơ bản
- **Product**: tên hàng

## Cột trong `SoGiaoHang.xlsx`
- **ĐV gốc**: đơn vị cơ bản
- **Biển số xe**: biển số xe
- **Mã bill**: mã đơn
- **Lượt giao**: đợt giao (1, 2, 3)
- **SL thực giao**: số lượng đã đổi ra đơn vị cơ bản
- **Tên hàng**: tên hàng
- **Ngày chở**: ngày giao
- **Người chở**: tài xế

## Cột trong `SoHanNo.xlsx`
- **So hoa don**: mã đơn
- **Hạn nợ (ngày)**: số ngày được nợ
- **Han tra**: hạn thanh toán

## Cột trong `SoNhapHang.xlsx`
- **Số phiếu**: mã phiếu nhập
- **Product**: tên hàng
- **Ngày nhập**: ngày nhập
- **ĐVT**: đơn vị nhập
- **Thành tiền**: tiền nhập của cả dòng
- **Nội dung**: ghi chú
- **Nhà cung cấp**: nhà cung cấp
- **SL nhập**: số lượng nhập
- **Giá nhập**: giá nhập một đơn vị (theo đơn vị nhập của dòng)

## Cột trong `BangGia.xlsx`
- **Ngày áp dụng**: ngày bắt đầu áp dụng giá
- **Giá cũ**: giá trước lần đổi (trống ở dòng đầu mỗi mặt hàng)
- **Giá mới**: giá bán áp dụng từ ngày đó (đơn vị cơ bản)
- **TenHang**: tên hàng

## Quy ước
- Dữ liệu có đến hết 20/05/2026.
- **Trả hàng**: hàng trả ghi số lượng âm, cùng mã đơn với đơn đã bán: đơn có dòng số lượng âm là đơn có trả hàng.
- **Tồn kho**: **Tồn thực** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
- **Hạn thanh toán**: chỉ đơn bán nợ có hạn. **Han tra** là ngày khách phải trả hết đơn; **Hạn nợ (ngày)** là số ngày được nợ, tính từ ngày đặt.
- **Giao hàng**: đơn không huỷ có ít nhất một mặt hàng nhóm cát đá, gạch, sắt thép, xi măng thì được giao tận nơi mọi mặt hàng của đơn, 1–3 đợt (**Lượt giao**); đơn khác khách tự chở, không có trong sổ giao; đơn đặt mấy ngày cuối dữ liệu có thể chưa giao. **SL thực giao** tính theo đơn vị cơ bản.
- **Nhập hàng**: **Giá nhập** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Thành tiền** là tiền nhập của cả dòng.
- **Giá bán**: **Giá mới** (theo đơn vị cơ bản) áp dụng từ **Ngày áp dụng** đến trước lần đổi giá sau của cùng mặt hàng; dòng đầu mỗi mặt hàng là giá lúc bắt đầu dữ liệu (**Giá cũ** trống).
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng, hệ số quy đổi ở `DanhMuc.xlsx`.
