import hashlib
import os
import bencode

def get_piece_length(file_size):
    # Nếu file lớn hơn 5 MB thì chọn piece length là 512 KB
    if file_size > 5 * 1024 * 1024:
        piece_length = 512 * 1024           #512 KB
    # Nếu từ 1 - 5 MB thì piece length chọn 128 KB
    elif file_size > 1024 * 1024:
        piece_length = 256 * 1024           #256 KB
    # Nhỏ hơn 1 MB lớn hơn 256 KB chọn 128 KB
    elif file_size > 256 * 1024:
        piece_length = 128 * 1024           #128 KB
    # Nhỏ hơn 256 KB thì chọn 64 KB
    else:
        piece_length = 64 * 1024            #64 KB
    return piece_length

def generate_pieces(file_path, piece_length):
    pieces = []
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(piece_length)
            if not chunk:
                break
            pieces.append(hashlib.sha1(chunk).digest())
    return b"".join(pieces)

def create_torrent_single(input_path, tracker_url, output_file):
    file_name = os.path.basename(input_path)
    file_size = os.path.getsize(input_path)
    piece_length = get_piece_length(file_size)
    
    # Tính toán các mảnh (pieces)
    pieces = generate_pieces(input_path, piece_length)
    
    torrent = {
        "announce": tracker_url,
        "info": {
            "name": file_name,
            "piece length": piece_length,
            "length": file_size,
            "pieces": pieces,
        }
    }
    
    torrent_data = bencode.ben_encode(torrent)
    if output_file[len(output_file)-8:] != ".torrent":
        with open(f"{output_file}.torrent", "wb") as f:
            f.write(torrent_data)
    else:
        with open(f"{output_file}", "wb") as f:
            f.write(torrent_data)

    print(f"Torrent file created at: {output_file}")

def hash_pieces_folder(file_paths, piece_length):
    total_chunk = b""
    pieces = b""
    # Tổng hợp tất cả dữ liệu theo byte lại, sau đó chia theo hash 20 byte
    for file_path in file_paths:
        with open(file_path, "rb") as f:
            while chunk := f.read(piece_length):
                total_chunk += chunk

    # Kết hợp pieces lại theo kích thước hash 20 bytes
    for i in range(0, len(total_chunk), piece_length):
        pieces += hashlib.sha1(total_chunk[i:i+piece_length]).digest()
    return pieces

def create_torrent_multi(folder_path, tracker_url, output_file):
    # Lấy danh sách tệp và đường dẫn tương đối
    file_paths = []
    file_info = []
    total_file_size = 0
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, folder_path)
            file_paths.append(file_path)
            file_size = os.path.getsize(file_path)
            file_info.append({
                "length": file_size,
                "path": relative_path.split(os.sep)  # Định dạng đường dẫn
            })
            total_file_size += file_size
            
    piece_length = get_piece_length(total_file_size)
    
    # Tính hash cho các phần (pieces)
    pieces = hash_pieces_folder(file_paths, piece_length)

    # Tạo metadata cho torrent
    torrent = {
        "announce": tracker_url,
        "info": {
            "name": os.path.basename(folder_path),  # Tên thư mục
            "piece length": piece_length,           # Kích thước mỗi phần
            "pieces": pieces,                       # Giá trị băm các phần
            "files": file_info                      # Danh sách tệp và kích thước
        }
    }
    
    torrent_data = bencode.ben_encode(torrent)
    if output_file[len(output_file)-8:] != ".torrent":
        with open(f"{output_file}.torrent", "wb") as f:
            f.write(torrent_data)
    else:
        with open(f"{output_file}", "wb") as f:
            f.write(torrent_data)

