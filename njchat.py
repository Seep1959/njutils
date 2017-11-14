#!/usr/bin/env python3
import argparse
import asyncio
from commander import *
from NJClientHandler import NJChatHandler, NJ_064_ChatHandler, NJ_07d_ChatHandler, NJ_07dg_ChatHandler
from NJController import NJController

class NJChatUI(Command):
    def send_message(self, line):
        controller.send_message(line)

class NJChatController(NJController):
    def send_message(self, message):
        assert self._thread is not None, 'Must start before message sending possible'
        if self.loop.is_running():
            if self.protocol is not None and self.transport is not None:
                if not self.transport.is_closing():
                    coro = self.protocol.handler.send_nj_chat_msg(message.encode())
                    future = asyncio.run_coroutine_threadsafe(coro, self.loop)
                else:
                    self.output("Could not send message, transport appears to be closed.", color="error")
            else:
                self.output("Could not send message, it seems you don't have a protocol or transport", color="error")

        else:
            self.output("Aint got no loop dogg", color="error")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="njchat.py")
    parser.add_argument("host", type=str, help="The IP/Domain of the njrat C2.")
    parser.add_argument("port", type=int, help="The port the njrat C2 is listening on.")
    parser.add_argument("-y", "--ver", default="0.7d", type=str, choices=["0.6.4", "0.7d", "0.7dg"], help="Version of NJRat Server. 0.6.4, 0.7d, 0.7dg.")
    parser.add_argument("-D", "--delimiter", type=str, help="Used to set a custom delimiter, useful for modded njrat versions.")
    parser.add_argument("-e", "--chat-echo", action='store_true', help="Echo chat messages.")
    parser.add_argument("-i", "--identifier", type=str, help="The full identifier used on initial callback for the C2 to identify which client the chat session is associated with")
    parser.add_argument("-r", "--reported-ip", type=str, help="The IP reported on initial callback for the C2 to identify which client the chat session is associated with")
    parser.add_argument("-p", "--reported-port", type=str, help="The port reported on initial callback for the C2 to identify which client the chat session is associated with")
    parser.add_argument("--non-interactive-chat", action='store_true', help="Do not start cli UI")
    parser.add_argument("--version", action='version', version='%(prog)s 1.0')

    args = vars(parser.parse_args())

    if args["non_interactive_chat"]:
        if args["ver"] == "0.6.4":
            controller = NJController(NJ_064_ChatHandler, args, c=None)
        if args["ver"] == "0.7d":
            controller = NJController(NJ_07d_ChatHandler, args, c=None)
        if args["ver"] == "0.7dg":
            controller = NJController(NJ_07dg_ChatHandler, args, c=None)
        try:
            controller.start()
            controller._thread.join()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            #print(error)
    else:
        c = Commander("NJChat UI", cmd_cb=NJChatUI())
        if args["ver"] == "0.6.4":
            controller = NJChatController(NJ_064_ChatHandler, args, c=c)
        if args["ver"] == "0.7d":
            controller = NJChatController(NJ_07d_ChatHandler, args, c=c)
        if args["ver"] == "0.7dg":
            controller = NJChatController(NJ_07dg_ChatHandler, args, c=c)
        try:
            controller.start()
            c.loop()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            #print(error)
