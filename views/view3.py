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
        action_button = ttk.Button(container, text=parent.status, command=lambda: actionButton_handle(torrent,action_button))
        #pause_button['font'] = font.Font(weight='bold')  
        action_button.pack(side="right", padx=10)  # Place it on the right
        parent.buttons.append(action_button)

        # Create and add torrent table
        Torrent_table = create_torrent_table(parent.content_frame)
        add_torrent_table_row(Torrent_table, torrent)
        Torrent_table.pack(fill=tk.BOTH, expand=True)
        parent.tables.append(Torrent_table)

    start_refresh_thread(parent)

def actionButton_handle(torrent, button):
    if button['text'] == "Stop":
        stop_download_torrent(torrent)
        button['text'] = "Start"
    else:
        start_download_torrent(torrent)
        button['text'] = "Stop"

def stop_download_torrent(parent):
    print(f"Stopping download torrent: {parent.meta_info.file_name}")
    parent.torrent_statistic.torrent_status = "Stopped"
    parent.status = "Start"

def start_download_torrent(parent):
    print(f"Starting download torrent: {parent.meta_info.file_name}")
    parent.torrent_statistic.torrent_status = "Starting"
    parent.status = "Stop"

def keep_refresh_view_3(parent):
    if parent.view3_flag:
        # Refresh existing labels and tables
        if parent.data.started_torrents == []:
            return
        for i, torrent in enumerate(parent.data.started_torrents):
            parent.labels[i].config(text=torrent.meta_info.file_name)
            # Clear and repopulate the table
            clear_torrent_table(parent.tables[i])
            add_torrent_table_row(parent.tables[i], torrent)
        
        # Schedule the next call to this function
        parent.root.after(2000, lambda: keep_refresh_view_3(parent))

def clear_torrent_table(table): 
    for item in table.get_children(): 
        table.delete(item)
def start_refresh_thread(parent):
    # Start the refresh in a separate thread
    thread = threading.Thread(target=keep_refresh_view_3, args=(parent,))
    thread.start()



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