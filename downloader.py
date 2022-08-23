import json
import random
import time
from math import inf
from pathlib import Path
from threading import Thread

import psutil
import requests
from requests.adapters import HTTPAdapter
from requests.sessions import Session
class Port_Getter:
    @staticmethod
    def busyports():
        return set(i.laddr.port for i in psutil.net_connections())

    def __init__(self):
        self.assigned = set()

    def randomport(self):
        port = random.randint(1, 65535)
        while port in Port_Getter.busyports() or port in self.assigned:
            port = random.randint(1, 65535)
        self.assigned.add(port)
        return port


class Adapter(HTTPAdapter):
    def __init__(self, port, *args, **kwargs):
        self._source_port = port
        super().__init__(*args, **kwargs)

class UserSession(Session):
    portassigner = Port_Getter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers.update(
            {'connection': 'close'})
        self.setport()

    def setport(self):
        port = UserSession.portassigner.randomport()
        self.mount('http://', Adapter(port))
        self.mount('https://', Adapter(port))


class Multidown:
    def __init__(self, dic, id):
        self.count = 0
        self.completed = False
        self.id = id
        self.dic = dic
        self.position = self.getval('position')

    def getval(self, key):
        return self.dic[self.id][key]

    def setval(self, key, val):
        self.dic[self.id][key] = val

    def worker(self):
        filepath = self.getval('filepath')
        path = Path(filepath)
        end = self.getval('end')
        if not path.exists():
            start = self.getval('start')
        else:
            self.count = path.stat().st_size
            start = self.getval('start') + self.count
        url = self.getval('url')
        self.position = start
        with open(path,'ab+') as f:
            if self.count != self.getval('length'):
                s = UserSession()
                r = s.get(
                    url, headers={'range': 'bytes={0}-{1}'.format(start, end)}, stream=True)
                while True:
                    if self.dic['paused']:
                        r.connection.close()
                        r.close()
                        s.close()
                        break
                    if (chunk := next(r.iter_content(128 * 1024), None)):
                        f.write(chunk)
                        self.count += len(chunk)
                        self.position += len(chunk)
                        self.setval('count', self.count)
                        self.setval('position', self.position)
                    else:
                        break
        if self.count == self.getval('length'):
            self.completed = 1
            self.setval('completed', 1)

class Singledown:
    def __init__(self):
        self.count = 0

    def worker(self, url, path):
        with requests.get(url, stream=True) as r:
            with path.open('wb') as file:
                for chunk in r.iter_content(1048576):
                    if chunk:
                        self.count += len(chunk)
                        file.write(chunk)
class Downloader:
    def __init__(self):
        self.dic = dict()
        self.workers = []
        self.progress = 0
        self.alive = True
        self.dic['paused'] = False

    def download(self, url, filepath, num_connections=20):
        f_path = filepath + '.progress.json'
        bcontinue = Path(f_path).exists()
        singlethread = False
        threads = []
        path = Path(filepath)
        head = requests.head(url)

        size = int(int(head.headers["Content-Length"])/1000000) #1MB = 1,000,000 bytes
        if size < 50:
            num_connections = 5

        folder = '/'.join(filepath.split('/')[:-1])
        Path(folder).mkdir(parents=True, exist_ok=True)
        headers = head.headers
        total = headers.get('content-length')
        if not total:
            print(
                f'Cannot find the total length of the content of {url}, the file will be downloaded using a single thread.')
            print('Download started!')
            sd = Singledown()
            th = Thread(target=sd.worker, args=(url, path))
            self.workers.append(sd)
            th.start()
            total = inf
            singlethread = True
        else:
            total = int(total)
            if not headers.get('accept-ranges'):
                print(
                    'Server does not support the `range` parameter, the file will be downloaded using a single thread.')
                print('Download started!')
                sd = self.Singledown()
                th = Thread(target=sd.singledown, args=(url, path))
                self.workers.append(sd)
                th.start()
                singlethread = True
            else:
                if bcontinue:
                    progress = json.loads(Path(f_path).read_text(),
                                        object_hook=lambda d: {int(k) if k.isdigit() else k: v for k, v in d.items()})
                segment = total / num_connections
                print('Download started!')
                self.dic['total'] = total
                self.dic['connections'] = num_connections
                for i in range(num_connections):
                    if not bcontinue:
                        start = int(segment * i)
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
                        'filepath': filepath + '.' + str(i).zfill(2) + '.part',
                        'count': 0,
                        'length': length,
                        'url': url,
                        'completed': False
                    }

                for i in range(num_connections):
                    md = Multidown(self.dic, i)
                    th = Thread(target=md.worker)
                    th.daemon = True
                    threads.append(th)
                    th.start()
                    self.workers.append(md)

                Path(f_path).write_text(json.dumps(self.dic, indent=4))
        downloaded = 0
        totalMiB = total / 1048576
        while True:
            Path(f_path).write_text(json.dumps(self.dic, indent=4))
            status = sum([i.completed for i in self.workers])
            downloaded = sum(i.count for i in self.workers)
            doneMiB = downloaded / 1048576
            try:
                self.progress = (doneMiB * 100)/ totalMiB
            except ZeroDivisionError:
                print("zero division error")
            if self.dic['paused'] == True:
                break
            if status == len(self.workers):
                if not singlethread:
                    BLOCKSIZE = 4096
                    BLOCKS = 1024
                    CHUNKSIZE = BLOCKSIZE * BLOCKS
                    with path.open('wb') as dest:
                        for i in range(num_connections):
                            file = filepath + '.' + str(i).zfill(2) + '.part'
                            with Path(file).open('rb') as f:
                                while (chunk := f.read(CHUNKSIZE)):
                                    dest.write(chunk)
                            Path(file).unlink()
                break
            time.sleep(0.04)
        status = sum([i.completed for i in self.workers])
        if status == len(self.workers):
            print('Download completed!')
            Path(f_path).unlink()
        else:
            print('Download interrupted!')