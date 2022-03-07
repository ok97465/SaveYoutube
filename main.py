"""Save Youtube."""
# Standard library imports
import subprocess
import argparse
import os
import os.path as osp

# Third party imports
from pytube import YouTube

FOLDER_OUT = "/home/ok97465/비디오"


def title2filename(title: str, unavailable_str: str = "%:/,\\[]<>{}*?") -> str:
    """Convert youtube title to filename."""
    name = "".join([c for c in title if c not in unavailable_str])
    name = name.replace(" ", "_")
    return name


def save_caption(yt: YouTube, path_base: str):
    """Save caption of youtube."""
    path = path_base + ".srt"
    caption_code = ""

    if "en" in yt.captions:
        caption_code = "en"
    elif "a.en" in yt.captions:
        caption_code = "a.en"
    else:
        print("Could not found caption")

    caption = yt.captions[caption_code]
    try:
        with open(path, "w") as fp:
            fp.write(caption.generate_srt_captions())
    except KeyError as e:
        os.remove(path)
        print(f"Could not save srt due to {repr(e)}")


def save_audio(yt: YouTube, filename_base: str):
    """Save audio of youtube."""
    stream = yt.streams.filter(only_audio=True).order_by("abr").last()
    ext = stream.mime_type.split("/")[-1]
    filename_mp3 = filename_base + ".mp3"
    filename_down = filename_base + f".{ext}"
    path_down = osp.join(FOLDER_OUT, filename_down)
    stream.download(output_path=FOLDER_OUT, filename=filename_down)

    print("Downloaded audio.")
    print("Convert audio to mp3.")
    completed = subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "quiet",
            "-hide_banner",
            "-y",
            "-i",
            path_down,
            "-write_id3v1",
            "1",
            "-id3v2_version",
            "3",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "3",
            osp.join(FOLDER_OUT, filename_mp3),
        ],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stdin=subprocess.PIPE,
    )

    if completed.returncode == 0:
        os.remove(path_down)
        print("Complete converting.")


def save_video(yt: YouTube, filename_base: str):
    """Save audio of youtube."""
    stream = yt.streams.filter(mime_type="video/mp4", progressive=True).order_by(
        "resolution"
    )[-1]
    filename_mp4 = filename_base + ".mp4"
    stream.download(output_path=FOLDER_OUT, filename=filename_mp4)


def download_youtube_link(link: str, video_flag: bool):
    """Start the download operation."""
    yt = YouTube(link)

    filename_base = title2filename(yt.title)
    path_base = osp.join(FOLDER_OUT, filename_base)
    save_caption(yt, path_base)
    save_audio(yt, filename_base)
    if video_flag:
        save_video(yt, filename_base)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Youtube using pytube.")
    parser.add_argument("url", type=str, help="URL of youtube")
    parser.add_argument("--video", action="store_true", help="store video of youtube")
    args = parser.parse_args()

    download_youtube_link(args.url, args.video)
