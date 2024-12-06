import tkinter as tk
from tkinter import messagebox
from modules.client import Node
import threading
from config.view_data import view_data
from views.view1 import show_view1
from views.view2 import show_view2
from views.view3 import show_view3
from views.view4 import show_view4


class MainView:
    def __init__(self, root):
        self.data = view_data()
        self.flag_lock = threading.Lock()
        self.torrent_list_lock = threading.Lock()
        self.choosen_torrent_lock = threading.Lock()   # Use for protecting in view 4, protect in torrent verification  
        self.root = root
        self.root.title("LIKE TORRENT")
        self.root.geometry("900x600")

        # Frame bên trái (sidebar) cho điều hướng
        self.sidebar_frame = tk.Frame(root, width=200, bg='lightgray')
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Frame bên phải cho nội dung chính
        self.content_frame = tk.Frame(root)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Nội dung sidebar
        self.label_nav = tk.Label(self.sidebar_frame, text="Navigation", bg='lightgray')
        self.label_nav.pack(pady=10)
        self.button_view1 = tk.Button(self.sidebar_frame, text="Torrents dash board", command=lambda:self.show_view1())
        self.button_view1.pack(pady=5, fill=tk.X)
        self.button_view2 = tk.Button(self.sidebar_frame, text="Peer list", command=lambda:self.show_view2())
        self.button_view2.pack(pady=5, fill=tk.X)
        self.button_view3 = tk.Button(self.sidebar_frame, text="Downloading status", command=lambda:self.show_view3())
        self.button_view3.pack(pady=5, fill=tk.X)
        self.button_view4 = tk.Button(self.sidebar_frame, text="Uploading status", command=lambda:self.show_view4())
        self.button_view4.pack(pady=5, fill=tk.X)

        # Nội dung chính (mặc định hiển thị View 1)
        self.show_view1()

    def show_view1(self):
        with self.flag_lock:
            self.view1_flag = True
            self.view2_flag = False
            self.view3_flag = False
            self.view4_flag = False
            show_view1(self)

    def show_view2(self):
        with self.flag_lock:
            self.view1_flag = False
            self.view2_flag = True
            self.view3_flag = False
            self.view4_flag = False
            show_view2(self)

    def show_view3(self):
        with self.flag_lock:
            self.view1_flag = False
            self.view2_flag = False
            self.view3_flag = True
            self.view4_flag = False
            show_view3(self)

    def show_view4(self):
        with self.flag_lock:
            self.view1_flag = False
            self.view2_flag = False
            self.view3_flag = False
            self.view4_flag = True
            show_view4(self)

    def clear_content(self):
        with self.choosen_torrent_lock:
            self.data.choosen_torrent = None
            self.data.choosen_torrent4 = None
            for widget in self.content_frame.winfo_children():
                widget.destroy()

    def start_download(self, des_link):
        with self.choosen_torrent_lock:
            if not self.data.choosen_torrent: 
                # Hiển thị hộp thoại pop-up nếu không có torrent được chọn 
                messagebox.showwarning("Warning", "You need to choose a torrent to start downloading. If no torrent appears, please submit a .torrent file!") 
                return

        for torrent in self.data.torrent_list:
            with self.choosen_torrent_lock:
                if torrent.meta_info.file_size == self.data.choosen_torrent[1] and  torrent.meta_info.file_name == self.data.choosen_torrent[0]:
                    self.data.started_torrents.add(torrent)
                    torrent.start_downloading(des_link)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainView(root)
    root.mainloop()
