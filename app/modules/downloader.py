import json
import os
import threading
import time
from math import inf
from pathlib import Path

import requests


class Multidown:
    """Class for downloading a specific part of a file in multiple chunks"""

    def __init__(self, dic, id, stop, error):
        self.curr = 0  # current size of downloaded file
        self.completed = 0  # whether the download for this part is complete
        self.id = id  # ID of this download part
        # dictionary containing download information for all parts, {start, curr, end, filepath, count, size, url, completed}
        self.dic = dic
        self.stop = stop  # event to stop the download
        self.error = error  # event to indicate an error occurred

    def getval(self, key):
        """Get the value of a key from the dictionary"""
        return self.dic[self.id][key]

    def setval(self, key, val):
        """Set the value of a key in the dictionary"""
        self.dic[self.id][key] = val

    def worker(self):
        """Download a part of the file in multiple chunks"""
        filepath = self.getval('filepath')
        path = Path(filepath)
        end = self.getval('end')

        # checks if the part exists if it doesn't exist set start from beginning else download rest of the file
        if not path.exists():
            start = self.getval('start')
        else:
            # gets the size of the file
            self.curr = path.stat().st_size
            # add the old start size and the current size to get the new start size
            start = self.getval("start") + self.curr
            # corruption check to make sure parts are not corrupted
            if start > end:
                os.remove(path)
                self.error.set()
                print("corrupted file!")

        url = self.getval('url')
        if self.curr != self.getval('size'):
            try:
                # download part
                with requests.session() as s, open(path, 'ab+') as f:
                    headers = {"range": f"bytes={start}-{end}"}
                    with s.get(url, headers=headers, stream=True, timeout=20) as r:
                        for chunk in r.iter_content(1048576):  # 1MB
                            if chunk:
                                f.write(chunk)
                                self.curr += len(chunk)
                                self.setval('curr', self.curr)
                            if not chunk or self.stop.is_set() or self.error.is_set():
                                break
            except Exception as e:
                self.error.set()
                time.sleep(1)
                print(
                    f"Error in thread {self.id}: ({e.__class__.__name__}, {e})")

        if self.curr == self.getval('size'):
            self.completed = 1
            self.setval('completed', 1)


class Singledown:
    """Class for downloading a whole file in a single chunk"""

    def __init__(self):
        self.curr = 0  # current size of downloaded file
        self.completed = 0  # whether the download is complete

    def worker(self, url, path, stop, error):
        """Download a whole file in a single chunk"""
        flag = True
        try:
            # download part
            with requests.get(url, stream=True, timeout=20) as r, open(path, 'wb') as file:
                for chunk in r.iter_content(1048576):  # 1MB
                    if chunk:
                        file.write(chunk)
                        self.curr += len(chunk)
                    if not chunk or stop.is_set() or error.is_set():
                        flag = False
                        break
        except Exception as e:
            error.set()
            time.sleep(1)
            print(f"Error in thread {self.id}: ({e.__class__.__name__}: {e})")
        if flag:
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
        head = requests.head(url, timeout=20, allow_redirects=True)
        total = int(head.headers.get('content-length'))
        self.totalMB = total / 1048576  # 1MB = 1048576 bytes (size in MB)
        singlethread = False
        # adjust the number of connections for small files
        if self.totalMB < 50:
            num_connections = 5 if num_connections > 5 else num_connections

        # if no range available in header or no size from header use single thread
        if not total or not head.headers.get('accept-ranges') or not multithread:
            # create single threaded download object
            sd = Singledown()
            # create single download worker thread
            th = threading.Thread(target=sd.worker, args=(
                url, f_path, self.Stop, self._Error))
            self._workers.append(sd)
            th.start()
            total = inf if not total else total
            singlethread = True
        else:
            # multiple threads possible
            if json_file.exists():
                # load the progress from the progress file
                # the object_hook converts the key strings whose value is int to type int
                progress = json.loads(json_file.read_text(), object_hook=lambda d: {
                    int(k) if k.isdigit() else k: v for k, v in d.items()})
            segment = total / num_connections
            self._dic['total'] = total
            self._dic['connections'] = num_connections
            self._dic['paused'] = False
            for i in range(num_connections):
                try:
                    # try to use progress file to resume download
                    start = progress[i]['start']
                    end = progress[i]['end']
                    curr = progress[i]['curr']
                    size = progress[i]['size']
                except:
                    # if not able to use progress file then calculate the start, end, curr and size
                    # calculate the beginning byte offset by multiplying the segment by num_connections.
                    start = int(segment * i)
                    # here end is the ((segment * next part ) - 1 byte) since the last byte is downloaded by next part except for the last part
                    end = int(segment * (i + 1)) - (i != num_connections - 1)
                    curr = start
                    size = end - start + (i != num_connections - 1)

                self._dic[i] = {
                    'start': start,
                    'curr': curr,
                    'end': end,
                    'filepath': f'{filepath}.{i}.part',
                    'size': size,
                    'url': url,
                    'completed': False
                }
                # create multidownload object for each connection
                md = Multidown(self._dic, i, self.Stop, self._Error)
                # create worker thread for each connection
                th = threading.Thread(target=md.worker)
                threads.append(th)
                th.start()
                self._workers.append(md)

            # save the progress to the progress file
            if not singlethread:
                json_file.write_text(json.dumps(self._dic, indent=4))

        downloaded = 0
        interval = 0.15
        while True:
            if not singlethread:
                # save progress to progress file
                json_file.write_text(json.dumps(self._dic, indent=4))
            # check if all workers have completed
            status = sum(i.completed for i in self._workers)
            # get the total amount of data downloaded
            downloaded = sum(i.curr for i in self._workers)
            try:
                # calculate download progress percentage
                self.progress = int(100 * downloaded / total)
            except ZeroDivisionError:
                self.progress = 0

            # check if download has been stopped or if an error has occurred
            if self.Stop.is_set() or self._Error.is_set():
                self._dic['paused'] = True
                if not singlethread:
                    # save progress to progress file
                    json_file.write_text(json.dumps(self._dic, indent=4))
                break

            # check if all workers have completed
            if status == len(self._workers):
                if not singlethread:
                    # combine the parts together
                    BLOCKSIZE = 4096
                    BLOCKS = 1024
                    CHUNKSIZE = BLOCKSIZE * BLOCKS
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
                    # delete the progress file
                    json_file.unlink()
                break
            time.sleep(interval)

        if display and self.Stop.is_set():
            print('Task interrupted')

    def start(self, url, filepath, num_connections=10, display=True, multithread=True, block=True, retries=0, retry_func=None):
        """
        Start the download process.

        Parameters:
            url (str): The download URL.
            filepath (str): The file path to save the download.
            num_connections (int): The number of connections to use for a multi-threaded download.
            display (bool): Whether to display download progress.
            multithread (bool): Whether to use multi-threaded download.
            block (bool): Whether to block until the download is complete.
            retries (int): The number of times to retry the download in case of an error.
            retry_func (function): A function to call to get a new download URL in case of an error.
        """
        def start_thread():
            try:
                # start the download
                self.download(url, filepath, num_connections,
                              display, multithread)
                # retry the download if there are errors
                for _ in range(retries):
                    if self._Error.is_set():
                        time.sleep(3)
                        # reset the downloader object
                        self.__init__(self.Stop)

                        # get a new download URL to retry
                        _url = url
                        if retry_func:
                            try:
                                _url = retry_func()
                            except Exception as e:
                                print(
                                    f"Retry function Error: ({e.__class__.__name__}, {e})")

                        if display:
                            print("retrying...")
                        # restart the download
                        self.download(_url, filepath, num_connections,
                                      display, multithread)
                    else:
                        break
            # if there's an error, set the error event and print the error message
            except Exception as e:
                print(f"Download Error: ({e.__class__.__name__}, {e})")
                self._Error.set()

            # if error flag is set, set the failed flag to True
            if self._Error.is_set():
                self.Failed = True
                print("Download Failed!")

        # Initialize the downloader with stop Event
        self.__init__(self.Stop)
        self.Stop.clear()
        # Start the download process in a new thread
        th = threading.Thread(target=start_thread)
        th.start()

        # Block the current thread until the download is complete, if necessary
        if block:
            th.join()
