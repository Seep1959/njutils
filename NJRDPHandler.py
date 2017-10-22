import asyncio
import base64
from threading import Thread
import threading
import time
import random
import datetime
import zlib
import sys
import tempfile
import os
from PIL import Image
from io import BytesIO

def get_box(pos_x, pos_y, width, height):
    return (pos_x, pos_y, pos_x + width, pos_y + height)

class NJRDPHandler(object):
    def __init__(self, proto, controller, args):
        self.proto = proto
        self.controller = controller
        self.host = None
        self.port = None
        self.ver = None
        self.image = None
        self.delimiter = None

        if args["host"]:
            self.host = args["host"]
        if args["port"]:
            self.port = args["port"]
        if args["identifier"]:
            self.identifier = args["identifier"]
        if args["ver"]:
            self.ver = args["ver"]
        if args["image"]:
            self.image = args["image"]
        if args["version_string"]:
            self.version_string = args["version_string"]
        else:
            self.version_string = self.ver
        if self.ver == "0.6.4" or self.ver == "0.7d":
            self.delimiter = "|'|'|"
        if self.ver == "0.7dg":
            self.delimiter = "|Hassan|"

    def close_connection(self):
        pass

    @asyncio.coroutine
    def send_nj_msg(self, data):
        yield from self.proto.send_nj_msg(data)

    @asyncio.coroutine
    def read_nj_msg(self):
        data = yield from self.proto.read_nj_msg()
        return data


    @asyncio.coroutine
    def handle_unknown_nj_command(self, msg):
        self.controller.output("Unknown command, received", color="error")
        try:
            self.controller.output(str(msg), color="error")
        except:
            self.controller.output("Failed to print command", color="error")
            self.controller.output(str(msg[0:1]), color="error")



class NJ_064_RDPHandler(NJRDPHandler):
    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.send_nj_msg(b"P")

    @asyncio.coroutine
    def get_image(self, size):
        im = Image.open(self.image)
        im_size = im.size
        self.controller.output("Image size: {}, server requested {}% of the image size".format(im_size, size))
        w,h = im_size #im sorry, i know this is a mess
        size = ( (size * w)/100, (size * h)/100 )
        if im_size != size:
            im.thumbnail(size, Image.ANTIALIAS)
        with BytesIO() as output:
            im.save(output, "JPEG")
            image = output.getvalue()
        return image

    def send_nj_sc_pk_msg(self, image):
         msg = b""
         msg += b"scPK"
         msg += self.delimiter.encode()
         msg += self.identifier.encode()
         msg += self.delimiter.encode()
         msg += b"~spl~"
         #msg += self.delimiter.encode()
         msg += image
         yield from self.send_nj_msg(msg)

    @asyncio.coroutine
    def handle_nj_sc_stop_command(self):
        self.controller.output("Received RDP stop command")

    @asyncio.coroutine
    def send_nj_sc_callin_msg(self):
        im = Image.open(self.image)
        width, height = im.size
        msg = ""
        msg += "sc~"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += str(width)
        msg += self.delimiter
        msg += str(height)
        msg += self.delimiter
        msg += str(1) #not sure yet
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def handle_nj_sc_start_command(self, msg):
        self.controller.output("Received RDP start command")
        image_size = str(msg[1], "utf-8")
        self.rip = str(msg[0], "utf-8").split(":")[0]
        self.rp = int(str(msg[0], "utf-8").split(":")[1])
        self.identifier = "{}:{}".format(self.rip, self.rp)
        image = yield from self.get_image(int(image_size))
        yield from self.send_nj_sc_pk_msg(image)

    @asyncio.coroutine
    def handle_nj_msg(self):
        data = yield from self.read_nj_msg()
        if data is None:
            return
        if data == b"P":
            yield from self.handle_nj_keepalive()
        else:
            msg = data.split(self.delimiter.encode())
            if msg[0] == b"!":
                yield from self.handle_nj_sc_start_command(msg[1:])
            elif msg[0] == b"!!":
                yield from self.handle_nj_sc_stop_command()

            else:
                yield from self.handle_unknown_nj_command(msg)

    @asyncio.coroutine
    def run(self):
        yield from self.send_nj_sc_callin_msg()
        self.controller.output("Sent initial callback message", color="green")
        while True:
            yield from self.handle_nj_msg()

class NJ_07d_RDPHandler(NJRDPHandler):
    @asyncio.coroutine
    def send_nj_sc_callin_msg(self):
        im = Image.open(self.image)
        width, height = im.size
        msg = ""
        msg += "sc~"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += str(width)
        msg += self.delimiter
        msg += str(height)
        yield from self.send_nj_msg(msg.encode())


    @asyncio.coroutine
    def send_nj_sc_pk_msg(self, positions, image):
         msg = b""
         msg += b"scPK"
         msg += self.delimiter.encode()
         msg += self.identifier.encode()
         msg += self.delimiter.encode()
         msg += positions
         msg += self.delimiter.encode()
         msg += image
         yield from self.send_nj_msg(msg)

        #cb_msg = []
        #cb_msg.append(b"scPK")
        #cb_msg.append(self.identifier)
        #cb_msg.append(positions)
        #cb_msg.append(image)
        #msg = self.delimiter.join(cb_msg)
        #yield from self.send_nj_msg(msg.encode())
        #yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.send_nj_msg(b"")

    @asyncio.coroutine
    def handle_nj_sc_start_command(self, msg):
        self.controller.output("Received RDP start command")
        width, height = str(msg[1], "utf-8").split("x")
        self.rip = str(msg[0], "utf-8").split(":")[0]
        self.rp = int(str(msg[0], "utf-8").split(":")[1])
        self.identifier = "{}:{}".format(self.rip, self.rp)
        size = (int(width), int(height))
        print(size)
        positions, image = yield from self.get_image(size)
        yield from self.send_nj_sc_pk_msg(positions.encode(), image)

    @asyncio.coroutine
    def get_image(self, size):
        im = Image.open(self.image)
        im_size = im.size
        print(im_size)
        if im_size != size:
            im.thumbnail(size, Image.ANTIALIAS)
        width, height = im.size
        sub_width = int(width/10)
        sub_height = int(height/10)
        positions = []
        positions.append("{},{}".format(width, height))
        positions.append(str(sub_height))
        im2 = Image.new("RGB", (sub_width, sub_height * 100))
        boxes = []
        for x in range(0, 10):
            for y in range(0, 10):
                box = get_box(sub_width * x, sub_height * y, sub_width, sub_height)
                positions.append("{},{}".format(sub_width * x, sub_height * y))
                boxes.append(box)
        x = 0
        for box in boxes:
            region = im.crop(box)
            box2 = get_box(0, sub_height * x, sub_width, sub_height)
            im2.paste(region,box2)
            x += 1
        with BytesIO() as output:
            im2.save(output, "JPEG")
            image = output.getvalue()
        positions = "-".join(positions)
        return positions,image

    @asyncio.coroutine
    def handle_nj_sc_stop_command(self):
        self.controller.output("Received RDP stop command")

    @asyncio.coroutine
    def handle_nj_msg(self):
        data = yield from self.read_nj_msg()
        if data is None:
            return
        if data == b"":
            yield from self.handle_nj_keepalive()
        else:
            msg = data.split(self.delimiter.encode())
            if msg[0] == b"!":
                yield from self.handle_nj_sc_start_command(msg[1:])
            elif msg[0] == b"!!":
                yield from self.handle_nj_sc_stop_command()

            else:
                yield from self.handle_unknown_nj_command(msg)

    @asyncio.coroutine
    def run(self):
        yield from self.send_nj_sc_callin_msg()
        self.controller.output("Sent initial callback message", color="green")
        while True:
            yield from self.handle_nj_msg()

class NJ_07dg_RDPHandler(NJ_07d_RDPHandler): #pretty much identical to 0.7d
    pass
