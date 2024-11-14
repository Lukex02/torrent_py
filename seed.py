import parse
import math
import struct
import peer

def wait_for_handshake(socket):
    response = socket.recv(1024)
    print("Received handshake response from a peer!")
    return response[0:68]

def wait_for_interested(socket):
    length, message_id, response = peer.receive_message(socket)
    if message_id == 2:  # Interested ID = 2
        print("Peer is interested!")
    return socket

def wait_for_request(socket):
    if socket is None:
        return None, None, None
    
    length, message_id, response = peer.receive_message(socket)
    # print("Request id: ", message_id)
    if message_id == 6:  # Interested ID = 6
        print("Received a request message!")
        piece_index, offset, length = parse.parse_request(response)
        print(f"Piece requested index: {piece_index}, offset: {offset}, length: {length}")
        return piece_index, offset, length

def validate_handshake(handshake, info_hash):
    if handshake[1:20] != b"BitTorrent protocol":
        return False
    if handshake[28:48] != info_hash:
        return False
    return True

def generate_bitfield(data, piece_size, num_pieces):
    bitfield = bytearray(math.ceil(num_pieces / 8))  # Khởi tạo bitfield với số byte cần thiết

    for i in range(num_pieces):
        start = i * piece_size
        end = start + piece_size
        piece = data[start:end]  # Lấy dữ liệu của mảnh từ dữ liệu tổng
        if piece:  # Giả sử nếu có dữ liệu trong đoạn này thì mảnh đó có sẵn
            byte_index = i // 8  # Xác định byte trong bitfield chứa bit của mảnh
            bit_index = i % 8  # Xác định vị trí bit trong byte
            bitfield[byte_index] |= (1 << (7 - bit_index))  # Đặt bit tương ứng thành 1

    return bitfield

def send_piece(socket, piece_index, begin_offset, block_data):
    message_id = 7  # ID của piece message
    message_length = 9 + len(block_data)  # 4 byte cho index, 4 byte cho begin_offset, và dữ liệu

    # Tạo thông điệp piece message
    piece_message = struct.pack(">IbII", message_length, message_id, piece_index, begin_offset)
    piece_message += block_data  # Thêm block dữ liệu vào thông điệp

    # Gửi thông điệp qua kết nối socket
    socket.sendall(piece_message)
    print(f"Sent piece {piece_index}, begin_offset {begin_offset}, length {len(block_data)} bytes")