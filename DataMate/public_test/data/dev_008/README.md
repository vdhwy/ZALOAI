# Dữ liệu dev_008

File xuất từ phần mềm bán hàng, 3 danh sách: chi tiết hoá đơn (mỗi dòng một mặt hàng trong đơn; thông tin đơn, khách lặp lại ở mọi dòng của đơn), danh mục hàng kèm tồn kho, chi tiết nhập hàng (thông tin phiếu nhập lặp lại ở mọi dòng của phiếu). Các file nối với nhau qua mã hàng.

## File
- `ChiTietHoaDon_1.xlsx` (xlsx)
- `ChiTietHoaDon_2.xlsx` (xlsx)
- `DanhMucHang.xlsx` (xlsx)
- `ChiTietNhapHang.xlsx` (xlsx)

## Cột trong `ChiTietHoaDon_1.xlsx`
- **Bill**: mã đơn
- **Trạng thái HĐĐT**: cột trống, không có dữ liệu
- **Mã người mua**: mã khách (trống nếu khách lẻ)
- **Bàn**: bàn
- **Đơn vị (tính)**: đơn vị tính
- **Phi ship**: phí giao hàng của cả đơn (lặp lại ở mọi dòng của đơn)
- **Thành tiền**: thành tiền sau giảm
- **Giảm (đ)**: tiền giảm của cả dòng
- **Giờ bán**: thời điểm đặt đơn (ngày giờ)
- **Tổng tiền hàng**: tổng tiền hàng của cả đơn, trước giảm giá của đơn (lặp lại ở mọi dòng của đơn)
- **Addr**: địa chỉ
- **Giới tính**: cột trống, không có dữ liệu
- **Giảm giá HĐ**: giảm giá của cả đơn (lặp lại ở mọi dòng của đơn)
- **Nhóm hàng**: nhóm hàng
- **Khách**: tên khách (Khách lẻ nếu không lưu)
- **Số dòng**: số thứ tự dòng trong đơn
- **Tên hàng**: tên hàng
- **Nhóm khách hàng**: nhóm khách
- **Số ĐT**: số điện thoại
- **SL lẻ**: số lượng đã đổi ra đơn vị cơ bản
- **TT đơn**: trạng thái đơn
- **SLg**: số lượng
- **Note**: ghi chú của đơn (lặp lại ở mọi dòng của đơn): đơn ghi nợ thì ghi khách đã đưa / còn thiếu bao nhiêu
- **Ngày xuất**: ngày bán
- **Nhân viên bán**: mã nhân viên bán
- **Tong tien**: khách cần trả cho cả đơn (lặp lại ở mọi dòng của đơn)
- **Kênh bán**: kênh bán
- **Đơn giá (đ)**: đơn giá
- **Ma hang**: mã hàng
- **Thanh toán bằng**: hình thức thanh toán của đơn: cash tiền mặt, transfer chuyển khoản, ewallet ví điện tử, cod giao hàng thu tiền, debt ghi nợ
- **Số khách**: số khách của đơn
- **Khu vực**: khu vực của bàn

## Cột trong `ChiTietHoaDon_2.xlsx`
- **Bill**: mã đơn
- **Trạng thái HĐĐT**: cột trống, không có dữ liệu
- **Mã người mua**: mã khách (trống nếu khách lẻ)
- **Bàn**: bàn
- **Đơn vị (tính)**: đơn vị tính
- **Phi ship**: phí giao hàng của cả đơn (lặp lại ở mọi dòng của đơn)
- **Thành tiền**: thành tiền sau giảm
- **Giảm (đ)**: tiền giảm của cả dòng
- **Giờ bán**: thời điểm đặt đơn (ngày giờ)
- **Tổng tiền hàng**: tổng tiền hàng của cả đơn, trước giảm giá của đơn (lặp lại ở mọi dòng của đơn)
- **Addr**: địa chỉ
- **Giới tính**: cột trống, không có dữ liệu
- **Giảm giá HĐ**: giảm giá của cả đơn (lặp lại ở mọi dòng của đơn)
- **Nhóm hàng**: nhóm hàng
- **Khách**: tên khách (Khách lẻ nếu không lưu)
- **Số dòng**: số thứ tự dòng trong đơn
- **Tên hàng**: tên hàng
- **Nhóm khách hàng**: nhóm khách
- **Số ĐT**: số điện thoại
- **SL lẻ**: số lượng đã đổi ra đơn vị cơ bản
- **TT đơn**: trạng thái đơn
- **SLg**: số lượng
- **Note**: ghi chú của đơn (lặp lại ở mọi dòng của đơn): đơn ghi nợ thì ghi khách đã đưa / còn thiếu bao nhiêu
- **Ngày xuất**: ngày bán
- **Nhân viên bán**: mã nhân viên bán
- **Tong tien**: khách cần trả cho cả đơn (lặp lại ở mọi dòng của đơn)
- **Kênh bán**: kênh bán
- **Đơn giá (đ)**: đơn giá
- **Ma hang**: mã hàng
- **Thanh toán bằng**: hình thức thanh toán của đơn: cash tiền mặt, transfer chuyển khoản, ewallet ví điện tử, cod giao hàng thu tiền, debt ghi nợ
- **Số khách**: số khách của đơn
- **Khu vực**: khu vực của bàn

## Cột trong `DanhMucHang.xlsx`
- **Hàng**: tên hàng
- **Đang kinh doanh**: còn kinh doanh (True/False)
- **Mã sản phẩm bán**: mã hàng
- **DVT**: đơn vị cơ bản
- **Tồn thực**: tồn kho (đơn vị cơ bản)
- **Loại hàng**: nhóm hàng
- **Giá vốn**: giá vốn
- **Giá hiện tại**: giá bán hiện tại

## Cột trong `ChiTietNhapHang.xlsx`
- **Giá nhập**: giá nhập một đơn vị (theo đơn vị nhập của dòng)
- **Mã NCC**: mã nhà cung cấp
- **Trạng thái phiếu**: trạng thái phiếu nhập
- **Ngày nhập**: ngày nhập
- **STT**: số thứ tự dòng trong phiếu nhập
- **Mã phiếu nhập**: mã phiếu nhập
- **Tổng tiền phiếu**: tổng tiền phiếu nhập
- **Lưu ý**: ghi chú
- **Tên mặt hàng**: tên hàng
- **Mã vạch**: mã hàng
- **Thành tiền**: tiền nhập của cả dòng
- **SL nhập**: số lượng nhập
- **ĐVT nhập**: đơn vị nhập

## Quy ước
- Dữ liệu có đến hết 22/07/2026.
- **Còn nợ**: ghi chú nợ ở **Note** là tình trạng của đơn tính đến hết ngày cuối dữ liệu.
- **Tồn kho**: **Tồn thực** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
- **Bàn**: đơn ăn tại quán có đúng một bàn (**Bàn**), kể cả đơn huỷ; đơn giao đi không có bàn. **Số khách** là số khách của đơn; một bàn có nhiều đơn trong ngày.
- **Phí phục vụ**: đơn ngồi phòng lạnh (không huỷ, không ghi nợ) có thêm dòng hàng "Phí phục vụ": phí phục vụ phòng lạnh của đơn, tính theo tiền món, đã ghi sẵn thành tiền.
- **Nhập hàng**: **Giá nhập** là giá nhập một đơn vị, theo đơn vị nhập của dòng; **Thành tiền** là tiền nhập của cả dòng; **Tổng tiền phiếu** là tổng tiền của cả phiếu nhập.
- **Quy đổi đơn vị**: số lượng ghi theo đơn vị của dòng:
  - Bia Tiger lon: 1 thùng = 24 lon
  - Bia Sài Gòn Special lon: 1 thùng = 24 lon
  - Coca-Cola lon: 1 thùng = 24 lon
  - Bia Tiger Bạc lon: 1 thùng = 24 lon
  - Nước suối: 1 thùng = 24 chai
  - Bia Heineken lon: 1 thùng = 24 lon
  - Bia Sài Gòn Lager chai: 1 két = 20 chai
  - 7Up lon: 1 thùng = 24 lon
