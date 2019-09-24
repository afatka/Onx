#! /usr/bin/env python
#install Onx

import maya.cmds as cmds
import maya.mel as mel
import os
def install():

	#ask the user to install Onx on the active shelf or a new shelf
	install_type = cmds.confirmDialog( 
		title='Install Onx', 
		message='Install to active shelf or new shelf?', 
		button=['Active','New'], 
		defaultButton='New', 
		cancelButton='Cancel', 
		dismissString='New' )

	if install_type == 'Cancel':
		cmds.error('Onx Install Cancelled.')
	icon_dir = os.path.join(os.path.dirname(__file__), 'icons')
	parent_shelfTabLayout = mel.eval("global string $gShelfTopLevel; $temp = $gShelfTopLevel;") 
	shelves = cmds.tabLayout(parent_shelfTabLayout, query = True, childArray = True)
	if install_type == 'Active':
		for shelf in shelves:
		    if cmds.shelfLayout(shelf, query = True, visible = True):
		        install_shelf = shelf
	if install_type == 'New':
		install_shelf = 'Onx'
		i = 1 
		while True:
			if install_shelf not in shelves:
				break
			else: 
				install_shelf = 'Onx' + str(i)
				i += 1
		cmds.shelfLayout(install_shelf, parent = parent_shelfTabLayout)

	#Onx Launcher button
	cmds.shelfButton(parent = install_shelf,
		annotation = 'Onx Launcher', 
		image1 = os.path.join(icon_dir, 'Onx_launcher.png'),
		command = """
#Onx Launcher
from Onx import Onx
#reload(Onx)
onx = Onx.OnxFileManager()
print 'Onx Launcher - Fire!'
		""",
		sourceType = 'python', 
		label = 'Onx'
		)

	shelfDirectory = cmds.internalVar(userShelfDir = True) + 'shelf_' + install_shelf
	cmds.saveShelf(install_shelf, shelfDirectory)

	cmds.confirmDialog( 
		title='Install Complete', 
		message='Onx Launcher Ready to Fire!', 
		button=['Awesome!'] )

	#this is a fix for a Maya issue 'provided' from Gary Fixler > in the comments MAR 2012
	# http://www.nkoubi.com/blog/tutorial/how-to-create-a-dynamic-shelf-plugin-for-maya/
	
	topLevelShelf = mel.eval("global string $gShelfTopLevel; $temp = $gShelfTopLevel;") 
	shelves = cmds.shelfTabLayout(topLevelShelf, query=True, tabLabelIndex=True)
	for index, shelf in enumerate(shelves):
		cmds.optionVar(stringValue=('shelfName%d' % (index+1), str(shelf)))


install()