# Assignment 1 - Mạng Máy Tính

### SIMPLE TORRENT APPLICATION sử dụng Python

#### Có thể sử dụng cho cả Window và Linux

Chức năng đã hiện thực có thể dùng được:

- Tạo 1 file torrent (từ 1 file lẫn 1 folder nhiều file)
- Tracker
- Gửi HTTP GET tới tracker
- Kết nối với peer
- Seed/Chia sẻ 1 file
- Tải về 1 hoặc nhiều file
- Kết nối với peer qua mạng LAN
- Tải 1 thư mục nhiều file (tạo torrent từ cả thư mục)
- Multithread kết nối nhiều peer cùng lúc
- Tải từ nhiều peer
- Seed cho nhiều peer
- Kết nối với peer thông qua IP mà tracker trả về

## Cài đặt thư viện trước khi chạy

`pip install -r requirements.txt`

## Cách chạy

Đầu tiên khởi chạy Tracker:

`python tracker.py`

Sau đó chạy chương trình chính:

`python main.py`

hoặc:

`python3 main.py`

## Reference

Link Bittorrent spec, để biết các message gửi với nhau cần gì:

https://wiki.theory.org/BitTorrentSpecification
