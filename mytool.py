#!/usr/bin/env Python
# -*- coding: utf-8 -*-
import random,time,struct,binascii,urllib
import socket,urllib2,urllib3
import sys
reload(sys)
sys.setdefaultencoding('utf8')

class mytool(object):
    def __init__(self):
        pass
    def to_hex(self,tostr,num):
        '''
        接收字符串转化为指定位数16进制字符串\n
        tostr:要转化为16进制的10进制数字\n
        num: 要转化为的位数，不足会在前面加0到指定位数\n
        return: 转化后的16进制数，字符串类型\n
        '''

        s = str(hex(int(tostr)))
        s=s[2:]
        while len(s) < num:
            s = '0' + s
        return s
    def to_pack(self,data):
        '''
        接收组装好的16进制字符串，进行打包返回数据包\n
        data: 16进制字符串\n
        return:数据包
        '''
        str1 = ''
        str2 = ''
        data=str(data)
        while data:
            str1=data[0:2]
            s=int(str1,16)
            str2+=struct.pack('B',s)
            data=data[2:]
        return str2
    def send_data(self,tcplink,data):
        '''
        发送报文\n
        tcplink:tcp连接\n
        data:报文\n
        return:
        '''
        tcplink.send(self.to_pack(data))
    def receive_data(self,tcplink):
        '''
        接收报文\n
        tcplink: tcp连接\n
        return: 解码后的响应报文
        '''
        res=tcplink.recv(1024)
        return res.encode('hex')
    def tcp_link(self,HOST,PORT):
        '''
        建立tcp连接\n
        HOST:ip\n
        PORT: 端口\n
        return: tcp连接
        '''
        HOST=str(HOST)
        PORT=int(PORT)
        tcplink=socket.socket(socket.AF_INET,socket.SOCK_STREAM)      #定义socket类型，网络通信，TCP
        tcplink.connect((HOST,PORT))   #连接
        tcplink.settimeout(10)
        return tcplink
    def get_zc_data(self,mobile,deviceid,g):
        '''
        生成注册报文\n
        mobile:电话号码\n
        deviceid: 设备号\n
        g:已经处理的车牌号\n
        return:注册报文
        '''
        #省id+市id+制造商id+终端型号+终端id+车牌颜色+车辆标识（车牌）
        body=self.to_hex(13,4)+self.to_hex(1125,4)+self.to_hex(0,10)+self.to_hex(0,40)+deviceid+self.to_hex(1,2)+g
        le=len(body)/2
        head="0100"+self.to_hex(le,4)+"0"+str(mobile)+"0000"
        zc="7e"+head+body+"017e"
        return zc
    def get_jq_data(self,mobile,a):
        '''
        组装鉴权报文\n
        mobile: 手机号\n
        a: 注册时返回接收\n
        return: 鉴权报文
        '''
        a=str(a)
        a=a[32:-4]
        body=a
        le=len(body)/2
        head="0102"+self.to_hex(le,4)+"0"+str(mobile)+"0000"
        jq="7e"+head+body+'547e'
        return jq
    def get_gps_data(self,mobile,jin,wei,high,speed,totalmileage,fx=random.randint(0,359)):
        '''
        组装gps报文\n
        mobile:手机号\n
        jin: 经度\n
        wei: 纬度\n
        high: 高度\n
        speed:速度\n
        totalmileage:里程\n
        fx: 方向（1-360），不传就随机\n
        return: gps报文
        '''
        pl="00000000"
        zt='00000003'
        ti=str(time.strftime("%y%m%d%H%M%S",time.localtime()))
        ad=""
        body=pl+zt+self.to_hex(wei,8)+self.to_hex(jin,8)+self.to_hex(high,4)+self.to_hex(speed,4)+self.to_hex(fx,4)+ti+'0104'+self.to_hex(totalmileage,8)
        #包头指令id+消息头+校验包尾
        le=len(body)/2
        head="0200"+self.to_hex(le,4)+"0"+str(mobile)+"0000"
        gps=head+body+'54'
        s = gps
        str1 = ''
        while len(s):
            s1 = s[-2:]
            if s1 == '7d':
                s1 = '7d01'
            elif s1 == '7e':
                s1 = '7d02'
            else:
                s1 = s1
            str1 = s1 + str1
            s = s[:-2]
        gpsdata="7e" + str1 + "7e"
        return gpsdata

    def get_id(self,deviceid):
        '''
        处理车辆id\n
        deviceid:设备id\n
        return:转化后的id
        '''
        did=binascii.b2a_hex(str(deviceid))
        print str(did)
        return str(did)
    def get_vnum(self,ver):
        '''
        处理车牌号\n
        ver: 车牌号\n
        return: 处理后的车牌号
        '''
        g=str(ver)
        g1=g.decode('utf-8').encode('gbk')
        g2=binascii.b2a_hex(g1)
        print g2
        return str(g2)
    def close(self,tcplink):
        '''
        关闭tcp连接\n
        tcplink:tcp连接\n
        return:
        '''
        tcplink.close()
    def all_send(self,ip,port,deviceid,ver,mobile,times,sleeptime,jin,wei,high,speed,totalmileage,addjin,addwei,addtotalmileage):
        '''
        进行一次完整轨迹模拟，
        :param ip: ip
        :param port: 端口
        :param deviceid: 处理后的设备号
        :param ver: 处理后的车牌号
        :param mobile: 手机号
        :param times: 循环发送次数
        :param sleeptime: 每次发送间隔时间
        :param jin: 初始经度
        :param wei: 初始纬度
        :param high:高度
        :param speed:速度
        :param totalmileage:初始里程
        :param addjin:每次发送增加经度
        :param addwei:每次发送增加纬度
        :param addtotalmileage:每次发送里程增加量
        :return:
        '''
        HOST=str(ip)
        PORT=int(port)
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((HOST,PORT))
        s.settimeout(10)
        zcbw=self.get_zc_data(mobile,deviceid,ver)
        s.send(self.to_pack(zcbw))
        res=s.recv(1024)
        print '>'+res.encode('hex')
        a=str(res.encode('hex'))
        a=a[32:-4]
        time.sleep(1)
        jqbw=self.get_jq_data(mobile,a)
        s.send(self.to_pack(jqbw))
        res=s.recv(1024)
        print '>'+res.encode('hex')
        time.sleep(1)
        for i in range(0,int(times)):
            gpsbw=self.get_gps_data(mobile,jin,wei,high,speed,totalmileage)
            s.send(self.to_pack(gpsbw))
            res=s.recv(1024)
            print '>'+res.encode('hex')
            time.sleep(int(sleeptime))
            jin+=int(addjin)
            wei+=int(addwei)
            totalmileage+=int(addtotalmileage)
        s.close()
    def send_3(self,ip,port,zc,jq,gps):
        '''
        顺序发送3种报文，第三种循环5次\n
        ip:ip\n
        port:端口\n
        zc:报文1\n
        jq:报文2\n
        gps:报文3\n
        return:
        '''
        HOST=str(ip)
        PORT=int(port)
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((HOST,PORT))
        s.settimeout(10)
        s.send(self.to_pack(zc))
        time.sleep(1)
        s.send(self.to_pack(jq))
        time.sleep(1)
        for i in range(0,5):
            s.send(self.to_pack(gps))
            time.sleep(15)
        s.close()
    def send_1(self,ip,port,bw):
        '''
        发送数据，循环5次\n
        ip:ip\n
        port:端口\n
        bw:报文\n
        return:
        '''
        HOST=str(ip)
        PORT=int(port)
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((HOST,PORT))
        s.settimeout(10)
        s.send(bw)
        for i in range(0,5):
            s.send(bw)
            time.sleep(15)
        s.close()
    def send_udp(self,ip,port,bw):
        '''
        以udp协议发送数据，循环5次\n
        ip: ip\n
        port: 端口\n
        bw: 报文\n
        return:
        '''
        HOST=str(ip)
        PORT=int(port)
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        for i in range(1,5):
            s.sendto(self.to_pack(bw),(HOST,PORT))
            time.sleep(15)
        s.close()
    def load_parameter(self,name,path):
        str=open(path,'r')
        j=str.read()
        str.close()
        dict=eval(j)
        parameter=dict.get(name)
        return parameter
    def get_end_gps_data(self,mobile,jin,wei,high,speed,totalmileage,fx=random.randint(0,359)):
        '''
        组装acc关gps报文\n
        mobile:手机号\n
        jin: 经度\n
        wei: 纬度\n
        high: 高度\n
        speed:速度\n
        totalmileage:里程\n
        fx: 方向（1-360），不传就随机\n
        return: gps报文
        '''
        pl="00000000"
        zt='00000002'
        ti=str(time.strftime("%y%m%d%H%M%S",time.localtime()))
        ad=""
        #标志+状态+纬度+经度+高度+速度+方向+时间+附属信息标志+里程
        body=pl+zt+self.to_hex(wei,8)+self.to_hex(jin,8)+self.to_hex(high,4)+self.to_hex(speed,4)+self.to_hex(fx,4)+ti+'0104'+self.to_hex(totalmileage,8)
        #包头指令id+消息头+校验包尾
        le=len(body)/2
        head="0200"+self.to_hex(le,4)+"0"+str(mobile)+"0000"
        gps="7e"+head+body+'547e'
        return gps
    def read_html(self,url):
        html=urllib2.urlopen(str(url))
        html=html.read()
        return html
    def down_file(self,url,path,filename,filetype):
        url=str(url)
        name=str(path)+'/'+str(filename)+'.'+str(filetype)
        urllib.urlretrieve(url,name)











