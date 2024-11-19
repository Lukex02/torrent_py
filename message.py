import struct
import parse

def create_handshake_message(info_hash, peer_id):
    pstr = b"BitTorrent protocol"
    pstrlen = len(pstr)
    reserved = b'\x00' * 8  # 8 byte reserved
    handshake_message = struct.pack('B', pstrlen) + pstr + reserved + info_hash + peer_id
    return handshake_message

def create_choke_message():
    length_prefix = struct.pack(">I", 1)
    message_id = struct.pack(">B", 0)
    return length_prefix + message_id

def create_unchoke_message():
    length_prefix = struct.pack(">I", 1)
    message_id = struct.pack(">B", 1)
    return length_prefix + message_id

def create_interested_message():
    length_prefix = struct.pack(">I", 1)
    message_id = struct.pack(">B", 2)
    return length_prefix + message_id

def create_not_interested_message():
    length_prefix = struct.pack(">I", 1)
    message_id = struct.pack(">B", 3)
    return length_prefix + message_id

def create_have_message(piece_index):
    length_prefix = struct.pack(">I", 5)
    message_id = struct.pack(">B", 4)
    payload = struct.pack(">I", piece_index)
    return length_prefix + message_id + payload

def create_bitfield_message(bitfield):
    length_prefix = struct.pack(">I", 1 + len(bitfield))
    message_id = struct.pack(">B", 5)
    return length_prefix + message_id + bitfield

def create_request_message(index, begin, length):
    length_prefix = struct.pack(">I", 13)
    message_id = struct.pack(">B", 6)
    payload = struct.pack(">III", index, begin, length)
    return length_prefix + message_id + payload

def create_piece_message(index, begin, block):
    length_prefix = struct.pack(">I", 9 + len(block))
    message_id = struct.pack(">B", 7)
    payload = struct.pack(">II", index, begin) + block
    return length_prefix + message_id + payload

def create_cancel_message(index, begin, length):
    length_prefix = struct.pack(">I", 13)
    message_id = struct.pack(">B", 8)
    payload = struct.pack(">III", index, begin, length)
    return length_prefix + message_id + payload

def send_handshake(sock, info_hash, peer_id):
    # Gửi handshake
    sock.send(create_handshake_message(info_hash, peer_id))

    # Nhận phản hồi handshake
    response = sock.recv(128)
    print("Received handshake response!")
    # print("Received handshake response:", response)
    handshake_response = response[0:68]
    bitfield_length = struct.unpack(">I", response[68:72])[0]
    bitfield_response = response[68:73+bitfield_length]
    
    return (parse.parse_handshake_response(handshake_response),
            parse.parse_bitfield(bitfield_response))


def send_interested(sock):
    interested_msg = create_interested_message()
    sock.send(interested_msg)
    return sock

def request_piece(sock, index, begin, length):
    request_msg = create_request_message(index, begin, length)  # Độ dài 13 byte, message ID 6
    sock.send(request_msg)
    return sock

def send_unchoke(sock):
    unchoke_msg = create_unchoke_message()
    sock.send(unchoke_msg)
    return sock

def send_bitfield(sock, bitfield):
    bitfield_msg = create_bitfield_message(bitfield)
    sock.send(bitfield_msg)
    return sock

def send_handshake_and_bitfield(sock, info_hash, peer_id, bitfield):
    handshake_msg = create_handshake_message(info_hash, peer_id)
    bitfield_msg = create_bitfield_message(bitfield)
    
    sock.sendall(handshake_msg + bitfield_msg)
    return sock