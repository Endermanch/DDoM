import webbrowser
import pathlib
import resources
import random
import re

from workers import *
from groupview import *
from strings import *
from utilities import *

from http.client import responses
from functools import partial

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class Window(QMainWindow):
    def __init__(self, width, height, title, icon, parent=None):
        super(Window, self).__init__(parent)

        self.width = width
        self.height = height

        self.left = 10
        self.top = 10
        self.right = self.width - 10
        self.bottom = self.height - 10

        self.setMinimumSize(self.width, self.height)
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(icon))


class Dialog(QDialog):
    def __init__(self, width, height, title, icon, parent=None):
        super().__init__(parent)

        self.width = width
        self.height = height

        self.left = 10
        self.top = 10
        self.right = self.width - 10
        self.bottom = self.height - 10

        self.setFixedSize(self.width, self.height)
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(icon))
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.setWindowModality(Qt.ApplicationModal)


class HelpWindow(Window):
    switch_window = pyqtSignal()

    def __init__(self):
        # Call parent constructor
        super(HelpWindow, self).__init__(600, 400, "Quick Start", ":help.ico")

        self.current_page = 1
        self.titles = []
        self.pages = []

        # Fill in lists
        for title in MANUAL_PAGES:
            self.titles.append(title)
            self.pages.append(MANUAL_PAGES[title])

        # Create labels
        self.title = QLabel(self.titles[0], self)
        self.title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title.adjustSize()
        self.title.move(self.left - 2, self.top - 5)

        self.manual = QLabel(self.pages[0], self)
        self.manual.setWordWrap(True)
        self.manual.adjustSize()
        self.manual.move(self.left, self.top + 30)

        # Create buttons
        self.back_button = QPushButton("Back", self)
        self.back_button.clicked.connect(self.dec_page)
        self.back_button.move(self.right - 205, self.bottom - 30)
        self.back_button.setEnabled(False)

        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.inc_page)
        self.next_button.move(self.right - 100, self.bottom - 30)

        self.finish_button = QPushButton("Finish", self)
        self.finish_button.clicked.connect(self.close)
        self.finish_button.move(self.right - 100, self.bottom - 30)
        self.finish_button.setVisible(False)

    def get_page(self):
        if self.current_page == 1:
            self.back_button.setEnabled(False)
        else:
            self.back_button.setEnabled(True)

        if self.current_page == len(MANUAL_PAGES):
            self.next_button.setVisible(False)
            self.finish_button.setVisible(True)
        else:
            self.next_button.setVisible(True)
            self.finish_button.setVisible(False)

        self.manual.setText(self.pages[self.current_page - 1])
        self.manual.adjustSize()

        self.title.setText(self.titles[self.current_page - 1])
        self.title.adjustSize()

    def inc_page(self):
        self.current_page += 1
        self.get_page()

    def dec_page(self):
        self.current_page -= 1
        self.get_page()

    def init_page(self):
        self.manual.setText(
            "This is a simple downloader that downloads a random image from unsplash.com and sets it as your desktop background. \n\n"
            "You can also download a random image from unsplash.com by clicking on the tray icon. \n\n"
            "If you want to download a specific image, you can use the following syntax: \n\n"
            "tag:\"Adware\", hash:\"j08923r0239fjoubfouwfj9023j\" \n\n"
            "This will download an image with the tag \"Adware\" and the hash \"j08923r0239fjoubfouwfj9023j\". \n\n"
            "If you want to download a specific image from a specific user, you can use the following syntax: \n\n"
            "user:\"username\", tag:\"Adware\", hash:\"j08923r0239fjoubfouwfj9023j\" \n\n"
            "This will download an image from the user \"username\" with the tag \"Adware\" and the hash \"j08923r0239fjoubfouwfj9023j\". \n\n"
            "You can also download a specific image from a specific user by using the following syntax: \n\n"
            "user:\"username\", id:\"j08923r0239fjoubfouwfj9023j\" \n\n"
            "This will download an image from the user \"username\" with the id \"j08923r0239fjoubfouwfj9023j\". \n\n"
            "If you want to download a specific image from a specific user by using the following syntax: \n\n"
            "user:\"username\", id:\"j08923r0239fjoubfouwfj9023j\" \n\n"
            "This will download")
        self.manual.adjustSize()


class AboutWindow(Dialog):
    def __init__(self):
        # Call parent constructor
        super(AboutWindow, self).__init__(400, 300, "About Daily Dose of Malware", ":about.ico")

        # Set vertical layout
        self.verticalLayout = QVBoxLayout(self)

        # Create image
        image = QLabel(self)

        image_source = QPixmap(":logo.png")
        image_source = image_source.scaled(380, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        image.setPixmap(image_source)

        # Create labels
        title = QLabel("Malware Downloader", self)

        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.adjustSize()

        label = QLabel(ABOUT_DESC + ABOUT_FACTS[random.randint(0, len(ABOUT_FACTS) - 1)], self)
        label.setWordWrap(True)
        label.adjustSize()

        # Create button
        ok = QPushButton("OK", self)
        ok.clicked.connect(self.close)

        # Align items
        self.verticalLayout.addWidget(image, alignment=Qt.AlignCenter | Qt.AlignTop)
        self.verticalLayout.addWidget(title, alignment=Qt.AlignCenter)
        self.verticalLayout.addWidget(label, alignment=Qt.AlignCenter)
        self.verticalLayout.addWidget(ok, alignment=Qt.AlignRight | Qt.AlignBottom)


class SetupWindow(Dialog):
    def __init__(self):
        # Call parent constructor
        super(SetupWindow, self).__init__(580, 420, "Quick Setup", ":setup.ico")

        self.init_ui()

    def init_ui(self):
        # Create labels
        self.title_label = QLabel(self)
        self.title_label.setText("Quick Setup")
        self.title_label.move(self.left - 2, self.top - 5)  # Font being dumb
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_label.adjustSize()

        self.desc_label = QLabel("Setup", self)
        self.desc_label.move(self.left, self.top + 30)

        self.help_label = QLabel(self)
        self.help_label.setWordWrap(True)

        # Create buttons
        self.back_button = QPushButton("Back", self)
        self.back_button.resize(90, 25)
        self.back_button.move(self.right - 185, self.bottom - 25)
        self.back_button.setEnabled(False)
        self.back_button.clicked.connect(self.close)

        self.next_button = QPushButton("Next", self)
        self.next_button.resize(90, 25)
        self.next_button.move(self.right - 90, self.bottom - 25)
        self.next_button.clicked.connect(self.close)


class MainWindow(Window):
    cancel = pyqtSignal()

    def __init__(self):
        # Call the parent constructor
        super(MainWindow, self).__init__(1280, 720, TITLE, ":logo.png")

        self.top = 30  # Context menu

        pathlib.Path(PATH).mkdir(parents=True, exist_ok=True)

        # Contain threads, workers and responses in a dictionary
        self.threads = {}
        self.workers = {}
        self.responses = {}

        self.message_box_shown = False

        # Change window color
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(240, 240, 240))
        self.setPalette(palette)

        # Window configuration
        self.setWindowTitle(TITLE)
        self.setWindowIcon(QIcon(":icon.png"))
        self.setAutoFillBackground(True)

        # Initialize UI
        self.init_menubar()
        self.init_ui()
        self.show()

        # Search fields
        self.search_table = None
        self.search_running = False

    @staticmethod
    def spawn_about():
        AboutWindow().exec()

    def spawn_help(self):
        self.help_window = HelpWindow()
        self.help_window.show()

    def spawn_setup(self):
        self.setup_window = SetupWindow()
        self.setup_window.show()

    def dummy(self):
        print("I'm a dummy! Please wait till the creator of this program adds me!")

    def init_menubar(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        m_file = menubar.addMenu("&File")
        m_file.addAction(QIcon(":setup.png"), "Quick Setup", self.spawn_setup, QKeySequence("Ctrl+Q"))
        m_file.addAction(QIcon(":export.ico"), "Export...", self.dummy, QKeySequence("Ctrl+S"))
        m_file.addSeparator()
        m_file.addAction(QIcon(":key.ico"), "Exit", self.close, QKeySequence("Alt+F4"))

        m_settings = menubar.addMenu("&Settings")
        m_settings.addAction("Save", self.dummy, QKeySequence("Ctrl+S"))

        m_resources = menubar.addMenu("&Resources")
        m_resources.addAction(QIcon(":mgen.png"), "Malware Generator", partial(webbrowser.open, WEBSITES["MGenerator"]))
        m_resources.addAction(QIcon(":vt.png"), "VirusTotal", partial(webbrowser.open, WEBSITES["VirusTotal"]))
        m_resources.addAction(QIcon(":anyrun.png"), "ANY.RUN", partial(webbrowser.open, WEBSITES["ANY.RUN"]))

        m_about = menubar.addMenu("&About")
        m_about.addAction(QIcon(":help.ico"), "Quick Start", self.spawn_help)
        m_about.addSeparator()
        m_about.addAction(QIcon(":url.ico"), "Website", partial(webbrowser.open, WEBSITES["Main"]))
        m_about.addAction(QIcon(":software.ico"), "GitHub", partial(webbrowser.open, WEBSITES["GitHub"]))
        m_about.addAction(QIcon(":about.ico"), "About DDoM...", self.spawn_about)

    def init_ui(self):
        # Labels
        self.title_label = QLabel(self)
        self.title_label.setText(TITLE)
        self.title_label.move(self.left - 2, self.top - 5)  # Font being dumb
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.title_label.adjustSize()

        self.description_label = QLabel(self)
        self.description_label.setText(DESC)
        self.description_label.move(self.left, self.top + 35)
        self.description_label.adjustSize()

        # Search button
        self.search_button = QPushButton(self)
        self.search_button.setText("&Go")
        self.search_button.resize(75, 20 + 2)
        self.search_button.move(self.right - 75, self.top - 1)
        self.search_button.clicked.connect(self.search)

        self.search_button_cancel = QPushButton(self)
        self.search_button_cancel.setText("Cancel")
        self.search_button_cancel.resize(75, 20 + 2)
        self.search_button_cancel.move(self.right - 75, self.top - 1)
        self.search_button_cancel.hide()
        self.search_button_cancel.clicked.connect(self.search_stop)

        # Editbox
        self.search_box = QLineEdit(self)
        self.search_box.resize(420, 20)
        self.search_box.move(self.right - 500, self.top)
        self.search_box.setPlaceholderText("Enter a tag, SHA256, MD5 hash...")
        self.search_box.returnPressed.connect(self.search_button.click)
        self.search_box.installEventFilter(self)

        # Search label
        self.search_label = QLabel(self)
        self.search_label.setText("Search:")
        self.search_label.setStyleSheet("font-size: 14px;")
        self.search_label.move(self.right - 552, self.top + 1)
        self.search_label.adjustSize()

        # Set table model (fill with data)
        self.model = GroupModel(self)
        # self.model.setSortRole(Qt.UserRole)

        self.group_view = GroupView(self.model, parent=self)

        self.group_view.move(self.left, self.top + 60)
        self.group_view.resize(self.width - 20, self.height - 140)

        self.group_view.beginDownload.connect(self.download)

        # Search progress bar
        self.search_progress = QProgressBar(self)
        self.search_progress.move(self.left, self.top + 60)
        self.search_progress.resize(self.width - 20, 24)
        self.search_progress.setTextVisible(False)
        self.search_progress.hide()

        # Loading animation (centered against the group view)
        self.search_anim = QLabel(self)
        self.search_anim.setAlignment(Qt.AlignCenter)

        anim_source = QMovie(":poke.gif")
        anim_source.setScaledSize(QSize(200, 200))
        anim_source.start()

        self.search_anim.setMovie(anim_source)
        self.search_anim.hide()

        group_layout = QVBoxLayout(self.group_view)
        group_layout.addWidget(self.search_anim)

        # Download progress
        self.download_progress = QProgressBar(self)
        # self.download_progress.setTextVisible(False)
        self.download_progress.resize(self.width - 155, 30)
        self.download_progress.move(self.left, self.bottom - 30)

        # Download button
        self.download_button = QPushButton(self)
        self.download_button.setText("&Download")
        self.download_button.setEnabled(False)
        self.download_button.move(self.right - 100, self.bottom - 30)
        self.download_button.clicked.connect(partial(self.download))

    def eventFilter(self, source, event):
        if source == self.search_box:
            if event.type() == QEvent.KeyPress:
                match event.key():
                    case Qt.Key_Return:
                        self.search()
                        return True

                    case Qt.Key_Escape:
                        self.search_stop()
                        return True

        return super(MainWindow, self).eventFilter(source, event)

    @pyqtSlot(QResizeEvent)
    def resizeEvent(self, event):
        new_dimensions = event.size()

        new_right = new_dimensions.width() - self.width + self.right
        new_bottom = new_dimensions.height() - self.height + self.bottom

        self.search_box.resize(
            new_right - (self.search_box.geometry().left() + self.search_button.width() + 5),
            self.search_box.height()
        )

        self.search_button.move(
            new_right - self.search_button.width(),
            self.search_button.geometry().top()
        )

        self.search_button_cancel.move(
            new_right - self.search_button_cancel.width(),
            self.search_button_cancel.geometry().top()
        )

        self.group_view.resize(
            new_right - self.group_view.geometry().left(),
            new_bottom - (self.group_view.geometry().top() + 40)
        )

        self.search_progress.resize(
            new_right - self.search_progress.geometry().left(),
            self.search_progress.height()
        )

        self.download_progress.setGeometry(
            self.download_progress.geometry().left(),
            new_bottom - self.download_button.height(),
            new_right - (self.download_button.width() + 10),
            self.download_progress.height()
        )

        self.download_button.move(
            new_right - self.download_button.width(),
            new_bottom - self.download_button.height()
        )

    def parse_query(self, search_query):
        """Parse the search query and return a list of keywords"""
        limit = 100

        if not search_query:
            self.parse_message('no_query')
            return None

        # Remove extra spaces
        search_query = " ".join(search_query.split())

        # Split the query into keywords and store them in a dictionary
        key_matches = {}

        # For each keyword separated by a space filter them out
        for items in search_query.split(' '):
            cfilter = items.split(':')

            if len(cfilter) < 2:
                return

            keyword = cfilter[0]
            value = cfilter[1]

            # If there are multiple colons in a single keyword or the keyword isn't approved,
            # search for the next keyword
            if len(cfilter) > 2 or keyword not in API_FILTERS.keys():
                continue

            match API_FILTERS[keyword]:
                case 'limit':
                    limit = int(value)

            # If the keyword is approved and the syntax is correct, add it to the list
            if value.startswith('"') and value.endswith('"') and len(value) > 2:
                value = value[1:-1]
                key_matches[API_FILTERS[keyword]] = value

        # Check if at least one filter was found
        if not key_matches:
            return None

        # API limitation
        if limit > 1000:
            limit = 1000

        request_batch = []

        # Assemble the request batch to be sent to the API
        for key, value in key_matches.items():
            for name in value.split(','):
                if name:
                    request_batch.append({
                        'query': API_QUERIES[API_FILTERS[key]],
                        API_FILTERS[key]: name,
                        'limit': limit
                    })

        # Tidy up the request for hash
        for request in request_batch:
            if request['query'] == 'hash':
                del request['limit']

        # Return a request batch
        return request_batch

    def show_message_box(self, severity, title, message):
        """Shows a message box."""
        response = getattr(QMessageBox, str(severity))(self, title, message, QMessageBox.Ok)

        self.message_box_shown = False

    def parse_message(self, error_name, error_info=None):
        """Parses the request response and shows a messagebox."""
        if self.message_box_shown:
            return

        if error_name not in REQUEST_STRINGS.keys():
            error_name = 'unknown_error'

        error_message = REQUEST_STRINGS[error_name]['message']

        if error_info is not None:
            error_message = error_message.format(*error_info)

        self.message_box_shown = True
        self.show_message_box(
            REQUEST_STRINGS[error_name]['severity'],
            REQUEST_STRINGS[error_name]['title'],
            error_message,
        )

    def update_search_progress(self, progress):
        """Updates the search progress bar."""
        self.search_progress.setValue(progress * 100)

    def update_download_progress(self, progress):
        self.download_button.setEnabled(False)
        self.download_progress.setValue(progress)

    def start_loading(self, request_count):
        self.search_running = True

        # Turn on the search box
        if self.search_box.isSignalConnected(getSignal(self.search_box, 'returnPressed')):
            self.search_box.returnPressed.disconnect(self.search_button.click)

        # Start loading animation
        self.group_view.setEnabled(False)
        self.search_button.setEnabled(False)
        self.search_button.setVisible(False)
        self.search_button_cancel.setVisible(True)

        self.search_progress.show()
        self.search_progress.setMaximum(request_count * 100)

        self.search_anim.show()

    def end_loading(self):
        # Turn off the search box
        if not self.search_box.isSignalConnected(getSignal(self.search_box, 'returnPressed')):
            self.search_box.returnPressed.connect(self.search_button.click)

        # Stop loading animation
        self.group_view.setEnabled(True)

        self.search_button.setVisible(True)
        self.search_button.setEnabled(True)
        self.search_button_cancel.setEnabled(True)
        self.search_button_cancel.setVisible(False)

        self.search_progress.hide()
        self.search_progress.setValue(0)
        self.search_anim.hide()

        self.search_running = False

    def search(self):
        """Search for a tag or signature with a limit."""
        if self.search_running:
            return

        # Parse the search query, create a request batch and send it to the server

        if not self.search_box.text():
            return self.parse_message('no_query')

        request_batch = self.parse_query(self.search_box.text())

        if request_batch is None:
            return self.parse_message('illegal_query')

        request_count = len(request_batch)

        worker = self.workers['Search'] = SearchWorker(request_batch)
        thread = self.threads['Search'] = QThread(parent=self)

        thread.setObjectName('Search')

        worker.moveToThread(thread)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)

        self.cancel.connect(worker.stop)

        worker.finished.connect(self.end_loading)
        worker.finished.connect(self.retrieve)
        worker.errorred.connect(self.parse_message)
        worker.progress.connect(self.update_search_progress)
        worker.ready.connect(self.ready)

        thread.started.connect(worker.search)
        thread.finished.connect(thread.deleteLater)

        thread.start()
        self.start_loading(request_count)

    def ready(self):
        self.search_button_cancel.setEnabled(False)
        self.search_running = False

    def search_stop(self):
        """Stop the search"""
        print("Cancel button pressed")

        if not self.search_running:
            return

        self.cancel.emit()
        self.ready()

        if 'Search' in self.workers.keys():
            self.threads['Search'].quit()
            self.threads['Search'].wait()

    def retrieve(self, search_table):
        """Clean up after search"""
        self.search_table = search_table

        if not self.search_table:
            return

        # Remove previous search results
        self.model.removeRows(0, self.model.rowCount())

        # Get appropriate group, if it doesn't exist, create
        section = self.model.get_group('MalwareBazaar')

        if section is None:
            section = self.model.add_group('MalwareBazaar')

        # Populate it with samples (post process it)
        for sample in self.search_table:
            self.model.append_element(section, sample)

        # Acquire the groups
        root = self.model.invisibleRootItem()
        rows = root.rowCount()

        # Expand all groups
        self.group_view.expandAll()

        # Expand on demand (future version)
        #for root_items in range(rows):
        #    if root.child(root_items).index().sibling(0, 1).data(Qt.DisplayRole) == "MalwareBazaar":
        #        if not self.app.group_view.isExpanded(root.child(root_items).index()):
        #            self.app.group_view.expand(root.child(root_items).index())

    def download(self, sha256_hash):
        """Download the selected sample"""

        request_info = {
            'query': 'get_file',
            'sha256_hash': sha256_hash
        }

        # Find the sample with the given hash in the list
        index = 0

        for i, item in enumerate(self.search_table):
            if item['sha256_hash'] == sha256_hash:
                index = i

        # Create thread
        self.workers['Download'] = RequestWorker(request_info, self.search_table[index], 1000)
        self.threads['Download'] = create_thread(
            self.workers['Download'],
            [],
            'download',
            []
        )

        self.threads['Download'].start()
