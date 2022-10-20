import base64
import datetime
import json
import tkinter as tk
import paipu
from tkinter.filedialog import askopenfilename
from genprotobuf import generate_metafile, load_protobuf

MAJSOUL_RPCS = {
    '心跳包' : 'heatBeat',
    '获取牌谱列表' : 'fetchGameRecordList',
}

def majsoul_record_to_paipu(record):
    meta = record.config.meta
    paipu_json = {}
    # 友人场应该有room_id字段，且不为0
    if getattr(meta, 'room_id', 0) > 0:
        tm = datetime.datetime.fromtimestamp(record.end_time)
        paipu_json['time'] = tm.strftime("%Y-%m-%d %H:%M")
        paipu_json['score'] = {}
        seats = [None] * 4
        for account in record.accounts:
            seats[account.seat] = account
        for player in record.result.players:
            # part_point_1字段才是最后得分，total_point不知道是什么，可能是换算后的马点？
            score = player.part_point_1
            account = seats[player.seat]
            paipu_json['score'][account.nickname] = score
    return paipu_json

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    filename = askopenfilename(filetypes=[("HTTP Archieve Document", "*.har"), ("All files", "*.*")])

    paipu_list = []
    pb2 = load_protobuf()
    with open(filename, 'r', encoding='utf-8') as har:
        data = json.load(har)
        for entry in data['log']['entries']:
            wsmsg = entry.get('_webSocketMessages')
            if wsmsg:
                '''
                报文的首字节决定消息类型
                0x01 服务器主动推送的通知
                0x02 客户端请求
                0x03 服务器响应
                对于0x02和0x03类型的报文，第2~3字节是报文的id，确保请求和响应正确对应；第4字节起才是正文
                正文是定义在liqi.proto中的Wrapper类型消息
                '''
                msg_id2req = {}
                for msg in wsmsg:
                    wrapper = pb2.Wrapper()
                    raw = base64.b64decode(msg['data'])
                    if raw[0] == 0x1: # 推送报文
                        pass
                    elif raw[0] == 0x2: # 请求报文
                        msg_id = int.from_bytes(raw[1:3], byteorder='little')
                        wrapper.ParseFromString(raw[3:])
                        msg_id2req[msg_id] = wrapper
                    elif raw[0] == 0x3: # 响应报文
                        msg_id = int.from_bytes(raw[1:3], byteorder='little')
                        # 响应报文没有name，需要通过请求报文的id判断响应类型
                        res_wrapper = msg_id2req.pop(msg_id)
                        wrapper.ParseFromString(raw[3:])
                        '''
                        name形如：
                        .lq.Lobby.heatbeat
                        .lq.Lobby.oauth2Login
                        .lq.Lobby.fetchFriendList
                        通过尾部的RPC方法名查找liqi.proto中方法对应的返回类型
                        '''
                        rpcname = res_wrapper.name.split('.')[-1]
                        svc_descriptor = pb2.Lobby().GetDescriptor()
                        method_descriptor = svc_descriptor.methods_by_name[rpcname]
                        response_descriptor = method_descriptor.output_type
                        response = getattr(pb2, response_descriptor.name)()
                        response.ParseFromString(wrapper.data)
                        # 除了获取牌谱列表外，还有很多功能可供开发
                        if rpcname == MAJSOUL_RPCS['获取牌谱列表']:
                            for record in response.record_list:
                                paipu_json = majsoul_record_to_paipu(record)
                                if paipu_json:
                                    paipu_list.append(paipu_json)
                break
    if paipu_list:
        paipu.analyze(paipu_list)
    else:
        print('没有找到牌谱列表信息！')
