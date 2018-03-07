import bluetooth
import threading
import time

class RxThread(threading.Thread):
    def __init__(self, sock):
        self.sock = sock
        threading.Thread.__init__(self)

    def run(self):
        while True:
            rx = sock.recv(1024)
            if not(rx==""):
                print(rx)

sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
addr = "DC:44:B6:93:4A:3F"
port = 1

sock.connect((addr,port))

RxThread(sock).start()

while True:
    tx = input('bluetooth> ')
    sock.send(tx)
    time.sleep(.5)


