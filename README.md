- Reference: https://github.com/kishanpatel22/bittorrent.git

- Set up:
    + U must have the file "Charlie_Chaplin_Mabels_Strange_Predicament.avi" for starting seeding. U can use the "t2.torrent" file in the "input" folder, paste it into the Transmission Qt Client app (link: https://transmissionbt.com/) and starting download the "Charlie_Chap..." file, put it into the src folder. (Chek the link in "src_config.py")
    + Recommend creat an empty folder "out" (Chek the link in "receiver_test_1.py)

- How to run? (in single file, single tracker, single peer case)
    + Store the source code in 2 computer (or using virtual machine technique)
    + Use the command: Python3 seeder_test_1.py to configure a seeder in computer A
    + Check client_IP, client_Port of Computer A, paste it into fields: ip, port in "receiver_test_1.py"
    + Use the command Python3 receiver_test_1.py to start the process
    + Result: successfully downloading the Charlie_Chaplin_Mabels_Strange_Predicament.avi" in the computer B.
- You can run the test file: print_piece.py to print the data of block 1 from piece 0. This will be the base for comparing with the result obtained from the test case above