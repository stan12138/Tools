# -*- coding: utf-8 -*-
"""
desc: 这是一个简单的http文件服务器，目前只支持python3
    为什么要开发一个这样的文件服务器？主要原因是自带的文件服务器定制新的功能比较复杂
    例如：页面样式，自定义url处理，增加文件上传功能等
    另外，整体逻辑理解起来可能也比较困难，不如新写一个
doc: 
    Messenger: 对于socket的简单包装，支持了协议的读写，只支持http协议
    Page: 负责html页面的组装
    Server: http服务器，负责接收连接，调度client
    Application: 负责调度url，提供了一个类似于flask的url注册和处理方式
功能:
    path: /
    默认是一个文件服务器，会列出所在文件夹的全部文件
    path: /file
    是一个文件上传页面，支持文件上传，不要上传太大的文件，没做什么优化

author: 韩仪
time: 2021.6.5 10:59
todo: 
    增加日志？
    支持低版本python3, python2
    os.path.isdir不准确？重新写了检查文件夹的工具，依旧偶有发现不准确的 应该已经被修复了

"""

import time
import socket
import time
import sys
import selectors
import http.client
import os
import signal
import threading
import re
import mimetypes
import posixpath
import json
import urllib


__all__ = ["Messenger", "RecvNothing", "SendNothing", "EncodeError", "DecodeError", "NeedCLError", "HeaderFormatError", "PartnerCloseError"]



class RecvNothing(Exception): pass
# recv没有收到信息， 应该关闭

class SendNothing(Exception): pass
#send没有发出去消息，应该关闭

class EncodeError(Exception): pass
#content的编码错误，需要bytes，无须关闭

class DecodeError(Exception): pass
#解码错误，收到的数据的header解码错误，客户端有问题

class NeedCLError(Exception): pass
#客户端发送的数据缺少了CL字段

class HeaderFormatError(Exception): pass
#客户端的header解析错误，不满足键值对的要求

class PartnerCloseError(Exception): pass
#对方关闭了

class Page:
    """
    负责生成html
    """
    def __init__(self, max_num_one_line=4):
        self.max_num_one_line = max_num_one_line

    def page_frame(self): 
        frame1 = '''
            <!DOCTYPE html>
            <html>
                <head>
                    <title>测试</title>
                    <style type="text/css">
                        a:link { 
                            text-decoration: none;color: blue
                        }
                        ul li {
                            list-style-type: none;
                        }

                        .file {
                            background:#eee;
                            background:-moz-linear-gradient(top, #ddd 0, #eee 15%, #fff 40%, #fff 70%, #eee 100%);
                            background:-webkit-linear-gradient(top, #ddd 0, #eee 15%, #fff 40%, #fff 70%, #eee 100%);
                            border:1px solid #ccc;
                            -moz-border-radius:3px 15px 3px 3px;
                            -webkit-border-radius:3px 15px 3px 3px;
                            border-radius:3px 15px 3px 3px;
                            -moz-box-shadow:inset rgba(255,255,255,0.8) 0 1px 1px;
                            -webkit-box-shadow:inset rgba(255,255,255,0.8) 0 1px 1px;
                            box-shadow:inset rgba(255,255,255,0.8) 0 1px 1px;
                            display: inline-block;
                            width: 20px;
                            height: 25px;
                            position:relative;
                            text-indent:-9999em;
                            margin: 0px;
                            margin-left: 20px;
                        }
                        .file:before {
                            content: "";
                            position: absolute;
                            right:0;
                            width: 10px;
                            height: 10px;
                            background:#ccc;
                            background:-moz-linear-gradient(45deg, #fff 0,  #eee 50%, #ccc 100%);
                            background:-webkit-linear-gradient(45deg, #fff 0,  #eee 50%, #ccc 100%);
                            box-shadow:rgba(0,0,0,0.05) -1px 1px 1px, inset white 0 0 1px;
                            border-bottom:1px solid #ccc;
                            border-left:1px solid #ccc;
                            -moz-border-radius:0 14px 0 0;
                            -webkit-border-radius:0 14px 0 0;
                            border-radius:0 10px 0 0;
                        }

                        .file:after {
                            content:"";
                            display:block;
                            position:absolute;
                            left:0;
                            top:0;
                            width: 40%;
                            margin: 10px 20% 0;
                            background:#ccc;
                            background:-moz-linear-gradient(top, #ccc 0, #ccc 20%, #fff 20%, #fff 40%, #ccc 40%, #ccc 60%, #fff 60%, #fff 80%, #ccc 80%, #ccc 100%);
                            background:-webkit-linear-gradient(top, #ccc 0, #ccc 20%, #fff 20%, #fff 40%, #ccc 40%, #ccc 60%, #fff 60%, #fff 80%, #ccc 80%, #ccc 100%);
                            height: 8px;
                        }

                        .folder {
                            width: 30px;
                            height: 20px;
                            display: inline-block;
                            margin: 0px;
                            position: relative;
                            background-color: #708090;
                            border-radius: 0 3px 3px 3px;
                            /*box-shadow: 4px 4px 7px rgba(0, 0, 0, 0.59);*/
                            /*margin-bottom: -8px;*/
                            margin-top: 7px;
                            margin-left: 20px;
                        }
                        .folder:before {
                            content: "";
                            width: 50%;
                            height: 0.2em;
                            border-radius: 0 20px 0 0;
                            background-color: #708090;
                            position: absolute;
                            top: -0.2em;
                            left: 0px;
                        }
                        p {
                            margin: 0px;
                            margin-left: 20px;
                            margin-bottom: 50px;
                            max-width: 150px;
                            overflow: hidden;
                            white-space: nowrap;
                        }
                        .container {
                            display: flex;
                            height: 100%; width: 100%;
                            /*box-shadow: 0 0 0 1px black;*/
                        }
                        .item-area {
                            width: 150px;
                            text-align: center;
                        }
                    </style>
                </head>
                <body>
        '''
        frame2 = '''
                </body>
            </html>
        '''
        return frame1, frame2
    def page_section(self):
        section = '''
            <section class="container">
                %s
            </section>
        '''
        return section
    def page_file(self): 
        file = '''
        <div class="item-area">
            <a href="%s">
                <span><div class="file"></div></span>
                <p>%s</p>
            </a>
        </div>
        '''
        return file
    def page_folder(self): 
        folder = '''
            <div class="item-area">
                <a href="%s">
                    <span><div class="folder"></div></span>
                    <p>%s</p>
                </a>
            </div>
        '''
        return folder

    def get_name(self, name, is_dir=True): 
        """
        根据文件路径计算href和用来显示的名字
        """
        if is_dir:
            prefix = "/folders"
        else:
            prefix = "/files"
        # print(prefix)
        if "/" in name:
            # print(os.path.join("/files", name))
            href = os.path.join(prefix, name) if name[0]!="/" else prefix + name
            return href, name[-(name[-1::-1].index("/")):]
        else: 
            href = os.path.join(prefix, name) if name[0]!="/" else prefix + name
            return href, name

    def generate_page(self, folder, file):
        """
        根据文件和文件夹列表生成网页
        """
        # 生成一个上层文件夹的文件夹路径，名字指定为..
        item = None
        item = folder[0] if len(folder)>0 else file[0]
        last_dir = os.path.join(item, "../..")
        
        folder.sort()
        file.sort()
        folder = [last_dir] + folder
        frame1, frame2 = self.page_frame()
        folder_num = len(folder)
        file_num = len(file)
        num = 0
        res = ""
        section_content = ""
        for item in folder: 
            part = self.page_folder()
            name_info = self.get_name(item)
            if item == last_dir:
                # 在这里指定的上层文件夹的名字
                name_info = (name_info[0], "..")
            part = part%name_info
            section_content += part
            num += 1
            if num%self.max_num_one_line==0: 
                sec = self.page_section()
                sec = sec%section_content
                res += sec
                num = 0
                section_content = ""
        for item in file:
            part = self.page_file()
            part = part%self.get_name(item, False)
            section_content += part
            num += 1
            if num%self.max_num_one_line==0: 
                sec = self.page_section()
                sec = sec%section_content
                res += sec
                num = 0
                section_content = ""
        if num>0: 
            sec = self.page_section()
            sec = sec%section_content
            res += sec
            num = 0
            section_content = ""

        frame = frame1 + res + frame2

        return frame

class Messenger:
    """
    对socket的封装，自动完成http协议的解析，和response的构建
    """
    def __init__(self, selector, fileobj, addr): 

        self.socket = fileobj
        self.addr = addr

        self.recv_time = None
        self.send_time = None

        # self.header = None
        self.body = None

        self.__header_length = None

        self.__content_length = None

        self.env = {}

    def __read(self, fi, read_line=True, read_size=0): 
        """
        读取一定数据
        private
        """
        if read_line: 
            try:
                data = fi.readline(65537)
            except BlockingIOError:
                pass
            except ConnectionResetError: 
                raise PartnerCloseError("recv close, partner close(reset), should close")
        else:
            data = b''
            while len(data)<read_size: 
                try:
                    tmp_data = fi.read(read_size-len(data))
                    if tmp_data is not None and len(tmp_data)>0:
                        data += tmp_data
                except BlockingIOError:
                    pass
                except ConnectionResetError: 
                    raise PartnerCloseError("recv close, partner close(reset), should close")

        return data

    def __write(self, message): 
        """
        发送二进制消息
        private
        """

        while len(message)>0: 
            try: 
                l = self.socket.send(message)
            except BlockingIOError: 
                pass
            except ConnectionAbortedError: 
                raise PartnerCloseError("partner close "+str(self.addr[0])+" "+str(self.addr[1]))
            else: 
                if l<=0:
                    raise SendNothing("send nothing, should close")
                else :
                    message = message[l:]

    def __parse_first_line(self, first_line):
        requestline = first_line.decode('utf-8')
        requestline = requestline.rstrip('\r\n')
        words = requestline.split()
        if len(words)==3 :
            command,path,version = words
            self.env['method'] = command
            self.env['path'] = urllib.parse.unquote(path)
            self.env['version'] = version
        else:
            print(requestline)

    def __construct_message(self, status_code, header, content): 
        """
        构建消息
        private
        """
        if content:         
            if type(content) != bytes: 
                content = content.encode("utf-8")
            content_length = len(content)
        else: 
            content_length = 0

        code = bytes(status_code, "utf-8")
        frame = b'HTTP/1.1 ' + code + b'\r\n'
        header_frame = ""
        if "Content-Length" not in header: 
            header["Content-Length"] = str(content_length)
        for key in header: 
            header_frame += key + ": " + header[key] + "\r\n"
        
        frame += bytes(header_frame, "utf-8") + b'\r\n' 

        if content_length>0: 
            frame += content   

        return frame

    def read(self): 
        """
        读取数据
        供外部调用
        """
        self.env = {}
        self.body = None
        fi = self.socket.makefile("rb", -1)
        first_line = self.__read(fi, read_line=True)
        self.__parse_first_line(first_line)

        headers = http.client.parse_headers(fi,_class=http.client.HTTPMessage)
        for item in headers: 
            self.env[item] = headers.get(item, "")
        if "Content-Length" in self.env: 
            length = int(self.env["Content-Length"])
            if length>0: 
                body_data = self.__read(fi, read_line=False, read_size=length)
                self.body = body_data
        fi.close()

        self.recv_time = time.time()

    def send(self, status_code, header, content=None):
        data_frame = self.__construct_message(status_code, header, content)

        self.__write(data_frame)

        self.send_time = time.time()

    def process_read(self): 
        """
        处理读数据请求，供外部调用
        """
        self.read()


class Server :
    """
    http服务器，负责调度client
    """
    def __init__(self, ip, port) :

        self.addr = (ip, port)
        self.server = self.__generate_server()

        self.__selector = selectors.DefaultSelector()

        self.__selector.register(self.server, selectors.EVENT_READ, data=None)

        self.messenger = []

        self._lock = threading.Lock()

        signal.signal(signal.SIGINT, self.__interrupt_handler)

    def register_application(self, application): 
        self.app = application

    def detect_ip(self): 
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        try :
            s.connect(('baidu.com',80))
            ip = s.getsockname()[0]
            s.close()
        except :
            ip = 'N/A'
        return ip

    def __interrupt_handler(self, sig, frame): 
        """
        捕捉到ctr-c
        定义处理方式为关闭所有socket
        private
        """
        print("get stop signal......")
        for item in self.messenger: 
            self.__selector.unregister(item.socket)
            item.socket.close()
        self.__selector.unregister(self.server)
        self.server.close()

        print("close work done, bye~~~")
        sys.exit(0)

    def __generate_server(self) :
        """
        生成TCP服务器
        配置TCP服务器
        private
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(self.addr)
        sock.listen(20)

        sock.setblocking(False)

        return sock

    def __accept(self, sock): 
        """
        接受一个客户端的连接
        private
        """
        client, addr = sock.accept()
        print("get client:", addr)
        client.setblocking(False)

        message = Messenger(self.__selector, client, addr)

        self.__selector.register(client, selectors.EVENT_READ, data=message)

        self._lock.acquire()
        self.messenger.append(message)
        self._lock.release()

    def _listen(self) :
        """
        持续监听
        供外部调用，但是不希望被override
        """
        while True: 
            events = self.__selector.select(timeout=None)

            for key, mask in events:
                # print(key.data) 
                if key.data == None: 
                    self.__accept(key.fileobj)
                else: 
                    message = key.data
                    try:
                        message.process_read()
                    except PartnerCloseError:
                        self._close_client(message)
                    except RecvNothing:
                        self._close_client(message)
                    else:
                        self.process_read(message)

    def _close_client(self, message_of_client, need_lock=True): 
        """
        关闭一个客户端，可以选择是否需要使用锁，注意
        绝对不可以遍历self.messenger同时删除

        外部可以调用
        不要override
        """
        self.__selector.unregister(message_of_client.socket)
        if need_lock:
            self._lock.acquire()
            self.messenger.remove(message_of_client)
            self._lock.release()
        else: 
            self.messenger.remove(message_of_client)

        print("close one client:", len(self.messenger))

    def serve_forever(self): 
        """
        示范性自定义方法
        使用两个线程同时实现了listen和broadcast
        """
        run_thread = threading.Thread(target=self._listen, daemon=True)

        run_thread.start()

        ip = self.detect_ip()
        self.addr = (ip, self.addr[1])
        print("server waiting in: %s:%s"%self.addr)

        while True :
            pass

    def process_read(self, messenger): 
        if "path" not in messenger.env: 
            self._close_client(messenger)
            return
        response = self.app(messenger)
        if response: 
            status_code, header, content = response
            
        else:
            status_code = "404 Not Found"
            header = {}
            content = None
        messenger.send(status_code, header, content)

class Application: 
    """
    对url处理的简单封装，提供了类似flask的url handler注册方式
    """
    def __init__(self, content_type_map=None): 
        self.handler_record = {}
        self.content_type_map = {} if content_type_map is None else content_type_map

    def detect_content_type(self, filename): 
        content_type = None
        base, ext = posixpath.splitext(filename)
        if ext in self.content_type_map:
            content_type = self.content_type_map[ext]
        ext = ext.lower()
        if ext in self.content_type_map:
            content_type = self.content_type_map[ext]
        guess, _ = mimetypes.guess_type(filename)
        if guess:
            content_type = guess
        if ".ts" in filename or content_type is None:
            content_type = 'application/octet-stream'
        # print(content_type)

        return content_type

    def set_url(self, url, method='GET'): 
        def second(func): 
            if method in self.handler_record: 
                self.handler_record[method][url] = func
            else: 
                self.handler_record[method] = {url: func}
            return func
        return second

    def application(self, messenger): 
        env = messenger.env
        path = env['path']
        method = env['method']
        print(messenger.addr, method, path)
        if method in self.handler_record: 
            path_length = len(path)
            for path_handle in self.handler_record[method]: 
                match_res = re.match(path_handle, path)
                if match_res is not None:
                    if match_res.span()[1]==path_length:
                        content = self.handler_record[method][path_handle](messenger)
                        return content
                else:
                    # print("path_handle faile", path_handle, path)
                    pass
        else: 
            # print("without PATH: %s, Method: %s"%(env["path"], env["method"]), " handler")
            pass

    def run(self, host, port, dirname=None): 
        if dirname is None: 
            self.dirname = os.path.dirname(os.path.abspath("__FILE__"))
        else: 
            self.dirname = os.path.dirname(os.path.abspath(dirname))
        self.server = Server(host, port)
        self.server.register_application(self.application)
        self.server.serve_forever()

def list_dir(dirname): 
    """
    列出路径下的文件和文件夹，分开进入两个列表
    """
    res = os.listdir(dirname)
    res = [os.path.abspath(os.path.join(dirname,item)) for item in res]
    folders = [item for item in res if check_is_dir(item)]
    files = [item for item in res if item not in folders]
    return folders, files

def check_is_dir(name): 
    """
    检测一个路径是文件还是文件夹,os.path.isdir好像不准确
    """
    try: 
        with open(name, "rb") as fi: 
            return False
    except: 
        return True


# 对于某些太大的文件，浏览器预览不了，例如过大的json，此时可以在这里首先自行格式化，以提供稍好的视觉体验
def file_pretty(filename): 
    if filename[-5:] == ".json": 
        with open(filename, "r", encoding="utf-8") as fi: 
            content = json.loads(fi.read())
            content = json.dumps(content, indent=4, sort_keys=True, ensure_ascii=False)
    else:
        with open(filename, "rb") as fi:
            content = fi.read()
    return content

# 根据后缀指定对应的content_type，指导浏览器预览文件
# 高版本python可以自动猜测出，低版本的可能就依赖映射表了
content_type_map = {
    ".json": "application/json",
    ".xml": "application/xml",
    ".php": "text/php",
    ".py": "text/python",
    ".pdf": "application/pdf",
    ".md": "text/markdown"
}

app = Application(content_type_map)

# 参数决定了生成的网页，每一行最多放置多少个文件或文件夹
page = Page(9)

# 主页
@app.set_url("/")
def index(request): 
    folder, files = list_dir(app.dirname)
    html = page.generate_page(folder, files)
    with open("index.html", "w", encoding="utf-8") as fi: 
        fi.write(html)
    return "200 OK", {"Content-Type": "text/html; charset=utf-8", 'Connection': 'keep-alive'}, html

# 点击文件
@app.set_url("/files/.*")
def files(request): 
    filename = request.env["path"].replace("/files", "")
    content = file_pretty(filename)
    return "200 OK", {"Content-Type": "%s; charset=utf-8"%app.detect_content_type(filename), 'Connection': 'keep-alive'}, content

# 点击文件夹
@app.set_url("/folders/.*")
def folders(request): 
    folder, files = list_dir(request.env["path"].replace("/folders", ""))
    html = page.generate_page(folder, files)

    return "200 OK", {"Content-Type": "text/html; charset=utf-8", 'Connection': 'keep-alive'}, html

# 上传文件页面
@app.set_url("/file")
def index(request): 
    html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>upload</title>
        </head>
        <body>
            <form id="upload-form" action="/upload" method="post" enctype="multipart/form-data" >
            　　　<input type="file" id="upload" name="upload" /> <br />
            　　　<input type="submit" value="Upload" />
            </form>
        </body>
        </html>
    """
    return "200 OK", {"Content-Type": "text/html; charset=utf-8", 'Connection': 'keep-alive'}, html

# 文件上传到这
@app.set_url("/upload", method='POST')
def upload(request):
    parse_multi_part(request)

    return "302 Found", {"Location": "/"}, ""

# 只支持multipart/form-data格式的文件上传
def parse_multi_part(request): 
    header = request.env
    key = "multipart/form-data; boundary="
    if "Content-Type" not in header or key not in header["Content-Type"]:
        return False
    boundary = header["Content-Type"].replace(key, "")
    data = request.body
    files = data.split(b'--' + boundary.encode())
    files = [item for item in files if len(item)>0]
    for file in files:
        parts = file.split(b'\r\n\r\n')
        if len(parts)!=2:
            continue
        head, body = parts
        head = head.replace(b'\r\n', b'; ').replace(b'=', b': ').decode()
        head = {item.split(": ")[0]:item.split(": ")[1] for item in head.split("; ") if len(item)>1}
        if "filename" not in head:
            continue
        with open(head["filename"].replace('"', ''), "wb") as fi:
            fi.write(body)
    return True

if __name__ == '__main__':
    app.run("0.0.0.0", 8666)