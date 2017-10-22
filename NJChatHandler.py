
import asyncio
import base64
from threading import Thread
import threading
import time
import random
import datetime
import sys
import os

class NJChatHandler(object):
    def __init__(self, proto, controller, args):
        self.proto = proto
        self.controller = controller
        self.args = args
        self.host = None
        self.port = None
        self.ver = None
        self.identifier = None
        self.delimiter = None
        self.ECHO = False

        if args["host"]:
            self.host = args["host"]
        if args["port"]:
            self.port = args["port"]
        if args["identifier"]:
            self.identifier = args["identifier"]
        if args["chat_echo"] == True:
            self.ECHO = True
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
        self.controller.output("Connection has been lost", color="error")

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
    def send_nj_ch_callin_msg(self):
        if not self.identifier:
            self.get_identifier()
        msg = ""
        msg += "CH"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "~"
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def send_nj_chat_ack(self):
        msg = ""
        msg += "CH"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "!"
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def send_nj_chat_msg(self, data):
        self.controller.output("Me> " + str(data, 'utf-8'), color="green")
        message = str(base64.b64encode(data), 'utf-8')
        msg = ""
        msg += "CH"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "@"
        msg += self.delimiter
        msg += message
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def handle_nj_chat_ack(self, data):
        self.nick = str(base64.b64decode(data), 'utf-8')
        self.controller.output("Connection from {}".format(self.nick), color="green")
        yield from self.send_nj_chat_ack()

    @asyncio.coroutine
    def handle_nj_chat_msg(self, data):
        msg = base64.b64decode(data)
        msg = str(msg, 'utf-8')
        msg = self.nick + '> ' + msg
        self.controller.output(msg, color="green")
        if self.ECHO:
            yield from self.send_nj_chat_msg(base64.b64decode(data))

    @asyncio.coroutine
    def handle_nj_chat_disconnect(self):
        if not self.nick:
            self.controller.output("Chat request was refused!", color="green")
        else:
            self.controller.output("{} has disconnected!".format(self.nick), color="green")

    @asyncio.coroutine
    def run(self):
        yield from self.send_nj_ch_callin_msg()
        self.controller.output("Sent initial callback message", color="green")
        while True:
            yield from self.handle_nj_msg()


class NJ_064_ChatHandler(NJChatHandler):
    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.proto.send_nj_msg(b"P")

    @asyncio.coroutine
    def handle_nj_msg(self):
        data = yield from self.read_nj_msg()
        if data is None:
            return
        if data == b"P":
            yield from self.handle_nj_keepalive()
        else:
            msg = data.split(self.delimiter.encode())
            if msg[0] == b'~':
                yield from self.handle_nj_chat_ack(msg[1])
            elif msg[0] == b'!':
                yield from self.handle_nj_chat_msg(msg[1])
            elif msg[0] == b'@':
                yield from self.handle_nj_chat_disconnect()
            else:
                yield from self.handle_unknown_nj_command(msg)


class NJ_07d_ChatHandler(NJChatHandler):
    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.send_nj_msg(b"")

    @asyncio.coroutine
    def handle_nj_msg(self):
        data = yield from self.read_nj_msg()
        if data is None:
            return
        if data == b"":
            yield from self.handle_nj_keepalive()
        else:
            msg = data.split(self.delimiter.encode())
            if msg[0] == b'~':
                yield from self.handle_nj_chat_ack(msg[1])
            elif msg[0] == b'!':
                yield from self.handle_nj_chat_msg(msg[1])
            elif msg[0] == b'@':
                yield from self.handle_nj_chat_disconnect()
            else:
                yield from self.handle_unknown_nj_command(msg)

class NJ_07dg_ChatHandler(NJ_07d_ChatHandler): #pretty much identical to 0.7d
    pass
