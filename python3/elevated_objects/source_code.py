import inspect
import typing

class Line:
    filename: typing.Union[str, None]
    lineno: typing.Union[int, None]

    def __init__(self):
        frame=inspect.currentframe().f_back
        self.filename = None if frame is None else inspect.getframeinfo(frame).filename
        self.lineno = None if frame is None else inspect.getframeinfo(frame).lineno

    def __str__(self):
        return None if self.filename is None else f"{self.filename}:{self.lineno}"
