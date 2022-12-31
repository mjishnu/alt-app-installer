import json
import time
from pathlib import Path
from threading import Thread

import requests


class Multidown:
    def __init__(self, dic, id):
        self.count = 0
        self.completed = False
        # used to differniate between diffent instance of multidown class
        self.id = id
        # the dic is filled with data from the json {start,position,end,filepath,count,length,url,completed}
        # the json also has info like paused,total bytes,number of connections (parts)
        self.dic = dic
        self.position = self.getval('position')

    def getval(self, key):
        return self.dic[self.id][key]

    def setval(self, key, val):
        self.dic[self.id][key] = val

    def worker(self):
        # getting the path(file_name/file) from the json file (dict)
        filepath = self.getval('filepath')
        path = Path(filepath)
        end = self.getval('end')
        # checks if the part exists if it doesn't exist set start from the json file(download from beginning) else download beginning from size of the file
        if not path.exists():
            start = self.getval('start')
        else:
            # gets the size of the file
            self.count = path.stat().st_size
            start = self.getval('start') + self.count
        url = self.getval('url')
        self.position = start
        with open(path, 'ab+') as f:
            if self.count != self.getval('length'):
                s = requests.sessions.Session()
                r = s.get(
                    url, headers={'range': 'bytes={0}-{1}'.format(start, end)}, stream=True)
                while True:
                    if self.dic['paused']:
                        r.connection.close()
                        r.close()
                        s.close()
                        break
                    # the next returns the next element form the iterator of r(the request we send to dowload) and returns None if the iterator is exhausted
                    chunk = next(r.iter_content(128 * 1024), None)
                    if chunk:
                        f.write(chunk)
                        self.count += len(chunk)
                        self.position += len(chunk)
                        self.setval('count', self.count)
                        self.setval('position', self.position)
                    else:
                        break
        # self.count is the length of current download if its equal to the size of the part we need to download them mark as downloaded
        if self.count == self.getval('length'):
            self.completed = 1
            self.setval('completed', 1)


class Singledown:
    def __init__(self):
        self.count = 0

    def worker(self, url, path):
        with requests.get(url, stream=True) as r, open(path, 'wb') as file:
            for chunk in r.iter_content(1048576):  # 1MB
                if chunk:
                    self.count += len(chunk)
                    file.write(chunk)


class Downloader:
    def __init__(self):
        self.dic = {}
        self.workers = []
        self.progress = 0
        self.alive = True
        self.completed = False

    def download(self, url, filepath, num_connections=20):
        json_path = filepath + '.progress.json'
        json_file = Path(json_path).exists()
        singlethread = False
        threads = []
        f_path = str(filepath)
        head = requests.head(url)
        total = int(head.headers.get('content-length'))
        size = total / 1048576  # 1MB = 1048576 bytes (size in MB)

        if size < 50:
            num_connections = 5
        # if no range avalable in header or no size from header
        if not total or not head.headers.get('accept-ranges'):
            print("the file will be downloaded using a single thread.")
            print('Download started!')
            sd = Singledown()
            th = Thread(target=sd.worker, args=(url, f_path))
            th.daemon = True
            self.workers.append(sd)
            th.start()
            singlethread = True
        else:
            # multiple threads possible
            if json_file:
                # the object_hook converts the key strings whose value is int to type int
                progress = json.loads(Path(json_path).read_text(), object_hook=lambda d: {
                                      int(k) if k.isdigit() else k: v for k, v in d.items()})
            segment = total / num_connections
            print('Download started!')
            self.dic['total'] = total
            self.dic['connections'] = num_connections
            self.dic['paused'] = False
            for i in range(num_connections):
                if not json_file:
                    # get the starting byte size by multiplying the segment by the part number eg 1024 * 2 = part2 beginning byte etc.
                    start = int(segment * i)
                    # here end is the ((segment * next part ) - 1 byte) since the last byte is also downloaded by next part
                    # here (i != num_connections - 1) since we don't want to do this 1 byte subtraction for last part (index is from 0)
                    end = int(segment * (i + 1)) - (i != num_connections - 1)
                    position = start
                    length = end - start + (i != num_connections - 1)
                else:
                    start = progress[i]['start']
                    end = progress[i]['end']
                    position = progress[i]['position']
                    length = progress[i]['length']
                self.dic[i] = {
                    'start': start,
                    'position': position,
                    'end': end,
                    'filepath': f'{filepath}.{i}.part',
                    'count': 0,
                    'length': length,
                    'url': url,
                    'completed': False
                }

                md = Multidown(self.dic, i)
                th = Thread(target=md.worker)
                th.daemon = True
                threads.append(th)
                th.start()
                self.workers.append(md)

            Path(json_path).write_text(json.dumps(self.dic, indent=4))

        downloaded = 0
        while True:
            Path(json_path).write_text(json.dumps(self.dic, indent=4))
            status = sum([i.completed for i in self.workers])
            downloaded = sum(i.count for i in self.workers)
            doneMiB = downloaded / 1048576
            try:
                self.progress = (doneMiB * 100) / size
            except ZeroDivisionError:
                print("zero division error")
            if self.dic['paused']:
                break
            if status == len(self.workers):
                if not singlethread:
                    BLOCKSIZE = 4096
                    BLOCKS = 1024
                    CHUNKSIZE = BLOCKSIZE * BLOCKS
                    # combine the parts together
                    with open(f_path, 'wb') as dest:
                        for i in range(num_connections):
                            file_ = f'{filepath}.{i}.part'
                            with open(file_, 'rb') as f:
                                while True:
                                    chunk = f.read(CHUNKSIZE)
                                    if chunk:
                                        dest.write(chunk)
                                    else:
                                        break
                            Path(file_).unlink()

                print('Download completed!')
                Path(json_path).unlink()
                self.completed = True
                break

            time.sleep(0.04)

        if not self.completed:
            print('Download interrupted!')
