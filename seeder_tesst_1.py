from Node import *
from src_config import *


metadata = readTorrentFile(file_path)
metaInfo = Metadata(*metadata)
node = Node(metaInfo)

# Set up data for seeder:
file_data = read_file_as_bytes(src_parth)
pieces = split_into_pieces(file_data, node.meta_info.piece_length)

for piece_index, complete_piece in enumerate(pieces):
    node.torrent_statistic.downloaded.add((piece_index, complete_piece))
    node.torrent_statistic.num_pieces_downloaded += 1
    node.torrent_statistic.bitfield_pieces.add((piece_index, 1))


node.get_central_tracker()
node.display_info()
node.start_uploading()
