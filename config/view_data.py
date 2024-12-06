class view_data():
    def __init__(self):
        self.torrent_list = set([])
        self.choosen_torrent = None # For UI in view 1
        self.choosen_torrent4 = None # For UI in View 4
        self.started_torrents = set([])
        self.up_torrents = set([]) # Torrents that your side starts uploading file.