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
    beginDownload = pyqtSignal(str)

    def __init__(self, model, parent=None):
        super(GroupView, self).__init__(parent)

        self.model = model

        # Overload default models
        self.setModel(model)
        self.setSelectionModel(QItemSelectionModel(self.model, self))

        # Set up the header
        self.setHeader(QHeaderView(Qt.Horizontal, self))
        self.init_header()

        # Set up the icon delegate
        custom_delegate = IconDelegate(self)
        self.setItemDelegateForColumn(0, custom_delegate)

        # Set custom context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        # Design
        self.setAnimated(True)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        # Edit / selection
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
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
        else:
            checkbox = self.model.itemFromIndex(index.siblingAtColumn(0))
            checkbox.setCheckState(not checkbox.checkState())
            # index.sibling(index.row(), 0).data(Qt.CheckStateRole) # This is a hack to make the checkbox work

    @pyqtSlot(QModelIndex)
    def on_double_clicked(self, index):
        if not index.parent().isValid():
            expander = index.siblingAtColumn(list(TREE_HEADER.keys()).index(''))
            self.setExpanded(expander, not self.isExpanded(expander))
        else:
            self.beginDownload.emit(
                index.siblingAtColumn(list(TREE_HEADER.keys()).index('SHA-256')).data(Qt.DisplayRole)
            )

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


class GroupSort(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(GroupSort, self).__init__(parent)


class GroupSelection(QItemSelectionModel):
    def __init__(self, parent=None):
        super(GroupSelection, self).__init__(parent)


class GroupModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(GroupModel, self).__init__(parent)

        self.setColumnCount(len(TREE_HEADER))
        self.setHorizontalHeaderLabels(TREE_HEADER.keys())

        for i in range(self.columnCount()):
            self.horizontalHeaderItem(i).setTextAlignment(Qt.AlignLeft)

        self.root_item = None

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.UserRole:
            if index.column() == list(TREE_HEADER.keys()).index('DL'):
                print("sort NOW")

        return super(GroupModel, self).data(index, role)

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

            # Set appropriate icon
            extension = info_dict['file_type'].lower()

            if extension not in FILE_ICONS.keys():
                extension = 'default'

            icon.setIcon(QIcon(FILE_ICONS[extension]))
            icon.setCheckable(True)

            group_name.setChild(last_row, column + 1, QStandardItem(info))

        # Set icon at column 0
        group_name.setChild(last_row, 0, icon)

    @staticmethod
    def remove_element(parent_group, row):
        parent_group.removeRow(row)
