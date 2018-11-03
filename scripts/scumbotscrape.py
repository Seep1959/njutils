#!/usr/bin/env python
import os
import re
import socket
import pprint
import nmap
import threading
from queue import Queue
from contextlib import closing
from struct import unpack
from socket import AF_INET, inet_pton
from twitterscraper import query_tweets

QUERY = "njRat found from%3AScumBots&src=typd"
PATTERN = 'tcp://(.*):(\d{1,5})'

def lookup(ip):
    f = unpack('!I',inet_pton(AF_INET,ip))[0]
    private = (
        [ 2130706432, 4278190080 ], # 127.0.0.0,   255.0.0.0   http://tools.ietf.org/html/rfc3330
        [ 3232235520, 4294901760 ], # 192.168.0.0, 255.255.0.0 http://tools.ietf.org/html/rfc1918
        [ 2886729728, 4293918720 ], # 172.16.0.0,  255.240.0.0 http://tools.ietf.org/html/rfc1918
        [ 167772160,  4278190080 ], # 10.0.0.0,    255.0.0.0   http://tools.ietf.org/html/rfc1918
    )
    for net in private:
        if (f & net[1]) == net[0]:
            return True
    return False

def is_ip(host):
    aa=re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",host)
    if aa:
        return True
    return False


def check_port(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(2)
        if sock.connect_ex((host,port)) == 0:
            return True
        else:
            return False

def get_hosts(query, count):
    njhosts = {}
    for tweet in query_tweets(QUERY, 400):
        text = tweet.text
        pattern = re.search(PATTERN, text, re.IGNORECASE)

        host = str(pattern.group(1).replace("[.]", '.')).lower()
        port = int(pattern.group(2))
        timestamp = tweet.timestamp.strftime('%m/%d/%Y')
        if ":" in host:
            host = host.split(":")[0] #easy fix

        if host not in njhosts:
            njhosts[host] = {
                    "ports": [port],
                    "open_ports": [],
                    "timestamps": [timestamp],
                    "seen": 1,
                    "routable": not (is_ip(host) and lookup(host))
                    }
        else:
            if port not in njhosts[host]["ports"]:
                njhosts[host]["ports"].append(port)
            if timestamp not in njhosts[host]["timestamps"]:
                njhosts[host]["timestamps"].append(timestamp)
            njhosts[host]["seen"] += 1
    return njhosts

def nmap_check_ports(host, ports, scan):
    scan = scan.format(','.join(map(str, ports)))
    open_ports = []
    nm = nmap.PortScanner()
    try:
        ip = nm.scan(hosts=host, arguments=scan)['scan'].keys()[0] #index is by ip even when scanning by fqdn
    except: #usually exception here means the domain doesn't point to any IP, should probably do better checks here but YOLO
        return open_ports
        #print("Exception: ", host)
    try:
        for port in nm[ip].all_tcp():
            if nm[ip]['tcp'][port]['state'] == 'open':
                open_ports.append(port)
    except:
        pass
        #print("Exception: ", host)
    return open_ports

def print_up_hosts(njhosts):
    for host, hostinfo in njhosts.iteritems():
        if hostinfo["open_ports"]:
            ports = ",".join("{0}".format(i) for i in hostinfo["open_ports"])
            print("{} {}".format(host, ports))

def scanner():
    while True:
        host = q.get()
        njhosts[host]["open_ports"] = nmap_check_ports(host, njhosts[host]["ports"], scan)
        q.task_done()



if __name__ == "__main__":
    #print("Getting tweets from scumbots")
    njhosts = get_hosts(QUERY, 400)
    #print ("Received bunch of tweets and shit")
    if os.geteuid() != 0:
        #print("No root, using tcp connect scan")
        scan = "-Pn -sT -p {}"
    else:
        #print("Have root, using tcp syn scan")
        scan = "-Pn -n -sS -p {}"

    #print(nmap_check_ports('8.8.8.8', [80,443,53], scan))
    #print(nmap_check_ports('www.google.com', [80,443,53], scan))

    q = Queue()
    for x in range(30):
        t = threading.Thread(target=scanner)
        t.daemon = True
        t.start()

    for host, hostinfo in njhosts.iteritems():
        if hostinfo["routable"]:
            q.put(host)
            #njhosts[host]["open_ports"] = nmap_check_ports(host, hostinfo["ports"], scan)
    q.join()
    #pprint.pprint(njhosts)
    print_up_hosts(njhosts)
