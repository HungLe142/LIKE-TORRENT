from  TorrentFileHandler import *
from Peer import *
from  TorrentFileHandler import *
from Contact_tracker import * 

import socket
import threading
import time
import random as rd
import struct

VERSION = 'Window' # Change it to 'Kali' or 'Ubuntu' corresponding to ur OS

try: 
    import netifaces as ni 
except ImportError: 
    ni = None

# BitTorrent protocol constants 
PSTR = "BitTorrent protocol" 
PSTRLEN = 68    # (49+len(pstr)) bytes long
RESERVED = b'\x00' * 8 

def get_ip_address(interface_name): 
    if VERSION == 'Window':
        hostname = socket.gethostname() # Lấy tên máy chủ 
        ip_address = socket.gethostbyname(hostname) # Truy xuất địa chỉ IP 

    else:
        if ni: 
            ip_address = ni.ifaddresses(interface_name)[ni.AF_INET][0]['addr'] 
        else: 
            raise ImportError('Module netifaces has not been imported')
    
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
            #continue # Optionally, handle the timeout or retry
            return False 
        except socket.error as e: 
            print(f"Socket error: {e}") 
            #break
            return False 
    return data

def find_missing_indices(count, data): 
    # Tạo một tập hợp tất cả các chỉ số từ 0 đến count - 1 
    all_indices = set(range(count)) 
    
    # Tạo một tập hợp các chỉ số có trong data
    present_indices = set(index for index, val in data) 
    
    # Tìm các chỉ số còn thiếu bằng cách lấy sự khác biệt của hai tập hợp 
    missing_indices = all_indices - present_indices 
    return sorted(missing_indices)

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
                #print(f"Block from index {index}, begin {begin}, length {length}")
                #print(piece[begin:begin + length])
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

                self.piece_buffer.remove(buff)
                if(verify_piece(data, piece_index, self.meta_info.pieces)):
                    self.downloaded.add((piece_index, data))
                    self.num_pieces_downloaded += 1
                    self.bitfield_pieces.add((piece_index, 1))
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

        if VERSION == 'Window':
            interface_name = 'Wi-Fi'
        elif VERSION == 'Ubuntu':
            interface_name = 'enp0s3'
        else:
            interface_name = 'eth0'

        # interface_name = 'enp0s3' # Use for virtual machine in VirtualBox
        self.client_IP = get_ip_address(interface_name)

        # Azureus-style encoding for peer id
        self.peer_id = ('-PC0001-' + ''.join([str(rd.randint(0, 9)) for i in range(12)])).encode()

        self.torrent_statistic = Torrent__Statistic(meta_info)
        self.choosen_tracker = None
        self.peer_list = []
        self.central_tracker_first_response = None # FOR TESTING

        self.handshake_msg = None

        # Khóa để đồng bộ hóa
        self.piece_lock = threading.Lock()

    def get_central_tracker(self):

        for tracker_url in self.meta_info.trackers_url_list:
            # classify HTTP and UDP torrent trackers...
            if 'http' in tracker_url[:4]: 

                rawresponse = get_HTTP_response(tracker_url, self, "started")
                if(rawresponse):
                    peer_list, complete, tracker_id = parse_http_tracker_response(rawresponse)
                    #print("#1 Active tracker response: ", rawresponse)
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

            #print(f"Received handshake with info_hash: {info_hash.hex()} and peer_id: {peer_id.decode('latin-1')}") 
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
        for piece_index, _ in self.torrent_statistic.bitfield_pieces: 
            bitfield[piece_index] = 1 
            
        # Chuyển đổi danh sách bitfield thành chuỗi nhị phân 
        bitfield_bytes = bytearray((len(bitfield) + 7) // 8) 
        for i, bit in enumerate(bitfield): 
            if bit: bitfield_bytes[i // 8] |= 1 << (7 - i % 8) 
        
        message = struct.pack('!IB', length_prefix, message_id) + bytes(bitfield_bytes) 
        #print("Bitfield message: ", decode_bitfield_message(message))
        return message

    def download_in_turn1(self):
        connected = set()
        threads = [] 
        for peer in self.peer_list: 
            ip, port = peer
            if (ip, port) in connected:
                continue
            connected.add((ip, port)) # need updating

            # Gọi hàm qua thread, dữ liệu của class chưa được cập nhật
            thread = threading.Thread(target=self.get_pieces_peer1, args=(ip, port)) 
            #print(thread)a
            threads.append(thread) 
            thread.start()

       # Chờ cho tất cả các luồng hoàn thành
        for thread in threads: 
            thread.join()
    
    def download_from_turn2(self, miss_index):
        self.get_central_tracker()

        connected = set()
        threads = [] 
        for peer in self.peer_list: 

            if(self.torrent_statistic.num_pieces_downloaded == self.meta_info.piece_count):
                return

            ip, port = peer
            if (ip, port) in connected:
                continue
            connected.add((ip, port)) # need updating

            # Gọi hàm qua thread, dữ liệu của class chưa được cập nhật
            thread = threading.Thread(target=self.get_pieces_peer2, args=(ip, port, miss_index)) 
            #print(thread)a
            threads.append(thread) 
            thread.start()

       # Chờ cho tất cả các luồng hoàn thành
        for thread in threads: 
            thread.join()

    def download_strategy(self):
        self.download_in_turn1()

        while True:
            if self.torrent_statistic.num_pieces_downloaded == self.meta_info.piece_count:
                break

            miss_index = find_missing_indices(self.meta_info.piece_count, self.torrent_statistic.bitfield_pieces)
            self.download_from_turn2(miss_index)

    def start_downloading(self): # Need updating by downloading strategy...
        #self.create_hand_shake_message()
        if not self.peer_list:
            return
        self.download_strategy()
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
                if(handle_incoming_message(message, client_socket, self, client_addr) is False):
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
            # Resending message to tracker for keep aliving
            get_HTTP_response(self.choosen_tracker, self, "started")
            print(f"Accepted connection from {addr}") 

            # Tạo một luồng mới để xử lý kết nối với client 
            thread = threading.Thread(target=self.handle_upload, args=(client_socket,addr))
            thread.start()

    def getPiece(self, client_socket, piece_index): 
        if piece_index == self.meta_info.piece_count - 1: # Last piece case 
            piece_length = self.meta_info.get_piece_length(piece_index) 
            num_blocks = math.ceil(piece_length / self.meta_info.block_length) 
        else: 
            piece_length = self.meta_info.piece_length 
            num_blocks = self.meta_info.num_block 
            
        for i in range(num_blocks): 
            offset = i * self.meta_info.block_length 
            length = min(self.meta_info.block_length, piece_length - offset) # Ensure the correct length for the last block 
            
            request_msg = create_request_message(piece_index, offset, length) 
            client_socket.sendall(request_msg) 
            
            piece_message = receive_full_message(client_socket, length + 13) 
            if piece_message is False: 
                ip_address, port = client_socket.getpeername() 
                print(f"Skip the {piece_index} piece from {ip_address} : {port}, try again later.") 
                return False 
            
            handle_piece_message(piece_message, self.torrent_statistic) 
        
        self.torrent_statistic.assemble_piece(piece_index) 
        ip_address, port = client_socket.getpeername() 
        print(f"Get piece {piece_index} from {ip_address} : {port} total piece: {self.torrent_statistic.num_pieces_downloaded}")


    def get_pieces_peer1(self, peer_ip, peer_port): # For downloading
        try: 
            # Tạo socket và kết nối đến peer 
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            client_socket.settimeout(5)
            client_socket.connect((peer_ip, peer_port)) 
            
            # Gửi thông điệp handshake 
            #client_socket.sendall(self.handshake_msg) 

            # Nhận phản hồi từ peer 
            # Nhận bitfield từ peer nếu có 
            #len = 1 + (self.meta_info.piece_count + 7) // 8 
            #raw_bitfield_response = receive_full_message(client_socket, len) 
            
            raw_bitfield_response = client_socket.recv(1024)
            bitfield_response = decode_bitfield_message(raw_bitfield_response)
            
            for piece_index, valid in enumerate(bitfield_response):
                if(self.torrent_statistic.num_pieces_downloaded == self.meta_info.piece_count):
                    return
                if valid:
                    with self.piece_lock:
                        bf_dict = dict(self.torrent_statistic.bitfield_pieces)
                        if bf_dict.get(piece_index) == 1:
                            continue
                        self.getPiece(client_socket, piece_index)

            #client_socket.close() 
        except Exception as e: 
            print(f"Error connecting to {peer_ip}:{peer_port} - {e}")

    def get_pieces_peer2(self, peer_ip, peer_port, miss_index):   
        try: 
            # Tạo socket và kết nối đến peer 
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            client_socket.settimeout(5)
            client_socket.connect((peer_ip, peer_port)) 
            
            # Gửi thông điệp handshake 
            #client_socket.sendall(self.handshake_msg) 

            # Nhận phản hồi từ peer 
            # Nhận bitfield từ peer nếu có 
            #len = 1 + (self.meta_info.piece_count + 7) // 8 
            #raw_bitfield_response = receive_full_message(client_socket, len) 
            
            raw_bitfield_response = client_socket.recv(1024)
            bitfield_response = decode_bitfield_message(raw_bitfield_response)

            for index in miss_index:
                if(self.torrent_statistic.num_pieces_downloaded == self.meta_info.piece_count):
                    return
                with self.piece_lock:
                    bf_dict = dict(self.torrent_statistic.bitfield_pieces)
                    if bf_dict.get(index) == 1:
                        continue
                    self.getPiece(client_socket, index)

            #client_socket.close() 
        except Exception as e: 
            print(f"Error connecting to {peer_ip}:{peer_port} - {e}")

if __name__ == "__main__":
    pass