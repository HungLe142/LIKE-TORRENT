import sys
import bencodepy
from collections import OrderedDict 
import hashlib


class Metadata():

    def __init__(self, trackers_url_list, file_name, file_size, piece_length, pieces, info_hash, files):
        self.trackers_url_list  = trackers_url_list     # list   : URL of trackers
        self.file_name      = file_name                 # string : file name
        self.file_size      = file_size                 # int    : file size in bytes
        self.piece_length   = piece_length              # int    : piece length in bytes
        self.pieces         = pieces                    # bytes  : sha1 hash concatination of file
        self.info_hash      = info_hash                 # sha1 hash of the info metadata
        self.files          = files                     # list   : [length, path] (multifile torrent)

    def display_info(self):
        print("Meta info:")
        print(" Trackers URL List:", self.trackers_url_list) 
        print(" File Name:", self.file_name) 
        print(" File Size:", self.file_size) 
        print(" Piece Length:", self.piece_length) 
        print(" Pieces:", self.pieces) 
        print(" Info Hash:", self.info_hash) 
        print(" Files:", self.files)

def generate_info_hash(torrent_file_raw_extract):
    sha1_hash = hashlib.sha1()
    # get the raw info value
    raw_info = torrent_file_raw_extract[b'info']
    # update the sha1 hash value
    sha1_hash.update(bencodepy.encode(raw_info))
    return sha1_hash.digest()

def extract_torrent_metadata(rawMetaData, encoding):
    torrent_extract = OrderedDict()

    for key, value in rawMetaData.items():
        # decoding the key
        new_key = key.decode(encoding)
        # if type of value is of type dictionary then do deep copying
        if type(value) == OrderedDict:
            torrent_extract[new_key] = extract_torrent_metadata(value,encoding)
        # if the current torrent file could have multiple files with paths
        elif type(value) == list and new_key == 'files':
            torrent_extract[new_key] = list(map(lambda x : extract_torrent_metadata(x, encoding), value))
        elif type(value) == list and new_key == 'path':
            torrent_extract[new_key] = value[0].decode(encoding)
        # url list parameter
        elif type(value) == list and new_key == 'url-list' or new_key == 'collections':
            torrent_extract[new_key] = list(map(lambda x : x.decode(encoding), value))
        # if type of value is of type list
        elif type(value) == list :
            try:
                torrent_extract[new_key] = list(map(lambda x : x[0].decode(encoding), value))
            except:
                torrent_extract[new_key] = value
        # if type of value if of types byte
        elif type(value) == bytes and new_key != 'pieces':
            try:
                torrent_extract[new_key] = value.decode(encoding)
            except:
                torrent_extract[new_key] = value
        else :
            torrent_extract[new_key] = value

    # torrent extracted metadata
    return torrent_extract

def readTorrentFile(path):
    try :
        torrent_file_raw_extract = bencodepy.decode_from_file(path)

        # check if encoding scheme is given in dictionary
        if b'encoding' in torrent_file_raw_extract.keys():
            encoding = torrent_file_raw_extract[b'encoding'].decode()
        else:
            encoding = 'UTF-8'

        # formatted metadata from the torrent file
        torrent_file_extract = extract_torrent_metadata(torrent_file_raw_extract, encoding)
        
        # check if there is list of trackers 
        if 'announce-list' in torrent_file_extract.keys():
            trackers_url_list = torrent_file_extract['announce-list'] 
        else:
            trackers_url_list = [torrent_file_extract['announce']]

         # file name 
        file_name    = torrent_file_extract['info']['name']
        # piece length in bytes
        piece_length = torrent_file_extract['info']['piece length']
        # sha1 hash concatenation of all pieces of files
        pieces       = torrent_file_extract['info']['pieces']
        # info hash generated for trackers
        info_hash    = generate_info_hash(torrent_file_raw_extract)

        # files is list of tuple of size and path in case of multifile torrent
        files = None

        # check if torrent file contains multiple paths 
        if 'files' in torrent_file_extract['info'].keys():
            # file information - (length, path)
            files_dictionary = torrent_file_extract['info']['files']
            files = [(file_data['length'], file_data['path']) for file_data in files_dictionary]
            file_size = 0
            for file_length, file_path in files:
                file_size += file_length
        else : 
            # file size in bytes 
            file_size = torrent_file_extract['info']['length']

        return trackers_url_list, file_name, file_size, piece_length, pieces, info_hash, files
    except Exception as err:
        print(err)
        sys.exit()


if __name__ == "__main__":
    metadata = readTorrentFile("./input/beautiful-picture.torrent")

    torrentInfo = Metadata(*metadata)
    torrentInfo.display_info()

