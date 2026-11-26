from datetime import datetime
from enum import Enum


class LogSource(Enum):
    """Источники записей журнала"""
    ENV = "ENV"
    OBJECT = "OBJECT"
    MODULE = "MODULE"
    CENTER = "CENTER"


class LogEntry:
    """Запись журнала"""

    def __init__(self, source, text):
        self.source = source
        self.text = text
        self.timestamp = datetime.now()

    def __str__(self):
        return f"[{self.source.value}] {self.text}"


class LoggingProxy:
    """Простой журнал без внешних зависимостей"""

    def __init__(self, echo=(LogSource.OBJECT, LogSource.CENTER)):
        self._entries = []
        self._echo = set(echo)

    def log(self, source, text):
        if not isinstance(source, LogSource):
            raise ValueError("Неизвестный источник записи: " + str(source))
        entry = LogEntry(source, text)
        self._entries.append(entry)
        if source in self._echo:
            print(" ", entry)
        return entry

    def set_echo(self, source, flag):
        if flag:
            self._echo.add(source)
        else:
            self._echo.discard(source)

    def get_entries(self, source=None):
        if source is None:
            return list(self._entries)
        return [entry for entry in self._entries if entry.source == source]

    def count(self, source=None):
        return len(self.get_entries(source))

    def clear(self):
        self._entries = []
