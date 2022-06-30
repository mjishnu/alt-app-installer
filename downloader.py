import json
import os
import psutil
import random
import re
import requests
import time
import validators
from collections import deque
from datetime import datetime
from math import inf
from pathlib import Path
from ping3 import ping
from requests.sessions import Session
from requests.adapters import HTTPAdapter
from threading import Thread
from urllib3.poolmanager import PoolManager
from win32gui import GetForegroundWindow
from win32process import GetWindowThreadProcessId

def is_active():
    active = GetWindowThreadProcessId(GetForegroundWindow())[1]
    parents = psutil.Process().parents()
    for p in parents:
        if p.pid == active:
            return True
    return False

def timestring(sec):
    sec = int(sec)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f'{h:02d}:{m:02d}:{s:02d}'


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
        super(Adapter, self).__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, source_address=('', self._source_port))


class USession(Session):
    portassigner = Port_Getter()

    def __init__(self, *args, **kwargs):
        super(USession, self).__init__(*args, **kwargs)
        self.headers.update(
            {'connection': 'close', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'})
        self.setport()

    def setport(self):
        port = USession.portassigner.randomport()
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
        interrupted = True
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
        f = path.open(mode='ab+')
        if self.count != self.getval('length'):
            interrupted = False
            s = USession()
            r = s.get(
                url, headers={'range': 'bytes={0}-{1}'.format(start, end)}, stream=True)
            while True:
                if self.dic['paused']:
                    r.connection.close()
                    r.close()
                    s.close()
                    interrupted = True
                    break
                if (chunk := next(r.iter_content(131072), None)):
                    f.write(chunk)
                    self.count += len(chunk)
                    self.position += len(chunk)
                    self.setval('count', self.count)
                    self.setval('position', self.position)
                else:
                    break
        f.close()
        if not interrupted:
            r.close()
            s.close()
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


class Verifier:
    @staticmethod
    def validate_filepath(path):
        path = path.replace('\\', '/')
        if (not re.match('^[a-zA-Z]:/(((?![<>:"/|?*]).)+((?<![ .])/)?)*$', path) or
                not Path(path[:3]).exists()):
            print('Invalid windows file path has been inputted, process will now stop.')
            return False
        return True
    
    @staticmethod
    def validate_url(url):
        if not validators.url(url):
            print('Invalid url been inputted, process will now stop.')
            return False
        if url.lower().startswith('ftp://'):
            print(
                "`requests` module doesn't suport File Transfer Protocol, process will now stop")
            return False
        return True
    
    @staticmethod
    def confirm_overwrite(path, overwrite):
        filepath = str(path)
        if not path.exists():
            return True
        if path.is_file():
            if overwrite:
                return True
            while True:
                answer = input(
                    f'`{filepath}` already exists, do you want to overwrite it? \n(Yes, No):').lower()
                if answer in ['y', 'yes', 'n', 'no']:
                    if answer.startswith('y'):
                        os.remove(filepath)
                        return True
                print('Invalid input detected, retaking input.')
        print(f'Overwritting {filepath} has been aborted, process will now stop.')
        return False
    
    @staticmethod
    def test_connection(url):
        server = url.split('/')[2]
        ok = ping(server, timeout=2)
        if ok == False:
            print(
                'The server of the inputted url is non-existent, process will now stop.')
            return False
        if ok:
            return True
        if not ok:
            print('Connection has timed out, will reattempt to ping server 5 times.')
            for i in range(5):
                print(
                    f'Reattempting to ping server, retrying {i + 1} out of 5')
                ok = ping(server, timeout=2)
                if ok:
                    print(
                        f'Connection successful on retry {i + 1}, process will now continue.')
                    return True
                print(f'Retry {i + 1} out of 5 timed out' + (i != 4)
                    * ', reattempting in 1 second.' + (i == 4) * '.')
                time.sleep(1)
        print('Failed to connect server, connection timed out, process will now stop')
        return False
    
    @staticmethod
    def validate_accessible(url):
        head = requests.head(url)
        if head.status_code == 200:
            return True
        for i in range(5):
            print(f'Server responce is invalid, retrying {i + 1} out of 5')
            head = requests.head(url)
            if head.status_code == 200:
                print(
                    f'Connection successful on retry {i + 1}, process will now continue.')
                return True
            print(f'Retry {i + 1} out of 5 failed to access data' +
                (i != 4) * ', reattempting in 1 second.' + (i == 4) * '.')
            time.sleep(1)
        print("Can't establish a connection with access to data, can't download target file, process will now stop.")
        return False


class Downloader:
    def __init__(self):
        self.recent = deque([0] * 12, maxlen=12)
        self.recentspeeds = deque([0] * 200, maxlen=200)
        self.dic = dict()
        self.workers = []
        self.progress = 0

    def download(self, url, filepath, num_connections=32, overwrite=False):
        info = requests.head(url)
        size = int(int(info.headers["Content-Length"])/1000000) #1MB = 1,000,000 bytes
        if size < 50:
            num_connections = 5
        bcontinue = Path(filepath + '.progress.json').exists()
        singlethread = False
        threads = []
        path = Path(filepath)
        if not Verifier.validate_filepath(filepath):
            raise ValueError()
        
        if not Verifier.validate_url(url):
            raise ValueError()
        
        if not bcontinue:
            if not Verifier.confirm_overwrite(path, overwrite):
                raise InterruptedError()
        
        if not Verifier.test_connection(url):
            raise TimeoutError()
        
        if not Verifier.validate_accessible(url):
            raise PermissionError()
        
        head = requests.head(url)
        folder = '/'.join(filepath.split('/')[:-1])
        Path(folder).mkdir(parents=True, exist_ok=True)
        headers = head.headers
        total = headers.get('content-length')
        if not total:
            print(
                f'Cannot find the total length of the content of {url}, the file will be downloaded using a single thread.')
            started = datetime.now()
            print('Task started on %s.' %
                    started.strftime('%Y-%m-%d %H:%M:%S'))
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
                started = datetime.now()
                print('Download started on %s.' %
                        started.strftime('%Y-%m-%d %H:%M:%S'))
                sd = self.Singledown()
                th = Thread(target=sd.singledown, args=(url, path))
                self.workers.append(sd)
                th.start()
                singlethread = True
            else:
                if bcontinue:
                    progress = json.loads(Path(filepath + '.progress.json').read_text(), 
                                        object_hook=lambda d: {int(k) if k.isdigit() else k: v for k, v in d.items()})
                segment = total / num_connections
                started = datetime.now()
                print('Task started on %s.' %
                        started.strftime('%Y-%m-%d %H:%M:%S'))
                self.dic['total'] = total
                self.dic['connections'] = num_connections
                self.dic['paused'] = False
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
                    threads.append(th)
                    th.start()
                    self.workers.append(md)
                
                Path(filepath + '.progress.json').write_text(json.dumps(self.dic, indent=4))
        downloaded = 0
        totalMiB = total / 1048576
        speeds = []
        interval = 0.04
        while True:
            Path(filepath + '.progress.json').write_text(json.dumps(self.dic, indent=4))
            status = sum([i.completed for i in self.workers])
            downloaded = sum(i.count for i in self.workers)
            self.recent.append(downloaded)
            doneMiB = downloaded / 1048576
            gt0 = len([i for i in self.recent if i])
            if not gt0:
                speed = 0
            else:
                recent = list(self.recent)[12 - gt0:]
                if len(recent) == 1:
                    speed = recent[0] / 1048576 / interval
                else:
                    diff = [b - a for a, b in zip(recent, recent[1:])]
                    speed = sum(diff) / len(diff) / 1048576 / interval
            speeds.append(speed)
            self.recentspeeds.append(speed)
            now = datetime.now()
            elapsed = (now - started).total_seconds()
            meanspeed = downloaded / elapsed / 1048576
            self.progress = (doneMiB * 100)/ totalMiB
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
                ended = datetime.now()
                break
            time.sleep(interval)
        time_spent = (ended - started).total_seconds()
        meanspeed = total / time_spent / 1048576
        status = sum([i.completed for i in self.workers])
        if status == len(self.workers):
            print('Download completed on {0}, total time elapsed: {1}, average speed: {2:.2f} MiB/s'.format(
                ended.strftime('%Y-%m-%d %H:%M:%S'), timestring(time_spent), meanspeed))
            Path(filepath + '.progress.json').unlink()
        else:
            print('Download interrupted on {0}, total time elapsed: {1}, average speed: {2:.2f} MiB/s'.format(
                ended.strftime('%Y-%m-%d %H:%M:%S'), timestring(time_spent), meanspeed))