// 集まったプレイ記録を見る画面。環境変数 ADMIN_PASS（パスワード）が必要。
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function authed(request, env) {
  const h = request.headers.get('Authorization') || '';
  if (!env.ADMIN_PASS || !h.startsWith('Basic ')) return false;
  try { const p = atob(h.slice(6)).split(':').slice(1).join(':'); return p === env.ADMIN_PASS; } catch (e) { return false; }
}

export async function onRequestGet({ request, env }) {
  if (!authed(request, env)) return new Response('パスワードが必要です', { status: 401, headers: { 'WWW-Authenticate': 'Basic realm="solo-siege"' } });
  if (!env.DB) return new Response('DBが未設定です（README参照）', { status: 500 });
  const url = new URL(request.url);
  const f = url.searchParams.get('f');
  if (f) {
    const r = await env.DB.prepare('SELECT data FROM runs WHERE id=?').bind(f).first();
    return new Response(r ? r.data : 'not found', { status: r ? 200 : 404, headers: { 'Content-Type': 'application/json; charset=utf-8' } });
  }
  if (url.searchParams.get('all')) {
    const { results } = await env.DB.prepare('SELECT data FROM runs ORDER BY received DESC').all();
    return new Response(results.map(x => x.data).join('\n') + '\n', { headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Content-Disposition': 'attachment; filename="solo-siege-logs.jsonl"' } });
  }
  const { results: rows } = await env.DB.prepare('SELECT id,pid,reason,character,stage,received,n,last_enemy FROM runs ORDER BY received DESC LIMIT 500').all();
  const win = rows.filter(r => r.reason === 'finalvictory').length;
  const lose = {};
  rows.filter(r => r.reason === 'hpzero').forEach(r => { const k = r.last_enemy || '?'; lose[k] = (lose[k] || 0) + 1; });
  const loseRows = Object.entries(lose).sort((a, b) => b[1] - a[1]).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${v}</td></tr>`).join('');
  const list = rows.map(r => `<tr><td><a href="?f=${encodeURIComponent(r.id)}">開く</a></td><td>${esc(r.received)}</td><td>${esc(r.pid)}</td><td>${esc(r.character)}</td><td>${esc(r.reason)}</td><td>${r.stage}</td><td>${r.n}</td><td>${esc(r.last_enemy)}</td></tr>`).join('');
  const html = `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SOLO SIEGE ログ</title>
<style>body{font:14px sans-serif;margin:16px}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:3px 7px}</style>
<h2>プレイ記録 ${rows.length}件（新しい500件まで） / クリア ${win}件</h2>
<p><a href="?all=1">全部ダウンロード（1行1件）</a></p>
<h3>負けた敵ランキング</h3><table>${loseRows}</table>
<h3>一覧（新しい順）</h3><table><tr><th></th><th>受信</th><th>ID</th><th>キャラ</th><th>終わり方</th><th>段</th><th>件数</th><th>最後の敵</th></tr>${list}</table>`;
  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
