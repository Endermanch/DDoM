import requests
import http.client
import pyzipper
import time
import re

from utilities import *
from strings import *

from requests.adapters import HTTPAdapter, Retry
from functools import partial

from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot


class SearchWorker(QObject):
    finished = pyqtSignal(object)
    progress = pyqtSignal(int)
    errorred = pyqtSignal(str, object)

    ready = pyqtSignal()

    def __init__(self, request_batch):
        super(SearchWorker, self).__init__()

        # Thread nitty-gritty
        self.thread_name = None
        self.cancelled = False
        self.children_finished = 0
        self.threads = {}
        self.workers = {}

        # Settings
        self.request_wait_time = 3000
        self.limit = 100

        # Technical
        self.request_batch = request_batch
        self.search_results = []

    def stop(self):
        """Stop all threads, it's different from the error stop!"""
        print("Stop signal run from SearchWorker.")

        # Have to stop the rest of the threads - don't know how YET!
        for name in list(self.threads.keys()):
            print(f"Waiting for thread {name} to stop.")
            self.threads[name].quit()
            self.threads[name].wait()

        print("Finished signal emitted from SearchWorker.")
        self.finished.emit(None)

    @pyqtSlot(str, object)
    def error(self, error_name, error_info):
        """Stop parent and all children threads and emit an error signal"""
        print("Error slot run from SearchWorker")

        time.sleep(0.5)
        self.errorred.emit(error_name, error_info)
        self.stop()

    def search(self):
        print("Search thread started")

        # Create threads for each request
        for i, request in enumerate(self.request_batch):
            worker = self.workers[f'Request-{i}'] = RequestWorker(request, None, i * self.request_wait_time)
            thread = self.threads[f'Request-{i}'] = QThread(parent=self)

            worker.moveToThread(thread)
            worker.finished.connect(thread.quit)
            worker.finished.connect(self.wait)

            worker.errorred.connect(self.error)

            thread.started.connect(worker.search)
            thread.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)

            thread.setObjectName(f'Request-{i}')

            thread.start()

    @pyqtSlot(object)
    def wait(self, search_results):
        print("Wait slot run from SearchWorker")

        self.children_finished += 1
        self.progress.emit(self.children_finished)

        if search_results is not None:
            self.search_results += search_results

        if self.children_finished == len(self.request_batch):
            print("All request threads have finished.")

            if not self.cancelled:
                self.ready.emit()
                self.parse_data()
            else:
                print("SearchWorker has been cancelled.")
                self.stop()

    def parse_data(self):
        print("Data parsing has started")

        # Remove duplicates (OR search)
        search_table = [i for n, i in enumerate(self.search_results) if i not in self.search_results[n + 1:]]
        time.sleep(0.5)
        self.finished.emit(search_table)


class RequestWorker(QObject):
    errorred = pyqtSignal(str, object)
    finished = pyqtSignal(object)
    progress = pyqtSignal(int)

    def __init__(self, request_info, file_info, wait_time):
        super().__init__()

        # Thread nitty-gritty
        self.thread_name = None

        # Request info
        self.file_info = file_info
        self.request_info = request_info
        self.api_key_bazaar = '702fa1bd438c5c46e6e2a4a2e53f46a2'
        self.api_key_malshare = '2988254c0d6e57c3c2ba1b46212e8893f22cb16bb883356b42db9b79451936bd'
        self.api_key_vshare = '8U57uYvZE7CEwmvqoaboG9JcZTI9VZTS'
        self.headers = {'API-KEY': self.api_key_bazaar}

        # Settings
        self.request_timeout = 30
        self.max_retries = 3
        self.wait_time = wait_time

        # Debug
        self.query = list(self.request_info.values())[1]

        # Response
        self.response = None

    def init_thread(self):
        self.thread_name = QThread.currentThread().objectName()
        thread_id = int(QThread.currentThreadId())  # cast to int() is necessary
        print('Running worker #1 from thread "{}" (#{})'.format(self.thread_name, thread_id))

        time.sleep(self.wait_time / 1000)

    def error(self, error_name, error_info):
        print("An error occurred inside RequestWorker")
        self.errorred.emit(error_name, error_info)

    def stop(self):
        print(f"Request thread {self.thread_name} for query {self.query} was stopped")
        self.finished.emit(None)

    def send_request(self):
        """
            Send an API request to MalwareBazaar.

            :return: The raw response from the API, or None if the request failed.
        """

        start_time = time.time()
        response = None

        retries = Retry(
            total=self.max_retries,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )

        with requests.Session() as session:
            session.mount('https://', HTTPAdapter(max_retries=retries))

            try:
                response = session.post(
                    API_SOURCES['MalwareBazaar'],
                    headers=self.headers, data=self.request_info, timeout=self.request_timeout
                )

                response.raise_for_status()

            except requests.exceptions.Timeout as e:
                return self.errorred.emit('timeout', [e, self.request_timeout, self.max_retries])

            except requests.exceptions.ConnectionError as e:
                return self.errorred.emit('connection_error', [e])

            except requests.exceptions.HTTPError:
                return self.errorred.emit('http_error', [response.status_code, http.client.responses[response.status_code]])

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
            return self.error(self.response['query_status'], [list(self.request_info.values())[1]])

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
