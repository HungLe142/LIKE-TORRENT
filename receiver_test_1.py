from Node import *

path5 = "./input/t2.torrent"
metadata = readTorrentFile(path5)

metaInfo = Metadata(*metadata)
node = Node(metaInfo)
# IP and Port from seeder config
ip = '192.168.1.37' 
port = 6881
des_path = './out/clone_' + node.meta_info.file_name
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    client_socket.settimeout(5) # Set timeout to 5 seconds
    client_socket.connect((ip, port))

    #client_socket.sendall(node.handshake_msg) 
    
    raw_bitfield_response = client_socket.recv(1024) 
    bitfield_response = decode_bitfield_message(raw_bitfield_response)
    #print(f"Bitfield response from {ip}:{port} - {bitfield_response}") 
    
    for piece_index, valid in enumerate(bitfield_response):
        if valid:
            #thread = threading.Thread(target=self.getPiece, args=(client_socket, piece_index))
            #thread.start()
            node.getPiece(client_socket, piece_index)
    print("------------------------------------------------")
    for(index, bit) in node.torrent_statistic.bitfield_pieces:
        if bit == 0:
            node.getPiece(client_socket, index)
    uncomplete = False
    for(index, bit) in node.torrent_statistic.bitfield_pieces:
        if bit == 0:
            print("Don't have piece: ", index)
            uncomplete = True
    if uncomplete:
        return False
    map_pieces_to_file(node.torrent_statistic.downloaded, node.meta_info.piece_length,des_path)
except Exception as e: 
    print(f"Error connecting to {ip}:{ip} - {e}")