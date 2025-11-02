# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'classroom_classworks_content.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QScrollArea, QSizePolicy, QSpacerItem, QToolButton,
    QVBoxLayout, QWidget)
import font_rc
import icons_rc

class Ui_ClassroomClassworksContent(object):
    def setupUi(self, ClassroomClassworksContent):
        if not ClassroomClassworksContent.objectName():
            ClassroomClassworksContent.setObjectName(u"ClassroomClassworksContent")
        ClassroomClassworksContent.resize(940, 530)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ClassroomClassworksContent.sizePolicy().hasHeightForWidth())
        ClassroomClassworksContent.setSizePolicy(sizePolicy)
        ClassroomClassworksContent.setMinimumSize(QSize(400, 530))
        ClassroomClassworksContent.setStyleSheet(u"QWidget {\n"
"       background-color: transparent;\n"
"       font-family: \"Poppins\", Arial, sans-serif;\n"
"   }")
        self.verticalLayout_2 = QVBoxLayout(ClassroomClassworksContent)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.classworkMainVerticalLayout = QVBoxLayout()
        self.classworkMainVerticalLayout.setSpacing(15)
        self.classworkMainVerticalLayout.setObjectName(u"classworkMainVerticalLayout")
        self.classworkMainVerticalLayout.setContentsMargins(20, 20, 20, 20)
        self.topBarLayout = QHBoxLayout()
        self.topBarLayout.setSpacing(15)
        self.topBarLayout.setObjectName(u"topBarLayout")
        self.createButton = QToolButton(ClassroomClassworksContent)
        self.createButton.setObjectName(u"createButton")
        self.createButton.setMaximumSize(QSize(100, 40))
        self.createButton.setContextMenuPolicy(Qt.NoContextMenu)
        self.createButton.setStyleSheet(u"   QToolButton {\n"
"       background-color: #084924;\n"
"       color: white;\n"
"       border: none;\n"
"       padding: 6px 12px;\n"
"       border-radius: 5px;\n"
"       font-weight: 600;\n"
"       font-size: 11px;\n"
"   }\n"
"   QToolButton:hover {\n"
"       background-color: #1B5E20;\n"
"   }\n"
"   QToolButton:pressed {\n"
"       background-color: #0D4E12;\n"
"   }")
        icon = QIcon()
        icon.addFile(u":/icons/baseline-add.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.createButton.setIcon(icon)
        self.createButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.createButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.createButton.setArrowType(Qt.NoArrow)

        self.topBarLayout.addWidget(self.createButton)

        self.horizontalSpacer = QSpacerItem(60, 20, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)

        self.topBarLayout.addItem(self.horizontalSpacer)


        self.classworkMainVerticalLayout.addLayout(self.topBarLayout)

        self.filterComboBox = QComboBox(ClassroomClassworksContent)
        self.filterComboBox.addItem("")
        self.filterComboBox.addItem("")
        self.filterComboBox.addItem("")
        self.filterComboBox.setObjectName(u"filterComboBox")
        self.filterComboBox.setMaximumSize(QSize(276, 40))
        self.filterComboBox.setStyleSheet(u"QComboBox {\n"
"       border: 1px solid #D0D7DE;\n"
"       border-radius: 4px;\n"
"       padding: 5px 8px;\n"
"       background-color: white;\n"
"       font-size: 12px;\n"
"   }\n"
"   QComboBox:hover {\n"
"       border-color: #A8A8A8;\n"
"   }\n"
"   QComboBox::drop-down {\n"
"       border: none;\n"
"       width: 20px;\n"
"   }\n"
"\n"
"	QComboBox::down-arrow {\n"
"       image: none;\n"
"       border-left: 4px solid transparent;\n"
"       border-right: 4px solid transparent;\n"
"       border-top: 4px solid #666;\n"
"   }\n"
"\n"
"")

        self.classworkMainVerticalLayout.addWidget(self.filterComboBox)

        self.topicScrollArea = QScrollArea(ClassroomClassworksContent)
        self.topicScrollArea.setObjectName(u"topicScrollArea")
        self.topicScrollArea.setMinimumSize(QSize(200, 0))
        self.topicScrollArea.setMaximumSize(QSize(16777215, 16777215))
        self.topicScrollArea.setBaseSize(QSize(0, 0))
        self.topicScrollArea.setStyleSheet(u"QScrollArea {\n"
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
"   }")
        self.topicScrollArea.setFrameShape(QFrame.NoFrame)
        self.topicScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 882, 370))
        self.scrollAreaWidgetContents.setMinimumSize(QSize(200, 0))
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.topicListLayout = QVBoxLayout()
        self.topicListLayout.setSpacing(4)
        self.topicListLayout.setObjectName(u"topicListLayout")
        self.topicListLayout.setContentsMargins(-1, 9, 0, 0)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.topicListLayout.addItem(self.verticalSpacer)


        self.verticalLayout_3.addLayout(self.topicListLayout)

        self.topicScrollArea.setWidget(self.scrollAreaWidgetContents)

        self.classworkMainVerticalLayout.addWidget(self.topicScrollArea)


        self.verticalLayout_2.addLayout(self.classworkMainVerticalLayout)


        self.retranslateUi(ClassroomClassworksContent)

        QMetaObject.connectSlotsByName(ClassroomClassworksContent)
    # setupUi

    def retranslateUi(self, ClassroomClassworksContent):
        ClassroomClassworksContent.setWindowTitle(QCoreApplication.translate("ClassroomClassworksContent", u"classworks", None))
        self.createButton.setText(QCoreApplication.translate("ClassroomClassworksContent", u"Create", None))
        self.filterComboBox.setItemText(0, QCoreApplication.translate("ClassroomClassworksContent", u"All items", None))
        self.filterComboBox.setItemText(1, QCoreApplication.translate("ClassroomClassworksContent", u"Material", None))
        self.filterComboBox.setItemText(2, QCoreApplication.translate("ClassroomClassworksContent", u"Assessment", None))

    # retranslateUi

