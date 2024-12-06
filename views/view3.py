# Download status view
import tkinter as tk
from tkinter import ttk
import threading
from tkinter import font
import time



def show_view3(parent):
    parent.clear_content()
    parent.label = tk.Label(parent.content_frame, text="Downloading status", bg='lightgray')
    parent.label.pack(fill=tk.X)

    # Create and store references to containers, buttons, and tables
    parent.containers = []  # For storing each file row container
    parent.buttons = []  # For storing start/stop button
    parent.tables = []
    parent.progress_bars = []
    parent.status="Stop"

    for torrent in parent.data.started_torrents:
        # Create a container for the file name and the button
        container = tk.Frame(parent.content_frame)
        container.pack(fill=tk.X, padx=10, pady=4)
        parent.containers.append(container)

        # File name label 
        label = ttk.Label(container, text=torrent.meta_info.file_name)
        label.pack(side="left", anchor="w")

        # Add start/stop button
        if torrent.torrent_statistic.torrent_status == "Finished" or torrent.torrent_statistic.torrent_status != "Stopped":
            pass

        elif torrent.torrent_statistic.torrent_status == "Downloading":
            parent.status = "Stop"
        
        else:
            parent.status = "Start"

        # Add progress bar 
        progress = ttk.Progressbar(container, orient="horizontal", mode="determinate") 
        progress.pack(fill=tk.X, padx=10, pady=4) 
        parent.progress_bars.append(progress)
        
        action_button = ttk.Button(container, text=parent.status, command=lambda: actionButton_handle(torrent,action_button, parent))
        #pause_button['font'] = font.Font(weight='bold')  
        action_button.pack(side="right", padx=10)  # Place it on the right
        parent.buttons.append(action_button)

        # Create and add torrent table
        Torrent_table = create_torrent_table(parent.content_frame)
        add_torrent_table_row(Torrent_table, torrent)
        Torrent_table.pack(fill=tk.BOTH, expand=True)
        parent.tables.append(Torrent_table)

    start_refresh_thread(parent)

def update_progress_bars(parent): 
    for index, torrent in enumerate(parent.data.started_torrents): 
        total_pieces = torrent.meta_info.file_size 
        downloaded_pieces = torrent.torrent_statistic.num_pieces_downloaded 
        progress_value = (downloaded_pieces / total_pieces) * 100 if total_pieces > 0 else 0 
        parent.progress_bars[index].config(value=progress_value)

def actionButton_handle(torrent, button, root):
    if torrent.torrent_statistic.torrent_status == "Finished": 
        button.grid_remove()    
    elif button['text'] == "Stop":
        stop_download_torrent(torrent, root)
        button['text'] = "Start"
    else:
        start_download_torrent(torrent)
        button['text'] = "Stop"

def stop_download_torrent(parent, root):
    print(f"Stopping download torrent: {parent.meta_info.file_name}")
    parent.torrent_statistic.torrent_status = "Stopped"
    root.data.started_torrents.clear()


def start_download_torrent(parent):
    print(f"Starting download torrent: {parent.meta_info.file_name}")
    link = parent.meta_info.des_link
    parent.start_downloading(link)

def start_refresh_thread(parent):
    # Start the refresh in a separate thread
    thread = threading.Thread(target=keep_refresh_view_3, args=(parent,))
    thread.start()

def keep_refresh_view_3(parent): 

    with parent.flag_lock:
        if parent.view3_flag == False:
            return
        
        all_torrent_stop = True
        for torrent in parent.data.torrent_list:
            if torrent.torrent_statistic.torrent_status == "Downloading":
                all_torrent_stop = False
                break
        if all_torrent_stop:
            return
        
        for table in parent.tables: 
            table.destroy() 
        parent.tables.clear()

        for torrent in parent.data.started_torrents: 
            if torrent.torrent_statistic.torrent_status == "Finished": 
                continue 
            update_progress_bars(parent)
            Torrent_table = create_torrent_table(parent.content_frame) 
            add_torrent_table_row(Torrent_table, torrent) 
            Torrent_table.pack(fill=tk.BOTH, expand=True) 
            parent.tables.append(Torrent_table) 
        
        parent.root.after(2000, keep_refresh_view_3, parent)

def create_torrent_table(parent):
    torrent_table = ttk.Treeview(parent, columns = ('Peer', 'Port', 'Status', 'Down' ), show = 'headings', height=8)
    torrent_table.heading('Peer', text = 'Peer')
    torrent_table.heading('Port', text = 'Port')
    torrent_table.heading('Status', text = 'Status')
    torrent_table.heading('Down', text = 'Down')

    torrent_table.column('Peer', width=200)
    torrent_table.column('Port', width=200) 
    torrent_table.column('Status', width=200) 
    torrent_table.column('Down', width=200) 

    torrent_table.bind('<<TreeviewSelect>>', lambda event: on_item_select())

    return torrent_table

def add_torrent_table_row(table, torrent):
    peer_list = torrent.torrent_statistic.peer_data
    for peer in peer_list:
        data = (peer['ip'], 
                peer['port'],
                peer['down_status'],
                peer['down']
                )
        iid = table.insert('', 'end', values=data)
    
def on_item_select():
    pass