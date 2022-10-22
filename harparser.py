import base64
import datetime
import json
import paipu
import sys
try:
    import tkinter as tk
    from tkinter.filedialog import askopenfilename
except Exception: # tkinter抛出的可能是自定义异常，不是ImportError
    tk = None
from genprotobuf import load_protobuf
from google.protobuf.json_format import MessageToJson

MAJSOUL_RPCS = {
    '心跳包' : 'heatBeat',
    'OAUTH2登录' : 'oauth2Login',
    '获取牌谱列表' : 'fetchGameRecordList',
}

def majsoul_record_to_paipu(record, account_id : int = None) -> dict:
    uuid = record.uuid
    if account_id:
        uuid += f'_a{paipu.encrypt_account_id(account_id)}'
    '''
    只统计四名人类玩家的友人场牌局，跳过三麻，AI玩家等
    GameConfig.category 1=友人场 2=段位场
    跳过修罗之战，血流换三张，瓦西子麻将等活动模式
    '''
    rule = record.config.mode.detail_rule
    if (record.config.category == 1 and
        len(record.accounts) == 4 and
        not rule.jiuchao_mode and # 瓦西子麻将
        not rule.muyu_mode and # 龙之目玉
        not rule.xuezhandaodi and # 修罗之战
        not rule.huansanzhang and # 换三张
        not rule.chuanma and # 川麻血战到底
        not rule.reveal_discard and # 暗夜之战
        not rule.field_spell_mode # 幻境传说
        ):
        tm = datetime.datetime.fromtimestamp(record.end_time)
        paipu_json = {
            'uuid' : uuid,
            'time' : tm.strftime("%Y-%m-%d %H:%M"),
            'score' : {},
        }
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
    if len(sys.argv) == 1 and tk:
        root = tk.Tk()
        root.withdraw()
        filename = askopenfilename(filetypes=[("HTTP Archieve Document", "*.har"), ("All files", "*.*")])
        if not filename:
            exit(0)
    elif len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        print('Usage: harparser.py [HAR file]')
        exit(0)

    with open(filename, 'r', encoding='utf-8') as har:
        paipu_list = []
        uuid_set = set()
        account_id = None
        nickname = None
        pb2 = load_protobuf()
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
                        # payload = MessageToJson(response)
                        # print(rpcname)
                        # print(payload)
                        if rpcname == MAJSOUL_RPCS['OAUTH2登录']:
                            account_id = response.account_id
                            nickname = response.account.nickname
                        elif rpcname == MAJSOUL_RPCS['获取牌谱列表']:
                            for record in response.record_list:
                                paipu_json = majsoul_record_to_paipu(record, account_id)
                                if paipu_json and paipu_json['uuid'] not in uuid_set:
                                    paipu_list.append(paipu_json)
                                    uuid_set.add(paipu_json['uuid'])
                        # TODO 除了获取牌谱列表外，还有很多功能可供开发
                break
        if paipu_list:
            paipu.analyze(paipu_list, nickname)
        else:
            print('没有找到牌谱列表信息！')
