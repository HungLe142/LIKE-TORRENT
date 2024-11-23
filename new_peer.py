from Node import *

path = "./input/t2.torrent"
metadata = readTorrentFile(path)
metaInfo = Metadata(*metadata)
node = Node(metaInfo)
des_path = './out/LBT_' + node.meta_info.file_name
node.get_central_tracker()
node.display_info()
node.start_downloading()
print('-------------------------------------------')
map_pieces_to_file(node.torrent_statistic.downloaded, node.meta_info.piece_length,des_path,node.meta_info.pieces)