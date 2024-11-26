def ben_encode(data):
    if isinstance(data, int):
        return f"i{data}e".encode()
    elif isinstance(data, bytes):
        return f"{len(data)}:".encode() + data
    elif isinstance(data, str):
        return f"{len(data.encode('utf-8'))}:".encode() + data.encode()
    elif isinstance(data, list):
        return b"l" + b"".join(ben_encode(item) for item in data) + b"e"
    elif isinstance(data, dict):
        items = sorted(data.items())  # Các khóa phải được sắp xếp
        return b"d" + b"".join(ben_encode(k) + ben_encode(v) for k, v in items) + b"e"
    else:
        raise TypeError("Unsupported data type for bencoding")
    
def ben_decode(data):
    # Giải mã số nguyên
    def decode_int(index):
        end = data.index(b'e', index)
        value = int(data[index + 1:end])
        return value, end + 1

    # Giải mã string
    def decode_str(index):
        colon = data.index(b':', index)
        length = int(data[index:colon])
        start = colon + 1
        end = start + length
        value = data[start:end]
        return value, end

    # Giải mã list
    def decode_list(index):
        result = []
        index += 1  # Bỏ qua 'l'
        while data[index] != ord(b'e'):
            value, index = decode(index)
            result.append(value)
        return result, index + 1

    # Giải mã dictionary
    def decode_dict(index):
        result = {}
        index += 1  # Bỏ qua 'd'
        while data[index] != ord(b'e'):
            key, index = decode_str(index)
            value, index = decode(index)
            result[key] = value
        return result, index + 1

    def decode(index):
        if data[index] == ord(b'i'):  
            return decode_int(index)
        elif data[index] == ord(b'l'):
            return decode_list(index)
        elif data[index] == ord(b'd'):
            return decode_dict(index)
        elif str(data[index]).isdigit():
            return decode_str(index)
        else:
            raise ValueError(f"Invalid bencode format at index {index}")

    # Bắt đầu giải mã từ vị trí 0
    # Số sau là index
    result, _ = decode(0)
    return result

