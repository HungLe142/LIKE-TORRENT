
import copy
import hashlib
import bencodepy 
import struct

import socket

# Testing function:
def get_piece_hashes(torrent_file_path): 
    with open(torrent_file_path, 'rb') as file: 
        torrent_data = bencodepy.decode(file.read()) 
        info = torrent_data[b'info'] 
        pieces = info[b'pieces'] 
        piece_length = info[b'piece length']
        
        # Lấy danh sách mã băm các mảnh 
        piece_hashes = [pieces[i:i+20] 
        for i in range(0, len(pieces), 20)] 
        return piece_hashes, piece_length # Sử dụng ví dụ 
 
def read_file_as_bytes(file_path):
    with open(file_path, 'rb') as file: 
        return file.read() 



# Functions for Downloading
def handle_incoming_mesage(message, client_socket, node, client_addr):
    print("Message received: ", message, " from ", client_addr) # Debugging print
    if len(message) >= 5:
        length_prefix, message_id = struct.unpack('!IB', message[:5])
        if message_id == 7: 
            print("Message is Piece message: ", message)
            #handle_piece_message(message[5:], node.torrent_statistic)
        if message_id == 6:
            print("Message is Request message: ", message)
            handle_request_mesage(message, client_socket, node)
    else: 
        print("Received message is too short: ", message)
        return False
    return 1

def handle_piece_message(piece_message, torrent_statistic): 
    # Message's form: <len=0009+X><id=7><index><begin><block>
    unpacked_data = struct.unpack('!IBII', piece_message[:13]) # Split first 13 byte into len, id, index, begin
    len, id, index, begin = unpacked_data
    block = piece_message[13:]
    torrent_statistic.add_block(index, begin, block, len-9)
    
    """
        Lúc đầu:
            form: <len=0009+X><id=7><index><begin><block> 

            I là số nguyên không dấu 4 byte (unsigned 32-bit integer).
            B là số nguyên không dấu 1 byte (unsigned 8-bit integer).
                        (4 1 4 4) -> (len id index begin) 
            struct.pack('!IBII', length_prefix, message_id, index, begin): Đóng gói các giá trị length_prefix, message_id, index, begin thành dạng nhị phân (binary).
            + block: Ghép phần dữ liệu block vào cuối thông điệp piece.

        struct.unpack('!II', piece_message[:8]): Giải nén phần đầu của thông điệp piece (8 byte đầu tiên) thành các giá trị index và begin.
        block = piece_message[8:]: Lấy toàn bộ phần còn lại của thông điệp piece bắt đầu từ byte thứ 8. Đây là phần dữ liệu block đã được ghép vào cuối thông điệp piece.

    """
def create_request_message(index, begin, block_length):
    message_id = 6 
    length_prefix = 13

    # Message's form: request: <len=0013><id=6><index><begin><length>
    message = struct.pack('!IBIII', length_prefix, message_id, index, begin, block_length)
    return message

def handle_request_mesage(request_message, client_socket, node):
    # Message's form: request: <len=0013><id=6><index><begin><length>
    unpacked_data = struct.unpack('!IBIII', request_message)
    _, id, index, begin, length = unpacked_data
    block = node.torrent_statistic.extract_block(index, begin, length)
    #print("Extracted block: ", block)
    piece_msg = create_piece_message(index, begin, block)

    # For debuging
    unpacked_data = struct.unpack('!IBII', piece_msg[:13])
    len, id, index, begin = unpacked_data
    print(id, index, begin, length)

    #print("Send piece message: ", piece_msg)
    client_socket.send(piece_msg)




# Function for dowloading ultimate file into local
def verify_piece(piece, piece_index, piece_hashes): # Get a {piece, index} from piece message -> hash it -> compare with piece[index] from MetaInfo file
    # Tính toán SHA1 hash của mảnh 
    sha1_hash = hashlib.sha1(piece).digest() 
    # So sánh với hash từ file .torrent 
    return sha1_hash == piece_hashes[piece_index] 

def map_pieces_to_file(pieces, piece_length, file_path, piece_hashes): 
    try: 
        # Cố gắng mở tệp trong chế độ đọc ghi 
        with open(file_path, 'r+b') as f: 
            pass 
    except FileNotFoundError: 
        # Nếu tệp không tồn tại, tạo tệp mới 
        with open(file_path, 'wb') as f: 
            pass 
        
    # Tiếp tục với việc ghi các mảnh vào tệp 
    with open(file_path, 'r+b') as f: 
        for index, piece in pieces: 
            if verify_piece(piece, index, piece_hashes): 
                offset = index * piece_length 
                f.seek(offset) 
                f.write(piece)
                # TO DO: Update downloaded, get a new piece
            else: 
                print(f"The {index} piece does not match the hash, it is ignored.")

def read_file_as_bytes(file_path):
    with open(file_path, 'rb') as file: 
        return file.read() 

def split_into_pieces(file_data, piece_length): 
    return [file_data[i:i + piece_length] for i in range(0, len(file_data), piece_length)]


# Functions for Uploading
def create_piece_message(index, begin, block):
    message_id = 7 
    block_length = len(block) 
    #print("length of block in piece request: ", block_length)
    length_prefix = 9 + block_length # 9 bytes for id, index, and begin 

    # Message's form: <len=0009+X><id=7><index><begin><block>
    message = struct.pack('!IBII', length_prefix, message_id, index, begin) + block
    return message
"""
        Chắc chắn rồi! struct.pack('!IIBII', length_prefix, message_id, index, begin) sử dụng cú pháp định dạng của struct module trong Python để đóng gói dữ liệu thành định dạng nhị phân. Dưới đây là giải thích chi tiết về '!IIBII':

        Giải thích '!IIBII'
        '!': Chỉ thị này xác định thứ tự byte là big-endian (byte quan trọng nhất trước).

        'I': Số nguyên không dấu 4 byte (32 bit unsigned integer).

        'B': Số nguyên không dấu 1 byte (8 bit unsigned integer).

        Cụ thể trong '!IIBII':

        'I': length_prefix - Độ dài tiền tố của thông điệp (4 byte).

        'I': message_id - ID của thông điệp (4 byte).

        'B': index - Chỉ số của mảnh (1 byte).

        'I': begin - Vị trí byte bắt đầu trong mảnh (4 byte).

        'I': block - Được thêm vào cuối thông điệp nhưng không phải là phần của struct.pack ở đây.
"""

  
if __name__ == "__main__":
    
    torrent_file_path = './input/t2.torrent' 

    file_source = "./src/Charlie_Chaplin_Mabels_Strange_Predicament.avi"
    file_data = read_file_as_bytes(file_source)

    pieces = split_into_pieces(file_data, 131072)

    #map_pieces_to_file(pieces, piece_length, file_path, piece_hashes)
    
    length_prefix = 13
    block = b'\xf8\x88\xf8\xc8\xf7]\xf8\x8b\xf7j\xf8:\xf7\x8c\xf8!\xf7\xb5\xf8f\xf7\xe7\xf8' 
    index = 0 
    begin = 0 
    message = create_piece_message(index,begin,block)
    print(message)

    unpacked_data = struct.unpack('!IBII', message[:13])
    block = message[13:]
    len, id, index, begin = unpacked_data 
    print(len, " ",id, " ", index,"  ", begin," ", block) 