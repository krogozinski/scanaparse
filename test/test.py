from scanaparse import I2cEventParser, I2cStream, I2cMsg, read_log
from scanaparse import I2cMsgPattern, I2cMsgQuery, I2cMsgType, I2cAck
from scanaparse import MSG_ADDR_ANY, MSG_DATA_ANY

def print_msg(msg, idx):
    print("Message index: {}- address: 0x{:x}".format(idx, msg.addr))
    print("Message index: {}- type: {}".format(idx, msg.type))
    print("Message index: {}- data: {}".format(idx, msg.data))
    print("Message index: {}- target ack status: {}".format(idx, msg.tgt_ack))

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

    # Test query to find a sequence with defined pattern in a list of messages

    pattern_1 = I2cMsgPattern(I2cMsgType.WRITE, addr=0x6b, data=[0x0a], tgt_ack=I2cAck.ACK)
    pattern_2 = I2cMsgPattern(I2cMsgType.READ, addr=MSG_ADDR_ANY, data=[0x06], tgt_ack=I2cAck.ACK)
    idx_msg_start = 0
    idx_msg_end = 3
    test_msgs = [I2cMsg(msgs[idx]) for idx in range(idx_msg_start, idx_msg_end)]
    query_result = I2cMsgQuery.find_sequence([pattern_1, pattern_2], test_msgs)
    
    if query_result:
        print("{} sequence match(es) found".format(len(query_result)))
        for idx_result, result in enumerate(query_result):
            print("Sequence no. {}".format(idx_result+1))
            for idx_match, match in enumerate(result):
                idx_msg, msg = match
                print_msg(msg, idx_msg)
    else:
        print("No sequence found")
