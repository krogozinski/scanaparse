import scanaparse

if __name__ == '__main__':
    i2c_log_file = 'lsm6ds33_fifo_test_01.csv'
    header, log_events = scanaparse.read_log(i2c_log_file)
    evt_parser = scanaparse.I2cEventParser()
    
    events = []

    for le in log_events:
        event = evt_parser.parse(le)
        events.append(event)

    stream = scanaparse.I2cStream(events)
    msgs = stream.msgs()
    print(stream.num_msgs())
    print(stream.num_events())

    # Find all instances of sequence of messages
    # 1. Start
    # 2. Write to address 6B
    # 3. ACK
    # 4. Data 