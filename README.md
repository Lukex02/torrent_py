# Assignment 1 - Mạng Máy Tính

### SIMPLE TORRENT APPLICATION sử dụng Python

#### Có thể sử dụng cho cả Window và Linux

Chức năng đã hiện thực có thể dùng được:

- Tạo 1 file torrent
- Gửi HTTP GET tới tracker
- Kết nối với peer
- Seed/Chia sẻ 1 file
- Tải về 1 file
- Kết nối với peer qua mạng LAN

Chức năng còn thiếu:

- Kết nối với peer thông qua IP mà tracker trả về
- UI thể hiện trạng thái rõ ràng dễ theo dõi

Chức năng chưa thử nghiệm (khả năng cao là còn thiếu)

- Kết nối peer qua mạng khác nhau
- Tải 1 thư mục nhiều file (tạo torrent từ cả thư mục)
- Multithread kết nối nhiều peer cùng lúc
- Tải từ nhiều peer
- Seed cho nhiều peer (thật ra code cơ chế seed hiện tại là trên lý thuyết có thể thực hiện được vì đang ở vòng `while True` request rồi gửi piece)
#### Idea của nhiều peer:
+ Tạo multi thread
+ Sync các thread
+ Có thể cần dùng máy ảo (virtual machine) để test > 2 peer
+ Thêm cái gì đó để lưu lịch sử đã tải (piece_index của piece đã download) để không phải request trùng
+ Có thể test tải multi thread cho cùng 1 peer (for testing purpose only)
#### *Chức năng có thể không cần thiết*
+ *Sau khi tải về có thể `send message have` để báo mình có mảnh nào đó*
+ *Nếu có `send message have` thì cần thêm `handle message have`*
+ *`Handle message have`: Có thể dùng cái `peer.receive_message()`*

Chức năng không sử dụng được:

- DHT (sử dụng libtorrent không dùng cho window được, và cũng không/chưa tìm được peer)

## Cài đặt thư viện trước khi chạy

`pip install -r requirement.txt`

## Cách chạy

Đầu tiên có thể chạy:

`python main.py help`

hoặc:

`python3 main.py help`

để xem những lệnh có thể chạy và những thông tin cần thiết

## Quy tắc làm việc

1. Clone repository ra, sync nó lên github desktop hay download zip gì đó về tự vọc trên máy local
2. Submit thì tạo branch mới từ cái đống trên máy local, pull request, assign chủ repo làm reviewer

## Reference

Link Bittorrent spec, để biết các message gửi với nhau cần gì:

https://wiki.theory.org/BitTorrentSpecification
