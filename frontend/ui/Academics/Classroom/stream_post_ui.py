# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'stream_post.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)
import font_rc

class Ui_ClassroomStreamContent(object):
    def setupUi(self, ClassroomStreamContent):
        if not ClassroomStreamContent.objectName():
            ClassroomStreamContent.setObjectName(u"ClassroomStreamContent")
        ClassroomStreamContent.resize(934, 513)
        ClassroomStreamContent.setStyleSheet(u"QWidget {\n"
"    background-color: transparent;\n"
"    font-family:\"Poppins\";\n"
"}")
        self.verticalLayout_2 = QVBoxLayout(ClassroomStreamContent)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setObjectName(u"main_layout")
        self.mainContent = QWidget(ClassroomStreamContent)
        self.mainContent.setObjectName(u"mainContent")
        self.mainContent.setMinimumSize(QSize(200, 0))
        self.mainContent.setStyleSheet(u"QWidget {\n"
"    background: transparent;\n"
"    border-radius: 12px;\n"
"}")
        self.verticalLayout = QVBoxLayout(self.mainContent)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(self.mainContent)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setMinimumSize(QSize(200, 0))
        self.scrollArea.setStyleSheet(u"QScrollArea {\n"
"       border: none;\n"
"       background-color: transparent;\n"
"   }\n"
"   QScrollBar:vertical {\n"
"       border: none;\n"
"       background: #F1F1F1;\n"
"       width: 8px;\n"
"       border-radius: 4px;\n"
"   }\n"
"   QScrollBar::handle:vertical {\n"
"       background: #C1C1C1;\n"
"       border-radius: 4px;\n"
"       min-height: 20px;\n"
"   }\n"
"QScrollBar:horizontal {\n"
"       border: none;\n"
"       background: #F1F1F1;\n"
"       width: 8px;\n"
"       border-radius: 4px;\n"
"   }\n"
"   QScrollBar::handle:horizontal {\n"
"       background: #C1C1C1;\n"
"       border-radius: 4px;\n"
"       min-height: 20px;\n"
"   }")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, -11, 888, 548))
        self.verticalLayout_5 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.courseHeDER = QWidget(self.scrollAreaWidgetContents)
        self.courseHeDER.setObjectName(u"courseHeDER")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.courseHeDER.sizePolicy().hasHeightForWidth())
        self.courseHeDER.setSizePolicy(sizePolicy)
        self.courseHeDER.setMinimumSize(QSize(200, 200))
        self.courseHeDER.setStyleSheet(u"QWidget {\n"
"    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, \n"
"        stop:0 #2d8f6f, stop:1 #4db38b);\n"
"    border-radius: 12px;\n"
"}")
        self.verticalLayout_4 = QVBoxLayout(self.courseHeDER)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.headerLayout_2 = QVBoxLayout()
        self.headerLayout_2.setObjectName(u"headerLayout_2")
        self.headerLayout_2.setContentsMargins(40, 30, 40, 30)
        self.courseCode_label = QLabel(self.courseHeDER)
        self.courseCode_label.setObjectName(u"courseCode_label")
        self.courseCode_label.setStyleSheet(u"QLabel {\n"
"    color: rgba(255, 255, 255, 0.8);\n"
"    font-size: 14px;\n"
"	font-family: \"Poppins\";\n"
"    background: transparent;\n"
"}")

        self.headerLayout_2.addWidget(self.courseCode_label)

        self.courseTitle_label = QLabel(self.courseHeDER)
        self.courseTitle_label.setObjectName(u"courseTitle_label")
        self.courseTitle_label.setStyleSheet(u"QLabel {\n"
"    color: white;\n"
"    font-size: 32px;\n"
"    font-weight: bold;\n"
"	font-family: \"Poppins-Semi-Bold\";\n"
"    background: transparent;\n"
"}")
        self.courseTitle_label.setWordWrap(True)

        self.headerLayout_2.addWidget(self.courseTitle_label)

        self.courseSection_label = QLabel(self.courseHeDER)
        self.courseSection_label.setObjectName(u"courseSection_label")
        self.courseSection_label.setStyleSheet(u"QLabel {\n"
"    color: rgba(255, 255, 255, 0.9);\n"
"    font-size: 16px;\n"
"    font-weight: 400;\n"
"	font-family: \"Poppins\";\n"
"    background: transparent;\n"
"    margin-top: 8px;\n"
"}")

        self.headerLayout_2.addWidget(self.courseSection_label)


        self.verticalLayout_4.addLayout(self.headerLayout_2)


        self.verticalLayout_5.addWidget(self.courseHeDER)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setSpacing(20)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 8, 0, 30)
        self.syllabusFrame = QFrame(self.scrollAreaWidgetContents)
        self.syllabusFrame.setObjectName(u"syllabusFrame")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.syllabusFrame.sizePolicy().hasHeightForWidth())
        self.syllabusFrame.setSizePolicy(sizePolicy1)
        self.syllabusFrame.setMinimumSize(QSize(133, 152))
        self.syllabusFrame.setMaximumSize(QSize(140, 170))
        self.syllabusFrame.setStyleSheet(u"QFrame {\n"
"    background-color: white;\n"
"    border-radius: 8px;\n"
"    border: 1px solid #084924;\n"
"	background-position: top right;\n"
"}\n"
"QFrame:hover {\n"
"    border: 1px solid #e9ecef;\n"
"    box-shadow: 0 2px 8px rgba(0,0,0,0.08);\n"
"}")
        self.verticalLayout_9 = QVBoxLayout(self.syllabusFrame)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.syllabusCard_layout = QVBoxLayout()
        self.syllabusCard_layout.setSpacing(7)
        self.syllabusCard_layout.setObjectName(u"syllabusCard_layout")
        self.syllabussss = QWidget(self.syllabusFrame)
        self.syllabussss.setObjectName(u"syllabussss")
        self.horizontalLayout_7 = QHBoxLayout(self.syllabussss)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.icon_label2 = QLabel(self.syllabussss)
        self.icon_label2.setObjectName(u"icon_label2")
        self.icon_label2.setMaximumSize(QSize(28, 28))
        self.icon_label2.setStyleSheet(u"QLabel {\n"
"    background-color: #084924;\n"
"    border-radius: 20px;\n"
"    border: 2px solid white;\n"
"    color: white;\n"
"    font-size: 18px;\n"
"}")
        self.icon_label2.setWordWrap(False)

        self.horizontalLayout_7.addWidget(self.icon_label2)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_2 = QLabel(self.syllabussss)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setStyleSheet(u"border: none;\n"
"font-size: 16px;")

        self.horizontalLayout_6.addWidget(self.label_2)


        self.horizontalLayout_7.addLayout(self.horizontalLayout_6)


        self.syllabusCard_layout.addWidget(self.syllabussss)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.syllabusCard_layout.addItem(self.verticalSpacer_3)

        self.pushButton = QPushButton(self.syllabusFrame)
        self.pushButton.setObjectName(u"pushButton")

        self.syllabusCard_layout.addWidget(self.pushButton)


        self.verticalLayout_9.addLayout(self.syllabusCard_layout)


        self.horizontalLayout_5.addWidget(self.syllabusFrame, 0, Qt.AlignLeft|Qt.AlignTop)

        self.stream_item_container = QWidget(self.scrollAreaWidgetContents)
        self.stream_item_container.setObjectName(u"stream_item_container")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.stream_item_container.sizePolicy().hasHeightForWidth())
        self.stream_item_container.setSizePolicy(sizePolicy2)
        self.verticalLayout_6 = QVBoxLayout(self.stream_item_container)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.stream_items_layout = QVBoxLayout()
        self.stream_items_layout.setSpacing(10)
        self.stream_items_layout.setObjectName(u"stream_items_layout")
        self.postTemplate = QFrame(self.stream_item_container)
        self.postTemplate.setObjectName(u"postTemplate")
        self.postTemplate.setMinimumSize(QSize(200, 0))
        self.postTemplate.setStyleSheet(u"QFrame {\n"
"    background-color: white;\n"
"    border-radius: 8px;\n"
"    border: 1px solid #084924;\n"
"}\n"
"QFrame:hover {\n"
"    border: 1px solid #e9ecef;\n"
"    box-shadow: 0 2px 8px rgba(0,0,0,0.08);\n"
"}")
        self.postTemplate.setFrameShape(QFrame.NoFrame)
        self.horizontalLayout_2 = QHBoxLayout(self.postTemplate)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.icon_label = QLabel(self.postTemplate)
        self.icon_label.setObjectName(u"icon_label")
        self.icon_label.setMaximumSize(QSize(50, 50))
        self.icon_label.setStyleSheet(u"background-color: #084924; \n"
"border-radius: 25px; \n"
"border: 2px solid white;")

        self.horizontalLayout_2.addWidget(self.icon_label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.title_label = QLabel(self.postTemplate)
        self.title_label.setObjectName(u"title_label")
        self.title_label.setStyleSheet(u"font-size: 18px;\n"
"border:none;")
        self.title_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.title_label)

        self.date_label = QLabel(self.postTemplate)
        self.date_label.setObjectName(u"date_label")
        self.date_label.setStyleSheet(u"\n"
"	font-size: 14px;\n"
"	border:none;")
        self.date_label.setFrameShape(QFrame.NoFrame)
        self.date_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.date_label)


        self.horizontalLayout.addLayout(self.verticalLayout_3)


        self.horizontalLayout_2.addLayout(self.horizontalLayout)

        self.menu_button = QPushButton(self.postTemplate)
        self.menu_button.setObjectName(u"menu_button")
        self.menu_button.setMaximumSize(QSize(32, 32))
        self.menu_button.setStyleSheet(u"QPushButton {\n"
"    background: transparent;\n"
"    border: none;\n"
"    color: #6c757d;\n"
"    font-size: 32px;\n"
"    font-weight: bold;\n"
"    border-radius: 16px;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #f8f9fa;\n"
"    color: #495057;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: #e9ecef;\n"
"}")

        self.horizontalLayout_2.addWidget(self.menu_button)


        self.stream_items_layout.addWidget(self.postTemplate)


        self.verticalLayout_6.addLayout(self.stream_items_layout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.verticalLayout_6.addItem(self.verticalSpacer)


        self.horizontalLayout_5.addWidget(self.stream_item_container)


        self.verticalLayout_5.addLayout(self.horizontalLayout_5)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.verticalLayout_5.addItem(self.verticalSpacer_2)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)


        self.main_layout.addWidget(self.mainContent)


        self.verticalLayout_2.addLayout(self.main_layout)


        self.retranslateUi(ClassroomStreamContent)

        QMetaObject.connectSlotsByName(ClassroomStreamContent)
    # setupUi

    def retranslateUi(self, ClassroomStreamContent):
        ClassroomStreamContent.setWindowTitle(QCoreApplication.translate("ClassroomStreamContent", u"Form", None))
        self.courseCode_label.setText(QCoreApplication.translate("ClassroomStreamContent", u"ITSD81", None))
        self.courseTitle_label.setText(QCoreApplication.translate("ClassroomStreamContent", u"DESKTOP APPLICATION DEVELOPMENT LECTURE", None))
        self.courseSection_label.setText(QCoreApplication.translate("ClassroomStreamContent", u"BSIT-2C\n"
"MONDAY - 1:00 - 4:00 PM", None))
        self.icon_label2.setText("")
        self.label_2.setText(QCoreApplication.translate("ClassroomStreamContent", u"Syllabus", None))
        self.pushButton.setText(QCoreApplication.translate("ClassroomStreamContent", u"View", None))
        self.icon_label.setText(QCoreApplication.translate("ClassroomStreamContent", u"TextLabel", None))
        self.title_label.setText(QCoreApplication.translate("ClassroomStreamContent", u"Carlos Fidel Castro posted a material: Desktop Project Guidelines", None))
        self.date_label.setText(QCoreApplication.translate("ClassroomStreamContent", u"Aug 18", None))
        self.menu_button.setText(QCoreApplication.translate("ClassroomStreamContent", u"\u22ee", None))
    # retranslateUi

