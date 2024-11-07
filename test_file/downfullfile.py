# test downloading the file into local by gathering all pieces
import os 
import hashlib



def read_file_as_bytes(file_path):
    with open(file_path, 'rb') as file: 
        return file.read() 

def split_into_pieces(file_data, piece_length): 
    return [file_data[i:i + piece_length] for i in range(0, len(file_data), piece_length)]
    """
    Giải thích split_into_pieces
        Tham số đầu vào:

        file_data: Đây là dữ liệu của tệp, được đọc dưới dạng byte.

        piece_length: Kích thước của mỗi mảnh (piece).

        Cách hoạt động:

        Hàm sử dụng một vòng lặp để chia dữ liệu tệp thành các mảnh.

        range(0, len(file_data), piece_length) tạo ra một chuỗi các giá trị từ 0 đến độ dài của dữ liệu tệp (len(file_data)), mỗi lần tăng thêm piece_length.
        range(start, stop, step)

        file_data[i:i + piece_length] lấy một mảnh dữ liệu từ vị trí i đến i + piece_length.

        for i in range(...) lặp qua tất cả các giá trị của i, tạo ra các mảnh dữ liệu.

        Trả về:

        Hàm trả về một danh sách các mảnh dữ liệu, mỗi mảnh có kích thước piece_length, ngoại trừ mảnh cuối cùng có thể nhỏ hơn nếu tổng độ dài của tệp không chia hết cho piece_length.
    
        Ví dụ:
            Giả sử bạn có một tệp với dữ liệu file_data = b'abcdefghijk' và piece_length = 3.

            Vòng lặp:

            i = 0: Lấy file_data[0:3] → b'abc'

            i = 3: Lấy file_data[3:6] → b'def'

            i = 6: Lấy file_data[6:9] → b'ghi'

            i = 9: Lấy file_data[9:12] → b'jk' (phần dư còn lại)

            Kết quả: [b'abc', b'def', b'ghi', b'jk']
    """

import bencodepy 
def get_piece_hashes(torrent_file_path): 
    with open(torrent_file_path, 'rb') as file: 
        torrent_data = bencodepy.decode(file.read()) 
        info = torrent_data[b'info'] 
        pieces = info[b'pieces'] 
        piece_length = info[b'piece length']
        
        # Lấy danh sách mã băm các mảnh 
        piece_hashes = [pieces[i:i+20] 
        for i in range(0, len(pieces), 20)] 
        return piece_hashes, piece_length # Sử dụng ví dụ 

def verify_piece(piece, piece_index, piece_hashes): 
    # Tính toán SHA1 hash của mảnh 
    sha1_hash = hashlib.sha1(piece).digest() 
    # So sánh với hash từ file .torrent 
    return sha1_hash == piece_hashes[piece_index] 

    """
        Giải thích verify_piece:
            Tham số đầu vào:
                piece: Dữ liệu của mảnh cần xác minh.

                piece_index: Chỉ số của mảnh này trong tệp torrent.

                piece_hashes: Danh sách các mã băm SHA1 của các mảnh từ file .torrent.

            Tính toán SHA1 hash của mảnh:

                python
                sha1_hash = hashlib.sha1(piece).digest()
                Sử dụng hashlib.sha1(piece).digest() để tính toán giá trị băm SHA1 của mảnh dữ liệu. Giá trị này sẽ là một chuỗi byte dài 20 byte.

            So sánh với hash từ file .torrent:

            python
                return sha1_hash == piece_hashes[piece_index]
                So sánh giá trị SHA1 hash của mảnh tính toán được (sha1_hash) với mã băm tương ứng của mảnh đó trong piece_hashes.

                piece_hashes[piece_index] là mã băm của mảnh ở vị trí piece_index trong danh sách các mã băm từ file .torrent.

            Nếu hai giá trị băm này bằng nhau (==), hàm trả về True, nghĩa là mảnh hợp lệ. Ngược lại, hàm trả về False.
    """

def map_pieces_to_file(pieces, piece_length, file_path, piece_hashes): 
    try: 
        # Cố gắng mở tệp trong chế độ đọc ghi 
        with open(file_path, 'r+b') as f: 
            pass 
    except FileNotFoundError: 
        # Nếu tệp không tồn tại, tạo tệp mới 
        with open(file_path, 'wb') as f: 
            pass 
        
    # Tiếp tục với việc ghi các mảnh vào tệp 
    with open(file_path, 'r+b') as f: 
        for index, piece in pieces: 
            if verify_piece(piece, index, piece_hashes): 
                offset = index * piece_length 
                f.seek(offset) 
                f.write(piece)
                # TO DO: Update downloaded, get a new piece
            else: 
                print(f"The {index} fragment does not match the hash, it is ignored.")
    """
        Giải thích map_pieces_to_file:
            Mở tệp để ghi (ghi kèm):

                python
                with open(file_path, 'r+b') as f:
                Mở tệp ở chế độ "read + binary" (r+b). Chế độ này cho phép đọc và ghi vào tệp đã tồn tại.

                Lặp qua các mảnh:

                python
                for index, piece in enumerate(pieces):
                Sử dụng enumerate để lặp qua danh sách các mảnh pieces. Mỗi mảnh có một chỉ số index và dữ liệu piece.

                Kiểm tra tính toàn vẹn của mảnh:

                python
                if verify_piece(piece, index, piece_hashes):
                Gọi hàm verify_piece để kiểm tra mã băm của mảnh có khớp với mã băm từ piece_hashes hay không. Nếu khớp, tiếp tục với bước sau, nếu không, bỏ qua mảnh này.

                Tính toán vị trí offset trong tệp:

                python
                offset = index * piece_length
                Tính toán vị trí bắt đầu trong tệp dựa trên chỉ số index và độ dài của mảnh piece_length.

                Ghi mảnh vào tệp:

                python
                f.seek(offset)
                f.write(piece)
                Sử dụng f.seek(offset) để di chuyển con trỏ tệp đến vị trí offset và f.write(piece) để ghi mảnh vào tệp tại vị trí đó.

                Xử lý mảnh không hợp lệ:

                python
                else:
                    print(f"Mảnh {index} không khớp với mã băm, bị bỏ qua.")
                Nếu mã băm của mảnh không khớp, in ra thông báo và bỏ qua mảnh này.
    """



torrent_file_path = './input/t2.torrent' 
file_source = "./src/Charlie_Chaplin_Mabels_Strange_Predicament.avi" 
file_data = read_file_as_bytes(file_source)
print("FIle data:")
file_data = read_file_as_bytes(file_source)
pieces = split_into_pieces(file_data, 131072)
for i, data in enumerate(pieces):
    if i == 0:
        print((data))
        break

#map_pieces_to_file(pieces, piece_length, file_path, piece_hashes)


