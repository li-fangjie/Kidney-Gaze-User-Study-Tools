import time
import zmq

ctx = zmq.Context()
soc = ctx.socket(zmq.REQ)
soc.setsockopt(zmq.LINGER, 1)
soc.connect("tcp://localhost:7788")
print("connected")

while True:
    soc.send_string("hello")
    print ("sent: 'hello'")
    s = soc.recv_string()
    print ( "recv: %s" % s)
