import sys
import os
import time

import numpy as np 
from vispy import app, scene 
from vispy.util.filter import gaussian_filter
import vispy

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from copy import deepcopy

class region:

	def __init__(self):

		self.nrows 			= -1
		self.ncols 			= -1
		self.xllcorner 		= -1
		self.yllcorner 		= -1
		self.cellsize 		= -1
		self.NODATA_value 	= -1

		self.lower_border 	= -1
		self.upper_border 	= -1
		self.left_border 	= -1
		self.right_border 	= -1

		self.src_filename 	= ""
		self.data 			= []
		self.have_data 		= False

		self.real_ncols		= -1
		self.real_nrows		= -1

	# Parses in header info & data from a .asc file
	#
	# src = filename for source .asc file
	# compression_factor = save every nth data (1 would save all data, 2 save every other, etc.)
	def parse_from_file(self, src, compression_factor=1):

		if self.have_data:
			temp = region()
			temp.parse_from_file(src,compression_factor)
			return self.stitch(temp)

		start_time = time.time()
		self.src_filename = src

		print "Parsing region topography from "+src+"..."

		file = open(src,'r')
		tags = ["ncols","nrows","xllcorner","yllcorner","cellsize","NODATA_value"]

		for tag in tags:

			line 			= file.readline()
			line_attribs 	= line.split()

			if line_attribs[0] != tag:

				print "Could not locate ["+tag+"] tag in file header, found ["+line_attribs[0]+"] instead."
				return -1

			self.__dict__[tag] = line_attribs[1]

		self.nrows 			= int(self.nrows)
		self.ncols 			= int(self.ncols)
		self.xllcorner 		= float(self.xllcorner)
		self.yllcorner 		= float(self.yllcorner)
		self.cellsize 		= float(self.cellsize)
		self.NODATA_value	= int(self.NODATA_value)

		x_ctr = 0
		for i in range(self.nrows):
			x_ctr += 1
			line = file.readline()
			if (x_ctr % compression_factor) == 0:

				new_data = []
				vals = line.split()

				y_ctr = 0
				for val in vals:
					y_ctr += 1
					if(y_ctr % compression_factor) == 0:
						new_data.append(int(val))

				self.data.append(new_data)

		self.lower_border 	= self.yllcorner
		self.upper_border 	= self.yllcorner+(self.cellsize*self.nrows)
		self.left_border 	= self.xllcorner
		self.right_border 	= self.xllcorner+(self.cellsize*self.ncols)

		self.real_nrows = self.nrows/compression_factor
		self.real_ncols = self.ncols/compression_factor

		self.have_data = True
		#print "Data read & parsed in "+str(time.time()-start_time)+" seconds."
		#print "Upper border: "+str(self.upper_border)+", Lower border: "+str(self.lower_border)
		#print "Left border: "+str(self.left_border)+", Right border: "+str(self.right_border)
		return 1

	# Returns the elevation value at the specified column and row
	def get_elev_col_row(self, column, row):

		return float(self.data[column][row])

	# Returns the elevation value closest to the input latitude & longitude
	def get_elev_lat_long(self, latitude, longitude):

		if latitude<self.lower_border or latitude>self.upper_border:
			print "Latitude ("+str(latitude)+") out of range, cannot locate elevation."
			return -1

		if longitude<self.left_border or longitude>self.right_border:
			print "Longitude ("+str(longitude)+") out of range, cannot locate elevation."
			return -1

		cur_lat = self.upper_border
		
		for row in self.data:

			if cur_lat <= latitude:

				cur_long = self.left_border

				for cell in row:

					if cur_long >= longitude:

						return int(cell)

					cur_long += self.cellsize

			cur_lat -= self.cellsize

		print "ERROR: got to end of get_elev_lat_long function."
		return -1

	# Returns the float value of the average of all elevations in region
	def get_avg_elev(self):

		total = 0.0

		for row in self.data:
			for cell in row:
				total += float(cell)

		return float(total/(self.nrows*self.ncols))

	# Get lowest elev
	def get_lowest_elev(self):

		lowest = 10000

		for row in self.data:
			for cell in row:
				if int(cell) < lowest:
					lowest = int(cell)

		return lowest

	# Get highest elev
	def get_highest_elev(self):

		highest = 0

		for row in self.data:
			for cell in row:
				if int(cell) > highest:
					highest = int(cell)

		return highest

	# Creates surface plot of data
	def plot(self, start_x=0, start_y=0, span=-1, compression_factor=1, type="3D", elev_scale=0.1):

		start_time = time.time()

		int_data 	= []

		if start_y+span >= self.real_nrows:

			print "ERROR: Number of rows specified greater than total in data set."
			return

		if start_x+span >= self.real_ncols:

			print "ERROR: Number of columns specified greater than total in data set."
			return

		if span == -1:

			span_x = self.real_ncols - start_x
			span_y = self.real_nrows - start_y


		x_ctr = 0
		for i in xrange(start_y, start_y+span_y):
			x_ctr+=1

			if (x_ctr % compression_factor) == 0:	
				cur_row = self.data[i]
				new_row = []

				y_ctr = 0
				for j in xrange(start_x, start_x+span_x):
					y_ctr+=1

					if (y_ctr % compression_factor) == 0:
						new_row.append(int(self.data[i][j]))

				int_data.append(new_row)

		Z = np.array(int_data)

		canvas 		= scene.SceneCanvas(keys='interactive',title="Terrain Map")
		view 		= canvas.central_widget.add_view()

		if type == "3D":
			#view.camera = scene.PerspectiveCamera(mode='ortho',fov=60.0)
			view.camera = scene.TurntableCamera(up='z',center=(span_y*0.5/compression_factor,span_x*0.5/compression_factor,0))
		if type == "2D":	
			view.camera = scene.PanZoomCamera(up='z')

		# Black background, no paning, blue graph
		p1 = scene.visuals.SurfacePlot(z=Z, color=(0.5, 0.5, 1, 1), shading='smooth')

		p1.transform = scene.transforms.AffineTransform()
		#p1.transform.scale([1/49., 1/49., 0.02])
		#p1.transform.translate([-0.5, -0.5, 0])
		p1.transform.scale([1, 1, elev_scale])
		p1.transform.translate([0, 0, 0])

		view.add(p1)
		canvas.show()

		total_time = time.time()-start_time
		time_per_data = total_time/(span_x*span_y)
		print "Surface plot rendered in "+str(total_time)+" seconds ("+str(time_per_data)+" seconds/point)."
		app.run()
		
	def stitch(self, o_region):

		if self.have_data==False:

			self.data = o_region.data
			self.nrows = o_region.nrows
			self.ncols = o_region.ncols
			self.real_ncols = o_region.real_ncols
			self.real_nrows = o_region.real_nrows
			self.lower_border = o_region.lower_border
			self.upper_border = o_region.upper_border
			self.left_border = o_region.left_border
			self.right_border = o_region.right_border
			self.xllcorner = o_region.xllcorner
			self.yllcorner = o_region.yllcorner
			self.have_data=True
			return 1

		new_data = []

		if self.xllcorner>o_region.xllcorner and abs(self.yllcorner-o_region.yllcorner)<0.1:
			# Case that the other region is directly left of this region
			#print "Concatenating new region to left of current region."
			new_data = o_region.data

			i = 0
			for my_row in self.data:
				new_data[i].extend(my_row)
				i+=1

			self.data = new_data
			self.xllcorner = o_region.xllcorner
			self.ncols += o_region.ncols
			self.real_ncols += o_region.real_ncols
			return 1

		if self.xllcorner<o_region.xllcorner and abs(self.yllcorner-o_region.yllcorner)<0.1:
			# Case that the other region is directly right of this region
			#print "Concatenating new region to right of current region."
			new_data = self.data

			i=0
			for other_row in o_region.data:
				new_data[i].extend(other_row)
				i+=1

			self.data = new_data
			self.ncols += o_region.ncols
			self.real_ncols += o_region.real_ncols
			return 1

		if self.yllcorner<o_region.yllcorner and abs(self.xllcorner-o_region.xllcorner)<0.1:
			# Case that the other region is directly above this region
			#print "Concatenating new region above current region."
			new_data = o_region.data

			for my_row in self.data:
				new_data.append(my_row)

			self.data = new_data
			self.nrows += o_region.nrows
			self.real_nrows += o_region.real_nrows
			return 1


		if self.yllcorner>o_region.yllcorner and abs(self.xllcorner-o_region.xllcorner)<0.1:
			# Case that the other region is directly below this region
			#print "Concatenating new region below current region."
			new_data = self.data

			for other_row in o_region.data:
				new_data.append(other_row)

			self.data = new_data
			self.nrows += o_region.nrows
			self.real_nrows += o_region.real_nrows
			return 1

		print "ERROR: Got to end of stitch function without entering a case."
		return -1

	def save(self, res):

		print "inside save function, see exporting png in vispy documentation"

	def get_plot(self, start_x=0, start_y=0, span=-1, compression_factor=1, type="3D", elev_scale=0.1):

		start_time = time.time()

		int_data 	= []

		if start_y+span >= self.real_nrows:

			print "ERROR: Number of rows specified greater than total in data set."
			return

		if start_x+span >= self.real_ncols:

			print "ERROR: Number of columns specified greater than total in data set."
			return

		if span == -1:

			span_x = self.real_ncols - start_x
			span_y = self.real_nrows - start_y


		x_ctr = 0
		for i in xrange(start_y, start_y+span_y):
			x_ctr+=1

			if (x_ctr % compression_factor) == 0:	
				cur_row = self.data[i]
				new_row = []

				y_ctr = 0
				for j in xrange(start_x, start_x+span_x):
					y_ctr+=1

					if (y_ctr % compression_factor) == 0:
						new_row.append(int(self.data[i][j]))

				int_data.append(new_row)

		Z = np.array(int_data)

		canvas 		= scene.SceneCanvas(keys='interactive',title="Terrain Map")
		view 		= canvas.central_widget.add_view()

		if type == "3D":
			#view.camera = scene.PerspectiveCamera(mode='ortho',fov=60.0)
			view.camera = scene.TurntableCamera(up='z',center=(span_y*0.5/compression_factor,span_x*0.5/compression_factor,0))
		if type == "2D":	
			view.camera = scene.PanZoomCamera(up='z')

		# Black background, no paning, blue graph
		p1 = scene.visuals.SurfacePlot(z=Z, color=(0.5, 0.5, 1, 1), shading='smooth')

		p1.transform = scene.transforms.AffineTransform()
		p1.transform.scale([1, 1, elev_scale])
		p1.transform.translate([0, 0, 0])

		view.add(p1)
		return canvas

class preferences():

	def __init__(self):

		self.import_compression_value 	= 10
		self.plot_compression_value 	= 1
		self.elev_scale_value 			= 0.1
		self.plot_type 					= "3D"

	def equals(self, other):

		if self.import_compression_value != other.import_compression_value:
			return False
		if self.plot_compression_value != other.plot_compression_value:
			return False
		if self.elev_scale_value != other.elev_scale_value:
			return False
		if self.plot_type != other.plot_type:
			return False

		return True

	def set_values(self, other):

		self.import_compression_value = other.import_compression_value
		self.plot_compression_value = other.plot_compression_value
		self.elev_scale_value = other.elev_scale_value
		self.plot_type = other.plot_type

class preferences_window(QWidget):

	def __init__(self, parent=None):

		super(preferences_window,self).__init__()
		self.prefs = preferences()
		self.backend = False
		self.initUI()

	def update_prefs(self, other_prefs):

		self.prefs.set_values(other_prefs)

		self.backend = True

		self.import_compression = other_prefs.import_compression_value
		self.plot_compression = other_prefs.plot_compression_value
		self.elev_scale = other_prefs.elev_scale_value
		self.plot_type.setCurrentIndex(0)
		if other_prefs.plot_type == "2D":
			self.plot_type.setCurrentIndex(1)

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
		self.import_compression.setValue(10)
		self.import_compression.valueChanged.connect(self.prefs_changed)
		self.import_compression.move(175, 23)
		self.import_compression.setFixedWidth(50)

		self.plot_compression_label = QLabel("Plot Downscaling Factor: ", self)
		self.plot_compression_label.move(20, 60)
		self.plot_compression_label.setToolTip("If 1, show all data points. If 2, show every other data point, etc.")

		self.plot_compression = QSpinBox(self)
		self.plot_compression.setRange(1,20)
		self.plot_compression.setValue(1)
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
		self.elev_scale.setValue(0.10)
		self.elev_scale.setRange(0.01,4.00)
		self.elev_scale.setFixedWidth(50)
		self.elev_scale.move(175, 118)
		self.elev_scale.valueChanged.connect(self.prefs_changed)

		self.plot_type_label = QLabel("Plot Format: ",self)
		self.plot_type_label.move(20, 160)

		plot_types = ["3D","2D"]
		self.plot_type = QComboBox(self)
		self.plot_type.addItems(plot_types)
		self.plot_type.setCurrentIndex(0)
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

		self.import_compression.setValue(10)
		self.prefs.import_compression_value = 10

		self.plot_compression.setValue(1)
		self.prefs.plot_compression_value = 1

		self.elev_scale.setValue(0.1)
		self.prefs.elev_scale_value = 0.1

		self.plot_type.setCurrentIndex(0)
		self.prefs.plot_type = "3D"

		self.backend = False

	def save_prefs(self):

		self.emit(SIGNAL("return_prefs(PyQt_PyObject)"), self.prefs)
		self.hide()

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
		self.new_window_action = self.file_menu.addAction("New Window", self.new_window, QKeySequence("Ctrl+N"))
		self.new_window_prefs_action = self.file_menu.addAction("New Window With Current Preferences", self.new_window_prefs, QKeySequence("Ctrl+Shift+N"))
		self.stitch_action.setEnabled(False)
		self.prefs_action = self.edit_menu.addAction("Preferences", self.open_prefs)
		self.view_log_action = self.tool_menu.addAction("View Import Log", self.view_log)

		# Window details
		self.setWindowTitle("Terrain Parser")
		self.resize(800,400)

		QtCore.QObject.connect(self.pref_window, QtCore.SIGNAL("return_prefs(PyQt_PyObject)"), self.set_prefs)

		# Show the window
		self.show()	
		self.view_log()	

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

		same = self.user_preferences.equals(pref)
		self.user_preferences = pref

		if same:
			return

		if len(self.regions) != 0:
			ok = update_dialog.get_response()

			if ok:
				files = self.regions
				self.regions = []

				self.import_file(files[0])

				files = files[1:]

				for file in files:
					self.stitch_region(file)

	# Opens the preferences window
	def open_prefs(self):

		self.pref_window.open_window()

	# Clears the plot from the layout
	def clear_layout(self):

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

			temp = self.current_region.get_plot(start_x=0,start_y=0,compression_factor=self.user_preferences.plot_compression_value,type=self.user_preferences.plot_type,elev_scale=self.user_preferences.elev_scale_value)
			canvas_widget = QWidget(self)
			canvas_widget = temp.native

			self.clear_layout()
			self.layout.addWidget(canvas_widget)

			self.setWindowTitle("Terrain Parser")
			self.stitch_action.setEnabled(True)

			self.regions.append(filename)
			self.user_log.update("[CLEARING PLOT]")
			self.user_log.update("Import: "+filename)

def main():


	pyqt_app = QtGui.QApplication(sys.argv)
	pyqt_app.setWindowIcon(QIcon("resources/logo.png"))
	_ = main_window()
	sys.exit(pyqt_app.exec_())


if __name__ == '__main__':
	main()