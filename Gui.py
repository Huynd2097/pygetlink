# -*- coding: utf-8 -*-
import time

import ttk
import Tix
from tkFont import Font
from Tkinter import *
from tkinter.scrolledtext import ScrolledText
import tkMessageBox
import tkFileDialog 

import thread
import threading
import pickle

from collections import OrderedDict, Iterable, deque
from api import check_url, get_link, get_list
from models import FileInfo
import utils

#Define variable
WINDOW_HEIGHT = 500
WINDOW_WIDTH = 1000

#position
MENU_BAR_X = 5
BUTTON_BAR_X = 40

BUTTON_WIDTH = 60
BUTTON_HEIGHT = 20


RESULT_FRAME_HEIGHT = 450
LIST_WIDTH = 150
TABLE_WIDTH = WINDOW_WIDTH - LIST_WIDTH - 25 #for scrollbars

MAX_THREAD = 10

class SubWindow(ttk.Frame):
	"""docstring for SubWindow"""
	def __init__(self, master=None, title='SubWindow',typeOfSubWin='Default', width=500, height=85, posX=700, posY=500):

		self.root = Tk()
		self.root.geometry('{}x{}+{}+{}'.format(width,height,posX,posY))
		self.root.wm_title(title)
		
		ttk.Frame.__init__(self, Toplevel(master))
		self.pack(fill=BOTH, expand=1)

		self.data = {}
		self.width = width
		self.height = height
		self.posX = posX
		self.posY = posY
		self.typeOfSubWin = typeOfSubWin

		self.createWidgetsDefault()

		# self.root.grab_set()  #disable parent window
		
		# self.root.wait_window(self)

		# self.root.protocol('WM_DELETE_WINDOW', self.__del__)


	def createWidgetsDefault(self):
		posY_upper = 10
		posY_lower = 45
		posX_left = 10
		posX_center = 70
		innerWitdh = self.width-BUTTON_WIDTH-10
		Label(self, text='Address').place(x=posX_left, y=posY_upper)
		Label(self, text='Password').place(x=posX_left, y=posY_lower)
		Label(self, text='Quality').place(x=posX_center + innerWitdh/3, y=posY_lower)

		self.entry_0 = Entry(self, text='input')
		self.entry_0.place(x = posX_center, y=posY_upper, width=innerWitdh - posX_center - 10)
		self.entry_0.focus()

		self.entry_1 = Entry(self)
		self.entry_1.place(x = posX_center, y=posY_lower, width=innerWitdh/3)

		self.entry_2 = Entry(self)
		self.entry_2.place(x = 2*innerWitdh/3 - posX_left,y=posY_lower, width=innerWitdh/3)

		btn_ok = Button(self, text='OK', command=self.onSubmit)
		btn_ok.place(x=innerWitdh, y=posY_upper, width=BUTTON_WIDTH, height=BUTTON_HEIGHT)

		btn_cancel = Button(self, text='Cancel', command=self.root.destroy)
		btn_cancel.place(x=innerWitdh, y=posY_lower, width=BUTTON_WIDTH, height=BUTTON_HEIGHT)

	def onSubmit(self, event=None):
		if 'url' in self.typeOfSubWin:
			url = self.entry_0.get().replace('"', '\\"').replace(' ', '%20')
			if not check_url(url, isList=('list' in self.typeOfSubWin)):
				tkMessageBox.showwarning('title_', 'Invalid/Unsupported URL entered!')
				return

		self.data = [url, self.entry_1.get(), self.entry_2.get()]

		self.root.destroy()

	def __del__(self):
		# self.root.grab_release()  #normalize parent window
		self.data = ''
		self.root.destroy()


		























class Application(ttk.Frame):
	_pathData = 'tmp'

	def __init__(self, master=None):
		ttk.Frame.__init__(self, master)
		self.pack(fill=BOTH, expand=1)
		self.root = master
		self.balloon = Tix.Balloon(self.root)
		self._headingsTable = ('Input URL', 'Status', 'File Name', 'Direct URL')	   


		#data = { inputUrl<list>:{password, quality, listFiles : [inputUrl<file>, status, directurl, fileName, password*, quality*]} }
		#Read data from file
		self._data = OrderedDict()
		self._data['Main'] = {'status':'','password':'', 'quality':'', 'listFiles':[]}
		self._activeList = 'Main'
		
		dataStored = self._import_data()	
		# print dataStored
		if (isinstance(dataStored, OrderedDict)): 
			self._data.update(dataStored)



		#create element
		self.createWidgets()
		self._save_data()

		self._thread_get_link = None
		self._queue_get_link = deque() #collections.deque

		# add info list, table
		for listName in self._data.keys():
			self._add_new_list(values=listName)
		for file in self._data[self._activeList]['listFiles']:
			self._add_new_row(index='end',values=file) ### content




		for sub in self.balloon.subwidgets_all():
			sub.config(bg='lightgrey')

	def callback(self):

		curItem = self._tableResult.focus()
		print self._tableResult.item(curItem)	




	def createWidgets(self):
		self._create_menu_bar()
		self._create_button_bar()
		self._create_table_result()

		self._create_popup_menu() #last add


 	def _create_menu_bar(self):

 		def on_click():
 			print 'on_click'
 			count = 0
 			export_menu.entryconfig('To text file', label="To text file <" + str(count) + ">")

 		menubar = Menu(self.root)

 		# create a pulldown menu, and add it to the menu bar
		tasks_menu = Menu(menubar, tearoff=0)
		tasks_menu.add_command(label="Add new URL", command=self._add_url_file)

		import_menu = Menu(tasks_menu, tearoff=0)
		import_menu.add_command(label="From URL list", command=self._add_url_list)
		import_menu.add_command(label="From text file", command=self.callback)
		tasks_menu.add_cascade(label="Import", menu=import_menu)

		export_menu = Menu(tasks_menu, tearoff=0)
		export_menu.add_command(label="To text file", command=lambda ext='.txt' : self.write_to_file(ext))
		export_menu.add_command(label="To csv file", command=lambda ext='.csv' : self.write_to_file(ext))
		tasks_menu.add_cascade(label="Export", menu=export_menu, command=on_click)


		tasks_menu.add_separator()
		tasks_menu.add_command(label="Exit", command=self.root.destroy)
		menubar.add_cascade(label="Tasks", menu=tasks_menu)

		# create more pulldown menus
		file_menu = Menu(menubar, tearoff=0)
		file_menu.add_command(label="Get", command=self.get_file)
		file_menu.add_command(label="Cancel", command=self.cancel_get_file)
		file_menu.add_command(label="Download", command=self.callback)
		file_menu.add_command(label="Remove", command=self.delete_selected_rows)
		menubar.add_cascade(label="File", menu=file_menu)

		help_menu = Menu(menubar, tearoff=0)
		help_menu.add_command(label="Help content", command=self.callback)
		help_menu.add_command(label="About", command=self.callback)
		menubar.add_cascade(label="Help", menu=help_menu)

		# display the menu
 		self.root.config(menu=menubar)



 	def _create_button_bar(self):
 		buttonFrame =  Frame(self,relief=FLAT)
 		buttonFrame.pack(side=TOP, fill=BOTH, expand=Y)
		buttonFrame.place(height=BUTTON_HEIGHT, width=WINDOW_WIDTH,y=0)
		buttonFrame.config(border=1)

		self._button= {}
 		self._button['addUrl'] = Button(buttonFrame, text='+URL', command=self._add_url_file)
 		self._button['addUrl'].pack(side=LEFT, fill=BOTH, expand=Y)

 		self._button['addList'] = Button(buttonFrame, text='+list', command=self._add_url_list)
 		self._button['addList'].pack(side=LEFT, fill=BOTH, expand=Y)

 		self._button['get'] = Button(buttonFrame, text='GET', command=self.get_file)
 		self._button['get'].pack(side=LEFT, fill=BOTH, expand=Y)

 		self._button['cancel'] = Button(buttonFrame, text='Cancel', command=self.cancel_get_file)
 		self._button['cancel'].pack(side=LEFT, fill=BOTH, expand=Y)

 		self._button['IDM'] = Button(buttonFrame, text='> IDM', command=self.get_file)
 		self._button['IDM'].pack(side=LEFT, fill=BOTH, expand=Y)


 		
 		for key, button in self._button.iteritems():
 			button.config(relief = FLAT, bg='lightgray')
 			button.bind("<Enter>", lambda event, h=button: h.configure(bg="#d2dff4"))
 			button.bind("<Leave>", lambda event, h=button: h.configure(bg="lightgray"))

			# bind balloon to buttons
			self.balloon.bind_widget(button, balloonmsg=key)



			  


	def _create_table_result(self):
		resultFrame = Frame(self)
		resultFrame.pack(side=TOP, fill=BOTH, expand=Y)
		resultFrame.place(y=WINDOW_HEIGHT - RESULT_FRAME_HEIGHT, height=RESULT_FRAME_HEIGHT, width=WINDOW_WIDTH)
		resultFrame.config(padx=10)



		listFrame = ttk.Frame(resultFrame)
		listFrame.pack(side=LEFT, fill=BOTH, expand=Y)
		listFrame.place(x=0,y=0,height=RESULT_FRAME_HEIGHT, width=LIST_WIDTH)
		listFrame.rowconfigure(0, weight=1) # Only 1 cell in Frame
		listFrame.columnconfigure(0, weight=1)

		dataColList = ('List' + ' '*1000,)
		self._listTables = ttk.Treeview(columns=dataColList, show='headings')
		self._listTables.pack(expand=True, fill=BOTH)
		self._listTables.grid(in_=listFrame, row=0, column=0, sticky=NSEW)	#FILLFULL Frame
		for c in dataColList:
			self._listTables.heading(c, text=c.title(), anchor=S)




		xsb_list = ttk.Scrollbar(orient=HORIZONTAL, command= self._listTables.xview)
		ysb_list = ttk.Scrollbar(orient=VERTICAL, command= self._listTables.yview)
		self._listTables['xscroll'] = xsb_list.set
		self._listTables['yscroll'] = ysb_list.set
		xsb_list.grid(in_=listFrame, row=1, column=0, sticky=EW)
		ysb_list.grid(in_=listFrame, row=0, column=1, sticky=NS)


		# self._listTables.insert('','end',values='List_1')

		# self._listTables.bind('<<ListboxSelect>>',self.get) ###
		self._listTables.bind('<ButtonRelease-3>',self.do_popup_list) ###
		self._listTables.bind('<ButtonRelease-1>',self._set_activeList) ###
		self._listTables.bind("<Delete>", lambda event, tree='_listTables':self.delete_selected_rows(treeview=tree))


		##	============================================================================
		##	=====================================TABLE================================
		##	============================================================================

		tableFrame = ttk.Frame(resultFrame)
		tableFrame.pack(side=RIGHT, fill=BOTH, expand=Y)
		tableFrame.place(x=LIST_WIDTH + 5,y=0,height=RESULT_FRAME_HEIGHT, width=TABLE_WIDTH)  
		
		

		# create the tree and scrollbars
		self._tableResult = ttk.Treeview(columns=self._headingsTable, show = 'headings')
		self._tableResult.tag_configure('evenrow', background='white')
		self._tableResult.tag_configure('oddrow', background='lightgray')
		# self._tableResult.place(height=450)

				
		# configure column headings
		for c in self._headingsTable:
			self._tableResult.heading(c, text=c.title())		   
			# self._tableResult.column(c, width=Font().measure(c.title())) #fit
		 
		# self._tableResult.column("IDs",minwidth=25,width=7)

		# add tree and scrollbars to frame
		ysb = ttk.Scrollbar(orient=VERTICAL, command= self._tableResult.yview)
		xsb = ttk.Scrollbar(orient=HORIZONTAL, command= self._tableResult.xview)
		self._tableResult['yscroll'] = ysb.set
		self._tableResult['xscroll'] = xsb.set

		self._tableResult.grid(in_=tableFrame, row=0, column=0, sticky=NSEW)

		self._tableResult.bind("<Delete>", lambda event, tree='tableResult':self.delete_selected_rows(treeview=tree))
		self._tableResult.bind('<Control-Shift-Key-C>',self.copy_selected_directUrls) # upper
		self._tableResult.bind('<Control-Shift-Key-c>',self.copy_selected_directUrls) # lower

		ysb.grid(in_=tableFrame, row=0, column=1, sticky=NS)
		xsb.grid(in_=tableFrame, row=1, column=0, sticky=EW)
		 
		# set frame resize priorities
		tableFrame.rowconfigure(0, weight=1)
		tableFrame.columnconfigure(0, weight=1)	
			
	def _create_popup_menu(self):
		self._popup = {}

		
		popup_list_item = Menu(self._listTables, tearoff=0)
		popup_list_item.add_command(label='Add new URL', command=lambda values='aa':self._add_url_file())
		popup_list_item.add_command(label='Get all URLs', command=lambda values='aa':self._add_url_list())
		popup_list_item.add_command(label='Get selected URLs', command=lambda values='aa':self._add_url_list())
		popup_list_item.add_command(label='Stop getting', command=lambda values='aa':self._add_url_list())
		popup_list_item.add_separator()
		popup_list_item.add_command(label='Rename', command=lambda values='aa':self.rename_listTable())
		popup_list_item.add_command(label='Remove', command=lambda tree='_listTables':self.delete_selected_rows(treeview=tree))

		self._popup['_listTables'] = popup_list_item

	def _add_new_row(self, index=0, values=[]):
		if isinstance(values, str) or isinstance(values, unicode):
			values = [values,]
		# print values
		columns = len(self._headingsTable)
		values = list(values)[:columns]
		values.extend([''] * (columns - len(values)))

		tag = 'evenrow' if ( len(self._tableResult.get_children()) % 2) else 'oddrow' #set separate color
		self._tableResult.insert('', index, values=values, tag=(tag,))
		# self._tableResult.column('IDs', width=Font().measure(vId)) #fit

	def _add_new_list(self, index='end', values=[]):
		self._listTables.insert('', index, values=values)

	def _index_row(self, url, listTableName):
		listInfo = self._data[listTableName]['listFiles']
		for i in xrange(0, len(listInfo)):
			compUrl = listInfo[i] if isinstance(listInfo[i], str) else listInfo[i][0]
			if (url == compUrl):
				return i 
		return -1 #not found

	def _find_id_list(self, listName):
		for i in xrange(0, len(self._data)):
			listOfLists = self._data.keys()
			if (listName == listOfLists[i]):
				return i 
		return -1 #not found
 

	def _update_row(self, content, listTableName=''):
		listTableName = listTableName or self._activeList
		if isinstance(content, str) or isinstance(content, unicode):
			content = [str(content),]
		content = list(content)
		content.extend([''] * (len(self._headingsTable) - len(content)))
		idRow = self._index_row(content[0], listTableName)
		if idRow > -1:
			self._data[listTableName]['listFiles'][idRow] = content
			#show in GUi
			if listTableName == self._activeList:
				iid = self._tableResult.get_children()[idRow]
				self._tableResult.item(iid, values=content)



		# values = {}
	def _add_url_file(self):
		values = self.get_values_subwindow(typeOfSubWin='add new url file')
		if not (values and isinstance(values,list)):
			return

		url = values[0]
		idRow = self._index_row(url, self._activeList)
		if idRow == -1:
			# not found, add new
			# [inputUrl<file>, status, directurl, fileName, password*, quality*]
			values[1:1] = ['']*3
			self._data[self._activeList]['listFiles'].insert(0, values)
			self._add_new_row(values=url)

		#highlight
		item = self._tableResult.get_children()[0] #url file add first
		self._tableResult.selection_set(item)
		self.get_file()

	def _add_url_list(self):
		values = self.get_values_subwindow(typeOfSubWin='add new url list')

		if not (values and isinstance(values, list)):
			return False
		url = values[0]
		idRow = self._find_id_list(url)
		if idRow == -1:
			# not found, add new
			listUrls = get_list(url)
			listFiles = [''] * len(listUrls)
			for x in xrange(0, len(listUrls)):
				listFiles[x] = [''] * (len(self._headingsTable) + 2)
				listFiles[x][0] = listUrls[x]

			self._data[url] = {'status':'','password':'', 'quality':'', 'listFiles':listFiles}
			self._add_new_list(values=values)
		#highlight
		item = self._listTables.get_children()[idRow]
		self._listTables.selection_set(item)
		self._set_activeList()

	# Default: set Main
	def _set_activeList(self, event=None):
		if self._listTables.selection():			
			selected_item = self._listTables.selection()[0]
			activeListName = self._listTables.item(selected_item)['values'][0]
		else:
			activeListName = "Main"
			#focus Main
			item = self._listTables.get_children()[0]
			self._listTables.selection_set(item)

		if (self._activeList == activeListName):
			print 'active', self._activeList

		self._activeList = activeListName
		#remove all item in current table
		self._tableResult.delete(*self._tableResult.get_children())
		
		#rewrite
		listData = self._data[self._activeList]['listFiles']
		# print listData	
		for rowContent in listData:
			self._add_new_row(index='end', values=rowContent)



		# self._activeList['values'] = 'chose'

	def _thread_get_link_file(self, rowContent, listTableName=''):
		listTableName = listTableName or self._activeList
		# _headingsTable + password + quality
		if not (isinstance(rowContent, tuple) or isinstance(rowContent, list)):
			return
		inputUrl = rowContent[0]
		idRow = self._index_row(inputUrl, listTableName)
		if idRow == -1:
			return #deleted?


		listInfo = self._data[listTableName]
		indexOfStatusInHeading = self._headingsTable.index('Status')
		rowContent = listInfo['listFiles'][idRow] #update 
		status = rowContent[indexOfStatusInHeading]
		print status
		if not status in ('Pending', 'pending'):
			return 

		rowContent[1] = 'Started'
		self._update_row(rowContent, listTableName)

		password = rowContent[-2] or listInfo['password']
		quality = rowContent[-1] or listInfo['quality']

		# try:
		json = get_link(url=inputUrl, password=password, quality=quality)
		if json['status'] == 'success':
			fi = json['message']
			if not isinstance(fi, FileInfo):
				rowContent[indexOfStatusInHeading] = 'Error'
			directUrl = fi.url
			fileName = fi.fileName
			rowContent[indexOfStatusInHeading] = 'Success'
			rowContent[2] = fileName
			rowContent[3] = directUrl
		else:# json['status'] == 'error':
			rowContent[indexOfStatusInHeading] = 'Get Error'
			rowContent[2] = json['message']
		# except Exception as e:
		# 	rowContent[indexOfStatusInHeading] = 'GUI Error'
		# 	rowContent[2] = e

		self._update_row(rowContent, listTableName)
		
	def _start_queue_thread_get_link_file(self):

		while self._queue_get_link:
			args = tuple(self._queue_get_link.popleft(),)
			try:
				while threading.activeCount() >= MAX_THREAD:
					activeThreads = threading.activeCount()
					print activeThreads
					time.sleep(activeThreads / 10)

				thread = threading.Thread(target=self._thread_get_link_file, args=args)
				thread.setDaemon(True)
				thread.start()
				# thread.join()
				time.sleep(0.1)				
			except Exception as e:
				print e

		self._thread_get_link = None #done
		


	def get_file(self):
		queue = []
		for selected_row in self._tableResult.selection():
			rowContent = self._tableResult.item(selected_row)['values']
			rowContent = list(rowContent)
			rowContent[1] = 'Pending'
			self._update_row(rowContent)
			self._queue_get_link.append( (rowContent,self._activeList) )
		# new thread get link
		if not self._thread_get_link:
			print 'start get file'
			self._thread_get_link = threading.Thread(target=self._start_queue_thread_get_link_file)
			self._thread_get_link.setDaemon(True)
			self._thread_get_link.start()

	def get_list(self):
		selected_row = self._tableResult.selection()[0]
		url = self._listTables.item(selected_row)['values'][0]
		listUrls = get_list(url)
		self._data[url]['listFiles'] = listUrls
		self._set_activeList()

	def cancel_get_file(self):
		for selected_row in self._tableResult.selection():
			rowContent = self._tableResult.item(selected_row)['values']
			rowContent = list(rowContent)
			if rowContent[1] in ('Pending', 'pending'):
				rowContent[1] = 'Canceled'
				self._update_row(rowContent)
				
	def copy_selected_directUrls(self, event=None):
		print 'Copy'
		dUrls = []
		for selected_row in self._tableResult.selection():
			rowContent = self._tableResult.item(selected_row)['values']
			dUrls.append(rowContent[3])

		self.root.clipboard_clear()
		self.root.clipboard_append('\n'.join(dUrls))

	def get_values_subwindow(self, typeOfSubWin='Default'):
		inputBox = SubWindow(master=self.root, typeOfSubWin=typeOfSubWin)
		# self.root.iconify() 	#hide window
		# inputBox.mainloop()
		while True:
			try:
				ret = inputBox.data
				inputBox.update_idletasks()
				inputBox.update()
			except:
				break
		# self.root.deiconify() 	#show window
		print ret
		return ret




	def write_to_file(self, ext='.txt'):
		rows = self._tableResult.selection() or self._tableResult.get_children()
		if not rows:
			return
		print 'export'
		dataToWrite = []
		options = {}
		options['filetypes'] = [('text files', ext), ('all files', '.*')]
		options['initialfile'] = 'export' + ext

		if ext == '.txt':
			out = tkFileDialog.asksaveasfile(mode='w', **options)
			if not out:
				return
				
			for row in rows:
				dataToWrite.append(self._tableResult.item(row)['values'][3]) #only direct url
			out.write('\n'.join(dataToWrite)) #write
			out.close()
		elif ext == '.csv':
			fileName = tkFileDialog.asksaveasfilename(**options)
			dataToWrite.append(list(self._headingsTable)) #first row
			for row in rows:
				dataToWrite.append(self._tableResult.item(row)['values']) #only direct url
			utils.write_file_csv(dataToWrite, fileName)

	

	def do_popup_list(self, event):
		iid = self._listTables.identify_row(event.y)
		if iid:
			# mouse pointer over item
			self._listTables.selection_set(iid)
			self._popup['_listTables'].post(event.x_root, event.y_root)			
		else:
			# mouse pointer not over item
			# occurs when items do not fill frame
			# no action required
			pass

	#bind ~ <Delete>
	#Menu PopupMenu > Remove
	def delete_selected_rows(self, event=None, treeview=''):
		if not treeview:
			print 'No selected treeview'
			return 
		try:
			if ('listTable' in treeview):
				selectedTreeview = self._listTables
				for selected_item in selectedTreeview.selection():
					rowContent = selectedTreeview.item(selected_item)['values'][0]

					if (rowContent == 'Main'):
						continue

					selectedTreeview.delete(selected_item) #remove from gui
					self._data.pop(rowContent) #remove from data
					print 'remove list', rowContent
					print rowContent == self._activeList
			elif ('tableResult' in treeview):
				selectedTreeview = self._tableResult
				for selected_item in selectedTreeview.selection():
					url = selectedTreeview.item(selected_item)['values'][0]
					idRow = self._index_row(url, self._activeList)
					self._data[self._activeList]['listFiles'].pop(idRow)
			# if delete list, active Main
			# if removw row, rewrite table
			self._set_activeList()
				
		except Exception as e:
			print e


	def rename_listTable(self):
		newName = self.get_values_subwindow()

		iid = self._listTables.selection()
		self._listTables.item(iid, values=newName)

		# if newName:
		# 	self._listTables.item(self._listTables.selection())['values'] = newName

	def _save_data(self):
		def sync():
			while (self._thread):
				time.sleep(self._delayTime)		
				if self._export_data():
					print 'Synced'

		try:
			self._delayTime = 1
			self._thread = threading.Thread(target=sync)
			self._thread.daemon = True
			self._thread.start()
			print 'Start sync'
			
		except (Exception, SystemExit) as e:
			self._thread = False
			self._delayTime = 0

	def _export_data(self):
		try:
			dataFile = self._import_data()
			if self._data != dataFile:
				with open(self._pathData, 'rb+') as out:
					pickle.dump(self._data, out, pickle.HIGHEST_PROTOCOL) #store
					# print 'write_file successfully.'
					out.close()
					return True
					
		except Exception as e:
			print 'write_file error.', format(e)

		return False


	def _import_data(self):
		# pathData = pathData or self._pathData
		try:
			with open(self._pathData, 'ab+') as inp:
				data = pickle.load(inp)
				# print 'read_file successfully.'
				inp.close()
				return data
		except Exception as e:
			print 'read_file Exception.', format(e)
			return ''























root = Tix.Tk()
#set windows size
root.maxsize(WINDOW_WIDTH, WINDOW_HEIGHT)
root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
root.geometry('+400+0')
root.wm_title("GET_LINK")

app = Application(master=root)
#alt mainloop
while True:
	try:
		app.update_idletasks()
		app.update()
	except:
		break

# app.mainloop()
