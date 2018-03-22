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
import numpy as np #for linspaces, creating sample-based map

#global variables
shape = ''
rxbuf = ''
surface = None
room_table = []
room_sample = np.array([])
wheel_circumference = 0.01 #we can change this value later
x_scale = 0
y_scale = 0
x_size = 0
y_size = 0
start = (0,0)

class MyWindow(Gtk.Window):

    def __init__(self,sock):
        global room_table
        global room_sample
        global rxbuf
        global start

        with open('room1.csv',newline='') as room: #to create table for room drawing, make an array of tuples with coordinates
            reader = csv.reader(room, delimiter=',', quotechar='|')
            for row in reader:
                room_table = room_table + [(float(row[0]),float(row[1]))]

        start = (room_table[1][0],room_table[1][1])

        #now that a table of coordinates is created, we need a way of turning it into a discrete grid
        #we can try this by sampling a large number of points for each line segment
        t = np.linspace(0,1,100) #the number of samples per line segment can be changed
        room_sample = np.array([0,0])

        #room sample:
        for idx,point in enumerate(room_table[2:-1]):
            if (point != (-1,-1)) and (room_table[idx+3] != (-1,-1)):
                point_next = room_table[idx+3]
                x = point[0] + (point_next[0] - point[0])*t
                y = point[1] + (point_next[1] - point[1])*t

                points_to_add = np.vstack((x,y)).T
                room_sample = np.vstack((room_sample,points_to_add))

        room_sample = room_sample[1:] #get rid of the first (0,0) point

        #for point in room_sample[1000:1200]:
        #    print(point)
        #test that points are sampled correctly

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

        self.room_map = Gtk.DrawingArea() #clickable area for route determination
        self.room_map.set_size_request(640,480)
        self.room_map.connect("draw", self.draw, [1,1,1], self.room_map)
        #self.room_map.connect("configure-event", self.configure_event)
        self.room_map.connect("button-press-event", self.coordinate_clicked)
        self.room_map.set_events(self.room_map.get_events() | Gdk.EventMask.BUTTON_PRESS_MASK)

        self.page1.add(vbox)
        self.page1.add(self.room_map)

        self.notebook.append_page(self.page1, Gtk.Label('Swarm Control'))

        #Page 2: Debug console

        self.page2 = Gtk.Box()
        self.page2.set_border_width(10)
        self.notebook.append_page(self.page2, Gtk.Label('Debug Console'))

        vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        entry = Gtk.Entry()
        entry.connect("activate",self.entry_activated)

        self.console = Gtk.TextView()
        self.textbuffer = self.console.get_buffer()
        self.textbuffer.set_text("enter data to send above")

        vbox2.pack_start(entry, False, False, True)
        vbox2.pack_start(self.console, False, False, True)
        self.page2.add(vbox2)
        
    
    def entry_activated(self, widget):
        global rxbuf
        tx = widget.get_text()
        print(tx)
        try:
            sock.send(tx) #if able
        except:
            print('Bluetooth not connected!')
        widget.set_text('')
        self.textbuffer.set_text(rxbuf)

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
        print("Character to be sent is:", txchar)
        sock.send(txchar)

    def stop_clicked(self, widget):
        print('Character to be sent is: X')
        sock.send('X')

    def draw(self, widget, event, color, da):
        global room_table
        global x_size,y_size
        global x_scale, y_scale
        cr = widget.get_property('window').cairo_create()
        cr.rectangle(0,0,640,480)
        cr.set_source_rgb(color[0],color[1],color[2])
        cr.fill()

        cr.rectangle(0,0,640,480)
        cr.set_source_rgb(0,0,0)
        cr.stroke()

        #first tuple in room table is for room scale
        x_size = room_table[0][0]
        y_size = room_table[0][1]
        x_scale = 640/room_table[0][0]
        y_scale = 480/room_table[0][1]




        #draw a square around start
        cr.move_to(start[0]*x_scale-10,start[1]*y_scale-10)
        cr.line_to(start[0]*x_scale+10,start[1]*y_scale+10)
        cr.move_to(start[0]*x_scale+10,start[1]*y_scale-10)
        cr.line_to(start[0]*x_scale-10,start[1]*y_scale+10)
        cr.stroke()

        cr.move_to(room_table[2][0]*x_scale,room_table[2][1]*y_scale)
       
        #draws the outline of any room, assuming it is a polygon
        for idx, point in enumerate(room_table[2:]):
            if point == (-1,-1):
                #print('new shape at', idx)
                #print('cursor at',room_table[idx+4])
                cr.move_to(room_table[idx+4][0]*x_scale,room_table[idx+3][1]*y_scale)
            else:
                cr.line_to(point[0]*x_scale,point[1]*y_scale)
                cr.move_to(point[0]*x_scale,point[1]*y_scale)

        cr.stroke()

    def redraw(self):
        global room_table
        global x_size,y_size
        global x_scale, y_scale
        cr = self.room_map.get_property('window').cairo_create()
        cr.rectangle(0,0,640,480)
        cr.set_source_rgb(1,1,1)
        cr.fill()

        cr.rectangle(0,0,640,480)
        cr.set_source_rgb(0,0,0)
        cr.stroke()

        #first tuple in room table is for room scale
        x_size = room_table[0][0]
        y_size = room_table[0][1]
        x_scale = 640/room_table[0][0]
        y_scale = 480/room_table[0][1]




        #draw a square around start
        cr.move_to(start[0]*x_scale-10,start[1]*y_scale-10)
        cr.line_to(start[0]*x_scale+10,start[1]*y_scale+10)
        cr.move_to(start[0]*x_scale+10,start[1]*y_scale-10)
        cr.line_to(start[0]*x_scale-10,start[1]*y_scale+10)
        cr.stroke()

        cr.move_to(room_table[2][0]*x_scale,room_table[2][1]*y_scale)
       
        #draws the outline of any room, assuming it is a polygon
        for idx, point in enumerate(room_table[2:]):
            if point == (-1,-1):
                #print('new shape at', idx)
                #print('cursor at',room_table[idx+4])
                cr.move_to(room_table[idx+4][0]*x_scale,room_table[idx+3][1]*y_scale)
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
            self.pathfind(event.x,event.y)

    def pathfind(self,x,y): #takes the sampled room grid and uses it for pathfinding
        global wheel_circumference
        global room_sample
        global x_scale,y_scale
        global x_size,y_size
        global start
        
        size = max(x_size,y_size)
        div = wheel_circumference

        while div < size:
            div *= 2
        while div > wheel_circumference: #loop until route is found, increase resolution if not
            x_blocks = np.ceil(x_size/div)
            y_blocks = np.ceil(y_size/div)

            print(x_blocks,y_blocks)

            room_grid = np.zeros((y_blocks,x_blocks))

            for y_iter, row in enumerate(room_grid):
                for x_iter,tile in enumerate(row):
                    x_coords1 = np.where(room_sample[:,0] >= x_iter*div)
                    x_coords2 = np.where(room_sample[:,0] < (x_iter+1)*div)
                    x_coords = np.intersect1d(x_coords1,x_coords2)
                    #print(x_coords)
                    y_coords1 = np.where(room_sample[:,1] >= y_iter*div)
                    y_coords2 = np.where(room_sample[:,1] < (y_iter+1)*div)
                    y_coords = np.intersect1d(y_coords1,y_coords2)
                    #print(y_coords)
                    region = np.intersect1d(x_coords,y_coords)
                    #print(region)
                    if region != np.array([]): 
                        room_grid[y_iter][x_iter] = 1

            padding = np.ones((y_blocks+2,x_blocks+2))
            padding[1:y_blocks+1, 1:x_blocks+1] = room_grid #makes sure the room is closed
            room_grid = padding

            start_idx = (np.floor(start[1]/div)+1,np.floor(start[0]/div)+1)
            print('start: ',start_idx)

            goal_idx = (np.floor(y/(y_scale*div))+1,np.floor(x/(x_scale*div))+1)
            print('goal: ',goal_idx)

            solution = self.solve(room_grid,start_idx,goal_idx)
            if solution is not None:
                self.drawpath(solution,div)
                break

            #print(room_grid)
            div /= 2

    def drawpath(self,solution,div): #now that the path solution has been found, draw it on the map
        global start
        global x_scale,y_scale,x_size,y_size
        self.redraw()
        cr = self.room_map.get_property('window').cairo_create()
        cr.move_to(solution[0][1]*div*x_scale,solution[0][0]*div*y_scale)
        for step in solution[1:]:
            cr.line_to(step[1]*div*x_scale,step[0]*div*y_scale)
            cr.move_to(step[1]*div*x_scale,step[0]*div*y_scale)
        cr.stroke()

    def solve(self,grid,start,goal): #the actual pathfinding algorithm
        print(grid)
        path = np.array([[goal[0],goal[1],0]]) #start at the goal point with counter 0
        ctr = 1 #path counter
        start_in_path = path[path[:,0]==start[0]]
        start_in_path = start_in_path[start_in_path[:,1]==start[1]]
        print('start as array:',np.array(start))
        print('start not in path:',len(start_in_path)==0)
        print('first two cols:',path[:,0:2])
        print('start in path:', start_in_path)
        while len(start_in_path)==0: #sometimes this loop doesn't happen for some reason
            print('loop begin!')
            if len(path[path[:,2]==ctr-1])==0: #quit the loop if no new points were added last iteration
                print('breaking!')
                break
            for cell in path[path[:,2]==ctr-1]: 

                #remove out-of-bounds indices
                print('x-size:',len(grid[0]))
                print('y-size:',len(grid))

                add_to_path = np.array([[cell[0]-1,cell[1],ctr],[cell[0]+1,cell[1],ctr],[cell[0],cell[1]-1,ctr],[cell[0],cell[1]+1,ctr]])
                add_to_path = add_to_path[add_to_path[:,0] >= 0]
                add_to_path = add_to_path[add_to_path[:,1] >= 0]
                add_to_path = add_to_path[add_to_path[:,0] < len(grid[0])]
                add_to_path = add_to_path[add_to_path[:,1] < len(grid)]

                print('cells in bounds:',add_to_path)

                #cut out walls
                without_walls = np.array([[0,0,0]])
                print('verifying without_walls:',without_walls)
                for new_cell in add_to_path:
                    print('potential cell:',new_cell)
                    print('wall value:',grid[new_cell[0]][new_cell[1]])
                    if grid[new_cell[0]][new_cell[1]]==0:
                        print('adding cell!')
                        without_walls = np.vstack((without_walls,new_cell))

                add_to_path = without_walls[1:]
                print('cells without walls:',add_to_path)

                print('points in path:',path[:,0:2])

                #get rid of repeats
                without_repeats = [[0,0,0]]
                for new_cell in add_to_path:
                    print('potential cell:',new_cell)
                    print('repeat:',new_cell[0:2].tolist() in path[:,0:2].tolist())
                    if not (new_cell[0:2].tolist() in path[:,0:2].tolist()):
                        print('cell added!')
                        without_repeats = np.vstack((without_repeats,new_cell))

                add_to_path = without_repeats[1:]

                print('without repeats:',add_to_path)

                if add_to_path != np.array([]):
                    path = np.vstack((path,add_to_path))
                print('counter:',ctr)
                print('new cells:',add_to_path)
                print('path:\n',path)

            start_in_path = path[path[:,0]==start[0]]
            start_in_path = start_in_path[start_in_path[:,1]==start[1]]
            print('start not in path:',len(start_in_path)==0)
            print('start:',start)
            ctr += 1
        if ctr > 3: #make sure path doesn't resolve too soon
            #now that all branches are made, count backwards to get from start to goal
            route = path[path[:,0]==start[0]]
            route = route[route[:,1]==start[1]]
            current_node = route[0]
            while current_node[2]>0:
                up_node = path[path[:,0]==current_node[0]-1]
                up_node = up_node[up_node[:,1]==current_node[1]]
                print('up:',up_node)

                right_node = path[path[:,0]==current_node[0]]
                right_node = right_node[right_node[:,1]==current_node[1]+1]
                print('right:',right_node)

                down_node = path[path[:,0]==current_node[0]+1]
                down_node = down_node[down_node[:,1]==current_node[1]]
                print('down:',down_node)

                left_node = path[path[:,0]==current_node[0]]
                left_node = left_node[left_node[:,1]==current_node[1]-1]
                print('left:',left_node)

                adj_nodes = np.vstack((up_node,right_node,down_node,left_node))
                print('unsorted:',adj_nodes)

                adj_nodes = adj_nodes[adj_nodes[:,2].argsort()]
                print('Adjacent nodes:',adj_nodes)

                current_node = adj_nodes[0] #lowest counter value
                route = np.vstack((route,current_node))
                
            print('route:',route)
            return route

class RxThread(threading.Thread):
    global textbuffer
    def __init__(self,sock):
        self.sock = sock
        self._stop = threading.Event()
        threading.Thread.__init__(self)
    def run(self):
        global rxbuf
        global dev_mode
        while not self.stopped():
            if not dev_mode:
                rx = sock.recv(1024)
                print('received', rx)
                rxbuf += rx
        sock.close()
    def stop(self):
        self._stop.set()
    def stopped(self):
        return self._stop.isSet()

sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
addr = ""
port = 1
dev_mode = True #used for developing program while not connected over bluetooth
if not dev_mode:
    sock.connect((port,addr))

win = MyWindow(sock) #pass socket into gtk window for it to use
win.connect("delete-event", Gtk.main_quit)
win.show_all()
#rxer = RxThread(sock)
#rxer.start()
Gtk.main()
print('exit here')
#rxer.stop()
