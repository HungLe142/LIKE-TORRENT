from  modules.file_processing import *
from modules.peer import *
from modules.tracker_contacting import * 
from tkinter import messagebox
from modules.peer import map_pieces_to_file

import socket
import threading
import time
import random as rd
import struct
import base64

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
        self.uploaded               = set([])   # pieces uploaded     -> NOT USED
        self.downloaded             = set([])   # pieces downloaded -> (piece_index, complete_piece)
        self.piece_buffer           = []   # each piece -> [{index, piece: [{begin, block}, {begin2, block 2}]}, {index2, piece: []}]
        self.num_pieces_downloaded  = 0         # blocks/pieces downloaded
        self.num_pieces_uploaded    = 0         # blocks/pieces uplaoded    
        self.num_pieces_left        = 0         # blocks/pieces left
        self.bitfield_pieces = set([])          # use for bitfield message
        self.peer_data                   =  []  # use for manage peers : [{peer_ip, port, status, up, down}]
        self.torrent_status = "Unstarted"
        self.torrent_status_up = 'Unstarted'

    def extract_block(self, index, begin, length):
        for piece_index, piece in self.downloaded:
            #print(piece_index)
            #if(piece_index == 0):
               # print("piece 0: ", piece_index)
            if(piece_index == index):
                #print(f"Piece {piece_index} found with length {len(piece)}") 
                #print(f"Requested block from {begin} to {begin + length}") 
                return piece[begin:begin + length] 
                
        print(f"Piece {index} not found")
        return None

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

def file_parse_controller(link): #DEPRECATED
    thread = threading.Thread(target=parse_torrent_file_link, args=(link,)) 
    thread.start()

def parse_torrent_file_link(link):

    metadata = readTorrentFile(link)
    expected_length = 8
    if metadata is None or len(metadata) != expected_length:
        return None

    metaInfo = Metadata(*metadata)
    #metaInfo.display_info()
    node = Node(metaInfo)
    node.get_central_tracker()
    return node


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
        self.status_lock = threading.Lock()
        self.peer_data_lock = threading.Lock()

    def get_central_tracker(self):

        for tracker_url in self.meta_info.trackers_url_list:
            # classify HTTP and UDP torrent trackers...
            if 'http' in tracker_url[:4]: 

                rawresponse = get_HTTP_response(tracker_url, self, "started")
                if(rawresponse):
                    peer_list, complete, tracker_id = parse_http_tracker_response(rawresponse)
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

    def start_downloading(self, des_link):

        self.meta_info.des_link = des_link
        self.torrent_statistic.torrent_status = "Downloading"
        thread = threading.Thread(target=self.download_controller,) 
        thread.start()

    def download_controller(self):
        # Turn 1: Get Pieces, focus on BitField response:
        print("Downloading in turn 1!")
        try_connected = set()
        threads = []
        for peer in self.peer_list:
            ip, port = peer
            if (ip, port) in try_connected:
                continue
            try_connected.add((ip, port))

            thread = threading.Thread(target=self.getFromBitField, args=(ip, port)) 
            threads.append(thread) 
            thread.start()

        # for thread in threads: 
        #    thread.join()

        # Turn 2: Get Pieces, focus on Missing Pieces:
        print("Start downloading from turn 2!")
        while True:
            if self.torrent_statistic.torrent_status == "Stopped":
                print("Stopping download section...")
                break
            if self.torrent_statistic.num_pieces_downloaded == self.meta_info.piece_count:
                break

            miss_index = find_missing_indices(self.meta_info.piece_count, self.torrent_statistic.bitfield_pieces)
            self.get_central_tracker()
            try_connected = set()

            threads = [] 
            for peer in self.peer_list: 

                if self.torrent_statistic.torrent_status == "Stopped":
                    print("Stopping download section...")
                    break

                if(self.torrent_statistic.num_pieces_downloaded == self.meta_info.piece_count):
                    return

                ip, port = peer
                if (ip, port) in try_connected:
                    continue
                try_connected.add((ip, port)) # need updating

                # Gọi hàm qua thread, dữ liệu của class chưa được cập nhật
                thread = threading.Thread(target=self.getFromMissPieces, args=(ip, port, miss_index)) 
                threads.append(thread) 
                thread.start()
            
            # for thread in threads: 
            #    thread.join()

        # Finish download or Pausing
        for peer in self.torrent_statistic.peer_data:
            peer['down_status'] =  "disconnected"
        
        with self.status_lock:
            if self.torrent_statistic.torrent_status == "Stopped":
                return
            self.torrent_statistic.torrent_status = "Finished"
            
            print("File downloaded with total of pieces:", self.torrent_statistic.num_pieces_downloaded)
            print(f"Destination path: {self.meta_info.des_link}")
            des_link = self.meta_info.des_link + self.meta_info.file_name
            map_pieces_to_file(self.torrent_statistic.downloaded, self.meta_info.piece_length, des_link, self.meta_info.pieces)

    def handle_upload(self, client_socket, client_addr): 
        try:
            if self.torrent_statistic.num_pieces_downloaded:
                bitfield_msg =  self.create_bitfield_message()
                #mess= decode_bitfield_message(bitfield_msg)
                #print(mess)
                # Send Bitfield
                client_socket.sendall(bitfield_msg)

            peer_state = {
                'am_choking'        :   0, 
                'am_interested'     :   0,
                'peer_choking'      :   0,
                'peer_interested'   :   0
            }
            while True:
                if self.torrent_statistic.torrent_status_up ==  'Stopped':
                    break
                # Wait for peer's request message
                message = client_socket.recv(17)
                #message = receive_full_message(client_socket, 17)
                if(handle_incoming_message(message, client_socket, self, client_addr) is False):
                    #client_socket.close()
                    print(f"Lost connection to peer {client_addr} due to short message, error,...")
                    break
                
        finally:
            client_socket.close()

    def start_uploading(self):
        with self.status_lock:
            self.torrent_statistic.torrent_status_up =  'Running'
            seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            seed_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow reuse local address
            print(f"Listening for handshake requests on {self.client_IP} : {self.client_port}...") 
            seed_socket.bind((self.client_IP, self.client_port))
            seed_socket.listen(5)

            while True:
                if self.torrent_statistic.torrent_status_up ==  'Stopped':
                    break
                client_socket, addr = seed_socket.accept()
                # Resending message to tracker for keep aliving
                get_HTTP_response(self.choosen_tracker, self, "started")
                print(f"Accepted connection from {addr}") 

                # Tạo một luồng mới để xử lý kết nối với client 
                thread = threading.Thread(target=self.handle_upload, args=(client_socket,addr))
                thread.start()

    def update_uploading_status(self, block):
        with self.status_lock:
            if self.torrent_statistic.torrent_status_up != 'Running':
                return
            
            piece_length = self.meta_info.piece_length
            
            # Convert block from bytes to length
            num_pieces_in_block = len(block) // piece_length  # Use integer division
            
            # Update number of pieces uploaded
            self.torrent_statistic.num_pieces_uploaded += num_pieces_in_block
            print("Piece uploaded: ", self.torrent_statistic.num_pieces_uploaded)

            

    def parse_script_file(self, link, root):
        # script is a txt file
        # format: each line: <index> <piece_data>
        # index is the index of piece
        
        piece_hashes = self.meta_info.pieces
        with open(link, 'r') as file:
            for line in file:
                parts = line.strip().split()
                piece_index = int(parts[0])
                complete_piece_str = parts[1]
                complete_piece = base64.b64decode(complete_piece_str.encode('ascii'))  # Chuyển đổi chuỗi base64 về dạng bytes
                
                #print(piece_index)
                with self.piece_lock:
                    
                    if verify_piece(complete_piece, piece_index, piece_hashes) is False:
                            root.root.after(0, lambda: messagebox.showwarning("Warning", "Your src file has some incorrect pieces, we discard them, the process is stopped.")) 
                            self.torrent_statistic.torrent_status_up = 'Stopped'
                            break
                    
                    piece = (piece_index, complete_piece)
                    if piece in self.torrent_statistic.bitfield_pieces:
                        continue
                    else:
                        #print("Added piece:", piece_index)
                        #if piece_index <= 0:
                            #print("Piece ",piece_index, ": ", complete_piece)
                        self.torrent_statistic.downloaded.add(piece)
                        self.torrent_statistic.num_pieces_downloaded += 1
                        self.torrent_statistic.bitfield_pieces.add((piece_index, 1))

        #for index, bit in self.torrent_statistic.bitfield_pieces:
            #print(index, bit)
        #block = self.torrent_statistic.extract_block(0, 1, 16384)
        #print("Extracted block after parse script: ", block)

        self.start_uploading()


    def upload_controller(self, link, root):
        thread = threading.Thread(target=self.parse_script_file, args=(link,root)) 
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
        
        for data in self.torrent_statistic.peer_data:
            with self.peer_data_lock:
                if data['ip'] == ip_address and data['port'] == port and data['down_status'] == "connected":
                    data['down'] += 1
                    break


        print(f"Get piece {piece_index} from {ip_address} : {port} total piece: {self.torrent_statistic.num_pieces_downloaded}")

    def getFromBitField(self, peer_ip, peer_port): # For downloading
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
            peer ={
                'ip'                :   peer_ip,
                'port'              :   peer_port,
                'down_status'       :   "connected",
                'up_status'         :   "unstarted",
                'up'                :   0,
                'down'              :   0
            }
            with self.peer_data_lock:
                if not self.check_new_peer(peer_ipip, peer_port): 
                    self.torrent_statistic.peer_data.append(peer)

            for piece_index, valid in enumerate(bitfield_response):
                
                # Condition for stopping current thread
                if self.torrent_statistic.torrent_status == "Stopped":
                    break

                if(self.torrent_statistic.num_pieces_downloaded == self.meta_info.piece_count):
                    return
                if valid:
                    
                    with self.piece_lock:
                        bf_dict = dict(self.torrent_statistic.bitfield_pieces)
                        if bf_dict.get(piece_index) == 1:
                            continue
                        else:
                            print("Turn 1 hit: piece: ", piece_index)
                            self.getPiece(client_socket, piece_index)

            ip_address, port = client_socket.getpeername()
            for data in self.torrent_statistic.peer_data:
                with self.peer_data_lock:
                    if data['ip'] == ip_address and data['port'] == port and data['down_status'] == "connected":
                        data['down_status'] = "disconnected"
                        break
            client_socket.close() 

        except socket.timeout:
          """  peer ={
                'ip'                :   peer_ip,
                'port'              :   peer_port,
                'down_status'       :   "cannot connect (Time out)",
                'up_status'         :   "unstarted",
                'up'                :   0,
                'down'              :   0
            }
            with self.peer_data_lock:
                if not self.check_new_peer(peer_ip, peer_port):
                    self.torrent_statistic.peer_data.append(peer)
                print(f"Timeout connecting to {peer_ip}:{peer_port}")"""

        except Exception as e: 
            """peer ={
                'ip'                :   peer_ip,
                'port'              :   peer_port,
                'down_status'       :   "cannot connect",
                'up_status'         :   "unstarted",
                'up'                :   0,
                'down'              :   0
            }
            with self.peer_data_lock:
                if not self.check_new_peer(peer_ip, peer_port):
                    self.torrent_statistic.peer_data.append(peer)        
                print(f"Error connecting to {peer_ip}:{peer_port} - {e}")"""

    def check_new_peer(self, ip, port):
        new_peer = True
        for data in self.torrent_statistic.peer_data:
            if data['ip'] == ip and data['port'] == port:
                new_peer = False
                break
        return  new_peer

    def getFromMissPieces(self, peer_ip, peer_port, miss_index):   
        try: 
            # Tạo socket và kết nối đến peer 
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            client_socket.settimeout(5)
            client_socket.connect((peer_ip, peer_port))

            existed = False
            with self.piece_lock:
                for data in self.torrent_statistic.peer_data:
                    with self.peer_data_lock:
                        if data['ip'] == peer_ip and data['port'] == peer_port:
                            existed = True
                            data['down_status'] = "connected"
                            break

                if not existed:
                    peer ={
                        'ip'                :   peer_ip,
                        'port'              :   peer_port,
                        'down_status'       :   "connected",
                        'up_status'         :   "disconnected",
                        'up'                :   0,
                        'down'              :   0
                    }
                    self.torrent_statistic.peer_data.append(peer)

            raw_bitfield_response = client_socket.recv(1024)
            bitfield_response = decode_bitfield_message(raw_bitfield_response)

            for index in miss_index:

                if(self.torrent_statistic.num_pieces_downloaded == self.meta_info.piece_count):
                    return
                with self.piece_lock:
                    bf_dict = dict(self.torrent_statistic.bitfield_pieces)

                    if bf_dict.get(index) == 1:
                        continue
                    else:
                        for piece_index, valid in enumerate(bitfield_response):
                            if piece_index == index:
                                if valid:
                                    print("Turn 2 hit, start get piece: ", piece_index)
                                    self.getPiece(client_socket, index)
                                    break
                                else:
                                    print("Turn 2 miss, the peer doesn't have the piece: ", piece_index)
                                    break

        except Exception as e:  
            print(f"Error connecting to {peer_ip}:{peer_port} - {e}")

if __name__ == "__main__":
    pass