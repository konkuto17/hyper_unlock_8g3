# HyperUnlock 🚀

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![SoC: Snapdragon 8G3 & 8G2](https://img.shields.io/badge/SoC-Qualcomm%20SM8650%20%7C%20SM8550-orange.svg)](https://www.qualcomm.com/)
[![HyperOS: 1, 2 & 3](https://img.shields.io/badge/HyperOS-1.0%20%7C%202.0%20%7C%203.0-red.svg)](https://hyperos.mi.com/)

> **Universal Bootloader Unlock & Hardware-Assisted Bypass Suite for Xiaomi / Redmi Snapdragon 8 Gen 3 (SM8650) and Snapdragon 8 Gen 2 (SM8550) Devices.**  
> *Bộ công cụ mở khóa Bootloader toàn diện: Hỗ trợ mở khóa chính thức (Official Server Unlock) và Bypass chuyên sâu cho các dòng máy Xiaomi / Redmi chạy Snapdragon 8 Gen 3 & 8 Gen 2 trên HyperOS 1, 2 và 3.*

---

## 🌟 Special Thanks & Acknowledgements (Lời cảm ơn & Tri ân)

Dự án này được kế thừa, hoàn thiện và phát triển dựa trên những công trình nghiên cứu xuất sắc của cộng đồng modding quốc tế. Chúng tôi xin gửi lời cảm ơn sâu sắc và ghi nhận bản quyền đến các tác giả:

* **Kernix ([@Linuxoid-cn](https://github.com/Linuxoid-cn))** — *Tác giả cốt lõi của [Mi8G3-Unlocker](https://github.com/Linuxoid-cn/Mi8G3-Unlocker) & [Mi8G2-Unlocker](https://github.com/Linuxoid-cn/Mi8G2-Unlocker)*:
  - Khám phá chuỗi khai thác ABL command injection và dịch vụ `IMQSNative` của Xiaomi trên nền tảng Snapdragon 8 Gen 3 & 8 Gen 2.
  - Tác giả của các universal unlock payload **`8gen3-Ennea.img`** và **`8550-Ennea.img`**.
  - Trích xuất và cấu trúc bảng phân vùng GPT (LUN4) cho cả 13 dòng máy SM8650 và SM8550.
  - *Liên hệ tác giả Kernix:* Telegram: `@C_Valmont` | Email: `jehsianbenites@gmail.com` | GitHub: [Linuxoid-cn](https://github.com/Linuxoid-cn)

* **MiForge & offici5l ([@offici5l](https://github.com/offici5l))**:
  - Tác giả dự án [MiUnlockTool](https://github.com/MiForge/MiUnlockTool) và thư viện [migate](https://github.com/offici5l/migate) giúp tái hiện giao thức trao đổi chữ ký với máy chủ Xiaomi.

* **MlgmXyysd ([@MlgmXyysd](https://github.com/MlgmXyysd))**:
  - Tác giả dự án [Xiaomi-HyperOS-BootLoader-Bypass](https://github.com/MlgmXyysd/Xiaomi-HyperOS-BootLoader-Bypass).

* **TinyblackQvQ ([@TinyblackQvQ](https://github.com/TinyblackQvQ))**:
  - Nghiên cứu cơ chế giao tiếp và gọi dịch vụ hệ thống `IMQSNative`.

---

## 📱 Supported Devices (Danh sách thiết bị hỗ trợ)

### 1. Snapdragon 8 Gen 3 (SM8650)
| Codename | Model thương mại | Trạng thái | Bảng phân vùng GPT | Payload |
| :--- | :--- | :---: | :---: | :---: |
| **`aurora`** | **Xiaomi 14 Ultra** | 🟢 **ĐÃ TEST TRÊN MÁY THỰC TẾ** | Tích hợp sẵn | 8gen3-Ennea.img |
| **`houji`** | **Xiaomi 14** | 🔵 Đã hỗ trợ | Tích hợp sẵn | 8gen3-Ennea.img |
| **`shennong`** | **Xiaomi 14 Pro** | 🔵 Đã hỗ trợ | Tích hợp sẵn | 8gen3-Ennea.img |
| **`manet`** | **Redmi K70 Pro** | 🔵 Đã hỗ trợ | Tích hợp sẵn | 8gen3-Ennea.img |
| **`zorn`** | **Redmi K80** | 🔵 Đã hỗ trợ | Tích hợp sẵn | 8gen3-Ennea.img |
| **`ruyi`** | **Xiaomi MIX Flip** | 🔵 Đã hỗ trợ | Tích hợp sẵn | 8gen3-Ennea.img |
| **`goku`** | **Xiaomi MIX Fold 4** | 🔵 Đã hỗ trợ | Tích hợp sẵn | 8gen3-Ennea.img |

### 2. Snapdragon 8 Gen 2 (SM8550)
| Codename | Model thương mại | Trạng thái | Bảng phân vùng GPT | Ghi chú tương thích |
| :--- | :--- | :---: | :---: | :--- |
| **`sheng`** | **Xiaomi Pad 6S Pro** | 🔵 Đã hỗ trợ | Tích hợp sẵn | Global: dùng `official` / China: bypass trước 01/02/2026 |
| **`fuxi`** | **Xiaomi 13** | 🔵 Đã hỗ trợ | Tích hợp sẵn | Offline bypass trước 01/02/2026 |
| **`nuwa`** | **Xiaomi 13 Pro** | 🔵 Đã hỗ trợ | Tích hợp sẵn | Offline bypass trước 01/02/2026 |
| **`ishtar`** | **Xiaomi 13 Ultra** | 🔵 Đã hỗ trợ | Tích hợp sẵn | Offline bypass trước 01/02/2026 |
| **`socrates`** | **Redmi K60 Pro** | 🔵 Đã hỗ trợ | Tích hợp sẵn | Offline bypass trước 01/02/2026 |
| **`vermeer`** | **Redmi K70** | 🔵 Đã hỗ trợ | Tích hợp sẵn | Offline bypass trước 01/02/2026 |

---

## 🧭 Lựa chọn phương pháp mở khóa (Unlock Strategy)

1. **Thiết bị bản Quốc tế (Global / EEA / Taiwan - Model kết thúc bằng chữ `G`):**
   - *Ví dụ:* Xiaomi Pad 6S Pro (`24018RPACG`), Xiaomi 14 Global.
   - **Khuyên dùng:** Sử dụng chế độ **`python main.py official`**.
   - **Ưu điểm:** Không bị lỗi phân vùng 20045, mở khóa chính thức qua server Xiaomi, an toàn tuyệt đối 100%, không cần flash lại toàn bộ firmware.

2. **Thiết bị bản Nội địa Trung Quốc (China - Model kết thúc bằng chữ `C`):**
   - *Ví dụ:* Xiaomi 14 Ultra (`24031PN0DC`) cài ROM quốc tế bị khóa lại, gặp lỗi `Code 20045`.
   - **Khuyên dùng:** Sử dụng chế độ **`python main.py bypass`**.
   - **Yêu cầu:** Chuẩn bị sẵn bản ROM Fastboot chính thức tương ứng để phục hồi sau khi nạp payload.

---

## 🛡️ Anti-Brick Safety System (Hệ thống an toàn chống Brick)

1. **Auto-Detect & Strict Model Match:** Tự động đọc mã thiết bị từ Fastboot. Tool sẽ lập tức từ chối chạy nếu phát hiện người dùng chọn sai model.
2. **Anti-Rollback (ARB) Protection:** Kiểm tra giá trị `anti` của máy trước khi ghi firmware, ngăn chặn việc nạp ROM có ARB thấp hơn gây brick máy.
3. **Mandatory Pre-Flash Backup:** Tự động sao lưu Primary GPT và Backup GPT của máy vào thư mục `backups/<serial>_<timestamp>/` trước khi chạm vào bất kỳ phân vùng flash nào.
4. **Patch Date Sentinel:** Tự động phát hiện ngày bản vá bảo mật trên các dòng 8G2 để cảnh báo nếu firmware đã được Xiaomi vá lỗi ABL injection.
5. **Pre-flight ROM Integrity Check:** Quét kiểm tra toàn bộ 45+ file ảnh phân vùng trong bản ROM Fastboot trước khi thực hiện.
6. **Emergency Recovery:** Cung cấp lệnh `python main.py restore-gpt` để khôi phục nhanh bảng phân vùng gốc khi gặp sự cố bất ngờ.

---

## 🚀 Cài đặt & Sử dụng (Installation & Usage)

### 1. Chuẩn bị (Pre-requisites)
1. Cài đặt đầy đủ **Driver Fastboot** trên máy tính (Device Manager nhận `Android Bootloader Interface`).
2. Cắm cáp USB kết nối điện thoại/máy tính bảng với máy tính.

---

### 2. Cài đặt môi trường nhanh bằng `uv`
```bash
cd HyperUnlock-8G3

# Kiểm tra danh sách thiết bị hỗ trợ
uv run python main.py supported

# Đánh giá thiết bị đang kết nối qua ADB
uv run python main.py assess

# Kiểm tra thiết bị ở chế độ Fastboot
uv run python main.py inspect
```

---

### 3. Hướng dẫn Mở khóa

#### Cách 1: Mở khóa chính thức qua Server (Dành cho máy Global hoặc tài khoản đủ điều kiện)
```bash
uv run python main.py official --zone Singapore
```
* Đưa máy về chế độ Fastboot (Nguồn + Giảm âm lượng).
* Tool sẽ yêu cầu đăng nhập tài khoản Mi đã liên kết với thiết bị.
* Sau khi server cấp chữ ký, tool sẽ gửi lệnh mở khóa an toàn mà không cần nạp firmware phức tạp!

#### Cách 2: Bypass phần cứng (Dành cho máy bị kẹt lỗi 20045)
```bash
uv run python main.py bypass --rom-dir "D:\ROM\aurora_images_OS2.0.205.0.VNATWXM"
```
* Tool sẽ nạp payload Ennea vào RAM.
* Màn hình máy tối đi, bạn giữ **Nguồn + Giảm âm lượng** để đưa máy về FASTBOOT.
* Nhấn **Enter**, tool sẽ khôi phục GPT gốc và nạp lại toàn bộ firmware chính thức sạch sẽ. Máy sẽ tự khởi động lại với Bootloader Unlocked 100%!

---

## ⚖️ Disclaimer (Tuyên bố từ chối trách nhiệm)

* Công cụ này được phát triển vì mục đích nghiên cứu học thuật và phục vụ nhu cầu cá nhân hóa thiết bị hợp pháp của người dùng.
* Việc mở khóa bootloader sẽ **xóa sạch toàn bộ dữ liệu** trên thiết bị. Hãy luôn sao lưu dữ liệu cẩn thận trước khi thực hiện!
* Tác giả không chịu trách nhiệm đối với bất kỳ trường hợp mất mát dữ liệu hoặc thao tác sai hướng dẫn của người dùng.

---

## 📄 License

Dự án được phân phối dưới giấy phép mã nguồn mở **GNU General Public License v3.0 (GPL-3.0)**. Xem chi tiết tại tệp [LICENSE](LICENSE).
