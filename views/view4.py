# Upload status view
import tkinter as tk

def show_view4(parent):
    
    parent.clear_content()
    parent.label = tk.Label(parent.content_frame, text="Uploading status", bg='lightgray')
    parent.label.pack(fill=tk.X) # only vertiacal