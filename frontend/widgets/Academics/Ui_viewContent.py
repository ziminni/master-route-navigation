from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_viewContent(object):
    def setupUi(self, viewContent, content_type="material"):
        viewContent.setObjectName("viewContent")
        viewContent.resize(747, 452)
        viewContent.setMinimumSize(QtCore.QSize(200, 300))
        viewContent.setStyleSheet("QWidget { background-color: white; font-family: \"Poppins\", Arial, sans-serif; }")
        
        # Top-level layout for viewContent
        main_layout = QtWidgets.QVBoxLayout(viewContent)
        main_layout.setObjectName("main_layout")
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create QScrollArea
        scroll_area = QtWidgets.QScrollArea(parent=viewContent)
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: white; }
            QScrollBar:vertical {
                border: none;
                background: #f8f9fa;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #084924;
                border-radius: 5px;
            }
        """)
        
        # Create content widget for scroll area
        scroll_content = QtWidgets.QWidget()
        scroll_content.setObjectName("scrollAreaWidgetContents")
        scroll_content.setStyleSheet("QWidget { background-color: white; }")
        
        # Move original verticalLayout_2 to scroll content
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(scroll_content)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout_2.setSpacing(8)
        
        # Header
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.headerLayout = QtWidgets.QHBoxLayout()
        self.headerLayout.setObjectName("headerLayout")
        self.backButton = QtWidgets.QPushButton(parent=scroll_content)
        self.backButton.setStyleSheet("border: none; background: transparent; padding: 5px;")
        self.backButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("frontend\\ui\\Classroom\\../../assets/icons/back2.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.backButton.setIcon(icon)
        self.backButton.setIconSize(QtCore.QSize(50, 50))
        self.backButton.setObjectName("backButton")
        self.headerLayout.addWidget(self.backButton)
        
        self.titleMetaLayout = QtWidgets.QVBoxLayout()
        self.titleMetaLayout.setObjectName("titleMetaLayout")
        self.title_label = QtWidgets.QLabel(parent=scroll_content)
        self.title_label.setStyleSheet("font-size: 54px; font-weight: 400; color: #333; margin-bottom: 10px;")
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("title_label")
        self.titleMetaLayout.addWidget(self.title_label)
        
        self.metaLayout = QtWidgets.QHBoxLayout()
        self.metaLayout.setObjectName("metaLayout")
        self.instructor_label = QtWidgets.QLabel(parent=scroll_content)
        self.instructor_label.setStyleSheet("font-size: 20px; color: #24292f; margin-left: 10px;")
        self.instructor_label.setObjectName("instructor_label")
        self.metaLayout.addWidget(self.instructor_label)
        self.date_label = QtWidgets.QLabel(parent=scroll_content)
        self.date_label.setStyleSheet("font-size: 20px; color: #656d76; padding-left: 5px;")
        self.date_label.setObjectName("date_label")
        self.metaLayout.addWidget(self.date_label)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.metaLayout.addItem(spacerItem)
        self.titleMetaLayout.addLayout(self.metaLayout)
        self.headerLayout.addLayout(self.titleMetaLayout)
        
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.headerLayout.addItem(spacerItem1)
        self.menuButton = QtWidgets.QPushButton(parent=scroll_content)
        self.menuButton.setMaximumSize(QtCore.QSize(40, 40))
        self.menuButton.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #6c757d; font-size: 40px; font-weight: bold; border-radius: 20px; }"
            "QPushButton:hover { background-color: #f8f9fa; color: #495057; }"
            "QPushButton:pressed { background-color: #e9ecef; }"
        )
        self.menuButton.setObjectName("menuButton")
        self.headerLayout.addWidget(self.menuButton)
        self.verticalLayout.addLayout(self.headerLayout)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        
        # Score label (only for assessments)
        self.scoreLayout = QtWidgets.QHBoxLayout()
        self.scoreLayout.setContentsMargins(80, 10, -1, 10)
        self.scoreLayout.setObjectName("scoreLayout")
        self.score_label = QtWidgets.QLabel(parent=scroll_content)
        self.score_label.setStyleSheet("font-size: 18px; font-weight: 400; color: #084924; margin-bottom: 10px;")
        self.score_label.setObjectName("score_label")
        if content_type == "assessment":
            self.scoreLayout.addWidget(self.score_label)
        self.verticalLayout_2.addLayout(self.scoreLayout)
        
        # Description
        self.descriptionEdit = QtWidgets.QTextEdit(parent=scroll_content)
        self.descriptionEdit.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        self.descriptionEdit.setMinimumSize(QtCore.QSize(200, 0))
        self.descriptionEdit.setMaximumSize(QtCore.QSize(16777215, 100))  # Limit height to ~3-5 lines
        self.descriptionEdit.setStyleSheet("""
            font-size: 16px;
            color: #000000;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-left: 80px;
            margin-bottom: 8px;
        """)
        self.descriptionEdit.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.WidgetWidth)
        self.descriptionEdit.setLineWrapColumnOrWidth(0)
        self.descriptionEdit.setReadOnly(True)
        self.descriptionEdit.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.descriptionEdit.setObjectName("descriptionEdit")
        self.verticalLayout_2.addWidget(self.descriptionEdit)
        
        # Attachment
        self.attachementLayout = QtWidgets.QHBoxLayout()
        self.attachementLayout.setContentsMargins(80, 10, -1, 10)
        self.attachementLayout.setSpacing(10)
        self.attachementLayout.setObjectName("attachementLayout")
        self.attachmentFrame = QtWidgets.QFrame(parent=scroll_content)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred)
        self.attachmentFrame.setSizePolicy(sizePolicy)
        self.attachmentFrame.setMinimumSize(QtCore.QSize(300, 76))
        self.attachmentFrame.setMaximumSize(QtCore.QSize(400, 76))
        self.attachmentFrame.setMouseTracking(True)
        self.attachmentFrame.setStyleSheet("QFrame #attachmentFrame { background-color: white; border: 1px solid #ddd; border-radius: 10px; padding: 5px;}")
        self.attachmentFrame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.attachmentFrame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.attachmentFrame.setObjectName("attachmentFrame")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.attachmentFrame)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.attachmentInnerLayout = QtWidgets.QVBoxLayout()
        self.attachmentInnerLayout.setObjectName("attachmentInnerLayout")
        self.attachmentName = QtWidgets.QLabel(parent=self.attachmentFrame)
        self.attachmentName.setStyleSheet("font-size: 16px; color: #24292f; text-align: center; text-decoration: underline;")
        self.attachmentName.setObjectName("attachmentName")
        self.attachmentInnerLayout.addWidget(self.attachmentName)
        self.attachmentType = QtWidgets.QLabel(parent=self.attachmentFrame)
        self.attachmentType.setStyleSheet("font-size: 14px; color: #656d76; text-align: center;")
        self.attachmentType.setObjectName("attachmentType")
        self.attachmentInnerLayout.addWidget(self.attachmentType)
        self.verticalLayout_7.addLayout(self.attachmentInnerLayout)
        self.attachementLayout.addWidget(self.attachmentFrame)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.attachementLayout.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.attachementLayout)
        
        # Comments
        self.commentLayout = QtWidgets.QHBoxLayout()
        self.commentLayout.setObjectName("commentLayout")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Minimum)
        self.commentLayout.addItem(spacerItem3)
        self.label = QtWidgets.QLabel(parent=scroll_content)
        self.label.setMaximumSize(QtCore.QSize(38, 38))
        self.label.setStyleSheet("background-color: #084924; border-radius: 19px; color: white; min-width: 38px; min-height: 38px; text-align: center; line-height: 38px;")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.commentLayout.addWidget(self.label)
        self.commentBox = QtWidgets.QTextEdit(parent=scroll_content)
        self.commentBox.setMinimumSize(QtCore.QSize(200, 20))
        self.commentBox.setMaximumSize(QtCore.QSize(16777215, 50))
        self.commentBox.setStyleSheet("""
            font-size: 14px; 
            color: #24292f; 
            padding: 5px; 
            border: 1px solid #ddd; 
            border-radius: 16.5px;
            background-color: #f8f9fa;
        """)
        self.commentBox.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.commentBox.setObjectName("commentBox")
        self.commentLayout.addWidget(self.commentBox)
        
        # UPDATED: Proper Send Button
        self.sendButton = QtWidgets.QPushButton(parent=scroll_content)
        self.sendButton.setMinimumSize(QtCore.QSize(80, 38))
        self.sendButton.setMaximumSize(QtCore.QSize(80, 38))
        self.sendButton.setStyleSheet("""
            QPushButton {
                background-color: #084924;
                color: white;
                border: none;
                border-radius: 19px;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0a5c2e;
            }
            QPushButton:pressed {
                background-color: #06381c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.sendButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.sendButton.setObjectName("sendButton")
        self.commentLayout.addWidget(self.sendButton)
        
        self.verticalLayout_2.addLayout(self.commentLayout)
        
        spacerItem4 = QtWidgets.QSpacerItem(20, 60, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_2.addItem(spacerItem4)
        
        # Set scroll content as the scroll area's widget
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.retranslateUi(viewContent)
        QtCore.QMetaObject.connectSlotsByName(viewContent)

    def retranslateUi(self, viewContent):
        _translate = QtCore.QCoreApplication.translate
        viewContent.setWindowTitle(_translate("viewContent", "content details"))
        self.title_label.setText(_translate("viewContent", "Desktop Project Guidelines"))
        self.instructor_label.setText(_translate("viewContent", "Carlos Fidel Castro"))
        self.date_label.setText(_translate("viewContent", "• August 18, 2025"))
        self.menuButton.setText(_translate("viewContent", "⋮"))
        self.score_label.setText(_translate("viewContent", "10 points"))
        self.descriptionEdit.setHtml(_translate("viewContent", "<p>Please ensure the task is completed as required...</p>"))
        self.attachmentName.setText(_translate("viewContent", "Desktop project guidelines"))
        self.attachmentType.setText(_translate("viewContent", "PDF"))
        self.label.setText(_translate("viewContent", "C"))
        self.commentBox.setHtml(_translate("viewContent", "<p style='font-size:8pt;'>Add a comment...</p>"))
        self.sendButton.setText(_translate("viewContent", "Send"))  # UPDATED: Set send button text


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    viewContent = QtWidgets.QWidget()
    ui = Ui_viewContent()
    ui.setupUi(viewContent, content_type="material")
    viewContent.show()
    sys.exit(app.exec())