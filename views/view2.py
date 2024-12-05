# Peer list view
import tkinter as tk
from tkinter import ttk
#from views.view1 import on_item_select

def show_view2(parent):

    parent.clear_content()
    parent.label = tk.Label(parent.content_frame, text="Peer list", bg='lightgray')
    parent.label.pack(fill=tk.X) # only vertiacal

    Torrent_table = create_torrent_table(parent.content_frame)
    add_torrent_table_row(Torrent_table, parent.data.torrent_list)
    Torrent_table.pack(fill=tk.BOTH, expand=True)


def create_torrent_table(parent):
    torrent_table = ttk.Treeview(parent, columns = ('File name', 'Tracker','Peer list'), show = 'headings', height=8)
    torrent_table.heading('File name', text = 'File name')
    torrent_table.heading('Tracker', text = 'Tracker')
    torrent_table.heading('Peer list', text = 'Peer list')

    torrent_table.column('File name', width=82) 
    torrent_table.column('Tracker', width=82) 
    torrent_table.column('Peer list', width=200) 

    torrent_table.bind('<<TreeviewSelect>>', lambda event: on_item_select())

    return torrent_table

def add_torrent_table_row(table, torrent_list):
    if not torrent_list:
        return
    for torrent in torrent_list:
        # Add data
        if torrent.peer_list == []:
            peer_list = 'None'
        else: 
            peer_list = torrent.peer_list

        data = (torrent.meta_info.file_name, 
                torrent.choosen_tracker,
                peer_list
                )
        
        iid = table.insert('', 'end', values=data)

def on_item_select():
    pass