# Thông Tin Deploy — Checkpoint 5

## Thông tin học viên

| Mục | Nội dung |
|---|---|
| Họ và tên | Trần Quốc Bảo Long |
| Mã học viên | 2A202602696 |
| Repo | https://github.com/longtqb04/K4-L3A-TranQuocBaoLong-2A202602696-Cloud-Service-And-Deployment |
| Public URL | https://k4-l3a-tranquocbaolong-2a202602696-cloud-service-production.up.railway.app |
| Platform | Railway |
| Ngày triển khai và kiểm tra | 28/09/2026 |
| Project | magnificent-empathy |
| Môi trường | production, US West, 1 replica agent + Redis |

## Cấu hình thực tế

Service kết nối GitHub branch main, bản code 85b266a (Completed CP1–4), build bằng Dockerfile. Đã tạo public domain trỏ cổng 8080, tạo Redis và triển khai lại cấu hình kết nối. Các sửa code/Docker Compose mới trong workspace chưa được push lên GitHub, nên chưa nằm trong bản cloud này.

| Biến | Nguồn |
|---|---|
| `PORT` | Railway cấp; domain trỏ port 8080 |
| `AGENT_API_KEY` | Secret đã đặt sẵn trên dashboard; request có xác thực đã thành công, không ghi giá trị |
| `REDIS_URL` | Tham chiếu `${{Redis.REDIS_URL}}` từ Redis service cùng project |
| `RATE_LIMIT_PER_MINUTE` | Biến dashboard; phép thử xác nhận 10 request/phút |
| `MONTHLY_BUDGET_USD` | Biến dashboard; cấu hình bài lab 10.0 USD, không thử tiêu hết ngân sách cloud |
| `LOG_LEVEL` | Biến dashboard; cấu hình bài lab INFO |

Healthcheck Path đặt `/health` trên dashboard. Đã tắt Wait for CI vì repository chưa có workflow; chưa triển khai CI/CD bonus. Railway hiện thông báo Config as Code đã deprecated và không nhận service mới chưa từng dùng từ 28/08/2026, vì vậy không mặc định coi mọi giá trị trong railway.toml đã được áp dụng. [Tài liệu Railway](https://docs.railway.com/config-as-code/reference).

## Kết quả gọi API thật

Kiểm tra qua HTTPS bằng HTTP client, không in khóa vào output:

```text
GET /health -> 200 {"status":"ok","service":"day12-agent","version":"1.0.0"}
GET /ready  -> 200 {"status":"ready","redis":true}
POST /ask, không có key -> 401 {"detail":"invalid or missing API key"}
POST /ask, có key, user exercise-88396e4f:
  Request 1..10: 200
  history_length: 0, 2, 4, 6, 8, 10, 12, 14, 16, 18
  Request 11..12: 429 {"detail":"rate limit exceeded"}
  Request 1: tokens_in=4, tokens_out=38, cost_usd=0.0000234
```

LLM là mock; cost_usd là chi phí mô phỏng. Hạ tầng Railway dùng tài khoản Trial hiện có.

## Lỗi triển khai đã sửa

Trước khi sửa, /health trả 200 nhưng /ready trả 503 với redis:false. Biến Redis đang trỏ localhost:6379, trong khi project chưa có Redis service. Đã tạo Redis, dùng tham chiếu kết nối nội bộ và triển khai lại; /ready sau đó trả 200. Xem thêm câu 10 trong exercises.md.

## Tái kiểm tra

```powershell
Invoke-RestMethod https://k4-l3a-tranquocbaolong-2a202602696-cloud-service-production.up.railway.app/health
Invoke-RestMethod https://k4-l3a-tranquocbaolong-2a202602696-cloud-service-production.up.railway.app/ready
```

Để thử /ask, dùng scripts/observe.py với OBSERVE_URL là Public URL và AGENT_API_KEY từ môi trường. Script tạo user thử riêng và không in secret.

## Bằng chứng local

Ảnh dashboard triển khai thành công: [screenshots/dashboard.png](screenshots/dashboard.png). Trình duyệt tích hợp chặn mở URL /health (`net::ERR_BLOCKED_BY_CLIENT`), nên chưa có ảnh trình duyệt cho endpoint này; kết quả HTTP và kiểm thử CP5 ở trên đã được chạy thật. CP5: 9 passed, 4 skipped (fallback).

[evidence/observations.md](evidence/observations.md), [log](evidence/local-agent.txt), [trạng thái stack](evidence/local-stack.txt) ghi kết quả Docker 3 replica, số đo image và kiểm tra bổ sung. Local chạy qua Nginx ở http://localhost:8000; không dùng fallback cho CP5 vì cloud đã hoạt động.
