// プレイ記録の受け取り（Cloudflare Pages Functions + D1）。個人情報は受け取らない。
const MAX_BYTES = 800 * 1024;      // 1回の送信の上限
const MAX_PER_PID_HOUR = 60;       // 同じIDが1時間に送れる回数
const MAX_ALL_HOUR = 3000;         // 全体で1時間に受け取る回数

export async function ensureTable(DB) {
  await DB.prepare(`CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY, pid TEXT, run TEXT, reason TEXT, character TEXT, stage INTEGER,
    received TEXT, n INTEGER, last_enemy TEXT, data TEXT)`).run();
  await DB.prepare('CREATE INDEX IF NOT EXISTS runs_received ON runs(received)').run();
}

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' } });
}

export async function onRequestPost({ request, env }) {
  const cors = { 'Access-Control-Allow-Origin': '*' };
  try {
    if (!env.DB) return new Response('no db', { status: 500, headers: cors });
    const raw = await request.text();
    if (raw.length < 20 || raw.length > MAX_BYTES) return new Response(null, { status: 413, headers: cors });
    let d; try { d = JSON.parse(raw); } catch (e) { return new Response(null, { status: 400, headers: cors }); }
    if (!d || typeof d !== 'object' || !Array.isArray(d.entries)) return new Response(null, { status: 400, headers: cors });
    const pid = String(d.pid || '').toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 24);
    if (!pid) return new Response(null, { status: 400, headers: cors });
    const reason = String(d.reason || 'x').toLowerCase().replace(/[^a-z]/g, '').slice(0, 16);
    const runKey = String(d.run || '').replace(/[^0-9A-Za-z:.\-]/g, '').slice(0, 40);

    await ensureTable(env.DB);
    const since = new Date(Date.now() - 3600 * 1000).toISOString();
    const a = await env.DB.prepare('SELECT COUNT(*) c FROM runs WHERE pid=? AND received>?').bind(pid, since).first();
    if (a && a.c >= MAX_PER_PID_HOUR) return new Response(null, { status: 429, headers: cors });
    const b = await env.DB.prepare('SELECT COUNT(*) c FROM runs WHERE received>?').bind(since).first();
    if (b && b.c >= MAX_ALL_HOUR) return new Response(null, { status: 429, headers: cors });

    const entries = d.entries.slice(-1000);
    let last = '';
    for (let i = entries.length - 1; i >= 0; i--) { const s = entries[i] && entries[i].state; if (s && s.eName) { last = String(s.eName).slice(0, 40); break; } }
    const id = `${pid}_${runKey}_${reason}`;
    const data = JSON.stringify({ v: 1, pid, run: runKey, reason, character: String(d.character || '').slice(0, 32), stage: Number(d.stage) || 0, ua: String(d.ua || '').slice(0, 200), entries });
    await env.DB.prepare('INSERT OR REPLACE INTO runs (id,pid,run,reason,character,stage,received,n,last_enemy,data) VALUES (?,?,?,?,?,?,?,?,?,?)')
      .bind(id, pid, runKey, reason, String(d.character || '').slice(0, 32), Number(d.stage) || 0, new Date().toISOString(), entries.length, last, data).run();
    return new Response(null, { status: 204, headers: cors });
  } catch (e) {
    return new Response(null, { status: 500, headers: cors });
  }
}
