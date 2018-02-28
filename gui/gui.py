#Sean Flaherty
#ECE 33334 - Robot Swarm Control Program

#imports
import gi #for gtk
import bluetooth #
import threading #for debug console
import time #also for debug console
import csv #for room map
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import cairo #also for room map

#global variables
shape = ''
rxbuf = ''
surface = None
room_table = []

class MyWindow(Gtk.Window):

    def __init__(self,sock):
        global room_table

        with open('room1.csv',newline='') as room: #to create table for room drawing, make an array of tuples with coordinates
            reader = csv.reader(room, delimiter=',', quotechar='|')
            for row in reader:
                room_table = room_table + [(float(row[0]),float(row[1]))]

        print(room_table) #for debugging purposes

        Gtk.Window.__init__(self, title="Simple Notebook Example")
        self.set_border_width(3)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.notebook = Gtk.Notebook() #notebook for tabbed layout
        self.add(self.notebook)

        #Page 1: Swarm Control

        self.page1 = Gtk.Box()
        self.page1.set_border_width(10)

        shape_button = Gtk.Button(label = "Make Shape")
        shape_button.connect("clicked", self.shape_clicked)

        start_button = Gtk.Button(label = "Start")
        #start_button.connect("clicked",self.start_clicked)

        stop_button = Gtk.Button(label = "Emergency Stop")
        stop_button.connect("clicked", self.stop_clicked)

        shape_store = Gtk.ListStore(str)
        shapes = ["Straight Line", "Box", "Stool", "T-beam"]
        for shape in shapes:
            shape_store.append([shape])

        shape_combo = Gtk.ComboBox.new_with_model(shape_store)
        renderer_text = Gtk.CellRendererText()
        shape_combo.pack_start(renderer_text, True)
        shape_combo.add_attribute(renderer_text, "text", 0)
        shape_combo.connect("changed",self.shape_changed)

        vbox.pack_start(shape_combo, False, False, True)
        vbox.pack_start(shape_button, False, False, True)
        vbox.pack_start(start_button, False, False, True)
        vbox.pack_start(stop_button, False, False, True)

        room_map = Gtk.DrawingArea() #clickable area for route determination
        room_map.set_size_request(640,480)
        room_map.connect("draw", self.draw, [1,1,1], room_map)
        #room_map.connect("configure-event", self.configure_event)
        room_map.connect("button-press-event", self.coordinate_clicked)
        room_map.set_events(room_map.get_events() | Gdk.EventMask.BUTTON_PRESS_MASK)

        self.page1.add(vbox)
        self.page1.add(room_map)

        self.notebook.append_page(self.page1, Gtk.Label('Swarm Control'))

        #Page 2: Debug console

        self.page2 = Gtk.Box()
        self.page2.set_border_width(10)
        self.notebook.append_page(self.page2, Gtk.Label('Debug Console'))

        console = Gtk.TextView()
        textbuffer = console.get_buffer()
        textbuffer.set_text("Debug console goes here")
        self.page2.add(console)
        
    def shape_changed(self, combo):
        global shape
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            shape = model[tree_iter][0]
            print(shape)

    def shape_clicked(self, widget):
        global shape
        txchar = ''
        if shape == "Straight Line":
            txchar = 'l'
        elif shape == "Box":
            txchar = 'b'
        elif shape == "Stool":
            txchar = 's'
        elif shape == "T-beam":
            txchar = 't'
        else:
            txchar = 'l' #default shape should be straight line
        print("Character to be sent is: %s", txchar)
        sock.send(txchar)

    def stop_clicked(self, widget):
        print('Character to be sent is: X')
        sock.send('X')

    def draw(self, widget, event, color, da):
        global room_table
        cr = widget.get_property('window').cairo_create()
        cr.rectangle(0,0,640,480)
        cr.set_source_rgb(color[0],color[1],color[2])
        cr.fill()

        cr.rectangle(0,0,640,480)
        cr.set_source_rgb(0,0,0)
        cr.stroke()

        #first tuple in room table is for room scale
        x_scale = 640/room_table[0][0]
        y_scale = 480/room_table[0][1]

        cr.move_to(room_table[1][0]*x_scale,room_table[1][1]*y_scale)
       
        #draws the outline of any room, assuming it is a polygon
        for idx, point in enumerate(room_table[2:]):
            if point == (-1,-1):
                print('new shape at', idx)
                print('cursor at',room_table[idx+3])
                cr.move_to(room_table[idx+3][0]*x_scale,room_table[idx+3][1]*y_scale)
            else:
                cr.line_to(point[0]*x_scale,point[1]*y_scale)
                cr.move_to(point[0]*x_scale,point[1]*y_scale)

        cr.stroke()

        
    def configure_event(self, widget, event): #set up cairo canvas for clickable environment
        global surface
        if surface is not None:
            del surface
            surface = None

        window = widget.get_window()
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        #todo: figure out how to overlay image/map over cairo canvas

        surface = window.create_similar_surface(cairo.CONTENT_COLOR,width,height) #create cairo canvas over drawingarea

        cr = cairo.Context(surface)
        cr.set_source_rgb(1,1,1)
        cr.paint()
    
        del cr

    def coordinate_clicked(self, widget, event): #this method will save the coordinates clicked for route calculation
        if event.button == Gdk.BUTTON_PRIMARY:
            print(event.x, event.y)

class RxThread(threading.Thread):
    def __init__(self,sock):
        self.sock = sock
        threading.Thread.__init__(self)
    def run(self):
        global rxbuf
        while True:
            rx = sock.recv(1024)
            rxbuf += rx

sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
addr = ""
port = 1
dev_mode = True
if not dev_mode:
    sock.connect((port,addr))

win = MyWindow(sock) #pass socket into gtk window for it to use
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
