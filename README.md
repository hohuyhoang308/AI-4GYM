# AI-4GYM

Chatbot Gym tiếng Việt cho người mới: tra cứu bài tập, hỏi kỹ thuật, gợi ý nhóm cơ và lịch tập. Web có đăng ký/đăng nhập để lưu lịch sử hội thoại; khách vẫn chat được nhưng lịch sử sẽ mất khi tải lại trang. AI chạy local bằng **LangChain + RAG + Chroma + Ollama**, không dùng API AI bên ngoài. Tài khoản và hội thoại được lưu trong MySQL của Serbay.

**Cài từ đầu:** xem [setup.md](setup.md). Tài liệu này hướng dẫn phần mềm cần cài, cấu hình Serbay/MySQL, tải model Ollama, tạo chỉ mục và chạy web trên Windows.

## Chạy nhanh sau khi đã cài

Mở hai cửa sổ PowerShell tại thư mục dự án.

**Cửa sổ backend:**

```powershell
Set-Location BE
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Cửa sổ frontend:**

```powershell
Set-Location FE
npm run dev
```

Vào [http://127.0.0.1:5173](http://127.0.0.1:5173). Trạng thái hệ thống ở [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health); Swagger API ở [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). MySQL và Ollama cần đang chạy.

## Tính năng

- Hỏi đáp nhiều lượt về bài tập, kỹ thuật và các lỗi cần tránh.
- Mỗi câu hỏi dùng tối đa 3 lượt hỏi–đáp gần nhất làm ngữ cảnh; câu hỏi nối tiếp được tìm tài liệu theo mạch hội thoại.
- Gợi ý bài tập theo nhóm cơ và lịch tập 1–6 buổi/tuần.
- Hiển thị nguồn dữ liệu được RAG truy xuất; từ chối câu hỏi ngoài Gym/Fitness.
- Tài khoản lưu lịch sử trong MySQL, có thể mở lại, đổi tên hoặc xóa hội thoại.
- Chế độ khách không ghi lịch sử vào MySQL và xóa cuộc chat khi F5.

## Cấu trúc

```text
AI-4GYM/
├── BE/
│   ├── app/
│   │   ├── api/routes/        # HTTP API: auth, chat, hội thoại, danh mục, health
│   │   ├── core/              # cấu hình
│   │   ├── db/                # MySQL: model, session
│   │   ├── services/          # RAG, dữ liệu, lịch tập, kiểm tra phạm vi
│   │   ├── scripts/           # init_db và ingest
│   │   └── main.py            # FastAPI và phục vụ FE/dist
│   ├── data/
│   │   ├── raw/data.xlsx
│   │   ├── processed/qa.json
│   │   ├── processed/train.json
│   │   ├── processed/test.json
│   │   ├── processed/split_manifest.json
│   │   ├── curated/exercises.json
│   │   └── index/chroma/      # tạo local, không đưa lên Git
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── FE/
│   ├── src/components/
│   ├── src/lib/api.ts
│   ├── src/App.tsx
│   └── package.json
├── setup.md
└── README.md
```

## Dữ liệu

`BE/data/raw/data.xlsx` có **965 cặp hỏi đáp**; `BE/data/processed/qa.json` là bản chuyển đổi đầy đủ sang JSON, có số thứ tự và dòng Excel. Dữ liệu được chia cố định theo câu hỏi đã chuẩn hóa:

| Tập dữ liệu | File | Số câu | Tỷ lệ | Cách dùng |
| --- | --- | ---: | ---: | --- |
| Train/corpus | `BE/data/processed/train.json` | 772 | 80% | Lập chỉ mục RAG trong Chroma |
| Test | `BE/data/processed/test.json` | 193 | 20% | Giữ riêng để kiểm tra, không lập chỉ mục |

`BE/data/processed/split_manifest.json` ghi seed, số lượng và tỷ lệ. Các câu hỏi trùng sau chuẩn hóa nằm cùng một tập. Thêm 10 bài tập có nguồn từ [ACE Exercise Library](https://www.acefitness.org/resources/everyone/exercise-library/experience/beginner/) vào corpus, nên Chroma có **782 tài liệu**. Excel không có cột nguồn riêng nên các mục hỏi đáp ghi nguồn `data.xlsx`.

Phép chia ngăn câu hỏi trùng sau chuẩn hóa xuất hiện ở cả hai tập; các câu diễn đạt khác nhau nhưng cùng ý chưa được nhóm tự động.

**Lưu ý cho báo cáo:** “80% train” ở đây là dữ liệu dùng để xây dựng kho truy xuất; dự án **không fine-tune/huấn luyện lại** model Qwen hay model embedding. RAG lấy tài liệu khi trả lời, theo [mô tả của LangChain](https://docs.langchain.com/oss/python/deepagents/retrieval). Tập test 20% chưa đồng nghĩa độ chính xác 20% hay bất kỳ chỉ số chất lượng nào.

Chất lượng từng câu trả lời trong Excel chưa được xác minh thủ công. Chatbot hỗ trợ tham khảo khi tập luyện, không thay thế đánh giá chuyên môn khi có chấn thương hoặc bệnh lý.

## Kiểm tra

```powershell
# Tại BE/, khi MySQL và Ollama đang chạy
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

# Tại FE/
npm run build
```

Xem [setup.md](setup.md) nếu cần cài mới hoặc xử lý lỗi khi chạy.
