from  TorrentFileHandler import *
from Peer import *
from  TorrentFileHandler import *
from Contact_tracker import * 

import socket
import threading
import time
import random as rd
import struct

# BitTorrent protocol constants 
PSTR = "BitTorrent protocol" 
PSTRLEN = 68    # (49+len(pstr)) bytes long
RESERVED = b'\x00' * 8 

def get_ip_address(): 
    hostname = socket.gethostname() # Lấy tên máy chủ 
    ip_address = socket.gethostbyname(hostname) # Truy xuất địa chỉ IP 
    return ip_address

def parse_peers(peers_binary):
    peers_list = []
    for i in range(0, len(peers_binary), 6):
        ip = socket.inet_ntoa(peers_binary[i:i+4])
        port = struct.unpack('!H', peers_binary[i+4:i+6])[0]
        peers_list.append((ip, port))
    return peers_list

def decode_bitfield_message(message): 
        
    # Tách length_prefix và message_id từ message đầu vào 
    length_prefix, message_id = struct.unpack('!IB', message[:5]) 
    
    # Phần còn lại của message là bitfield 
    bitfield_bytes = message[5:] 
    
    # Tạo danh sách bitfield từ chuỗi nhị phân 
    bitfield = [] 
    for byte in bitfield_bytes: 
        for i in range(8): 
            bitfield.append((byte >> (7 - i)) & 1) 
    
    # Cắt danh sách bitfield đến kích thước gốc của nó dựa trên length_prefix 
    bitfield = bitfield[:(length_prefix - 1) * 8] 
    return bitfield

def receive_full_message(sock, length): 
    data = b'' 
    while len(data) < length: 
        try: 
            part = sock.recv(length - len(data)) 
            if not part: 
                raise socket.error("Connection closed by peer") 
            data += part 
        except socket.timeout: 
            print("Receive timeout") 
            continue # Optionally, handle the timeout or retry 
        except socket.error as e: 
            print(f"Socket error: {e}") 
            break 
    return data



class Torrent__Statistic():
    def __init__(self, meta_info):
        self.meta_info              = meta_info
        self.uploaded               = set([])   # pieces uploaded
        self.downloaded             = set([])   # pieces downloaded -> (piece_index, complete_piece)
        self.piece_buffer           = []   # each piece -> [{index, piece: [{begin, block}, {begin2, block 2}]}, {index2, piece: []}]
        self.num_pieces_downloaded  = 0         # blocks/pieces downloaded
        self.num_pieces_uploaded    = 0         # blocks/pieces uplaoded
        self.num_pieces_left        = 0         # blocks/pieces left

        self.bitfield_pieces = set([])          # use for bitfield message


    def extract_block(self, index, begin, length):
        for piece_index, piece in self.downloaded:
            if(piece_index == index):
                print(f"Block from index {index}, begin {begin}, length {length}")
                print(piece[begin:begin + length])
                return piece[begin:begin + length]


    def add_block(self, piece_index, begin, block, block_length): # Receive piece message -> buffer the piece until get enough block -> create piece.
        existed_buffer = False
        for buff in self.piece_buffer: 
            if buff['index'] == piece_index: 
                existed_buffer = True
                buff['piece'].append({
                    'begin'         :   begin,
                    'block'         :   block
                })
                break
                        
        if not existed_buffer: 
            piece = {'index': piece_index, 'piece': []} 
            piece['piece'].append({
                    'begin'         :   begin,
                    'block'         :   block
                })
            self.piece_buffer.append(piece)

        #print(self.piece_buffer)
        
    def assemble_piece(self, piece_index): 
        for buff in self.piece_buffer:
            if buff['index'] == piece_index:
                sorted_block = sorted(buff['piece'], key=lambda x: x['begin'])
                data = b''
                for block in sorted_block:
                    data += block['block']
                self.downloaded.add((piece_index, data))
                self.piece_buffer.remove(buff)
                return data
        
        return None


    def display_info(self):
        print("Torrent Statistic:")
        print("Uploaded: ", self.uploaded)
        #print("Download", self.downloaded)
        print("num_pieces_downloaded", self.num_pieces_downloaded)
        print("num_pieces_uploaded", self.num_pieces_uploaded)
        print("num_pieces_left", self.num_pieces_left)
        print("---------------------------------------------------")


class Node():
    def __init__(self, meta_info):
        self.meta_info = meta_info # Metadata class
        self.client_port = 6881
        self.client_IP = get_ip_address()

        # Azureus-style encoding for peer id
        self.peer_id = ('-PC0001-' + ''.join([str(rd.randint(0, 9)) for i in range(12)])).encode()

        self.torrent_statistic = Torrent__Statistic(meta_info)
        self.choosen_tracker = None
        self.peer_list = []
        self.central_tracker_first_response = None # FOR TESTING

        self.handshake_msg = None

    def get_central_tracker(self):

        for tracker_url in self.meta_info.trackers_url_list:
            # classify HTTP and UDP torrent trackers...
            if 'http' in tracker_url[:4]: 

                rawresponse = get_HTTP_response(tracker_url, self, "started")
                if(rawresponse):
                    peer_list, complete, tracker_id = parse_http_tracker_response(rawresponse)
                    print("#1 Active tracker response: ", rawresponse)
                    if(peer_list):
                        self.choosen_tracker = tracker_url
                        self.central_tracker_first_response = rawresponse
                        self.peer_list = peer_list
                        break

    def display_info(self):
        self.meta_info.display_info()
        print("Node's information: ")
        print("client_port: ", self.client_port)
        print("client_IP: ", self.client_IP)
        print("peer_id: ", self.peer_id)
        print("peer_list: ", self.peer_list)
        print("choosen_tracker: ", self.choosen_tracker)
        #print("Central tracker first response: ", self.central_tracker_first_response)
        print("---------------------------------------------------")
        self.torrent_statistic.display_info()

    def create_hand_shake_message(self):  # DEPRECATED
        self. handshake_msg = struct.pack('!B19s8s20s20s', PSTRLEN, PSTR.encode('utf-8'), RESERVED, self.meta_info.info_hash,self.peer_id) 
        self. handshake_msg

    def receive_handshake(client_socket): # DEPRECATED
        try: 
            #response = client_socket.recv(68)
            response = receive_full_message(client_socket, 68) 
            if len(response) < 68: 
                raise ValueError("Handshake message is too short.") 
            pstrlen, pstr, reserved, info_hash, peer_id = struct.unpack('!B19s8s20s20s', response) 
            
            if pstr.decode('utf-8') != PSTR: 
                raise ValueError("Invalid protocol string.") 
            if info_hash != self.info_hash:
                raise ValueError("Invalid Info hash.") 

            print(f"Received handshake with info_hash: {info_hash.hex()} and peer_id: {peer_id.decode('latin-1')}") 
            # Send BitField message
            return info_hash, peer_id

        except ValueError as e: 
            print(f"Error: {e}") 
            error_message = str(e).encode('utf-8') 
            client_socket.sendall(error_message) 
            client_socket.close()
            return

    def create_bitfield_message(self): 
        # form: bitfield: <len=0001+X><id=5><bitfield> 
        length_prefix = 1 + (self.meta_info.piece_count + 7) // 8 
        message_id = 5 
        bitfield = [0] * self.meta_info.piece_count 
        for piece_index, _ in self.torrent_statistic.downloaded: 
            bitfield[piece_index] = 1 
            
        # Chuyển đổi danh sách bitfield thành chuỗi nhị phân 
        bitfield_bytes = bytearray((len(bitfield) + 7) // 8) 
        for i, bit in enumerate(bitfield): 
            if bit: bitfield_bytes[i // 8] |= 1 << (7 - i % 8) 
        
        message = struct.pack('!IB', length_prefix, message_id) + bytes(bitfield_bytes) 
        #print("Bitfield message: ", decode_bitfield_message(message))
        return message

    def start_downloading(self):
        #self.create_hand_shake_message()
        connected = set()
        threads = [] 
        for peer in self.peer_list: 
            ip, port = peer
            if (ip, port) in connected:
                continue
            connected.add((ip, port))
            thread = threading.Thread(target=self.handle_peer_connection, args=(ip, port)) 
            #print(thread)
            threads.append(thread) 
            thread.start()

       # Chờ cho tất cả các luồng hoàn thành
        for thread in threads: 
            thread.join()

        print("File downloaded with total of pieces:", self.torrent_statistic.num_pieces_downloaded)

    def handle_upload(self, client_socket, client_addr): 
        try:
            if self.torrent_statistic.num_pieces_downloaded:
                bitfield_msg =  self.create_bitfield_message()
                # Send Bitfield
                client_socket.sendall(bitfield_msg)

            peer_state = {
                'am_choking'        :   0, 
                'am_interested'     :   0,
                'peer_choking'      :   0,
                'peer_interested'   :   0
            }
            while True:
                # Wait for peer's request message
                #message = client_socket.recv(17)
                message = receive_full_message(client_socket, 17)
                if(handle_incoming_mesage(message, client_socket, self, client_addr) is False):
                    #client_socket.close() 
                    print(f"Lost connection to peer {client_addr} due to short message, error,...")
                    break
                
        finally:
            client_socket.close()

    def start_uploading(self):
        #thread = []
        seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Listening for handshake requests on port {self.client_port}...") 
        seed_socket.bind((self.client_IP, self.client_port))
        seed_socket.listen(5)

        while True:
            client_socket, addr = seed_socket.accept() 
            print(f"Accepted connection from {addr}") 

            # Tạo một luồng mới để xử lý kết nối với client 
            thread = threading.Thread(target=self.handle_upload, args=(client_socket,addr))
            thread.start()

    def getPiece(self, client_socket, piece_index): # Continually get blocks in the piece
        block_length = self.meta_info.block_length
        num_blocks = self.meta_info.num_block
        
        for i in range(num_blocks):
            request_msg = create_request_message(piece_index, i * block_length, block_length)
            #print(f"Send request message {i}: ", request_msg)
            client_socket.sendall(request_msg)
            
            # Wait for piece message
            # Message's form: <len=0009+X><id=7><index><begin><block>  -> '!IBII'
            # 13 byte (4 byte for len, 1 byte for id, 4 byte for index, 4 byte for begin) and block length
            piece_message = receive_full_message(client_socket, block_length + 13) 
            #print(f"Receive piece message: {piece_message}")
            handle_piece_message(piece_message, self.torrent_statistic)
        
        self.torrent_statistic.assemble_piece(piece_index)
        print(f"Get piece {piece_index}")



    def handle_peer_connection(self, peer_ip, peer_port): # For downloading
        try: 
            # Tạo socket và kết nối đến peer 
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            client_socket.settimeout(5)
            client_socket.connect((peer_ip, peer_port)) 
            
            # Gửi thông điệp handshake 
            #client_socket.sendall(self.handshake_msg) 

            # Nhận phản hồi từ peer 
            # Nhận bitfield từ peer nếu có 
            len = 1 + (self.meta_info.piece_count + 7) // 8 
            #raw_bitfield_response = client_socket.recv(len)
            raw_bitfield_response = receive_full_message(client_socket, len) 
            bitfield_response = decode_bitfield_message(raw_bitfield_response)
            #print(f"Bitfield response from {peer_ip}:{peer_port} - {bitfield_response}") 
            
            
            # Giờ có thể thực hiện các tương tác khác 
            # # Ví dụ: gửi thông điệp request, nhận thông điệp piece, gửi thông điệp hứng thú 
            # # Thêm logic ở đây để gửi/nhận các thông điệp cần thiết
            # Đóng kết nối 
            #threads = []
            if(self.torrent_statistic.num_pieces_downloaded == 0):
                for piece_index, valid in enumerate(bitfield_response):
                    if valid:
                        #thread = threading.Thread(target=self.getPiece, args=(client_socket, piece_index))
                        #thread.start()
                        self.getPiece(client_socket, piece_index)

            #client_socket.close() 
        except Exception as e: 
            print(f"Error connecting to {peer_ip}:{peer_port} - {e}")
        

if __name__ == "__main__":
    file_path = "./input/t2.torrent"
    src_parth = "./src/Charlie_Chaplin_Mabels_Strange_Predicament.avi"  
    metadata = readTorrentFile(file_path)
    metaInfo = Metadata(*metadata)
    node = Node(metaInfo)


    file_data = read_file_as_bytes(src_parth)
    pieces = split_into_pieces(file_data, node.meta_info.piece_length)

    for piece_index, complete_piece in enumerate(pieces):
        node.torrent_statistic.downloaded.add((piece_index, complete_piece))
        node.torrent_statistic.num_pieces_downloaded += 1
    count = 0

    node.display_info()
    for index, data in node.torrent_statistic.downloaded:
        if index == 0:
            print(data[:node.meta_info.block_length])
            break