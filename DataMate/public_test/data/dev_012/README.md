# Dữ liệu dev_012

Sổ sửa xe chủ tiệm tự ghi trên Excel, mỗi tháng một sheet: mỗi dòng một lượt xe vào sửa (một phiếu), không ghi mã phiếu, không ghi tên khách. Ô Làm gì ghi mọi việc của phiếu. Tiền là tổng cả phiếu, không ghi tiền từng việc. File DanhSachTho.xlsx ghi họ tên, phần trăm hoa hồng các thợ; sổ ghi thợ theo tên gọi. Phiếu ghi chú bảo hành, Tiền 0: xe quay lại bảo hành việc của một phiếu trước, tiệm không thu tiền.

## File
- `SoSuaXe.xlsx` (xlsx)
- `DanhSachTho.xlsx` (xlsx)

## Cột trong `SoSuaXe.xlsx`
- **Ngày**: ngày sửa
- **Xe**: dòng xe và biển số ghi chung một ô
- **Làm gì**: các việc đã làm cho xe, nhiều việc ghi chung một ô
- **Thợ**: thợ làm phiếu, ghi tên gọi
- **Tiền**: tổng tiền cả phiếu
- **Ghi chú**: ghi chú

## Cột trong `DanhSachTho.xlsx`
- **Họ tên**: họ tên thợ
- **Ngày vào làm**: ngày vào làm
- **Hoa hồng (%)**: phần trăm hoa hồng của thợ, tính trên tổng Tiền các phiếu thợ làm trong tháng

## Quy ước
- Dữ liệu có đến hết 31/08/2026.
