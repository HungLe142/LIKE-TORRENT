import threading
from queue import Queue

# Danh sách các peer
peers = ['peer1', 'peer2', 'peer3', 'peer4', 'peer5']
# Queue để quản lý các piece cần tải
piece_queue = Queue()
# Khóa để đồng bộ hóa
piece_lock = threading.Lock()
# Biến để theo dõi các piece đã được tải
downloaded_pieces = set()

# Hàm mô phỏng quá trình tải piece
def download_piece(peer, piece):
    with piece_lock:
        if piece in downloaded_pieces:
            return 
        # Đây là nơi bạn sẽ triển khai logic tải piece từ peer
        print(f"{peer} đang tải piece {piece}")
        # Mô phỏng thời gian tải
        import time
        time.sleep(1)
        # Đánh dấu piece đã được tải
        downloaded_pieces.add(piece)
        print(f"{peer} đã tải xong piece {piece}")

# Hàm xử lý luồng
def peer_worker(peer):
    while not piece_queue.empty():
        piece = piece_queue.get()
        download_piece(peer, piece)
        piece_queue.task_done()

# Thêm các piece cần tải vào queue
pieces_to_download = [9, 10, 11, 12]
for piece in pieces_to_download:
    piece_queue.put(piece)

# Tạo và khởi động các luồng
threads = []
for peer in peers:
    t = threading.Thread(target=peer_worker, args=(peer,))
    t.start()
    threads.append(t)

# Chờ tất cả các luồng hoàn thành
for t in threads:
    t.join()

print("Tất cả các piece đã được tải xong:", downloaded_pieces)
