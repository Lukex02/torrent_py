import hashlib
import requests
import socket
import struct
import random
import urllib.parse
import threading
import time
import os

import bencode
import makeTorrent
import peer
import message
import piece
import seed

OUTPUT_FILE = 'output.temp'         # Tên tệp đầu ra sau khi tải xong
BLOCK_SIZE = 16 * 1024  # 16KB      # Kích cỡ 1 block
local_port = random.randint(49123, 60999)

# Decode file đã download 
def rename_download(new_file_name):
    if not os.path.exists("./download"): 
        os.makedirs("./download") 
    new_file_path = os.path.join("./download", new_file_name)
    os.rename(new_file_name + ".temp", new_file_path)

# Decode file và folder đã download   
def rename_download_folder(new_file_list, file_length_list):
    with open(new_file_list[0] + ".temp", 'rb') as f:
        output_raw = f.read()
    root_path = "./download/" + new_file_list[0]
    os.makedirs(root_path)
    
    path = root_path
    index = 0
    offset = 0
    for dir in new_file_list[1:]:
        path += "/" + dir
        if '.' not in os.path.basename(dir):
            print(f"Folder path: {path}")
            if not os.path.exists(path): 
                os.makedirs(path)
        else:
            with open(path, 'wb') as f:
                f.truncate(file_length_list[index])
            with open(path, 'wb') as f:
                f.seek(0)  # Định vị trí ghi
                f.write(output_raw[offset: offset + file_length_list[index]])  # Ghi mảnh vào tệp
                print(f"Done writing file index: {index} - offset: {offset} - length: {file_length_list[index]} (bytes) at path: {path}")
                offset += file_length_list[index]
                path = root_path
                index += 1

# Kết hợp file để share folder
def combine_files(file_list):
    root_path = "./seeds/" + file_list[0]
    path = root_path
    data = b''
    for dir in file_list[1:]:
        path += "/" + dir
        if '.' not in os.path.basename(dir):
            print(f"Folder path: {path}")
            if not os.path.exists(path): 
                os.makedirs(path)
        else:
            print(f"Decode binary file {dir}...")
            with open(path, 'rb') as f:
                data += f.read()
            path = root_path
    return data

class TorrentClient:
    def __init__(self, torrent_file):
        self.stop_flag = threading.Event()
        self.lock = threading.Lock()  # Khóa đồng bộ
        self.downloaded = 0
        self.downloaded_piece = []
        self.downloading_piece = []
        self.number_of_threads = 0
        self.download_threads = []
        self.upload_threads = []
        self.torrent_path = torrent_file
        self.torrent_data = self.load_torrent_file(torrent_file)
        self.info_hash = self.calculate_info_hash()
        self.tracker_url = self.torrent_data[b'announce'].decode()
        self.name = self.calculate_name()
        self.peer_id = self.generate_peer_id()
        self.piece_length = self.calculate_piece_size()
        self.pieces = self.calculate_pieces()
        self.num_pieces = piece.get_num_pieces(self.torrent_data[b'info'])
        self.length_list = []
        self.file_length = self.calculate_file_size()
    
    def load_torrent_file(self, torrent_file):
        with open(torrent_file, 'rb') as f:
            return bencode.ben_decode(f.read())

    def calculate_info_hash(self):
        info = bencode.ben_encode(self.torrent_data[b'info'])
        return hashlib.sha1(info).digest()

    def calculate_file_size(self):
        info = self.torrent_data[b'info']
        if b'files' in info:
            total_file_size = 0
            for file in info[b'files']:
                self.length_list.append(file[b'length'])
                total_file_size += file[b'length']
            return total_file_size 
        else:
            return info[b'length']
    
    def calculate_name(self):
        # Đối với file trong folder list sẽ là [b'dir1', b'dir2', b'file'] (dir1/dir2/file)
        info = self.torrent_data[b'info']
        if b'files' in info:
            folder_name = self.torrent_data[b'info'][b'name'].decode('utf-8')
            name_list = [folder_name]
            for file in info[b'files']:
                for dir in file[b'path']:
                    name_list.append(dir.decode('utf-8'))
            return name_list
        else:
            return self.torrent_data[b'info'][b'name'].decode('utf-8')
    
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

    def connect_to_tracker(self, event, ip, port, uploaded, downloaded, left):
        params = {
            'info_hash': self.info_hash,
            'peer_id': self.peer_id,
            'port': port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': left,
            'compact': 1,
            'event': event,
            'ip': ip
        }
        url = f"{self.tracker_url}?{urllib.parse.urlencode(params)}"
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to connect to tracker")
            return None
        return bencode.ben_decode(response.content)
    
    def get_peers(self, tracker_response):
        peers = tracker_response[b'peers']
        peers = [peers[i:i+6] for i in range(0, len(peers), 6)]
        return [(socket.inet_ntoa(peer[:4]), struct.unpack('!H', peer[4:])[0]) for peer in peers]

    def download(self):
        # Lấy tên máy chủ
        hostname = socket.gethostname()
        # Lấy địa chỉ IP của máy chủ
        local_ip = socket.gethostbyname(hostname)
        
        tracker_response = self.connect_to_tracker('started', local_ip, local_port, 0, 0, self.file_length)
        if tracker_response is None:
            raise Exception("Tracker didn't response")
        
        peers = self.get_peers(tracker_response)
        print(f"({self.name}) Found {len(peers)} peers from tracker.")
        if len(peers) == 0:          
            print("No peers available")
            return
        
        if isinstance(self.name, list):
            # Lấy tên folder gốc để làm tên file tạm
            output = self.name[0] + ".temp"
        else:
            # Lấy tên file gốc để làm tên file tạm
            output = self.name + ".temp"
        with open(output, 'wb') as f:
            f.truncate(self.file_length)  # Dành dung lượng cho tệp đầu ra

        # Connect to peer
        for ip, port in peers:
            print(f"Connecting to peer {ip}:{port}...")
            # Kết nối với peer thử, nếu không thành công thì sẽ không tạo thread
            sock = peer.connect_to_peer(ip, port)
            
            if sock is not None:
                # Phân tích peer để tạo số lượng thread
                downloader_thread = threading.Thread(target=self.download_from_peer, args=(sock, ip, port, output))
                downloader_thread.start()
                self.download_threads.append(downloader_thread)
            
        for thread in self.download_threads:
            thread.join()

        self.connect_to_tracker('completed', local_ip, port, 0, self.downloaded, 0)
        self.connect_to_tracker('stopped', local_ip, local_port, 0, self.downloaded, 0)

        if isinstance(self.name, list):
            rename_download_folder(self.name, self.length_list)
        else:
            rename_download(self.name)
            
    def download_from_peer(self, sock, client_ip, client_port, output):
        _, bitfield_response = message.send_handshake(sock, self.info_hash, self.peer_id)
        
        print(f'Client {client_ip}:{client_port} has {bitfield_response["pieces"]}')
        
        # Send Interested message
        sock = message.send_interested(sock)

        # Wait for Unchoke
        peer.wait_for_unchoke(sock)
        time.sleep(1)

        for piece_index in range(len(bitfield_response["pieces"])):
            with self.lock:
                # Đảm bảo không request piece đã download hay đang download
                if bitfield_response["pieces"][piece_index] in self.downloaded_piece or bitfield_response["pieces"][piece_index] in self.downloading_piece:
                    continue
                self.downloading_piece.append(bitfield_response["pieces"][piece_index])
                print(f'Added piece {bitfield_response["pieces"][piece_index]} to queue...')
            remain_data = self.file_length - self.downloaded
            
            print(f"Downloaded: {self.downloaded}, remaining: {remain_data}(bytes)")
            
            # Nếu như piece là piece cuối cùng
            if piece_index == len(bitfield_response["pieces"]) - 1:
                print("Asking for the remaining piece...")
                # Vì request luôn luôn là 1 piece giống nhau trừ piece cuối luôn nhỏ hơn
                requested_piece_size = self.file_length % self.piece_length 
            else:
                print(f"Asking for 1 piece from {client_ip}:{client_port}...")
                requested_piece_size = self.piece_length
            # Bắt đầu vào quá trình gửi request cho piece số <piece_index>
            print("Sending request piece:", piece_index)
            
            # Request piece theo từng block BLOCK_SIZE (16KB)
            piece_data = b''
            piece_offset = 0
            while len(piece_data) < requested_piece_size:
                request_block = BLOCK_SIZE
                remaining_data = requested_piece_size - len(piece_data)
                if remaining_data < BLOCK_SIZE:
                    request_block = remaining_data
                print(f"Sending {request_block} Bytes block request for piece {piece_index}...")
                message.request_piece(sock, piece_index, piece_offset, request_block)
            
                # Tính toán phần data còn lại để tìm kích thước block cuối cùng
                recv_block_length, recv_piece_offset, block = piece.wait_for_pieces(sock, request_block)
                piece_data += block
                piece_offset = recv_piece_offset + recv_block_length
                print(f"Got block offset: {recv_piece_offset}, length: {recv_block_length} for piece {piece_index}")
                print("-----------------o0o-----------------")

            print(f"Downloaded piece {piece_index} from {client_ip}:{client_port}")
            print("-----------------o0o-----------------")
            
            with self.lock:
                self.downloaded += requested_piece_size
                self.downloading_piece.remove(bitfield_response["pieces"][piece_index])
                self.downloaded_piece.append(bitfield_response["pieces"][piece_index])
            
            print("-----------------o0o-----------------")
            # Xác minh mảnh và ghi vào tệp nếu hợp lệ
            if piece.verify_piece(piece_data, self.pieces[piece_index]):
                print(f"Piece {piece_index} is verified!")
                piece.write_piece_to_file(output, piece_index, piece_data, self.piece_length)
                print(f"Write to temporary file completed!")
            else:
                raise Exception(f"Piece {piece_index} failed hash check. Please redownload")
            print("-----------------o0o-----------------")
        
        sock.close()
    
    def start_seeding_server(self, port, input_file_path):
        # Lấy tên máy (hostname) của máy tính hiện tại
        hostname = socket.gethostname()
        # Lấy địa chỉ IP của máy tính
        ip_address = socket.gethostbyname(hostname)
        self.connect_to_tracker('started', ip_address, port, 0, 0, 0)
        self.connect_to_tracker('completed', ip_address, port, 0, self.file_length, 0)
        
        # Tạo socket server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        server_socket.bind(("", port))
        server_socket.listen(5)  # Lắng nghe tối đa 5 kết nối
        
        print(f"Seeding server is listening on : {ip_address}:{port}...")
        try:
            while not self.stop_flag.is_set():
                server_socket.settimeout(1) # Kiểm tra stop_flag mỗi giây
                try:
                    # Chấp nhận kết nối từ peer
                    peer_socket, peer_address = server_socket.accept()
                    print(f"Peer has connected from: {peer_address}")
                    uploader_thread = threading.Thread(target=self.share_with_peer, args=(peer_socket, input_file_path))
                    uploader_thread.start()
                    self.upload_threads.append(uploader_thread)
                except socket.timeout:
                    continue
        finally:
            print("-----------------o0o-----------------")
            print("Stopping server...")
            for thread in self.upload_threads:
                thread.join()  # Wait for all threads to finish
                
            self.connect_to_tracker('stopped', ip_address, port, self.file_length, 0, 0)
            server_socket.close()
            print("Server stopped")

    def upload(self, input_file_path):
        server_thread = threading.Thread(target=self.start_seeding_server, args=(local_port, input_file_path))
        server_thread.start()
        
        try:
            input("Press Enter to stop the server...\n")
        except KeyboardInterrupt:
            print("KeyboardInterrupt received, shutting down.")

        self.stop_flag.set()
        server_thread.join()
        
    def share_with_peer(self, socket, input_file_path):
        # Tạo bitfield từ file có sẵn (Vì là seed nên coi như có tất cả mọi mảnh)
        if os.path.isdir(input_file_path):
            input_file_data = combine_files(self.name)
        else:    
            with open(input_file_path, "rb") as file:
                input_file_data = file.read()
        
        bitfield_data = seed.generate_bitfield(input_file_data, self.piece_length, self.num_pieces)
        
        print("-----------------o0o-----------------")
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
            if (piece_index, offset, length) == (None, None, None):
                print("Peer has disconnected...")
                break
            else:
                # Gửi từng piece dựa trên request
                piece_begin = piece_index * self.piece_length + offset
                piece_end = piece_begin + length
                seed.send_piece(socket, piece_index, offset, input_file_data[piece_begin:piece_end])
                print("-----------------o0o-----------------")
    
        return  # Ngừng seed với peer đang kết nối

    def force_stopped_all(self):
        # Lấy tên máy chủ
        hostname = socket.gethostname()
        # Lấy địa chỉ IP của máy chủ
        local_ip = socket.gethostbyname(hostname)
        
        tracker_response = self.connect_to_tracker('started', local_ip, local_port, 0, 0, self.file_length)
        if tracker_response is None:
            raise Exception("Tracker didn't response")
        # print(tracker_response)
        
        peers = self.get_peers(tracker_response)
        print(f"Found {len(peers)} peers from tracker.")
        
        # Connect to peer
        for ip, port in peers:
            print(f"Sent 'stopped' for peer {ip}:{port}...")
            self.connect_to_tracker('stopped', ip, port, 0, 0, 0)

if __name__ == '__main__':
    # Create mandatory directory
    if not os.path.exists("./torrent"): 
        os.makedirs("./torrent")
    if not os.path.exists("./seeds"): 
        os.makedirs("./seeds")
    if not os.path.exists("./download"): 
        os.makedirs("./download")
    while True:
        usr_inp = input('Enter your command ("help" to see all commands):')
        if usr_inp.lower() == "exit":
            break
        arguments = usr_inp.split()
        
        # python main.py download <torrent_path>
        if arguments[0] == "download":
            if len(arguments) < 2:
                print("Wrong argument...")
                continue
            client_active = []
            client_active_download_thread = []
            for input_torrent_index in range(len(arguments[1:])):
                torrent_name = arguments[input_torrent_index+1]
                torrent_file = os.path.join("./torrent", torrent_name)
                client_active.append(TorrentClient(torrent_file))
                client_download_thread = threading.Thread(target=client_active[input_torrent_index].download, args=())
                client_active_download_thread.append(client_download_thread)
                client_download_thread.start()
            
            for thread in client_active_download_thread:
                thread.join()
            
            print("---------///////---------")
            print("------Closed Download!")
            print("---------///////---------")

        # python main.py upload <torrent_path> <input_file_name in /seeds>
        elif arguments[0] == "upload":
            if len(arguments) != 2:
                print("Wrong argument...")
                continue
            
            torrent_file = arguments[1]
            torrent_path = os.path.join("./torrent", torrent_file)
            client = TorrentClient(torrent_path)
            input_file = client.name

            if isinstance(input_file, list):
                input_file_path = os.path.join("./seeds", input_file[0])
            else:
                input_file_path = os.path.join("./seeds", input_file)

            client.upload(input_file_path)
            print("---------///////---------")
            print("------Closed Upload!")
            print("---------///////---------")

        # python main.py maketor <input_path> <torrent_name>
        elif arguments[0] == "maketor":
            if len(arguments) < 3:
                print("Missing argumnent for maketor")
                continue
            input_name = arguments[1]
            input_path = os.path.join("./seeds", input_name)
            torrent_name = arguments[2]
            tracker_url = "http://192.168.31.130:8080/announce"
            # tracker_url = "http://10.128.28.179:8080/announce"

            torrent_path = os.path.join("./torrent", torrent_name)

            if '.' in input_name:
                makeTorrent.create_torrent_single(input_path, tracker_url, torrent_path)
            else:
                makeTorrent.create_torrent_multi(input_path, tracker_url, torrent_path)
            
            print("---------///////---------")
            print("------Make torrent completed!")
            print("---------///////---------")

        # python main.py help
        elif arguments[0] == "help":
            if len(arguments) != 1:
                print("Wrong argument...")
                continue
            print("Available commands:")
            print("Download: download <torrent_name stored in /torrent>.torrent")
            print("Upload: upload <torrent_name stored in /torrent>.torrent <input_file_name stored in /seeds>")
            print("Make torrent: maketor <input_file stored in /seeds> <torrent_name> <optional|tracker_url>")
        elif arguments[0] == "stop_all":
            if len(arguments) != 2:
                print("Wrong argument...")
                continue
            torrent_name = arguments[1]
            torrent_file = os.path.join("./torrent", torrent_name)
            client = TorrentClient(torrent_file)
            client.force_stopped_all()
            