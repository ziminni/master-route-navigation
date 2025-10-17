# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'view_material.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PyQt6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PyQt6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PyQt6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTextEdit,
    QVBoxLayout, QWidget)
import font_rc
import icons_rc

class Ui_viewMaterial(object):
    def setupUi(self, viewMaterial):
        if not viewMaterial.objectName():
            viewMaterial.setObjectName(u"viewMaterial")
        viewMaterial.resize(747, 452)
        viewMaterial.setMinimumSize(QSize(200, 300))
        viewMaterial.setStyleSheet(u"QWidget { background-color: white; font-family: \"Poppins\", Arial, sans-serif; }")
        self.verticalLayout_2 = QVBoxLayout(viewMaterial)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setObjectName(u"headerLayout")
        self.headerLayout.setContentsMargins(-1, 10, -1, -1)
        self.backButton = QLabel(viewMaterial)
        self.backButton.setObjectName(u"backButton")
        self.backButton.setMinimumSize(QSize(50, 50))
        self.backButton.setMaximumSize(QSize(50, 50))
        self.backButton.setStyleSheet(u"border: none; background: transparent; padding: 5px;")
        self.backButton.setPixmap(QPixmap(u":/icons/back2.png"))

        self.headerLayout.addWidget(self.backButton)

        self.titleMetaLayout = QVBoxLayout()
        self.titleMetaLayout.setObjectName(u"titleMetaLayout")
        self.title_label = QLabel(viewMaterial)
        self.title_label.setObjectName(u"title_label")
        self.title_label.setStyleSheet(u"font-size: 54px; font-weight: 400; color: #333; margin-bottom: 10px;\n"
"")
        self.title_label.setWordWrap(True)

        self.titleMetaLayout.addWidget(self.title_label)

        self.metaLayout = QHBoxLayout()
        self.metaLayout.setObjectName(u"metaLayout")
        self.instructor_label = QLabel(viewMaterial)
        self.instructor_label.setObjectName(u"instructor_label")
        self.instructor_label.setStyleSheet(u"font-size: 20px; color: #24292f;\n"
"margin-left: 10px;")

        self.metaLayout.addWidget(self.instructor_label)

        self.date_label = QLabel(viewMaterial)
        self.date_label.setObjectName(u"date_label")
        self.date_label.setStyleSheet(u"font-size: 20px; color: #656d76; padding-left: 5px;")

        self.metaLayout.addWidget(self.date_label)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.metaLayout.addItem(self.horizontalSpacer_3)


        self.titleMetaLayout.addLayout(self.metaLayout)


        self.headerLayout.addLayout(self.titleMetaLayout)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.headerLayout.addItem(self.horizontalSpacer_2)

        self.menuButton = QPushButton(viewMaterial)
        self.menuButton.setObjectName(u"menuButton")
        self.menuButton.setMaximumSize(QSize(40, 40))
        self.menuButton.setStyleSheet(u"QPushButton {\n"
"    background: transparent;\n"
"    border: none;\n"
"    color: #6c757d;\n"
"    font-size: 40px;\n"
"    font-weight: bold;\n"
"    border-radius: 20px;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #f8f9fa;\n"
"    color: #495057;\n"
"}\n"
"QPushButton:pressed {\n"
"    background-color: #e9ecef;\n"
"}")

        self.headerLayout.addWidget(self.menuButton)


        self.verticalLayout.addLayout(self.headerLayout)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.descriptionEdit = QTextEdit(viewMaterial)
        self.descriptionEdit.setObjectName(u"descriptionEdit")
        self.descriptionEdit.setMinimumSize(QSize(200, 0))
        self.descriptionEdit.setMaximumSize(QSize(16777215, 16777215))
        self.descriptionEdit.setStyleSheet(u"font-size: 16px; color: #000000; padding: 10px;  border: 1px solid #ddd; border-radius: 5px;\n"
"margin-left: 80px;\n"
"margin-bottom: 10px;")
        self.descriptionEdit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.descriptionEdit.setLineWrapColumnOrWidth(0)
        self.descriptionEdit.setReadOnly(True)
        self.descriptionEdit.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.verticalLayout_2.addWidget(self.descriptionEdit)

        self.attachementLayout = QHBoxLayout()
        self.attachementLayout.setSpacing(10)
        self.attachementLayout.setObjectName(u"attachementLayout")
        self.attachementLayout.setContentsMargins(80, 10, -1, 10)
        self.attachmentFrame = QFrame(viewMaterial)
        self.attachmentFrame.setObjectName(u"attachmentFrame")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.attachmentFrame.sizePolicy().hasHeightForWidth())
        self.attachmentFrame.setSizePolicy(sizePolicy)
        self.attachmentFrame.setMinimumSize(QSize(300, 76))
        self.attachmentFrame.setMaximumSize(QSize(400, 76))
        self.attachmentFrame.setMouseTracking(True)
        self.attachmentFrame.setStyleSheet(u"QFrame #attachmentFrame { \n"
"background-color: white; \n"
"border: 1px solid #ddd; \n"
"border-radius: 10px; \n"
"padding: 5px;}")
        self.attachmentFrame.setFrameShape(QFrame.StyledPanel)
        self.attachmentFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_7 = QVBoxLayout(self.attachmentFrame)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.attachmentInnerLayout = QVBoxLayout()
        self.attachmentInnerLayout.setObjectName(u"attachmentInnerLayout")
        self.attachmentName = QLabel(self.attachmentFrame)
        self.attachmentName.setObjectName(u"attachmentName")
        self.attachmentName.setStyleSheet(u"\n"
"font-size: 16px; \n"
"color: #24292f; \n"
"text-align: center; \n"
"text-decoration: underline;\n"
"")

        self.attachmentInnerLayout.addWidget(self.attachmentName)

        self.attachmentType = QLabel(self.attachmentFrame)
        self.attachmentType.setObjectName(u"attachmentType")
        self.attachmentType.setStyleSheet(u"font-size: 14px; color: #656d76; text-align: center;")

        self.attachmentInnerLayout.addWidget(self.attachmentType)


        self.verticalLayout_7.addLayout(self.attachmentInnerLayout)


        self.attachementLayout.addWidget(self.attachmentFrame)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.attachementLayout.addItem(self.horizontalSpacer_4)


        self.verticalLayout_2.addLayout(self.attachementLayout)

        self.commentLayout = QHBoxLayout()
        self.commentLayout.setObjectName(u"commentLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.commentLayout.addItem(self.horizontalSpacer)

        self.label = QLabel(viewMaterial)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(38, 38))
        self.label.setStyleSheet(u"background-color: #084924; border-radius: 19px; color: white; min-width: 38px; min-height: 38px; text-align: center; line-height: 38px;")
        self.label.setAlignment(Qt.AlignCenter)

        self.commentLayout.addWidget(self.label)

        self.commentBox = QTextEdit(viewMaterial)
        self.commentBox.setObjectName(u"commentBox")
        self.commentBox.setMinimumSize(QSize(200, 20))
        self.commentBox.setMaximumSize(QSize(16777215, 50))
        self.commentBox.setStyleSheet(u"font-size: 14px; color: #24292f; padding: 5px; border: 1px solid #ddd; border-radius: 16.5px;")
        self.commentBox.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.commentLayout.addWidget(self.commentBox)

        self.pushButton = QPushButton(viewMaterial)
        self.pushButton.setObjectName(u"pushButton")

        self.commentLayout.addWidget(self.pushButton)


        self.verticalLayout_2.addLayout(self.commentLayout)

        self.verticalSpacer = QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.retranslateUi(viewMaterial)

        QMetaObject.connectSlotsByName(viewMaterial)
    # setupUi

    def retranslateUi(self, viewMaterial):
        viewMaterial.setWindowTitle(QCoreApplication.translate("viewMaterial", u"material details", None))
        self.backButton.setText("")
        self.title_label.setText(QCoreApplication.translate("viewMaterial", u"Desktop Project Guidelines", None))
        self.instructor_label.setText(QCoreApplication.translate("viewMaterial", u"Carlos Fidel Castro", None))
        self.date_label.setText(QCoreApplication.translate("viewMaterial", u"\u2022 August 18, 2025", None))
        self.menuButton.setText(QCoreApplication.translate("viewMaterial", u"\u22ee", None))
        self.descriptionEdit.setHtml(QCoreApplication.translate("viewMaterial", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Poppins,Arial,sans-serif'; font-size:16px; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14px;\">Please ensure that the task is completed according to the requirements provided, keeping everything consistent and aligned throughout the process. Make sure to follow the necessary steps as outlined, review your work before finalizing, and confirm that it meets the expected standards. Always double-check that the format is correct, the details are accurate, and the output follows the general guidelines. Be mindful of maintaining a clear structure, avoid unnecessary errors, and ensure that the submission is prope"
                        "rly prepared before turning it in.</span></p></body></html>", None))
        self.attachmentName.setText(QCoreApplication.translate("viewMaterial", u"Desktop project guidelines", None))
        self.attachmentType.setText(QCoreApplication.translate("viewMaterial", u"PDF", None))
        self.label.setText(QCoreApplication.translate("viewMaterial", u"C", None))
        self.commentBox.setHtml(QCoreApplication.translate("viewMaterial", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Poppins,Arial,sans-serif'; font-size:14px; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Add a comment...</span></p></body></html>", None))
        self.pushButton.setText(QCoreApplication.translate("viewMaterial", u"Send", None))
    # retranslateUi

