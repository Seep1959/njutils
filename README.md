# njutils
usage: njclient.py [-h] [-i IMAGE] [-t THUMBNAIL] [-c CAM_IMAGE]
                   [-f FOREGROUND_WINDOW] [-n NAME] [-d DATE] [-o OS]
                   [-p PC_NAME] [-u USERNAME] [-y {0.6.4,0.7d,0.7dg}]
                   [-Y VERSION_STRING] [-k KEYLOG_TEXT] [-K INITIAL_TEXT]
                   [-j AV] [-e] [--non-interactive-chat] [--disable-rdp]
                   [--disable-mic] [--disable-cam] [--disable-chat]
                   [--version]
                   host port

positional arguments:
  host                  The IP/Domain of the njrat C2.
  port                  The port the njrat C2 is listening on.

optional arguments:
  -h, --help            show this help message and exit
  -i IMAGE, --image IMAGE
                        Image to send when remote desktop is requested.
  -t THUMBNAIL, --thumbnail THUMBNAIL
                        Image to send when screenshot is requested.
  -c CAM_IMAGE, --cam-image CAM_IMAGE
                        Image to send when remote cam is requested.
  -f FOREGROUND_WINDOW, --foreground-window FOREGROUND_WINDOW
                        Foreground window reported on initial callback.
  -n NAME, --name NAME  Name reported on initial callback.
  -d DATE, --date DATE  Install date reported on initial callback. format=YY-
                        MM-DD
  -o OS, --os OS        Operating system reported on initial callback.
  -p PC_NAME, --pc-name PC_NAME
                        PC name reported on initial callback.
  -u USERNAME, --username USERNAME
                        Username reported on inital callback.
  -y {0.6.4,0.7d,0.7dg}, --ver {0.6.4,0.7d,0.7dg}
                        Version of NJRat Server. 0.6.4, 0.7d, 0.7dg.
  -Y VERSION_STRING, --version-string VERSION_STRING
                        NJRat version string reported on initial callback.
  -k KEYLOG_TEXT, --keylog-text KEYLOG_TEXT
                        Text to send when keylogs are requested.
  -K INITIAL_TEXT, --initial-text INITIAL_TEXT
                        Opens the file specified in the keylog window on the
                        C2 server upon connecting.
  -j AV, --av AV        Antivirus reported on initial callback.
  -e, --chat-echo       Echo chat messages.
  --non-interactive-chat
                        Do not opens the chat client in a new terminal window.
  --disable-rdp         Disables the remote desktop module.
  --disable-mic         Disables the microphone spying module.
  --disable-cam         Disables the webcam spying module.
  --disable-chat        Disables the chat module.
  --version             show program's version number and exit


usage: njchat.py [-h] [-y {0.6.4,0.7d,0.7dg}] [-e] [-i IDENTIFIER]
                 [-r REPORTED_IP] [-p REPORTED_PORT] [--non-interactive-chat]
                 [--version]
                 host port

positional arguments:
  host                  The IP/Domain of the njrat C2.
  port                  The port the njrat C2 is listening on.

optional arguments:
  -h, --help            show this help message and exit
  -y {0.6.4,0.7d,0.7dg}, --ver {0.6.4,0.7d,0.7dg}
                        Version of NJRat Server. 0.6.4, 0.7d, 0.7dg.
  -e, --chat-echo       Echo chat messages.
  -i IDENTIFIER, --identifier IDENTIFIER
                        The full identifier used on initial callback for the
                        C2 to identify which client the chat session is
                        associated with
  -r REPORTED_IP, --reported-ip REPORTED_IP
                        The IP reported on initial callback for the C2 to
                        identify which client the chat session is associated
                        with
  -p REPORTED_PORT, --reported-port REPORTED_PORT
                        The port reported on initial callback for the C2 to
                        identify which client the chat session is associated
                        with
  --non-interactive-chat
                        Do not start cli UI
  --version             show program's version number and exit


./njclient.py 192.168.56.101 5552 -k "You won't find keylogs here" -u "5k1d d357r0y3r" -p "m41nfr4m3-3000" -f "TRACKING LOCATION - PREPARING DRONE STRIKE" -o "Mac OSX 9.9"

![NJRAT 0.7d callback](https://raw.githubusercontent.com/Seep1959/njutils/master/screenshots/callback.png)
![NJRAT 0.7d RDP/CAM/CHAT modules](https://raw.githubusercontent.com/Seep1959/njutils/master/screenshots/plugindemo.png)
![NJRAT 0.7d client](https://raw.githubusercontent.com/Seep1959/njutils/master/screenshots/client.png)
![NJRAT 0.7d chat client](https://raw.githubusercontent.com/Seep1959/njutils/master/screenshots/chat.png)

Use njclient.py -K option to open your l33t ascii art upon successfully connecting. Example:
./njclient.py 192.168.56.101 5553 -y0.7dg -K ascii/doge.txt
![NJRAT 0.7d golden edition ascc art](https://raw.githubusercontent.com/Seep1959/njutils/master/screenshots/ascii.png)
