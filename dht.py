import libtorrent as lt
import time

def dht(torrent_path):        
    dht_session = lt.session()
    # Cấu hình DHT
    settings = {
        'enable_dht': True,
        'dht_announce_interval': 30,   # Thời gian thông báo lại với DHT
        'dht_bootstrap_nodes': 'dht.libtorrent.org:25401'  # Bootstrap node mặc định
    }

    # Áp dụng cấu hình DHT
    dht_session.apply_settings(settings)

    dht_params = {
        'save_path': './',  # Đường dẫn lưu tạm tệp (không cần thiết cho tìm peer)
        'storage_mode': lt.storage_mode_t(2),  # Bộ nhớ đệm, không cần lưu tệp
        'ti': lt.torrent_info(torrent_path)
    } 

    # Add torrent vào session
    handle = dht_session.add_torrent(dht_params)

    # Chờ để nhận phản hồi từ DHT
    print("Đang tìm kiếm peer qua DHT...")
    time_limit = time.time() + 60  # Giới hạn thời gian là 60 giây

    while handle.status().state != lt.torrent_status.seeding:
        time.sleep(1)
        if time.time() > time_limit:
            print("Hết thời gian chờ.")
        break

    # Lấy danh sách các peer đã tìm được
    if handle.status().state == lt.torrent_status.seeding or handle.status().progress > 0:
        print("Tìm thấy metadata. Danh sách các peer:")
        peers = handle.get_peer_info()
        for peer in peers:
            print(f"IP: {peer.ip[0]}, Port: {peer.ip[1]}")
    else:
        print("Không tìm thấy peer nào.")
    
    return