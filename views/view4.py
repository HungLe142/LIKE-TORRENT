# Upload status view
import tkinter as tk
from tkinter import ttk, messagebox
from views.view1 import browse_files
from modules.file_processing import readTorrentFile
import binascii
import threading


def show_view4(parent):
    
    parent.clear_content()
    parent.label = tk.Label(parent.content_frame, text="Uploading status", bg='lightgray')
    parent.label.pack(fill=tk.X) # only vertiacal

    paned_window = tk.PanedWindow(parent.content_frame, orient=tk.HORIZONTAL) 
    paned_window.pack(fill=tk.BOTH, expand=True)
    parent.tables = []
    parent.textbutton4 = 'Start'

    # Left frame
    left_frame = tk.Frame(paned_window)
    paned_window.add(left_frame, minsize=600)
    
    action_button = ttk.Button(left_frame, text=parent.textbutton4, command=lambda: actionButton_handle(parent))
    action_button.pack()

    Torrent_table = create_torrent_table(left_frame, parent)
    add_torrent_table_row(Torrent_table, parent.data.torrent_list)
    Torrent_table.pack(fill=tk.BOTH, expand=True)
    parent.tables.append(Torrent_table)

    # Right frame
    right_frame = tk.Frame(paned_window)
    paned_window.add(right_frame, minsize=100)

    label = ttk.Label(right_frame, text="Enter source's link") 
    label.pack(padx=10, pady=4, anchor='center')

    input_frame1 = create_input_frame0(right_frame,parent)
    input_frame1.pack(fill=tk.BOTH, expand=True)


    start_refresh_thread(parent, left_frame)

def start_refresh_thread(parent, left_frame):
    thread = threading.Thread(target=keep_refresh_view_4, args=(parent,left_frame))
    thread.start()

def keep_refresh_view_4(parent, left_frame): 
    with parent.flag_lock:
        if parent.view4_flag == False:
            return
        
        all_torrent_stop = True
        for torrent in parent.data.torrent_list:
            if torrent.torrent_statistic.torrent_status_up == 'Running':
                all_torrent_stop = False
                break
        if all_torrent_stop:
            return
        
        # Xóa các bảng hiện tại
        for table in parent.tables: 
            table.destroy() 
        parent.tables.clear()

        # Tạo lại các bảng
        # if torrent.torrent_statistic.torrent_status_up == 'Stopped':
        #    continue 
        Torrent_table = create_torrent_table(left_frame, parent)  # Sửa thứ tự tham số
        add_torrent_table_row(Torrent_table, parent.data.torrent_list) 
        Torrent_table.pack(fill=tk.BOTH, expand=True) 
        parent.tables.append(Torrent_table) 
        
        parent.root.after(2000, keep_refresh_view_4, parent, left_frame)  # Sửa thứ tự tham số



def create_input_frame0(parent, root): # 
    frame = ttk.Frame(parent)
    
    entry = ttk.Entry(frame, width=50) 
    entry.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

    browse_button = ttk.Button(frame, text="Browse", command=lambda: browse_files(entry)) 
    browse_button.grid(row=0, column=1, padx=5, pady=5)

    submit_button = ttk.Button(frame, text="Start uploading", command=lambda: on_upload(entry, root, parent)) 
    submit_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
    
    frame.grid_columnconfigure(0, weight=1)

    return frame

def on_upload(entry, root, parent): 
    file_link = entry.get()
    if file_link == '':
        messagebox.showwarning("Warning", "You need to add a link to your source file for starting.")
        return 

    with root.choosen_torrent_lock:
        if not root.data.choosen_torrent4:
            messagebox.showwarning("Warning", "You need to choose a torrent for uploading. No torrent show? Back to Torrent view and submit a file end with .torrent!") 
            return

    if not file_link.endswith('.txt'):
        messagebox.showwarning("Warning", "Please submit a suitable text file") 
        return

    with root.choosen_torrent_lock:
        messagebox.showwarning("Warning", "Please provide a correct data file. Please don't spawn trash data. Thank you!") 
        expected_info_hash = root.data.choosen_torrent4[4]
        info_hash_bytes = binascii.unhexlify(expected_info_hash)

        with root.torrent_list_lock:
            
            for torrent in root.data.torrent_list:
                if torrent.meta_info.info_hash == info_hash_bytes:
                    torrent.upload_controller(file_link, root)
                    break
            

def create_torrent_table(parent, root):
    torrent_table = ttk.Treeview(parent, columns = ('File name', 'Tracker', 'Up', 'Status', 'Info_hash'), show = 'headings', height=8)
    torrent_table.heading('File name', text = 'File name')
    torrent_table.heading('Tracker', text = 'Tracker')
    torrent_table.heading('Up', text = 'Up (piece)')
    torrent_table.heading('Status', text = 'Status')
    torrent_table.heading('Info_hash', text='Info_hash')

    torrent_table.column('File name', width=82) 
    torrent_table.column('Tracker', width=82) 
    torrent_table.column('Up', width=82) 
    torrent_table.column('Status', width=82)
    torrent_table.column('Info_hash', width=0, stretch=tk.NO)

    torrent_table.bind('<<TreeviewSelect>>', lambda event: on_item_select(event, torrent_table, root))

    return torrent_table

def add_torrent_table_row(table, torrent_list):
    if not torrent_list:
        return
    for torrent in torrent_list: # torrent with Node type =))
        # Add data
        info_hash_hex = binascii.hexlify(torrent.meta_info.info_hash).decode('utf-8')
        print("Fix bug view 4, updoaded pieces: ", torrent.torrent_statistic.num_pieces_uploaded)
        data = (torrent.meta_info.file_name, 
                torrent.choosen_tracker,
                torrent.torrent_statistic.num_pieces_uploaded,
                torrent.torrent_statistic.torrent_status_up,
                info_hash_hex
                )
        
        iid = table.insert('', 'end', values=data)

def on_item_select(event, tree, root): 
    selected_item = tree.selection()[0] 
    item_data = tree.item(selected_item)['values'] 
    print(f'Dòng được chọn: {item_data}')
    with root.choosen_torrent_lock:
        root.data.choosen_torrent4 = item_data

        if item_data[3] == 'Running':
            root.textbutton4 = 'Stop'
        elif item_data[3] == 'Stopped':
             root.textbutton4 = 'Start'
        else:
            root.textbutton4 = ''

def actionButton_handle(parent):
    if parent.data.choosen_torrent4 is None:
        messagebox.showwarning("Warning", "You need to choose a torrent for start Uploading")
        return

    with parent.torrent_list_lock:
            expected_info_hash = parent.data.choosen_torrent4[4]
            info_hash_bytes = binascii.unhexlify(expected_info_hash)
            for torrent in parent.data.torrent_list:
                if torrent.meta_info.info_hash == info_hash_bytes:
                    if torrent.torrent_statistic.num_pieces_downloaded == 0:
                        messagebox.showwarning("Warning","You currently don't have any pieces, please use the script file or start downloading first!")
                        return
                    if torrent.torrent_statistic.torrent_status_up == 'Unstarted' or torrent.torrent_statistic.torrent_status_up == 'Stopped':
                        thread = threading.Thread(target=torrent.start_uploading)
                        thread.start()
                        parent.textbutton4 = "Stop"

                    elif torrent.torrent_statistic.torrent_status_up == 'Running':
                        torrent.torrent_statistic.torrent_status_up == 'Stopped'
                        parent.textbutton4 = "Start"