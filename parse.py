import struct
import urllib.parse

def parse_handshake_response(response):
    # Protocal name (1 byte)
    protocol_name_length = response[0]
    
    # Protocol name length (protocol_name_length bytes)
    protocol_name = response[1:1 + protocol_name_length].decode("utf-8")
    
    # Reserved bytes (8 bytes)
    reserved_bytes = response[1 + protocol_name_length:1 + protocol_name_length + 8]
    
    # Info hash (20 bytes)
    info_hash = response[1 + protocol_name_length + 8:1 + protocol_name_length + 8 + 20]
    
    # Peer ID nằm (20 bytes)
    peer_id = response[1 + protocol_name_length + 8 + 20:1 + protocol_name_length + 8 + 20 + 20]

    return {
        "protocol_name": protocol_name,
        "reserved_bytes": reserved_bytes,
        "info_hash": info_hash,
        "peer_id": peer_id,
    }

def parse_bitfield(message):
    length_prefix = struct.unpack(">I", message[:4])[0]
    message_id = message[4]
    bitfield_data = message[5:5+length_prefix-1]

    bitfield_bits = ''.join(f'{byte:08b}' for byte in bitfield_data)

    pieces = [index for index, bit in enumerate(bitfield_bits) if bit == '1']

    print("Pieces have:", pieces)

    if message_id != 5:
        raise ValueError("Message ID is not bitfield")
    return {
        "length_prefix": length_prefix,
        "message_id": message_id,
        "bitfield_data": bitfield_data,
        "pieces": pieces
    }

def parse_unchoke(message):
    length_prefix = struct.unpack(">I", message[:4])[0]
    message_id = message[4]
    if message_id != 1:
        raise ValueError("Message ID is not unchoke")
    return {
        "length_prefix": length_prefix,
        "message_id": message_id,
        "type": "unchoke"
    }

def parse_piece(length, data):
    recv_piece_length = length - 9
    piece_index = data[0:4]
    piece_begin_offset = struct.unpack(">I",data[4:8])[0]
    piece_data = data[8:8+length]

    return recv_piece_length, piece_begin_offset, piece_data

def parse_magnet(magnet_link):
    # Phân tích URL
    parsed_url = urllib.parse.urlparse(magnet_link)
    
    # Lấy các tham số từ query
    params = urllib.parse.parse_qs(parsed_url.query)
    
    # Extract info_hash, name, và tracker
    info_hash = params['xt'][0].split(':')[2]  # info_hash
    name = params.get('dn', [None])[0]  # tên file (nếu có)
    trackers = params.get('tr', [])  # danh sách tracker (nếu có)

    return info_hash, name, trackers
