# Cách trình bày phần Python trong báo cáo

## 1. Mục tiêu

Sau khi xác định vùng khảo sát và vị trí gNB trên Google Earth, Python được dùng như công cụ mô phỏng RF để đánh giá phương án quy hoạch ban đầu. Mục tiêu là biến dữ liệu tọa độ thực thành các KPI có thể kiểm tra: Path Loss, RSRP, Serving Cell, SINR, vùng chồng phủ, throughput và vùng phủ yếu.

## 2. Chuỗi xử lý

```text
Google Earth KML
      ↓
Đọc polygon + tọa độ gNB
      ↓
WGS84 → UTM (mét)
      ↓
Sinh lưới UE trong vùng khảo sát
      ↓
Xác suất LOS/NLOS (3GPP UMa)
      ↓
Path Loss + Shadow Fading
      ↓
RSRP-like của từng gNB
      ↓
Chọn Serving Cell mạnh nhất
      ↓
Massive-MIMO serving gain / interference suppression
      ↓
SINR
      ↓
Throughput estimate
      ↓
Weak zone / overlap zone
      ↓
Gợi ý điểm cần kiểm tra để add/move gNB
```

## 3. Công thức chính

### 3.1 Khoảng cách 3D

`d3D = sqrt(d2D² + (hBS - hUT)²)`

### 3.2 UMa LOS path loss

Với khoảng cách trước breakpoint:

`PL_LOS = 28 + 22 log10(d3D) + 20 log10(fc)`

Sau breakpoint chương trình dùng biểu thức UMa PL2 của 3GPP TR 38.901.

### 3.3 UMa NLOS path loss

`PL_NLOS' = 13.54 + 39.08 log10(d3D) + 20 log10(fc) - 0.6(hUT - 1.5)`

`PL_NLOS = max(PL_LOS, PL_NLOS')`

Trong đó `fc` tính theo GHz và khoảng cách tính theo mét.

### 3.4 RSRP-like

Chương trình dùng equivalent EIRP và phân bố công suất trên các resource elements:

`RSRP ≈ EIRP - PL - SystemLoss - 10log10(12 × NRB)`

Đây là đại lượng phục vụ so sánh quy hoạch. Khi có thông số vendor thực tế, EIRP/gain/loss phải được hiệu chỉnh.

### 3.5 SINR

`SINR = S / (ΣI + N)`

Tất cả gNB dùng cùng carrier được xem là nguồn nhiễu đồng kênh. Massive MIMO được biểu diễn đơn giản bằng gain trên serving beam và suppression trên interfering links.

### 3.6 Throughput

`SE = min(log2(1 + SINR), SE_max)`

`Throughput ≈ BW × efficiency × SE`

Đây là throughput ước lượng để so sánh giữa các vị trí, không phải mô phỏng scheduler vendor.

## 4. Điểm sáng tạo để demo với thầy

### Blockage vẽ từ Google Earth

Bạn có thể tự khoanh một vùng nhiều nhà cao tầng trong Google Earth, đặt tên `BLOCKAGE-01`, export KML lại rồi chạy lại Python. Không cần sửa code. Mọi đường truyền gNB → UE cắt vùng đó sẽ được cộng thêm blockage loss.

Như vậy demo trực tiếp được:

1. Bản đầu chưa có vật cản.
2. Thêm polygon che khuất trên Google Earth.
3. Chạy Python lại.
4. Quan sát RSRP/SINR giảm phía sau vùng che.
5. Python phát hiện weak zone.
6. Dời/thêm gNB rồi chạy lại.

Đây là một closed-loop planning workflow rõ ràng hơn việc chỉ vẽ các vòng tròn cell.

## 5. Không nên nói quá khi thuyết trình

- Không gọi kết quả là coverage thương mại chính xác tuyệt đối.
- Không nói tọa độ hiện tại là tối ưu cuối cùng.
- Không nói heuristic airport/open-area là dữ liệu building thật.
- Nên gọi đây là **initial RF planning simulation** và nhấn mạnh vòng lặp hiệu chỉnh.
