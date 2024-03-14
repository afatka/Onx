#!/usr/bin/env python

#Onx is a file management solution built for maya. 
#The tool finds all the the files of a certain type and allows quickly move from one file to the next
import maya.cmds as cmds
import os, logging, datetime, sys, subprocess
import maya.mel


class OnxFileManager(object):

	def __init__(self, fileTypesToFind = ('.mb', '.ma'), **kwargs):
		#control log silencing
		self.development = kwargs.get('development', False)#set up development / print log behavior
		
		self.log('kwargs: {}'.format(kwargs))
		self.full_vis = kwargs.get('vis', False) #sets default visibility for the interface
		self.write_log = kwargs.get('log', False) #sets default logging behavior
		self.colorize = kwargs.get('colorize', False) #sets default colorize behavior
		self.auto_sort = kwargs.get('autoSort', False) #sets default color sorting behavior)

		self.log('write_log: {}'.format(self.write_log))

		self.import_order = []
		self.log_active = False
		self.toolStarted = False
		self.uiPadding = 2
		#input args
		# self.pathType = pathSelection #1 is singleSection, 2 is allSections
		self.fileTypes = fileTypesToFind

		#possibly make it work on windows as well? no testing done
		if os.name == 'posix':
			self.fileSeparator = '/'
		else: self.fileSeparator = "\\"

		#declaration of variables
		
		self.completedFiles = []

		#build GUI
		self.fileManagerGUI()

	def toggle_colorize(self):
		self.log('toggle colorize')
		self.colorize = not self.colorize
		self.log('colorize: {}'.format(self.colorize))
		self.log('tool started: {}'.format(self.toolStarted))
		if self.colorize == True:#and self.toolStarted == True:
			self.log('make colorize!')
			self.make_colorize()
			
	def make_colorize(self):
		self.log('make colorize!')

		self.log('collect incomplete files. Color Red')
		#collect 'incomplete files path list'
		cmds.textScrollList(self.incompleteFilesScrollList, edit = True, deselectAll = True)
		incList = cmds.textScrollList(self.incompleteFilesScrollList, query = True, allItems = True)

		if incList != None:
			for i in range(1, len(incList)+1):
			    cmds.textScrollList(self.incompleteFilesScrollList, edit = True, selectIndexedItem = [i])

		redList = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectUniqueTagItem = True)
		self.log('redList: {}'.format(redList))
		#colorize incomplete files red
		if redList != None:
			self.colorize_list('red', redList)

		self.log('collect complete files. Color green')
		#collect completed files path list
		cmds.textScrollList(self.completeFilesScrollList, edit = True, deselectAll = True)
		compList = cmds.textScrollList(self.completeFilesScrollList, query = True, allItems = True)
		if compList != None:
			for i in range(1, len(compList)+1):
			    cmds.textScrollList(self.completeFilesScrollList, edit = True, selectIndexedItem = [i])

		greenList = cmds.textScrollList(self.completeFilesScrollList, query = True, selectUniqueTagItem = True)
		self.log('greenList: {}'.format(greenList))
		#colorize completed files green
		if greenList != None:
			self.colorize_list('green', greenList)
		cmds.textScrollList(self.completeFilesScrollList, edit = True, deselectAll = True)
		cmds.textScrollList(self.incompleteFilesScrollList, edit = True, deselectAll = True)

	def colorize_file(self, ColorName,FileName, *args):
		#The colorize code from from Stackoverflow user Beroe. Post is a comment on the following post
		# http://stackoverflow.com/a/19722230/5079170
		#slightly modified to suit purpose. 

		#provide color as a string. 
		#provide color name as a string... include containing quotes 

	    ReverseTable = {
	         "clear"  :  "01",
	         "gray"   :  "03",
	         "green"  :  "04",
	         "purple" :  "06",
	         "blue"   :  "09",
	         "yellow" :  "0A",
	         "red"    :  "0C",
	         "orange" :  "0E",
	         "c"      :  "01",
	         "a"      :  "03",
	         "g"      :  "04",
	         "p"      :  "06",
	         "b"      :  "09",
	         "y"      :  "0A",
	         "r"      :  "0C",
	         "o"      :  "0E",
	    }

	    HexString = 18*"0" + ReverseTable.get(ColorName) + 44*"0"
	    Xcommand = 'xattr -wx com.apple.FinderInfo {0} {1}'.format(HexString,"'" + FileName + "'")
	    ProcString = subprocess.check_call(Xcommand, stderr=subprocess.STDOUT,shell = True) 

	def colorize_list(self, colorName, fileList):
		self.log('colorize all')
		self.log('color: {}'.format(colorName))

		#initialize the progress bar
		gMainProgressBar = maya.mel.eval('$tmp = $gMainProgressBar')

		status = 'Colorize files: {}'.format(colorName)

		cmds.progressBar( gMainProgressBar,
	     edit=True, 
	     beginProgress=True, 
	     isInterruptable=True, 
	     status=status, 
	     maxValue=100 )

		step = 100/len(fileList)

		for f in fileList: 
			self.log('f: {}'.format(f))
			self.colorize_file(colorName, f )
			cmds.progressBar(gMainProgressBar, edit=True, step=step)

		cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)

	def clear_colors(self):
		self.log('clear colors')
		self.log('Import Files: ')
		f_list = []
		for f in self.import_order:
			self.log('Clearing: {}'.format(f[1]))
			# self.colorize_file('clear', f[1])
			f_list.append(f[1])
		self.colorize_list('clear', f_list)
		self.colorize = False
		cmds.menuItem(self.colorize_box, edit = True, checkBox = False)

	def toggle_auto_sort(self):
		self.log('toggle auto sort')
		self.auto_sort = not self.auto_sort
		self.log('auto_sort: {}'.format(self.auto_sort))

	def sort_file(self, inputFile):
		self.log('sort file')
		xcommand = "xattr -p com.apple.FinderInfo " + "'" + inputFile + "'"
		self.log('xcom: {}'.format(xcommand))
		try:
			ProcString = subprocess.check_output(xcommand, stderr=subprocess.STDOUT,shell = True)[27:29]
		except subprocess.CalledProcessError as e:
			cmds.warning('CalledProcessError: {}'.format(e.output))
			ProcString = ''
		
		# self.log('full string: {}'.format(subprocess.check_output(xcommand, stderr=subprocess.STDOUT,shell = True)))
		self.log('File Color: {}'.format(ProcString))
		self.log('repr: {}'.format(repr(ProcString)))
		self.log('=04: {}'.format(ProcString == '04'))
		if ProcString == '04':
			self.log('Green File Detected!\n moving to completed list')
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True, removeItem = inputFile.rsplit(self.fileSeparator)[-1])
			cmds.textScrollList(self.completeFilesScrollList, edit = True, append = [inputFile.rsplit(self.fileSeparator)[-1]], uniqueTag = [inputFile])

	def toggle_log(self):
		self.log('toggle log')
		self.log('write_log: {}'.format(self.write_log))
		self.write_log = not self.write_log
		self.log('write_log: {}'.format(self.write_log))
		if self.write_log == True and self.log_active == False:
			self.log('fire up the log!')
			self.do_log(self.workingDirectory)

	def do_log(self, directory):
		self.log('fire up logging and write logs')
		if self.write_log == True:
			self.logger = logging.getLogger(__name__)
			print(('name: {}'.format(__name__)))
			handler = logging.FileHandler(directory + 'Onx.log')
			formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt = '%m/%d/%y %H:%M' )
			handler.setFormatter(formatter)
			self.logger.addHandler(handler)
			self.logger.setLevel(logging.INFO)
			self.log_active = True
			self.output_log('Log Activated')

	def output_log(self, message):
		self.log('write to log')
		if self.write_log:
			self.logger.info(message)

	def runFileManager(self, pathSelection, *args):

		self.directoryContentPaths = []
		self.foundFiles = []
		self.pathType = pathSelection#1 is singleSection, 2 is allSections

		#ID working directory, make that directory functional
		try: 
			self.workingDirectory = cmds.fileDialog2(fileMode = 3, caption = 'Select Directory')[0] + self.fileSeparator
		except TypeError:
			cmds.error('Cancelled file add. Tool Stalled. ')
		
		self.log('working directory: {}'.format(self.workingDirectory))
		self.workingDirectoryOSWalk = self.workingDirectory

		if os.path.isdir(self.workingDirectory):
			self.log('self.workingDirectory is a directory')

		#capture contents of the self.workingDirectory, strip out 'extra'/ignore files
		directoryContents = self.stripFiles(os.listdir(self.workingDirectory))
		self.log('new directoryContents: {}'.format(directoryContents))

		
		for item in directoryContents:
			self.directoryContentPaths.append(self.workingDirectory + item)
		self.log('new item with path: {}'.format(self.directoryContentPaths))

		try:
			self.log('prefoundFiles declare: {}'.format(self.foundFiles))
		except:
			pass
		self.log('found Files: {}'.format(self.foundFiles))

		self.fileFinderOSWalk()

		self.log('{} maya files found'.format(len(self.foundFiles)))
		self.log('Maya files: {}'.format(self.foundFiles))

		if not self.log_active == False and self.write_log == True:
			self.do_log(self.workingDirectory)

		for fileItem in self.foundFiles:

			self.log('All Items in Completed: \n{}'.format(cmds.textScrollList(self.completeFilesScrollList, query = True, allItems = True)))
			self.log('item is: {}'.format(fileItem))
			completedFilesTempList = cmds.textScrollList(self.completeFilesScrollList, query = True, allItems = True)
			if completedFilesTempList is not None:
				if fileItem.rsplit(self.fileSeparator)[-1] in completedFilesTempList:
					self.log('added file is in completed list')
					cmds.textScrollList(self.completeFilesScrollList, edit = True, removeItem = fileItem.rsplit(self.fileSeparator)[-1])

			self.log('file name: {}'.format(fileItem.rsplit(self.fileSeparator)[-1]))
			incompleteFilesTempList = cmds.textScrollList(self.incompleteFilesScrollList, query = True, allItems = True)
			try: 
				cmds.textScrollList(self.incompleteFilesScrollList, edit = True, append = [fileItem.rsplit(self.fileSeparator)[-1]], uniqueTag = [fileItem])
			except RuntimeError:
				cmds.warning('File already in Queue, Ignoring File.')
			

		self.import_order_add()

		if self.auto_sort == True:

			gMainProgressBar = maya.mel.eval('$tmp = $gMainProgressBar')

			cmds.progressBar( gMainProgressBar,
		     edit=True, 
		     beginProgress=True, 
		     isInterruptable=True, 
		     status='Sorting File Colors', 
		     maxValue=100 )

			step = 100/len(self.foundFiles)

			for fileItem in self.foundFiles:
				self.sort_file(fileItem)
				cmds.progressBar(gMainProgressBar, edit=True, step=step)

			cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)

		if self.colorize == True:
			self.make_colorize()

	def loadNow(self, *args):
		self.log('Load File Now!')
		selection = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
		if selection == None: 
			cmds.error('No item selected')
		if len(selection) != 1:
			cmds.error('Please select only 1 entry to load now')
		self.toolStarted = False
		self.grade_next()
		self.runNextFile()

	def grade_next(self, *args):
		self.log('send selection to next')

		first_file = cmds.textScrollList(self.incompleteFilesScrollList, query = True, allItems = True)[0]

		currentSelection = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
		currentSelectionUniqueTags = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectUniqueTagItem = True)
		if currentSelection == None:
			cmds.error('No item selected')
		i = 1
		if self.toolStarted:
			i = 2
		i2 = 0
		for item in currentSelection:
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True, removeItem = item)	
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True,  appendPosition = [i, item], uniqueTag = currentSelectionUniqueTags[i2])
			i += 1
			i2 += 1

		if first_file in currentSelection and self.toolStarted == True:
				self.log('load next file')
				self.toolStarted = False
				self.runNextFile()

	def skip_current(self, *args):
		self.log('skip_current activated')
		original_selected = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
		top_file = cmds.textScrollList(self.incompleteFilesScrollList, edit = True, selectIndexedItem = 1)
		self.send_to_last()
		if original_selected != None:
			for item in original_selected:
				cmds.textScrollList(self.incompleteFilesScrollList, edit = True, selectItem = item)

	def send_to_last(self, *args):
		self.log('send selection to last')
		first_file = cmds.textScrollList(self.incompleteFilesScrollList, query = True, allItems = True)[0]

		currentSelection = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
		currentSelectionUniqueTags = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectUniqueTagItem = True)
		if currentSelection == None:
			cmds.error('No item selected')
		i = 0
		for item in currentSelection:
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True, removeItem = item)	
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True,  append = item, uniqueTag = currentSelectionUniqueTags[i])
			i += 1
		if first_file in currentSelection and self.toolStarted == True:
				self.log('load next file')
				self.toolStarted = False
				self.runNextFile()

	def what_is_the_next_file(self):
		original_selected = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
		if original_selected == None:
			try:
				cmds.textScrollList(self.incompleteFilesScrollList, edit = True, selectIndexedItem = [1])
			except RuntimeError:
				self.log('No Files to Select')
				next_file = None
				return next_file 
			next_file = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectUniqueTagItem = True)
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True, deselectIndexedItem = [1])
		else: 
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True, deselectAll = True)
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True, selectIndexedItem = [1])
			next_file = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectUniqueTagItem = True)
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True, deselectAll = True)
			for item in original_selected:
				cmds.textScrollList(self.incompleteFilesScrollList, edit = True, selectItem = item)
		return next_file[0], next_file[0].rsplit(self.fileSeparator)[-1]

	def what_is_the_current_file(self):
		currentFile = cmds.textScrollList(self.incompleteFilesScrollList, query = True, allItems = True)
		return currentFile[0]

	def is_last_file(self):
		self.log('Is this the last file?')
		itemCount = cmds.textScrollList(self.incompleteFilesScrollList, query = True, numberOfItems = True)
		if itemCount == 1:
			return True
		return False

	def cycle_file(self, *args):
		original_selected = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
		cmds.textScrollList(self.incompleteFilesScrollList, edit = True, deselectAll = True)
		cmds.textScrollList(self.incompleteFilesScrollList, edit = True, selectIndexedItem = [1])
		finishedFile = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
		if self.write_log == True:
			logging.info('{0} - {1}'.format(datetime.datetime.today().strftime("%m/%d/%Y"), finishedFile[0]))
		self.markAsComplete(cycle = True)
		cmds.textScrollList(self.incompleteFilesScrollList, edit = True, deselectAll = True)
		if original_selected != None:
			for item in original_selected:
				cmds.textScrollList(self.incompleteFilesScrollList, edit = True, selectItem = item)

	def markAsComplete(self, *args, **kwargs):
		
		first_file = cmds.textScrollList(self.incompleteFilesScrollList, query = True, allItems = True)[0]

		selected = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
		selectedUniqueTags = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectUniqueTagItem = True)
		i = 0
		if selected != None:
			for item in selected:
				cmds.textScrollList(self.incompleteFilesScrollList, edit = True, removeItem = item)
				cmds.textScrollList(self.completeFilesScrollList, edit = True, append = item, uniqueTag = selectedUniqueTags[i])
				i+=1
			if self.colorize == True:
					self.colorize_list('green', selectedUniqueTags )

			self.log('trying kwargs: {}'.format(kwargs.get('cycle', False)))
			if first_file in selected and self.toolStarted == True and not kwargs.get('cycle', False):
				self.log('load next file')
				self.toolStarted = False
				self.runNextFile()

		else: cmds.warning('No item selected from incompleted list.')

	def markAsIncomplete(self, *args):
		selected = cmds.textScrollList(self.completeFilesScrollList, query = True, selectItem = True)
		selectedUniqueTags = cmds.textScrollList(self.completeFilesScrollList, query = True, selectUniqueTagItem = True)
		i = 0
		if selected != None:
			for item in selected:
				cmds.textScrollList(self.completeFilesScrollList, edit = True, removeItem = item)
				cmds.textScrollList(self.incompleteFilesScrollList, edit = True, append = item, uniqueTag = selectedUniqueTags[i])
				i+=1
			if self.colorize == True:
					self.colorize_list('red', selectedUniqueTags)
		else: cmds.warning('No item selected from completed list.')

	def scrollListSelectCommand(self):
		if self.development:
			selected = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
			self.log('selected is: {}'.format(selected))
			uniqueSelected = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectUniqueTagItem = True)
			self.log('path: {}'.format(uniqueSelected))

	def stripFiles(self, directoryList):
		ignoreFiles = [".DS_Store", "workspace.mel"] 
		for item in ignoreFiles:
			if item in directoryList:
				directoryList.remove(item)
		return directoryList

	def fileFinderOSWalk(self, *args):
		directoryDepth = 0

		for directoryName, subDirectoryName, fileList in os.walk(self.workingDirectoryOSWalk):
			if directoryDepth == 0:
				directoryDepth = len(directoryName.split(self.fileSeparator))
			if len(directoryName.split(self.fileSeparator)) - directoryDepth >= 6:
				print('os.walk recursion break triggered')
				break
			
			for item in fileList:
				if item.endswith(self.fileTypes):
					self.log('directory name is: {}'.format(directoryName))
					self.log('file name: {}'.format(item))
					if directoryName.endswith(self.fileSeparator):
						fileToAdd = directoryName + item
					else:
						fileToAdd = directoryName + self.fileSeparator + item
					self.foundFiles.append(fileToAdd)

	def removeFile(self, *args):
		
		first_file = cmds.textScrollList(self.incompleteFilesScrollList, query = True, allItems = True)[0]
		self.log('first file: {0}'.format(first_file))

		self.log('Remove a File from Queue')
		incompleteFilesSelected = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
		incompleteFilesSelectedUniqueTags = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectUniqueTagItem = True)
		completeFilesSelected = cmds.textScrollList(self.completeFilesScrollList, query = True, selectItem = True)
		completeFilesSelectedUniqueTags = cmds.textScrollList(self.completeFilesScrollList, query = True, selectUniqueTagItem = True)
		selected = []
		removalString = ''
		if  incompleteFilesSelected is not None:
			removalString += 'Remove {} queued files?'.format(len(incompleteFilesSelected))
			for selectedFile in incompleteFilesSelected:
				selected.append(selectedFile)
		if completeFilesSelected is not None:
			removalString += '\nRemove {} graded files'.format(len(completeFilesSelected))
			for selectedFile in completeFilesSelected:
				selected.append(selectedFile)
		self.log('selected: {}'.format(selected))
		if selected:
			if cmds.confirmDialog( title='Confirm Removal,\n Are you sure?', message=removalString, button=['Remove File','Cancel'], defaultButton='Remove File', cancelButton='Cancel', dismissString='No' ) == 'Remove File':
				for item in selected:
					self.log('Removing file: {}'.format(item))
					if incompleteFilesSelected != None and item in incompleteFilesSelected:

						cmds.textScrollList(self.incompleteFilesScrollList, edit = True, deselectAll = True)
						cmds.textScrollList(self.incompleteFilesScrollList, edit = True, selectItem = item)
						f = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectUniqueTagItem = True)
						self.colorize_file('clear', f[0])
						cmds.textScrollList(self.incompleteFilesScrollList, edit = True, deselectAll = True)

						cmds.textScrollList(self.incompleteFilesScrollList, edit = True, removeItem = item)
					else:

						cmds.textScrollList(self.completeFilesScrollList, edit = True, deselectAll = True)
						cmds.textScrollList(self.completeFilesScrollList, edit = True, selectItem = item)
						f = cmds.textScrollList(self.completeFilesScrollList, query = True, selectUniqueTagItem = True)
						self.colorize_file('clear', f[0])
						cmds.textScrollList(self.completeFilesScrollList, edit = True, deselectAll = True)

						cmds.textScrollList(self.completeFilesScrollList, edit = True, removeItem = item)
					self.log('Removed file: {}'.format(item))
			if first_file in selected and self.toolStarted == True:
				self.log('load next file')
				self.toolStarted = False
				self.runNextFile()
				

		else: cmds.warning('No item selected from lists for removal.')

	def removeCompletedFile(self, *args):
		self.log('remove complted file')
		completeFilesSelected = cmds.textScrollList(self.completeFilesScrollList, query = True, selectItem = True)
		for item in completeFilesSelected:
			cmds.textScrollList(self.completeFilesScrollList, edit = True, removeItem = item)

	def removeIncompleteFile(self, *args):
		self.log('remove complted file')
		incompleteFilesSelected = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectItem = True)
		for item in incompleteFilesSelected:
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True, removeItem = item)

	def runNextFile(self):
		self.log('This method will run all methods necessary to move from one file to another')
		if not self.toolStarted:
			self.log('cycle the active file to the completed list')
			cmds.button(self.next_button, edit = True, label = 'Next File')
			self.toolStarted = True
		else:
			self.log('else statement: Tool started - Cycle File')
			self.output_log(self.what_is_the_next_file()[1])
			self.cycle_file()
		self.log('capture next file')
		nextFile = self.what_is_the_next_file()
		self.log('nextFile: {}'.format(nextFile))
		if nextFile != None:
			self.log('nextFile != None')
			self.log('New Maya Scene')
			cmds.file(force = True, newFile = True)
			self.log('load the next Maya file')
			try:
				self.log('we are in the "try" - open the file')
				cmds.file(nextFile[0], open = True)
			except RuntimeError:
				cmds.warning('File is from Maya {}. Ignoring version.'.format(cmds.fileInfo('version', query = True)))
				cmds.warning('Errors may occur')
				cmds.file(nextFile[0], open = True, ignoreVersion = True)
			self.log('end of file loading')
		else:
			self.endOfQueue()

	def endOfQueue(self):
		button_str = ['Add Files', 'Done!']
		if self.colorize == True:
			button_str = ['Add Files', 'Remove Color, Done!', 'Done!']
		dialog = cmds.confirmDialog( title="You've reached the end of the queue!", 
			message='Are you finished?', 
			button=button_str, 
			defaultButton='Done!', 
			cancelButton='Done!', 
			dismissString='Done!')
		# self.reset()
		if dialog == 'Add Files':
			self.log('Add Files')
			dialog_return = self.runFileManager(1)
			print(('dialog_return: {}'.format(dialog_return)))
		elif dialog == 'Remove Color, Done!':
			self.log('Removing Color...done!')
			self.clear_colors()
			cmds.deleteUI('OnxWin')
			cmds.file(force = True, newFile = True)

		elif dialog == 'Done!':
			self.log('Done!')
			cmds.deleteUI('OnxWin')
			cmds.file(force = True, newFile = True)
		else:
			cmds.error('I think the dialog is broken?')

	def fileManagerGUI(self):
		"""
		Stand alone GUI element. Single UI Parent required to return
		"""

		# self.full_vis = False

		#if Onx File Wrangler window exists delete it
		if (cmds.window('OnxWin', exists = True)):
			cmds.deleteUI('OnxWin')
		# if preferences exist, delete them
		if self.development:
			if (cmds.windowPref('OnxWin', exists = True)):
				cmds.windowPref('OnxWin', remove = True)

		doWindow = True
		scrollListWidth = 75
		scrollListHeight = 155
		buttonWidth = 95
		addonTitle = ''
		if self.development == True:
			addonTitle = ' Dev'
		windowTitle = 'Onx File Wrangler' + addonTitle
		if doWindow:
			cmds.window('OnxWin', title = windowTitle, width = scrollListWidth, menuBar = True, height = 216)
			cmds.menu(label = 'Sorting')
			cmds.menuItem(label = 'Reverse', command = lambda *args: self.sort_reverse())
			cmds.menuItem(label = 'Alphabetical', command = lambda *args: self.sort_alpha())
			cmds.menuItem(label = 'Modified Date', command = lambda *args: self.sort_modified())
			cmds.menuItem(label = 'Import Order', command = lambda *args: self.sort_import_order())
			cmds.menu(label = 'Tracking')
			cmds.menuItem(label = 'Logging', checkBox = self.write_log, command = lambda *args: self.toggle_log())
			self.colorize_box = cmds.menuItem(label = 'Colorize', checkBox = self.colorize, command = lambda *args: self.toggle_colorize())
			cmds.menuItem(label = 'Auto Sort Color', checkBox = self.auto_sort, command = lambda *args: self.toggle_auto_sort())
			cmds.menuItem(label = 'Clear All Color', command = lambda *args: self.clear_colors())
			# cmds.menu(label = 'Edit Queue')
			# cmds.menuItem(label = 'Remove Read')
		self.master_form = cmds.formLayout(numberOfDivisions = 200, width = 220)
		self.fileManagerFormLayout = cmds.formLayout('fileManager Form Layout', numberOfDivisions = 200, width = 220)

		self.addFileButton = cmds.button(label = 'Add File +', command = lambda *args: self.runFileManager(1), width = buttonWidth)
		self.menuButton = cmds.button(label = '|||', command = lambda *args: self.cycle_GUI_vis(), width = 15)
		self.removeFileButton = cmds.button(label = '- Remove File', command = self.removeFile, width = buttonWidth)
		fieldSeparator1 = cmds.separator()
		self.incompleteFilesScrollList = cmds.textScrollList(numberOfRows=10, allowMultiSelection=True, selectCommand = self.scrollListSelectCommand, width = scrollListWidth, height = scrollListHeight, font = "smallObliqueLabelFont", deleteKeyCommand = self.removeIncompleteFile)
		cmds.popupMenu(parent = self.incompleteFilesScrollList, button = 3)
		cmds.menuItem(label = 'Send to Next', command = self.grade_next)
		cmds.menuItem(label = 'Send to Bottom', command = self.send_to_last)
		cmds.menuItem(label = 'Load now', command = self.loadNow)
		self.next_button = cmds.button(label = 'Start Files', command = lambda *args: self.runNextFile(), width = scrollListWidth)
		cmds.setParent(self.fileManagerFormLayout)
		cmds.setParent(self.master_form)

		self.lowerFormLayout = cmds.formLayout('lowerFormLayout', numberOfDivisions = 200, width = 220)
		self.fieldSeparator2 = cmds.separator()
		self.markAsCompleteButton = cmds.button(label = 'Mark as Done v', command = self.markAsComplete, width = buttonWidth)
		self.markAsIncompleteButton = cmds.button(label = '^ Add to Queue', command = self.markAsIncomplete, width = buttonWidth)
		self.fieldSeparator3 = cmds.separator()
		self.completeFilesScrollList = cmds.textScrollList(numberOfRows=10, allowMultiSelection=True, width = scrollListWidth, height = scrollListHeight, font = "smallObliqueLabelFont", deleteKeyCommand = self.removeCompletedFile)
		cmds.setParent(self.lowerFormLayout)
		cmds.setParent(self.master_form)

		cmds.formLayout(self.master_form, edit = True, 
			attachForm = [
			(self.fileManagerFormLayout, 'top', self.uiPadding),
			(self.fileManagerFormLayout, 'left', self.uiPadding),
			(self.fileManagerFormLayout, 'right', self.uiPadding),
			(self.lowerFormLayout, 'left', self.uiPadding),
			(self.lowerFormLayout, 'right', self.uiPadding)
			],
			attachControl = [
			(self.lowerFormLayout, 'top', self.uiPadding, self.fileManagerFormLayout)
			])
		
		cmds.formLayout(self.fileManagerFormLayout, edit = True, 
			attachForm = [
			(self.addFileButton, 'top', self.uiPadding),
			(self.addFileButton, 'left', self.uiPadding),
			(self.menuButton, 'top', self.uiPadding),
			(self.removeFileButton, 'top', self.uiPadding),
			(self.removeFileButton, 'right', self.uiPadding),
			(fieldSeparator1, 'right', self.uiPadding),
			(fieldSeparator1, 'left', self.uiPadding),
			(self.incompleteFilesScrollList, 'left', self.uiPadding),
			(self.incompleteFilesScrollList, 'right', self.uiPadding),
			(self.next_button, 'left', self.uiPadding),
			(self.next_button, 'right', self.uiPadding)
			],
			attachControl = [
			(self.addFileButton, 'right', self.uiPadding, self.menuButton),
			(self.menuButton, 'right', self.uiPadding, self.removeFileButton),
			(fieldSeparator1, 'top', self.uiPadding, self.addFileButton),
			(self.incompleteFilesScrollList, 'top', self.uiPadding, fieldSeparator1),
			(self.next_button, 'top', self.uiPadding, self.incompleteFilesScrollList)
			])

		cmds.formLayout(self.lowerFormLayout, edit = True, 
			attachForm = [
			(self.fieldSeparator2, 'top', self.uiPadding),
			(self.fieldSeparator2, 'right', self.uiPadding), 
			(self.fieldSeparator2, 'left', self.uiPadding),
			(self.markAsCompleteButton, 'left', self.uiPadding),
			(self.markAsIncompleteButton, 'right', self.uiPadding),
			(self.fieldSeparator3, 'right', self.uiPadding), 
			(self.fieldSeparator3, 'left', self.uiPadding),
			(self.completeFilesScrollList, 'left', self.uiPadding),
			(self.completeFilesScrollList, 'right', self.uiPadding),
			],
			attachControl = [
			(self.markAsCompleteButton, 'top', self.uiPadding, self.fieldSeparator2), 
			(self.markAsCompleteButton, 'right', self.uiPadding, self.markAsIncompleteButton),
			(self.markAsIncompleteButton, 'top', self.uiPadding, self.fieldSeparator2),
			(self.fieldSeparator3, 'top', self.uiPadding, self.markAsIncompleteButton),
			(self.completeFilesScrollList, 'top', self.uiPadding, self.fieldSeparator3)
			])

		cmds.formLayout(self.lowerFormLayout, edit = True, visible = self.full_vis)
		if self.full_vis == False:
			cmds.window('OnxWin', edit = True, height = 216)
		if doWindow:
			cmds.showWindow()
		self.log('Window Height = {}'.format(cmds.window('OnxWin', query = True, height = True)))

	def cycle_GUI_vis(self):
		self.log('cycle GUI vis')
		self.full_vis = not self.full_vis
		cmds.formLayout(self.lowerFormLayout, edit = True, visible = self.full_vis)
		if self.full_vis == False:
			cmds.window('OnxWin', edit = True, height = 216)
		self.log(cmds.window('OnxWin', query = True, height = True))

	def sort_alpha(self):
		self.log('sort alpha')
		file_list = self.collect_files()
		self.log('back from collect_files')
		sorted_list = sorted(file_list, key=lambda x:x[0].lower())
		self.log('New list: ')
		self.log(sorted_list)
		self.repop_incomplete_list(sorted_list)
		self.sort_reload()

	def import_order_add(self):
		self.log('import order add')
		file_list = self.collect_files()
		for f in file_list:
			if f not in self.import_order:
				self.import_order.append(f)
		self.log('import order: {}'.format(self.import_order))
		self.sort_reload()

	def sort_import_order(self):
		self.log('sort import order')
		new_order = []
		file_list = self.collect_files()
		for f in self.import_order:
			if f in file_list:
				new_order.append(f)
		self.repop_incomplete_list(new_order)
		self.sort_reload()

	def sort_modified(self):
		self.log('sort motified date')
		file_list = self.collect_files()
		sorted_list = sorted(file_list, key=lambda x: os.stat(x[1]).st_mtime)
		self.repop_incomplete_list(sorted_list)
		self.sort_reload()

	def sort_reverse(self):
		self.log('sort reverse order')
		list_items = self.collect_files()
		self.log('files: {}\n'.format(list_items))
		list_items.reverse()
		self.log('rev?: {}\n'.format(list_items))
		self.repop_incomplete_list(list_items)
		self.sort_reload()

	def repop_incomplete_list(self, list_of_tagUTag_tuples):
		self.log('repopulate incomplete list')
		#list_of_tagUtag_tuples should be a structured as such [(item, item unique tag), (item2, item2 unique tag)]
		cmds.textScrollList(self.incompleteFilesScrollList, edit = True, removeAll = True)

		for f in list_of_tagUTag_tuples:
			cmds.textScrollList(self.incompleteFilesScrollList, edit = True, append = f[0], uniqueTag = f[1])

	def sort_reload(self):
		if self.toolStarted:
			self.toolStarted = False
			self.runNextFile()

	def collect_files(self):
		self.log('collect_files')
		cmds.textScrollList(self.incompleteFilesScrollList, edit = True, deselectAll = True)
		selected = cmds.textScrollList(self.incompleteFilesScrollList, query = True, allItems = True)

		for i in range(1, len(selected)+1):
		    cmds.textScrollList(self.incompleteFilesScrollList, edit = True, selectIndexedItem = [i])

		selectedUniqueTags = cmds.textScrollList(self.incompleteFilesScrollList, query = True, selectUniqueTagItem = True)
		list_items =  list(zip(selected, selectedUniqueTags))
		return list_items

	def reset(self):
		self.toolStarted = False
		cmds.textScrollList(self.incompleteFilesScrollList, edit = True, removeAll = True)
		cmds.textScrollList(self.completeFilesScrollList, edit = True, removeAll = True)

	def log(self, message, prefix = 'Onx: '):
		if self.development:
			print(('{0} {1}'.format(prefix, message)))
