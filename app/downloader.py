import json
import threading
import time
from math import inf
from pathlib import Path

import requests


class Multidown:
    def __init__(self, dic, id, stop, Error):
        self.count = 0
        self.completed = 0
        # used to differniate between diffent instance of multidown class
        self.id = id
        # the dic is filled with data from the json {start,position,end,filepath,count,length,url,completed}
        # the json also has info like total bytes,number of connections (parts)
        self.dic = dic
        self.position = self.getval('position')
        self.stop = stop
        self.Error = Error

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
        if self.count != self.getval('length'):
            try:
                with requests.session() as s, open(path, 'ab+') as f:
                    with s.get(url, headers={"range": f"bytes={start}-{end}"}, stream=True, timeout=20) as r:
                        while True:
                            if self.stop.is_set() or self.Error.is_set():
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
            except Exception as e:
                self.Error.set()
                time.sleep(1)
                print(
                    f"Error in thread {self.id}: ({e.__class__.__name__}, {e})")
        # self.count is the length of current download if its equal to the size of the part we need to download them mark as downloaded
        if self.count == self.getval('length'):
            self.completed = 1
            self.setval('completed', 1)


class Singledown:
    def __init__(self):
        self.count = 0
        self.completed = 0

    def worker(self, url, path, stop, Error):
        try:
            with requests.get(url, stream=True, timeout=20) as r, open(path, 'wb') as file:
                for chunk in r.iter_content(1048576):  # 1MB
                    if chunk:
                        self.count += len(chunk)
                        file.write(chunk)
                    if stop.is_set() or Error.is_set():
                        return
        except Exception as e:
            Error.set()
            time.sleep(1)
            print(f"Error in thread {self.id}: ({e.__class__.__name__}, {e})")

        self.completed = 1


class Downloader:
    def __init__(self, StopEvent=threading.Event()):
        self._dic = {}
        self._workers = []
        self._Error = threading.Event()

        # attributes
        self.Stop = StopEvent  # stop Event
        self.Failed = False
        self.totalMB = 0
        self.progress = 0

    def download(self, url, filepath, num_connections, display, multithread):
        json_file = Path(filepath + '.progress.json')
        threads = []
        f_path = str(filepath)
        head = requests.head(url, timeout=20)
        total = int(head.headers.get('content-length'))
        self.totalMB = total / 1048576  # 1MB = 1048576 bytes (size in MB)
        singlethread = False

        if self.totalMB < 50:
            num_connections = 5 if num_connections > 5 else num_connections
        # if no range avalable in header or no size from header use single thread
        if not total or not head.headers.get('accept-ranges') or not multithread:
            sd = Singledown()
            th = threading.Thread(target=sd.worker, args=(
                url, f_path, self.Stop, self._Error))
            self._workers.append(sd)
            th.start()
            total = inf if not total else total
            singlethread = True
        else:
            # multiple threads possible
            if json_file.exists():
                # the object_hook converts the key strings whose value is int to type int
                progress = json.loads(json_file.read_text(), object_hook=lambda d: {
                                      int(k) if k.isdigit() else k: v for k, v in d.items()})
            segment = total / num_connections
            self._dic['total'] = total
            self._dic['connections'] = num_connections
            self._dic['paused'] = False
            for i in range(num_connections):
                if not json_file.exists() or progress == {}:
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

                self._dic[i] = {
                    'start': start,
                    'position': position,
                    'end': end,
                    'filepath': f'{filepath}.{i}.part',
                    'count': 0,
                    'length': length,
                    'url': url,
                    'completed': False
                }
                md = Multidown(self._dic, i, self.Stop, self._Error)
                th = threading.Thread(target=md.worker)
                threads.append(th)
                th.start()
                self._workers.append(md)

            json_file.write_text(json.dumps(self._dic, indent=4))
        downloaded = 0
        interval = 0.15
        status = 0
        while True:
            json_file.write_text(json.dumps(self._dic, indent=4))
            status = sum([i.completed for i in self._workers])
            downloaded = sum(i.count for i in self._workers)
            try:
                self.progress = int(100 * downloaded / total)
            except ZeroDivisionError:
                self.progress = 0

            if self.Stop.is_set() or self._Error.is_set():
                self._dic['paused'] = True
                json_file.write_text(json.dumps(self._dic, indent=4))
                break

            if status == len(self._workers):
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
                json_file.unlink()
                if display:
                    print('Task completed')
                break
            time.sleep(interval)

        if display and self.Stop.is_set():
            print('Task interrupted')

    def start(self, url, filepath, num_connections=10, display=True, multithread=True, block=True, retries=0, retry_func=None):

        def start_thread():
            try:
                self.download(url, filepath, num_connections,
                              display, multithread)
                for _ in range(retries):
                    if self._Error.is_set():
                        time.sleep(3)
                        self.__init__(self.Stop)

                        _url = url
                        if retry_func:
                            try:
                                _url = retry_func()
                            except Exception as e:
                                print(
                                    f"Retry function Error: ({e.__class__.__name__}, {e})")

                        if display:
                            print("retrying...")
                        self.download(_url, filepath, num_connections,
                                      display, multithread)
                    else:
                        break
            except Exception as e:
                print(f"Download Error: ({e.__class__.__name__}, {e})")
                self._Error.set()

            if self._Error.is_set():
                self.Failed = True
                print("Download Failed!")

        self.__init__(self.Stop)
        self.Stop.clear()
        th = threading.Thread(target=start_thread)
        th.start()

        if block:
            th.join()
