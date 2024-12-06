# Upload file view
import tkinter as tk
from tkinter import ttk 
from tkinter import filedialog
from tkinter import messagebox
import threading


from modules.client import parse_torrent_file_link

def show_view1(parent):
    
    parent.clear_content()
    parent.label = tk.Label(parent.content_frame, text="File uploading", bg='lightgray')
    parent.label.pack(fill=tk.X) # only vertiacal

    paned_window = tk.PanedWindow(parent.content_frame, orient=tk.HORIZONTAL) 
    paned_window.pack(fill=tk.BOTH, expand=True)
    parent.des_entry = None #  For automatic fill the entry of destination link
   
    # Left frame
    left_frame = tk.Frame(paned_window)
    #paned_window.add(left_frame, minsize=600, stretch="always")
    paned_window.add(left_frame, minsize=600)
    Torrent_table = create_torrent_table(left_frame, parent)
    #Torrent_table.pack(fill=tk.BOTH, expand=True)
    #Torrent_table = add_torrent_table_row(Torrent_table, parent.node_list)
    add_torrent_table_row(Torrent_table, parent.data.torrent_list)
    Torrent_table.pack(fill=tk.BOTH, expand=True)

    # Right frame
    right_frame = tk.Frame(paned_window)
    #paned_window.add(right_frame, minsize=100, stretch="never")
    paned_window.add(right_frame, minsize=100)

    label = ttk.Label(right_frame, text="Enter file's link") 
    label.pack(padx=10, pady=4, anchor='center')

    input_frame = create_input_frame(right_frame,parent)
    input_frame.pack(fill=tk.BOTH, expand=True)

    label_1 = ttk.Label(right_frame, text="Choose destination's directory") 
    label_1.pack(padx=10, pady=4, anchor='center')

    start_frame = create_start_frame(right_frame,parent)
    start_frame.pack(fill=tk.BOTH, expand=True)

    paned_window.paneconfigure(left_frame, stretch='always', minsize=600) 
    paned_window.paneconfigure(right_frame, stretch='never', minsize=100)

def create_torrent_table(parent, root):
    torrent_table = ttk.Treeview(parent, columns = ('File name', 'File size', 'Pieces', 'Status' ,'Link'), show = 'headings', height=8)
    torrent_table.heading('File name', text = 'File name')
    torrent_table.heading('File size', text = 'File size', command=lambda: sort_table(torrent_table, 'File size', False))
    torrent_table.heading('Pieces', text = 'Pieces', command=lambda: sort_table(torrent_table, 'Pieces', False))
    torrent_table.heading('Status', text='Status')
    torrent_table.heading('Link', text='Link')


    torrent_table.column('File name', width=82) 
    torrent_table.column('File size', width=82) 
    torrent_table.column('Pieces', width=82) 
    torrent_table.column('Status', width=82)
    torrent_table.column('Link', width=0, stretch=tk.NO)

    torrent_table.bind('<<TreeviewSelect>>', lambda event: on_item_select(event, torrent_table, root))

    return torrent_table

def create_input_frame(parent, root):
    frame = ttk.Frame(parent)
    
    entry = ttk.Entry(frame, width=50) 
    entry.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

    browse_button = ttk.Button(frame, text="Browse", command=lambda: browse_files(entry)) 
    browse_button.grid(row=0, column=1, padx=5, pady=5)

    submit_button = ttk.Button(frame, text="Submit", command=lambda: on_submit(entry, root)) 
    submit_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
    
    frame.grid_columnconfigure(0, weight=1)

    return frame

def create_start_frame(parent, root):
    frame = ttk.Frame(parent)
    
    root.des_entry = ttk.Entry(frame, width=50) 
    root.des_entry.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

    browse_button = ttk.Button(frame, text="Browse", command=lambda: browse_directory(root.des_entry)) 
    browse_button.grid(row=0, column=1, padx=5, pady=5)

    submit_button = ttk.Button(frame, text="Start downloading", command=lambda: on_download(root.des_entry, root, parent)) 
    submit_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='ew')
    
    frame.grid_columnconfigure(0, weight=1)

    return frame

def parse_file(link, root):
        node = parse_torrent_file_link(link)

        with root.torrent_list_lock:
            if node == None or node.meta_info == None:
                # MainView.root
                root.root.after(0, lambda: messagebox.showwarning("Warning", "Cannot parse the link!")) 
                return
                
            for torrent in root.data.torrent_list:
                if torrent.meta_info.file_link == link or (torrent.choosen_tracker == node.choosen_tracker and torrent.meta_info.file_name == node.meta_info.file_name) :
                    root.root.after(0, lambda: messagebox.showwarning("Warning", f"Existed Torrent (Link: {link})")) 
                    return
            root.data.torrent_list.add(node)
        
def on_submit(entry, root): 
    file_link = entry.get()
    
    if file_link == '':
        messagebox.showwarning("Warning", "File's link must not be empty!")
        return

    elif file_link.endswith('.torrent'):
        thread = threading.Thread(target = parse_file, args=(file_link, root)) 
        thread.start()

    else:
        messagebox.showwarning("Warning", "Cannot parse the link, please enter a correct link to a .torrent file!") 
        return
        



def on_download(entry, root,parent):
    file_link = entry.get()
    if file_link == '':
        messagebox.showwarning("Warning", "Destination's link must not be empty!") 
        return

    file_link += '/LTR_'
    root.start_download(file_link) # Root is main_view object!!


def browse_files(entry): 
    file_path = filedialog.askopenfilename() 
    entry.delete(0, tk.END) 
    entry.insert(0, file_path)

def browse_directory(entry): 
    file_path = filedialog.askdirectory() 
    entry.delete(0, tk.END) 
    entry.insert(0, file_path)

def sort_table(tree, col, reverse): 
    l = [(tree.set(k, col), k) for k in tree.get_children('')] 
    l.sort(reverse=reverse, key=lambda t: float(t[0]) if t[0].isdigit() or is_float(t[0]) else t[0]) 
    for index, (val, k) in enumerate(l): 
        tree.move(k, '', index) 
        tree.heading(col, command=lambda: sort_table(tree, col, not reverse)) 
        
def is_float(value): 
    try: 
        float(value) 
        return True 
    except ValueError: return

def on_item_select(event, tree, root): 
    with root.choosen_torrent_lock:
        selected_item = tree.selection()[0] 
        item_data = tree.item(selected_item)['values'] 
        print(f'Dòng được chọn: {item_data}')
        root.data.choosen_torrent = item_data
        if item_data[4] != 'None':
            root.des_entry.delete(0, tk.END) 
            root.des_entry.insert(0, item_data[4])

def add_torrent_table_row(table, torrent_list):
    if not torrent_list:
        return
    for torrent in torrent_list: # torrent with Node type =))
        # Add data
        data = (torrent.meta_info.file_name, 
                torrent.meta_info.file_size,
                torrent.meta_info.piece_count,
                torrent.torrent_statistic.torrent_status,
                torrent.meta_info.des_link
                )
        
        iid = table.insert('', 'end', values=data)

    #return table
