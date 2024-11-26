import socket
import struct
import time

def connect_to_peer(peer_ip, peer_port):
    try:
        # Tạo kết nối với peer
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)                 # Thiết lập timeout (5 giây)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.connect((peer_ip, peer_port)) # Kết nối tới peer
        print(f"Connected to {peer_ip}:{peer_port}")
        return s
    except socket.error as e:
        print(f"Connection to {peer_ip}:{peer_port} failed with error: {e}")
        return None, None, None

def receive_message(sock):
    # Đọc và phân tích message từ peer
    response = sock.recv(1024)  # Giới hạn kích thước nhận

    if len(response) >= 5:
        length = struct.unpack('>I', response[:4])[0]
        message_id = struct.unpack('>B', response[4:5])[0]
        return length, message_id, response[5:]
    return None, None, None

def wait_for_unchoke(sock):
    while True:
        # Liên tục nhận message từ peer
        _, message_id, _ = receive_message(sock)
        
        if message_id == 1:  # Unchoke's ID is 1
            print("Received Unchoke message. Start requesting pieces now...")
            break
        else:
            print("Waiting for unchoke...")
            time.sleep(3)     # Cooldown 3 seconds

