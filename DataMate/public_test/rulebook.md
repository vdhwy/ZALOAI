# DataMate — Rulebook (bộ public test)

Mọi đáp án chuẩn tính theo các luật dưới đây. Câu hỏi nói khác thì làm theo câu hỏi; không nói thì áp luật mặc định ở đây.

**Hôm nay** của mỗi câu là trường `as_of_date` trong `questions.jsonl`. Mọi cách nói tương đối tính theo ngày này. File có thể có bản ghi ngày sau hôm nay: với câu hỏi theo hôm nay, những bản ghi đó coi như chưa xảy ra. Riêng trạng thái huỷ, trả hàng của đơn lấy theo trạng thái ghi trên đơn, kể cả khi phiếu trả ghi ngày sau hôm nay.

## 1. Đơn hàng và doanh thu
| Luật | Mặc định |
|---|---|
| Đơn tính vào doanh thu | đơn **không huỷ** và **không trả hàng**. Đơn có trả hàng, **kể cả chỉ trả một phần**, là đơn trả hàng: bỏ **cả đơn**. Đơn đang giao vẫn tính |
| Bán được bao nhiêu tiền, thu về bao nhiêu tiền | là **doanh thu** theo mục này, không phải tiền khách đã trả |
| Đơn thuộc kỳ nào | theo **ngày đặt**, không theo ngày giao hay ngày thu tiền. Đơn trả hàng sau kỳ, kể cả trả sau hôm nay, vẫn bị loại khỏi doanh thu kỳ đặt |
| Đơn bị huỷ | đơn có trạng thái huỷ. Đơn trả hàng **không** phải đơn huỷ |
| Số đơn | chỉ tính đơn không huỷ, không trả; cả khi đếm số đơn có một mặt hàng, số đơn của một khách. **Khách đã mua** trong kỳ là khách có ít nhất một đơn như vậy trong kỳ |
| Doanh thu một đơn | tổng **thành tiền các dòng hàng** (đã trừ giảm giá trên từng dòng). **Không** trừ giảm giá trên cả đơn (khuyến mãi theo tổng tiền đơn, voucher shop), **không** cộng thuế VAT, **không** gồm phí giao hàng. **Tiền hàng**, **tiền bán** của đơn bán cùng nghĩa với doanh thu |
| Doanh thu theo hình thức thanh toán | theo hình thức **ghi trên đơn**, không theo lần trả nợ về sau: đơn ghi nợ không tính vào tiền mặt hay chuyển khoản. Đơn **COD** là hình thức riêng, không tính vào tiền mặt |
| Doanh thu theo nhóm khách | nhóm theo cột nhóm khách. Đơn không ghi khách (khách vãng lai) **không thuộc nhóm nào**, kể cả nhóm `lẻ`. Tỉ trọng của nhóm chia cho doanh thu **cả shop** cùng kỳ, tính cả đơn vãng lai |
| Báo cáo tiền mặt theo ca | chỉ ghi **tiền mặt**, theo **giờ thu tiền**, gồm cả tiền khách trả nợ. Doanh thu, số đơn tính từ đơn hàng theo ngày, giờ đặt như trên, không tính từ báo cáo ca |
| Tỉ lệ đơn huỷ trong kỳ | phần trăm đơn huỷ trong **mọi đơn đặt trong kỳ** (theo ngày đặt, **mọi trạng thái**: cả đơn huỷ, đơn trả, đơn đang giao). Làm tròn 2 chữ số thập phân. |
| Phần trăm thay đổi, tăng trưởng | so với **kỳ trước**; giảm thì ra **số âm** |
| Chênh lệch, hơn / kém, tăng / giảm bao nhiêu (số, không phải %) | **kỳ hỏi − kỳ so**: ít hơn ra số âm, giữ đơn vị của số đo |

## 2. Thời gian
| Cách nói | Nghĩa |
|---|---|
| Ngày X, hôm nay, hôm qua | hỏi số phát sinh (doanh thu, số đơn, giá bán…): chỉ **trong** ngày đó |
| Đến hết ngày X, tính đến hôm nay | hỏi số còn lại (còn nợ, còn tồn, còn hàng, chưa giao…): **tình trạng lúc hết ngày đó**, tính mọi phát sinh **từ đầu dữ liệu** đến hết ngày đó; không phải kỳ **tháng này** |
| Từ X đến Y, nhóm X–Y | gồm cả X và Y |
| N ngày gần nhất | N ngày liền nhau **kể cả hôm nay**, ngày cuối là hôm nay |
| Quá N, hơn N, trên N, dưới N | **không** gồm N. **Từ N trở lên** thì gồm N |
| Tuần | bắt đầu **thứ Hai**. **Tuần này**: từ thứ Hai của tuần chứa hôm nay đến hết hôm nay. **Tuần trước, tuần rồi**: **cả** tuần liền trước, thứ Hai đến Chủ nhật |
| Tháng M/Y | cả tháng, từ ngày 1 đến hết ngày cuối tháng |
| Tháng này | từ ngày 1 đến **hết hôm nay**. So với tháng trước thì lấy **cùng số ngày** của tháng trước: từ ngày 1 đến hết ngày trùng số với hôm nay; tháng trước không có ngày đó thì đến hết tháng trước |
| Từ đầu năm, từ đầu năm tới nay | từ 01/01 của năm nay đến **hết hôm nay** |
| Tháng M, quý Q không ghi năm | của **năm nay** nếu không sau hôm nay; sau hôm nay thì của **năm trước**. Quý theo dương lịch, mỗi quý 3 tháng tính từ tháng 1 |
| Tết năm Y, dịp Tết, mùa Tết | từ ngày dương của **23 tháng Chạp** (năm âm Y − 1) đến **hết** ngày dương của **mùng 10 tháng Giêng** (năm âm Y). **So với trước Tết** = cùng số ngày ngay trước 23 tháng Chạp. Tra lịch âm trong `calendar.csv` cùng thư mục. |
| Ca sáng, ca chiều | theo giờ tạo đơn: ca sáng 06:00–13:59, ca chiều 14:00–21:59. So ca chiều với ca sáng: mốc là **ca sáng** |
| Trung bình mỗi ngày thứ X của kỳ | chia cho **số ngày thứ X** trong kỳ, kể cả ngày không có đơn, phiếu |

## 3. Xếp hạng
| Luật | Mặc định |
|---|---|
| Mặt hàng | **Món**, hàng, sản phẩm cùng nghĩa với mặt hàng. Dòng **Phí phục vụ** không phải mặt hàng: không xếp hạng, không đếm. Vẫn tính vào doanh thu, kể cả mẫu số tỉ trọng nhóm hàng |
| Nhóm hàng | theo cột nhóm hàng, đúng tên nhóm câu hỏi nêu; không gộp nhóm khác tên dù tên gần nhau |
| Bán chạy | theo **số lượng quy về đơn vị cơ bản**, không theo số dòng hay số tiền; bỏ đơn huỷ, trả. Mặt hàng khác đơn vị cơ bản vẫn xếp chung theo số đó. **Bán nhiều nhất**, **bán được nhiều nhất**, **hot nhất** cùng nghĩa với **bán chạy nhất** |
| Bán được bao nhiêu <đơn vị> | cộng số lượng quy về đơn vị cơ bản của các mặt hàng **có đơn vị cơ bản là <đơn vị>**, kể cả dòng bán theo đơn vị lớn; mặt hàng có đơn vị cơ bản khác không tính |
| Hàng lời nhất | theo **tổng lãi gộp** của mặt hàng (§5) |
| Xác định khách | Shop có mã khách: mỗi **mã khách** là một khách, hai mã trùng tên là hai khách; đơn không ghi mã (**khách lẻ**) không phải khách, không đếm và không xếp hạng. Shop không có mã khách: xác định khách theo **tên ghi trên đơn**: hai tên **chỉ khác cách viết** là cùng một khách, hai tên **khác chữ hoặc khác số** là hai khách; đơn **khách lẻ** không tính. Khách mua **nhiều tiền** nhất xếp theo doanh thu (§1). |
| Nhân viên bán giỏi nhất | theo **doanh thu** (§1) của nhân viên trong kỳ, không theo số đơn |
| Giá trị trung bình một đơn | làm tròn về đồng, nửa đồng làm tròn lên |
| Khách trung thành nhất | khách (xác định như dòng Xác định khách) có **nhiều ngày có mua nhất** trong kỳ |
| Khách sộp nhất | khách có **giá trị trung bình một đơn** cao nhất trong kỳ, chỉ xét khách có **từ 3 đơn trở lên** trong kỳ |
| Khách hay đổi ý nhất | khách có **nhiều đơn huỷ nhất** trong kỳ |
| Mặt hàng được ưa chuộng nhất | mặt hàng có mặt trong **nhiều đơn nhất** trong kỳ |
| Nhân viên, thợ chăm chỉ nhất | người có **nhiều ngày làm việc nhất** trong kỳ; ngày làm việc là ngày có ít nhất một đơn, kể cả phiếu bảo hành, do người đó bán hoặc làm |
| Ngày đắt khách nhất | ngày có **nhiều đơn nhất** trong kỳ |
| Giờ cao điểm | khung **một giờ tròn** theo giờ tạo đơn (từ h giờ đến trước h + 1 giờ) có nhiều đơn nhất trong kỳ. Đáp án là **giờ bắt đầu khung**, type `number` |

## 4. Công nợ
| Luật | Mặc định |
|---|---|
| Đơn được tính vào nợ | đơn không huỷ; **đơn trả hàng vẫn tính** nếu còn nợ |
| Nợ một đơn tại ngày X | phần chưa trả của **tổng đơn** (số khách phải trả cả đơn: đã trừ giảm giá trên cả đơn, **gồm phí giao**), tính các khoản trả đến hết ngày X. Còn nợ = cộng các đơn **còn nợ > 0** |
| Nợ theo khách | xác định khách như §3. Đơn **khách lẻ** vẫn tính vào **tổng nợ**, nhưng không có dòng trong bảng nợ theo khách |
| Đơn COD, đơn bán qua sàn TMĐT | **không phải khách nợ**, kể cả khi chưa thu được tiền; bỏ khỏi công nợ và tuổi nợ |
| Tuổi nợ | số ngày tính từ **ngày đặt**, không từ hạn thanh toán. Đơn đặt hôm nay có tuổi nợ **0** ngày, đơn đặt hôm qua **1** ngày |
| Nợ thêm, trả nợ, thu nợ trong kỳ | chỉ đơn **ghi nợ**, không huỷ. **Nợ thêm**: phần tổng đơn chưa trả ngay trong ngày mua, của đơn đặt trong kỳ. **Trả nợ / thu nợ**: các khoản trả **sau ngày mua** có ngày trả trong kỳ, của mọi đơn ghi nợ (kể cả đơn kỳ trước, đơn trả hàng). Tiền trả cùng ngày mua là trả lúc mua. Hoàn tiền trả hàng không trừ |

## 5. Kho, nhập hàng, giá vốn
| Luật | Mặc định |
|---|---|
| Tiền nhập hàng trong kỳ | tổng tiền các phiếu nhập có **ngày phiếu** trong kỳ, bỏ phiếu huỷ. Phiếu, dòng ghi **nhập đầu kỳ** là phiếu nhập như mọi phiếu khác: có ngày phiếu trong kỳ thì tính. Nhà cung cấp nhập nhiều nhất = nhà cung cấp có tiền nhập cao nhất |
| Nhà cung cấp chính | nhà cung cấp có **nhiều phiếu nhập nhất** trong kỳ, bỏ phiếu huỷ. Khác nhà cung cấp nhập nhiều tiền nhất |
| Nhập trừ bán, chênh nhập và bán | phần **bán** là số lượng của đơn tính vào doanh thu (§1), quy về cùng đơn vị với phần nhập |
| Giá trị hàng tồn kho | tồn **hết hôm nay** của từng mặt hàng nhân **giá vốn một đơn vị cơ bản ghi trong danh mục hàng**; chỉ tính hàng còn tồn |
| Mặt hàng hết hàng cuối ngày | mặt hàng **mua về để bán** (không tính món pha chế, chế biến tại chỗ) mà lúc **hết ngày** đó tồn kho bằng 0; hết giữa ngày nhưng nhập thêm trước cuối ngày thì không tính |
| Mặt hàng không bán được trong kỳ (ế) | mặt hàng cửa hàng **đã từng bán trước kỳ** (có trong đơn §1, không tính đơn huỷ, đơn trả) nhưng trong kỳ không có đơn nào (§1) mua mặt hàng đó |
| Hiệu ứng tăng giá | lần tăng giá = ngày D giá mới cao hơn giá liền trước (theo bảng giá); tăng lên cùng một giá nhiều lần thì lấy lần đầu. So số lượng (đơn vị cơ bản) **N ngày kể từ D** (tính cả D) với **N ngày ngay trước D**; cả hai khoảng bỏ đơn huỷ và đơn trả |
| Giá vốn | bình quân gia quyền theo lô nhập, tại thời điểm bán; không theo FIFO, không theo giá nhập lần cuối |
| Lãi gộp | doanh thu (§1) trừ giá vốn của hàng đã bán. Giá vốn của mỗi dòng bán bằng số lượng nhân với **giá vốn ghi trên dòng bán** (cho **một đơn vị bán**, cùng đơn vị với đơn giá). Không tự tính lại giá vốn từ phiếu nhập hay từ lô |
| Lãi ròng một tháng | lãi gộp của tháng trừ **mọi khoản** ghi trong sổ chi phí của tháng đó, kể cả sửa chữa, thay thiết bị |

## 6. Theo ngành
Luật riêng của từng ngành, dùng cùng với luật chung ở các mục trên. Khi luật ngành khác luật chung, theo **luật ngành**.

### Cà phê
| Luật | Mặc định |
|---|---|
| Size M, size L | món có tên kết thúc bằng `(M)` hoặc `(L)`, **không phân biệt hoa thường** |
| Topping ghi chung ô với món | món và topping là **hai** mặt hàng bán: số lượng, tiền của topping tính vào mặt hàng topping (cùng mặt hàng với topping ghi dòng riêng), không tính vào món |

### Nhà thuốc
| Luật | Mặc định |
|---|---|
| Thuốc kê đơn | **Thuốc kê đơn** = sản phẩm ghi kê đơn trong danh mục thuốc; mọi sản phẩm còn lại là **hàng không kê đơn**. Tỉ lệ kê đơn tính theo doanh thu |
| Hàng hết hạn trong N ngày tới | tính tại hôm nay D: lô còn tồn có hạn dùng từ D đến hết ngày D + N. **Tiền vốn** là giá trị phần **còn tồn** của lô, theo giá nhập của chính lô đó quy về đơn vị cơ bản, không theo giá vốn bình quân |
| Doanh thu theo hoạt chất | doanh thu (§1) các thuốc có hoạt chất ghi **đúng như vậy** trong danh mục thuốc. Thuốc phối hợp nhiều hoạt chất là **một loại riêng**, không tính vào từng hoạt chất trong đó |
| Lô gần hết hạn nhất của một thuốc | trong các lô còn tồn chưa quá hạn tại hôm nay, lô có hạn sớm nhất |

### Vật liệu xây dựng
| Luật | Mặc định |
|---|---|
| Giao nhiều đợt | tính đến hết hôm nay. **Số đợt giao trong tháng X** = số đợt có ngày giao trong tháng X; **mỗi đợt của mỗi đơn tính một đợt**, kể cả đợt của đơn sau đó trả hàng. Đợt đã chở vẫn tính dù đơn sau đó trả hàng |

### Mẹ và bé
| Luật | Mặc định |
|---|---|
| Tiền giảm voucher, tiền giảm nhờ dùng điểm, phí ship | trả **số dương**; cộng theo **ngày của hoá đơn**; chỉ tính hoá đơn không huỷ, không trả |
| Số sữa, size bỉm | lấy theo cột Số / Size của danh mục: hàng để trống cột Số / Size thì không xếp vào số, size nào, dù tên hàng có số. Phần trăm của một size hay một hãng chia cho tổng số bịch mọi hàng **bỉm tã** cùng kỳ |
| Khách thành viên mới trong tháng | số khách có **Ngày đăng ký** trong tháng đó, kể cả khách chưa mua lần nào |

### Sửa xe
| Luật | Mặc định |
|---|---|
| Lượt xe, phiếu | mỗi dòng sổ sửa xe là **một lượt xe** (một phiếu), kể cả phiếu bảo hành; một xe tới hai lần là hai lượt. **Số phiếu, số lượt xe** của tiệm hay của một thợ tính cả phiếu bảo hành. Tiền trung bình một phiếu chia cho số phiếu **có thu tiền** (không tính phiếu bảo hành) |
| Việc ghi trong ô Làm gì | lượt xe có làm một việc = phiếu có việc đó, tính một lượt. `Nhớt` ghi trơn là nhớt máy, không phải nhớt láp; `ruột` ghi trơn là thay ruột mới, không phải vá. **Sửa điện** không gồm thay bóng đèn, thay ắc quy. **Phiếu bảo hành** **không** tính là lượt làm việc đó |
| Dòng xe, biển số | Tên dòng xe chỉ khác hoa/thường hoặc ghi tắt là cùng một dòng. **Số chiếc xe** mang tới = số biển số khác nhau, tính cả xe chỉ tới bảo hành |
| Thợ làm nhiều nhất | theo **số lượt xe**, kể cả phiếu bảo hành thợ đó làm |
| Bảo hành | **Tỉ lệ bảo hành** bằng số phiếu bảo hành có ngày trong kỳ, chia cho số phiếu có thu tiền trong cùng kỳ; phiếu bảo hành của xe sửa từ kỳ trước vẫn tính |
| Khách quen, xe tới nhiều lần | xác định xe theo **biển số**. Chỉ đếm phiếu **có thu tiền**: phiếu bảo hành không tính là một lần tới. **Xe khách quen** = xe có từ 2 phiếu có thu tiền trong kỳ. Câu hỏi **xe nào** thì trả lời bằng biển số |

### Cửa hàng điện thoại
| Luật | Mặc định |
|---|---|
| Thu máy cũ | **Khách phải trả** là tiền của đơn sau bớt và sau trừ máy cũ, gồm cả phần còn nợ. Tiền thu máy cũ **không** trừ vào doanh thu. Tổng khách phải trả, tiền thu máy cũ của một kỳ chỉ tính đơn không huỷ, không trả (§1) |
| Trả góp | Đơn trả góp là đơn **ghi nợ** (§4): phần góp chưa trả là tiền khách còn nợ, tiền góp mỗi kỳ là tiền khách trả nợ (tính vào thu nợ). Tiền góp không tính vào doanh thu, vì doanh thu đã tính đủ giá máy vào ngày mua; tiền trả trước không phải tiền góp. Câu hỏi khách nợ, mua chịu, trả nợ, thu nợ gồm cả đơn trả góp, dù shop ghi sổ góp riêng với sổ nợ. Kỳ góp có hạn **trước** ngày hỏi mà chưa góp đủ là **quá hạn**; kỳ có hạn đúng ngày hỏi thì chưa quá hạn. |
| Bảo hành | **Tỉ lệ bảo hành** của một quý bằng số **lượt** bảo hành có ngày nhận trong quý, chia cho số máy bán trong quý (bỏ đơn huỷ, đơn trả). Lượt bảo hành của máy bán từ quý trước vẫn tính. |
| Dòng máy, hãng | **dòng máy** = phần tên hàng đứng trước dung lượng `…GB`; tên không có phần `…GB` thì dòng máy là cả tên (`Nokia 105 4G`: `4G` là mạng, không phải dung lượng). **Hãng** = chữ đầu tên hàng; máy `iPhone` là hãng Apple. Máy khách mang tới đổi không phải máy bán |

## 7. Không trả lời được
Câu **không trả lời được** khi dữ liệu phát hành không đủ để trả lời. Đáp án chỉ lấy từ dữ liệu phát hành, không lấy từ hiểu biết bên ngoài. Nộp `{"type": "unanswerable", "reason": "…"}`.
- Thông tin file không ghi thì không suy ra từ cột khác, trừ khi rulebook ghi cách lấy.
- Không có dữ liệu khác với bằng 0: kỳ nằm **hoàn toàn** ngoài khoảng ngày có dữ liệu của shop, hoặc shop không ghi loại thông tin câu hỏi cần, thì không trả lời được, không phải 0.
- Kỳ chỉ có một phần nằm trong khoảng ngày có dữ liệu thì tính trên phần có dữ liệu.

Trường `reason` không bắt buộc và không chấm tự động. Nếu có, `reason` phải là chuỗi; dòng có `reason` không phải chuỗi không đọc được và tính như bỏ trống.

## 8. Cách ghi trong file
| Cách ghi | Hiểu là |
|---|---|
| Tên gọi, nhãn | các tên cùng chỉ một thứ, trong file hay trong câu hỏi, là cùng một thứ. File có mã thì theo mã |
| Ô để trống ở các dòng sau của cùng một nhóm dòng | giống ô đó ở dòng đầu nhóm: khách, ghi chú, trạng thái của đơn áp cho mọi dòng của đơn. Không phải thiếu dữ liệu, không có nghĩa là khách lẻ hay đơn hoàn thành |
| Sổ không có cột trạng thái | trạng thái đơn ghi ở cột Ghi chú. Ghi chú không nhắc trạng thái là đơn hoàn thành |
| Trạng thái đơn | mỗi đơn có đúng một trong bốn trạng thái: **hoàn thành**, **huỷ**, **trả hàng**, **đang giao** |
| Hai dòng của **cùng một đơn** giống nhau ở mọi ô | lỗi xuất file, tính một lần. Hai dòng giống nhau của hai đơn khác nhau là hai lần bán, tính cả hai |
| Bảng không ghi theo đơn | mỗi dòng là một lần ghi; hai dòng giống nhau trong cùng file vẫn tính cả hai |
| Ngày không ghi năm | năm của sheet chứa dòng đó |

## 9. Đáp án và chấm điểm
Mỗi dòng `submission.jsonl`: `{"id": "...", "type": "...", "answer": ...}`. Đúng **+1**, sai **−1**, bỏ trống (`{"type": "abstain"}` hoặc không có dòng) **0**.

**Mỗi type có một format duy nhất; sai format là sai.** Đáp án chỉ ghi **giá trị**: số không kèm chữ đơn vị hay ký hiệu %; tên lấy nguyên từ dữ liệu, không kèm tên cột hay nhãn nhóm. Câu hỏi nhiều số thì ghi list theo đúng thứ tự câu hỏi nêu.

| type | Format | Đúng | Sai |
|---|---|---|---|
| number | JSON number, không đơn vị, không dấu phân cách nghìn. Tiền là số nguyên VND | `4820000`, `18.6` | `"4,82 triệu"`, `"4.820.000"`, `"4820K"`, `"4820000"` |
| percent | JSON number là **số phần trăm**: 12,4 % ghi `12.4`, không kèm ký hiệu % | `12.4` | `"12,4%"`, `0.124` |
| date | `"YYYY-MM-DD"`; câu hỏi theo tháng: `"YYYY-MM"` | `"2026-08-15"`, `"2025-09"` | `"15/08/2026"`, `"tháng 9/2025"` |
| boolean | `true` / `false` | `true` | `"có"`, `1` |
| string | tên như trong dữ liệu, đủ dấu tiếng Việt | `"Sting dâu 330ml"` | `"Sting dầu 330ml"` (sai dấu, file không có cách viết này), `["Sting dâu 330ml"]` |
| list | mảng JSON, có thứ tự; một phần tử vẫn là mảng | `["Cà phê sữa"]`, `[3, 10]` | `"Cà phê sữa, Bạc xỉu"`, `"3 thùng 10 chai"` |
| table | `{"columns": [...], "rows": [[...], ...]}`, ô số là JSON number | `{"columns": ["khach_hang", "so_tien_no"], "rows": [["Chị Lan", 3200000]]}` | ô `"3.200.000đ"` |
| unanswerable | `{"type": "unanswerable", "reason": "..."}` | | |

Đúng format rồi mới so giá trị:
- **Số, phần trăm:** khớp tuyệt đối. Tiền đúng từng đồng, số đếm đúng từng đơn vị, phần trăm đúng 2 chữ số thập phân. Chỉ bỏ qua sai số dấu phẩy động.
- **Làm tròn:** tiền ra số lẻ làm tròn về đồng; trung bình của một khoản tiền cũng là tiền, làm tròn về đồng. Phần trăm và số trung bình khác làm tròn 2 chữ số thập phân, trừ khi một luật khác trong rulebook ghi khác.
- **Chuỗi:** không phân biệt hoa thường, khoảng trắng, dấu câu. Nhận **mọi cách viết** tên có trong file của shop, hoặc **mã**. Tên khách chép kèm số điện thoại như trong file cũng được nhận. Ngoài các cách viết đó, dấu tiếng Việt phải đúng.
- **Danh sách:** đúng cả tập và thứ tự. Top k xếp theo tiêu chí câu hỏi, giảm dần. Câu "liệt kê": có số đo thì số đo giảm dần, cùng số đo thì theo **mã** tăng dần; liệt kê hàng theo hạn dùng thì hạn sớm nhất của mặt hàng trước, cùng hạn thì theo mã; còn lại (chỉ lọc theo điều kiện, không có số đo) theo mã tăng dần.
- **Bằng nhau:** hai đối tượng bằng nhau ở tiêu chí câu hỏi thì xếp theo mã tăng dần (không có mã thì theo tên). Câu hỏi một đối tượng lấy đối tượng đứng đầu theo thứ tự đó.
- **Bảng:** mỗi dòng một đối tượng; cột **đầu** là tên đối tượng, các cột **sau** là số đo theo **đúng thứ tự câu hỏi nêu**. Cột so theo tên; tên không khớp thì so theo vị trí, nên ghi đúng thứ tự cột. Thứ tự các dòng không ảnh hưởng kết quả chấm.

## 10. Từ ngữ
| Từ | Nghĩa |
|---|---|
| Đơn vị cơ bản, đơn vị lớn | mỗi mặt hàng có một **đơn vị cơ bản** (đơn vị nhỏ nhất shop đếm) và có thể có **đơn vị lớn**. Hệ số quy đổi khác nhau theo shop và theo mặt hàng, luôn đọc ở bảng quy đổi hoặc README của shop; đơn vị không có dòng quy đổi nào là đơn vị cơ bản, hệ số 1 |
