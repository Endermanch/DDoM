import pyperclip
import humanize

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from strings import *

class NonSelectableDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return None


class IconDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(IconDelegate, self).__init__(parent)

        self.closed_icon = QIcon(":closed.png")
        self.opened_icon = QIcon(":opened.png")

    def initStyleOption(self, option, index):
        super(IconDelegate, self).initStyleOption(option, index)

        # If the item is a root group, set the open / close icon
        if not index.parent().isValid():
            option.features |= QStyleOptionViewItem.HasDecoration
            option.icon = self.opened_icon if option.state & QStyle.State_Open else self.closed_icon


class GroupView(QTreeView):
    beginDownload = pyqtSignal(int)

    def __init__(self, model, parent=None):
        super(GroupView, self).__init__(parent)

        self.setModel(model)
        self.setHeader(QHeaderView(Qt.Horizontal, self))

        self.init_header()

        custom_delegate = IconDelegate(self)
        self.setItemDelegateForColumn(0, custom_delegate)

        # Set custom context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        # Design
        self.setAnimated(True)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        # Edit / selection
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Setup slots
        self.clicked.connect(self.on_clicked)
        self.doubleClicked.connect(self.on_double_clicked)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def init_header(self):
        self.header().setSectionsClickable(True)
        self.header().setSectionsMovable(False)
        self.header().setStretchLastSection(True)

        for i, width in enumerate(TREE_HEADER.values()):
            self.header().resizeSection(i, width)

            if i == 0:
                self.header().setSectionResizeMode(i, QHeaderView.Fixed)

        self.header().sectionPressed.connect(self.on_section_press)

    @pyqtSlot(int)
    def on_section_press(self, index):
        if index == 0:
            return

    @pyqtSlot(QModelIndex)
    def on_clicked(self, index):
        if not index.parent().isValid():
            if index.column() == 0:
                self.setExpanded(index, not self.isExpanded(index))

    @pyqtSlot(QModelIndex)
    def on_double_clicked(self, index):
        if not index.parent().isValid():
            expander = index.siblingAtColumn(list(TREE_HEADER.keys()).index(''))
            self.setExpanded(expander, not self.isExpanded(expander))
        else:
            self.beginDownload.emit(index.row())

    @pyqtSlot(QPoint)
    def on_context_menu(self, pos):
        index = self.indexAt(pos)

        if not index.isValid() or index.column() == 0 or not index.parent().isValid():
            return

        menu = QMenu()

        copy_action = menu.addAction("&Copy")
        action = menu.exec_(self.viewport().mapToGlobal(pos))

        if action == copy_action:
            information = self.selectedIndexes()
            text = ""

            for column, data in enumerate(information):
                if column == index.column():
                    text = data.data()

            pyperclip.copy(str(text))


class GroupModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(GroupModel, self).__init__(parent)

        self.setColumnCount(len(TREE_HEADER))
        self.setHorizontalHeaderLabels(TREE_HEADER.keys())

        for i in range(self.columnCount()):
            self.horizontalHeaderItem(i).setTextAlignment(Qt.AlignLeft)

        self.root_item = None

    def add_group(self, group_name):
        self.root_item = QStandardItem()

        item = QStandardItem(group_name)
        root = self.invisibleRootItem()
        i = root.rowCount()
        for row, it in enumerate((self.root_item, item)):
            root.setChild(i, row, it)

        for column in range(self.columnCount()):
            it = root.child(i, column)

            if it is None:
                it = QStandardItem()
                root.setChild(i, column, it)

        return self.root_item

    def get_group(self, group_name):
        root = self.invisibleRootItem()

        for row in range(root.rowCount()):
            if root.child(row, 1).text() == group_name:
                return root.child(row, 0)

        return None

    @staticmethod
    def append_element(group_name, info_dict):
        last_row = group_name.rowCount()

        icon = QStandardItem()
        icon.setIcon(QIcon(":sample.png"))

        # Set icon at column 0
        group_name.setChild(last_row, 0, icon)

        # For each next column set info from the dictionary
        for column, (key, value) in enumerate(info_dict.items()):
            # Some elements need formatting
            match key:
                case 'file_size':
                    info = str(humanize.naturalsize(value))
                case 'tags':
                    info = str(value).replace('[', '').replace(']', '').replace("'", '')
                case _:
                    info = value

            group_name.setChild(last_row, column + 1, QStandardItem(info))

    @staticmethod
    def remove_element(parent_group, row):
        parent_group.removeRow(row)
