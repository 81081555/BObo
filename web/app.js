const roomFromPath = location.pathname.startsWith('/room/') ? location.pathname.split('/')[2] : '';
let roomId = roomFromPath || new URLSearchParams(location.search).get('room') || '';
let playerId = localStorage.getItem('playerId') || '';

const $ = (id) => document.getElementById(id);
const setup = $('setup');
const play = $('play');

async function post(url, data) {
  const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || '请求失败');
  return json;
}

async function refreshState() {
  if (!roomId || !playerId) return;
  const res = await fetch(`/api/rooms/${roomId}/state?player_id=${encodeURIComponent(playerId)}`);
  if (!res.ok) return;
  const state = await res.json();
  setup.hidden = true;
  play.hidden = false;
  $('roomInfo').textContent = `房间: ${state.room_id} | 你: ${state.you.name} | 对手: ${state.opponent ? state.opponent.name : '等待加入...'}`;
  if (state.winner) {
    $('status').textContent = state.winner === playerId ? '你赢了 🎉' : '你输了';
  } else if (state.draw) {
    $('status').textContent = '平局';
  } else {
    $('status').textContent = state.submitted ? '已提交，等待对方...' : '请提交本回合猜测';
  }

  $('history').innerHTML = '';
  for (const item of state.rounds) {
    const li = document.createElement('li');
    const marks = item.colors.map((c) => `<span class="${c}">${c === 'green' ? '✓' : c === 'yellow' ? '△' : '✗'}</span>`).join(' ');
    li.innerHTML = `第 ${item.round_no} 回合：${item.guess} => ${marks}`;
    $('history').appendChild(li);
  }
}

$('createBtn').onclick = async () => {
  try {
    const data = await post('/api/rooms', {
      name: $('name').value,
      secret: $('secret').value,
      nonce: $('nonce').value,
      yellow_hint_enabled: $('yellow').checked,
    });
    roomId = data.room_id;
    playerId = data.player_id;
    localStorage.setItem('playerId', playerId);
    const shareUrl = `${location.origin}${data.share_url}`;
    $('share').textContent = `分享给微信好友：${shareUrl}`;
    if (navigator.share) {
      navigator.share({ title: '来玩猜数字对战', text: '点击链接加入房间', url: shareUrl }).catch(() => {});
    }
    history.replaceState(null, '', `/room/${roomId}`);
    refreshState();
  } catch (e) { alert(e.message); }
};

$('joinBtn').onclick = async () => {
  try {
    const targetRoom = $('roomId').value || roomId;
    const data = await post(`/api/rooms/${targetRoom}/join`, {
      name: $('name').value,
      secret: $('secret').value,
      nonce: $('nonce').value,
    });
    roomId = data.room_id;
    playerId = data.player_id;
    localStorage.setItem('playerId', playerId);
    history.replaceState(null, '', `/room/${roomId}`);
    refreshState();
  } catch (e) { alert(e.message); }
};

$('guessBtn').onclick = async () => {
  try {
    await post(`/api/rooms/${roomId}/guess`, { player_id: playerId, guess: $('guess').value });
    $('guess').value = '';
    refreshState();
  } catch (e) { alert(e.message); }
};

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}

setInterval(refreshState, 2000);
refreshState();
