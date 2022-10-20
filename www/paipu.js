const paipuArr = []
let filteredPaipu = paipuArr

class Player {
    constructor(name) {
        this.name = name
        this.accum = 0
        this.gamePlayed = 0
        this.hakoshita = 0
        this.juni = [0,0,0,0]
    }

    juni_litsu(rank) {
        const sum = this.juni.reduce((pre, curr) => pre + curr)
        if (sum === 0)
            return 0.0
        else
            return this.juni[rank] / sum
    }
}

function renderPaipu() {
    // 需要重新计算总场次，总得失点等等
    $('table#paipu tr:not(:first)').empty()
    $('table#summary tr:not(:first)').empty()
    const playersMap = new Map()
    filteredPaipu.forEach(function(paipu) {
        const row = document.createElement('tr')
        for (let i = 0; i < 5; i++) {
            if (i === 0) {
                const time = paipu['time']
                $(row).append('<td><span class="time">' +
                    moment(time).format('YYYY-MM-DD HH:mm') +
                    '</span></td>')
            } else {
                const [name, score] = paipu['players'][i - 1]
                const td = document.createElement('td')
                const scoreSpan = document.createElement('span')
                $(scoreSpan).attr('class', 'score')
                $(scoreSpan).text(score)
                let player = playersMap.get(name)
                if (!player) {
                    player = new Player(name)
                    playersMap.set(name, player)
                }
                player.accum += (score - 25000)
                player.juni[i - 1]++
                player.gamePlayed++
                if (score < 0) {
                    player.hakoshita++
                    $(scoreSpan).attr('class', 'score-hakoshita')
                }
                $(td).append('<span>' + name + '</span>')
                $(td).append(scoreSpan)
                $(row).append(td)
            }
        }
        $('table#paipu').append(row)
    })

    playersMap.forEach(function(player) {
        const row = document.createElement('tr')
        // 玩家名
        $(row).append('<td>' + player.name + '</td>')
        // 总场次
        $(row).append('<td>' + player.gamePlayed + '</td>')
        // 总得失点
        $(row).append('<td>' + player.accum + '</td>')
        // 一位率~四位率
        for (let i = 0; i < 4; i++) {
            $(row).append('<td>' + (player.juni_litsu(i) * 100).toFixed(2) + '%</td>')
        }
        // 被飞次数
        $(row).append('<td>' + player.hakoshita + '</td>')
        $('table#summary').append(row)
    })
}

$(document).ready(function() {
    $('table#paipu tbody tr').each(function() {
        const row = {'players': []}
        $(this).children('td').each(function(i, item) {
            if (i === 0)
                row['time'] = new Date(item.innerText)
            else
                row['players'].push(Array.from($(item).children('span'),
                    (e, i) => i == 1 ? parseInt(e.innerText) : e.innerText)
                )
        })
        paipuArr.push(row)
    })
})

$('.date-selector button').click(function() {
    let startDate = $('#startdate').val()
    let endDate = $('#enddate').val()
    if (startDate && endDate) {
        startDate = new Date(startDate + 'T00:00')
        endDate = new Date(endDate + 'T00:00')
        filteredPaipu = paipuArr.filter(paipu => 
            paipu['time'] >= startDate && paipu['time'] <= endDate
        )
    } else {
        filteredPaipu = paipuArr
    }
    renderPaipu()
})
