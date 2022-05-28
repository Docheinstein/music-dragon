# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './res/ui/mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(964, 715)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.pagesButtons = QtWidgets.QWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pagesButtons.sizePolicy().hasHeightForWidth())
        self.pagesButtons.setSizePolicy(sizePolicy)
        self.pagesButtons.setMinimumSize(QtCore.QSize(160, 0))
        self.pagesButtons.setMaximumSize(QtCore.QSize(140, 16777215))
        self.pagesButtons.setObjectName("pagesButtons")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.pagesButtons)
        self.verticalLayout_6.setContentsMargins(0, -1, 0, -1)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.searchPageButton = ClickableLabel(self.pagesButtons)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.searchPageButton.setFont(font)
        self.searchPageButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.searchPageButton.setObjectName("searchPageButton")
        self.verticalLayout_6.addWidget(self.searchPageButton)
        self.localPageButton = ClickableLabel(self.pagesButtons)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.localPageButton.setFont(font)
        self.localPageButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.localPageButton.setObjectName("localPageButton")
        self.verticalLayout_6.addWidget(self.localPageButton)
        self.downloadsPageButton = ClickableLabel(self.pagesButtons)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.downloadsPageButton.setFont(font)
        self.downloadsPageButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.downloadsPageButton.setObjectName("downloadsPageButton")
        self.verticalLayout_6.addWidget(self.downloadsPageButton)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_6.addItem(spacerItem)
        self.horizontalLayout_5.addWidget(self.pagesButtons)
        self.verticalLayout_7 = QtWidgets.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.backButton = QtWidgets.QPushButton(self.centralwidget)
        self.backButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.backButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./res/ui/../images/back.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.backButton.setIcon(icon)
        self.backButton.setFlat(True)
        self.backButton.setObjectName("backButton")
        self.horizontalLayout_4.addWidget(self.backButton)
        self.forwardButton = QtWidgets.QPushButton(self.centralwidget)
        self.forwardButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.forwardButton.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("./res/ui/../images/forward.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.forwardButton.setIcon(icon1)
        self.forwardButton.setFlat(True)
        self.forwardButton.setObjectName("forwardButton")
        self.horizontalLayout_4.addWidget(self.forwardButton)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.verticalLayout_7.addLayout(self.horizontalLayout_4)
        self.pages = QtWidgets.QStackedWidget(self.centralwidget)
        self.pages.setObjectName("pages")
        self.searchPage = QtWidgets.QWidget()
        self.searchPage.setObjectName("searchPage")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.searchPage)
        self.verticalLayout.setObjectName("verticalLayout")
        self.searchBar = QtWidgets.QLineEdit(self.searchPage)
        self.searchBar.setText("")
        self.searchBar.setObjectName("searchBar")
        self.verticalLayout.addWidget(self.searchBar)
        self.searchResults = SearchResultsWidget(self.searchPage)
        self.searchResults.setIconSize(QtCore.QSize(80, 80))
        self.searchResults.setObjectName("searchResults")
        self.verticalLayout.addWidget(self.searchResults)
        self.pages.addWidget(self.searchPage)
        self.localPage = QtWidgets.QWidget()
        self.localPage.setObjectName("localPage")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.localPage)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.localSongs = LocalSongsView(self.localPage)
        self.localSongs.setMouseTracking(True)
        self.localSongs.setIconSize(QtCore.QSize(64, 64))
        self.localSongs.setUniformItemSizes(True)
        self.localSongs.setObjectName("localSongs")
        self.verticalLayout_4.addWidget(self.localSongs)
        self.localSongCount = QtWidgets.QLabel(self.localPage)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.localSongCount.setFont(font)
        self.localSongCount.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.localSongCount.setObjectName("localSongCount")
        self.verticalLayout_4.addWidget(self.localSongCount)
        self.pages.addWidget(self.localPage)
        self.downloadsPage = QtWidgets.QWidget()
        self.downloadsPage.setObjectName("downloadsPage")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.downloadsPage)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.manualDownloadURL = QtWidgets.QLineEdit(self.downloadsPage)
        self.manualDownloadURL.setObjectName("manualDownloadURL")
        self.horizontalLayout_7.addWidget(self.manualDownloadURL)
        self.manualDownloadButton = QtWidgets.QPushButton(self.downloadsPage)
        self.manualDownloadButton.setObjectName("manualDownloadButton")
        self.horizontalLayout_7.addWidget(self.manualDownloadButton)
        self.verticalLayout_11.addLayout(self.horizontalLayout_7)
        self.downloadsTabs = QtWidgets.QTabWidget(self.downloadsPage)
        self.downloadsTabs.setObjectName("downloadsTabs")
        self.downloadsQueuedTab = QtWidgets.QWidget()
        self.downloadsQueuedTab.setObjectName("downloadsQueuedTab")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.downloadsQueuedTab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.queuedDownloads = DownloadsWidget(self.downloadsQueuedTab)
        self.queuedDownloads.setObjectName("queuedDownloads")
        self.verticalLayout_3.addWidget(self.queuedDownloads)
        self.downloadsTabs.addTab(self.downloadsQueuedTab, "")
        self.downloadsFinishedTab = QtWidgets.QWidget()
        self.downloadsFinishedTab.setObjectName("downloadsFinishedTab")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.downloadsFinishedTab)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.finishedDownloads = DownloadsWidget(self.downloadsFinishedTab)
        self.finishedDownloads.setObjectName("finishedDownloads")
        self.verticalLayout_12.addWidget(self.finishedDownloads)
        self.downloadsTabs.addTab(self.downloadsFinishedTab, "")
        self.verticalLayout_11.addWidget(self.downloadsTabs)
        self.pages.addWidget(self.downloadsPage)
        self.albumPage = QtWidgets.QWidget()
        self.albumPage.setObjectName("albumPage")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.albumPage)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.albumCover = ClickableLabel(self.albumPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.albumCover.sizePolicy().hasHeightForWidth())
        self.albumCover.setSizePolicy(sizePolicy)
        self.albumCover.setMaximumSize(QtCore.QSize(160, 160))
        self.albumCover.setStyleSheet("")
        self.albumCover.setText("")
        self.albumCover.setPixmap(QtGui.QPixmap("./res/ui/../images/questionmark.png"))
        self.albumCover.setScaledContents(True)
        self.albumCover.setObjectName("albumCover")
        self.verticalLayout_2.addWidget(self.albumCover)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.albumCoverPrevButton = QtWidgets.QPushButton(self.albumPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.albumCoverPrevButton.sizePolicy().hasHeightForWidth())
        self.albumCoverPrevButton.setSizePolicy(sizePolicy)
        self.albumCoverPrevButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.albumCoverPrevButton.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("./res/ui/../images/left.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.albumCoverPrevButton.setIcon(icon2)
        self.albumCoverPrevButton.setIconSize(QtCore.QSize(20, 20))
        self.albumCoverPrevButton.setFlat(True)
        self.albumCoverPrevButton.setObjectName("albumCoverPrevButton")
        self.horizontalLayout.addWidget(self.albumCoverPrevButton)
        self.albumCoverNumber = QtWidgets.QLabel(self.albumPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.albumCoverNumber.sizePolicy().hasHeightForWidth())
        self.albumCoverNumber.setSizePolicy(sizePolicy)
        self.albumCoverNumber.setAlignment(QtCore.Qt.AlignCenter)
        self.albumCoverNumber.setObjectName("albumCoverNumber")
        self.horizontalLayout.addWidget(self.albumCoverNumber)
        self.albumCoverNextButton = QtWidgets.QPushButton(self.albumPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.albumCoverNextButton.sizePolicy().hasHeightForWidth())
        self.albumCoverNextButton.setSizePolicy(sizePolicy)
        self.albumCoverNextButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.albumCoverNextButton.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("./res/ui/../images/right.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.albumCoverNextButton.setIcon(icon3)
        self.albumCoverNextButton.setIconSize(QtCore.QSize(20, 20))
        self.albumCoverNextButton.setFlat(True)
        self.albumCoverNextButton.setObjectName("albumCoverNextButton")
        self.horizontalLayout.addWidget(self.albumCoverNextButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setContentsMargins(16, -1, -1, -1)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.albumTitle = QtWidgets.QLabel(self.albumPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.albumTitle.sizePolicy().hasHeightForWidth())
        self.albumTitle.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.albumTitle.setFont(font)
        self.albumTitle.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.albumTitle.setObjectName("albumTitle")
        self.verticalLayout_5.addWidget(self.albumTitle)
        self.albumArtist = ClickableLabel(self.albumPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.albumArtist.sizePolicy().hasHeightForWidth())
        self.albumArtist.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.albumArtist.setFont(font)
        self.albumArtist.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.albumArtist.setObjectName("albumArtist")
        self.verticalLayout_5.addWidget(self.albumArtist)
        self.albumYear = QtWidgets.QLabel(self.albumPage)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.albumYear.setFont(font)
        self.albumYear.setObjectName("albumYear")
        self.verticalLayout_5.addWidget(self.albumYear)
        self.albumSongCount = QtWidgets.QLabel(self.albumPage)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.albumSongCount.setFont(font)
        self.albumSongCount.setObjectName("albumSongCount")
        self.verticalLayout_5.addWidget(self.albumSongCount)
        self.widget = QtWidgets.QWidget(self.albumPage)
        self.widget.setMinimumSize(QtCore.QSize(0, 40))
        self.widget.setMaximumSize(QtCore.QSize(16777215, 40))
        self.widget.setObjectName("widget")
        self.verticalLayout_5.addWidget(self.widget)
        self.horizontalLayout_3.addLayout(self.verticalLayout_5)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.verticalLayout_10.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.albumDownloadAllButton = QtWidgets.QPushButton(self.albumPage)
        self.albumDownloadAllButton.setEnabled(False)
        self.albumDownloadAllButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.albumDownloadAllButton.setStyleSheet("padding: 8px")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("./res/ui/../images/download.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.albumDownloadAllButton.setIcon(icon4)
        self.albumDownloadAllButton.setIconSize(QtCore.QSize(26, 26))
        self.albumDownloadAllButton.setFlat(False)
        self.albumDownloadAllButton.setObjectName("albumDownloadAllButton")
        self.horizontalLayout_2.addWidget(self.albumDownloadAllButton)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.albumDownloadStatus = QtWidgets.QLabel(self.albumPage)
        self.albumDownloadStatus.setText("")
        self.albumDownloadStatus.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.albumDownloadStatus.setObjectName("albumDownloadStatus")
        self.horizontalLayout_2.addWidget(self.albumDownloadStatus)
        self.verticalLayout_10.addLayout(self.horizontalLayout_2)
        self.albumTracks = AlbumTracksWidget(self.albumPage)
        self.albumTracks.setObjectName("albumTracks")
        self.verticalLayout_10.addWidget(self.albumTracks)
        self.pages.addWidget(self.albumPage)
        self.artistPage = QtWidgets.QWidget()
        self.artistPage.setObjectName("artistPage")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.artistPage)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.artistCover = ClickableLabel(self.artistPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.artistCover.sizePolicy().hasHeightForWidth())
        self.artistCover.setSizePolicy(sizePolicy)
        self.artistCover.setMaximumSize(QtCore.QSize(160, 160))
        self.artistCover.setText("")
        self.artistCover.setPixmap(QtGui.QPixmap("./res/ui/../images/questionmark.png"))
        self.artistCover.setScaledContents(True)
        self.artistCover.setObjectName("artistCover")
        self.horizontalLayout_6.addWidget(self.artistCover)
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setContentsMargins(16, -1, -1, -1)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.artistName = QtWidgets.QLabel(self.artistPage)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.artistName.sizePolicy().hasHeightForWidth())
        self.artistName.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.artistName.setFont(font)
        self.artistName.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.artistName.setObjectName("artistName")
        self.verticalLayout_8.addWidget(self.artistName)
        self.horizontalLayout_6.addLayout(self.verticalLayout_8)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem4)
        self.verticalLayout_9.addLayout(self.horizontalLayout_6)
        self.artistAlbums = ArtistAlbumsWidget(self.artistPage)
        self.artistAlbums.setObjectName("artistAlbums")
        self.verticalLayout_9.addWidget(self.artistAlbums)
        self.pages.addWidget(self.artistPage)
        self.verticalLayout_7.addWidget(self.pages)
        self.horizontalLayout_5.addLayout(self.verticalLayout_7)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 964, 34))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuTools = QtWidgets.QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionPreferences = QtWidgets.QAction(MainWindow)
        self.actionPreferences.setObjectName("actionPreferences")
        self.actionReload = QtWidgets.QAction(MainWindow)
        self.actionReload.setObjectName("actionReload")
        self.actionYtMusicSetup = QtWidgets.QAction(MainWindow)
        self.actionYtMusicSetup.setObjectName("actionYtMusicSetup")
        self.menuFile.addAction(self.actionReload)
        self.menuEdit.addAction(self.actionPreferences)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())

        self.retranslateUi(MainWindow)
        self.pages.setCurrentIndex(4)
        self.downloadsTabs.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Music Dragon"))
        self.searchPageButton.setText(_translate("MainWindow", "Search"))
        self.localPageButton.setText(_translate("MainWindow", "Local"))
        self.downloadsPageButton.setText(_translate("MainWindow", "Downloads"))
        self.searchBar.setPlaceholderText(_translate("MainWindow", "Search for artists, album, songs..."))
        self.localSongCount.setText(_translate("MainWindow", "0 Songs"))
        self.manualDownloadURL.setPlaceholderText(_translate("MainWindow", "YouTube URL..."))
        self.manualDownloadButton.setText(_translate("MainWindow", "Download"))
        self.downloadsTabs.setTabText(self.downloadsTabs.indexOf(self.downloadsQueuedTab), _translate("MainWindow", "Queue"))
        self.downloadsTabs.setTabText(self.downloadsTabs.indexOf(self.downloadsFinishedTab), _translate("MainWindow", "Completed"))
        self.albumCoverNumber.setText(_translate("MainWindow", "1/2"))
        self.albumTitle.setText(_translate("MainWindow", "Fear of the Dark"))
        self.albumArtist.setText(_translate("MainWindow", "Iron Maiden"))
        self.albumYear.setText(_translate("MainWindow", "1992"))
        self.albumSongCount.setText(_translate("MainWindow", "8 songs - 58 min 37 sec"))
        self.albumDownloadAllButton.setText(_translate("MainWindow", "Download missing songs"))
        self.artistName.setText(_translate("MainWindow", "Iron Maiden"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuTools.setTitle(_translate("MainWindow", "Tools"))
        self.actionPreferences.setText(_translate("MainWindow", "Preferences"))
        self.actionReload.setText(_translate("MainWindow", "Reload"))
        self.actionReload.setShortcut(_translate("MainWindow", "F5"))
        self.actionYtMusicSetup.setText(_translate("MainWindow", "YtMusic Setup"))
from ui.albumtrackswidget import AlbumTracksWidget
from ui.artistalbumswidget import ArtistAlbumsWidget
from ui.clickablelabel import ClickableLabel
from ui.downloadswidget import DownloadsWidget
from ui.localsongsview import LocalSongsView
from ui.searchresultswidget import SearchResultsWidget
