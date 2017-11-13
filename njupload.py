#!/usr/bin/env python3
import argparse
import asyncio
from NJUploadHandler import NJUploadHandler, NJ_064_UploadHandler, NJ_07d_UploadHandler, NJ_07dg_UploadHandler
from NJController import NJController

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="njchat.py")
    parser.add_argument("host", type=str, help="The IP/Domain of the njrat C2.")
    parser.add_argument("port", type=int, help="The port the njrat C2 is listening on.")
    parser.add_argument("-y", "--ver", default="0.7d", type=str, choices=["0.6.4", "0.7d", "0.7dg"], help="Version of NJRat Server. 0.6.4, 0.7d, 0.7dg.")
    parser.add_argument("-u", "--upload-file", type=str, help="File to upload")
    parser.add_argument("-i", "--identifier", type=str, help="The full identifier used on initial callback for the C2 to identify which client the chat session is associated with")
    parser.add_argument("-r", "--reported-ip", type=str, help="The IP reported on initial callback for the C2 to identify which client the chat session is associated with")
    parser.add_argument("-p", "--reported-port", type=str, help="The port reported on initial callback for the C2 to identify which client the chat session is associated with")
    parser.add_argument("--version", action='version', version='%(prog)s 1.0')

    args = vars(parser.parse_args())

    if args["ver"] == "0.6.4":
        controller = NJController(NJ_064_UploadHandler, args, c=None)
    if args["ver"] == "0.7d":
        controller = NJController(NJ_07d_UploadHandler, args, c=None)
    if args["ver"] == "0.7dg":
        controller = NJController(NJ_07dg_UploadHandler, args, c=None)
    try:
        controller.start()
        controller._thread.join()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        #print(error)
