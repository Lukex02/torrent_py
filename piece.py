import hashlib
import math
import time

import parse
import struct

def get_num_pieces(info):
    # Lấy kích thước của mỗi mảnh
    piece_length = info[b'piece length']

    # Lấy tổng kích thước của tệp
    if b'length' in info:
        # Torrent một tệp
        total_size = info[b'length']
    elif b'files' in info:
        # Torrent nhiều tệp
        total_size = sum(file[b'length'] for file in info[b'files'])
    else:
        raise ValueError("Không tìm thấy thông tin dung lượng trong tệp .torrent")

    # Tính số mảnh
    num_pieces = math.ceil(total_size / piece_length)
    return num_pieces

def wait_for_pieces(sock, piece_size):
    while True:
        # Liên tục nhận message từ peer
        length, message_id, data = receive_data(sock, piece_size)

        if message_id == 7:  # Piece's ID is 7
            print("Received Piece message!")
            return parse.parse_piece(length, data)            
        else:
            print("Waiting pieces...")
            time.sleep(1)     # Cooldown

def verify_piece(piece_data, expected_hash):
    actual_hash = hashlib.sha1(piece_data).digest()
    # print("Actual:", actual_hash)
    # print("Expected:", expected_hash)
    return actual_hash == expected_hash

def write_piece_to_file(filename, piece_index, piece_data, piece_length):
    with open(filename, 'r+b') as f:
        f.seek(piece_index * piece_length)  # Định vị trí ghi
        f.write(piece_data)  # Ghi mảnh vào tệp

def receive_data(sock, piece_size):
    # Biến để lưu dữ liệu nhận được
    data = b""

    # Tiếp tục nhận dữ liệu cho đến khi đủ kích thước piece_size
    while len(data) < piece_size:
        # Tính toán bao nhiêu byte còn thiếu
        remaining = piece_size - len(data)

        # Nhận dữ liệu, tối đa là remaining bytes
        chunk = sock.recv(min(remaining, 1024))  # Đọc tối đa 16KB mỗi lần

        # Nếu không còn dữ liệu (kết nối bị đóng), thoát
        if not chunk:
            raise Exception("Kết nối bị đóng trước khi nhận hết dữ liệu.")

        # Thêm dữ liệu nhận được vào biến data
        data += chunk

    # Because the package return is always greater than 16KB
    last_chunk = sock.recv(1024)
    data += last_chunk

    length = struct.unpack('>I', data[:4])[0]
    message_id = struct.unpack('>B', data[4:5])[0]

    return length, message_id, data[5:]