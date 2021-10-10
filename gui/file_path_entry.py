# coding: utf-8

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pathvalidate

from gui.pg_qt import *

__all__ = ['FilePathEntry']


class FilePathEntry(QWidget):
    def __init__(self, initial_file_path: str = '', parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.path: Optional[Path] = None

        self.setLayout(QHBoxLayout())

        self.text: QLineEdit = QLineEdit(self)
        self.text.setText(initial_file_path)
        self.text.textChanged.connect(self.on_text_changed)
        self.layout().addWidget(self.text)

        self.status: QLabel = QLabel(self)
        self.layout().addWidget(self.status)

        self.browse_button: QPushButton = QPushButton('Browse…', self)
        self.browse_button.clicked.connect(self.on_browse_button_clicked)
        self.layout().addWidget(self.browse_button)

        self.layout().setStretch(1, 0)
        self.layout().setStretch(2, 0)

    def on_text_changed(self, text: str) -> None:
        """ display an icon showing whether the entered file name is acceptable """

        self.text.setToolTip(text)

        if not text:
            self.status.clear()
            self.path = None
            return

        path: Path = Path(text).resolve()
        if path.is_dir():
            self.status.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(self.text.height()))
            self.path = None
            return
        if path.exists():
            self.status.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(self.text.height()))
            self.path = path
            return
        try:
            pathvalidate.validate_filepath(path, platform='auto')
        except pathvalidate.error.ValidationError as ex:
            print(ex.description)
            self.status.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(self.text.height()))
            self.path = None
        else:
            self.status.clear()
            self.path = path

    def on_browse_button_clicked(self) -> None:
        new_file_name: str
        new_file_name, _ = QFileDialog.getSaveFileName(
            self, 'Save As...',
            str(self.path or ''),
            'Tab Separated Values (*.tsv)')
        if new_file_name:
            self.text.setText(new_file_name)
