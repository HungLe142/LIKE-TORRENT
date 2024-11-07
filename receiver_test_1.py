from Node import *

path5 = "./input/t2.torrent"
metadata = readTorrentFile(path5)

metaInfo = Metadata(*metadata)
node = Node(metaInfo)



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

except Exception as e: 
    print(f"Error connecting to {ip}:{ip} - {e}")