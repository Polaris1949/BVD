# BVD
Bilibili Video Downloader

## Disclaimer
This tool is made for educational and research purpose. You may get **blocked** by bilibili for any abuse.

## Requirements
- Python 3.x
- Packages (`pip install -r requirements.txt`)
```
requests
tqdm
```

## Usage
This is a command line tool. Type `python bvd.py --help` for more help.

### BVID
BVID in url `https://www.bilibili.com/video/BV19a411P7zk` is `19a411P7zk` (excluding `BV`).

### Episode description
Episode description is similar to *custom print range* when you print documents, adding `$` marking the last episode (page). For example, supposing there are 10 episodes in a video, thus `1,3-6,9-$` specifies `1,3,4,5,6,9,10`.

## Examples
Download all episodes in a video as anonymous:
```
python bvd.py -i 19a411P7zk -o myvideo
```
Download specified episodes in a video as user:
```
python bvd.py -i 19a411P7zk -e 1 -o myvideo -c COOKIE
```

## Acknowledgements
Inspired from [Henryhaohao/Bilibili_video_download](https://github.com/Henryhaohao/Bilibili_video_download).
