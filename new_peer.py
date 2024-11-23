from Node import *

path = "./input/t2.torrent"
des_path = './out/LBT_' + node.meta_info.file_name
metadata = readTorrentFile(path)
metaInfo = Metadata(*metadata)
node = Node(metaInfo)
node.display_info()

node.start_downloading()