import collections
import tkinter as tk
from tkinter import filedialog, colorchooser
from tkinter import simpledialog, messagebox
# from tkinter import commondialog
import tkinter.ttk as ttk
import PIL
from PIL import Image, ImageTk, ImageColor


class DialogSize(tk.simpledialog.Dialog):
    def __init__(self, parent):
        self.w = None
        self.h=None
        super().__init__(parent, "Image size")

    def body(self, frame):
        self.lbl = tk.Label(frame, text='Width')
        self.lbl.pack()

        self.width = tk.Entry(frame)
        self.width.pack()

        self.lbl = tk.Label(frame, text='Height')
        self.lbl.pack()

        self.height = tk.Entry(frame)
        self.height.pack()
        return frame

    def buttonbox(self):
        self.ok_button = tk.Button(self, text='OK', width=5, command=self.ok_pressed)
        self.ok_button.pack(side="left")
        cancel_button = tk.Button(self, text='Cancel', width=5, command=self.cancel_pressed)
        cancel_button.pack(side="right")
        self.bind("<Return>", lambda event: self.ok_pressed())
        self.bind("<Escape>", lambda event: self.cancel_pressed())

    def ok_pressed(self):
        # print("ok")
        self.w = int(self.width.get())
        self.h = int(self.height.get())
        self.destroy()

    def cancel_pressed(self):
        # print("cancel")
        self.destroy()

class AutoScrollbar(ttk.Scrollbar):
    ''' A scrollbar that hides itself if it's not needed.
        Works only if you use the grid geometry manager '''
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with this widget')

    def place(self, **kw):
        raise tk.TclError('Cannot use place with this widget')

class Paint(tk.Frame):
    class PenForm:
        def __init__(self, diam):
            r, v = divmod(diam - 1, 2)

            form = list()
            self.R = list()
            self.B = list()
            self.RB = list()
            self.RBAll = list()
            # create round
            x = 0
            y = r
            d = 1 - 2 * r
            # last move -1 - horiz, 0 - diag, 1 - vert
            l = 0
            while y >= 0:

                if d < 0 and 2 * (d + y) - 1 < 0:
                    l = -1
                    x += 1
                    d += 2 * x + 1
                    continue
                if d > 0 and 2 * (d - x) - 1 > 0:
                    self.R.append((x, y))
                    self.B.append((y, x))
                    self.R.append((x, -y - v))
                    self.B.append((-y - v, x))
                    self.RBAll.append((x, y))
                    self.RBAll.append((y, x))
                    self.RBAll.append((x, -y - v))
                    self.RBAll.append((-y - v, x))
                    self.RBAll.append((-x-v, y))
                    self.RBAll.append((y, -x-v))
                    self.RBAll.append((-x-v, -y - v))
                    self.RBAll.append((-y - v, -x-v))
                    # if prev move - diag or horiz
                    if l <= 0: self.RB.append((x, y))
                    for xx in range(-x - v, +x + 1):
                        form.append((xx, +y))
                        form.append((xx, -y - v))
                    l = 1
                    y -= 1
                    d += -2 * y + 1
                    continue

                self.R.append((x, y))
                self.B.append((y, x))
                self.R.append((x, -y - v))
                self.B.append((-y - v, x))
                self.RBAll.append((x, y))
                self.RBAll.append((y, x))
                self.RBAll.append((x, -y - v))
                self.RBAll.append((-y - v, x))
                self.RBAll.append((x, y-1))
                self.RBAll.append((y-1, x))
                self.RBAll.append((x, -y+1 - v))
                self.RBAll.append((-y+1 - v, x))
                self.RBAll.append((-x-v, y))
                self.RBAll.append((y, -x-v))
                self.RBAll.append((-x-v, -y - v))
                self.RBAll.append((-y - v, -x-v))
                self.RBAll.append((-x-v, y-1))
                self.RBAll.append((y-1, -x-v))
                self.RBAll.append((-x-v, -y+1 - v))
                self.RBAll.append((-y+1 - v, -x-v))
                if (l <= 0): self.RB.append((x, y))
                for xx in range(-x - v, +x + 1):
                    form.append((xx, +y))
                    form.append((xx, -y - v))
                l = 0
                x += 1
                y -= 1
                d += 2 * (x - y) + 2
            #
            # self.RB = list()
            # self.RB.append(self.R)
            # self.RB.append(self.B)
            self.form = form

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        self.fig_width = 640
        self.fig_height = 480

        # self.image = tk.PhotoImage(width=self.fig_width, height=self.fig_height)

        self.image = Image.new('RGB', (self.fig_width, self.fig_height), color=(255, 255, 255))
        # self.image = Image.open('img.jpg').convert('RGB')
        self.imgcopy = self.image.copy()
        self.x = -1
        self.y = -1

        self.selection = None
        self.selection_move = False
        self.selection_resize = False
        self.selection_resize_border = 3
        self.selection_image = None

        self.brush_size = 10
        self.brush_color = (0,0,0)
        self.brush = self.PenForm(self.brush_size)

        self.modes = {"pen": (self.PointToImage, self.PrepareDraw, self.pen, self.null),
                      "line": (self.PointToImage, self.PrepareDraw, self.line, self.null),
                      "rect": (self.PointToImage, self.PrepareDraw, self.rect, self.null),
                      "ellipse": (self.PointToImage, self.PrepareDraw, self.round, self.null),
                      "fill": (self.PointToImage, self.fill, self.null, self.null),
                      "move": ((lambda x,y: (x,y)), (lambda x,y: self.canvas.scan_mark(x, y)), self.move, self.null),
                      "select": (self.PointToImage, self.select_start, self.select, self.select_end),
                      }
        self.mode = self.modes["pen"]


        self.initUI()
        # self.canvas.create_image((0, 0), image=ImageTk.PhotoImage(self.img2), anchor='nw')
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind("<1>", self.LBdown)
        self.canvas.bind("<B1-Motion>", self.LBmove)
        self.canvas.bind("<ButtonRelease-1>", self.LBup)
        self.canvas.bind('<MouseWheel>', self.wheel)  # with Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.wheel)  # only with Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.wheel)  # only with Linux, wheel scroll up

        h = 21
        r, _ = divmod(h - 1, 2)
        xx0 = r + _
        yy0 = r
        for i in range(1, 22):
            im = Image.new('RGB', (h, h), color=(255, 255, 255))
            # im.putpixel((0,0), (255))
            # im.putpixel((1,1), (255))
            f = self.PenForm(i)
            for x, y in f.form:
                im.putpixel((xx0 + x, yy0 + y), (0, 0, 0))
            for x, y in f.R:
                im.putpixel((xx0 + x, yy0 + y), (255, 0, 0))
            for x, y in f.B:
                im.putpixel((xx0 + x, yy0 + y), (0, 255, 0))
            for x, y in f.RB:
                im.putpixel((xx0 + x, yy0 + y), (0, 0, 255))
            for x, y in f.RBAll:
                im.putpixel((xx0 + x, yy0 + y), (0, 255, 255))

            im.save(f'brush_{i}.png')

        print("done")

    def initUI(self):

        self.parent.title("My Paint")
        self.pack(fill=tk.BOTH, expand=1)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.top_panel = tk.Frame(self)
        self.top_panel.grid(column=0, row=0, sticky='nswe')

        vbar = AutoScrollbar(self, orient='vertical')
        hbar = AutoScrollbar(self, orient='horizontal')
        vbar.grid(row=1, column=1, sticky='ns')
        hbar.grid(row=2, column=0, sticky='we')
        self.canvas = tk.Canvas(self, highlightthickness=0,
                                # width=self.fig_width - 2, height=self.fig_height - 2,
                                bg="#C0C0C0",
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)  # Создаем поле для рисования, устанавливаем белый фон
        self.canvas.grid(column=0, row=1, sticky='nswe')
        self.canvas.update()
        # self.canvas.create_image((0, 0), image=ImageTk.PhotoImage(self.image), anchor='nw')
        vbar.configure(command=self.scroll_y)  # bind scrollbars to the canvas
        hbar.configure(command=self.scroll_x)

        self.width, self.height = self.image.size
        # scale for the canvaas image
        self.imscale = 1.0
        # zoom magnitude
        self.delta = 1.3
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        self.show_image()

        btn = tk.Button(self.top_panel, text="New", width=10, command=self.new_image)
        btn.grid(column=0, row=0, sticky='nswe', padx=5, pady=5)

        color_bar = tk.Frame(self.top_panel)
        color_bar.grid(column=1, row=0, sticky='nswe', padx=5, pady=5)

        colors_list = ["red", "green", "yellow", "blue", "#0FFF00", "#45A5F0", "black", "white"]
        self.color_buttons = list()
        for i in range(len(colors_list)):
            btn = tk.Button(color_bar, bg=colors_list[i],  width=4, command=lambda c=ImageColor.getcolor(colors_list[i], 'RGB'): self.set_color(c))
            btn.bind("<3>", lambda e, b=btn: self.ChangeColorTile(b))
            d, m = divmod(i, 2)
            btn.grid(column=d + 1, row=m)
            self.color_buttons.append(btn)

        bar = tk.Frame(self.top_panel)
        lbl = tk.Label(bar, text="Size")
        lbl.grid(column=0, row=0, sticky='nswe', padx=0, pady=0)
        scale = tk.Scale(bar, from_=1, to_=20, variable=self.brush_size, command=self.set_size, length=100,
                         orient=tk.HORIZONTAL)
        scale.set(self.brush_size)
        scale.grid(column=2, row=0, sticky='nswe', padx=0, pady=0)
        bar.grid(column=2, row=0, sticky='nswe', padx=5, pady=5)

        bar = tk.Frame(self.top_panel)
        i = 0
        for m in self.modes.keys():
            btn = tk.Button(bar, text=m, width=6, command=(lambda c=m: self.set_mode(c)))
            d, m = divmod(i, 2)
            btn.grid(column=d + 1, row=m)
            i += 1
        bar.grid(column=3, row=0, sticky='nswe', padx=5, pady=5)

        btn = tk.Button(self.top_panel, text="Save", width=10, command=self.save)
        btn.grid(column=4, row=0, sticky='nswe', padx=5, pady=5)

        btn = tk.Button(self.top_panel, text="About", width=10, command=self.about)
        btn.grid(column=5, row=0, sticky='nswe', padx=5, pady=5)



    def set_mode(self, m):
        self.mode = self.modes[m]
        # self.image = self.imgcopy.copy()
        # self.show_image()
        print(m)

    def ChangeColorTile(self, btn):
        col = ImageColor.getcolor(btn["bg"], 'RGB')
        color = colorchooser.askcolor(initialcolor=col, parent=self)
        btn.configure(bg = color[1])
        btn["command"] = lambda c=color[0]: self.set_color(c)

    def scroll_y(self, *args, **kwargs):
        ''' Scroll canvas vertically and redraw the image '''
        self.canvas.yview(*args, **kwargs)  # scroll vertically
        self.show_image()  # redraw the image

    def scroll_x(self, *args, **kwargs):
        ''' Scroll canvas horizontally and redraw the image '''
        self.canvas.xview(*args, **kwargs)  # scroll horizontally
        self.show_image()  # redraw the image

    def wheel(self, event):
        ''' Zoom with mouse wheel '''
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        bbox = self.canvas.bbox(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        else: return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down
            i = min(self.width, self.height)
            if int(i * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.delta
            scale        /= self.delta
        if event.num == 4 or event.delta == 120:  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale        *= self.delta
        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.show_image()

    def show_image(self, event=None, img=None):
        ''' Show image on the Canvas '''
        if img == None:
            img = self.image
        bbox1 = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                 self.canvas.canvasy(0),
                 self.canvas.canvasx(self.canvas.winfo_width()),
                 self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),  # get scroll region box
                max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]
        if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:  # whole image in the visible area
            bbox[0] = bbox1[0]
            bbox[2] = bbox1[2]
        if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:  # whole image in the visible area
            bbox[1] = bbox1[1]
            bbox[3] = bbox1[3]
        self.canvas.configure(scrollregion=bbox)  # set scroll region
        x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(bbox2[1] - bbox1[1], 0)
        x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        y2 = min(bbox2[3], bbox1[3]) - bbox1[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            x = min(int(x2 / self.imscale), self.width)   # sometimes it is larger on 1 pixel...
            y = min(int(y2 / self.imscale), self.height)  # ...and sometimes not
            image = img.crop((int(x1 / self.imscale), int(y1 / self.imscale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

    def putpixel(self, x, y):
        if x >= 0 and y >= 0 and x < self.width and y < self.height:
            # self.image.put(self.brush_color, (x, y))
            self.image.putpixel((x, y), self.brush_color)

    def pen(self, cx, cy):
        self.draw_line(self.x, self.y, cx, cy)
        self.x, self.y = cx, cy

    def fill(self, cx, cy):
        source = self.image.getpixel((cx, cy))
        color = self.brush_color
        toFill = set()
        toFill.add((cx,cy))
        while toFill:
            (x,y) = toFill.pop()
            c = self.image.getpixel((x,y))
            if not c == source:
                continue
            self.image.putpixel((x,y), color)
            toFill.add((x-1,y))
            toFill.add((x+1,y))
            toFill.add((x,y-1))
            toFill.add((x,y+1))
        # if source != color:
        #     pixels = collections.deque([(cx, cy)])
        #     while pixels:
        #         place = pixels.popleft()
        #         x, y = place
        #         self.image.putpixel(place, color)
        #         for x_offset in -1, 1:
        #             x_offset += x
        #             for y_offset in -1, 1:
        #                 y_offset += y
        #                 new_place = x_offset, y_offset
        #                 if self.image.getpixel(new_place) == source:
        #                     pixels.append(new_place)

    def line(self, cx, cy):
        self.image = self.imgcopy.copy()
        self.show_image()
        # self.canvas.create_image((0, 0), image=self.image, anchor='nw')
        self.draw_line(self.x, self.y, cx, cy)

    def rect(self, cx, cy):
        self.image = self.imgcopy.copy()
        self.show_image()
        # self.canvas.create_image((0, 0), image=self.image, anchor='nw')
        self.draw_rectangle(self.x, self.y, cx, cy)

    def round(self, cx, cy):
        self.image = self.imgcopy.copy()
        self.show_image()
        # self.canvas.create_image((0, 0), image=self.image, anchor='nw')
        self.draw_ellipse(self.x, self.y, cx, cy)
        # self.draw_round(self.x, self.y, cx, cy)

    def move(self, cx, cy):
        self.canvas.scan_dragto(cx, cy, gain=1)
        self.show_image()  # redraw the image

    def select_start(self, cx, cy):
        # if not selected yet => prepare for drawing
        if self.selection == None:

            self.x, self.y = cx, cy
            self.imgcopy = self.image.copy()
        else:
            # if pointer inside selection (with borders for resizing)  => prepare for dragging
            b = self.selection_resize_border
            if cx>self.selection[0]+b and cx<self.selection[2]-b and cy>self.selection[1]+b and cy<self.selection[3]-b:
                self.selection_move = True
                # save coords of selection relative to pointer
                self.x, self.y = cx - self.selection[0], cy - self.selection[1]
                return
            # if pointer at border => prepare for resize
            # if right border
            if cx>self.selection[2]-b and cx<self.selection[2]+b and cy>self.selection[1]+b and cy<self.selection[3]-b:
                self.selection_resize = "r"
                # save pointer coords
                self.x, self.y = cx, cy
                return
            # if left border
            if cx>self.selection[0]-b and cx<self.selection[0]+b and cy>self.selection[1]+b and cy<self.selection[3]-b:
                self.selection_resize = "l"
                # save pointer coords
                self.x, self.y = cx, cy
                return
            # if top border
            if cx>self.selection[0]+b and cx<self.selection[2]-b and cy>self.selection[1]-b and cy<self.selection[1]+b:
                self.selection_resize = "t"
                # save pointer coords
                self.x, self.y = cx, cy
                return
            # if bottom border
            if cx>self.selection[0]+b and cx<self.selection[2]-b and cy>self.selection[3]-b and cy<self.selection[3]+b:
                self.selection_resize = "b"
                # save pointer coords
                self.x, self.y = cx, cy
                return
            # if right top corner
            if cx>self.selection[2]-b and cx<self.selection[2]+b and cy>self.selection[1]-b and cy<self.selection[1]+b:
                self.selection_resize = "rt"
                # save pointer coords
                self.x, self.y = cx, cy
                return
            # if right bottom corner
            if cx>self.selection[2]-b and cx<self.selection[2]+b and cy>self.selection[3]-b and cy<self.selection[3]+b:
                self.selection_resize = "rb"
                # save pointer coords
                self.x, self.y = cx, cy
                return
            # if left top corner
            if cx>self.selection[0]-b and cx<self.selection[0]+b and cy>self.selection[1]-b and cy<self.selection[1]+b:
                self.selection_resize = "lt"
                # save pointer coords
                self.x, self.y = cx, cy
                return
            # if left bottom corner
            if cx>self.selection[0]-b and cx<self.selection[0]+b and cy>self.selection[3]-b and cy<self.selection[3]+b:
                self.selection_resize = "lb"
                # save pointer coords
                self.x, self.y = cx, cy
                return

            # else reset selection
            self.image = self.imgcopy.copy()
            self.image.paste(self.selection_image,
                             box=(self.selection[0], self.selection[1], self.selection[2], self.selection[3]))
            self.imgcopy = self.image.copy()
            self.selection = None
            self.x, self.y = cx, cy
            self.image = self.imgcopy.copy()

    def select(self, cx, cy):
        if self.selection == None:
            if self.x<0 or self.y<0 or self.x>=self.width or self.y>=self.height:
                return
            self.image = self.imgcopy.copy()
            self.show_image()
            if cx<0:
                cx=0
            if cy<0:
                cy=0
            if cx>=self.width:
                cx=self.width-1
            if cy>=self.height:
                cy=self.height-1
            self.draw_select(self.x, self.y, cx, cy)
            return
        else:
            if self.selection_move:
                self.image = self.imgcopy.copy()
                self.image.paste(self.selection_image,
                                 box=(cx-self.x, cy-self.y, cx-self.x+self.selection[2]-self.selection[0], cy-self.y+self.selection[3]-self.selection[1]))
                return
            if self.selection_resize:
                self.image = self.imgcopy.copy()
                img = self.selection_image.copy()
                w, h = img.size
                if self.selection_resize == "r":
                    img = img.resize((w+cx-self.x,h), Image.ANTIALIAS)
                    self.image.paste(img,
                                     box=(self.selection[0], self.selection[1], self.selection[0]+w+cx-self.x, self.selection[1]+h))
                if self.selection_resize == "l":
                    img = img.resize((w-cx+self.x,h), Image.ANTIALIAS)
                    self.image.paste(img,
                                     box=(self.selection[2]-w+cx-self.x, self.selection[1], self.selection[2], self.selection[1]+h))
                if self.selection_resize == "t":
                    img = img.resize((w,h-cy+self.y), Image.ANTIALIAS)
                    self.image.paste(img,
                                     box=(self.selection[0], self.selection[3]-h+cy-self.y, self.selection[0]+w, self.selection[3]))
                if self.selection_resize == "b":
                    img = img.resize((w,h+cy-self.y), Image.ANTIALIAS)
                    self.image.paste(img,
                                     box=(self.selection[0], self.selection[1], self.selection[0]+w, self.selection[3]+cy-self.y))
                if self.selection_resize == "rt":
                    img = img.resize((w+cx-self.x,h-cy+self.y), Image.ANTIALIAS)
                    self.image.paste(img,
                                     box=(self.selection[0], self.selection[3]-h+cy-self.y, self.selection[0]+w+cx-self.x, self.selection[3]))
                if self.selection_resize == "rb":
                    img = img.resize((w+cx-self.x,h+cy-self.y), Image.ANTIALIAS)
                    self.image.paste(img,
                                     box=(self.selection[0], self.selection[1], self.selection[0]+w+cx-self.x, self.selection[3]+cy-self.y))
                if self.selection_resize == "lt":
                    img = img.resize((w-cx+self.x,h-cy+self.y), Image.ANTIALIAS)
                    self.image.paste(img,
                                     box=(self.selection[2]-w+cx-self.x, self.selection[3]-h+cy-self.y, self.selection[2], self.selection[3]))
                if self.selection_resize == "lb":
                    img = img.resize((w-cx+self.x,h+cy-self.y), Image.ANTIALIAS)
                    self.image.paste(img,
                                     box=(self.selection[2]-w+cx-self.x, self.selection[1], self.selection[2], self.selection[3]+cy-self.y))

    def select_end(self, cx, cy):
        if (self.selection_move):
            # self.imgcopy = self.image.copy()
            self.selection = (cx-self.x, cy-self.y, cx-self.x+self.selection[2]-self.selection[0], cy-self.y+self.selection[3]-self.selection[1])
            self.draw_select(self.selection[0], self.selection[1], self.selection[2], self.selection[3])
            self.selection_move = False
            return
            # self.selection = None

        if (self.selection_resize):
            w, h = self.selection[2]-self.selection[0], self.selection[3]-self.selection[1]
            if self.selection_resize == "r":
                self.selection = (self.selection[0], self.selection[1], self.selection[0]+w+cx-self.x, self.selection[1]+h)
                self.selection_image = self.selection_image.resize((w+cx-self.x,h), Image.ANTIALIAS)
            if self.selection_resize == "l":
                self.selection = (self.selection[2]-w+cx-self.x, self.selection[1], self.selection[2], self.selection[1]+h)
                self.selection_image = self.selection_image.resize((w-cx+self.x,h), Image.ANTIALIAS)
            if self.selection_resize == "t":
                self.selection = (self.selection[0], self.selection[3]-h+cy-self.y, self.selection[0]+w, self.selection[3])
                self.selection_image = self.selection_image.resize((w,h-cy+self.y), Image.ANTIALIAS)
            if self.selection_resize == "b":
                self.selection = (self.selection[0], self.selection[1], self.selection[0]+w, self.selection[3]+cy-self.y)
                self.selection_image = self.selection_image.resize((w,h+cy-self.y), Image.ANTIALIAS)
            if self.selection_resize == "rt":
                self.selection = (self.selection[0], self.selection[3]-h+cy-self.y, self.selection[0]+w+cx-self.x, self.selection[3])
                self.selection_image = self.selection_image.resize((w+cx-self.x,h-cy+self.y), Image.ANTIALIAS)
            if self.selection_resize == "rb":
                self.selection = (self.selection[0], self.selection[1], self.selection[0]+w+cx-self.x, self.selection[3]+cy-self.y)
                self.selection_image = self.selection_image.resize((w+cx-self.x,h+cy-self.y), Image.ANTIALIAS)
            if self.selection_resize == "lt":
                self.selection = (self.selection[2]-w+cx-self.x, self.selection[3]-h+cy-self.y, self.selection[2], self.selection[3])
                self.selection_image = self.selection_image.resize((w-cx+self.x,h-cy+self.y), Image.ANTIALIAS)
            if self.selection_resize == "lb":
                self.selection = (self.selection[2]-w+cx-self.x, self.selection[1], self.selection[2], self.selection[3]+cy-self.y)
                self.selection_image = self.selection_image.resize((w-cx+self.x,h+cy-self.y), Image.ANTIALIAS)

            self.draw_select(self.selection[0], self.selection[1], self.selection[2], self.selection[3])
            self.selection_resize = False
        else:
            if self.x<0 or self.y<0 or self.x>=self.width or self.y>=self.height:
                return
            if cx<0:
                cx=0
            if cy<0:
                cy=0
            if cx>=self.width:
                cx=self.width-1
            if cy>=self.height:
                cy=self.height-1
            x0, x1 = ((self.x, cx) if cx>self.x else (cx, self.x))
            y0, y1 = ((self.y, cy) if cy>self.y else (cy, self.y))
            self.selection = (x0, y0, x1, y1)
            w = self.selection[2]-self.selection[0]
            h = self.selection[3]-self.selection[1]
            self.selection_image = self.imgcopy.crop(self.selection)
            img = Image.new('RGB', (w, h), color=(255,255,255))
            self.imgcopy.paste(img, (self.selection[0],self.selection[1], self.selection[2], self.selection[3]))

    def set_color(self, new_color):
        print(new_color)
        self.brush_color = new_color

    def PointToImage(self, xd, yd):
        bbox1 = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                 self.canvas.canvasy(0),
                 self.canvas.canvasx(self.canvas.winfo_width()),
                 self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = (bbox1[0]-bbox2[0],bbox1[1]-bbox2[1],bbox1[2]-bbox2[2],bbox1[3]-bbox2[3])
        x, y = int((xd-bbox[0])/self.imscale), int((yd-bbox[1])/self.imscale)
        return (x, y)

    def PrepareDraw(self, x, y):
        self.x, self.y = x, y
        self.imgcopy = self.image.copy()

    def LBdown(self, e):
        x, y = e.x, e.y
        x, y = self.mode[0](x,y)
        self.mode[1](x,y)
        self.LBmove(e)

    def LBmove(self, e):
        # self.canvas.create_line((self.x, self.y, e.x, e.y), width=self.brush_size)
        # self.canvas.create_oval(e.x - self.brush_size/2,
        #                       e.y - self.brush_size/2,
        #                       e.x + self.brush_size/2,
        #                       e.y + self.brush_size/2,
        #                       fill=self.brush_color, outline=self.brush_color)
        # self.image.put(self.brush_color, (e.x, e.y))
        x, y = e.x, e.y
        cx, cy = self.mode[0](x,y)
        self.mode[2](cx, cy)
        self.show_image()
        # self.canvas.scale('all', 0, 100, 5, 5)

    def LBup(self, e):
        cx, cy = self.mode[0](e.x, e.y)
        self.mode[3](cx, cy)
        self.show_image()
    #
    # def Ent(self, e):
    #     self.x, self.y = e.x, e.y

    def draw_line(self, x0, y0, x1, y1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        dirx = 1 if x1 - x0 > 0 else -1
        diry = 1 if y1 - y0 > 0 else -1
        brush = self.brush
        # w1, w2 = divmod(self.brush_size, 2)
        # w1, w2 = w1, w1+w2
        e = 0

        # draw start point
        for x, y in self.brush.form:
            self.putpixel(x0 + x * dirx, y0 + y * diry)


        if dx > dy:
            de = dy + 1
            y = y0
            for x in range(x0, x1 + dirx, dirx):
                for xx, yy in brush.R:
                    self.putpixel(x + xx * dirx, y + yy * diry)
                # for yy in range(y-w1, y+w2):
                #     self.putpixel(x, yy)
                e += de
                if e > dx + 1:
                    y += diry
                    for xx, yy in brush.B:
                        self.putpixel(x + xx * dirx, y + yy * diry)
                    e -= (dx + 1)

        else:
            de = dx + 1
            x = x0
            for y in range(y0, y1 + diry, diry):
                for xx, yy in brush.B:
                    self.putpixel(x + xx * dirx, y + yy * diry)
                # for xx in range(x-w1, x+w2):
                #     self.putpixel(xx, y)
                e += de
                if e > dy + 1:
                    x += dirx
                    for xx, yy in brush.R:
                        self.putpixel(x + xx * dirx, y + yy * diry)
                    e -= (dy + 1)


        #
        # for x, y in self.brush.form:
        #     self.image.put(self.brush_color, (x1+x, y1+y))

    def draw_select(self, x0, y0, x1, y1):
        color = ((0,0,0), (255,255,255))
        if x0>x1: x0, x1 = x1, x0
        if y0>y1: y0, y1 = y1, y0
        for x in range(x0, x1+1):
            self.image.putpixel((x, y0), color[x%2])
            self.image.putpixel((x, y1), color[x%2])
        for y in range(y0, y1+1):
            self.image.putpixel((x0, y), color[y%2])
            self.image.putpixel((x1, y), color[y%2])

    def draw_rectangle(self, x0, y0, x1, y1):
        h = self.brush_size
        h1, h2 = divmod(h, 2)
        h1, h2 = h1, h1+h2
        if x0>x1: x0, x1 = x1, x0
        if y0>y1: y0, y1 = y1, y0
        for x in range(x0-h1, x1+h2):
            for yy in range(-h1, h2):
                self.putpixel(x, y0+yy)
                self.putpixel(x, y1+yy)
        for y in range(y0-h1, y1+h2):
            for xx in range(-h1, h2):
                self.putpixel(x0+xx, y)
                self.putpixel(x1+xx, y)

    def draw_round(self, x0, y0, x1, y1):
        diam = min(abs(x1 - x0), abs(y1 - y0))
        r, _ = divmod(diam - 1, 2)
        # xc = (x0 if x1>x0 else x0-diam) + r+_
        # yc = (y0 if y1>y0 else y0-diam) + r
        xc = x0 + (r + _ if x1 > x0 else -r)
        yc = y0 + (r if y1 > y0 else -r - _)
        xcm = xc - _
        ycm = yc - _

        # r1, r2 = divmod(diam-1, 2)
        # r1, r2 = r1, r1+r2
        x = 0
        y = r
        d = 1 - 2 * r
        while y > int(r / 2):
            self.putpixel(xc + x, yc + y)
            self.putpixel(xc + x, ycm - y)
            self.putpixel(xcm - x, yc + y)
            self.putpixel(xcm - x, ycm - y)
            self.putpixel(xc + y, yc + x)
            self.putpixel(xc + y, ycm - x)
            self.putpixel(xcm - y, yc + x)
            self.putpixel(xcm - y, ycm - x)
            e = 2 * (d + y) - 1
            if d < 0 and e <= 0:
                x += 1
                d += 2 * x + 1
                continue
            if d > 0 and e > 0:
                y -= 1
                d -= (2 * y + 1)
                continue
            x += 1
            y -= 1
            d += 2 * (x - y)

    def draw_ellipse(self, x0, y0, x1, y1):
        xc = int((x1 + x0) / 2)
        yc = int((y1 + y0) / 2)
        # rx
        a = abs(x0 - xc)
        # ry
        b = abs(y0 - yc)
        a2 = a * a
        b2 = b * b
        x = 0
        y = b
        d = b2 - 2 * b * a2 + a2
        e = 0

        # draw start point
        for xx, yy in self.brush.form:
            self.putpixel(xc + xx, yc+b + yy)
            self.putpixel(xc + xx, yc-b - yy)
            self.putpixel(xc+a - xx, yc + yy)
            self.putpixel(xc-a - xx, yc - yy)

        while y >= 0:
            if y == 0:
                for xf in range(x, a + 1):
                    for xx, yy in self.brush.R:
                        self.putpixel(xc+xf + xx, yc + yy)
                        self.putpixel(xc-xf - xx, yc + yy)
                    # self.putpixel(xc + xf, yc)
                    # self.putpixel(xc - xf, yc)
                y -= 1
            else:
                # self.putpixel(xc + x, yc + y)
                # self.putpixel(xc + x, yc - y)
                # self.putpixel(xc - x, yc + y)
                # self.putpixel(xc - x, yc - y)
                for xx, yy in self.brush.RBAll:
                    self.putpixel(xc+x + xx, yc+y + yy)
                    self.putpixel(xc-x - xx, yc+y + yy)
                    self.putpixel(xc+x + xx, yc-y - yy)
                    self.putpixel(xc-x - xx, yc-y - yy)
                # for xx, yy in self.brush.form:
                #     self.putpixel(xc+x + xx, yc+y + yy)
                #     self.putpixel(xc+x + xx, yc-y - yy)
                #     self.putpixel(xc-x - xx, yc+y + yy)
                #     self.putpixel(xc-x - xx, yc-y - yy)
                # horizontal or diag
                if d < 0:
                    e = 2 * d + 2 * y * a2 - a2
                    # horizontal
                    if e < 0:
                        x += 1
                        d += 2 * x * b2 + b2
                        # for xx, yy in self.brush.R:
                        #     self.putpixel(xc+x + xx, yc+y + yy)
                        #     self.putpixel(xc-x - xx, yc+y + yy)
                        #     self.putpixel(xc+x + xx, yc-y - yy)
                        #     self.putpixel(xc-x - xx, yc-y - yy)
                        # for xx, yy in self.brush.B:
                        #     self.putpixel(xc+x + xx, yc+y + yy)
                        #     self.putpixel(xc-x - xx, yc+y + yy)
                        #     self.putpixel(xc+x + xx, yc-y - yy)
                        #     self.putpixel(xc-x - xx, yc-y - yy)
                    # diag
                    else:
                        x += 1
                        y -= 1
                        d += (2 * x * b2 + b2 - 2 * y * a2 + a2)
                        # for xx, yy in self.brush.R:
                        #     self.putpixel(xc+x + xx, yc+y + yy)
                        #     self.putpixel(xc-x - xx, yc+y + yy)
                        #     self.putpixel(xc+x + xx, yc-y - yy)
                        #     self.putpixel(xc-x - xx, yc-y - yy)
                        # for xx, yy in self.brush.B:
                        #     self.putpixel(xc+x + xx, yc+y + yy)
                        #     self.putpixel(xc-x - xx, yc+y + yy)
                        #     self.putpixel(xc+x + xx, yc-y - yy)
                        #     self.putpixel(xc-x - xx, yc-y - yy)
                # vertical or diag
                else:
                    e = 2 * d - 2 * x * b2 - b2
                    # vertical
                    if e > 0:
                        y -= 1
                        d += (-2 * y * a2 + a2)
                        # for xx, yy in self.brush.R:
                        #     self.putpixel(xc+x + xx, yc+y + yy)
                        #     self.putpixel(xc-x - xx, yc+y + yy)
                        #     self.putpixel(xc+x + xx, yc-y - yy)
                        #     self.putpixel(xc-x - xx, yc-y - yy)
                        # for xx, yy in self.brush.B:
                        #     self.putpixel(xc+x + xx, yc+y + yy)
                        #     self.putpixel(xc-x - xx, yc+y + yy)
                        #     self.putpixel(xc+x + xx, yc-y - yy)
                        #     self.putpixel(xc-x - xx, yc-y - yy)
                    # diag
                    else:
                        x += 1
                        y -= 1
                        d += (2 * x * b2 + b2 - 2 * y * a2 + a2)
                        # for xx, yy in self.brush.R:
                        #     self.putpixel(xc+x + xx, yc+y + yy)
                        #     self.putpixel(xc-x - xx, yc+y + yy)
                        #     self.putpixel(xc+x + xx, yc-y - yy)
                        #     self.putpixel(xc-x - xx, yc-y - yy)
                        # for xx, yy in self.brush.B:
                        #     self.putpixel(xc+x + xx, yc+y + yy)
                        #     self.putpixel(xc-x - xx, yc+y + yy)
                        #     self.putpixel(xc+x + xx, yc-y - yy)
                        #     self.putpixel(xc-x - xx, yc-y - yy)

    def set_size(self, val):
        self.brush_size = int(val)
        self.brush = self.PenForm(int(val))

    def new_image(self):
        d = DialogSize(self)
        if (d.h == None):
            return
        w, h = d.w, d.h

        self.canvas.scale('all', 0, 0, 1/self.imscale, 1/self.imscale)  # rescale all canvas objects
        self.image = Image.new('RGB', (w, h), color=(255, 255, 255))
        self.imgcopy = self.image.copy()
        self.width, self.height = self.image.size
        # scale for the canvaas image
        self.imscale = 1.0
        # zoom magnitude
        self.delta = 1.3
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        self.show_image()


    def save(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=(("png file", "*.png"),("All Files", "*.*") ))
        if path != "":
            # self.image.write(path)
            self.image.save(path)

    def about(self):
        messagebox.showinfo('About', 'Это сделал Мансуров Юрий.', parent=self)

    def save_img(self):
        self.imgcopy = self.image.copy()

    def null(self, *args):
        return



def main():
    root = tk.Tk()
    root.geometry("800x600+300+300")
    app = Paint(root)
    root.mainloop()


if __name__ == "__main__":
    main()
