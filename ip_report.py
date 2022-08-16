import socket
import smtplib
from email.mime.text import MIMEText
import requests
import time
import os


def getIP() :
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try :
        s.connect(("baidu.com",12567))
        ip = s.getsockname()[0]
        s.close()
    except Exception :
        ip = "N/A"

    return ip

def read_ip() :
    try :
        with open(os.path.dirname(__file__)+"/ip.txt", "rb") as fi :
            content = fi.read()
        ip = content.decode("utf-8")
        return ip
    except :
        return 0

def save_ip(ip) :
    try :
        with open(os.path.dirname(__file__)+"/ip.txt", "wb") as fi :
            # print(os.path.dirname(__file__)+"ip.txt")
            fi.write(ip.encode("utf-8"))
    except :
        pass

def test_login(se) :
    try :
        content = se.get("http://baidu.com",timeout=5)
        if "baidu" in content.text :
            return True
        else :
            return False
    except :
        return False

def send_email(ip) :
    content = '''
    <!DOCTYPE html>
    <html>
        <head>
            <title>IP Report</title>
            <style type="text/css">
                html{
                    height: 100%%;
                    font-family: Roboto,Arial,Helvetica,sans-serif;
                    background-color: white;
                }
                body{
                    margin: 0px;
                    height: 100%%;
                }
                h1{
                    height: 15%%;
                    margin-top: 0;
                    margin-bottom: 5%%;
                    margin-right: 0;
                    margin-left: 0;
                    padding: 0px;
                    display: inline-block;
                }
                div#title-box{
                    padding-top: 40px;
                    padding-bottom: 40px;
                    margin-bottom: 20px;
                    background-color: #FF6347;
                    box-shadow: 0px 5px 4px -4px gray;
                }
                #title{
                    display: inline-block;
                    position: relative;
                    left: 50%%;
                    transform: translateX(-50%%);
                }
                .main{
                    display: inline-block;          
                }
                #content{
                    display: inline-block;
                    position: relative;
                    left: 50%%;
                    transform: translateX(-50%%);
                    padding-top: 50px;
                    padding-bottom: 50px;
                    padding-left: 15%%;
                    padding-right: 15%%;
                    background: #ededed;
                    box-shadow: 0px 5px 4px -4px gray;
                    border-radius: 5px;

                }

                div.label{
                    display: inline-block;
                    width: 70px;
                    font-weight: 700;
                }
                div.value{
                    display: inline-block;
                }

            </style>


        </head>
        <body>
            <div id="title-box">
            <div id="title">
                <h1>IP Report</h1>
            </div>
            </div>
            <div id="content">
                <div>
                    <p class="main">
                        <div class="label">IP</div>
                        <div class="value">%s</div>
                    </p>
                </div>

                <div>
                    <p class="main">
                        <div class="label">Time</div>
                        <div class="value">%s</div>
                    </p>
                </div>

                <div>
                    <p class="main">
                        <div class="label">From</div>
                        <div class="value">%s</div>
                    </p>
                </div>
            </div>
        </body>
    </html>


    '''

    user = "email sender address"
    code = "emial sender code"

    reciver = "email reciver"

    msg = MIMEText(content%(ip,time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), "Raspberry-Pi"), "html", "utf-8")
    msg["Subject"] = ip
    msg["From"] = user
    msg["To"] = reciver

    try :
        smtp = smtplib.SMTP_SSL("smtp.qq.com")
        smtp.login(user, code)
        smtp.sendmail(user, reciver, msg.as_string())
        smtp.quit()
    except Exception :
        print("send fail...")   

ip = getIP()
send_email(ip)
save_ip(ip)