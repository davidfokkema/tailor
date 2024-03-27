# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'csv_format_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.3.2
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QButtonGroup, QCheckBox,
    QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLabel, QPlainTextEdit, QRadioButton,
    QSizePolicy, QSpinBox, QVBoxLayout, QWidget)

class Ui_CsvFormatDialog(object):
    def setupUi(self, CsvFormatDialog):
        if not CsvFormatDialog.objectName():
            CsvFormatDialog.setObjectName(u"CsvFormatDialog")
        CsvFormatDialog.resize(655, 414)
        self.verticalLayout_2 = QVBoxLayout(CsvFormatDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.columnDelimiterLabel = QLabel(CsvFormatDialog)
        self.columnDelimiterLabel.setObjectName(u"columnDelimiterLabel")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.columnDelimiterLabel)

        self.delimiter_box = QComboBox(CsvFormatDialog)
        self.delimiter_box.setObjectName(u"delimiter_box")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.delimiter_box)

        self.numberFormatLabel = QLabel(CsvFormatDialog)
        self.numberFormatLabel.setObjectName(u"numberFormatLabel")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.numberFormatLabel)

        self.num_format_box = QComboBox(CsvFormatDialog)
        self.num_format_box.setObjectName(u"num_format_box")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.num_format_box)

        self.useColumnHeaderLabel = QLabel(CsvFormatDialog)
        self.useColumnHeaderLabel.setObjectName(u"useColumnHeaderLabel")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.useColumnHeaderLabel)

        self.use_header_box = QCheckBox(CsvFormatDialog)
        self.use_header_box.setObjectName(u"use_header_box")
        self.use_header_box.setChecked(True)

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.use_header_box)

        self.headerRowLabel = QLabel(CsvFormatDialog)
        self.headerRowLabel.setObjectName(u"headerRowLabel")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.headerRowLabel)

        self.header_row_box = QSpinBox(CsvFormatDialog)
        self.header_row_box.setObjectName(u"header_row_box")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.header_row_box)


        self.verticalLayout.addLayout(self.formLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(CsvFormatDialog)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.preview_csv_button = QRadioButton(CsvFormatDialog)
        self.preview_choice = QButtonGroup(CsvFormatDialog)
        self.preview_choice.setObjectName(u"preview_choice")
        self.preview_choice.addButton(self.preview_csv_button)
        self.preview_csv_button.setObjectName(u"preview_csv_button")
        self.preview_csv_button.setChecked(True)

        self.horizontalLayout.addWidget(self.preview_csv_button)

        self.preview_text_button = QRadioButton(CsvFormatDialog)
        self.preview_choice.addButton(self.preview_text_button)
        self.preview_text_button.setObjectName(u"preview_text_button")

        self.horizontalLayout.addWidget(self.preview_text_button)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.preview_box = QPlainTextEdit(CsvFormatDialog)
        self.preview_box.setObjectName(u"preview_box")
        font = QFont()
        font.setFamilies([u"Courier New"])
        self.preview_box.setFont(font)
        self.preview_box.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.preview_box.setReadOnly(True)

        self.verticalLayout.addWidget(self.preview_box)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.buttonBox = QDialogButtonBox(CsvFormatDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout_2.addWidget(self.buttonBox)


        self.retranslateUi(CsvFormatDialog)
        self.buttonBox.accepted.connect(CsvFormatDialog.accept)
        self.buttonBox.rejected.connect(CsvFormatDialog.reject)

        QMetaObject.connectSlotsByName(CsvFormatDialog)
    # setupUi

    def retranslateUi(self, CsvFormatDialog):
        CsvFormatDialog.setWindowTitle(QCoreApplication.translate("CsvFormatDialog", u"Dialog", None))
        self.columnDelimiterLabel.setText(QCoreApplication.translate("CsvFormatDialog", u"Column delimiter:", None))
        self.numberFormatLabel.setText(QCoreApplication.translate("CsvFormatDialog", u"Number format:", None))
        self.useColumnHeaderLabel.setText(QCoreApplication.translate("CsvFormatDialog", u"Use column header:", None))
        self.headerRowLabel.setText(QCoreApplication.translate("CsvFormatDialog", u"Header row / number of rows to skip:", None))
        self.label.setText(QCoreApplication.translate("CsvFormatDialog", u"Preview:", None))
        self.preview_csv_button.setText(QCoreApplication.translate("CsvFormatDialog", u"CSV import", None))
        self.preview_text_button.setText(QCoreApplication.translate("CsvFormatDialog", u"Plain text", None))
    # retranslateUi

