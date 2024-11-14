# Assignment 1 - Mạng Máy Tính

SIMPLE TORRENT APPLICATION sử dụng Python

Chức năng đã hiện thực có thể dùng được:

- Tạo 1 file torrent
- Gửi HTTP GET tới tracker
- Kết nối với peer
- Seed/Chia sẻ 1 file
- Tải về 1 file

Chức năng còn thiếu:

- Kết nối với peer thông qua IP mà tracker trả về
- UI thể hiện trạng thái rõ ràng dễ theo dõi

Chức năng chưa thử nghiệm (khả năng cao là còn thiếu)

- Tải 1 thư mục nhiều file
- Multithread kết nối nhiều peer cùng lúc
- Tải từ nhiều peer
- Seed cho nhiều peer

Chức năng không sử dụng được:

- DHT (sử dụng libtorrent không dùng cho window được, và cũng không chưa tìm được peer)

### Cài đặt thư viện trước khi chạy

`pip install -r requirement.txt`

### Cách chạy

Đầu tiên có thể chạy:

`python main.py help`
hoặc:
`python3 main.py help`

để xem những lệnh có thể chạy và những thông tin cần thiết
