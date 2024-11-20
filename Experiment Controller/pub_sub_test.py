import time
import zmq


ctx = zmq.Context()
soc = ctx.socket(zmq.PUB)
soc.setsockopt(zmq.LINGER, 1)
soc.bind("tcp://*:7788")
print("connected")

while True:
    soc.send_string("TEST:hello")
    # print ("sent: 'hello'")
    # time.sleep(2)

