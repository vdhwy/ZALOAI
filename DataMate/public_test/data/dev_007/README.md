# Dữ liệu dev_007

File xuất từ phần mềm bán hàng, 3 danh sách: chi tiết hoá đơn (mỗi dòng một mặt hàng trong đơn; thông tin đơn, khách lặp lại ở mọi dòng của đơn), danh mục hàng kèm tồn kho, chi tiết nhập hàng (thông tin phiếu nhập lặp lại ở mọi dòng của phiếu). Các file nối với nhau qua mã hàng.

## File
- `chi_tiet_hoa_don.csv` (csv)
- `danh_muc_hang.csv` (csv)
- `chi_tiet_nhap_hang.csv` (csv)

## Cột trong `chi_tiet_hoa_don.csv`
- **Bàn**: bàn
- **Thành tiền**: thành tiền sau giảm
- **Nhóm khách hàng**: nhóm khách
- **Mặt hàng**: tên hàng
- **Khu vực**: khu vực của bàn
- **Nguồn**: kênh bán
- **Nội dung**: cột trống, không có dữ liệu
- **Giờ bán**: thời điểm đặt đơn (ngày giờ)
- **Giới tính**: cột trống, không có dữ liệu
- **No.**: số thứ tự dòng trong đơn
- **Ngày giao dịch**: ngày bán
- **Tiến độ**: trạng thái đơn
- **Trạng thái HĐĐT**: cột trống, không có dữ liệu
- **Mã vạch**: mã hàng
- **Khách trả**: khách đã trả cho cả đơn (lặp lại ở mọi dòng của đơn); tiền của đơn có phí giao gồm cả phí giao (file này không có cột phí giao riêng)
- **Họ tên khách**: tên khách (Khách lẻ nếu không lưu)
- **Mã khách mua**: mã khách (trống nếu khách lẻ)
- **Còn nợ**: khách còn nợ của cả đơn (lặp lại ở mọi dòng của đơn)
- **Tiền giảm**: tiền giảm của cả dòng
- **Mã bill**: mã đơn
- **Số khách**: số khách của đơn
- **Sluong**: số lượng
- **Nhân viên bán**: mã nhân viên bán
- **Phone**: số điện thoại
- **Tổng tiền hàng**: tổng tiền hàng của cả đơn, trước giảm giá của đơn (lặp lại ở mọi dòng của đơn)
- **Giảm giá HĐ**: giảm giá của cả đơn (lặp lại ở mọi dòng của đơn)
- **Addr**: địa chỉ
- **Phân loại**: nhóm hàng
- **Số lượng lẻ**: số lượng đã đổi ra đơn vị cơ bản
- **Đơn giá (đ)**: đơn giá

## Cột trong `danh_muc_hang.csv`
- **Đang kinh doanh**: còn kinh doanh (True/False)
- **ĐVT**: đơn vị cơ bản
- **Giá vốn**: giá vốn
- **Hàng bán**: tên hàng
- **Nhóm**: nhóm hàng
- **Giá**: giá bán hiện tại
- **Tồn cuối**: tồn kho (đơn vị cơ bản)
- **Mã SKU**: mã hàng

## Cột trong `chi_tiet_nhap_hang.csv`
- **Mã NCC**: mã nhà cung cấp
- **Tổng tiền phiếu**: tổng tiền phiếu nhập
- **SL nhập**: số lượng nhập
- **Hàng hóa**: tên hàng
- **STT**: số thứ tự dòng trong phiếu nhập
- **ĐVT nhập**: đơn vị nhập
- **Mã hàng bán**: mã hàng
- **Giá nhập**: giá nhập một đơn vị (theo đơn vị nhập của dòng)
- **Note**: ghi chú
- **Ngày nhập**: ngày nhập
- **Thành tiền**: tiền nhập của cả dòng
- **Mã phiếu nhập**: mã phiếu nhập
- **Trạng thái phiếu**: trạng thái phiếu nhập

## Quy ước
- Dữ liệu có đến hết 19/09/2026.
- **Còn nợ**: **Còn nợ** là số khách còn nợ của đơn, tính đến hết ngày cuối dữ liệu.
- **Tồn kho**: **Tồn cuối** là tồn cuối ngày cuối có dữ liệu, theo đơn vị cơ bản.
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
