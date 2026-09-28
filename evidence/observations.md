# Quan sát thực tế ngày 2026-09-28

## Docker local

- Docker Engine 29.0.1; `docker compose up -d --build --scale agent=3` thành công.
- Ba agent healthy, một Redis dùng chung, Nginx xuất cổng 8000.
- `/health`: 200; `/ready`: 200; `/ask` thiếu key: 401.
- User `exercise-ecded850`, 12 request liên tiếp: 10 lần 200 rồi 2 lần 429.
- `history_length`: 0, 2, 4, 6, 8, 10, 12, 14, 16, 18.
- Log cùng user xuất hiện ở cả agent-1, agent-2 và agent-3 (xem local-agent.txt).
- `docker images agent --format '{{.Repository}}:{{.Tag}} {{.Size}}'`:
  - agent:single 1.73GB
  - agent:multi 295MB
- Docker Desktop còn hiển thị CONTENT SIZE: single 447MB, multi 75.8MB. Đây là cột khác với DISK USAGE; không trộn hai loại số đo.
- `docker image inspect ... .Size`: single 446586967 bytes; multi 75786024 bytes trên image store hiện tại.
- Thêm comment vào app/main.py rồi build: các bước dependency CACHED; COPY source chạy lại. Đã khôi phục file.
- `docker run --rm agent:multi id`: uid=10001(appuser) gid=10001(appuser).
- Settings không có API key: ValidationError, agent_api_key, Field required.
- CP1–CP4: 68 passed, 2 deselected (`not docker`), chạy container với repository gắn chỉ đọc để đọc được Dockerfile/Compose đã bị loại khỏi image bởi .dockerignore.

## Lỗi đã quan sát

- Local: container unhealthy dù /health 200; `curl`: executable file not found in $PATH. Sửa health check Compose sang Python urllib.
- Railway: /health 200 nhưng /ready 503 với `{"status":"not ready","redis":false}`. /ask thiếu key trả 401. Cần khắc phục Redis trước khi xác nhận triển khai hoàn tất.
- Kiểm tra giao diện sửa REDIS_URL xác nhận hostname cũ là `localhost`, port `6379`. Đã tạo Redis trong cùng project và thay bằng tham chiếu `${{Redis.REDIS_URL}}`.
- Kiểm chứng guards với Redis local và user riêng: rate allowed / cost 402 khi spent=10.01, budget=10; budget allowed / rate 429 ở lần thứ 11 khi spent=0.
- Sau triển khai lại Railway: /health 200, /ready 200 (redis:true), thiếu key 401; user exercise-88396e4f có 10 lần 200, history_length 0..18 bước 2, tiếp theo hai lần 429.
- CP5: 9 passed, 4 skipped (các bài local fallback); có chạy test dùng API key thật từ môi trường, không xuất khóa.
- Deployment cuối: add6774f-3ad8-45ee-8de3-2be139f2c08d, dashboard ghi Active / Deployment successful. Ảnh tại ../screenshots/dashboard.png.
- Trình duyệt tích hợp chặn mở URL /health với net::ERR_BLOCKED_BY_CLIENT; kiểm chứng HTTP và CP5 qua Docker vẫn thành công. Không có ảnh health giả lập.
