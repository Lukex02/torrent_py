import struct
import parse

def handshake(sock, info_hash, peer_id):
    # Tạo message handshake
    pstr = b"BitTorrent protocol"
    pstrlen = len(pstr)
    reserved = b'\x00' * 8  # 8 byte reserved
    handshake_message = struct.pack('B', pstrlen) + pstr + reserved + info_hash + peer_id

    # Gửi handshake
    sock.send(handshake_message)

    # Nhận phản hồi handshake
    response = sock.recv(100)
    print("Received handshake response!")
    # print("Received handshake response:", response)
    
    # print(response[0:68])
    # print(response[68:74])
    # print(response[74:79])
    # print(parse.parse_handshake_response(response[0:68]))
    # print(parse.parse_bitfield(response[68:74]))
    # print(parse.parse_unchoke(response[74:79]))
    return (parse.parse_handshake_response(response[0:68]),
            parse.parse_bitfield(response[68:74]),
            parse.parse_unchoke(response[74:79]))

