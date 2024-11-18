from torrentool.api import Torrent

def create_torrent(input_path, tracker_url, output_file):
    torrent = Torrent.create_from(input_path)
    torrent.announce_urls = tracker_url
    # torrent.meta['info']['piece length'] = 16*1024
    if output_file[len(output_file)-8:] != ".torrent":
        correct_output = output_file + ".torrent"
        torrent.to_file(correct_output)
    else:
        torrent.to_file(output_file)

    print(f"Torrent file created at: {output_file}")


