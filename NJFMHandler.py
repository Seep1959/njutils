import asyncio
import os
import sys
import pathlib
import base64

class NJFMHandler(object):
    def __init__(self, proto, controller, args):
        self.proto = proto
        self.controller = controller
        self.host = None
        self.port = None
        self.ver = None
        self.delimiter = None
        self.rootdir = pathlib.Path("rootdir").resolve()
        self.drive = pathlib.PureWindowsPath("Z:\\")
        self.STARTED = False

        if args["host"]:
            self.host = args["host"]
        if args["port"]:
            self.port = args["port"]
        if args["identifier"]:
            self.identifier = args["identifier"]
        if args["ver"]:
            self.ver = args["ver"]
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



class NJ_064_FMHandler(NJFMHandler):
    @asyncio.coroutine
    def handle_nj_keepalive(self):
        yield from self.send_nj_msg(b"P")

    def net_to_host_path(self, path):
        parts = pathlib.PureWindowsPath(path).parts[1:]
        host_path = self.rootdir.joinpath(*parts).resolve()
        return host_path

    def host_to_net_path(self, path):
        pass

    @asyncio.coroutine
    def send_nj_upload(self, msg):
        net_path = base64.b64decode(msg[0])
        host_path = self.net_to_host_path(str(net_path, 'utf-8'))
        identifier = msg[1]
        print("ABOUT TO ENSURE FUTURE")
        asyncio.ensure_future(self.upload_file(host_path, identifier))
        print("FUTURE HAS BEEN ENSURED")


    @asyncio.coroutine
    def upload_file(self, file_path, identifier):
        print("I AM THE FUTURE")
        connect = asyncio.open_connection(self.host, self.port)
        reader, writer = yield from connect
        msg = b"post"
        msg += self.delimiter.encode()
        msg += base64.b64encode(file_path.name.encode())
        msg += self.delimiter.encode()
        msg += str(os.stat(str(file_path)).st_size).encode()
        msg += self.delimiter.encode()
        msg += identifier
        msg += b"[endof]"
        writer.write(msg)
        data = yield from reader.readexactly(2)
        if data == b"ok":
            print("WE GOT THE OK, YEAHHAHA")
            writer.write(file_path.read_bytes())

    @asyncio.coroutine
    def send_nj_fm_callin_msg(self):
        msg = ""
        msg += "FM"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "~"
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def send_nj_fm_dirs(self):
        msg = ""
        msg += "FM"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "!"
        msg += self.delimiter
        msg += str(base64.b64encode(b"Z:\\;Fixed"), 'utf-8')

        mylist = sorted([x for x in self.rootdir.iterdir() if x.is_dir()])
        for directory in mylist:
            msg += self.delimiter
            path = pathlib.PureWindowsPath("Z:\\").joinpath(str(directory.name))
            msg += str(base64.b64encode(str(path).encode() + b";"), 'utf-8')
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def send_nj_fm_dir_list(self, directory):
        msg = ""
        msg += "FM"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "@"
        msg += self.delimiter
        msg += str(directory, 'utf-8')
        msg += self.delimiter

        try:
            mydir = str(base64.b64decode(directory), 'utf-8')
            path = self.net_to_host_path(mydir)

            mylist = sorted([x for x in path.iterdir() if x.is_dir()])
            text = ""
            for directory in mylist:
                text += str(base64.b64encode(directory.name.encode()), 'utf-8')
                text += ";"
            msg += text

        except Exception as error:
            print("Unexpected error:", sys.exc_info()[0])
            print(error)
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def send_nj_fm_file_list(self, directory):
        msg = ""
        msg += "FM"
        msg += self.delimiter
        msg += self.identifier
        msg += self.delimiter
        msg += "#"
        msg += self.delimiter
        msg += str(directory, 'utf-8')
        msg += self.delimiter

        try:
            mydir = str(base64.b64decode(directory), 'utf-8')
            path = self.net_to_host_path(mydir)

            mylist = sorted([x for x in path.iterdir() if x.is_file()])
            print(mylist)
            text = ""
            for directory in mylist:
                text += str(base64.b64encode("{};{}".format(directory.name, directory.stat().st_size).encode()), 'utf-8')
                text += ";"
                print(text)
            msg += text

        except Exception as error:
            print("Unexpected error:", sys.exc_info()[0])
            print(error)
        yield from self.send_nj_msg(msg.encode())

    @asyncio.coroutine
    def handle_nj_msg(self):
        data = yield from self.read_nj_msg()
        if data is None:
            return
        if data == b"P":
            yield from self.handle_nj_keepalive()
        else:
            msg = data.split(self.delimiter.encode())
            if msg[0] == b"~":
                yield from self.send_nj_fm_dirs()
            elif msg[0] == b"!":
                yield from self.send_nj_fm_dir_list(msg[1])
            elif msg[0] == b"@":
                yield from self.send_nj_fm_file_list(msg[1])
            elif msg[0] == b"dw":
                yield from self.send_nj_upload(msg[1:])
            else:
                yield from self.handle_unknown_nj_command(msg)

    @asyncio.coroutine
    def run(self):
        try:
            yield from self.send_nj_fm_callin_msg()
            self.controller.output("Sent initial callback message", color="green")
            while True:
                yield from self.handle_nj_msg()
        except Exception as error:
            print("Unexpected error:", sys.exc_info()[0])
            print(error)

