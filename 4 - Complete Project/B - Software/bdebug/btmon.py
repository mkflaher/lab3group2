import bluetooth

addr = ""
port = 1

sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.settimeout(0.1) #time allowed for response from server

sock.connect(addr,1)

while True:
    tx = input('bluetooth>')
    sock.send(tx);
    rx = sock.recv(1024)
    print(rx)
