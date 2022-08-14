# BVD - Bilibili Video Download
BVD_VER = '1.0'
import argparse, hashlib, json, os, random, re, sys, time
import requests, tqdm

# External class kazuha.json.JSONFile
class JSONFile:
    def __init__(self, path:str):
        assert len(path) > 0, 'Empty path not allowed'
        self._path = path

    def load(self, default={}, allow_not_found:bool=False):
        filename = self._path
        if allow_not_found and not os.path.exists(filename):
            return default
        input = sys.stdin if filename == '-' else open(filename, 'r', encoding='utf-8')
        return json.load(input) if input else default

    def dump(self, data, pretty_print:bool=False):
        filename = self._path
        output = sys.stdout if filename == '-' else open(filename, 'w', encoding='utf-8')
        if pretty_print:
            json.dump(data, output, ensure_ascii=False, indent=4)
        else:
            json.dump(data, output)

# External function kazuha.fs.canonize_filename
def canonize_filename(f:str)->str:
    return f.replace('\\', '＼').replace('/', '／').replace(':', '：').replace('*', '＊').replace('?', '？').replace('<', '＜').replace('>', '＞').replace('|', '｜')

BVD_USERAGENT = ''
# External function kazuha.net.rand_useragent
def rand_useragent()->str:
    user_agent_data = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
        "Opera/8.0 (Windows NT 5.1; U; en)",
        "Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36"
    ]
    index = random.randint(0, len(user_agent_data) - 1)
    return user_agent_data[index]

# No longer support video combination
# ENABLE_COMBINE = False

# Check if blocked by bilibili
def chk_blocked(response):
    if response.status_code not in (200, 206):
        print('[ERROR] HTTP Status Code:', response.status_code)
        print('[DEBUG] response.headers =', response.headers)
        if response.status_code in (403, 412):
            print('[NOTE] You may have been blocked by bilibili. Try again later.')
        exit(1)

# Get play url
def get_playurl(bvid, cid, quality, video_apiurl):
    if args.cookie: # User mode
        apiurl = f'https://api.bilibili.com/x/player/playurl?cid={cid}&bvid={bvid}&qn={quality}'
        headers = {
            'Cookie': args.cookie, # Note cookie
            'Host': 'api.bilibili.com',
            'User-Agent': BVD_USERAGENT
        }
    else: # Anonymous mode
        entropy = 'rbMCKn@KuamXWlPMoJGsKcbiJKUfkPF_8dABscJntvqhRSETg'
        appkey, sec = ''.join([chr(ord(i) + 2) for i in entropy[::-1]]).split(':')
        params = f'appkey={appkey}&cid={cid}&otype=json&qn={quality}&quality={quality}&type='
        chksum = hashlib.md5(bytes(params + sec, 'utf8')).hexdigest()
        apiurl = f'https://interface.bilibili.com/v2/playurl?{params}&sign={chksum}'
        headers = {
            'Referer': video_apiurl, # Note referer
            'User-Agent': BVD_USERAGENT
        }
    response = requests.get(apiurl, headers=headers)
    chk_blocked(response)
    html = response.json()
    video_list = []
    if args.cookie:
        durl = html['data']['durl']
    else:
        durl = html['durl']
    for i in durl:
        video_list.append(i['url'])
    assert len(video_list) == 1, 'No longer support video combination'
    return video_list[0]

# Download from url
def download_from_url(url, filename, headers):
    headers['Range'] = 'bytes=0-'
    response = requests.get(url, stream=True, headers=headers)
    chk_blocked(response)
    file_size = int(response.headers['Content-Length'])
    # Resume from breakpoint if any
    if os.path.exists(filename):
        first_byte = os.path.getsize(filename)
    else:
        first_byte = 0
    if first_byte >= file_size:
        return 1 # Complete last time
    headers['Range'] = f'bytes={first_byte}-{file_size}'
    pbar = tqdm.tqdm(total=file_size, initial=first_byte, unit='B', unit_scale=True)
    req = requests.get(url, stream=True, headers=headers)
    with open(filename, 'ab') as f:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                pbar.update(1024)
    pbar.close()
    return 0 # Complete this time

# Download a bilibili video
def download_video(video_url, video_apiurl, page, video_title, episode_title):
    episode_name = f'P{page} {episode_title}'
    print('[INFO] Download started')
    video_path = os.path.join(args.output, video_title)
    if not os.path.exists(video_path):
        os.makedirs(video_path)
    headers = {
        # 'Host': 'upos-hz-mirrorks3.acgvideo.com', # Host is not necessary
        'User-Agent': BVD_USERAGENT,
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': video_apiurl, # Note referer
        'Origin': 'https://www.bilibili.com',
        'Connection': 'keep-alive',
    }
    filename = os.path.join(video_path, f'{episode_name}.flv')
    ret = download_from_url(video_url, filename, headers)
    print('[INFO] Download finished')
    return ret

# Download main process
def download_main(args)->None:
    match_result = re.match(r'https://www.bilibili.com/video/BV(\w+)(\?p=(\d+))?', args.bvid)
    args.bvid = match_result.group(1) if match_result else args.bvid
    print('[INFO] BVID:', args.bvid)
    url_p_flag = False
    if match_result:
        url_p = match_result.group(3)
        if url_p:
            url_p_flag = True
            print('[INFO] Episode id found in url:', url_p)
            if args.episode or args.range:
                print('[WARNING] Episode id in url is overriden by cmd args')
    video_apiurl = 'https://api.bilibili.com/x/web-interface/view?bvid=' + args.bvid
    global BVD_USERAGENT
    BVD_USERAGENT = rand_useragent()
    headers = {
        'User-Agent': BVD_USERAGENT
    }
    data = requests.get(video_apiurl, headers=headers).json()['data']
    video_title = data['title']
    print('[INFO] Video title:', video_title)
    video_title = canonize_filename(video_title)
    cid_list = data['pages']

    if args.episode:
        ep_parts = args.episode.split(',')
        episode = []
        for ep_part in ep_parts:
            match_result = re.match(r'([0123456789$]+)(-([0123456789$]+))?$', ep_part)
            epp_beg = match_result.group(1)
            if epp_beg == '$':
                epp_beg = len(cid_list)
            epp_end = match_result.group(3) or epp_beg
            if epp_end == '$':
                epp_end = len(cid_list)
            for ch in range(int(epp_beg), int(epp_end)+1):
                episode.append(ch)
    elif url_p_flag:
        episode = [int(url_p)]
    else:
        episode = [ch for ch in range(1, len(cid_list)+1)]
    print('[INFO] Episode list:', episode)

    first_flag = True
    lret = 0
    for i, item in enumerate(cid_list, 1):
        if i not in episode:
            continue
        if args.time and not first_flag and not args.list and lret == 0:
            print(f'[INFO] Sleep for {args.time}s...')
            time.sleep(args.time)
        else:
            first_flag = False
        cid = str(item['cid'])
        episode_title = item['part']
        if not episode_title:
            episode_title = video_title
        page = str(item['page'])
        episode_apiurl = video_apiurl + "&p=" + page
        print('[INFO] Episode title:', f'P{page}', episode_title)
        if args.list:
            continue # List only
        episode_title = canonize_filename(episode_title)
        episode_url = get_playurl(args.bvid, cid, args.quality, episode_apiurl)
        lret = download_video(episode_url, episode_apiurl, page, video_title, episode_title)

# Parse args
def parse_args(dargs:list=sys.argv[1:]):
    parser = argparse.ArgumentParser(description='parse and download bilibili video')
    parser.add_argument('-v, --version', help='output version information and exit', action='version', version=f'%(prog)s {BVD_VER}')
    parser.add_argument('-i', help='bvid or url', metavar='BVID', dest='bvid')
    parser.add_argument('-q', help='quality [default=1080] (1080|720|480|360)', metavar='QUAL', dest='quality', type=int, default=1080)
    parser.add_argument('-e', help='episode description (indexed from 1)', metavar='STR', dest='episode')
    parser.add_argument('-o', help='output directory [default=download]', metavar='DIR', default='download', dest='output')
    parser.add_argument('-l', help='list episode only', action='store_true', dest='list')
    parser.add_argument('-c', help='user cookie', metavar='STR', dest='cookie')
    parser.add_argument('-t', help='sleep time (s) [default=1.0]', metavar='TIME', type=float, default=1.0, dest='time')
    args = parser.parse_args(dargs)
    print('[INFO] Parsed cmd:', args)
    if args.bvid is None:
        return 15

    QUALITY_DICT = {1080: 80, 720: 64, 480: 32, 360: 16}
    if args.quality in QUALITY_DICT:
        args.quality = QUALITY_DICT[args.quality]
    else:
        print('[ERROR] Bad quality; expect one of (1080, 720, 480, 360)')
        return 1
    return args

if __name__ == '__main__':
    args = parse_args()
    if isinstance(args, int):
        if args == 15: # Exit if bvid not supplied
            print('[ERROR] BVID not supplied')
            exit(1)
        else:
            exit(args)
    download_main(args)
