import pathlib
import threading
import requests
import pyzipper
import time
import re

from strings import *
from http.client import responses

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal


class SearchWorker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, app, parent=None):
        super(SearchWorker, self).__init__(parent)

        # Thread nitty-gritty
        self.thread_name = None
        self.app = app


        self.samples_info = []

    def init_thread(self):
        self.thread_name = threading.current_thread().name
        self.app.responses[self.thread_name] = None

        # Tell main thread we've started
        self.started.emit()

    def parse_query(self):
        """Parse the search query and return a list of keywords"""

        # Receive search query from the box
        search_query = self.app.search_box.text()

        # Split the query into keywords and store them in a dictionary
        key_matches = {}

        for items in search_query.split(' '):
            cfilter = items.split(':')

            # If there are multiple colons in a single keyword or the keyword isn't approved, search for the next keyword
            if len(cfilter) > 2 or cfilter[0] not in FILTERS.keys():
                continue

            # If the keyword is approved and the syntax is correct, add it to the list
            if cfilter[1].startswith('"') and cfilter[1].endswith('"') and len(cfilter[1]) > 1:
                cfilter[1] = cfilter[1][1:-1]
                key_matches[cfilter[0]] = cfilter[1]

        # old
        limit_match = re.search(r"limit:(\d+)", search_query)  # likely a different function to be wrapped

        # Check if at least one filter was found
        if not key_matches:
            self.app.parseRequest.emit('illegal_query', self.thread_name)
            return None

        # Old
        if limit_match is None:
            limit = '100'
        else:
            limit = limit_match.group(1)

            # API limitation
            if int(limit) > 1000:
                limit = 1000

        # Assemble the request batch to be sent to the API
        request_batch = [
            {
                'query': FILTERS[key],
                key: value,
                'limit': limit
            }

            for key, value in key_matches.items()
        ]

        return request_batch

    def append(self, samples_info):
        """Append a new dictionary of samples to the list of them"""
        self.samples_info.append(samples_info)

    def search(self):
        self.init_thread()

        # Parse the search query, store keywords
        request_batch = self.parse_query()

        if request_batch is None:
            self.finished.emit()
            return

        # Create threads for each request
        for i, request in enumerate(request_batch):
            self.app.create_thread(
                f'Request-{i}',
                RequestWorker(self.app, request, None),
                [],
                'search',
                [self.append]
            ).start()

        # Wait for all threads to finish
        for i in range(len(request_batch)):
            self.app.threads[f'Request-{i}'].wait()

        self.retrieve()

    def retrieve(self):
        """Clean up after search"""
        self.app.samples_info = self.samples_info

        if self.samples_info is not None:
            # Remove previous search results
            self.app.model.removeRows(0, self.app.model.rowCount())

            # Create appropriate group
            section = self.app.model.get_group('MalwareBazaar')

            if section is None:
                section = self.app.model.add_group('MalwareBazaar')

            # Populate it with samples (post process it)
            for sample in self.samples_info:
                self.app.model.append_element(section, sample)

            # Acquire the groups
            root = self.app.model.invisibleRootItem()
            rows = root.rowCount()

            # Expand on demand
            for root_items in range(rows):
                if root.child(root_items).index().sibling(0, 1).data(Qt.DisplayRole) == "MalwareBazaar":
                    if not self.app.group_view.isExpanded(root.child(root_items).index()):
                        self.app.group_view.expand(root.child(root_items).index())

        self.finished.emit()


class RequestWorker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal(object)

    def __init__(self, app, request_info, additional_info):
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
        self.timer_secs = 30
        self.repeat_req = 3

        # Response
        self.response = None

    def init_thread(self):
        self.thread_name = threading.current_thread().name
        self.app.responses[self.thread_name] = None

        # Tell main thread we've started
        self.started.emit()

    def send_request(self):
        """
            Send an API request to MalwareBazaar.

            :return: The raw response from the API, or None if the request failed.
        """

        start_time = time.time()
        response = None

        for _ in range(self.repeat_req):
            try:
                response = requests.post('https://mb-api.abuse.ch/api/v1/',
                                         data=self.request_info, timeout=self.timer_secs, headers=self.headers)
                break
            except requests.exceptions.Timeout as e:
                if time.time() > start_time + self.timer_secs:
                    response = e
                else:
                    time.sleep(self.timer_secs // 6)

            except requests.exceptions.ConnectionError as e:
                self.app.showMessage.emit(
                    self.thread_name,
                    'critical',
                    'An error occured!',
                    f'Connection error:\n\n{e}\n\nPlease check your Internet connection and try again.'
                )

                return None

            except requests.exceptions.HTTPError as e:
                self.app.showMessage.emit(
                    self.thread_name,
                    'critical',
                    'An error occured!',
                    f'HTTP Error {response.status_code}: {responses[response.status_code]}\nPlease try again in a little bit.'
                )

                return None

        if isinstance(response, requests.exceptions.Timeout):
            self.app.showMessage.emit(
                self.thread_name,
                'critical',
                'An error occured!',
                f'API request failed with a timeout:\n\n{response}\n\nYou can adjust session timeout in settings or try again. Current value is {self.timer_secs} second(-s). The session has timed out a total of {self.repeat_req} time(-s).'
            )

            return None

        return response

    def search(self):
        """Search for a sample in MalwareBazaar."""

        self.init_thread()

        # Send a request to the API
        response = self.send_request()

        if response is None:
            return self.finished.emit(None)

        self.response = response.json()

        # If query status is OK, parse the response into a resulting list of tuples
        if self.response['query_status'] != 'ok':
            # Emit a signal to the main thread to reset the animation
            self.finished.emit(None)

            # Emit a signal to the main thread to display an error message
            return self.app.parseRequest.emit(self.response['query_status'], self.thread_name)
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
        self.finished.emit(samples_info)

    def download(self):
        """Download a sample from MalwareBazaar."""

        self.init_thread()

        # Send a request to the API
        response = self.send_request()

        if 'file_not_found' in response.text:
            self.app.showMessage.emit(
                self.thread_name,
                'warning',
                'File not found',
                f'Download failed. The following sample:\n\n{self.additional_info["file_name"]}\n\nwas not found on the download server. It might have been taken down while the search was underway. Please select a different sample to download.'
            )

            self.finished.emit(None)
        else:
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