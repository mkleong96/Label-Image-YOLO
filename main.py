import os
import glob
import shutil
import ntpath
import os.path
import qdarkstyle
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from utils.mainwindow_ui import Ui_Form
import sys
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename
# import cv2
import numpy as np

PATH = os.getcwd()

class Local_Labelling_Program(QWidget):
    close_signal = pyqtSignal(bool) #### Signal to send to local labelling login to show login page

    def __init__(self):
        super(Local_Labelling_Program, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.showMaximized()
        self.setWindowTitle('Label Image YOLO')
        self.dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()

        self.num = 0
        self.imagenumber = 0
        self.program_dir_path = os.path.dirname(os.path.realpath(__file__)) #### Get current working directory
        #### Clear label
        self.ui.btn_save.setFocus()

        #### Initialize needed dictionary and list
        self.color = {}
        self.data_dict = {}
        self.classes_dict = {}
        self.png_list = []
        self.jpg_list = []
        self.classes_list = []
        self.filtered_list = []
        self.image_num_list = []
        self.rectangles_list = []
        self.selected_rectangle_list = []
        self.selected_rectangle_index_list = []
        
        #### Connect buttons and signals to functions
        self.ui.btn_next.clicked.connect(self.next_button_callback)
        self.ui.btn_prev.clicked.connect(self.prev_button_callback)
        self.ui.btn_save.clicked.connect(self.save_button_callback)
        self.ui.graphicsView.rectClicked.connect(self.rectangle_selected)
        self.ui.comboBox.currentIndexChanged.connect(self.filtering_images)
        self.ui.listWidget_classes.itemDoubleClicked.connect(self.check_label)
        self.ui.listWidget_classes.currentItemChanged.connect(self.check_label)
        self.ui.btn_add_rectangle.clicked.connect(self.draw_rect_button_callback)
        self.ui.comboBox.currentIndexChanged.connect(self.show_filtered_image_pre_process)
        self.ui.btn_deleterectangle.clicked.connect(self.delete_rectangle_button_callback)
        
        #### Initialize table widget
        self.ui.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableWidget.show()
        self.ui.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget.setStyleSheet('font-size: 12pt')


        self.ui.btn_open_folder.clicked.connect(self.load_source_button_callback)
        self.ui.btn_open_classes.clicked.connect(self.select_classes_button_callback)

        self.ui.listWidget.itemDoubleClicked.connect(self.listwidget_show_image)

        self.init()

        try:
            os.makedirs('tempDataSet')
        except:
            pass


    def init(self):
        f = open('classes.txt', 'r')
        self.classes_list = f.readlines()
        self.ui.tableWidget.setColumnCount(2) #### Set number of column
        self.ui.tableWidget.setHorizontalHeaderLabels(['CLASSES', 'NUMBER']) #### Set table header
        self.ui.tableWidget.setRowCount(len(self.classes_list)) #### Set table row according to number of classes
        for i in range(len(self.classes_list)):
            self.ui.tableWidget.setItem(i, 0, QTableWidgetItem(self.classes_list[i])) #### Add classes to table widget first column
            self.ui.listWidget_classes.addItem(self.classes_list[i]) #### Add classes to list widget
            self.ui.tableWidget.setItem(i, 1, QTableWidgetItem('0')) #### Set zero to table widget second column


    def select_classes_button_callback(self):
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        self.text_path = askopenfilename(title='Select Classes.txt')
        if self.text_path == '':
            pass
        else:
            file = open(self.text_path, 'r')
            self.classes_list = file.readlines()
            # self.load_button_callback(self.loaded_source_path,self.classes_list)


    def load_source_button_callback(self):
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        self.loaded_source_path = askdirectory(title='Select Folder')
        if not self.loaded_source_path == '':
            self.load_button_callback(self.loaded_source_path,self.classes_list)


    def listwidget_show_image(self):

        self.ui.listWidget_rectangles.clear()
        for item in self.rectangles_list:
            self.ui.graphicsView.delete_rec(item)
        self.rectangles_list.clear()

        self.image_selected = self.ui.listWidget.currentItem().text()
        self.pixmap = QPixmap(self.image_selected) #### Extract pixmap of image
        # image = QImage(self.filtered_list[imagenumber]) 
        self.image = QImage(self.image_selected)
        file = ntpath.basename(self.image_selected) #### Extract file name from image path (including extension but excluding path)
        filename, extension = os.path.splitext(file) #### Extract file name (excluding path and extension)
        text_file_extension = ".txt" #### Join filename with '.txt' extension to get text file name
        self.text_file_name = filename + text_file_extension #### join file name to get full path name of text file
        open(self.text_file_name, "a") #### Create a text file if text file not existed
        #### Get image width and height
        self.image_width = self.image.width()
        self.image_height = self.image.height()
        #### Send image width and height to graphics view
        self.ui.graphicsView.image_size(self.image_width, self.image_height)
        #### Send pixmap to graphics view to set photo on graphics view
        self.ui.graphicsView.setPhoto(self.pixmap)
        ### Open text file to read data
        open_text_file = open(self.text_file_name, "r")
        lines = open_text_file.readlines()
        index = []
        xc_iw = []
        yc_ih = []
        rw_iw = []
        rh_ih = []
        #### Extract data from text file and append separately to list accordingly
        for x in lines:
            index.append(x.split(' ')[0])
            xc_iw.append(x.split(' ')[1])
            yc_ih.append(x.split(' ')[2])
            rw_iw.append(x.split(' ')[3])
            rh_ih.append(x.split(' ')[4])
        #### Get value from list to draw rectangle
        for i in range(0, len(xc_iw)):
            index_value = index[i] #### Class of rectangle
            xc_iw_value = xc_iw[i]
            xc = (float(xc_iw_value))*self.image_width #### X center of rectangle
            yc_ih_value = yc_ih[i]
            yc = (float(yc_ih_value))*self.image_height #### Y center of rectangle
            rw_iw_value = rw_iw[i]
            rw = (float(rw_iw_value))*self.image_width #### Width of rectangle
            rh_ih_value = rh_ih[i]
            rh = (float(rh_ih_value))*self.image_height #### Height of rectangle
            topleft_x = xc - (rw/2) #### Top left x geometry of rectangle
            topleft_y = yc - (rh/2) #### Top left y geometry of rectangle
            self.ui.graphicsView.add_rect(topleft_x, topleft_y, rw, rh) #### Send data to graphics view to draw rectangles
            self.rectangles_list.append(self.ui.graphicsView._current_rect_item) #### Add rectangle name to list
            for h in range(len(self.classes_list)):
                if index_value == str(h):
                    self.ui.listWidget_rectangles.addItem(self.classes_list[h]) #### Add class of rectangle to list widget
                    self.color[f'{h}'].append(self.ui.graphicsView._current_rect_item) #### Add rectangle name to dictionary according to class
        self.ui.graphicsView.color_dict(self.color) #### Send data to graphics view to set color of rectangle 
        open_text_file.close() #### Close text file


    #### Get images of selected class from dictionary
    def filtering_images(self):
        if self.data_dict != {}:
            self.ui.listWidget.clear()
            self.filtered_list.clear()
            for i in range(len(self.classes_list)):
                if self.ui.comboBox.currentText() == self.classes_list[i]:
                    for h in range(len(self.data_dict[f'{i}'])):
                        self.filtered_list.append(self.data_dict[f'{i}'][h])

    #### Show filtered image pre process
    def show_filtered_image_pre_process(self):
        if self.data_dict != {}:
            self.show_filtered_image(0) #### Show first image in list
            self.ui.btn_save.setFocus()

    #### Display filtered image
    def show_filtered_image(self, imagenumber):
        if self.filtered_list != []:
        #### Check if images enough to go to next image
            if imagenumber < len(self.filtered_list): #### If images enough to go to next image
                #### Clear list widget before adding to avoid duplicate
                self.ui.listWidget_rectangles.clear()
                #### Delete rectangles from graphics view to avoid duplicate 
                for item in self.rectangles_list:
                    self.ui.graphicsView.delete_rec(item)
                #### Clear list
                self.rectangles_list.clear() 
                for i in range(len(self.classes_list)):
                    self.color[f'{i}'].clear()
                self.selected_rectangle_list.clear()
                self.selected_rectangle_index_list.clear()
                #### Set image number on label
                self.pixmap = QPixmap(self.filtered_list[imagenumber]) #### Extract pixmap of image
                # image = QImage(self.filtered_list[imagenumber]) 
                self.image = QImage(self.filtered_list[imagenumber])
                file = ntpath.basename(self.filtered_list[imagenumber]) #### Extract file name from image path (including extension but excluding path)
                filename, extension = os.path.splitext(file) #### Extract file name (excluding path and extension)
                text_file_extension = ".txt" #### Join filename with '.txt' extension to get text file name
                self.text_file_name = filename + text_file_extension #### join file name to get full path name of text file
                open(self.text_file_name, "a") #### Create a text file if text file not existed
                #### Get image width and height
                self.image_width = self.image.width()
                self.image_height = self.image.height()
                #### Send image width and height to graphics view
                self.ui.graphicsView.image_size(self.image_width, self.image_height)
                #### Send pixmap to graphics view to set photo on graphics view
                self.ui.graphicsView.setPhoto(self.pixmap)
                ### Open text file to read data
                open_text_file = open(self.text_file_name, "r")
                lines = open_text_file.readlines()
                index = []
                xc_iw = []
                yc_ih = []
                rw_iw = []
                rh_ih = []
                #### Extract data from text file and append separately to list accordingly
                for x in lines:
                    index.append(x.split(' ')[0])
                    xc_iw.append(x.split(' ')[1])
                    yc_ih.append(x.split(' ')[2])
                    rw_iw.append(x.split(' ')[3])
                    rh_ih.append(x.split(' ')[4])
                #### Get value from list to draw rectangle
                for i in range(0, len(xc_iw)):
                    index_value = index[i] #### Class of rectangle
                    xc_iw_value = xc_iw[i]
                    xc = (float(xc_iw_value))*self.image_width #### X center of rectangle
                    yc_ih_value = yc_ih[i]
                    yc = (float(yc_ih_value))*self.image_height #### Y center of rectangle
                    rw_iw_value = rw_iw[i]
                    rw = (float(rw_iw_value))*self.image_width #### Width of rectangle
                    rh_ih_value = rh_ih[i]
                    rh = (float(rh_ih_value))*self.image_height #### Height of rectangle
                    topleft_x = xc - (rw/2) #### Top left x geometry of rectangle
                    topleft_y = yc - (rh/2) #### Top left y geometry of rectangle
                    self.ui.graphicsView.add_rect(topleft_x, topleft_y, rw, rh) #### Send data to graphics view to draw rectangles
                    self.rectangles_list.append(self.ui.graphicsView._current_rect_item) #### Add rectangle name to list
                    for h in range(len(self.classes_list)):
                        if index_value == str(h):
                            self.ui.listWidget_rectangles.addItem(self.classes_list[h]) #### Add class of rectangle to list widget
                            self.color[f'{h}'].append(self.ui.graphicsView._current_rect_item) #### Add rectangle name to dictionary according to class
                self.ui.graphicsView.color_dict(self.color) #### Send data to graphics view to set color of rectangle 
                open_text_file.close() #### Close text file

                for item in self.filtered_list:
                    self.ui.listWidget.addItem(item)

        else:
            self.ui.listWidget.clear()
            self.ui.listWidget_rectangles.clear()
            for item in self.rectangles_list:
                self.ui.graphicsView.delete_rec(item)
            self.rectangles_list.clear()

            black_img = 0 * np.ones((1000,1000,3), np.uint8)
            img_resize = black_img
            self.image_height, self.image_width, ch = img_resize.shape
            self.ui.graphicsView.image_size(self.image_width, self.image_height)
            bytesPerLine = ch * self.image_width
            qimage = QImage(img_resize.data, self.image_width, self.image_height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
            self.pixmap = QPixmap(qimage)
            self.ui.graphicsView.setPhoto(self.pixmap)



    #### Draw rectangle function
    def draw_rect_button_callback(self):
        #### Check if rectangles have classes selected
        if self.ui.listWidget_rectangles.count() == len(self.ui.graphicsView.rect_list):
            #### Change color of frame and buttons
            self.ui.btn_save.setStyleSheet(self.dark_stylesheet)
            self.ui.frame.setStyleSheet(self.dark_stylesheet)
            self.ui.graphicsView.add_rect(0, 0, self.image_width/2.4, self.image_height/4.896) #### Send data to graphics view to draw rectangle
            self.rectangles_list.append(self.ui.graphicsView._current_rect_item) #### Add rectangle name to list
            self.ui.btn_add_rectangle.clearFocus()

    #### Logout function
    def logout_button_callback(self):
        # os.chdir(self.program_dir_path) #### Change directory to program directory
        #### Clear widgets
        self.ui.listWidget_classes.clear()
        self.ui.listWidget_rectangles.clear()
        self.ui.comboBox.clear()
        self.close() #### Close labelling program
        self.close_signal.emit(True) #### Send signal to login page 

    #### Save function
    def save_button_callback(self):
        self.index_list = []
        f = open(self.text_file_name, "w") #### Open text file to write data
        for i in range(0, len(self.ui.graphicsView.rect_list)):
            rect = self.ui.graphicsView.rect_list[i].sceneBoundingRect() #### Get rectangles geometry from graphics view
            rect_xcoor = rect.x() + 10 #### Find top left x geometry 
            rect_ycoor = rect.y() + 10 #### Find top left y geometry 
            rect_width = rect.width() - 20 #### Find width of rectangle
            rect_height = rect.height() - 20 #### Find height of rectangle
            rect_width_center = rect_width / 2 #### Find width center
            rect_height_center = rect_height / 2 #### Find height center
            x_center_coordinate = rect_xcoor + rect_width_center #### Find x center 
            y_center_coordinate = rect_ycoor + rect_height_center #### Find y center
            self.abs_x_center = x_center_coordinate / self.image_width #### Find absolute x center
            self.abs_y_center = y_center_coordinate / self.image_height #### Find absolute y center
            self.abs_width = rect_width / self.image_width #### Find absolute width 
            self.abs_height = rect_height / self.image_height #### Find absolute height
            self.ui.listWidget_rectangles.setCurrentRow(i) #### Set list widget focus on current rectangle to get class of rectangle

            #### Find index of current rectangle
            for j in range(len(self.classes_list)):
                if self.ui.listWidget_rectangles.currentItem().text() == self.classes_list[j]:
                    self.class_index = j
                    self.index_list.append(self.class_index)

            f.write("%s %s %s %s %s \n" % (self.class_index, self.abs_x_center, self.abs_y_center, self.abs_width, self.abs_height)) #### Write data to text file
            self.image_dict[f'{self.imagenumber}'] = self.index_list #### Add index to dictionary according to image number 

        f.close() #### Close text file
        #### Clear list in dictionary (This dictionary will be used to set value on table widget)

        try:
            shutil.copy(f'{self.open_file}\\{self.text_file_name}',f'{PATH}\\tempDataSet')
        except:
            file = open(f'{PATH}\\tempDataSet\\{self.text_file_name}', "w")
            file.write("%s %s %s %s %s \n" % (self.class_index, self.abs_x_center, self.abs_y_center, self.abs_width, self.abs_height)) #### Write data to text file


        self.file_list = os.listdir(self.open_file)
        self.filename = f'{self.open_file}\\{self.text_file_name}'.replace('txt','jpg')
        if self.filename in self.file_list:
            try:
                shutil.copy(self.filename, f'{PATH}\\tempDataSet')
            except shutil.SameFileError:
                pass

        else:
            self.filename = f'{self.open_file}\\{self.text_file_name}'.replace('txt','png')
            try:
                shutil.copy(self.filename, f'{PATH}\\tempDataSet')
                print('copied')
            except shutil.SameFileError:
                pass


        # try:
        #     try:
        #         shutil.copy(f'{self.open_file}\\{self.text_file_name}'.replace('txt','jpg'), f'{PATH}\\tempDataSet')
        #     except shutil.SameFileError:
        #         pass
        #         print('SameFileError')
        # except:
        #     try:
        #         shutil.copy(f'{self.open_file}\\{self.text_file_name}'.replace('txt','png'), f'{PATH}\\tempDataSet')
        #     except shutil.SameFileError:
        #         pass
        #         print('SameFileError')


        for s in range(0, 11):
            self.classes_dict[f'{s}'].clear()
        #### Read data from 'self.image_dict' and get all data in it to add to 'self.classes_dict'
        #### So 'self.classes_dict' will have all the labelled classes
        for i in range(0, len(self.image_dict)):
            for k in range(0, len(self.image_dict[f'{i}'])):
                for j in range(0, 11):
                    if self.image_dict[f'{i}'][k] == j:
                        self.classes_dict[f'{j}'].append(self.image_dict[f'{i}'][k])
        #### Calculate the length of list to set table widget
        for d in range(0, len(self.classes_list)):
            self.ui.tableWidget.setItem(d, 1, QTableWidgetItem(str(len(self.classes_dict[f'{d}']))))
        #### Change frame and button color
        self.ui.btn_save.setStyleSheet("background-color: lightgreen")
        self.ui.frame.setStyleSheet("background-color: lightgreen")
        self.ui.btn_save.clearFocus()
        self.ui.btn_next.setEnabled(True)

    #### Get data from local labelling login window
    def load_button_callback(self, path, classes):
        self.ui.listWidget_rectangles.clear()
        self.ui.listWidget_classes.clear()

        #### Assign variables
        self.classes_list = classes
        self.open_file = path
        #### Get files in selected directory
        self.list_images = os.listdir(self.open_file)
        #### Initialize dictionary
        self.image_dict = {}
        for i in range(int((len(self.list_images))/2)):
            self.image_dict[f'{i}'] = []
        self.ui.tableWidget.setRowCount(len(self.classes_list)) #### Set table row according to number of classes
        self.ui.comboBox.addItems(self.classes_list) #### Add classes to combobox
        self.ui.comboBox.insertItem(0, '') #### Add an empty item
        self.ui.comboBox.setCurrentIndex(0) #### Set current item to empty 
        self.ui.tableWidget.setColumnCount(2) #### Set number of column
        self.ui.tableWidget.setHorizontalHeaderLabels(['CLASSES', 'NUMBER']) #### Set table header
        for i in range(len(self.classes_list)):
            self.ui.tableWidget.setItem(i, 0, QTableWidgetItem(self.classes_list[i])) #### Add classes to table widget first column
            self.ui.listWidget_classes.addItem(self.classes_list[i]) #### Add classes to list widget
            #### Initialize list in dictionary
            self.classes_dict[f'{i}'] = []
            self.data_dict[f'{i}'] = []
            self.color[f'{i}'] = []
            self.ui.tableWidget.setItem(i, 1, QTableWidgetItem('0')) #### Set zero to table widget second column

        self.file_list = os.listdir(self.open_file)
        #### Filter images according to classes
        for file in os.listdir(self.open_file):
            if file.endswith(".txt"): #### Get text file in folder
                self.file_path = f"{self.open_file}\\{file}" #### Join path


                #### open text file and read data
                f = open(self.file_path, 'r')
                lines = f.readlines()
                if lines == []:
                    for h in range(len(self.classes_list)):
                        image_path = self.file_path.replace("txt", "jpg")
                        if image_path in self.file_list:
                            self.data_dict[f'{h}'].append(image_path)
                        else:
                            image_path = self.file_path.replace("txt", "png")
                            self.data_dict[f'{h}'].append(image_path)

                else:
                    for line in lines:
                        class_index = line[0:2]
                        classes_index = class_index.strip()
                        
                    #### Change file type and append image path to list in dictionary according to classes
                    for h in range(len(self.classes_list)):
                        if classes_index == str(h):
                            image_path = self.file_path.replace("txt", "jpg")
                            if image_path in self.file_list:
                                self.data_dict[f'{h}'].append(image_path)
                            else:
                                image_path = self.file_path.replace("txt", "png")
                                self.data_dict[f'{h}'].append(image_path)
        self.showimage(0) #### Show the first image from overall files in folder
        #### Open 'unsure' folder in selected directory
        self.unsure_folder_path = self.open_file + '\\unsure' 
        if not os.path.exists(self.unsure_folder_path):
            os.makedirs(self.unsure_folder_path)
            
    #### Next image function
    def next_button_callback(self):
        #### Check if user using filtering function
        if self.ui.comboBox.currentText() == '': #### If user not using filtering function
            self.ui.listWidget.clear()
            #### Change frame and buttons color
            self.ui.btn_save.setStyleSheet(self.dark_stylesheet)
            self.ui.frame.setStyleSheet(self.dark_stylesheet)
            self.ui.listWidget_rectangles.clear() #### Clear list widget to avoid duplicate
            #### Delete rectangles from graphics view
            for item in self.rectangles_list:
                self.ui.graphicsView.delete_rec(item)
            #### Clear list
            self.rectangles_list.clear()
            for i in range(len(self.classes_list)):
                self.color[f'{i}'].clear()
            self.imagenumber = self.imagenumber + 1 #### Increase image number by one
            self.showimage(self.imagenumber) #### Show the next image
        else: #### If user using filtering function
            self.ui.listWidget.clear()
            #### Change frame and buttons color
            self.ui.btn_save.setStyleSheet(self.dark_stylesheet)
            self.ui.frame.setStyleSheet(self.dark_stylesheet)
            self.ui.listWidget_rectangles.clear() #### Clear list widget to avoid duplicate
            #### Delete rectangles from graphics view
            for item in self.rectangles_list:
                self.ui.graphicsView.delete_rec(item)
            #### Clear list
            self.rectangles_list.clear()
            for i in range(len(self.classes_list)):
                self.color[f'{i}'].clear()
            self.imagenumber = self.imagenumber + 1 #### Increase image number by one
            self.show_filtered_image(self.imagenumber) #### Show the next image

    #### Previous image function
    def prev_button_callback(self):
        #### Check if current image number is zero
        if self.imagenumber != 0: #### If current image number is not zero
            #### Check if user using filtering function
            if self.ui.comboBox.currentText() == '': #### If user not using filtering function
                self.ui.listWidget.clear()
                #### Change frame and buttons color
                self.ui.btn_save.setStyleSheet(self.dark_stylesheet)
                self.ui.frame.setStyleSheet(self.dark_stylesheet)
                self.ui.listWidget_rectangles.clear() #### Clear list widget to avoid duplicate
                #### Delete rectangles from graphics view
                for item in self.rectangles_list:
                    self.ui.graphicsView.delete_rec(item)
                #### Clear list
                self.rectangles_list.clear()
                for i in range(len(self.classes_list)):
                    self.color[f'{i}'].clear()
                self.imagenumber = self.imagenumber - 1 #### Decrease image number by one
                self.showimage(self.imagenumber) #### Show the previous image
            else: #### If user using filtering function
                self.ui.listWidget.clear()
                #### Change frame and buttons color
                self.ui.btn_save.setStyleSheet(self.dark_stylesheet)
                self.ui.frame.setStyleSheet(self.dark_stylesheet)
                self.ui.listWidget_rectangles.clear() #### Clear list widget to avoid duplicate
                #### Delete rectangles from graphics view
                for item in self.rectangles_list:
                    self.ui.graphicsView.delete_rec(item)
                #### Clear list
                self.rectangles_list.clear()
                for i in range(len(self.classes_list)):
                    self.color[f'{i}'].clear()
                self.imagenumber = self.imagenumber - 1 #### Decrease image number by one
                self.show_filtered_image(self.imagenumber) #### Show the previous image

    #### Delete rectangles function
    def delete_rectangle_button_callback(self):
        #### Change frame and buttons color
        self.ui.btn_save.setStyleSheet(self.dark_stylesheet)
        self.ui.frame.setStyleSheet(self.dark_stylesheet)
        #### Delete rectangles from graphics view
        for item in self.rectangles_list:
            self.ui.graphicsView.delete_rec(item)
        self.ui.listWidget_rectangles.clear() #### Clear list widget
        self.rectangles_list.clear() #### Clear list
        self.ui.btn_save.setFocus()

    #### If rectangle is selected
    def rectangle_selected(self):
        self.num = self.ui.graphicsView.number #### Get rectangle number from graphics view
        self.ui.listWidget_rectangles.setCurrentRow(self.num) #### Set focus item to selected rectangle class
        #### Change frame and buttons color
        self.ui.btn_save.setStyleSheet(self.dark_stylesheet)
        self.ui.frame.setStyleSheet(self.dark_stylesheet)

    #### Shortcut keys function
    def keyPressEvent(self, event):
        #### Previous image function (Key A)
        if event.key() == Qt.Key_A and self.ui.btn_prev.isEnabled():
            self.prev_button_callback()
        #### Next image function (Key D)
        if event.key() == Qt.Key_D and self.ui.btn_next.isEnabled():
            self.next_button_callback()
        #### Save function (Key Space)
        if event.key() == Qt.Key_Space and self.ui.btn_save.isEnabled():
            self.ui.btn_save.setFocus()
            self.save_button_callback()
        #### Delete rectangles function (Key Delete)
        if event.key() == Qt.Key_Delete and self.ui.btn_deleterectangle.isEnabled():
            self.delete_rectangle_button_callback()
        #### Change classes of rectangles
        #### Change to 1st class(Key 1)
        if event.key() == Qt.Key_1:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 0: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(0) #### Set current row to first item
                    self.check_label()
        #### Change to 2nd class(Key 2)
        if event.key() == Qt.Key_2:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 1: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(1) #### Set current row to first item
                    self.check_label()
        #### Change to 3rd class(Key 3)
        if event.key() == Qt.Key_3:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 2: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(2) #### Set current row to first item
                    self.check_label()
        #### Change to 4th class(Key 4)
        if event.key() == Qt.Key_4:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 3: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(3) #### Set current row to first item
                    self.check_label()
        #### Change to 5th class(Key 5)
        if event.key() == Qt.Key_5:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 4: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(4) #### Set current row to first item
                    self.check_label()
        #### Change to 6th class(Key 6)
        if event.key() == Qt.Key_6:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 5: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(5) #### Set current row to first item
                    self.check_label()
        #### Change to 7th class(Key 7)
        if event.key() == Qt.Key_7:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 6: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(6) #### Set current row to first item
                    self.check_label()
        #### Change to 8th class(Key 8)
        if event.key() == Qt.Key_8:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 7: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(7) #### Set current row to first item
                    self.check_label()
        #### Change to 9th class(Key 9)
        if event.key() == Qt.Key_9:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 8: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(8) #### Set current row to first item
                    self.check_label()
        #### Change to 10th class(Key 10)
        if event.key() == Qt.Key_0:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 9: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(9) #### Set current row to first item
                    self.check_label()
        #### Change to 11th class(Key 11)
        if event.key() == Qt.Key_Q:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 10: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(10) #### Set current row to first item
                    self.check_label()
        #### Change to 12th class(Key 12)
        if event.key() == Qt.Key_W:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 11: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(11) #### Set current row to first item
                    self.check_label()
        #### Change to 13th class(Key 13)
        if event.key() == Qt.Key_E:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 12: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(12) #### Set current row to first item
                    self.check_label()
        #### Change to 14th class(Key 14)
        if event.key() == Qt.Key_R:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 13: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(13) #### Set current row to first item
                    self.check_label()
        #### Change to 15th class(Key 15)
        if event.key() == Qt.Key_T:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 14: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(14) #### Set current row to first item
                    self.check_label()
        #### Change to 16th class(Key 16)
        if event.key() == Qt.Key_Y:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 15: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(15) #### Set current row to first item
                    self.check_label()
        #### Change to 17th class(Key 17)
        if event.key() == Qt.Key_U:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 16: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(16) #### Set current row to first item
                    self.check_label()
        #### Change to 18th class(Key 18)
        if event.key() == Qt.Key_I:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 17: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(17) #### Set current row to first item
                    self.check_label()
        #### Change to 19th class(Key 19)
        if event.key() == Qt.Key_O:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 18: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(18) #### Set current row to first item
                    self.check_label()
        #### Change to 20th class(Key 20)
        if event.key() == Qt.Key_P:
            #### Check if graphics view has any rectangle
            if len(self.ui.graphicsView.rect_list) == 0: #### If has no rectangle
                self.clear_list_widget() #### Clear focus on item of list widget
            else: #### If has any rectangle
                #### Check if list widget has enough item to select
                if self.ui.listWidget_classes.count() - 1 >= 19: #### If list widget has enough item to select
                    self.ui.listWidget_classes.setCurrentRow(19) #### Set current row to first item
                    self.check_label()

    #### Clear widget before closing local labelling program
    def closeEvent(self, event):
        #### Clear widgets
        self.ui.comboBox.clear()
        self.ui.listWidget_classes.clear()
        self.ui.listWidget_rectangles.clear()
        self.close_signal.emit(True) #### Send signal to local labelling login

    #### Clear focus on item of list widget
    def clear_list_widget(self):
        self.ui.listWidget_classes.clear() #### Clear list widget
        #### Add items to list widget
        for i in range(0, len(self.classes_list)):
            self.ui.listWidget_classes.addItem(self.classes_list[i])

    #### Show image on graphics view (Not filtering)
    def showimage(self, imagenumber):
        #### Clear all list
        self.selected_rectangle_list.clear()
        self.selected_rectangle_index_list.clear()
        self.png_list.clear()
        self.jpg_list.clear()

        self.total_image_list = []
        directory = self.open_file
        os.chdir(directory) #### Change working directory to read files
        #### Check image type
        for file in glob.glob("*.png"):
            self.png_list.append(file)
        for file in glob.glob("*jpg"):
            self.jpg_list.append(file)

        self.png_list.extend(self.jpg_list)
        self.total_image_list = self.png_list

        #### Check image enough to display
        if imagenumber < len(self.total_image_list):
            pixmap = QPixmap(directory + '\\' + self.total_image_list[imagenumber]) #### Convert image to pixmap
            image = QImage(directory + '\\' + self.total_image_list[imagenumber])
            self.image = QImage(directory + '\\' + self.total_image_list[imagenumber])
            filename, extension = os.path.splitext(self.total_image_list[imagenumber]) #### Split filename

        # if imagenumber < len(self.png_list) or imagenumber < len(self.jpg_list): #### If enough to display
            # try: #### Image type = jpg
            #     pixmap = QPixmap(directory + '\\' + self.jpg_list[imagenumber]) #### Convert image to pixmap
            #     image = QImage(directory + '\\' + self.jpg_list[imagenumber])
            #     self.image = QImage(directory + '\\' + self.jpg_list[imagenumber])
            #     filename, extension = os.path.splitext(self.jpg_list[imagenumber]) #### Split filename
            # except: #### Image type  = png
            #     pixmap = QPixmap(directory + '\\' + self.png_list[imagenumber]) #### Convert image to pixmap
            #     image = QImage(directory + '\\' + self.png_list[imagenumber])
            #     self.image = QImage(directory + '\\' + self.png_list[imagenumber])
            #     filename, extension = os.path.splitext(self.png_list[imagenumber]) #### Split filename

            text_file_extension = ".txt" #### Change image to text file
            self.text_file_name = filename + text_file_extension #### Join filename with text file extension
            open(self.text_file_name, "a") #### Create a text file if text file not existed
            #### Get image width and height
            self.image_width = image.width()
            self.image_height = image.height()
            self.ui.graphicsView.image_size(self.image_width, self.image_height) #### Send imag ewidth and height to graphics view
            self.ui.graphicsView.setPhoto(pixmap) #### Send pixmap to graphics view to show image
            #### Open text file to read data
            open_text_file = open(self.text_file_name, "r") 
            lines = open_text_file.readlines()
            index = []
            xc_iw = []
            yc_ih = []
            rw_iw = []
            rh_ih = []
            #### Extract data from text file and append separately to list accordingly
            for x in lines:
                index.append(x.split(' ')[0])
                xc_iw.append(x.split(' ')[1])
                yc_ih.append(x.split(' ')[2])
                rw_iw.append(x.split(' ')[3])
                rh_ih.append(x.split(' ')[4])
            #### Get value from list to draw rectangles
            for i in range(0, len(xc_iw)):
                index_value = index[i] #### Class of rectangle
                xc_iw_value = xc_iw[i]
                xc = (float(xc_iw_value))*self.image_width #### X center of rectangle
                yc_ih_value = yc_ih[i]
                yc = (float(yc_ih_value))*self.image_height #### Y center of rectangle
                rw_iw_value = rw_iw[i]
                rw = (float(rw_iw_value))*self.image_width #### Width of rectangle
                rh_ih_value = rh_ih[i]
                rh = (float(rh_ih_value))*self.image_height #### Height of rectangle
                topleft_x = xc - (rw/2) #### Top left x geometry of rectangle
                topleft_y = yc - (rh/2) #### Top left y geometry of rectangle
                self.ui.graphicsView.add_rect(topleft_x, topleft_y, rw, rh) #### Send data to graphics view to draw rectangles
                self.rectangles_list.append(self.ui.graphicsView._current_rect_item) #### Add rectangle name to list
                for h in range(len(self.classes_list)):
                    if index_value == str(h):
                        self.ui.listWidget_rectangles.addItem(self.classes_list[h]) #### Add class of rectangle to list widget
                        self.color[f'{h}'].append(self.ui.graphicsView._current_rect_item) #### Add rectangle name to dictionary
            self.ui.graphicsView.color_dict(self.color) #### Send data to graphics view to set color of rectangle 
            open_text_file.close() #### Close text file
        else:
            self.ui.listWidget.clear()
            self.ui.listWidget_rectangles.clear()
            for item in self.rectangles_list:
                self.ui.graphicsView.delete_rec(item)
            self.rectangles_list.clear()

            black_img = 0 * np.ones((1000,1000,3), np.uint8)
            img_resize = black_img
            self.image_height, self.image_width, ch = img_resize.shape
            self.ui.graphicsView.image_size(self.image_width, self.image_height)
            bytesPerLine = ch * self.image_width
            qimage = QImage(img_resize.data, self.image_width, self.image_height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
            self.pixmap = QPixmap(qimage)
            self.ui.graphicsView.setPhoto(self.pixmap)


    #### Enable buttons
    def enable_button(self):
        self.ui.btn_save.setEnabled(True)
        self.ui.btn_next.setEnabled(True)
        self.ui.btn_prev.setEnabled(True)
        self.ui.btn_add_rectangle.setEnabled(True)
        self.ui.btn_deleterectangle.setEnabled(True)
        
    #### Check when changing class
    def check_label(self):
        self.ui.listWidget_rectangles.takeItem(self.num) #### Remove the selected class from list widget
        if len(self.rectangles_list) == 0: #### If no rectangle on graphics view
            self.ui.listWidget_rectangles.clear() #### Clear list widget
        else: #### If has rectangle on graphics view
            self.select_label() #### Add item on list widget

    #### Add item on list widget
    def select_label(self):
        #### Change buttons and frame color
        self.ui.btn_save.setStyleSheet(self.dark_stylesheet)
        self.ui.frame.setStyleSheet(self.dark_stylesheet)
        #### Add item to list widget and list
        for i in range(len(self.classes_list)):
            if self.ui.listWidget_classes.currentRow() == i: #### Get the selected class
                self.ui.listWidget_rectangles.insertItem(self.num, self.classes_list[i]) #### Add class on list widget 
                self.selected_rectangle_list.append(self.rectangles_list[self.num]) #### Add rectangle name to list
                self.selected_rectangle_index_list.append(i) #### Add class index to list
        #### Send data to graphics view to change color of rectangle
        self.ui.graphicsView.selected_rectangle(self.selected_rectangle_list)
        self.ui.graphicsView.selected_rectangle_index(self.selected_rectangle_index_list)
        self.ui.listWidget_rectangles.setCurrentRow(self.num) #### Set current row of list widget to the selected rectangle
        self.ui.listWidget_classes.clearFocus()
        self.ui.graphicsView.setFocus()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Local_Labelling_Program()
    dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()
    window.setStyleSheet(dark_stylesheet)
    window.show()
    sys.exit(app.exec_())