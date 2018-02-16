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
addr = "00:06:66:DA:08:67"
port = 1

sock.connect((addr,port))

RxThread(sock).start()

while True:
    tx = input('bluetooth> ')
    time.sleep(0.1)
    sock.send(tx)


