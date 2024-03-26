# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'multiplot_tab.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget

class Ui_MultiPlotTab(object):
    def setupUi(self, MultiPlotTab):
        if not MultiPlotTab.objectName():
            MultiPlotTab.setObjectName(u"MultiPlotTab")
        MultiPlotTab.resize(1000, 600)
        self.horizontalLayout = QHBoxLayout(MultiPlotTab)
#ifndef Q_OS_MAC
        self.horizontalLayout.setSpacing(-1)
#endif
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout_5 = QVBoxLayout()
#ifndef Q_OS_MAC
        self.verticalLayout_5.setSpacing(-1)
#endif
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.plot_widget = PlotWidget(MultiPlotTab)
        self.plot_widget.setObjectName(u"plot_widget")

        self.verticalLayout_5.addWidget(self.plot_widget)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.groupBox_2 = QGroupBox(MultiPlotTab)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout = QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(4, 4, 4, 4)
        self.x_max = QLineEdit(self.groupBox_2)
        self.x_max.setObjectName(u"x_max")
        self.x_max.setMaximumSize(QSize(50, 16777215))

        self.gridLayout.addWidget(self.x_max, 0, 5, 1, 1)

        self.ylabel = QLineEdit(self.groupBox_2)
        self.ylabel.setObjectName(u"ylabel")

        self.gridLayout.addWidget(self.ylabel, 1, 1, 1, 1)

        self.xlabel = QLineEdit(self.groupBox_2)
        self.xlabel.setObjectName(u"xlabel")

        self.gridLayout.addWidget(self.xlabel, 0, 1, 1, 1)

        self.x_min = QLineEdit(self.groupBox_2)
        self.x_min.setObjectName(u"x_min")
        self.x_min.setMaximumSize(QSize(50, 16777215))

        self.gridLayout.addWidget(self.x_min, 0, 3, 1, 1)

        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 0, 4, 1, 1)

        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.label_3 = QLabel(self.groupBox_2)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 0, 2, 1, 1)

        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout.addWidget(self.label_6, 1, 4, 1, 1)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.y_max = QLineEdit(self.groupBox_2)
        self.y_max.setObjectName(u"y_max")
        self.y_max.setMaximumSize(QSize(50, 16777215))

        self.gridLayout.addWidget(self.y_max, 1, 5, 1, 1)

        self.label_4 = QLabel(self.groupBox_2)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 1, 2, 1, 1)

        self.y_min = QLineEdit(self.groupBox_2)
        self.y_min.setObjectName(u"y_min")
        self.y_min.setMaximumSize(QSize(50, 16777215))

        self.gridLayout.addWidget(self.y_min, 1, 3, 1, 1)


        self.horizontalLayout_2.addWidget(self.groupBox_2)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.set_limits_button = QPushButton(MultiPlotTab)
        self.set_limits_button.setObjectName(u"set_limits_button")

        self.verticalLayout_6.addWidget(self.set_limits_button)


        self.horizontalLayout_2.addLayout(self.verticalLayout_6)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)


        self.horizontalLayout.addLayout(self.verticalLayout_5)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.groupBox = QGroupBox(MultiPlotTab)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(self.groupBox)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.plot_selection = QWidget()
        self.plot_selection.setObjectName(u"plot_selection")
        self.plot_selection.setGeometry(QRect(0, 0, 94, 565))
        self.scrollArea.setWidget(self.plot_selection)

        self.verticalLayout.addWidget(self.scrollArea)


        self.verticalLayout_2.addWidget(self.groupBox)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.horizontalLayout.setStretch(0, 1)
        QWidget.setTabOrder(self.xlabel, self.x_min)
        QWidget.setTabOrder(self.x_min, self.x_max)
        QWidget.setTabOrder(self.x_max, self.ylabel)
        QWidget.setTabOrder(self.ylabel, self.y_min)
        QWidget.setTabOrder(self.y_min, self.y_max)

        self.retranslateUi(MultiPlotTab)

        QMetaObject.connectSlotsByName(MultiPlotTab)
    # setupUi

    def retranslateUi(self, MultiPlotTab):
        MultiPlotTab.setWindowTitle(QCoreApplication.translate("MultiPlotTab", u"Plot Tab", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MultiPlotTab", u"Axis settings", None))
        self.label_5.setText(QCoreApplication.translate("MultiPlotTab", u"Max:", None))
        self.label_2.setText(QCoreApplication.translate("MultiPlotTab", u"Y \u2014", None))
        self.label_3.setText(QCoreApplication.translate("MultiPlotTab", u"Min:", None))
        self.label_6.setText(QCoreApplication.translate("MultiPlotTab", u"Max:", None))
        self.label.setText(QCoreApplication.translate("MultiPlotTab", u"X \u2014", None))
        self.label_4.setText(QCoreApplication.translate("MultiPlotTab", u"Min:", None))
        self.set_limits_button.setText(QCoreApplication.translate("MultiPlotTab", u"(Re)Set plot limits", None))
        self.groupBox.setTitle(QCoreApplication.translate("MultiPlotTab", u"Plot Selection", None))
    # retranslateUi

