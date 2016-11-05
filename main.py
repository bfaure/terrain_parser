import sys
import os
import time

import numpy as np 
from vispy import app, scene 
from vispy.util.filter import gaussian_filter
import vispy



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
				return

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
		print "Data read & parsed in "+str(time.time()-start_time)+" seconds."
		print "Upper border: "+str(self.upper_border)+", Lower border: "+str(self.lower_border)
		print "Left border: "+str(self.left_border)+", Right border: "+str(self.right_border)

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
	def plot(self, start_x=0, start_y=0, span=-1, compression_factor=1, type="3D"):

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
		p1.transform.scale([1, 1, 0.10])
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
			return

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
			return

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
			return

		if self.yllcorner<o_region.yllcorner and abs(self.xllcorner-o_region.xllcorner)<0.1:
			# Case that the other region is directly above this region
			#print "Concatenating new region above current region."
			new_data = o_region.data

			for my_row in self.data:
				new_data.append(my_row)

			self.data = new_data
			self.nrows += o_region.nrows
			self.real_nrows += o_region.real_nrows
			return


		if self.yllcorner>o_region.yllcorner and abs(self.xllcorner-o_region.xllcorner)<0.1:
			# Case that the other region is directly below this region
			#print "Concatenating new region below current region."
			new_data = self.data

			for other_row in o_region.data:
				new_data.append(other_row)

			self.data = new_data
			self.nrows += o_region.nrows
			self.real_nrows += o_region.real_nrows
			return

		print "ERROR: Got to end of stitch function without entering a case."

	def save(self, res):

		print "inside save function, see exporting png in vispy documentation"


def main():

	"""
	file_pre = "data/srtm_"
	file_post = ".asc"
	cols = ["12","13","14","15","16","17","18","19","20","21","22"]
	rows = ["03","04","05"]

	usa = region()

	for row in rows:

		usa_row = region()

		for col in cols:

			filename = "data/srtm_"+col+"_"+row+".asc"
			temp = region()
			temp.parse_from_file(filename,compression_factor=4)
			usa_row.stitch(temp)

		usa.stitch(usa_row)

	usa.plot(start_x=0,start_y=0,compression_factor=5,type="3D")
	"""
	file = "data/srtm_22_04.asc"
	reg = region()
	reg.parse_from_file(file)
	reg.plot(start_x=0,start_y=0,compression_factor=1,type="3D")


if __name__ == '__main__':
	main()