from PyQt5 import QtGui, QtWidgets as w
from PyQt5.QtCore import pyqtSignal, Qt, QTimer

from deepinesStore.demoted_actions import browse, open_telegram_link

class G:
	def __init__(self, name, contact=None):
		self.name = name
		self.contact = contact

class NoClickableStyle(w.QProxyStyle):
	def __init__(self, parent=None, skip_indices=[]):
		super().__init__(parent)
		self.skip_indices = skip_indices

	def drawControl(self, element, option, painter, widget=None):
		if element == w.QStyle.CE_ItemViewItem:
			index = option.index
			if index.isValid() and index.row() in self.skip_indices:
				option.state &= ~w.QStyle.State_Enabled
				option.state &= ~w.QStyle.State_MouseOver
		super().drawControl(element, option, painter, widget)

class ClickableList(w.QListWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setAutoFillBackground(True)
		self.setFrameShape(w.QFrame.Shape.NoFrame)

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if event.buttons() == Qt.LeftButton:
			event.ignore()
		else:
			super().mouseMoveEvent(event)

	def set_skip_item_action_indices(self, skip_indices=[]):
		self.setStyle(NoClickableStyle(self.style(), skip_indices))

	# Accessibility!!
	def keyPressEvent(self, event):
		if event.key() in (Qt.Key_Enter, Qt.Key_Return):
			current_item = self.currentItem()
			if current_item:
				current_item.setSelected(True)
				self.itemClicked.emit(current_item)
		else:
			super().keyPressEvent(event)


# FIXME: Need to revisit this! AI is not a good coder!
class CreditsListWidget(w.QListWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.itemClicked.connect(self.on_item_click)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setStyleSheet("background-color: transparent;")
		self.setAutoFillBackground(True)
		self.setFrameShape(w.QFrame.Shape.NoFrame)
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.scroll)
		self.timer.start(30)  # scroll every 30 ms
		self.setVerticalScrollMode(w.QAbstractItemView.ScrollPerPixel)
		self.setMouseTracking(True) # enable mouse tracking
		self.is_paused = False
		
	def mousePressEvent(self, event):
		if event.buttons() == Qt.LeftButton:
			self.is_paused = True
			self.timer.stop()
		super().mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		if event.buttons() == Qt.LeftButton:
			self.is_paused = False
			self.timer.start()
		super().mouseReleaseEvent(event)

	def mouseMoveEvent(self, event):
		pos = self.mapFromGlobal(QtGui.QCursor.pos())
		'''
		if self.rect().contains(pos):
			self.is_paused = True
			self.timer.stop()
		else:
			self.is_paused = False
			self.timer.start()
		'''

	def on_item_click(self, item):
		contact = item.data(Qt.UserRole)
		if contact:
			if contact.startswith('@'):
				open_telegram_link(contact[1:])
			else:
				browse(f'mailto:{contact}')

	def scroll(self):
		if self.is_paused:
			return
		current_value = self.verticalScrollBar().value()
		if current_value == self.verticalScrollBar().maximum():
			self.verticalScrollBar().setValue(0)
		else:
			self.verticalScrollBar().setValue(current_value + 1)

class ClickableLabel(w.QLabel):
	clicked = pyqtSignal()

	def __init__(self, parent=None):
		super().__init__(parent)

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.clicked.emit()

class LinkLabel(w.QLabel):
	def on_link_clicked(self, link):
		if link.startswith("https://t.me/"):
			open_telegram_link(link[13:])
		else:
			browse(link)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setTextInteractionFlags(Qt.TextBrowserInteraction)
		self.linkActivated.connect(self.on_link_clicked)

def add_people_to_list(people, list_widget):
	group_box = w.QGroupBox()
	layout = w.QVBoxLayout()
	for person in people:
		item = w.QListWidgetItem()
		item.setText(person.name)
		item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
		item.setData(Qt.UserRole, person.contact)
		if person.contact:
			font = item.font()
			item.setFont(font)
			item.setForeground(QtGui.QColor('#4b71fa'))
			if person.contact.startswith('@'):
				item.setToolTip(f'Telegram: {person.contact}')
			else:
				item.setToolTip(f'Email: {person.contact}')
		list_widget.addItem(item)
	layout.addWidget(list_widget)
	group_box.setLayout(layout)
	return group_box

