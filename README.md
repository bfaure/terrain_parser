# terrain_parser
Tool that allows for reading, viewing, and stitching together of ArcInfo Ascii Terrain files. Terrain data can be found [here](http://srtm.csi.cgiar.org/SELECTION/inputCoord.asp) as well as several other .gov sites. 

[ArcInfo Ascii Format](https://en.wikipedia.org/wiki/Esri_grid)

## Screenshots
### User Interface
![Alt text](https://github.com/bfaure/terrain_parser/blob/master/resources/pic3.png)
![Alt text](https://github.com/bfaure/terrain_parser/blob/master/resources/Screen%20Shot%202016-11-07%20at%201.11.53%20AM.png)
![Alt text](https://github.com/bfaure/terrain_parser/blob/master/resources/Screen%20Shot%202016-11-07%20at%201.12.17%20AM.png)
### Preferences Pane
![Alt text](https://github.com/bfaure/terrain_parser/blob/master/resources/prefs.png)
### Plot Samples
![Alt text](https://github.com/bfaure/terrain_parser/blob/master/resources/USA.png)
![Alt text](https://github.com/bfaure/terrain_parser/blob/master/resources/ne.png)
![Alt text](https://github.com/bfaure/terrain_parser/blob/master/resources/ne2.png)

# Instructions
Either download as a .zip file or clone the repository using Git. After the /terrain_parser is saved on your computer, open up a terminal window, cd into the /terrain_parser directory, and type the command "python main.py" to open the UI interface. .asc files can be imported using the "Import" function found under the "File" menubar item. Subsequent .asc files can be added onto the plot using the "Stitch" function so long as they lie geogpraphically adjacent to the initial imported region. The following are several use cases representing both working (green) and not yet working (red/blue) .asc file importing sessions.
![Alt text](https://github.com/bfaure/terrain_parser/blob/master/resources/Capture.PNG)

## Dependencies
[Python 2.7](https://www.python.org/download/releases/2.7/)
, [PyQt4](https://www.riverbankcomputing.com/software/pyqt/download) 
, [VisPy](http://vispy.org/)

## Future Work
Add image overlay for maps, more tool functionality (paning), add more import use cases (see above tutorial), color selection, lat/long plot search, plot axes.
