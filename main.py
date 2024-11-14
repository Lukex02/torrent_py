import bencodepy
import hashlib
import requests
import socket
import struct
import random
import urllib.parse
import sys
import time
import os

import makeTorrent
import peer
import message
import piece
import seed

OUTPUT_FILE = 'output_temp'         # Tên tệp đầu ra sau khi tải xong
BLOCK_SIZE = 16 * 1024  # 16KB      # Kích cỡ 1 block

def rename_download(new_file_name):
    if not os.path.exists("./download"): 
        os.makedirs("./download") 
    new_file_path = os.path.join("./download", new_file_name)
    os.rename(OUTPUT_FILE, new_file_path)

class TorrentClient:
    def __init__(self, torrent_file):
        self.torrent_path = torrent_file
        self.torrent_data = self.load_torrent_file(torrent_file)
        self.info_hash = self.calculate_info_hash()
        self.tracker_url = self.torrent_data[b'announce'].decode()
        self.name = self.torrent_data[b'info'][b'name'].decode('utf-8')
        self.file_length = self.calculate_file_size()
        self.piece_length = self.calculate_piece_size()
        self.pieces = self.calculate_pieces()
        self.num_pieces = piece.get_num_pieces(self.torrent_data[b'info'])
        self.peer_id = self.generate_peer_id()
    
    def load_torrent_file(self, torrent_file):
        with open(torrent_file, 'rb') as f:
            return bencodepy.decode(f.read())

    def calculate_info_hash(self):
        info = bencodepy.encode(self.torrent_data[b'info'])
        return hashlib.sha1(info).digest()

    def calculate_file_size(self):
        info = self.torrent_data[b'info']
        return info[b'length']
    
    def calculate_piece_size(self):
        info = self.torrent_data[b'info']
        return info[b'piece length']
    
    def calculate_pieces(self):
        info = self.torrent_data[b'info']
        pieces_hash_data = info[b'pieces']
        hash_size = 20

        pieces_hash_list = [pieces_hash_data[i:i+hash_size] for i in range(0, len(pieces_hash_data), hash_size)]
        return pieces_hash_list
    
    def generate_peer_id(self):
        return b'-tP1001-' + ''.join([str(random.randint(0, 9)) for _ in range(12)]).encode()

    def connect_to_tracker(self, event, uploaded, downloaded, left):
        params = {
            'info_hash': self.info_hash,
            'peer_id': self.peer_id,
            'port': 6881,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': left,
            'compact': 1,
            'event': event
        }
        url = f"{self.tracker_url}?{urllib.parse.urlencode(params)}"
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to connect to tracker")
            return None
        # print(bencodepy.decode(response.content))
        return bencodepy.decode(response.content)
    
    def get_peers(self, tracker_response):
        peers = tracker_response[b'peers']
        peers = [peers[i:i+6] for i in range(0, len(peers), 6)]
        return [(socket.inet_ntoa(peer[:4]), struct.unpack('!H', peer[4:])[0]) for peer in peers]

    def download(self):
        tracker_response = self.connect_to_tracker('started', 0, 0, self.file_length)
        if tracker_response is None:
            return
        
        # print(tracker_response)
        peers = self.get_peers(tracker_response)
        print(f"Found {len(peers)} peers from tracker.")

        # Connect to peer
        for ip, port in peers:
            print(f"Connecting to peer {ip}:{port}...")
        
            # What it should be, but...
            # peer.connect_to_peer(ip, port)
        # It is what it is, fuck the tracker's response peer
        defIp = "192.168.31.74"
        # defPort = 48756
        defPort = 53049
        # defIp = "0.0.0.0"
        # defPort = 49053
        print(f"Connect Hard.......")

        sock = peer.connect_to_peer(defIp, defPort)

        _, bitfield_response = message.send_handshake(sock, self.info_hash, self.peer_id)

        # if unchoke_response is None:
        # Send Interested message
        sock = message.send_interested(sock)

        # Wait for Unchoke
        peer.wait_for_unchoke(sock)
        time.sleep(1)

        with open(OUTPUT_FILE, 'wb') as f:
            f.truncate(self.file_length)  # Dành dung lượng cho tệp đầu ra

        downloaded = 0
        # piece_data = b''
        for piece_index in range(len(bitfield_response["pieces"])):
            # piece_data = bytearray(self.file_length)
            # for begin in (0, self.piece_length, BLOCK_SIZE)
            remain_piece = self.file_length - downloaded
            
            print("Downloaded:", downloaded)
            print("Remain:", remain_piece)
            if remain_piece < self.piece_length:
                print("Ask for remaining...")
                requested_size = remain_piece
            else:
                print("Ask for 16KB piece...")
                requested_size = self.piece_length
            
            message.request_piece(sock, piece_index, 0, requested_size)
            print("Sent request piece:", piece_index)
            time.sleep(1)

            recv_piece_length, recv_piece_begin_offset, block = piece.wait_for_pieces(sock, requested_size)
            
            print("Write from", downloaded + recv_piece_begin_offset, "to", downloaded + recv_piece_begin_offset + recv_piece_length)
            downloaded += requested_size
            # print("Done get piece (in hex):", block.hex())
            
            # Xác minh mảnh và ghi vào tệp nếu hợp lệ
            if piece.verify_piece(block, self.pieces[piece_index]):
                print("Piece verified...")
                piece.write_piece_to_file(OUTPUT_FILE, piece_index, block, self.piece_length)
                print(f"Write to temporary file completed!")
            else:
                raise Exception(f"Piece {piece_index} failed hash check. Please redownload")

        self.connect_to_tracker('completed', 0, downloaded, 0)
        sock.close()
        rename_download(self.name)
    
    def start_seeding_server(self, port=49053):
        # Tạo socket server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        server_socket.bind(("", port))
        server_socket.listen(5)  # Lắng nghe tối đa 5 kết nối
        
        print(f"Seeding server is listening on port: {port}...")

        while True:
            # Chấp nhận kết nối từ peer
            peer_socket, peer_address = server_socket.accept()
            print(f"Peer has connected from: {peer_address}")
            # print(peer_socket)
            return peer_socket

    def upload(self, input_file_path):
        # Tạo bitfield từ file có sẵn (Vì là seed nên coi như có tất cả mọi mảnh)
        with open(input_file_path, "rb") as file:
            input_file_data = file.read()
        bitfield_data = seed.generate_bitfield(input_file_data, self.piece_length, self.num_pieces)
        
        tracker_response = self.connect_to_tracker('started', 0, 0, 0)
        if tracker_response is None:
            return
        
        socket = self.start_seeding_server()
        if socket is None:
            raise Exception("Something failed, try again...")
        
        print("Current seeding...")
        
        # user_input = input("Type 'exit' to stop seeding...")
        # if user_input.lower() == 'exit':
        #     print("Exiting...")
        # else: 
        
        # Sau khi kết nối được với peer khác, đợi handshake
        handshake_response = seed.wait_for_handshake(socket)
        if seed.validate_handshake(handshake_response, self.info_hash):
            print("Handshake valid. Sending handshake response.")
            # Gửi về handshake + bitfield
            socket = message.send_handshake_and_bitfield(socket, self.info_hash, self.peer_id, bitfield_data)
        
        # Đợi peer gửi interested sau đó gửi unchoke để peer bắt đầu request
        socket = seed.wait_for_interested(socket)
        socket = message.send_unchoke(socket)
        
        while True:
            # Đợi request
            piece_index, offset, length = seed.wait_for_request(socket)
            if (piece_index, offset, length) is None:
                print("Peer has disconnected...")
                break
            # Gửi từng piece dựa trên request
            piece_begin = piece_index * self.piece_length + offset
            piece_end = piece_begin + length
            seed.send_piece(socket, piece_index, offset, input_file_data[piece_begin:piece_end])
    
        socket.close()
        return  # Ngừng seed

if __name__ == '__main__':
    # python main.py download <torrent_path>
    if sys.argv[1] == "download":
        # client = TorrentClient("sample_2.torrent")
        client = TorrentClient(sys.argv[2])
        client.download()
        print("Download completed!")

    # python main.py upload <torrent_path> <input_file_path>
    elif sys.argv[1] == "upload":
        torrent_path = sys.argv[2]
        input_file_path = sys.argv[3]
        client = TorrentClient(torrent_path)
        client.upload(input_file_path)
        print("Upload completed!")

    # python main.py maketor <input_path> <torrent_name> <optional|tracker_url>
    elif sys.argv[1] == "maketor":
        if len(sys.argv) < 4:
            raise Exception("Missing argumnent for maketor")
        if os.path.exists(sys.argv[2]):
            input_path = sys.argv[2]
        else:
            raise Exception("Input path is not valid!")
        torrent_name = sys.argv[3]
        tracker_url = "https://tr.zukizuki.org:443/announce"
        if len(sys.argv) > 4:
            for i in len(sys.argv) - 5:
                tracker_url[i] = sys.argv[4]

        if not os.path.exists("./torrent"): 
            os.makedirs("./torrent") 
        torrent_path = os.path.join("./torrent", torrent_name)

        makeTorrent.create_torrent(input_path, tracker_url, torrent_path)
        print("Make torrent completed!")

    # python main.py help
    elif sys.argv[1] == "help":
        print("Available commands:")
        print("Download: python main.py download <torrent_path>")
        print("Upload: python main.py upload <torrent_path>")
        print("Make torrent: python main.py maketor <input_path> <torrent_name> <optional|tracker_url>")