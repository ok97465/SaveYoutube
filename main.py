"""Save Youtube."""
# Standard library imports
import argparse
import os
import os.path as osp
import subprocess
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape

# Third party imports
from pytube import YouTube

FOLDER_OUT = "/home/ok97465/비디오"


def title2filename(title: str, unavailable_str: str = "%:/,\\[]<>{}*?") -> str:
    """Convert youtube title to filename."""
    name = "".join([c for c in title if c not in unavailable_str])
    name = name.replace(" ", "_")
    return name


@dataclass
class CapInfo:
    """Dataclass for caption information."""

    start_time_int: int
    end_time_int: int
    caption: str


def ms_time_to_srt_time_format(d: int) -> str:
    """Convert decimal durations into proper srt format.

    ms_time_to_srt_time_format(3890) -> '00:00:03,890'
    """
    sec, ms = d // 1000, d % 1000
    time_fmt = time.strftime("%H:%M:%S", time.gmtime(sec))

    # if ms < 100 we get ...,00 or ...,0 when expected ...,000
    ms = "0" * (3 - len(str(ms))) + str(ms)

    return f"{time_fmt},{ms}"


def xml_caption_to_srt(xml_captions: str) -> str:
    """Convert xml caption tracks to "SubRip Subtitle (srt)".

    :param str xml_captions:
        XML formatted caption tracks.
    """
    tree = ET.fromstring(xml_captions)
    root = tree.find("body")

    cap_info_list = []

    for i, child in enumerate(list(root)):
        text = "".join(child.itertext()).strip()
        if not text:
            continue

        caption = unescape(
            text.replace("\n", " ").replace("  ", " "),
        )
        try:
            duration = int(child.attrib["d"])  # in milliseconds
        except KeyError:
            duration = 0

        start = int(child.attrib["t"])  # in milliseconds
        end = start + duration
        cap_info_list.append(CapInfo(start, end, caption))

    # Align time of CapInfo
    for info1, info2 in zip(cap_info_list[:-1], cap_info_list[1:]):
        if info1.end_time_int > info2.start_time_int:
            info1.end_time_int = info2.start_time_int

    # Info to String
    segments = []
    for idx, info in enumerate(cap_info_list, 1):
        line = "{seq}\n{start} --> {end}\n{text}\n".format(
            seq=idx,
            start=ms_time_to_srt_time_format(info.start_time_int),
            end=ms_time_to_srt_time_format(info.end_time_int),
            text=info.caption,
        )
        segments.append(line)
    return "\n".join(segments).strip()


def save_caption(yt: YouTube, path_base: str):
    """Save caption of youtube."""
    path = path_base + ".srt"
    caption_code = ""

    if "en" in yt.captions:
        caption_code = "en"
    elif "a.en" in yt.captions:
        caption_code = "a.en"
    else:
        print(f"Captions is {yt.captions}")
        print("Could not found english caption")
        return

    caption = yt.captions[caption_code]
    try:
        with open(path, "w") as fp:
            fp.write(xml_caption_to_srt(caption.xml_captions))
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


def download_youtube_link(link: str, only_video_flag: bool, only_audio_flag: bool):
    """Start the download operation."""
    yt = YouTube(link)

    filename_base = title2filename(yt.title)
    path_base = osp.join(FOLDER_OUT, filename_base)
    save_caption(yt, path_base)

    if only_video_flag:
        save_video(yt, filename_base)
    elif only_audio_flag:
        save_audio(yt, filename_base)
    else:
        save_audio(yt, filename_base)
        save_video(yt, filename_base)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Youtube using pytube.")
    parser.add_argument("url", type=str, help="URL of youtube")
    parser.add_argument(
        "--video_only", action="store_true", help="store only video of youtube"
    )
    parser.add_argument(
        "--audio_only", action="store_true", help="store only audio of youtube"
    )
    args = parser.parse_args()

    download_youtube_link(args.url, args.video_only, args.audio_only)
