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

import handshake
import peer
import message
import piece

OUTPUT_FILE = 'output_temp'         # Tên tệp đầu ra sau khi tải xong
BLOCK_SIZE = 16 * 1024  # 16KB      # Kích cỡ 1 block

def rename_download(new_file_name):
    new_file_path = os.path.join("./download", new_file_name)
    os.rename(OUTPUT_FILE, new_file_path)

class TorrentClient:
    def __init__(self, torrent_file):
        self.torrent_path = torrent_file
        self.torrent_data = self.load_torrent_file(torrent_file)
        self.info_hash = self.calculate_info_hash()
        self.peer_id = self.generate_peer_id()
        self.tracker_url = self.torrent_data[b'announce'].decode()
        self.file_length = self.calculate_file_size()
        self.piece_length = self.calculate_piece_size()
        self.pieces = self.calculate_pieces()
        self.num_pieces = piece.get_num_pieces(self.torrent_data[b'info'])
    
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
        return b'-PC0001-' + ''.join([str(random.randint(0, 9)) for _ in range(12)]).encode()

    def connect_to_tracker(self):
        params = {
            'info_hash': self.info_hash,
            'peer_id': self.peer_id,
            'port': 6881,
            'uploaded': 0,
            'downloaded': 0,
            'left': self.torrent_data[b'info'][b'length'],
            # 'compact': 1,
            'event': 'started'
        }
        url = f"{self.tracker_url}?{urllib.parse.urlencode(params)}"
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to connect to tracker")
            return None

        return bencodepy.decode(response.content)
    
    def get_peers(self, tracker_response):
        peers = tracker_response[b'peers']
        peers = [peers[i:i+6] for i in range(0, len(peers), 6)]
        return [(socket.inet_ntoa(peer[:4]), struct.unpack('!H', peer[4:])[0]) for peer in peers]

    def download(self):
        tracker_response = self.connect_to_tracker()
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
        defPort = 48756
        print(f"Connect Hard.......")

        sock = peer.connect_to_peer(defIp, defPort)

        _, bitfield_response, unchoke_response = handshake.handshake(sock, self.info_hash, self.peer_id)

        # if unchoke_response is None:
        # Send Interested message
        sock = message.send_interested(sock)

        # Wait for Unchoke
        peer.wait_for_unchoke(sock)

        with open(OUTPUT_FILE, 'wb') as f:
            f.truncate(self.file_length)  # Dành dung lượng cho tệp đầu ra

        downloaded = 0
        # piece_data = b''
        for piece_index in range(len(bitfield_response["pieces"])):
            # piece_data = bytearray(self.file_length)
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
            # piece_data[downloaded + recv_piece_begin_offset:downloaded + recv_piece_begin_offset + recv_piece_length] = block
            # print("Hash block:", hashlib.sha1(block).digest())
            # piece_data += block
            downloaded += requested_size
            # print("Done get piece (in hex):", piece_data.hex())
            
            # Xác minh mảnh và ghi vào tệp nếu hợp lệ
            if piece.verify_piece(block, self.pieces[piece_index]):
                print("Piece verified...")
                piece.write_piece_to_file(OUTPUT_FILE, piece_index, block, self.piece_length)
                print(f"Write to temporary file completed!")
            else:
                print(f"Piece {piece_index} failed hash check. Please redownload")

        sock.close()
        rename_download(self.torrent_data[b'info'][b'name'].decode('utf-8'))
        print("Download completed!")

if __name__ == '__main__':
    client = TorrentClient("sample_2.torrent")
    # client = TorrentClient(sys.argv[1])
    client.download()
    print("Closing download...\n")
