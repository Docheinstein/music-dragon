# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui/mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.stack = QtWidgets.QStackedWidget(self.centralwidget)
        self.stack.setObjectName("stack")
        self.searchWidget = QtWidgets.QWidget()
        self.searchWidget.setObjectName("searchWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.searchWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.searchBar = QtWidgets.QLineEdit(self.searchWidget)
        self.searchBar.setObjectName("searchBar")
        self.verticalLayout.addWidget(self.searchBar)
        self.label = QtWidgets.QLabel(self.searchWidget)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.searchResults = QtWidgets.QListView(self.searchWidget)
        self.searchResults.setIconSize(QtCore.QSize(80, 80))
        self.searchResults.setObjectName("searchResults")
        self.verticalLayout.addWidget(self.searchResults)
        self.stack.addWidget(self.searchWidget)
        self.albumWidget = QtWidgets.QWidget()
        self.albumWidget.setObjectName("albumWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.albumWidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.albumBackButton = QtWidgets.QToolButton(self.albumWidget)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./ui/../res/back.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.albumBackButton.setIcon(icon)
        self.albumBackButton.setIconSize(QtCore.QSize(24, 24))
        self.albumBackButton.setObjectName("albumBackButton")
        self.verticalLayout_2.addWidget(self.albumBackButton)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(20)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.albumIcon = QtWidgets.QLabel(self.albumWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.albumIcon.sizePolicy().hasHeightForWidth())
        self.albumIcon.setSizePolicy(sizePolicy)
        self.albumIcon.setMaximumSize(QtCore.QSize(160, 160))
        self.albumIcon.setText("")
        self.albumIcon.setPixmap(QtGui.QPixmap("./ui/../res/questionmark.png"))
        self.albumIcon.setScaledContents(True)
        self.albumIcon.setObjectName("albumIcon")
        self.horizontalLayout.addWidget(self.albumIcon)
        self.albumTitle = QtWidgets.QLabel(self.albumWidget)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.albumTitle.setFont(font)
        self.albumTitle.setObjectName("albumTitle")
        self.horizontalLayout.addWidget(self.albumTitle)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.albumSongs = QtWidgets.QListView(self.albumWidget)
        self.albumSongs.setObjectName("albumSongs")
        self.verticalLayout_2.addWidget(self.albumSongs)
        self.stack.addWidget(self.albumWidget)
        self.horizontalLayout_3.addWidget(self.stack)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 34))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.stack.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.searchBar.setPlaceholderText(_translate("MainWindow", "Search for artist..."))
        self.label.setText(_translate("MainWindow", "Results"))
        self.albumBackButton.setText(_translate("MainWindow", "..."))
        self.albumTitle.setText(_translate("MainWindow", "Fear of the Dark"))
