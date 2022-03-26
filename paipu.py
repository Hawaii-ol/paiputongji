import json
import sys
import webbrowser
from jinja2 import Environment, FileSystemLoader

class Player:
    def __init__(self, name):
        self.juni = [0, 0, 0, 0]
        self.accum = 0
        self.games = 0
        self.hakoshita = 0
        self.name = name
    
    def juni_ritsu(self, rank):
        if sum(self.juni) == 0:
            return 0.0
        else:
            return self.juni[rank] / sum(self.juni)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = 'paipu.json'
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        players = {}
        for paipu in data:
            scoresum = 0
            rank_order = sorted(paipu['score'].items(), key = lambda t : -t[1])
            for rank, t_name_score in enumerate(rank_order):
                name, score = t_name_score
                scoresum += score
                if name not in players:
                    players[name] = Player(name)
                players[name].games += 1
                players[name].juni[rank] += 1
                players[name].accum += score - 25000
                if score < 0:
                    players[name].hakoshita += 1
            if scoresum != 100000:
                print(paipu)
                print('!!! sum=%d !!!' % scoresum)
        
        for player in players.values():
            print('玩家：%s' % player.name)
            print('总得失点：%d' % player.accum)
            print('一位率: %.2f%%' % (player.juni_ritsu(0) * 100))
            print("二位率: %.2f%%" % (player.juni_ritsu(1) * 100))
            print("三位率: %.2f%%" % (player.juni_ritsu(2) * 100))
            print("四位率: %.2f%%" % (player.juni_ritsu(3) * 100))
            print("被飞次数：%d" % player.hakoshita)
            print()
    
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('template.html')
        with open('index.html', 'w', encoding='utf-8') as html:
            html.write(template.render(data=data, players=players))
            webbrowser.open_new_tab('index.html')
