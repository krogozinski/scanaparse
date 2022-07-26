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

class I2cEventType(Enum):
    NONE = 0
    START = 1
    STOP = 2
    RESTART = 3
    ACK = 4
    NACK = 5
    READ = 6
    WRITE = 7
    DATA = 8

class I2cEvent():
    def __init__(self, type = I2cEventType.NONE, data = []):
        self.data = []
        self.type = type
        self.data.append(data)


class I2cEventParser():
    _start_pattern = re.compile(r'^START')
    _stop_pattern = re.compile(r'^STOP')
    _read_pattern = re.compile(r'^Read from 0x([0-9A-Fa-f]+) - R/W = 1')
    _write_pattern = re.compile(r'^Write to 0x([0-9A-Fa-f]+) - R/W = 0')
    _ack_pattern = re.compile(r'^ACK')
    _nack_pattern = re.compile(r'^NACK')
    _data_pattern = re.compile(r'^DATA = 0x([0-9A-Fa-f]+)')

    event_pattern = {
        I2cEventType.START: _start_pattern,
        I2cEventType.STOP: _stop_pattern,
        I2cEventType.ACK: _ack_pattern,
        I2cEventType.NACK: _nack_pattern,
        I2cEventType.READ: _read_pattern,
        I2cEventType.WRITE: _write_pattern,
        I2cEventType.DATA: _data_pattern
        }

    def __init__(self, log_event = []):
        if log_event:
            return self.parse(log_event)

    def parse(self, log_event):
        event_type = I2cEventType.NONE
        for e in self.event_pattern.keys():
            pattern = self.event_pattern[e]
            match = re.search(pattern, log_event[IDX_I2C_EVENT])
            if (match):
                event_type = e
                if (self._event_has_data(e)):
                    data = self._parse_data(match.group(1))
                else:
                    data = []
                break
        return I2cEvent(event_type, data)

    def _parse_data(self, data):
        return int(data, 16)

    def _event_has_data(self, event):
        return (self.event_pattern[event].groups > 0)

class I2cMsgType(Enum):
    INVALID = 0
    READ = 1
    WRITE = 2

class I2cAck(Enum):
    NACK = 0
    ACK = 1

class I2cMsg():
    _STATE_INVALID = -1
    _STATE_START = 0
    _STATE_ADDR = 1
    _STATE_ADDR_ACK = 2
    _STATE_DATA = 3
    _STATE_DATA_ACK = 4
    _STATE_STOP_RESTART = 5

    def __init__(self, events = []):
        self.init(events)

    def init(self, events):
        self.addr = 0xFF
        self.type = I2cMsgType.INVALID
        self.data = []
        self.tgt_ack = I2cAck.NACK

        if ((len(events) != 0) and
            (self._events_are_valid_msg(events))):
            self._deserialize(events)
    
    def _events_are_valid_msg(self, events):
        valid = True
        if ((events[0].type != I2cEventType.START) or
            ((events[-1].type != I2cEventType.STOP) and
             (events[-1].type != I2cEventType.RESTART))):
             valid = False
        
        for i in range(1,len(events)-1):
            if ((events[i].type == I2cEventType.START) or
                (events[i].type == I2cEventType.STOP) or
                (events[i].type == I2cEventType.RESTART)):
                 valid = False
        return valid

    def type(self, events):
        
        msg_type = I2cMsgType.INVALID
        if (self._events_are_valid(events) == False):
            return msg_type
        for e in events:
            if e == I2cEventType.READ:
                msg_type = I2cMsgType.READ
                break

    def _deserialize(self, events):
        state = self._STATE_START

        for e in events:
            if (state == self._STATE_START):
                if (e.type != I2cEventType.START):
                    self.type = I2cMsgType.INVALID
                    break
                else:
                    state = self._STATE_ADDR
            elif (state == self._STATE_ADDR):
                if ((e.type != I2cEventType.READ) and
                    (e.type != I2cEventType.WRITE)):
                    self.type = I2cMsgType.INVALID
                    break
                if (e.type == I2cEventType.READ):
                    self.type = I2cMsgType.READ
                else:
                    self.type = I2cMsgType.WRITE
                state = self._STATE_ADDR_ACK
                self.addr = e.data[0]
            elif (state == self._STATE_ADDR_ACK):
                if ((e.type != I2cEventType.ACK) and
                    (e.type != I2cEventType.NACK)):
                    self.type = I2cMsgType.INVALID
                    break
                if (e.type == I2cEventType.ACK):
                    self.tgt_ack = I2cAck.ACK
                else:
                    self.tgt_ack = I2cAck.NACK
                state = self._STATE_DATA
            elif (state == self._STATE_DATA):
                if (e.type == I2cEventType.STOP):
                    break
                if (e.type != I2cEventType.DATA):
                    self.type = I2cMsgType.INVALID
                    break
                self.data.append(e.data[0])
                state = self._STATE_DATA_ACK
            elif (state == self._STATE_DATA_ACK):
                if ((e.type != I2cEventType.ACK) and 
                    (e.type != I2cEventType.NACK)):
                    self.type = I2cMsgType.INVALID
                    break
                if ((self.type == I2cMsgType.WRITE) and
                    (e.type == I2cEventType.ACK)):
                    self.tgt_ack = I2cAck.ACK
                state = self._STATE_DATA
            elif (state == self._STATE_STOP):
                break
            else:
                break


class I2cStream():

    def __init__(self, events = []):
        self._events = events
        self._msgs =[]
        self._start_idx = -1
        self._end_idx = -1
        if self._events:
            self._msgs = self._find_msgs()
        
    def append(self, events):
        self._events.append(events)
        self._msgs = self._find_msgs()

    def clear(self):
        self._events.clear()
        self._msgs.clear()
        self._start_idx = -1
        self._end_idx = -1
    
    def _find_msgs(self):
        msgs = []
        for i in range(len(self._events)):
            e = self._events[i]
            if e.type == I2cEventType.START:
                self._start_idx = i
            if e.type == I2cEventType.STOP:
                self._end_idx = i
                if (self._start_idx >= 0 and (self._end_idx > self._start_idx)):
                    msgs.append(self._events[self._start_idx:self._end_idx+1])
        return msgs

    def msgs(self):
        return self._msgs

    def num_events(self):
        return len(self._events)

    def num_msgs(self):
        return len(self._msgs)
        