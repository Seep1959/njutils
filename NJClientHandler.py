import asyncio
import base64
import time
import sys
import os
import zlib
import tempfile
import subprocess

from PIL import Image
from io import BytesIO

from NJProtocol import NJRatProtocol, NJRat_064_Protocol, NJRat_07d_Protocol, NJRat_07dg_Protocol
from NJRDPHandler import NJRDPHandler, NJ_064_RDPHandler, NJ_07d_RDPHandler, NJ_07dg_RDPHandler
from NJCamHandler import NJCamHandler, NJ_064_CamHandler, NJ_07d_CamHandler, NJ_07dg_CamHandler
from NJChatHandler import NJChatHandler, NJ_064_ChatHandler, NJ_07d_ChatHandler, NJ_07dg_ChatHandler
from NJController import NJController

modules = {b"2681e81bb4c4b3e6338ce2a456fb93a7": "sc2.dll",
           b"c4d7f8abbf369dc795fc7f2fdad65003": "cam.dll",
           b"2ff6644f405ebbe9cf2b70722b23d64b": "mic.dll",
           b"8e78a69ca187088abbea70727d268e90": "ch.dll",
           b"1160d9aa3de4ef527f216c0393862101": "sc2.dll",
           b"5546459fd68bf16831797d2aa2e7d569": "sc2.dll",
           b"2b3328e57676df442688f81f9824276a": "cam.dll",
           b"9de95a29dc2a0e10e95f43f8e9f190dd": "mic.dll",
           b"39b7927e0d4deb5c10fb380b7c53c617": "fm.dll",
           b"f6f6bcff36399302d016a2766c919bad": "ch.dll",
           b"140dc0e9ebf6b13690e878616dc2eba9": "cam.dll",
           b"d07291b438fb3f7ccb64c2e1efaf75d1": "ch.dll"}


class NJClientHandler(object):
    def __init__(self, proto, controller, args):
        self.proto = proto
        self.controller = controller
        self.args = args
        self.host = None
        self.port = None
        self.ver = None
        self.image = None
        self.thumbnail = None
        self.initial_text = None
        self.version_string = None
        self.name = None
        self.pc_name = None
        self.username = None
        self.os = None
        self.delimiter = None
        self.keylog_txt = None
        self.foreground_window = None

        self.CAP = False
        self.RESIZE = True       #Set to false to send fullsize image rather than resizing to servers request, looks nicer with resize False
        self.SENDONCE = True     #Set to false to send new image every request.

        self.CAM_ENABLED = True
        self.CHAT_ENABLED = True
        self.MIC_ENABLED = True
        self.RDP_ENABLED = True
        self.ECHO = False
        self.INTERACTIVE_CHAT = False


        if args["host"]:
            self.host = args["host"]
        if args["port"]:
            self.port = args["port"]
        if args["ver"]:
            self.ver = args["ver"]
        if args["image"]:
            self.image = args["image"]
        if args["thumbnail"]:
            self.thumbnail = args["thumbnail"]
        if args["cam_image"]:
            self.cam = args["cam_image"]
        if args["initial_text"]:
            self.initial_text = args["initial_text"]
        if args["version_string"]:
            self.version_string = args["version_string"]
        else:
            self.version_string = self.ver
        if args["name"]:
            self.name = args["name"]
        if args["username"]:
            self.username = args["username"]
        if args["pc_name"]:
            self.pc_name = args["pc_name"]
        if args["os"]:
            self.os = args["os"]
        if args["av"]:
            self.av = args["av"]
        if args["date"]:
            self.date = args["date"]
        if args["foreground_window"]:
            self.foreground_window = args["foreground_window"]
        if args["keylog_text"]:
            self.keylog_text = args["keylog_text"]

        if args["disable_cam"] == True:
            self.CAM_ENABLED = False
        if args["disable_chat"] == True:
            self.CHAT_ENABLED = False
        if args["disable_mic"] == True:
            self.MIC_ENABLED = False
        if args["disable_rdp"] == True:
            self.RDP_ENABLED = False
        if args["chat_echo"] == True:
            self.ECHO = True
        if args["non_interactive_chat"] == False:
            self.INTERACTIVE_CHAT = True

        if self.ver == "0.6.4" or self.ver == "0.7d":
            self.delimiter = "|'|'|"
        if self.ver == "0.7dg":
            self.delimiter = "|Hassan|"
        self.filepath = "downloads/" + str(self.host) + "_" + str(self.port)
        tempfile.tempdir = self.filepath
        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)

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
    def nj_send_plugin_ret(self, module, ret):
        msg = b"pl" + self.delimiter.encode() + module + self.delimiter.encode() + str(ret).encode()
        yield from self.send_nj_msg(msg)

    @asyncio.coroutine
    def nj_send_er_msg(self, error):
        msg = b"ER" + self.delimiter.encode() + b"!" + self.delimiter.encode() + error
        yield from self.send_nj_msg(msg)

    @asyncio.coroutine
    def nj_update_foreground(self, text):
        msg = b"act" + self.delimiter.encode() + base64.b64encode(text)
        yield from self.send_nj_msg(msg)

    @asyncio.coroutine
    def nj_send_keylogs(self, keylogs):
        if isinstance(keylogs, str):
            keylogs = keylogs.encode()
        msg = b"kl" + self.delimiter.encode() + base64.b64encode(keylogs)
        yield from self.send_nj_msg(msg)

    @asyncio.coroutine
    def nj_send_keylog_file(self):
        if self.initial_text:
            try:
                with open(self.initial_text, 'r') as f:
                    data = f.read()
            except Exception as error:
                print("Unexpected error:", sys.exc_info()[0])
                print(error)
            yield from self.nj_send_keylogs(data)


    @asyncio.coroutine
    def handle_nj_cap_command(self, msg):
        if self.CAP == False:     #We only send one screen cap
            self.controller.output("CAP REQUEST")
        try:
            width = int(msg[0])
            height = int(msg[1])
            size = (width,height)
            if self.CAP == True and self.RESIZE == False and self.SENDONCE:
                #yield from self.send_nj_msg(b"CAP" + self.delimiter.encode() + b"\x00")
                return
            if self.CAP == True and self.LASTSIZE == size and self.SENDONCE:
                #yield from self.send_nj_msg(b"CAP" + self.delimiter.encode() + b"\x00") #sent when image hasn't changed
                return

            im = Image.open(self.thumbnail).convert('RGB')
            if self.RESIZE:
                im.thumbnail(size, Image.ANTIALIAS)
                self.LASTSIZE = size
            with BytesIO() as output:
                im.save(output, "JPEG")
                image = output.getvalue()
            yield from self.send_nj_msg(b"CAP" + self.delimiter.encode() + image)
        except Exception as error:
            print("Unexpected error:", sys.exc_info()[0])
            print(error)

        finally:
            self.CAP = True

    @asyncio.coroutine
    def handle_nj_un_command(self, msg):
        if msg[0] == b"~":
            yield from self.handle_nj_un_uninstall()
        if msg[0] == b"!":
            yield from self.handle_nj_un_close()
        if msg[0] == b"@":
            yield from self.handle_nj_un_restart()

    @asyncio.coroutine
    def handle_nj_un_uninstall(self):
        yield from self.nj_update_foreground(b"NO PLEASE DONT UNINSTALL ME")
        self.controller.output("un uninstall command received")

    @asyncio.coroutine
    def handle_nj_un_close(self):
        yield from self.nj_update_foreground(b"NO PLEASE DONT CLOSE ME")
        self.controller.output("un close command received")

    @asyncio.coroutine
    def handle_nj_un_restart(self):
        yield from self.nj_update_foreground(b"NO PLEASE DONT RESTART ME")
        self.controller.output("un restart command received")

    @asyncio.coroutine
    def handle_nj_kl_command(self):
        self.controller.output("Received request for keylogs")
        yield from self.nj_update_foreground(b"Quit looking at my keys")
        yield from self.nj_send_keylogs(self.keylog_text)

    @asyncio.coroutine
    def handle_nj_rn_command(self, msg):
        pass

class NJ_064_ClientHandler(NJClientHandler):
    @asyncio.coroutine
    def send_nj_callback_msg(self):
        cb_msg = []
        cb_msg.append("lv")
        cb_msg.append(str(base64.b64encode(self.name.encode()), 'utf-8'))
        cb_msg.append(self.pc_name)
        cb_msg.append(self.username)
        cb_msg.append(self.date)
        cb_msg.append("") #not sure what this field is for
        cb_msg.append(self.os)
        cb_msg.append("Yes") #cam bool
        cb_msg.append(self.version_string)
        cb_msg.append("..") #initial value to put in ping column, only shown for a second, then we have no control over it. .. is sent with legitimate client
        cb_msg.append(str(base64.b64encode(self.foreground_window.encode()), 'utf-8'))
        cb_msg.append("2681e81bb4c4b3e6338ce2a456fb93a7,8e78a69ca187088abbea70727d268e90,b88ece4c04f706c9717bbe6fbda49ed2,c4d7f8abbf369dc795fc7f2fdad65003,2ff6644f405ebbe9cf2b70722b23d64b,") #tells the server what plugin modules we already have.
        msg = self.delimiter.join(cb_msg)
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.proto.send_nj_msg(b"P")

    @asyncio.coroutine
    def handle_nj_rn_command(self, msg):
        extension = str(msg[0], 'utf-8')
        if str(msg[1][:4], 'utf-8').lower() == "http":
            url = str(msg[1], 'utf-8')
            self.controller.output("HTTP DOWNLOAD/EXEC {} as {}".format(url, extension))
        else:
            data = base64.b64decode(msg[1])
            decoded = zlib.decompress(data, wbits=zlib.MAX_WBITS|16)
            filename = tempfile.mktemp("." + extension)
            self.controller.output("DOWNLOAD/EXEC, saving file to {}".format(filename))
            with open(filename, "wb") as f:
                f.write(decoded)

    @asyncio.coroutine
    def handle_nj_inv_command(self, msg):
        module = modules.get(msg[0], "unknown")
        self.controller.output("INV Module:{} Module ID:{} Identifier:{}".format(module, msg[0], msg[1]))
        yield from self.send_nj_msg(b"bla")
        yield from self.nj_send_plugin_ret(msg[0], 0)
        if module == "ch.dll" and self.CHAT_ENABLED:
            self.args["identifier"] = str(msg[1], 'utf-8')
            if self.INTERACTIVE_CHAT:
                # a malicious server could do some command line injection here, ehh ill maybe fix it later
                command = "gnome-terminal -- bash -c \"python3 njchat.py {} {} --identifier {} --ver {}\"".format(
                     self.host,
                     self.port,
                     self.args["identifier"],
                     self.ver)
                self.controller.output("Starting interactive chat, running the following command\n{}".format(command))
                subprocess.Popen(command, shell=True)
            else:
                controller = NJController(NJ_064_ChatHandler, self.args, c=None)
                controller.start()
        if module == "sc2.dll" and self.RDP_ENABLED:
            self.args["identifier"] = str(msg[1], 'utf-8')
            controller = NJController(NJ_064_RDPHandler, self.args, c=None)
            controller.start()
        if module == "cam.dll" and self.CAM_ENABLED:
            self.args["identifier"] = str(msg[1], 'utf-8')
            controller = NJController(NJ_064_CamHandler, self.args, c=None)
            controller.start()


    @asyncio.coroutine
    def handle_nj_msg(self):
        data = yield from self.read_nj_msg()
        msg = data.split(self.delimiter.encode())
        if msg[0] == b"P":
            yield from self.handle_nj_keepalive()
        if msg[0] == b"CAP":
            yield from self.handle_nj_cap_command(msg[1:])
        if msg[0] == b"un":
            yield from self.handle_nj_un_command(msg[1:])
        if msg[0] == b"kl":
            yield from self.handle_nj_kl_command()
        if msg[0] == b"rn":
            yield from self.handle_nj_rn_command(msg[1:])
        if msg[0] == b"inv":
            yield from self.handle_nj_inv_command(msg[1:])

    @asyncio.coroutine
    def run(self):
        try:
            yield from self.send_nj_callback_msg()
            yield from self.nj_send_keylog_file()
            for key in modules.keys(): #tells the server we have every plugin
                yield from self.nj_send_plugin_ret(key, 0)
            self.controller.output("Sent initial callback message")
            while True:
                yield from self.handle_nj_msg()

        except asyncio.IncompleteReadError as error:
            self.controller.output("Disconnected from server")
            self.controller.stop()

class NJ_07d_ClientHandler(NJClientHandler):

    def close_connection(self):
        self.controller.stop()

    @asyncio.coroutine
    def send_nj_callback_msg(self):
        cb_msg = []
        cb_msg.append("ll")
        cb_msg.append(str(base64.b64encode(self.name.encode()), 'utf-8'))
        cb_msg.append(self.pc_name)
        cb_msg.append(self.username)
        cb_msg.append(self.date)
        cb_msg.append("") #not sure what this field is for
        cb_msg.append(self.os)
        cb_msg.append("Yes") #cam bool
        cb_msg.append(self.version_string)
        cb_msg.append("..") #initial value to put in ping column, only shown for a second, then we have no control over it.
        cb_msg.append(str(base64.b64encode(self.foreground_window.encode()), 'utf-8'))
        cb_msg.append("2681e81bb4c4b3e6338ce2a456fb93a7,8e78a69ca187088abbea70727d268e90,b88ece4c04f706c9717bbe6fbda49ed2,c4d7f8abbf369dc795fc7f2fdad65003,2ff6644f405ebbe9cf2b70722b23d64b,") #tells the server what plugin modules we already have.
        msg = self.delimiter.join(cb_msg)
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.send_nj_msg(b"")

    @asyncio.coroutine
    def handle_nj_rn_command(self, msg):
        extension = str(msg[0], 'utf-8')
        if msg[1][0] == 0x1f: #gzip magic value
            data = msg[1]
            decoded = zlib.decompress(data, wbits=zlib.MAX_WBITS|16)
            filename = tempfile.mktemp("." + extension)
            self.controller.output("DOWNLOAD/EXEC, saving file to {}".format(filename))
            with open(filename, "wb") as f:
                f.write(decoded)
        else:
            url = str(msg[1], 'utf-8')
            self.controller.output("HTTP DOWNLOAD/EXEC {} as {}".format(url, extension))

    @asyncio.coroutine
    def handle_nj_inv_command(self, msg):
        module = modules.get(msg[0], "unknown")
        self.controller.output("INV Module:{} Module ID:{} Identifier:{}".format(module, msg[0], msg[1]))
        if module == "ch.dll" and self.CHAT_ENABLED:
            self.args["identifier"] = str(msg[1], 'utf-8')
            if self.INTERACTIVE_CHAT:
                command = "gnome-terminal -- bash -c \"python3 njchat.py {} {} --identifier {} --ver {}\"".format(
                     self.host,
                     self.port,
                     self.args["identifier"],
                     self.ver)
                self.controller.output("Starting interactive chat, running the following command\n{}".format(command))
                subprocess.Popen(command, shell=True)
            else:
                controller = NJController(NJ_07d_ChatHandler, self.args, c=None)
                controller.start()
        if module == "sc2.dll" and self.RDP_ENABLED:
            self.args["identifier"] = str(msg[1], 'utf-8')
            controller = NJController(NJ_07d_RDPHandler, self.args, c=None)
            controller.start()
        if module == "cam.dll" and self.CAM_ENABLED:
            self.args["identifier"] = str(msg[1], 'utf-8')
            controller = NJController(NJ_07d_CamHandler, self.args, c=None)
            controller.start()



    @asyncio.coroutine
    def handle_nj_msg(self):
        data = yield from self.read_nj_msg()
        if data is None:
            return
        if data == b"":
            yield from self.handle_nj_keepalive()
        else:
            msg = data.split(self.delimiter.encode())
            if msg[0] == b"CAP":
                yield from self.handle_nj_cap_command(msg[1:])
            if msg[0] == b"un":
                yield from self.handle_nj_un_command(msg[1:])
            if msg[0] == b"kl":
                yield from self.handle_nj_kl_command()
            if msg[0] == b"rn":
                yield from self.handle_nj_rn_command(msg[1:])
            if msg[0] == b"inv":
                yield from self.handle_nj_inv_command(msg[1:])


    @asyncio.coroutine
    def run(self):
        try:
            yield from self.send_nj_callback_msg()
            yield from self.nj_send_keylog_file()
            self.controller.output("Sent initial callback message")
            while True:
                yield from self.handle_nj_msg()
        except asyncio.IncompleteReadError as error:
            self.controller.output("Disconnected from server")
            self.controller.stop()

class NJ_07dg_ClientHandler(NJClientHandler):

    @asyncio.coroutine
    def send_nj_callback_msg(self):
        cb_msg = []
        cb_msg.append("ll")
        cb_msg.append(str(base64.b64encode(self.name.encode()), 'utf-8'))
        cb_msg.append(self.pc_name)
        cb_msg.append(self.username)
        cb_msg.append(self.date)
        cb_msg.append("")       #not sure what this field is for
        cb_msg.append(self.os)
        cb_msg.append("Yes")    #cam bool
        cb_msg.append(self.av)  #why send antivirus 3 times, holyshit what kind of idiot designed this
        cb_msg.append(self.av)
        cb_msg.append(self.av)
        cb_msg.append("")
        msg = self.delimiter.join(cb_msg)
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.send_nj_msg(b"")

    @asyncio.coroutine
    def handle_nj_rn_command(self, msg):
        extension = str(msg[0], 'utf-8')
        if msg[1][0] == 0x1f: #gzip magic value
            data = msg[1]
            decoded = zlib.decompress(data, wbits=zlib.MAX_WBITS|16)
            filename = tempfile.mktemp("." + extension)
            self.controller.output("DOWNLOAD/EXEC, saving file to {}".format(filename))
            with open(filename, "wb") as f:
                f.write(decoded)
        else:
            url = str(msg[1], 'utf-8')
            self.controller.output("HTTP DOWNLOAD/EXEC {} as {}".format(url, extension))

    @asyncio.coroutine
    def handle_nj_inv_command(self, msg):
        module = modules.get(msg[0], "unknown")
        self.controller.output("INV Module:{} Module ID:{} Identifier:{}".format(module, msg[0], msg[1]))
        if module == "ch.dll" and self.CHAT_ENABLED:
            self.args["identifier"] = str(msg[1], 'utf-8')
            if self.INTERACTIVE_CHAT:
                command = "gnome-terminal -- bash -c \"python3 njchat.py {} {} --identifier {} --ver {}\"".format(
                     self.host,
                     self.port,
                     self.args["identifier"],
                     self.ver)
                self.controller.output("Starting interactive chat, running the following command\n{}".format(command))
                subprocess.Popen(command, shell=True)
            else:
                controller = NJController(NJ_07dg_ChatHandler, self.args, c=None)
                controller.start()
        if module == "sc2.dll" and self.RDP_ENABLED:
            self.args["identifier"] = str(msg[1], 'utf-8')
            controller = NJController(NJ_07dg_RDPHandler, self.args, c=None)
            controller.start()
        if module == "cam.dll" and self.CAM_ENABLED:
            self.args["identifier"] = str(msg[1], 'utf-8')
            controller = NJController(NJ_07dg_CamHandler, self.args, c=None)
            controller.start()

    @asyncio.coroutine
    def handle_nj_msg(self):
        data = yield from self.read_nj_msg()
        if data is None:
            return
        if data == b"":
            yield from self.handle_nj_keepalive()
        else:
            msg = data.split(self.delimiter.encode())
            if msg[0] == b"CAP":
                yield from self.handle_nj_cap_command(msg[1:])
            if msg[0] == b"un":
                yield from self.handle_nj_un_command(msg[1:])
            if msg[0] == b"kl":
                yield from self.handle_nj_kl_command()
            if msg[0] == b"rn":
                yield from self.handle_nj_rn_command(msg[1:])
            if msg[0] == b"inv":
                yield from self.handle_nj_inv_command(msg[1:])


    @asyncio.coroutine
    def run(self):
        try:
            yield from self.send_nj_callback_msg()
            yield from self.nj_update_foreground(self.foreground_window.encode()) #fg not sent with callback message in 0.7d golden edition
            yield from self.nj_send_keylog_file()
            self.controller.output("Sent initial callback message")
            while True:
                yield from self.handle_nj_msg()

        except asyncio.IncompleteReadError as error:
            self.controller.output("Disconnected from server")
            self.controller.stop()
