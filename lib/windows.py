
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from structs import preferences
from structs import _DEFAULT_IMPORT_COMPRESSION_VALUE, _DEFAULT_PLOT_COMPRESSION_VALUE, _DEFAULT_ELEV_SCALE_VALUE, _DEFAULT_PLOT_TYPE 


class preferences_window(QWidget):

	def __init__(self, parent=None):

		super(preferences_window,self).__init__()
		self.prefs = preferences()
		self.backend = False
		self.initUI()

	def update_prefs(self, other_prefs):

		self.prefs.set_values(other_prefs)

		self.backend = True

		self.import_compression.setValue(self.prefs.import_compression_value)
		self.plot_compression.setValue(self.prefs.plot_compression_value)
		self.elev_scale.setValue(self.prefs.elev_scale_value)
		self.plot_type.setCurrentIndex(0 if self.prefs.plot_type=="3D" else 1)
		
		self.backend = False

	def initUI(self):

		self.setFixedWidth(250)
		self.setFixedHeight(325)

		self.setWindowTitle("Preferences")

		self.import_compression_label = QLabel("Import Compression Factor: ", self)
		self.import_compression_label.move(20, 25)
		self.import_compression_label.setToolTip("If 1, import all data points. If 2, import every other data point, etc.")

		self.import_compression = QSpinBox(self)
		self.import_compression.setRange(1,20)
		self.import_compression.setValue(_DEFAULT_IMPORT_COMPRESSION_VALUE)
		self.import_compression.valueChanged.connect(self.prefs_changed)
		self.import_compression.move(175, 23)
		self.import_compression.setFixedWidth(50)

		self.plot_compression_label = QLabel("Plot Downscaling Factor: ", self)
		self.plot_compression_label.move(20, 60)
		self.plot_compression_label.setToolTip("If 1, show all data points. If 2, show every other data point, etc.")

		self.plot_compression = QSpinBox(self)
		self.plot_compression.setRange(1,20)
		self.plot_compression.setValue(_DEFAULT_PLOT_COMPRESSION_VALUE)
		self.plot_compression.valueChanged.connect(self.prefs_changed)
		self.plot_compression.move(175, 58)
		self.plot_compression.setFixedWidth(50)

		self.divider = QFrame(self)
		self.divider.setFrameShape(QFrame.HLine)
		self.divider.move(20, 85)
		self.divider.setFixedWidth(210)

		self.elev_scale_label = QLabel("Elevation Scaling: ", self)
		self.elev_scale_label.move(20, 120)
		self.elev_scale_label.setToolTip("Anywhere in range 0.01 to 4.00")

		self.elev_scale = QDoubleSpinBox(self)
		self.elev_scale.setDecimals(2)
		self.elev_scale.setValue(_DEFAULT_ELEV_SCALE_VALUE)
		self.elev_scale.setRange(0.01,4.00)
		self.elev_scale.setFixedWidth(50)
		self.elev_scale.move(175, 118)
		self.elev_scale.valueChanged.connect(self.prefs_changed)

		self.plot_type_label = QLabel("Plot Format: ",self)
		self.plot_type_label.move(20, 160)

		plot_types = ["3D","2D"]
		self.plot_type = QComboBox(self)
		self.plot_type.addItems(plot_types)
		self.plot_type.setCurrentIndex(0 if _DEFAULT_PLOT_TYPE == "3D" else 1)
		self.plot_type.move(175, 158)
		self.plot_type.currentIndexChanged.connect(self.prefs_changed)
		self.plot_type.setFixedWidth(50)

		self.save_prefs_button = QPushButton("Save", self)
		self.save_prefs_button.move(45,295)
		self.save_prefs_button.clicked.connect(self.save_prefs)

		self.reset_prefs_button = QPushButton("Reset", self)
		self.reset_prefs_button.move(135, 295)
		self.reset_prefs_button.clicked.connect(self.reset_prefs)

	def reset_prefs(self):

		self.backend = True

		self.import_compression.setValue(_DEFAULT_IMPORT_COMPRESSION_VALUE)
		self.prefs.import_compression_value = _DEFAULT_IMPORT_COMPRESSION_VALUE

		self.plot_compression.setValue(_DEFAULT_PLOT_COMPRESSION_VALUE)
		self.prefs.plot_compression_value = _DEFAULT_PLOT_COMPRESSION_VALUE

		self.elev_scale.setValue(_DEFAULT_ELEV_SCALE_VALUE)
		self.prefs.elev_scale_value =_DEFAULT_ELEV_SCALE_VALUE

		self.plot_type.setCurrentIndex(0 if _DEFAULT_PLOT_TYPE=="3D" else 1)
		self.prefs.plot_type = _DEFAULT_PLOT_TYPE

		self.backend = False

	def save_prefs(self):
		
		self.prefs_changed()
		self.hide()
		self.emit(SIGNAL("return_prefs(PyQt_PyObject)"), self.prefs)

	def open_window(self, location=None):
		if location == None:
			self.show()
		else:
			self.move(location)
			self.show()

	def prefs_changed(self):

		if self.backend == False:

			self.prefs.import_compression_value = self.import_compression.value()
			self.prefs.plot_compression_value = self.plot_compression.value()
			self.prefs.elev_scale_value = self.elev_scale.value()
			self.prefs.plot_type = self.plot_type.currentText()

class log_window(QWidget):

	def __init__(self, parent=None):
		super(log_window, self).__init__()
		self.initVars()
		self.initUI()

	def initVars(self):
		self.imports = []

	def initUI(self):

		self.layout = QVBoxLayout(self)
		self.setWindowTitle("Import Log")

		self.log = QTextEdit(self)
		self.layout.addWidget(self.log)
		self.resize(400, 600)

	def open(self,location=None):
		if location == None:
			self.show()
		else:
			self.move(location)
			self.show()

	def update(self, new_import):

		self.imports.append(new_import)
		self.log.append(new_import)

class update_dialog(QDialog):

	def __init__(self, parent=None):
		super(update_dialog, self).__init__(parent)

		layout = QVBoxLayout(self)

		self.notice = QLabel("You have made changes to the plot preferences, \nwould you like to reload the current plot with \nthe new preferences?")
		self.setWindowTitle("Alert")
		layout.addWidget(self.notice)

		buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)

	@staticmethod
	def get_response(parent = None):
		dialog = update_dialog(parent)
		result = dialog.exec_()
		return(result == QDialog.Accepted)