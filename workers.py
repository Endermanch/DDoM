import threading
import requests
import pyzipper
import time
import re

from utilities import *
from strings import *
from http.client import responses

from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot


class SearchWorker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    stopped = pyqtSignal()

    def __init__(self, app):
        super(SearchWorker, self).__init__()

        # Thread nitty-gritty
        self.thread_name = None
        self.thread_end = False
        self.finished_count = 0
        self.threads = {}
        self.workers = {}

        # Save the main application pointer
        self.app = app

        # Settings
        self.request_wait_time = 1000
        self.limit = 100

        # Search results
        self.search_results = []
        self.search_table = []

    def parse_query(self):
        """Parse the search query and return a list of keywords"""

        # Receive search query from the box
        search_query = " ".join(self.app.search_box.text().split())

        if not search_query:
            self.error('no_query', None)
            return None

        # Split the query into keywords and store them in a dictionary
        key_matches = {}

        # For each keyword separated by a space filter them out
        for items in search_query.split(' '):
            cfilter = items.split(':')

            if len(cfilter) < 2:
                return

            keyword = cfilter[0]
            value = cfilter[1]

            # If there are multiple colons in a single keyword or the keyword isn't approved, search for the next keyword
            if len(cfilter) > 2 or keyword not in API_FILTERS.keys():
                continue

            match API_FILTERS[keyword]:
                case 'limit':
                    self.limit = int(value)

            # If the keyword is approved and the syntax is correct, add it to the list
            if value.startswith('"') and value.endswith('"') and len(value) > 2:
                value = value[1:-1]
                key_matches[API_FILTERS[keyword]] = value

        # Check if at least one filter was found
        if not key_matches:
            return None

        # API limitation
        if self.limit > 1000:
            self.limit = 1000

        request_batch = []

        # Assemble the request batch to be sent to the API
        for key, value in key_matches.items():
            for name in value.split(','):
                if name:
                    request_batch.append({
                        'query': API_QUERIES[API_FILTERS[key]],
                        API_FILTERS[key]: name,
                        'limit': self.limit
                    })

        # Tidy up the request for hash
        for request in request_batch:
            if request['query'] == 'hash':
                del request['limit']

        # Return a request batch
        return request_batch

    def error(self, error_name, error_info):
        if not self.thread_end:
            time.sleep(0.5)
            self.app.parseRequest.emit(error_name, self.thread_name)

        for thread in self.threads.values():
            self.stopped.emit()

    def stop(self):
        self.thread_end = True
        self.finished.emit()

    def search(self):
        print("Search thread started")
        self.app.responses[self.thread_name] = None
        # Parse the search query, store keywords
        self.request_batch = self.parse_query()

        # If there are no keywords, exit the thread
        if self.request_batch is None:
            self.error('illegal_query', None)

            return self.finished.emit()

        # Create threads for each request
        for i, request in enumerate(self.request_batch):
            worker = self.workers[f'Request-{i}'] = RequestWorker(self.app, request, None, i * self.request_wait_time)
            thread = self.threads[f'Request-{i}'] = QThread()

            self.finished.connect(worker.stop)

            worker.moveToThread(thread)
            worker.finished.connect(worker.deleteLater)
            worker.finished.connect(thread.quit)
            worker.finished.connect(self.wait)

            worker.errored.connect(worker.deleteLater)
            worker.errored.connect(thread.quit)
            worker.errored.connect(self.error)
            worker.errored.connect(self.stop)

            thread.started.connect(worker.search)
            thread.finished.connect(thread.deleteLater)

            thread.start()

    @pyqtSlot(object)
    def wait(self, search_results):
        self.finished_count += 1

        if search_results is not None:
            self.search_results += search_results

        if self.finished_count == len(self.request_batch):
            print("All request threads have finished.")
            self.parse_data()

    def parse_data(self):
        # Remove duplicates (OR search)
        self.search_table = [i for n, i in enumerate(self.search_results) if i not in self.search_results[n + 1:]]

        self.retrieve()
        self.finished.emit()

    def retrieve(self):
        """Clean up after search"""
        self.app.search_table = self.search_table

        if self.search_table is None or not self.search_table:
            return

        # Remove previous search results
        self.app.model.removeRows(0, self.app.model.rowCount())

        # Get appropriate group, if it doesn't exist, create
        section = self.app.model.get_group('MalwareBazaar')

        if section is None:
            section = self.app.model.add_group('MalwareBazaar')

        # Populate it with samples (post process it)
        for sample in self.search_table:
            self.app.model.append_element(section, sample)

        # Acquire the groups
        root = self.app.model.invisibleRootItem()
        rows = root.rowCount()

        # Expand on demand
        self.app.group_view.expandAll()

        #for root_items in range(rows):
        #    if root.child(root_items).index().sibling(0, 1).data(Qt.DisplayRole) == "MalwareBazaar":
        #        if not self.app.group_view.isExpanded(root.child(root_items).index()):
        #            self.app.group_view.expand(root.child(root_items).index())


class RequestWorker(QObject):
    started = pyqtSignal()
    errored = pyqtSignal(str, object)
    finished = pyqtSignal(object)

    def __init__(self, app, request_info, additional_info, request_wait_time):
        super().__init__()

        # Thread nitty-gritty
        self.thread_name = None
        self.app = app

        # Request info
        self.additional_info = additional_info
        self.request_info = request_info
        self.api_key_bazaar = '702fa1bd438c5c46e6e2a4a2e53f46a2'
        self.headers = {'API-KEY': self.api_key_bazaar}

        # Settings
        self.request_timeout = 30
        self.request_repeat = 3
        self.wait_time = request_wait_time
        # Response
        self.response = None

    def init_thread(self):
        self.thread_name = threading.current_thread().name
        self.app.responses[self.thread_name] = None

        # Tell main thread we've started
        time.sleep(self.wait_time / 1000)
        self.started.emit()

    def error(self, error_name, error_info):
        self.errored.emit(error_name, error_info)
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
                return self.errored.emit('connection_error', (e))

            except requests.exceptions.HTTPError:
                return self.errored.emit('http_error', (response.status_code))

        if isinstance(response, requests.exceptions.Timeout):
            return self.errored.emit('timeout', (response, self.request_timeout, self.request_repeat))

        return response

    def search(self):
        """Search for a sample in MalwareBazaar."""
        self.init_thread()
        print("NESTED THREAD STARTED")

        # Send a request to the API
        response = self.send_request()

        if response is None:
            return self.finished.emit(None)

        self.response = response.json()

        # If query status is OK, parse the response into a resulting list of tuples
        if self.response['query_status'] != 'ok':
            # Emit a signal to the main thread to display an error message
            self.errored.emit(self.response['query_status'], None)

            # Emit a signal to the main thread to reset the animation
            return self.finished.emit(None)
        else:
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
        print("NESTED THREAD FINISHED")
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
                f'Download failed. The following sample:\n\n{self.additional_info["file_name"]}\n\nwas not found on the download server. It might have been taken down while the search was underway. Please select a different sample to download.'
            )

            self.finished.emit(None)
        else:
            print(f"Downloading file {self.additional_info['sha256_hash']}")
            with open(f"{PATH}/{self.additional_info['sha256_hash']}.zip", 'wb') as file:
                bytes_downloaded = 0
                bytes_total = self.additional_info['file_size']

                chunk_size = bytes_total // 100

                for data in response.iter_content(chunk_size=chunk_size):
                    bytes_downloaded += chunk_size
                    file.write(data)

                    # Update progress bar
                    self.app.updateProgress.emit(int(100 * bytes_downloaded / bytes_total))
                    time.sleep(0.001)

            self.app.updateProgress.emit(100)
            time.sleep(1)
            self.app.updateProgress.emit(0)

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

    def stop(self):
        print("Request thread received stop signal")
        self.finished.emit(None)