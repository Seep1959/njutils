import asyncio
import base64
from threading import Thread
import threading
import time
import random
import datetime
import sys
import os

class NJUploadHandler(object):
    def __init__(self, proto, controller, args):
        self.proto = proto
        self.controller = controller
        self.args = args
        self.host = None
        self.port = None
        self.ver = None
        self.identifier = None
        self.delimiter = None
        self.upload_file = None

        if args["host"]:
            self.host = args["host"]
        if args["port"]:
            self.port = args["port"]
        if args["identifier"]:
            self.identifier = args["identifier"]
        if args["upload_file"]:
            self.upload_file = args["upload_file"]
        if args["ver"]:
            self.ver = args["ver"]
        if self.ver == "0.6.4" or self.ver == "0.7d":
            self.delimiter = "|'|'|"
        if self.ver == "0.7dg":
            self.delimiter = "|Hassan|"

    def get_identifier(self):
        if self.args["reported_ip"]:
            rip = self.args["reported_ip"]
        else:
            rip = self.proto.sockip
        if self.args["reported_port"]:
            rp = self.args["reported_port"]
        else:
            rp = self.proto.sockport
        self.identifier = "{}:{}".format(rip, rp)

    def close_connection(self):
        self.controller.output("Upload finished, or not, i'm just a script", color="error")
        self.controller.stop()

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

    @asyncio.coroutine
    def send_nj_post_msg(self):
        if not self.identifier:
            self.get_identifier()
        filename = os.path.basename(self.upload_file) #usually this would be full path, but we don't want to give that away.
        msg = ""
        msg += "post"
        msg += self.delimiter
        msg += str(base64.b64encode(filename.encode()), 'utf-8')
        msg += self.delimiter
        msg += str(os.stat(self.upload_file).st_size)
        msg += self.delimiter
        msg += self.identifier
        yield from self.send_nj_msg(msg.encode())

        time.sleep(2)
        with open(self.upload_file, 'rb') as f:
            data = f.read()
        self.proto.writer.write(data)

    @asyncio.coroutine
    def run(self):
        yield from self.send_nj_post_msg()
        self.controller.output("Sent upload message", color="green")
        while True:
            yield from self.handle_nj_msg()


class NJ_064_UploadHandler(NJUploadHandler):
    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.send_nj_msg(b"P")

    @asyncio.coroutine
    def handle_nj_msg(self):
        data = yield from self.read_nj_msg()
        if data is None:
            return
        if data == b"P":
            yield from self.handle_nj_keepalive()
        elif data == b"ok":
            self.controller.output("ok")

class NJ_07d_UploadHandler(NJUploadHandler):
    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.send_nj_msg(b"")

    @asyncio.coroutine
    def handle_nj_msg(self):
        data = yield from self.read_nj_msg()
        if data is None:
            return
        elif data == b"":
            yield from self.handle_nj_keepalive()
        elif data == b'ok':
            self.controller.output("ok")

class NJ_07dg_UploadHandler(NJ_07d_UploadHandler): #pretty much identical to 0.7d
    pass
