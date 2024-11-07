from Node import *

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

# Print block 1 of piece 0
for index, data in node.torrent_statistic.downloaded:
    if(index == 0):
        print(data[node.meta_info.block_length:node.meta_info.block_length*2])

# Other way:
"""
file_path = "./input/t2.torrent"
src_parth = "./src/Charlie_Chaplin_Mabels_Strange_Predicament.avi"  
metadata = readTorrentFile(file_path)
metaInfo = Metadata(*metadata)
node = Node(metaInfo)

file_data = read_file_as_bytes(src_parth)
pieces = split_into_pieces(file_data, node.meta_info.piece_length)

data = pieces[0]

print(data[0:0 + node.meta_info.block_length])
print("------------------------------------------------------")
print(data[node.meta_info.block_length:node.meta_info.block_length*2])
"""