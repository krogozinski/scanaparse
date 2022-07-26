from scanaparse import I2cEventParser, I2cStream, I2cMsg, read_log

if __name__ == '__main__':
    i2c_log_file = './test/lsm6ds33_fifo_test_01.csv'
    header, log_events = read_log(i2c_log_file)
    evt_parser = I2cEventParser()
    
    events = []

    for le in log_events:
        event = evt_parser.parse(le)
        events.append(event)

    stream = I2cStream(events)
    msgs = stream.msgs()
    print("Number of messages: {}".format(stream.num_msgs()))
    print("Number of events: {}".format(stream.num_events()))

    idx_msg = 0
    test_msg = I2cMsg(msgs[idx_msg])

    print("Message {}- address: 0x{:x}".format(idx_msg, test_msg.addr))
    print("Message {}- type: {}".format(idx_msg, test_msg.type))
    print("Message {}- data: {}".format(idx_msg, test_msg.data))
    print("Message {}- target ack status: {}".format(idx_msg, test_msg.tgt_ack))
