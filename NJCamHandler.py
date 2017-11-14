import asyncio
import base64
from PIL import Image
from io import BytesIO

class NJCamHandler(object):
    def __init__(self, proto, controller, args):
        self.proto = proto
        self.controller = controller
        self.host = None
        self.port = None
        self.ver = None
        self.image = None
        self.delimiter = None
        self.STARTED = False

        if args["host"]:
            self.host = args["host"]
        if args["port"]:
            self.port = args["port"]
        if args["identifier"]:
            self.identifier = args["identifier"]
        if args["ver"]:
            self.ver = args["ver"]
        if args["cam_image"]:
            self.image = args["cam_image"]
        if args["version_string"]:
            self.version_string = args["version_string"]
        else:
            self.version_string = self.ver
        if self.ver == "0.6.4" or self.ver == "0.7d":
            self.delimiter = "|'|'|"
        if self.ver == "0.7dg":
            self.delimiter = "|Hassan|"
        if args["delimiter"]:
            self.delimiter = args["delimiter"]

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



class NJ_064_CamHandler(NJCamHandler):
    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.send_nj_msg(b"P")

    @asyncio.coroutine
    def send_nj_cam_callin_msg(self):
        msg = ""
        msg += "CAM"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "~"
        msg += self.delimiter
        msg += "Dick Cam"
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def send_nj_cam_img(self, size):
        image = yield from self.get_image(size)
        msg = b""
        msg += b"CAM"
        msg += self.delimiter.encode()
        msg += self.identifier.encode()
        msg += self.delimiter.encode()
        msg += b"!"
        msg += self.delimiter.encode()
        msg += base64.b64encode(image)
        yield from self.send_nj_msg(msg)

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

    @asyncio.coroutine
    def send_nj_cam_ack(self):
        msg = ""
        msg += "CAM"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "!"
        msg += self.delimiter
        msg += "!"
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def handle_nj_cam_start_command(self, msg):
        if not self.STARTED:
            self.controller.output("Received CAM start command") #one stupid nj variant spams the start message
            self.STARTED = True
        yield from self.send_nj_cam_ack()
        #usually the server sends the size it wants, im lazy just give 100%
        yield from self.send_nj_cam_img(100)

    @asyncio.coroutine
    def handle_nj_cam_stop_command(self):
        self.STARTED = False
        self.controller.output("Received CAM stop command")

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
                yield from self.handle_nj_cam_start_command(msg[1:])
            elif msg[0] == b"@":
                yield from self.handle_nj_cam_stop_command()

            else:
                yield from self.handle_unknown_nj_command(msg)

    @asyncio.coroutine
    def run(self):
        yield from self.send_nj_cam_callin_msg()
        self.controller.output("Sent initial callback message", color="green")
        while True:
            yield from self.handle_nj_msg()

class NJ_07d_CamHandler(NJCamHandler):
    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.send_nj_msg(b"")

    @asyncio.coroutine
    def send_nj_cam_callin_msg(self):
        msg = ""
        msg += "CAM"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "~"
        msg += self.delimiter
        msg += "Dick Cam"
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def send_nj_cam_ack(self):
        msg = ""
        msg += "CAM"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "!"
        msg += self.delimiter
        msg += "!"
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def send_nj_cam_img(self, size):
        image = yield from self.get_image(size)
        msg = b""
        msg += b"CAM"
        msg += self.delimiter.encode()
        msg += self.identifier.encode()
        msg += self.delimiter.encode()
        msg += b"!"
        msg += self.delimiter.encode()
        msg += image
        yield from self.send_nj_msg(msg)

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

    @asyncio.coroutine
    def handle_nj_cam_start_command(self, msg):
        self.controller.output("Received CAM start command")
        cam = str(msg[0], 'utf-8') #we aint do shit with this
        size = int(str(msg[1], 'utf-8')[1:]) #dont want no disgusting percent sign
        yield from self.send_nj_cam_ack()
        yield from self.send_nj_cam_img(size)

    @asyncio.coroutine
    def handle_nj_cam_stop_command(self):
        self.controller.output("Received CAM stop command")


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
                yield from self.handle_nj_cam_start_command(msg[1:])
            elif msg[0] == b"@":
                yield from self.handle_nj_cam_stop_command()

            else:
                yield from self.handle_unknown_nj_command(msg)

    @asyncio.coroutine
    def run(self):
        yield from self.send_nj_cam_callin_msg()
        self.controller.output("Sent initial callback message", color="green")
        while True:
            yield from self.handle_nj_msg()

class NJ_07dg_CamHandler(NJ_07d_CamHandler): #pretty much identical to 0.7d
    pass
