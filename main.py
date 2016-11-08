import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))+"/lib")

import numpy as np 
from vispy import app, scene 
from vispy.util.filter import gaussian_filter
import vispy


from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from copy import deepcopy

from structs import region, preferences
from windows import preferences_window, log_window, update_dialog


class main_window(QWidget):

	def __init__(self, parent=None):

		super(main_window, self).__init__()
		self.initVars()
		self.initUI()

	# Initialize all member variables of class
	def initVars(self):
		self.regions = []
		self.user_preferences = preferences()
		self.user_log = log_window(self)
		self.pref_window = preferences_window(self)
		self.current_region = region()
		self.child_windows = []

	# Initialize the main UI
	def initUI(self):

		# Layout items
		self.layout = QVBoxLayout(self)
		self.layout.addSpacing(20)

		# Menu items
		self.menubar = QMenuBar(self)
		self.file_menu = self.menubar.addMenu("File")
		self.edit_menu = self.menubar.addMenu("Edit")
		self.tool_menu = self.menubar.addMenu("Tools")
		self.menubar.resize(self.menubar.sizeHint())

		# Menubar actions
		self.open_action = self.file_menu.addAction("Import...", self.import_file, QKeySequence("Ctrl+I"))
		self.stitch_action = self.file_menu.addAction("Stitch...", self.stitch_region, QKeySequence("Ctrl+S"))
		self.file_menu.addSeparator()
		self.export_image_action = self.file_menu.addAction("Export...", self.export_png, QKeySequence("Ctrl+E"))
		self.export_image_action.setEnabled(False)
		self.file_menu.addSeparator()
		self.new_window_action = self.file_menu.addAction("New Window", self.new_window, QKeySequence("Ctrl+N"))
		self.new_window_prefs_action = self.file_menu.addAction("New Window With Current Preferences", self.new_window_prefs, QKeySequence("Ctrl+Shift+N"))
		self.stitch_action.setEnabled(False)
		self.file_menu.addSeparator()
		self.exit_action = self.file_menu.addAction("Quit", self.quit_app, QKeySequence("Ctrl+Q"))
		
		self.prefs_action = self.edit_menu.addAction("Preferences", self.open_prefs, QKeySequence("Ctrl+P"))
		self.view_log_action = self.tool_menu.addAction("View Import Log", self.view_log, QKeySequence("Ctrl+L"))

		# Window details
		self.setWindowTitle("Terrain Parser")
		self.resize(900,700)

		QtCore.QObject.connect(self.pref_window, QtCore.SIGNAL("return_prefs(PyQt_PyObject)"), self.set_prefs)

		# Show the window
		self.show()	
		self.view_log()	

	# Exports the current plot as a .png image file
	def export_png(self):

		filename = QtGui.QFileDialog.getSaveFileName(self, "Export As", filter=".png")

		if filename != "":
			plot = self.get_plot()
			print plot
			#vispy.io.write_png(filename, self.get_plot.render())

	# Quits the app and closes all child windows
	def quit_app(self):
		self.collect_garbage()
		self.close()

	# Opens window with log of all imported files
	def view_log(self):
		my_point = self.rect().topRight()
		global_point = self.mapToGlobal(my_point)
		self.user_log.open(global_point)

	# Closes all auxiliary and child windows
	def collect_garbage(self):

		for child in self.child_windows:
			child.collect_garbage()

		self.user_log.close()
		self.pref_window.close()

	# Close all child windows when this one is closed
	def closeEvent(self, event):

		self.collect_garbage()
		event.accept()

	# Open a new child window with default preferences
	def new_window(self):

		temp = main_window(self)
		self.child_windows.append(temp)

	# Open a new window with same preferences
	def new_window_prefs(self):

		temp = main_window(self)
		temp.user_preferences.set_values(self.user_preferences)
		temp.pref_window.update_prefs(self.user_preferences)
		self.child_windows.append(temp)

	# Slot called from preferences window
	def set_prefs(self, pref):

		same = self.user_preferences.equal_to(pref)
		self.user_preferences.set_values(pref)

		print "here"

		if same:
			print "same"
			return

		if len(self.regions) != 0:
			print "here 2"
			ok = update_dialog.get_response()

			if ok:
				print "here 3"
				files = self.regions
				self.regions = []

				self.import_file(files[0])

				files = files[1:]

				for file in files:
					self.stitch_region(file)

	# Opens the preferences window
	def open_prefs(self):

		self.pref_window.open_window()

	# Returns the canvas plot (if one)
	def get_plot(self):

		try:
			return self.layout.takeAt(1)
		except:
			return "-1"

	# Clears the plot from the layout
	def clear_layout(self):

		self.export_image_action.setEnabled(False)

		plot = self.layout.takeAt(1)
		try:
			plot.widget().deleteLater()
		except:
			return
		
	# Stitches an adjacent region to the current
	def stitch_region(self, file=None):

		filename = file 

		if filename == None:
			filename = QFileDialog.getOpenFileName(self, "Select File", filter="*.asc")

		if filename != "":

			self.setWindowTitle("Terrain Parser - Rendering")

			temp_region = region()
			code 		= temp_region.parse_from_file(filename, self.user_preferences.import_compression_value)
		
			if code == -1:
				print "ERROR: Could not stitch regions together, probably not adjacent."
				return

			self.current_region.stitch(temp_region)

			temp = self.current_region.get_plot(start_x=0,start_y=0,compression_factor=self.user_preferences.plot_compression_value,type=self.user_preferences.plot_type,elev_scale=self.user_preferences.elev_scale_value)
			canvas_widget = QWidget(self)
			canvas_widget = temp.native

			self.clear_layout()
			self.layout.addWidget(canvas_widget)

			self.setWindowTitle("Terrain Parser")
			self.stitch_action.setEnabled(True)

			self.regions.append(filename)
			self.user_log.update("Stitch: "+filename)

	# Imports ArcInfo Ascii file
	def import_file(self, file=None):

		self.regions = []

		filename = file

		if filename == None:
			filename = QFileDialog.getOpenFileName(self, "Select File", filter="*.asc")

		if filename != "":

			self.setWindowTitle("Terrain Parser - Rendering")

			temp_region = region()
			code = temp_region.parse_from_file(filename,self.user_preferences.import_compression_value)
		
			if code == -1:
				print "ERROR: Could not import .asc file."
				return

			self.current_region = deepcopy(temp_region)

			self.cur_plot = self.current_region.get_plot(start_x=0,start_y=0,compression_factor=self.user_preferences.plot_compression_value,type=self.user_preferences.plot_type,elev_scale=self.user_preferences.elev_scale_value)
			canvas_widget = QWidget(self)
			canvas_widget = self.cur_plot.native

			self.clear_layout()
			self.layout.addWidget(canvas_widget)

			self.setWindowTitle("Terrain Parser")
			self.stitch_action.setEnabled(True)

			self.regions.append(filename)
			self.user_log.update("[CLEARING PLOT]")
			self.user_log.update("Import: "+filename)
			self.export_image_action.setEnabled(True)

def main():


	pyqt_app = QtGui.QApplication(sys.argv)
	pyqt_app.setWindowIcon(QIcon("resources/logo.png"))
	_ = main_window()
	sys.exit(pyqt_app.exec_())


if __name__ == '__main__':
	main()