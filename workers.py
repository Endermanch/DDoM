import threading
import requests
import pyzipper
import time
import re

from utilities import *
from strings import *

from functools import partial
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot


class SearchWorker(QObject):
    finished = pyqtSignal(object)
    unparsed = pyqtSignal(str, object)
    progress = pyqtSignal(int)

    def __init__(self, request_batch):
        super(SearchWorker, self).__init__()

        # Thread nitty-gritty
        self.thread_name = None

        self.children_finished = 0
        self.threads = {}
        self.workers = {}

        # Settings
        self.continue_on_error = False
        self.request_wait_time = 3000
        self.limit = 100

        # Technical
        self.request_batch = request_batch
        self.search_results = []

    def destroy(self, name):
        del self.workers[name]
        del self.threads[name]

    def stop(self):
        """Stop all threads, it's different from the error stop!"""
        print("Search thread stopped")

        for name, worker in list(self.workers.items()):
            worker.stop()

            del self.workers[name]
            del self.threads[name]

        self.finished.emit(None)

    def error(self, error_name, error_info):
        """Stop parent and all children threads and emit an error signal"""
        time.sleep(0.5)
        self.unparsed.emit(error_name, error_info)

        # Have to stop the rest of the threads - don't know how YET!
        for name, worker in list(self.workers.items()):
            worker.stop()

            del self.workers[name]
            del self.threads[name]

        if not self.continue_on_error:
            self.finished.emit(None)

    def search(self):
        print("Search thread started")

        # Create threads for each request
        for i, request in enumerate(self.request_batch):
            worker = self.workers[f'Request-{i}'] = RequestWorker(request, None, i * self.request_wait_time)
            thread = self.threads[f'Request-{i}'] = QThread()

            worker.moveToThread(thread)
            worker.finished.connect(thread.quit)
            worker.finished.connect(self.wait)

            worker.errored.connect(self.error)

            thread.started.connect(worker.search)
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(worker.deleteLater)
            thread.finished.connect(partial(self.destroy, f'Request-{i}'))

            thread.start()

    @pyqtSlot(object)
    def wait(self, search_results):
        self.children_finished += 1
        self.progress.emit(self.children_finished)

        if search_results is not None:
            self.search_results += search_results

        if self.children_finished == len(self.request_batch):
            print("All request threads have finished.")
            self.parse_data()

    def parse_data(self):
        # Remove duplicates (OR search)
        search_table = [i for n, i in enumerate(self.search_results) if i not in self.search_results[n + 1:]]
        time.sleep(0.5)
        self.finished.emit(search_table)


class RequestWorker(QObject):
    errored = pyqtSignal(str, object)
    finished = pyqtSignal(object)
    progress = pyqtSignal(int)

    def __init__(self, request_info, file_info, request_wait_time):
        super().__init__()

        # Thread nitty-gritty
        self.thread_name = None

        # Request info
        self.file_info = file_info
        self.request_info = request_info
        self.api_key_bazaar = '702fa1bd438c5c46e6e2a4a2e53f46a2'
        self.headers = {'API-KEY': self.api_key_bazaar}

        # Settings
        self.request_timeout = 30
        self.request_repeat = 3
        self.wait_time = request_wait_time

        # Debug
        self.query = list(self.request_info.values())[1]

        # Response
        self.response = None

    def init_thread(self):
        self.thread_name = threading.current_thread().name

        time.sleep(self.wait_time / 1000)

    def error(self, error_name, error_info):
        self.errored.emit(error_name, error_info)

        self.stop()

    def stop(self):
        print(f"Request thread for query {self.query} received stop signal")
        self.finished.emit(None)

    def send_request(self):
        """
            Send an API request to MalwareBazaar.

            :return: The raw response from the API, or None if the request failed.
        """

        start_time = time.time()
        response = None

        for _ in range(self.request_repeat):
            try:
                response = requests.post('https://mb-api.abuse.ch/api/v1/',
                                         data=self.request_info, timeout=self.request_timeout, headers=self.headers)
                break
            except requests.exceptions.Timeout as e:
                if time.time() > start_time + self.request_timeout:
                    response = e
                else:
                    time.sleep(self.request_timeout // 6)

            except requests.exceptions.ConnectionError as e:
                return self.errored.emit('connection_error', [e])

            except requests.exceptions.HTTPError:
                return self.errored.emit('http_error', [response.status_code])

        if isinstance(response, requests.exceptions.Timeout):
            return self.errored.emit('timeout', [response, self.request_timeout, self.request_repeat])

        return response

    def search(self):
        """Search for a sample in MalwareBazaar."""
        self.init_thread()

        print(f"Started search query {self.query} in thread {self.thread_name}")

        # Send a request to the API
        response = self.send_request()

        if response is None:
            return self.stop()

        self.response = response.json()

        # If query status is OK, parse the response into a resulting list of tuples
        if self.response['query_status'] != 'ok':
            # Emit a signal to the main thread to display an error message
            print(f"Query {self.query} returned an error: {self.response['query_status']}")
            return self.errored.emit(self.response['query_status'], [list(self.request_info.values())[1]])

        # Generate a list of dictionaries from the response
        samples_info = [
            {
                'file_name': sample['file_name'],
                'file_type': sample['file_type'],
                'file_size': sample['file_size'],
                'signature': sample['signature'],
                'sha256_hash': sample['sha256_hash'],
                'first_seen': sample['first_seen'],
                'downloads': sample['intelligence']['downloads'],
                'uploads': sample['intelligence']['uploads'],
                'tags': sample['tags']
            }

            for sample in self.response['data']
        ]

        # We found some samples, emit a signal to the main thread to display them
        print(f"Response for {self.query} was received, returning sample info")
        self.finished.emit(samples_info)

    def download(self):
        """Download a sample from MalwareBazaar."""
        self.init_thread()
        print("Download thread created")

        # Send a request to the API
        response = self.send_request()

        print("Response received")

        if 'file_not_found' in response.text:
            self.app.showMessage.emit(
                self.thread_name,
                'warning',
                'File not found',
                f'Download failed. The following sample:\n\n{self.file_info["file_name"]}\n\nwas not found on the download server. It might have been taken down while the search was underway. Please select a different sample to download.'
            )

            self.finished.emit(None)
        else:
            print(f"Downloading file {self.file_info['sha256_hash']}")
            with open(f"{PATH}/{self.file_info['sha256_hash']}.zip", 'wb') as file:
                bytes_downloaded = 0
                bytes_total = self.file_info['file_size']

                chunk_size = bytes_total // 100

                for data in response.iter_content(chunk_size=chunk_size):
                    bytes_downloaded += chunk_size
                    file.write(data)

                    # Update progress bar
                    self.progress.emit(int(100 * bytes_downloaded / bytes_total))
                    time.sleep(0.001)

            self.progress.emit(100)
            time.sleep(1)
            self.progress.emit(0)

        print("Download thread exited")

    def export(self):
        pass

        # output_file = open('output.json', 'w')
        # json.dump(response.json(), output_file, indent=4, sort_keys=True)

    @staticmethod
    def unzip(sha256_hash):
        zip_password = b'infected'

        with pyzipper.AESZipFile(sha256_hash + ".zip") as zf:
            zf.pwd = zip_password
            my_secrets = zf.extractall(".")
            print("Malicious sample \"" + sha256_hash + "\" unpacked.")
