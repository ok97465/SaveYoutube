"""Save Youtube."""
# Standard library imports
import argparse
import os.path as osp

# Local imports
from helper_youtube import download_youtube_link

FOLDER_OUT = "/home/ok97465/비디오"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Youtube using pytube.")
    parser.add_argument(
        "url_or_filename", type=str, help="URL of youtube Or filename including urls"
    )
    parser.add_argument(
        "--video_only", action="store_true", help="store only video of youtube"
    )
    parser.add_argument(
        "--audio_only", action="store_true", help="store only audio of youtube"
    )
    parser.add_argument("--list", action="store_true", help="")
    args = parser.parse_args()

    if args.list:
        if osp.isfile(args.url_or_filename) is False:
            raise RuntimeError("Need filename including urls.")
        with open(args.url_or_filename, "r") as fp:
            urls = fp.readlines()
            for url in urls:
                if len(url.strip()) == 0:
                    continue
                print(f"Download {url}")
                download_youtube_link(url, args.video_only, args.audio_only, FOLDER_OUT)
    else:
        download_youtube_link(
            args.url_or_filename, args.video_only, args.audio_only, FOLDER_OUT
        )

    print("Download complete.")
