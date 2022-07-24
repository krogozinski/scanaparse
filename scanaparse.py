import re
import csv
from enum import Enum

IDX_TIME = 0
IDX_I2C_EVENT = 1

def read_log(file):
    with open(file, encoding='utf_8') as log_file:
        log_reader = csv.reader(log_file, delimiter=';')
        log_raw = []
        for row in log_reader:
            log_raw.append(row)
    header = log_raw[0]
    events = log_raw[1:]

    for event in events:
        event.pop()
    
    return (header, events)

class I2cEvent(Enum):
    NONE = 0
    START = 1
    STOP = 2
    ACK = 3
    NACK = 4
    READ = 5
    WRITE = 6
    DATA = 7


class I2cEventParser():
    _start_pattern = re.compile(r'^START')
    _stop_pattern = re.compile(r'^STOP')
    _read_pattern = re.compile(r'^Read from 0x([0-9A-Fa-f]+) - R/W = 1')
    _write_pattern = re.compile(r'^Write to 0x([0-9A-Fa-f]+) - R/W = 0')
    _ack_pattern = re.compile(r'^ACK')
    _nack_pattern = re.compile(r'^NACK')
    _data_pattern = re.compile(r'^DATA = 0x([0-9A-Fa-f]+)')

    event_pattern = {
        I2cEvent.START: _start_pattern,
        I2cEvent.STOP: _stop_pattern,
        I2cEvent.ACK: _ack_pattern,
        I2cEvent.NACK: _nack_pattern,
        I2cEvent.READ: _read_pattern,
        I2cEvent.WRITE: _write_pattern,
        I2cEvent.DATA: _data_pattern
        }

    def __init__(self, log_event = []):
        if log_event:
            return self.parse(log_event)

    def parse(self, log_event):
        event = I2cEvent.NONE
        for e in self.event_pattern.keys():
            pattern = self.event_pattern[e]
            match = re.search(pattern, log_event[IDX_I2C_EVENT])
            if (match):
                event = e
                if (self._event_has_data(e)):
                    data = self._parse_data(match.group(1))
                else:
                    data = []
                break
        return {'type': event, 'data': data}

    def _parse_data(self, data):
        return int(data, 16)

    def _event_has_data(self, event):
        return (self.event_pattern[event].groups > 0)

class I2cStream():

    def __init__(self, events = []):
        self._events = events
        self._msgs =[]
        if self._events:
            self._msgs = self._find_msgs()
        
    def append(self, events):
        self._events.append(events)
        self._msgs = self._find_msgs()

    def clear(self):
        self._events.clear()
    
    def _find_msgs(self):
        start_idx = -1
        end_idx = -1
        msgs = []
        for i in range(len(self._events)):
            e = self._events[i]
            if e['type'] == I2cEvent.START:
                start_idx = i
            if e['type'] == I2cEvent.STOP:
                end_idx = i
                if (start_idx >= 0 and (end_idx > start_idx)):
                    msgs.append(self._events[start_idx:end_idx+1])
        return msgs

    def msgs(self):
        return self._msgs

    def num_events(self):
        return len(self._events)

    def num_msgs(self):
        return len(self._msgs)