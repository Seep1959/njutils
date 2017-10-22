#!/usr/bin/env python3
import argparse
from NJClientHandler import NJClientHandler, NJ_064_ClientHandler, NJ_07d_ClientHandler, NJ_07dg_ClientHandler
from NJController import NJController

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="njclient.py")
    parser.add_argument("host", type=str, help="The IP/Domain of the njrat C2.")
    parser.add_argument("port", type=int, help="The port the njrat C2 is listening on.")
    parser.add_argument("-i", "--image", default="default/image.jpg", type=str, help="Image to send when remote desktop is requested.")
    parser.add_argument("-t", "--thumbnail", default="default/thumbnail.jpg", type=str, help="Image to send when screenshot is requested.")
    parser.add_argument("-c", "--cam-image", default="default/cam.png", type=str, help="Image to send when remote cam is requested.")
    parser.add_argument("-f", "--foreground-window", default="Desktop", type=str, help="Foreground window reported on initial callback.")
    parser.add_argument("-n", "--name", default="HacKed_5C96AEE2", type=str, help="Name reported on initial callback.")
    parser.add_argument("-d", "--date", default="17-01-15", type=str, help="Install date reported on initial callback. format=YY-MM-DD")
    parser.add_argument("-o", "--os", default="Windows 7 Home Premium SP1 x64", type=str, help="Operating system reported on initial callback.")
    parser.add_argument("-p", "--pc-name", default="Jack-PC", type=str, help="PC name reported on initial callback.")
    parser.add_argument("-u", "--username", default="Jack", type=str, help="Username reported on inital callback.")
    parser.add_argument("-y", "--ver", default="0.7d", type=str, choices=["0.6.4", "0.7d", "0.7dg"], help="Version of NJRat Server. 0.6.4, 0.7d, 0.7dg.")
    parser.add_argument("-Y", "--version-string", type=str, help="NJRat version string reported on initial callback.")
    parser.add_argument("-k", "--keylog-text", default="No keylogs are available at this time. Please try again later.", type=str, help="Text to send when keylogs are requested.")
    parser.add_argument("-K", "--initial-text", help="Opens the file specified in the keylog window on the C2 server upon connecting.")
    parser.add_argument("-j", "--av", default="No Antivirus", type=str, help="Antivirus reported on initial callback.")
    parser.add_argument("-e", "--chat-echo", action='store_true', help="Echo chat messages.")
    parser.add_argument("--non-interactive-chat", action='store_true', help="Do not opens the chat client in a new terminal window.")
    parser.add_argument("--disable-rdp", action='store_true', help="Disables the remote desktop module.")
    parser.add_argument("--disable-mic", action='store_true', help="Disables the microphone spying module.")
    parser.add_argument("--disable-cam", action='store_true', help="Disables the webcam spying module.")
    parser.add_argument("--disable-chat", action='store_true', help="Disables the chat module.")
    parser.add_argument("--version", action='version', version='%(prog)s 1.0')
    args = vars(parser.parse_args())

    if args["ver"] == "0.6.4":
        controller = NJController(NJ_064_ClientHandler, args, c=None)
    if args["ver"] == "0.7d":
        controller = NJController(NJ_07d_ClientHandler, args, c=None)
    if args["ver"] == "0.7dg":
        controller = NJController(NJ_07dg_ClientHandler, args, c=None)
    try:
        controller.start()
        controller._thread.join()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        #print(error)
