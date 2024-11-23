import sys
import bencodepy
from collections import OrderedDict 
import hashlib
import math


class Metadata():

    def __init__(self, trackers_url_list, file_name, file_size, piece_length, pieces, info_hash, files):
        self.trackers_url_list  = trackers_url_list     # list   : URL of trackers
        self.file_name      = file_name                 # string : file name
        self.file_size      = file_size                 # int    : file size in bytes
        self.piece_length   = piece_length              # int    : piece length in bytes
        self.pieces         = pieces                    # bytes  : sha1 hash concatination of file
        self.info_hash      = info_hash                 # sha1 hash of the info metadata
        self.files          = files                     # list   : [length, path] (multifile torrent)
        self.piece_count    = math.ceil(file_size / piece_length) # number of pieces the client need to download
        self.num_block      = math.ceil(piece_length / (16 * (2 ** 10)) )
        # pieces divided into chunks of fixed block size
        self.block_length   = 16 * (2 ** 10)            # 16KB

    def get_piece_length(self, piece_index):
        # Trả về độ dài của piece cuối cùng nếu piece_index là piece cuối cùng, ngược lại trả về piece_length
        if piece_index == self.piece_count - 1:
            return self.file_size % self.piece_length or self.piece_length
        return self.piece_length

    def display_info(self):
        print("---------------------------------------------------")
        print("Meta info:")
        print(" Trackers URL List:", self.trackers_url_list) 
        print(" File Name:", self.file_name) 
        print(" File Size:", self.file_size) 
        print(" Piece Length:", self.piece_length) 
        #print(" Pieces:", self.pieces) 
        print(" Info Hash:", self.info_hash) 
        print(" Files:", self.files)
        print(" Piece count:", self.piece_count)
        print("Number of pieces: ", self.piece_count)
        print("Block size: ", self.block_length)
        print("Num block: ", self.num_block)
        print("---------------------------------------------------")

def get_piece_hashes(torrent_data): 

    info = torrent_data[b'info'] 
    pieces = info[b'pieces'] 
    piece_length = info[b'piece length']
    
    # Lấy danh sách mã băm các mảnh 
    piece_hashes = [pieces[i:i+20] 
    for i in range(0, len(pieces), 20)] 
    return piece_hashes, piece_length

def get_tracker_url_list(torrent_data):
    
    info = torrent_data[b'info'] 
    # Kiểm tra và lấy danh sách tracker URL từ file .torrent 
    tracker_url_list = [] 
    if b'announce-list' in torrent_data: 
        for tier in torrent_data[b'announce-list']: 
            for url in tier: 
                tracker_url_list.append(url.decode('utf-8')) 
    elif b'announce' in torrent_data: 
        tracker_url_list.append(torrent_data[b'announce'].decode('utf-8')) 
    
    return tracker_url_list

def get_file_info(torrent_data):
   
    info = torrent_data[b'info'] 
    # Lấy tên tệp 
    file_name = info[b'name'].decode('utf-8') 
    # Lấy kích thước tệp 
    file_size = 0 
    if b'files' in info: 
        # Đối với tệp nhiều phần 
        for file_dict in info[b'files']: 
            file_size += file_dict[b'length'] 
    else: 
        # Đối với tệp đơn 
        file_size = info[b'length'] 

    return file_name, file_size

def generate_info_hash(torrent_data):
    sha1_hash = hashlib.sha1()
    # get the raw info value
    raw_info = torrent_data[b'info']
    # update the sha1 hash value
    sha1_hash.update(bencodepy.encode(raw_info))
    return sha1_hash.digest()

def readTorrentFile(path):
    try :
        with open(path, 'rb') as file:
            torrent_data = bencodepy.decode(file.read())

            trackers_url_list = get_tracker_url_list(torrent_data)
            pieces, piece_length = get_piece_hashes(torrent_data)
            file_name, file_size = get_file_info(torrent_data)
            info_hash = generate_info_hash(torrent_data)
            # files is list of tuple of size and path in case of multifile torrent
            files = None

        return trackers_url_list, file_name, file_size, piece_length, pieces, info_hash, files
    
    except Exception as err:
        print(err)
        sys.exit()


if __name__ == "__main__":
    metadata = readTorrentFile("./input/mix_http.torrent")

    torrentInfo = Metadata(*metadata)
    torrentInfo.display_info()

