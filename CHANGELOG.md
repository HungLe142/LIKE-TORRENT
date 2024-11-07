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