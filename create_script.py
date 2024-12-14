from modules.client import *
import base64

def read_and_save_pieces(file_link, piece_length, output_file):
    # Open the input file and output file
    with open(file_link, 'rb') as f, open(output_file, 'w') as out:
        index = 0
        for i in range(500):
            if i == 0 or i == 4 or i == 2:
                # Read a piece of data
                piece = f.read(piece_length)
                if not piece:
                    break
                
                # Encode the piece using base64
                encoded_piece = base64.b64encode(piece).decode('utf-8')
                
                # Write the index and encoded data to the output file
                out.write(f"{index} {encoded_piece}\n")
                index += 1

# modify link here
torrent_link = "./script_data/t1/t1.torrent"
file_link = "./script_data/t1/A-Brief-Review-of-NatureInspired-Algorithms-for-Optimization.pdf"
output_file = "./scrip_data1.txt"

node = parse_torrent_file_link(torrent_link)
node.display_info()
piece_length = node.meta_info.piece_length

read_and_save_pieces(file_link, piece_length, output_file)