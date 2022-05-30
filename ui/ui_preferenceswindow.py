# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './res/ui/preferenceswindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PreferencesWindow(object):
    def setupUi(self, PreferencesWindow):
        PreferencesWindow.setObjectName("PreferencesWindow")
        PreferencesWindow.resize(474, 642)
        self.verticalLayout = QtWidgets.QVBoxLayout(PreferencesWindow)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(PreferencesWindow)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tab)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.scrollArea = QtWidgets.QScrollArea(self.tab)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 438, 533))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setSpacing(12)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.directoryWidget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.directoryWidget.sizePolicy().hasHeightForWidth())
        self.directoryWidget.setSizePolicy(sizePolicy)
        self.directoryWidget.setObjectName("directoryWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.directoryWidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label = QtWidgets.QLabel(self.directoryWidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout_3.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.directory = ClickableLabel(self.directoryWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.directory.sizePolicy().hasHeightForWidth())
        self.directory.setSizePolicy(sizePolicy)
        self.directory.setMinimumSize(QtCore.QSize(0, 40))
        self.directory.setObjectName("directory")
        self.horizontalLayout.addWidget(self.directory)
        self.browseDirectoryButton = QtWidgets.QPushButton(self.directoryWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.browseDirectoryButton.sizePolicy().hasHeightForWidth())
        self.browseDirectoryButton.setSizePolicy(sizePolicy)
        self.browseDirectoryButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.browseDirectoryButton.setIconSize(QtCore.QSize(24, 24))
        self.browseDirectoryButton.setFlat(False)
        self.browseDirectoryButton.setObjectName("browseDirectoryButton")
        self.horizontalLayout.addWidget(self.browseDirectoryButton)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout_4.addWidget(self.directoryWidget)
        self.widget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.widget.setObjectName("widget")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_2 = QtWidgets.QLabel(self.widget)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_5.addWidget(self.label_2)
        self.coverSize = QtWidgets.QComboBox(self.widget)
        self.coverSize.setObjectName("coverSize")
        self.coverSize.addItem("")
        self.coverSize.addItem("")
        self.coverSize.addItem("")
        self.coverSize.addItem("")
        self.verticalLayout_5.addWidget(self.coverSize)
        self.verticalLayout_4.addWidget(self.widget)
        self.widget_2 = QtWidgets.QWidget(self.scrollAreaWidgetContents)
        self.widget_2.setObjectName("widget_2")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.widget_2)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label_3 = QtWidgets.QLabel(self.widget_2)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_6.addWidget(self.label_3)
        self.outputFormat = QtWidgets.QLineEdit(self.widget_2)
        self.outputFormat.setObjectName("outputFormat")
        self.verticalLayout_6.addWidget(self.outputFormat)
        self.label_4 = QtWidgets.QLabel(self.widget_2)
        self.label_4.setWordWrap(True)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_6.addWidget(self.label_4)
        self.verticalLayout_4.addWidget(self.widget_2)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_2.addWidget(self.scrollArea)
        self.tabWidget.addTab(self.tab, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.tab_3)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.scrollArea_3 = QtWidgets.QScrollArea(self.tab_3)
        self.scrollArea_3.setWidgetResizable(True)
        self.scrollArea_3.setObjectName("scrollArea_3")
        self.scrollAreaWidgetContents_3 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_3.setGeometry(QtCore.QRect(0, 0, 438, 533))
        self.scrollAreaWidgetContents_3.setObjectName("scrollAreaWidgetContents_3")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_3)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.cacheWidget = QtWidgets.QWidget(self.scrollAreaWidgetContents_3)
        self.cacheWidget.setObjectName("cacheWidget")
        self.verticalLayout_13 = QtWidgets.QVBoxLayout(self.cacheWidget)
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.label_9 = QtWidgets.QLabel(self.cacheWidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.verticalLayout_13.addWidget(self.label_9)
        self.cache = ClickableLabel(self.cacheWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cache.sizePolicy().hasHeightForWidth())
        self.cache.setSizePolicy(sizePolicy)
        self.cache.setMinimumSize(QtCore.QSize(0, 40))
        self.cache.setObjectName("cache")
        self.verticalLayout_13.addWidget(self.cache)
        self.cacheImagesCheck = QtWidgets.QCheckBox(self.cacheWidget)
        self.cacheImagesCheck.setObjectName("cacheImagesCheck")
        self.verticalLayout_13.addWidget(self.cacheImagesCheck)
        self.cacheRequestsBox = QtWidgets.QCheckBox(self.cacheWidget)
        self.cacheRequestsBox.setObjectName("cacheRequestsBox")
        self.verticalLayout_13.addWidget(self.cacheRequestsBox)
        self.cacheSize = QtWidgets.QLabel(self.cacheWidget)
        self.cacheSize.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.cacheSize.setObjectName("cacheSize")
        self.verticalLayout_13.addWidget(self.cacheSize)
        self.cacheClearButton = QtWidgets.QPushButton(self.cacheWidget)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./res/ui/../images/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.cacheClearButton.setIcon(icon)
        self.cacheClearButton.setIconSize(QtCore.QSize(24, 24))
        self.cacheClearButton.setObjectName("cacheClearButton")
        self.verticalLayout_13.addWidget(self.cacheClearButton)
        spacerItem1 = QtWidgets.QSpacerItem(17, 289, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_13.addItem(spacerItem1)
        self.verticalLayout_12.addWidget(self.cacheWidget)
        self.scrollArea_3.setWidget(self.scrollAreaWidgetContents_3)
        self.verticalLayout_11.addWidget(self.scrollArea_3)
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.tab_2)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.scrollArea_2 = QtWidgets.QScrollArea(self.tab_2)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 438, 533))
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_7.setSpacing(12)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.widget_3 = QtWidgets.QWidget(self.scrollAreaWidgetContents_2)
        self.widget_3.setObjectName("widget_3")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.widget_3)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.label_6 = QtWidgets.QLabel(self.widget_3)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.verticalLayout_9.addWidget(self.label_6)
        self.threadNumber = QtWidgets.QSpinBox(self.widget_3)
        self.threadNumber.setObjectName("threadNumber")
        self.verticalLayout_9.addWidget(self.threadNumber)
        self.label_5 = QtWidgets.QLabel(self.widget_3)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setItalic(True)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.verticalLayout_9.addWidget(self.label_5)
        self.verticalLayout_7.addWidget(self.widget_3)
        self.widget_4 = QtWidgets.QWidget(self.scrollAreaWidgetContents_2)
        self.widget_4.setObjectName("widget_4")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.widget_4)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.label_8 = QtWidgets.QLabel(self.widget_4)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.verticalLayout_10.addWidget(self.label_8)
        self.maxSimultaneousDownloads = QtWidgets.QSpinBox(self.widget_4)
        self.maxSimultaneousDownloads.setObjectName("maxSimultaneousDownloads")
        self.verticalLayout_10.addWidget(self.maxSimultaneousDownloads)
        self.label_7 = QtWidgets.QLabel(self.widget_4)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setItalic(True)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.verticalLayout_10.addWidget(self.label_7)
        self.verticalLayout_7.addWidget(self.widget_4)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_7.addItem(spacerItem2)
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)
        self.verticalLayout_8.addWidget(self.scrollArea_2)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(PreferencesWindow)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(PreferencesWindow)
        self.tabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(PreferencesWindow.accept) # type: ignore
        self.buttonBox.rejected.connect(PreferencesWindow.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(PreferencesWindow)

    def retranslateUi(self, PreferencesWindow):
        _translate = QtCore.QCoreApplication.translate
        PreferencesWindow.setWindowTitle(_translate("PreferencesWindow", "Preferences"))
        self.label.setText(_translate("PreferencesWindow", "Directory"))
        self.directory.setText(_translate("PreferencesWindow", "~/MusicDragon"))
        self.browseDirectoryButton.setText(_translate("PreferencesWindow", "Browse"))
        self.label_2.setText(_translate("PreferencesWindow", "Cover size"))
        self.coverSize.setItemText(0, _translate("PreferencesWindow", "Small (250)"))
        self.coverSize.setItemText(1, _translate("PreferencesWindow", "Medium (500)"))
        self.coverSize.setItemText(2, _translate("PreferencesWindow", "Large (1200)"))
        self.coverSize.setItemText(3, _translate("PreferencesWindow", "Largest"))
        self.label_3.setText(_translate("PreferencesWindow", "Output format"))
        self.label_4.setText(_translate("PreferencesWindow", "<html><head/><body><p><span style=\" font-size:10pt;\">{artist}: </span><span style=\" font-size:10pt; font-style:italic;\">artist name</span><span style=\" font-size:10pt;\"><br/>{album}: </span><span style=\" font-size:10pt; font-style:italic;\">album title</span><span style=\" font-size:10pt;\"><br/>{song}: </span><span style=\" font-size:10pt; font-style:italic;\">song name</span><span style=\" font-size:10pt;\"><br/>{ext}: </span><span style=\" font-size:10pt; font-style:italic;\">extension</span></p></body></html>"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("PreferencesWindow", "General"))
        self.label_9.setText(_translate("PreferencesWindow", "Cache"))
        self.cache.setText(_translate("PreferencesWindow", " ~/MusicDragon"))
        self.cacheImagesCheck.setText(_translate("PreferencesWindow", "Cache images"))
        self.cacheRequestsBox.setText(_translate("PreferencesWindow", "Cache requests"))
        self.cacheSize.setText(_translate("PreferencesWindow", "Size: 0MB"))
        self.cacheClearButton.setText(_translate("PreferencesWindow", "Clear Cache"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("PreferencesWindow", "Cache"))
        self.label_6.setText(_translate("PreferencesWindow", "Thread number"))
        self.label_5.setText(_translate("PreferencesWindow", "This option requires an application restart to take effect."))
        self.label_8.setText(_translate("PreferencesWindow", "Maximum simultaneous downloads"))
        self.label_7.setText(_translate("PreferencesWindow", "This option requires an application restart to take effect."))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("PreferencesWindow", "Threads"))
from ui.clickablelabel import ClickableLabel
