import asyncio


class NJRatProtocol(asyncio.StreamReaderProtocol):
    def __init__(self, controller, handler_cls, args):
        asyncio.StreamReaderProtocol.__init__(self, asyncio.StreamReader(), self._pseudo_connected)
        self.controller = controller
        self.handler = handler_cls(self, controller, args)

        #self.sockname = None
        #self.sockip = None
        #self.sockport = None
        #self.peername = None

    def connection_made(self, transport):
        super().connection_made(transport)
        #self.sockname = self.writer.get_extra_info('sockname')
        #self.sockip = self.sockname[0]
        #self.sockport = self.sockname[1]
        #self.peername = self.writer.get_extra_info('peername')

        self.controller.output("Connected to {}:{}".format(self.peername[0], self.peername[1]), color="green")
        f = asyncio.async(self.handler.run())
        f.add_done_callback(self.terminated)

    def _pseudo_connected(self, reader, writer):
        pass


    def connection_lost(self, exc):
        super().connection_lost(exc)

    def terminated(self, f):
        if f.done() and not f.cancelled():
            ex = f.exception()
            if ex:
                #print(ex)
                #self.controller.output("Connection has been terminated.", color="green")
                self.handler.close_connection()

    @property
    def writer(self):
        return self._stream_writer

    @property
    def reader(self):
        return self._stream_reader

    @property
    def sockname(self):
        return self.writer.get_extra_info('sockname')

    @property
    def peername(self):
        return self.writer.get_extra_info('peername')

    @property
    def sockip(self):
        return self.sockname[0]

    @property
    def sockport(self):
        return self.sockname[1]


class NJRat_064_Protocol(NJRatProtocol):

    @asyncio.coroutine
    def read_nj_msg(self):
        marker = b"[endof]"
        data = yield from self.reader.readuntil(separator=marker)
        return data[:-len(marker)] #readuntil return data including the seperator, we don't want the seperator

    @asyncio.coroutine
    def send_nj_msg(self, data):
        msg = data + b'[endof]'
        self.writer.write(msg)

class NJRat_07d_Protocol(NJRatProtocol):
    @asyncio.coroutine
    def read_nj_msg(self):
        size = yield from self.reader.readuntil(separator=b'\x00')
        data = yield from self.reader.readexactly(int(size.decode()[:-1]))
        return data

    @asyncio.coroutine
    def send_nj_msg(self, data):
        size = len(data)
        header = str(size).encode() + b'\x00'
        msg = header + data
        self.writer.write(msg)

class NJRat_07dg_Protocol(NJRatProtocol):
    @asyncio.coroutine
    def read_nj_msg(self):
        size = yield from self.reader.readuntil(separator=b'\x00')
        data = yield from self.reader.readexactly(int(size.decode()[:-1]))
        return data

    @asyncio.coroutine
    def send_nj_msg(self, data):
        size = len(data)
        header = str(size).encode() + b'\x00'
        msg = header + data
        self.writer.write(msg)
