import http.server
import socketserver
import urllib.parse as urlparse
import bencodepy

# Lưu thông tin các peer
swarm = {}

class TorrentTrackerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse URL và truy vấn
        parsed_url = urlparse.urlparse(self.path)
        query_params = urlparse.parse_qs(parsed_url.query)

        # Xác định endpoint
        if parsed_url.path == '/announce':
            self.handle_announce(query_params)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
    
    def handle_announce(self, query_params):
        # Lấy thông tin từ truy vấn
        info_hash = query_params.get('info_hash', [None])[0]
        peer_id = query_params.get('peer_id', [None])[0]
        port = query_params.get('port', [None])[0]
        event = query_params.get('event', [None])[0]
        ip = query_params.get('ip', [None])[0]          # Dùng để lấy IP parse từ bên gửi nếu có

        if not info_hash or not peer_id or not port:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing parameters")
            return

        # Lấy địa chỉ IP của peer từ địa chỉ chính peer gửi nếu như ip ở trên không được gửi kèm
        if ip is None:
            ip = self.client_address[0]

        # Thêm peer vào swarm
        if info_hash not in swarm:
            swarm[info_hash] = []

        peer_info = {'peer_id': peer_id, 'ip': ip, 'port': int(port)}
        if peer_info not in swarm[info_hash]:
            if event == "started":
                swarm[info_hash].append(peer_info)
            elif event == "completed":
                swarm[info_hash].remove(peer_info)
            elif event == "stopped":
                swarm[info_hash].remove(peer_info)

        # Tạo danh sách peer
        peer_list = b''
        for peer in swarm[info_hash]:
            peer_ip = socketserver.socket.inet_aton(peer['ip'])
            peer_port = int(peer['port']).to_bytes(2, 'big')        # Port dưới dạng 2 byte
            peer_list += peer_ip + peer_port
        
        # Phản hồi theo định dạng bencode
        response = {
            b'interval': 1800,      # Thời gian cho peer gửi lại yêu cầu (30 phút)
            b'peers': peer_list     # Danh sách peer
        }
        
        peer_info = {'peer_id': peer_id, 'ip': ip, 'port': port}
        if peer_info not in swarm[info_hash]:
            swarm[info_hash].append(peer_info)

        # Trả danh sách các peer trong swarm (theo định dạng bencode)
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')  # Bencode là văn bản thuần
        self.end_headers()
        self.wfile.write(bencodepy.encode(response))

# Chạy server trên port 8080
def run_tracker():
    PORT = 8080
    with socketserver.TCPServer(("10.128.28.179", PORT), TorrentTrackerHandler) as httpd:
        print(f"Tracker is running at http://10.128.28.179:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_tracker()
