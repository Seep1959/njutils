import asyncio
import datetime
from threading import Thread
import threading
from NJProtocol import NJRatProtocol, NJRat_064_Protocol, NJRat_07d_Protocol, NJRat_07dg_Protocol

class NJController:
     def __init__(self, handler, args, loop=None, c=None):
         self.handler = handler
         self.host = None
         self.port = None
         self.args = args
         self.loop = asyncio.new_event_loop() if loop is None else loop
         self._thread = None
         self._thread_exception = None

         self.c = c
         self.client = None
         self.transport = None
         self.protocol = None
         self.ver = "0.7d"
         if args["ver"]:
             self.ver = args["ver"]
         if args["host"]:
             self.host = args["host"]
         if args["port"]:
             self.port = args["port"]

     def factory(self):
         protocol = None
         if self.ver == "0.6.4":
             protocol = NJRat_064_Protocol(self, self.handler, self.args)
         if self.ver == "0.7d":
             protocol = NJRat_07d_Protocol(self, self.handler, self.args)
         if self.ver == "0.7dg":
             protocol = NJRat_07dg_Protocol(self, self.handler, self.args)
         return protocol

     def _run(self):
         try:
             asyncio.set_event_loop(self.loop)
             self.transport, self.protocol = self.loop.run_until_complete(
                 self.loop.create_connection(self.factory, host=self.host, port=self.port))
             self.loop.set_debug(enabled=True)
             self.loop.run_forever()
         except KeyboardInterrupt:
             raise
         except Exception as error:
             self._thread_exception = error
             print(error)

     def start(self):
         assert self._thread is None, 'Already been started'
         self._thread = threading.Thread(target=self._run)
         self._thread.daemon=True
         self._thread.start()

     def _stop(self):
         self.loop.stop()
         for task in asyncio.Task.all_tasks(self.loop):
             task.cancel()

     def stop(self):
         assert self._thread is not None, 'What is dead may never die'
         self.loop.call_soon_threadsafe(self._stop)
         #self._thread.join()
         self._thread = None

     def output(self, message, color=None):
         timestamp = "[{}] ".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
         if self.c is not None:
             self.c.output(timestamp + message, color)
         else:
             print(timestamp + message)

