import requests
import bencodepy


def get_HTTP_response(tracker_url, Node, event = None):
    request_parameters = {
        'info_hash' : Node.meta_info.info_hash,
        'peer_id'   : Node.peer_id,
        'port'      : Node.client_port,
        'uploaded'  : Node.torrent_statistic.num_pieces_uploaded,
        'downloaded': Node.torrent_statistic.num_pieces_downloaded,
        'left'      : Node.torrent_statistic.num_pieces_left,
        'compact'   : 1,
        'event'     : event, # must be one of started, completed, stopped. If None, need resending
        'ip'        : Node.client_IP
    }
    try:
        bencoded_response = requests.get(tracker_url, request_parameters, timeout=5)
        raw_response_dict = bencodepy.decode(bencoded_response.content)        
        return raw_response_dict

    except Exception as error_msg:
        # cannont establish a connection with the tracker
        print(error_msg)
        return False

def parse_http_tracker_response(raw_response_dict):
    import struct

    # list of peers form the participating the torrent
    peers_list = [] 
    complete = 0 
    incomplete = 0 
    tracker_id = None

    if b'peers' in raw_response_dict:
        # extract the raw peers data 
        raw_peers_data = raw_response_dict[b'peers']

        # ensure peers data is in bytes format
        if isinstance(raw_peers_data, bytes):
            # create a list of each peer information which is of 6 bytes
            raw_peers_list = [raw_peers_data[i : 6 + i] for i in range(0, len(raw_peers_data), 6)]
            # extract all the peer id, peer IP and peer port
            for raw_peer_data in raw_peers_list:
                # extract the peer IP address 
                peer_IP = ".".join(str(int(a)) for a in raw_peer_data[0:4])
                # extract the peer port number
                peer_port = struct.unpack('!H', raw_peer_data[4:6])[0]
                # append the (peer IP, peer port)
                peers_list.append((peer_IP, peer_port))
        else:
            # handle case where peers data might be a dictionary
            for peer in raw_response_dict[b'peers']:
                peer_IP = peer[b'ip'].decode('utf-8')
                peer_port = peer[b'port']
                peers_list.append((peer_IP, peer_port))

    # number of peers with the entire file aka seeders
    if b'complete' in raw_response_dict:
        complete = raw_response_dict[b'complete']

    # number of non-seeder peers, aka "leechers"
    if b'incomplete' in raw_response_dict:
        incomplete = raw_response_dict[b'incomplete']
    
    # tracker id must be sent back by the user on announcement
    if b'tracker id' in raw_response_dict:
        tracker_id = raw_response_dict[b'tracker id']

    return peers_list, complete, tracker_id

