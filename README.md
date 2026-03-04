# TIỂU LUẬN MÔN HỌC LẬP TRÌNH WEB

> **Tên đề tài:** Xây dựng Website GodWEB – Nền tảng blog, cửa hàng số và ví nội bộ  
> **URL triển khai trên Internet:** [https://godexvn.me/](https://godexvn.me/)  
> **Ghi chú bìa:** Sinh viên tự thêm bìa chuẩn VHU từ file mẫu theo yêu cầu giảng viên.

---

## THÔNG TIN BÁO CÁO

- **Môn học:** Lập trình Web
- **Đề tài:** Thiết kế và triển khai Website GodWEB
- **Ngôn ngữ báo cáo:** Tiếng Việt (Unicode)
- **Khuyến nghị định dạng khi xuất Word:** Times New Roman, cỡ chữ 12pt, giãn dòng 1.5, căn đều hai bên
- **Kết quả chạy thực tế:** [https://godexvn.me/](https://godexvn.me/)

---

## LỜI MỞ ĐẦU

Trong bối cảnh chuyển đổi số diễn ra sâu rộng ở hầu hết các lĩnh vực, các website không còn dừng lại ở vai trò “trang giới thiệu thông tin” mà đã trở thành nền tảng cung cấp dịch vụ, giao tiếp với người dùng, và tạo doanh thu trực tiếp. Nhu cầu xây dựng một hệ thống web có tính tích hợp nhiều chức năng – vừa truyền tải nội dung, vừa hỗ trợ giao dịch, vừa quản trị người dùng – ngày càng phổ biến, đặc biệt đối với các nhóm khởi nghiệp, tổ chức cộng đồng và doanh nghiệp vừa, nhỏ.

Xuất phát từ yêu cầu thực tiễn đó, đề tài **GodWEB** được xây dựng với mục tiêu tạo ra một website tổng hợp gồm các phân hệ: trang nội dung (blog), cửa hàng trực tuyến (store), quản lý hồ sơ cá nhân (profile), ví điện tử nội bộ (wallet), cùng khu vực quản trị (admin) để vận hành toàn hệ thống. Việc lựa chọn kiến trúc và công nghệ được cân nhắc theo hướng cân bằng giữa tính thực dụng (dễ phát triển, dễ bảo trì) và khả năng mở rộng trong tương lai.

Báo cáo này trình bày toàn bộ quá trình thực hiện đề tài theo cấu trúc khoa học gồm: tổng quan đề tài, cơ sở lý thuyết, thiết kế website, kết luận và tài liệu tham khảo. Nội dung tập trung vào góc nhìn phân tích chức năng và thiết kế hệ thống, hạn chế trình bày chi tiết câu lệnh/mã nguồn vì phần đó đã có trong source code của dự án.

---

## MỤC LỤC

1. [Chương 1: Tổng quan về đề tài Website](#chương-1-tổng-quan-về-đề-tài-website)
	1. [Bối cảnh và lý do chọn đề tài](#11-bối-cảnh-và-lý-do-chọn-đề-tài)
	2. [Mục tiêu nghiên cứu và phát triển](#12-mục-tiêu-nghiên-cứu-và-phát-triển)
	3. [Phạm vi đề tài](#13-phạm-vi-đề-tài)
	4. [Đối tượng sử dụng](#14-đối-tượng-sử-dụng)
	5. [Kết quả đạt được và URL triển khai](#15-kết-quả-đạt-được-và-url-triển-khai)
2. [Chương 2: Cơ sở lý thuyết](#chương-2-cơ-sở-lý-thuyết)
	1. [Tổng quan kiến trúc ứng dụng web](#21-tổng-quan-kiến-trúc-ứng-dụng-web)
	2. [Công nghệ và công cụ sử dụng](#22-công-nghệ-và-công-cụ-sử-dụng)
	3. [Các nguyên lý thiết kế website áp dụng](#23-các-nguyên-lý-thiết-kế-website-áp-dụng)
	4. [Bảo mật và an toàn thông tin](#24-bảo-mật-và-an-toàn-thông-tin)
	5. [Triển khai, vận hành và bảo trì](#25-triển-khai-vận-hành-và-bảo-trì)
3. [Chương 3: Thiết kế Website](#chương-3-thiết-kế-website)
	1. [Mô hình tổng thể hệ thống](#31-mô-hình-tổng-thể-hệ-thống)
	2. [Thiết kế bố cục giao diện](#32-thiết-kế-bố-cục-giao-diện)
	3. [Thiết kế chức năng theo từng phân hệ](#33-thiết-kế-chức-năng-theo-từng-phân-hệ)
	4. [Thiết kế dữ liệu và luồng nghiệp vụ](#34-thiết-kế-dữ-liệu-và-luồng-nghiệp-vụ)
	5. [Mô tả minh họa giao diện đề xuất chèn hình](#35-mô-tả-minh-họa-giao-diện-đề-xuất-chèn-hình)
4. [Chương 4: Kết luận](#chương-4-kết-luận)
	1. [Kết quả đạt được](#41-kết-quả-đạt-được)
	2. [Hạn chế](#42-hạn-chế)
	3. [Hướng phát triển](#43-hướng-phát-triển)
5. [Tài liệu tham khảo](#tài-liệu-tham-khảo)
6. [Phụ lục gợi ý trình bày Word](#phụ-lục-gợi-ý-trình-bày-word)

---

# CHƯƠNG 1: TỔNG QUAN VỀ ĐỀ TÀI WEBSITE

## 1.1. Bối cảnh và lý do chọn đề tài

Hiện nay, người dùng Internet có xu hướng tiếp cận thông tin, mua sắm và thanh toán trực tuyến ngay trong một hệ sinh thái thống nhất thay vì di chuyển qua nhiều nền tảng rời rạc. Đối với đơn vị vận hành nội dung số, việc tách riêng một website blog, một website bán hàng và một công cụ quản lý giao dịch nội bộ thường tạo ra các bất cập: dữ liệu phân mảnh, khó đồng bộ tài khoản, khó đánh giá hành vi người dùng tổng thể và chi phí quản trị cao.

Đề tài GodWEB được thực hiện nhằm giải quyết bài toán trên theo hướng tích hợp: cùng một tài khoản người dùng có thể đọc bài viết, mua sản phẩm, theo dõi lịch sử đơn hàng, quản lý số dư ví và thực hiện các thao tác liên quan ngay trên cùng một website. Đồng thời, phía quản trị có thể theo dõi sản phẩm, tồn kho, giao dịch, người dùng, bài viết và hoạt động nạp tiền trong một dashboard tập trung.

Lý do chọn đề tài gồm các điểm chính:

- Đáp ứng nhu cầu thực tế về mô hình website đa chức năng.
- Có tính ứng dụng cao cho mô hình startup/SME.
- Phù hợp để vận dụng kiến thức môn Lập trình Web từ frontend đến backend.
- Tạo môi trường thực hành đầy đủ các kỹ năng: thiết kế giao diện, mô hình dữ liệu, xác thực người dùng, quản lý phiên, xử lý form, và triển khai thực tế trên Internet.

## 1.2. Mục tiêu nghiên cứu và phát triển

Mục tiêu tổng quát của đề tài là xây dựng một website vận hành ổn định, có giao diện thân thiện, cung cấp đầy đủ chức năng cốt lõi cho người dùng cuối và quản trị viên.

Mục tiêu cụ thể:

1. Xây dựng hệ thống tài khoản người dùng gồm đăng ký, đăng nhập, quên mật khẩu, cập nhật hồ sơ và đổi mật khẩu.
2. Tạo phân hệ blog cho phép hiển thị danh sách bài viết và trang chi tiết.
3. Tạo phân hệ cửa hàng với sản phẩm, danh mục, chi tiết sản phẩm và lịch sử mua hàng.
4. Tạo phân hệ ví nội bộ để theo dõi số dư, lịch sử nạp tiền, lịch sử giao dịch.
5. Xây dựng khu vực quản trị để quản lý dữ liệu trọng yếu như người dùng, sản phẩm, danh mục, bài viết, đơn hàng, giao dịch và tồn kho.
6. Triển khai website lên môi trường Internet với tên miền truy cập công khai.

Ngoài các mục tiêu chức năng, đề tài còn hướng tới các tiêu chí chất lượng:

- Mã nguồn tổ chức rõ ràng theo module.
- Dễ bảo trì, dễ mở rộng.
- Đảm bảo các nguyên tắc bảo mật cơ bản cho ứng dụng web.
- Trải nghiệm người dùng nhất quán trên các trang.

## 1.3. Phạm vi đề tài

### 1.3.1. Phạm vi chức năng

Đề tài tập trung vào các chức năng chính của một website tích hợp nội dung và thương mại điện tử mức cơ bản đến trung cấp, cụ thể:

- Quản lý người dùng và phân quyền.
- Quản lý bài viết và hiển thị nội dung.
- Quản lý sản phẩm, danh mục, tồn kho.
- Ghi nhận đơn hàng và lịch sử mua hàng.
- Quản lý ví nội bộ và các giao dịch liên quan.
- Dashboard quản trị tổng hợp.

### 1.3.2. Phạm vi kỹ thuật

- Ứng dụng web dạng server-side rendering.
- Cơ sở dữ liệu quan hệ.
- Giao diện sử dụng HTML/CSS/JS truyền thống, tối ưu cho tính dễ triển khai.
- Triển khai lên hạ tầng có thể truy cập qua tên miền công khai.

### 1.3.3. Những nội dung chưa đi sâu

- Chưa triển khai kiến trúc microservices.
- Chưa tích hợp cổng thanh toán bên thứ ba hoàn chỉnh.
- Chưa triển khai hệ thống phân tích dữ liệu nâng cao theo thời gian thực.
- Chưa xây dựng bộ kiểm thử tự động toàn diện (end-to-end ở mức lớn).

## 1.4. Đối tượng sử dụng

Hệ thống GodWEB hướng đến ba nhóm đối tượng chính:

1. **Khách truy cập (Guest):**
	- Xem trang chủ, trang giới thiệu, điều khoản, liên hệ.
	- Xem nội dung blog và sản phẩm công khai.

2. **Người dùng đã đăng ký (Member):**
	- Thực hiện đăng nhập, quản lý hồ sơ cá nhân.
	- Theo dõi đơn hàng đã mua.
	- Sử dụng ví nội bộ: xem số dư, lịch sử nạp, lịch sử giao dịch.

3. **Quản trị viên (Admin):**
	- Quản lý người dùng.
	- Quản lý danh mục, sản phẩm, tồn kho.
	- Quản lý bài viết.
	- Theo dõi đơn hàng, giao dịch, topup.
	- Kiểm soát tổng thể hoạt động hệ thống.

Việc thiết kế theo nhóm đối tượng giúp xác định rõ quyền truy cập, từ đó đảm bảo vừa dễ dùng cho người dùng phổ thông, vừa đủ công cụ nghiệp vụ cho nhà quản trị.

## 1.5. Kết quả đạt được và URL triển khai

Sau quá trình phân tích, thiết kế, lập trình và triển khai, đề tài đã đạt các kết quả chính sau:

- Xây dựng thành công website GodWEB có đầy đủ các phân hệ theo mục tiêu ban đầu.
- Tổ chức source code theo cấu trúc module rõ ràng (routes, templates, static, models, utils).
- Hoàn thiện giao diện đa trang với bố cục thống nhất.
- Triển khai thực tế và truy cập được trên Internet.

**Địa chỉ website đang hoạt động:**  
[https://godexvn.me/](https://godexvn.me/)

Ý nghĩa của kết quả này là đề tài không chỉ dừng ở mức mô phỏng trong môi trường local mà đã đạt mức “sản phẩm có thể vận hành”, đủ cơ sở để đánh giá thực nghiệm theo góc nhìn người dùng thực tế.

---

# CHƯƠNG 2: CƠ SỞ LÝ THUYẾT

## 2.1. Tổng quan kiến trúc ứng dụng web

Ứng dụng web hiện đại thường bao gồm ba lớp logic cốt lõi:

1. **Lớp giao diện (Presentation):** chịu trách nhiệm hiển thị dữ liệu cho người dùng và nhận input từ form, thao tác nút bấm, điều hướng trang.
2. **Lớp nghiệp vụ (Business Logic):** xử lý các quy tắc hệ thống, xác thực điều kiện và điều phối các tác vụ.
3. **Lớp dữ liệu (Data Access):** tương tác với cơ sở dữ liệu để truy vấn, thêm/sửa/xóa thông tin.

Trong đề tài GodWEB, tư duy này được thể hiện bằng việc tách biệt:

- **Routes** xử lý request/response theo từng nhóm chức năng.
- **Models** biểu diễn dữ liệu và quan hệ trong cơ sở dữ liệu.
- **Templates** đảm nhiệm hiển thị giao diện.
- **Static assets** (CSS/JS/image) phục vụ trải nghiệm trực quan.

Việc phân tách rõ tầng chức năng mang lại các lợi ích:

- Dễ mở rộng tính năng mà không phá vỡ toàn hệ thống.
- Dễ kiểm soát lỗi theo module.
- Dễ phân công công việc trong nhóm phát triển.

## 2.2. Công nghệ và công cụ sử dụng

### 2.2.1. Ngôn ngữ và framework phía server

Đề tài sử dụng **Python** làm ngôn ngữ backend và framework web nhẹ, linh hoạt theo mô hình blueprint/module. Điểm mạnh của lựa chọn này:

- Cú pháp rõ ràng, giảm thời gian phát triển.
- Hệ sinh thái thư viện phong phú.
- Phù hợp cho dự án học thuật cần triển khai nhanh nhưng vẫn có cấu trúc chuẩn.

### 2.2.2. Mẫu thiết kế route theo module

Hệ thống route được chia theo nhóm nghiệp vụ:

- `main`: trang chung và điều hướng tổng quan.
- `auth`: đăng ký, đăng nhập, quên mật khẩu.
- `blog`: danh sách và chi tiết bài viết.
- `store`: danh mục sản phẩm, chi tiết, lịch sử mua.
- `wallet`: ví, nạp tiền, lịch sử giao dịch.
- `profile`: hồ sơ cá nhân, đổi mật khẩu, đơn hàng/purchases.
- `admin`: dashboard và các chức năng quản trị dữ liệu.

Mô hình tách route theo chức năng giúp giảm “điểm nghẽn” ở một file lớn, đồng thời tăng khả năng bảo trì về dài hạn.

### 2.2.3. Cơ sở dữ liệu và ORM

Đề tài áp dụng mô hình cơ sở dữ liệu quan hệ, với đối tượng dữ liệu được ánh xạ thông qua ORM. Cách làm này giúp:

- Viết logic nghiệp vụ gần với ngôn ngữ tự nhiên của Python.
- Hạn chế lỗi thao tác SQL thủ công.
- Quản lý quan hệ giữa bảng dữ liệu rõ ràng hơn.

Các thực thể điển hình bao gồm:

- User
- Product
- Category
- Order
- Transaction
- Topup
- Post
- Inventory log

### 2.2.4. Giao diện và template engine

Website dùng mô hình template kế thừa để tái sử dụng bố cục chung:

- `base.html` đóng vai trò khung chính.
- Các trang con kế thừa và điền nội dung theo block.

Lợi ích:

- Đồng nhất giao diện toàn website.
- Giảm lặp mã HTML.
- Thuận tiện bảo trì khi thay đổi header/footer/menu.

### 2.2.5. Công cụ hỗ trợ triển khai

Thông qua các tệp cấu hình như `Procfile` và `requirements.txt`, dự án có thể:

- Chuẩn hóa quá trình cài đặt thư viện.
- Xác định điểm chạy ứng dụng.
- Thuận lợi khi đưa lên môi trường production.

Khi triển khai thành công với tên miền riêng, tính ứng dụng thực tiễn của đề tài được tăng lên rõ rệt, giúp quá trình đánh giá mang tính khách quan hơn.

## 2.3. Các nguyên lý thiết kế website áp dụng

### 2.3.1. Nguyên lý phân cấp thông tin

Thông tin trên website được tổ chức theo cấp độ ưu tiên:

- Cấp cao: trang chủ, danh mục lớn, CTA chính.
- Cấp trung: danh sách sản phẩm/bài viết.
- Cấp chi tiết: trang detail, thông tin cụ thể từng đối tượng.

Nguyên lý này giúp người dùng định hướng nhanh và giảm tải nhận thức khi truy cập lần đầu.

### 2.3.2. Tính nhất quán giao diện

Các thành phần điều hướng, màu sắc chủ đạo, cách đặt nút hành động và cấu trúc tiêu đề được giữ nhất quán giữa các trang. Nhất quán giúp:

- Giảm thời gian làm quen.
- Hạn chế thao tác sai.
- Tạo cảm giác chuyên nghiệp cho sản phẩm.

### 2.3.3. Khả năng sử dụng (Usability)

Website hướng đến các đặc tính:

- Dễ học: người mới có thể sử dụng nhanh.
- Dễ nhớ: quay lại sau thời gian dài vẫn thao tác được.
- Ít lỗi: có thông báo khi nhập sai hoặc thiếu dữ liệu.
- Hài lòng: giao diện rõ ràng, điều hướng liền mạch.

### 2.3.4. Thiết kế hướng chức năng

Thay vì trình bày website như tập hợp trang tĩnh, đề tài được xây dựng theo “hành trình người dùng” (user flow):

- Đăng ký/đăng nhập → truy cập nội dung → chọn sản phẩm → mua hàng → kiểm tra ví/giao dịch → xem lịch sử.

Thiết kế hướng chức năng giúp website giải quyết bài toán thực tế, thay vì chỉ chú trọng hình thức.

## 2.4. Bảo mật và an toàn thông tin

Trong ứng dụng web, bảo mật là yêu cầu nền tảng. Đề tài áp dụng các nguyên tắc cơ bản:

1. **Xác thực người dùng:** chỉ tài khoản hợp lệ mới truy cập chức năng riêng.
2. **Phân quyền:** khu vực admin tách biệt với khu vực người dùng thường.
3. **Quản lý phiên làm việc:** duy trì trạng thái đăng nhập an toàn.
4. **Kiểm tra dữ liệu đầu vào:** giảm rủi ro nhập dữ liệu không hợp lệ.
5. **Bảo vệ thông tin nhạy cảm:** dữ liệu mật khẩu cần lưu trữ theo nguyên tắc mã hóa băm.

Ngoài ra, các thực hành nên tiếp tục hoàn thiện trong tương lai:

- Áp dụng CSRF token cho toàn bộ form quan trọng.
- Tăng cường giới hạn tần suất đăng nhập để giảm brute-force.
- Ghi log bảo mật phục vụ giám sát và phản ứng sự cố.
- Triển khai HTTPS toàn diện và chính sách bảo mật header.

## 2.5. Triển khai, vận hành và bảo trì

### 2.5.1. Quy trình triển khai cơ bản

Một quy trình triển khai thực tiễn thường gồm:

1. Chuẩn hóa phụ thuộc thư viện.
2. Cấu hình biến môi trường.
3. Khởi tạo cơ sở dữ liệu.
4. Chạy migrate/seed (nếu có).
5. Khởi động ứng dụng qua lệnh hoặc process manager.
6. Kiểm thử smoke test trên domain thật.

### 2.5.2. Vận hành sau triển khai

Sau khi website hoạt động công khai, các tác vụ vận hành định kỳ bao gồm:

- Theo dõi trạng thái uptime.
- Kiểm tra log lỗi.
- Sao lưu dữ liệu định kỳ.
- Cập nhật phiên bản thư viện bảo mật.
- Theo dõi hiệu năng truy vấn và tốc độ phản hồi.

### 2.5.3. Ý nghĩa của việc triển khai thật

Nhiều dự án học thuật chỉ chạy ở localhost, do đó khó đánh giá toàn diện. Với GodWEB, việc có URL công khai [https://godexvn.me/](https://godexvn.me/) cho phép:

- Kiểm tra thực tế trên nhiều thiết bị/mạng.
- Đánh giá trải nghiệm người dùng thực.
- Phát hiện vấn đề liên quan cấu hình production mà môi trường local không thể hiện.

---

# CHƯƠNG 3: THIẾT KẾ WEBSITE

## 3.1. Mô hình tổng thể hệ thống

Website GodWEB được thiết kế theo mô hình web server-side rendering với cấu trúc thành phần như sau:

- **Lớp người dùng:** trình duyệt web truy cập domain.
- **Lớp ứng dụng:** xử lý request tại các route theo module chức năng.
- **Lớp dữ liệu:** lưu trữ thông tin người dùng, sản phẩm, giao dịch, bài viết.
- **Lớp tệp tĩnh:** cung cấp CSS, JavaScript, hình ảnh và tài nguyên minh họa.

Luồng hoạt động tổng quát:

1. Người dùng gửi yêu cầu từ trình duyệt.
2. Route tương ứng tiếp nhận và xử lý nghiệp vụ.
3. Hệ thống truy vấn/cập nhật dữ liệu.
4. Kết quả được render thành HTML từ template.
5. Trả phản hồi về trình duyệt.

Điểm mạnh của mô hình này là đơn giản, dễ triển khai cho dự án học thuật nhưng vẫn đáp ứng đầy đủ tính năng nghiệp vụ đa module.

## 3.2. Thiết kế bố cục giao diện

### 3.2.1. Bố cục tổng thể

Giao diện website được tổ chức theo mô hình ba phần:

- **Header:** logo/brand, menu điều hướng, trạng thái đăng nhập.
- **Main content:** nội dung chính thay đổi theo từng trang.
- **Footer:** thông tin bổ sung, liên kết phụ trợ, điều khoản.

Sự thống nhất cấu trúc giúp người dùng dễ định vị và giảm thời gian tìm kiếm chức năng.

### 3.2.2. Điều hướng

Thanh điều hướng được xây dựng theo hướng ưu tiên tác vụ:

- Trang chủ.
- Blog.
- Cửa hàng.
- Ví.
- Hồ sơ cá nhân.
- Khu vực quản trị (khi có quyền).

Mỗi mục menu gắn với nhu cầu thao tác cụ thể, tránh tình trạng menu quá dài gây nhiễu.

### 3.2.3. Tính đáp ứng giao diện

Thiết kế hướng responsive đảm bảo nội dung hiển thị hợp lý trên:

- Màn hình desktop.
- Máy tính bảng.
- Thiết bị di động.

Nguyên tắc áp dụng:

- Chia khối nội dung theo hàng/cột linh hoạt.
- Giãn cách hợp lý để dễ thao tác cảm ứng.
- Giữ cỡ chữ dễ đọc và nút bấm đủ lớn.

## 3.3. Thiết kế chức năng theo từng phân hệ

## 3.3.1. Phân hệ trang chung (`main`)

Bao gồm các trang thông tin cơ bản:

- `home`: giới thiệu nhanh website, điều hướng đến các khu vực chính.
- `about`: mô tả dự án, mục đích hoạt động.
- `contact`: thông tin liên hệ.
- `terms`: điều khoản sử dụng.

Vai trò của phân hệ này là tạo nền tảng nhận diện và tính minh bạch thông tin cho người dùng mới.

## 3.3.2. Phân hệ xác thực (`auth`)

Chức năng trọng tâm:

- Đăng ký tài khoản mới.
- Đăng nhập.
- Quên mật khẩu.

Nguyên tắc thiết kế:

- Form ngắn gọn, rõ nhãn trường nhập.
- Thông báo lỗi cụ thể khi dữ liệu không hợp lệ.
- Điều hướng rõ ràng giữa các trang đăng nhập/đăng ký/quên mật khẩu.

Phân hệ này là cổng vào cho các chức năng cá nhân hóa của toàn website.

## 3.3.3. Phân hệ hồ sơ (`profile`)

Sau khi đăng nhập, người dùng có khu vực cá nhân gồm:

- Trang thông tin hồ sơ.
- Chỉnh sửa thông tin cá nhân.
- Đổi mật khẩu.
- Xem đơn hàng đã đặt.
- Xem lịch sử mua hàng.

Lợi ích thiết kế:

- Người dùng chủ động quản lý thông tin tài khoản.
- Tăng tính tin cậy vì dữ liệu giao dịch minh bạch.
- Tạo trải nghiệm “self-service” thay vì phụ thuộc quản trị viên.

## 3.3.4. Phân hệ blog (`blog`)

Chức năng:

- Danh sách bài viết.
- Trang chi tiết bài viết.

Mục tiêu của blog là xây dựng nội dung giá trị, tăng thời gian ở lại website và hỗ trợ truyền thông cho sản phẩm/dịch vụ. Blog còn là kênh tăng trưởng người dùng thông qua SEO và chia sẻ mạng xã hội.

## 3.3.5. Phân hệ cửa hàng (`store`)

Đây là phân hệ thương mại cốt lõi, gồm:

- Trang danh sách sản phẩm.
- Trang chi tiết sản phẩm.
- Lịch sử giao dịch/mua hàng của người dùng.

Yếu tố đặc thù được mô tả trong thiết kế:

- Hiển thị thông tin sản phẩm rõ ràng (tên, mô tả, giá, trạng thái).
- Liên kết sản phẩm với danh mục giúp điều hướng tốt hơn.
- Cơ chế đối chiếu giao dịch với số dư ví nội bộ.

## 3.3.6. Phân hệ ví (`wallet`)

Phân hệ ví giúp người dùng kiểm soát tài chính nội bộ:

- Xem số dư hiện tại.
- Nạp tiền vào tài khoản.
- Xem lịch sử nạp tiền.
- Xem lịch sử giao dịch.

Thiết kế ví đóng vai trò trung tâm trong trải nghiệm mua hàng, tạo thành hệ tuần hoàn dữ liệu giữa topup – thanh toán – lịch sử giao dịch.

## 3.3.7. Phân hệ quản trị (`admin`)

Đây là phân hệ có độ phức tạp nghiệp vụ cao nhất, bao gồm:

- Dashboard tổng quan.
- Quản lý người dùng.
- Quản lý bài viết (tạo/sửa/xóa).
- Quản lý danh mục sản phẩm.
- Quản lý sản phẩm và tồn kho.
- Quản lý đơn hàng.
- Quản lý giao dịch ví.
- Quản lý topup.

Mục tiêu thiết kế admin:

- Tập trung công cụ vận hành về một khu vực.
- Giảm thao tác phân tán ở nhiều hệ thống rời rạc.
- Tăng khả năng giám sát chất lượng dữ liệu và vận hành.

## 3.4. Thiết kế dữ liệu và luồng nghiệp vụ

## 3.4.1. Các thực thể dữ liệu chính

Hệ thống gồm nhiều thực thể liên kết với nhau theo quan hệ nghiệp vụ:

- **User:** thông tin tài khoản, vai trò, trạng thái.
- **Category:** phân loại sản phẩm.
- **Product:** thông tin mặt hàng.
- **Order:** thông tin đơn mua của người dùng.
- **Transaction:** ghi nhận biến động tài chính.
- **Topup:** ghi nhận sự kiện nạp tiền.
- **Post:** dữ liệu bài viết blog.
- **Inventory record:** theo dõi tồn kho/biến động hàng hóa.

## 3.4.2. Luồng đăng ký và đăng nhập

1. Người dùng truy cập trang đăng ký.
2. Nhập thông tin theo biểu mẫu.
3. Hệ thống kiểm tra hợp lệ và tạo tài khoản.
4. Người dùng đăng nhập.
5. Hệ thống tạo phiên làm việc và điều hướng về khu vực phù hợp.

Luồng này được thiết kế ngắn gọn để giảm tỷ lệ bỏ dở khi tạo tài khoản.

## 3.4.3. Luồng nạp tiền và giao dịch ví

1. Người dùng vào trang ví.
2. Thực hiện yêu cầu nạp tiền.
3. Hệ thống ghi nhận lịch sử topup.
4. Cập nhật số dư ví.
5. Khi mua sản phẩm, hệ thống tạo giao dịch trừ tiền và ghi log lịch sử.

Mục tiêu của luồng là đảm bảo tính minh bạch và khả năng kiểm tra ngược giao dịch.

## 3.4.4. Luồng mua sản phẩm

1. Người dùng xem danh sách sản phẩm.
2. Mở trang chi tiết để xem thông tin.
3. Xác nhận thao tác mua (nếu đủ điều kiện).
4. Hệ thống kiểm tra số dư ví, tồn kho và trạng thái sản phẩm.
5. Tạo đơn hàng và giao dịch liên quan.
6. Cập nhật lịch sử mua trong hồ sơ người dùng.

Luồng nghiệp vụ này phản ánh đúng vòng đời giao dịch trong hệ thống thương mại điện tử cơ bản.

## 3.4.5. Luồng quản trị nội dung và sản phẩm

1. Admin đăng nhập vào khu vực quản trị.
2. Thêm/sửa/xóa bài viết để cập nhật nội dung.
3. Quản lý danh mục và sản phẩm.
4. Theo dõi tồn kho và đơn hàng.
5. Kiểm tra giao dịch/topup để đối soát.

Thiết kế luồng theo tác vụ vận hành giúp hệ thống đáp ứng nhu cầu thực tế của quản trị viên trong việc điều hành liên tục.

## 3.5. Mô tả minh họa giao diện (đề xuất chèn hình)

> Theo yêu cầu tiểu luận, Chương 3 cần có hình ảnh minh họa. Trong bản Markdown này, các vị trí chèn hình được đánh dấu để bạn thay bằng ảnh chụp màn hình thực tế khi hoàn thiện bản Word.

### 3.5.1. Hình trang chủ

- **Hình 3.1 – Giao diện trang chủ GodWEB**
- Nội dung nên thể hiện: banner chính, khu vực điều hướng, các khối thông tin nổi bật.
- Gợi ý chèn ảnh: ảnh toàn màn hình trang [https://godexvn.me/](https://godexvn.me/).

### 3.5.2. Hình đăng nhập/đăng ký

- **Hình 3.2 – Giao diện đăng nhập**
- **Hình 3.3 – Giao diện đăng ký**
- Nội dung cần nhấn mạnh: cấu trúc form, thông báo lỗi/hướng dẫn nhập.

### 3.5.3. Hình blog

- **Hình 3.4 – Danh sách bài viết blog**
- **Hình 3.5 – Trang chi tiết bài viết**
- Nội dung nhấn mạnh: bố cục thông tin, khu vực nội dung chính, điều hướng quay lại.

### 3.5.4. Hình cửa hàng

- **Hình 3.6 – Danh sách sản phẩm**
- **Hình 3.7 – Trang chi tiết sản phẩm**
- Nội dung nhấn mạnh: thẻ sản phẩm, thông tin giá, trạng thái và khu vực thao tác.

### 3.5.5. Hình ví và lịch sử giao dịch

- **Hình 3.8 – Trang ví (số dư, tác vụ nạp tiền)**
- **Hình 3.9 – Lịch sử topup/giao dịch**
- Nội dung nhấn mạnh: tính minh bạch tài chính, khả năng tra cứu lịch sử.

### 3.5.6. Hình khu vực quản trị

- **Hình 3.10 – Dashboard admin**
- **Hình 3.11 – Quản lý sản phẩm**
- **Hình 3.12 – Quản lý người dùng**
- **Hình 3.13 – Quản lý giao dịch/đơn hàng**

Các hình ảnh này giúp báo cáo đạt hiệu quả trực quan, tạo “bức tranh tổng thể” đúng như tiêu chí đề bài.

## 3.6. Đánh giá thiết kế theo tiêu chí môn học

Đề tài được đánh giá theo các nhóm tiêu chí phổ biến của môn Lập trình Web:

1. **Đúng yêu cầu chức năng:**
	- Website có hệ thống tài khoản, nội dung, sản phẩm, giao dịch, quản trị.

2. **Cấu trúc hệ thống rõ ràng:**
	- Tách module theo chức năng, thuận tiện phát triển.

3. **Khả năng vận hành thực tế:**
	- Có URL public để kiểm thử thực nghiệm: [https://godexvn.me/](https://godexvn.me/).

4. **Khả năng mở rộng:**
	- Dễ bổ sung tính năng mới như thanh toán online, coupon, API mobile.

5. **Tính trực quan:**
	- Bố cục giao diện thống nhất và dễ sử dụng.

6. **An toàn và kiểm soát:**
	- Có xác thực tài khoản và phân quyền quản trị.

---

# CHƯƠNG 4: KẾT LUẬN

## 4.1. Kết quả đạt được

Sau quá trình thực hiện, đề tài GodWEB đã hoàn thành các mục tiêu quan trọng:

- Xây dựng được một website đa chức năng trên nền tảng web.
- Triển khai đầy đủ các phân hệ chính: Auth, Blog, Store, Wallet, Profile, Admin.
- Tổ chức mã nguồn rõ ràng theo hướng module.
- Hoàn thiện giao diện và các luồng nghiệp vụ cơ bản phục vụ người dùng thực.
- Triển khai thành công lên Internet tại [https://godexvn.me/](https://godexvn.me/).

Xét trên tiêu chí học phần, đề tài thể hiện đầy đủ năng lực từ phân tích yêu cầu, thiết kế hệ thống, phát triển tính năng đến vận hành thực tế.

## 4.2. Hạn chế

Bên cạnh kết quả đạt được, đề tài vẫn còn một số điểm cần cải thiện:

1. Chưa tích hợp cổng thanh toán điện tử bên ngoài ở mức hoàn chỉnh.
2. Chưa có dashboard phân tích dữ liệu chuyên sâu (BI/analytics).
3. Chưa xây dựng bộ test tự động toàn diện cho mọi luồng nghiệp vụ.
4. Chưa tối ưu sâu về hiệu năng ở tải lớn.
5. Chưa tích hợp quy trình CI/CD đầy đủ cho vòng đời release.

Các hạn chế này là cơ sở để xác định lộ trình phát triển phiên bản tiếp theo.

## 4.3. Hướng phát triển

Trong giai đoạn tiếp theo, dự án có thể mở rộng theo các định hướng sau:

### 4.3.1. Nâng cấp chức năng nghiệp vụ

- Tích hợp thanh toán trực tuyến đa kênh.
- Thêm mã giảm giá, chương trình khuyến mãi.
- Bổ sung quản lý đơn hàng nâng cao (trạng thái, vận chuyển).

### 4.3.2. Nâng cấp kỹ thuật

- Xây dựng API chuẩn để hỗ trợ mobile app.
- Bổ sung caching để tăng hiệu năng.
- Tách dịch vụ gửi email/thông báo thành thành phần riêng.

### 4.3.3. Nâng cấp bảo mật và vận hành

- Áp dụng chính sách mật khẩu mạnh và 2FA.
- Hoàn thiện cơ chế chống tấn công phổ biến.
- Thiết lập giám sát hệ thống theo thời gian thực.
- Chuẩn hóa CI/CD cho kiểm thử và triển khai tự động.

### 4.3.4. Nâng cấp trải nghiệm người dùng

- Cải thiện khả năng tìm kiếm và lọc sản phẩm.
- Tối ưu giao diện mobile-first.
- Bổ sung trang trợ giúp/FAQ và chatbot hỗ trợ.

Nhìn chung, GodWEB có nền tảng tốt để phát triển thành một sản phẩm hoàn chỉnh ở mức thương mại.

---

# TÀI LIỆU THAM KHẢO

1. Tài liệu chính thức Flask: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
2. Tài liệu SQLAlchemy: [https://docs.sqlalchemy.org/](https://docs.sqlalchemy.org/)
3. Tài liệu Jinja: [https://jinja.palletsprojects.com/](https://jinja.palletsprojects.com/)
4. MDN Web Docs (HTML/CSS/JavaScript): [https://developer.mozilla.org/](https://developer.mozilla.org/)
5. OWASP Top 10: [https://owasp.org/www-project-top-ten/](https://owasp.org/www-project-top-ten/)
6. REST API Design Best Practices (tham khảo mở rộng): [https://restfulapi.net/](https://restfulapi.net/)
7. Nền tảng triển khai thực tế của đề tài: [https://godexvn.me/](https://godexvn.me/)

---

# PHỤ LỤC GỢI Ý TRÌNH BÀY WORD

Để đảm bảo đúng yêu cầu nộp bài “minimum 16 trang A4 với font Unicode cỡ 12pt”, có thể thực hiện như sau:

1. Mở `README.md` bằng VS Code.
2. Chuyển đổi sang `.docx` bằng một trong các cách:
	- Copy toàn bộ nội dung sang Microsoft Word.
	- Hoặc dùng công cụ chuyển Markdown sang Word (Pandoc nếu có).
3. Trong Word, áp dụng định dạng:
	- Font: Times New Roman (Unicode)
	- Cỡ chữ: 12pt
	- Giãn dòng: 1.5
	- Lề chuẩn A4 (trên 2cm, dưới 2cm, trái 3cm, phải 2cm hoặc theo quy định của Khoa)
4. Chèn bìa chuẩn VHU từ file mẫu theo yêu cầu giảng viên.
5. Chèn mục lục tự động (References → Table of Contents).
6. Bổ sung ảnh chụp màn hình theo các vị trí gợi ý ở Chương 3 để tăng tính trực quan và đảm bảo số trang.
7. Kiểm tra lại số trang tổng (không tính bìa theo quy định nếu giảng viên yêu cầu riêng).

---

## KẾT LUẬN CHUNG CỦA BÁO CÁO

Tiểu luận đã trình bày đầy đủ quá trình xây dựng và triển khai website GodWEB từ góc nhìn môn học Lập trình Web, bao gồm nền tảng lý thuyết, thiết kế chức năng, tổ chức hệ thống và đánh giá kết quả thực nghiệm. Dự án có thể truy cập công khai tại [https://godexvn.me/](https://godexvn.me/), thể hiện tính ứng dụng thực tế và khả năng vận hành ngoài môi trường phòng lab.

Với nền tảng hiện có, GodWEB hoàn toàn có thể tiếp tục mở rộng theo hướng sản phẩm số hoàn chỉnh, góp phần củng cố năng lực thiết kế và phát triển web toàn diện cho sinh viên trong quá trình học tập cũng như định hướng nghề nghiệp sau này.