07/11/2024:

What is archived?

    Parse MetaInfo file

    Successfully contact tracker and get peers list

    Successfully download individual piece (in single file, single tracker, single peer case)

        Send request message to a seeder (set up by ourselves)

        Get piece message, handle it with a buffer for blocks

        When downloading all, gather the blocks to get a piece

TO DO:

    Continue the case with single tracker, single file, single seeder; aim to download the file successfully

    Test the above case with more test cases

Backlog:

    Expand to multiple peers, each peer can handle downloading and uploading simultaneously

    Handle multiple file cases