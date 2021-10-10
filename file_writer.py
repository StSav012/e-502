# coding: utf-8

from __future__ import annotations

from multiprocessing import Process, Queue
from pathlib import Path
from typing import Iterable, Optional, TextIO, Tuple

import numpy as np

from stubs import Literal

FileWritingMode = Literal['w', 'w+', '+w', 'wt', 'tw', 'wt+', 'w+t', '+wt', 'tw+', 't+w', '+tw',
                          'a', 'a+', '+a', 'at', 'ta', 'at+', 'a+t', '+at', 'ta+', 't+a', '+ta',
                          'x', 'x+', '+x', 'xt', 'tx', 'xt+', 'x+t', '+xt', 'tx+', 't+x', '+tx']


class FileWriter(Process):
    def __init__(self, requests_queue: Queue[Tuple[Optional[Path], FileWritingMode, np.ndarray]]):
        super(Process, self).__init__()

        self.requests_queue: Queue[Tuple[Optional[Path], FileWritingMode, np.ndarray]] = requests_queue

    @property
    def done(self) -> bool:
        return self.requests_queue.empty()

    def run(self) -> None:
        file_path: Optional[Path]
        file_mode: FileWritingMode
        x: np.ndarray
        f_out: TextIO

        while True:
            file_path, file_mode, x = self.requests_queue.get(block=True)
            if file_path is None:
                continue
            with file_path.open(file_mode) as f_out:
                f_out.writelines((('\t'.join(f'{xii}' for xii in xi)
                                   if isinstance(xi, Iterable)
                                   else f'{xi}'
                                   ) + '\n')
                                 for xi in x)
