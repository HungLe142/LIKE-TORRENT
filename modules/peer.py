
import copy
import hashlib
import bencodepy 
import struct
import os
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




def handle_incoming_message(message, client_socket, node, client_addr): 
    
    if not message: # Check if message is None or empty 
        print("Received message is invalid: ", message) 
        return False 
    
    if isinstance(message, bytes) and len(message) >= 5: 
        length_prefix, message_id = struct.unpack('!IB', message[:5]) 
        if message_id == 7: 
            print("Message received is Piece message: ", message) 
            handle_piece_message(message[5:], node.torrent_statistic) 
        elif message_id == 6: 
            print("Message received is Request message: ", message) 
            handle_request_message(message, client_socket, node) 
    else: 
        print("Received message is too short or invalid type: ", message) 
        return False 
            
    return True

def handle_piece_message(piece_message, torrent_statistic): 
    # Message's form: <len=0009+X><id=7><index><begin><block>
    unpacked_data = struct.unpack('!IBII', piece_message[:13]) # Split first 13 byte into len, id, index, begin
    len, id, index, begin = unpacked_data
    block = piece_message[13:]
    torrent_statistic.add_block(index, begin, block, len-9)
    
def create_request_message(index, begin, block_length):
    message_id = 6 
    length_prefix = 13

    # Message's form: request: <len=0013><id=6><index><begin><length>
    message = struct.pack('!IBIII', length_prefix, message_id, index, begin, block_length)
    return message

def handle_request_message(request_message, client_socket, node):
    # Message's form: request: <len=0013><id=6><index><begin><length>
    unpacked_data = struct.unpack('!IBIII', request_message)
    _, id, index, begin, length = unpacked_data
    #print("id: ", id,"index: ", index,"begin: ", begin,"length: ", length)
    #print("Start block extracting!")
    block = node.torrent_statistic.extract_block(index, begin, length)
    #print("Extracted block: ", block, "index: ", index, "begin: ", begin)
    piece_msg = create_piece_message(index, begin, block)

    # For debuging
    #unpacked_data = struct.unpack('!IBII', piece_msg[:13])
    #len, id, index, begin = unpacked_data
    #print(id, index, begin, length)

    #print("Send piece message: ", piece_msg)
    try:
        client_socket.send(piece_msg)
        if block:
            node.update_uploading_status(index)

    except Exception as e:
        print(f"Failed to send piece message: {e}")




# Function for dowloading ultimate file into local
def verify_piece(piece, piece_index, piece_hashes): # Get a {piece, index} from piece message -> hash it -> compare with piece[index] from MetaInfo file
    # Tính toán SHA1 hash của mảnh 
    sha1_hash = hashlib.sha1(piece).digest() 
    # So sánh với hash từ file .torrent 
    return sha1_hash == piece_hashes[piece_index] 

def map_pieces_to_file(pieces, piece_length, file_path, piece_hashes):
    # Tạo thư mục nếu không tồn tại
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Kiểm tra nếu file tồn tại và đổi tên nó
    if os.path.exists(file_path):
        base, extension = os.path.splitext(file_path)
        new_file_path = base + "_backup" + extension
        os.rename(file_path, new_file_path)
        print(f"Renamed existing file to {new_file_path}")

    # Cố gắng mở tệp trong chế độ đọc ghi, hoặc tạo mới nếu không tồn tại
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
    if block is None:
        block_length = 0
        block = b''
    else:
        block_length = len(block) 
    length_prefix = 9 + block_length # 9 bytes for id, index, and begin 

    # Message's form: <len=0009+X><id=7><index><begin><block>
    message = struct.pack('!IBII', length_prefix, message_id, index, begin) + block
    return message
  
if __name__ == "__main__":
    pass