07/11/2024:

What is archived?

    Parse MetaInfo file

    Successfully contact tracker and get peers list

    Successfully download individual piece (in single file, single tracker, single peer case)

        Send request message to a seeder (set up by ourselves)

        Get piece message, handle it with a buffer for blocks

        When downloading all, gather the blocks to get a piece
    
    Successfully download the file in t2.torrent (case 1 seeder, 1 tracker, 1 file)

TO DO:

    Test the above case with more test cases

Backlog:

    Expand to multiple peers, each peer can handle downloading and uploading simultaneously

    Handle multiple file cases

23/11/2024:

TO DO:
    - Check network config with virtualBox -> OK
    - Make scenarious: set up peers, each of them has different parts of file.
    - Seeding activites:
        + After an interval of time (may be a minute), each peer need to contact tracker for keep aliving as seeder?
        + Send Bitfield message for each peer when start connection
    - Choosing pieces algorithm: downloading in turn, each tủn base on peer-list receiving from the tracker
        + Synchronizing technique (mutex lock, simaphore,...) for protecting the downloaded list, bitfield list when downloading from multi peers.
        + After get all pieces in the connection with a peer, disconnect with it?
        + Each 1 minutes, contact trackers for new peer list.
        + Contact peers in the list for receiving algorithm
            * After receiving the bitfield message, compare and try to get pieces we don't have?
        + 
    - Print report:
        + print line: Get which piece of file from which peer
        + 