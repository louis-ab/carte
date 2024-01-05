import tkinter as tk
from owslib.wms import WebMapService
import threading
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument('--wms', type=str, help='Url du service WMS', default= \
    'https://geoservices.wallonie.be/arcgis/services/IMAGERIE/ORTHO_LAST/MapServer/WmsServer')
parser.add_argument('-w', type=int, help='Larger de la fenêtre', default = 1000)
parser.add_argument('-t', type=int, help='Hauteur de la fenêtre', default = 1000)
parser.add_argument('-x', type=float, help='Longitude', default = 4.56)
parser.add_argument('-y', type=float, help='Latitutde', default = 50.635)
args = parser.parse_args()

wms = WebMapService(args.wms)
w, h = args.w, args.t
zoom = 100
tile_size = 100
pos_x = args.x
pos_y = args.y
moved = [0, 0]
box = [0, 0, w//tile_size, h//tile_size]
im = {}
ims_canv = []
h_compr = 0.64 # ~=cos(50°), pour normaliser les distances

root = tk.Tk()
root.title("Carte")
root.geometry(str(w+2)+'x'+str(h+2))
canvas = tk.Canvas(root,width=w,height=h)
canvas.pack()

def download(i, j, ans):
    data = wms.getmap(layers='0', srs='EPSG:4326', \
                      bbox=(pos_x+i/zoom, pos_y+(h//tile_size-j-1)*h_compr/zoom, \
                            pos_x+(i+1)/zoom, pos_y+(h//tile_size-j)*h_compr/zoom), \
                      size=(tile_size,tile_size), format='image/png')
    ans[(i,j)] = data

def start():
    global im
    threads = []
    ans = {}
    for i in range(int(moved[0]), int(box[2]+moved[0])):
        for j in range(int(moved[1]), int(box[3]+moved[1])):
            if (zoom, i, j) not in im:
                threads.append(threading.Thread(target=download, args=(i, j, ans)))
                threads[-1].start()
    for thread in threads:
        thread.join()
    for i in range(int(moved[0]), int(box[2]+moved[0])):
        for j in range(int(moved[1]), int(box[3]+moved[1])):
            if (zoom, i, j) not in im:
                im[(zoom, i, j)] = tk.PhotoImage(data=ans[(i,j)].read(), format='PNG')
            render(i, j, tile_size//2+i*tile_size, tile_size//2+j*tile_size)

def render(i, j, x, y):
    global ims_canv
    ims_canv.append(canvas.create_image(x, y, image=im[(zoom, i, j)]))

def move(direction):
    global ims_canv
    threads = []
    ans = {}
    if direction == 'left':
        moved[0] -= 0.1
        if moved[0] < box[0]:
            box[0] -= 1
            for j in range(box[1], box[3]):
                if (zoom, box[0], j) not in im:
                    threads.append(threading.Thread(target=download, args=(box[0], j, ans)))
                    threads[-1].start()
            for thread in threads:
                thread.join()
            for j in range(box[1], box[3]):
                if (zoom, box[0], j) not in im:
                    im[(zoom, box[0], j)] = tk.PhotoImage(data=ans[(box[0], j)].read(), format='PNG')
                render(box[0], j, tile_size//2+(box[0]-moved[0]-0.1)*tile_size, tile_size//2+(j-moved[1])*tile_size)
        to_remove = list(filter(lambda x: canvas.coords(x)[0] - moved[0] - tile_size//2 > w, ims_canv))
        ims_canv = [x for x in ims_canv if x not in to_remove]
        if len(to_remove) != 0:
            box[2] -= 1
        for im_canv in to_remove:
            canvas.delete(im_canv)
        for im_canv in ims_canv:
            canvas.move(im_canv, 10, 0)
            
    elif direction == 'right':
        moved[0] += 0.1
        if moved[0]+w//tile_size > box[2]:
            for j in range(box[1], box[3]):
                if (zoom, box[2], j) not in im:
                    threads.append(threading.Thread(target=download, args=(box[2], j, ans)))
                    threads[-1].start()
            for thread in threads:
                thread.join()
            for j in range(box[1], box[3]):
                if (zoom, box[2], j) not in im:
                    im[(zoom, box[2], j)] = tk.PhotoImage(data=ans[(box[2], j)].read(), format='PNG')
                render(box[2], j, tile_size//2+(box[2]-moved[0]+0.1)*tile_size, tile_size//2+(j-moved[1])*tile_size)
            box[2] += 1
        to_remove = list(filter(lambda x: canvas.coords(x)[0] - moved[0] + tile_size//2 < 0, ims_canv))
        ims_canv = [x for x in ims_canv if x not in to_remove]
        if len(to_remove) != 0:
            box[0] += 1
        for im_canv in to_remove:
            canvas.delete(im_canv)
        for im_canv in ims_canv:
            canvas.move(im_canv, -10, 0)
            
    elif direction == 'up':
        moved[1] -= 0.1
        if moved[1] < box[1]:
            box[1] -= 1
            for i in range(box[0], box[2]):
                if (zoom, i, box[1]) not in im:
                    threads.append(threading.Thread(target=download, args=(i, box[1], ans)))
                    threads[-1].start()
            for thread in threads:
                thread.join()
            for i in range(box[0], box[2]):
                if (zoom, i, box[1]) not in im:
                    im[(zoom, i, box[1])] = tk.PhotoImage(data=ans[(i, box[1])].read(), format='PNG')
                render(i, box[1], tile_size//2+(i-moved[0])*tile_size, tile_size//2+(box[1]-moved[1]-0.1)*tile_size)
        to_remove = list(filter(lambda x: canvas.coords(x)[1] - moved[1] - tile_size//2 > h, ims_canv))
        ims_canv = [x for x in ims_canv if x not in to_remove]
        if len(to_remove) != 0:
            box[3] -= 1
        for im_canv in to_remove:
            canvas.delete(im_canv)
        for im_canv in ims_canv:
            canvas.move(im_canv, 0, 10)
            
    elif direction == 'down':
        moved[1] += 0.1
        if moved[1]+h//tile_size > box[3]:
            for i in range(box[0], box[2]):
                if (zoom, i, box[3]) not in im:
                    threads.append(threading.Thread(target=download, args=(i, box[3], ans)))
                    threads[-1].start()
            for thread in threads:
                thread.join()
            for i in range(box[0], box[2]):
                if (zoom, i, box[3]) not in im:
                    im[(zoom, i, box[3])] = tk.PhotoImage(data=ans[(i, box[3])].read(), format='PNG')
                render(i, box[3], tile_size//2+(i-moved[0])*tile_size, tile_size//2+(box[3]-moved[1]+0.1)*tile_size)
            box[3] += 1
        to_remove = list(filter(lambda x: canvas.coords(x)[1] - moved[1] + tile_size//2 < 0, ims_canv))
        ims_canv = [x for x in ims_canv if x not in to_remove]
        if len(to_remove) != 0:
            box[1] += 1
        for im_canv in to_remove:
            canvas.delete(im_canv)
        for im_canv in ims_canv:
            canvas.move(im_canv, 0, -10)

def zoom_change(direction):
    global zoom, moved, pos_x, pos_y, box, im, ims_canv
    if direction == 'in':
        pos_x += moved[0]/zoom + w/(1000*zoom)
        pos_y -= moved[1]*h_compr/zoom - h*h_compr/(1000*zoom)
        zoom *= 1.2
    else:
        pos_x += moved[0]/zoom - w/(1000*zoom)
        pos_y -= moved[1]*h_compr/zoom + h*h_compr/(1000*zoom)
        zoom /= 1.2
    moved = [0, 0]
    box = [0, 0, w//tile_size, h//tile_size]
    im = {}
    ims_canv = []
    start()

def debug(func):
    def wrapper(*args, **kwargs):
        print('Zoom :', zoom)
        print('Position :', pos_x, ',', pos_y)
        print('Déplacement :', moved[0], moved[1])
        print('')
        func(*args, **kwargs)
    return wrapper

@debug
def zoom_change_debug(*args, **kwargs):
    zoom_change(*args, **kwargs)

@debug
def move_debug(*args, **kwargs):
    move(*args, **kwargs)

print("Mouvement : flèches du clavier")
print("Zoom : clic gauche et droit")
print("Débug : Ctrl+flèche, Ctrl+i/Ctrl+o")
print('')
root.bind("<Left>", lambda event: move('left'))
root.bind("<Right>", lambda event: move('right'))
root.bind("<Up>", lambda event: move('up'))
root.bind("<Down>", lambda event: move('down'))
root.bind("<Button-1>", lambda event: zoom_change('in'))
root.bind("<Button-3>", lambda event: zoom_change('out'))
root.bind("<Control-i>", lambda event: zoom_change_debug('in'))
root.bind("<Control-o>", lambda event: zoom_change_debug('out'))
root.bind("<Control-Left>", lambda event: move_debug('left'))
root.bind("<Control-Right>", lambda event: move_debug('right'))
root.bind("<Control-Up>", lambda event: move_debug('up'))
root.bind("<Control-Down>", lambda event: move_debug('down'))

start()
root.mainloop()
