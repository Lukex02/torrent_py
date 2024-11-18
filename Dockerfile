# 1. Sử dụng base image Python
FROM python:3.9-slim

# 2. Thiết lập thư mục làm việc
WORKDIR /app

# 3. Sao chép các file cần thiết vào container
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# 4. Sao chép toàn bộ mã nguồn
COPY . .

ENV PORT=5000

# 5. Expose cổng ứng dụng
EXPOSE 5000

# 6. Lệnh để chạy ứng dụng
# CMD ["python", "main.py"]
