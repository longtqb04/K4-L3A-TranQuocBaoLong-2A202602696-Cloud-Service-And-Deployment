# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Bài làm đã thay các dòng giữ chỗ bằng câu trả lời và số liệu quan sát.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Trần Quốc Bảo Long — Mã học viên: 2A202602696
>
> Quan sát ngày 28/09/2026. Số đo Docker và log lấy từ lần chạy thật;
> bằng chứng bổ sung ở `evidence/observations.md` và `evidence/local-agent.txt`.

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Khi đưa image lên Railway nhưng quên khai báo `AGENT_API_KEY`, nếu dùng mặc định `changeme` thì service vẫn có thể nhận request bằng khóa dễ đoán và bị dùng trái phép. Bắt buộc có khóa giúp phát hiện lỗi cấu hình trước khi phục vụ người dùng. Khi chạy `Settings(_env_file=None)` trong container không truyền khóa, tôi nhận `ValidationError: agent_api_key — Field required`.

Tôi còn thấy cấu hình ban đầu được đọc lười: khởi động bằng Uvicorn chưa chắc tạo `Settings` ngay. Vì vậy đã thêm `get_settings()` ở đầu `lifespan`, để thiếu khóa thực sự làm startup thất bại, thay vì chỉ lỗi ở request đầu tiên.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Một dòng log thật của agent-3 sau khi gọi `/ask` qua Nginx:

```json
{"event": "ask_completed", "level": "info", "timestamp": "2026-09-28T16:12:51.427350+00:00", "user_id": "exercise-ecded850", "tokens_in": 4, "tokens_out": 38, "cost_usd": 2.34e-05}
```

Tôi có thể (1) lọc theo `user_id`, `event` và khoảng thời gian để tìm các lần hỏi của một người dùng trên nhiều container; (2) cộng `cost_usd`, `tokens_in`, `tokens_out` theo user hoặc theo ngày để theo dõi chi phí và đặt cảnh báo. Một dòng `print("đã trả lời xong")` không cung cấp các trường dữ liệu này. Chi phí trong lab là số do mock LLM mô phỏng, không phải hóa đơn LLM thật.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | khoảng 1730 MB (`1.73GB`) |
| Multi-stage | 295 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Tôi dựng `Dockerfile.single` theo các lệnh của bản đầu ở commit `1bf8ea5` (`FROM python:3.11`, `COPY . .`, `RUN pip install -r requirements.txt`), rồi build hai tag `agent:single` và `agent:multi`. Bảng dùng cùng trường `.Size` của `docker images --format`, tương ứng DISK USAGE trên Docker Desktop 29.0.1. Chênh lệch xấp xỉ 1435 MB, khoảng 83%.

Phần lớn chênh lệch đến từ base Python đầy đủ có nhiều công cụ, compiler và thư viện phát triển; bản mới dùng `python:3.11-slim`, đồng thời tắt cache của pip. Không thể quy toàn bộ mức giảm cho riêng multi-stage vì hai bản còn thay đổi base image và cách cài dependency. Runtime hiện vẫn cài cả thư viện test trong `requirements.txt`; thư mục wheels đã COPY ở layer trước cũng không mất khỏi lịch sử image chỉ vì bị xóa ở layer sau.

Docker còn hiển thị CONTENT SIZE lần lượt `447MB` và `75.8MB`; không dùng cột này lẫn với DISK USAGE trong bảng. Tham khảo cách các layer được lưu: [Docker storage drivers](https://docs.docker.com/engine/storage/drivers/).

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Tôi thêm tạm một comment vào `app/main.py`, build `agent:cache-check` rồi khôi phục file. Build log báo `CACHED` ở `WORKDIR`, `COPY requirements.txt`, `RUN pip wheel` của builder và ở bước tạo user, COPY wheels, COPY requirements, `RUN pip install` của runtime. Chỉ bước `COPY --chown=appuser:appuser . .` phải tạo lại, sau đó Docker xuất image/config mới.

Nếu đặt `COPY . .` trước `RUN pip install` trong cùng stage, sửa source sẽ làm cache của COPY thay đổi và bước pip install phía sau phải chạy lại dù `requirements.txt` không đổi. Vì thế tách dependency khỏi source giúp các lần sửa code nhanh hơn.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Một lỗ hổng thực thi mã trong Python có thể cho kẻ tấn công chạy lệnh với quyền của process ứng dụng. Nếu process là root trong container, họ có nhiều quyền hơn với filesystem và tài nguyên được cấp; kết hợp mount nhạy cảm, Docker socket, cấu hình privileged hoặc lỗ hổng kernel/container runtime có thể dẫn đến quyền cao trên host. Root trong container không tự động đồng nghĩa đã là root trên host: vẫn cần đường vượt qua lớp cách ly.

`USER appuser` giảm quyền ngay tại bước mã bị khai thác chạy trong container. Kết quả `id` của image là `uid=10001(appuser) gid=10001(appuser)`, thay vì UID 0. Biện pháp này giảm thiệt hại, nhưng không thay thế cập nhật bảo mật và hạn chế mount/capability.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> Tối đa 20 request được chấp nhận trong hai giây nằm hai bên ranh giới phút: gửi 10 request lúc 10:00:59.x, rồi thêm 10 request lúc 10:01:00.x sau khi bộ đếm reset. Mỗi phút vẫn chỉ có 10 request. Sliding window xét 60 giây gần nhất nên 10 request trước vẫn được tính, không cho burst 20 request này. Trong phép thử tuần tự qua Nginx của tôi, 10 request đầu trả 200, request 11 và 12 trả 429. Đây là quan sát tuần tự; code hiện chưa dùng thao tác Redis nguyên tử cho toàn bộ check-and-add nên không khẳng định chống vượt hạn mức khi nhiều request đồng thời.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> Rate limit giới hạn tần suất theo user trong 60 giây, còn cost guard giới hạn tổng USD theo user trong tháng UTC. Tôi thử trên Redis local với các user riêng: ghi chi tiêu 10.01 USD vào ngân sách 10 USD, request đầu vẫn qua rate limit nhưng cost guard trả `402 monthly budget exceeded`. Ngược lại, user có chi tiêu 0 USD qua cost guard, nhưng sau 10 lần trong cửa sổ, lần thứ 11 bị rate limit trả `429 rate limit exceeded`.

Trong `/ask`, rate limit được gọi trước cost guard. `guard.check(user_id)` hiện không truyền chi phí ước lượng, mặc định là 0, và điều kiện chặn là `spent > budget`. Do đó request khi vừa bằng hoặc gần sát ngân sách vẫn có thể được xử lý rồi mới đẩy tổng chi phí vượt mức; đây chưa phải cơ chế bảo đảm tuyệt đối không vượt ngân sách.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Nếu cùng một endpoint kiểm tra Redis được dùng cho cả liveness và readiness, trình tự là: Redis mất kết nối → ba instance kiểm tra dependency thất bại → readiness loại chúng khỏi danh sách nhận traffic → nếu lỗi kéo dài đủ ngưỡng liveness thì orchestrator restart các container → container mới vẫn không kết nối được Redis, nên có thể tiếp tục bị loại/restart → khi Redis phục hồi, probe thành công và các instance mới nhận traffic lại. Restart ứng dụng không chữa được Redis và có thể làm gián đoạn request đang chạy.

Không thể kết luận cứ mất Redis 30 giây là cả ba chắc chắn restart: còn phụ thuộc chu kỳ và ngưỡng probe. Riêng Compose của bài dùng interval 30 giây, retries 3; Docker healthcheck chỉ đánh dấu unhealthy, không tự restart vì unhealthy. Thiết kế tách biệt giữ `/health` trả 200 khi process còn sống, còn `/ready` trả 503 nếu Redis hỏng. Trên Railway tôi đã quan sát đúng cặp kết quả 200/503 này trước khi sửa kết nối Redis.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Tôi sửa Compose để agent chỉ expose cổng nội bộ 8000 và Nginx nhận cổng host 8000, rồi chạy `docker compose up -d --build --scale agent=3`. Nếu vẫn map `8000:8000` trên từng agent như cấu hình ban đầu, các replica sẽ tranh cùng cổng host.

Với cùng `X-User-Id: exercise-ecded850`, 10 request tuần tự qua Nginx cho `history_length` bằng `0, 2, 4, 6, 8, 10, 12, 14, 16, 18`. Log xác nhận request được xử lý trên cả agent-1, agent-2 và agent-3. Response đếm lịch sử trước câu hỏi hiện tại; mỗi lần thành công thêm hai message. Store giữ tối đa 20 message nên không tăng vô hạn.

Nếu dùng dict Python riêng từng process và phân phối round-robin đều, có thể thấy `0, 0, 0, 2, 2, 2, 4, 4, 4, ...`; khi phân phối không đều con số có thể tăng rồi giảm khi đổi instance. Restart sẽ mất lịch sử ở instance đó. Dùng Redis chung giúp cả ba đọc cùng lịch sử; kết quả này không chứng minh các request đồng thời của cùng user được tuần tự hóa.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> Lỗi thật trên Railway: `/health` trả 200 nhưng `/ready` trả **503** với `{"status":"not ready","redis":false}`. Tôi kiểm tra biến `REDIS_URL` trong dashboard và thấy hostname là `localhost`, port `6379`. Địa chỉ này trỏ vào container agent, không phải Redis ở máy cá nhân; project lúc đó cũng chưa có Redis service.

Tôi tạo Redis trong cùng project, thay kết nối bằng tham chiếu `${{Redis.REDIS_URL}}`, rồi triển khai lại. Bản deploy còn bị kẹt `Waiting for CI` vì bật chờ CI trong khi repository chưa có workflow; tôi tắt tùy chọn đó cho bài lab và đặt health check `/health` trên dashboard.

Sau khi sửa, URL `https://k4-l3a-tranquocbaolong-2a202602696-cloud-service-production.up.railway.app` trả `/health` 200, `/ready` 200 với `redis:true`; `/ask` thiếu khóa trả 401, có khóa trả 200. Với user `exercise-88396e4f`, 10 request đầu thành công, request 11 và 12 trả 429. Tôi xác nhận bằng API thực tế thay vì chỉ nhìn trạng thái deployment Online.
