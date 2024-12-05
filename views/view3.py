# Download status view
import tkinter as tk
from tkinter import ttk
import threading
import time



def show_view3(parent):
    parent.clear_content()
    parent.label = tk.Label(parent.content_frame, text="Downloading status", bg='lightgray')
    parent.label.pack(fill=tk.X)  # only vertical

    # Create and store references to labels and tables
    parent.labels = []
    parent.tables = []

    for torrent in parent.data.started_torrents:
        label = ttk.Label(parent.content_frame, text=torrent.meta_info.file_name)
        label.pack(padx=10, pady=4, anchor='w')
        parent.labels.append(label)

        Torrent_table = create_torrent_table(parent.content_frame)
        add_torrent_table_row(Torrent_table, torrent)
        Torrent_table.pack(fill=tk.BOTH, expand=True)
        parent.tables.append(Torrent_table)

    start_refresh_thread(parent)

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