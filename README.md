- Reference: https://github.com/kishanpatel22/bittorrent.git

- Set up:
    + U must have the file "Charlie_Chaplin_Mabels_Strange_Predicament.avi" for starting seeding. U can use the "t2.torrent" file in the "input" folder, paste it into the Transmission Qt Client app (link: https://transmissionbt.com/) and starting download the "Charlie_Chap..." file, put it into the src folder. (Chek the link in "src_config.py")

- How to run? (in single file, single tracker, single peer case)

    + Use the command: Python3 seeder_test_1.py to configure a seeder in computer A

    + Use the command Python3 receiver_test_1.py to start the process

- You can run the test file: print_piece.py to print the data of block 1 from piece 0. This will be the base for comparing with the result obtained from the test case above