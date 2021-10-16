# coding: utf-8

""" a convenient import of all Qt classes used """

from pyqtgraph import Qt

if Qt.QT_LIB == Qt.PYSIDE6:
    from PySide6.QtCore import QTimer, QSettings, Qt, Signal, QRect, QByteArray, QPoint, QModelIndex
    from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget, QFormLayout, QGroupBox, QSizePolicy, \
        QSpinBox, QLineEdit, QApplication, QLabel, QStyle, QFileDialog, QMainWindow, QVBoxLayout, QTabWidget, \
        QCheckBox, QComboBox, QToolButton, QDialog, QListWidget
    from PySide6.QtGui import QColor, QCloseEvent, QValidator, QPalette, QPaintEvent
elif Qt.QT_LIB == Qt.PYQT5:
    from PyQt5.QtCore import QTimer, QSettings, Qt, pyqtSignal as Signal, QRect, QByteArray, QPoint, QModelIndex
    from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget, QFormLayout, QGroupBox, QSizePolicy, \
        QSpinBox, QLineEdit, QApplication, QLabel, QStyle, QFileDialog, QMainWindow, QVBoxLayout, QTabWidget, \
        QCheckBox, QComboBox, QToolButton, QDialog, QListWidget
    from PyQt5.QtGui import QCloseEvent, QColor, QPaintEvent, QPalette, QValidator
elif Qt.QT_LIB == Qt.PYQT6:
    from PyQt6.QtCore import QTimer, QSettings, Qt, pyqtSignal as Signal, QRect, QByteArray, QPoint, QModelIndex
    from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget, QFormLayout, QGroupBox, QSizePolicy, \
        QSpinBox, QLineEdit, QApplication, QLabel, QStyle, QFileDialog, QMainWindow, QVBoxLayout, QTabWidget, \
        QCheckBox, QComboBox, QToolButton, QDialog, QListWidget
    from PyQt6.QtGui import QCloseEvent, QColor, QPaintEvent, QPalette, QValidator
elif Qt.QT_LIB == Qt.PYSIDE2:
    from PySide2.QtCore import QTimer, Qt, QSettings, Signal, QRect, QByteArray, QPoint, QModelIndex
    from PySide2.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget, QFormLayout, QGroupBox, QSizePolicy, \
        QSpinBox, QLineEdit, QApplication, QLabel, QStyle, QFileDialog, QMainWindow, QVBoxLayout, QTabWidget, \
        QCheckBox, QComboBox, QToolButton, QDialog, QListWidget
    from PySide2.QtGui import QCloseEvent, QColor, QPaintEvent, QPalette, QValidator

    QApplication.exec = QApplication.exec_
else:
    raise ImportError('PySide6, or PyQt5, or PySide2, is required. PyQt6 support is not guaranteed. '
                      f'{Qt.QT_LIB} is not supported at all.')  # in case pg add support for another framework

__all__ = [
    'Qt',
    'QByteArray',
    'QModelIndex',
    'QPoint',
    'QRect',
    'QSettings',
    'QTimer',
    'Signal',

    'QSizePolicy', 'QStyle',
    'QWidget',
    'QTabWidget',
    'QFormLayout', 'QHBoxLayout', 'QVBoxLayout',
    'QGroupBox',
    'QLabel', 'QCheckBox', 'QPushButton', 'QToolButton', 'QLineEdit', 'QSpinBox', 'QComboBox',
    'QListWidget',
    'QDialog', 'QFileDialog',
    'QMainWindow',
    'QApplication',

    'QCloseEvent',
    'QColor',
    'QPaintEvent',
    'QPalette',
    'QValidator'
]
