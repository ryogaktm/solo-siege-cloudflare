// セーブデータの預かり（D1）。引き継ぎコードを知っている人だけが読み書きできる。
const MAX_BYTES = 300 * 1024;
const CODE_RE = /^[A-Z2-9]{12}$/;
const cors = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' };

async function ensure(DB) {
  await DB.prepare('CREATE TABLE IF NOT EXISTS saves (code TEXT PRIMARY KEY, data TEXT, updated TEXT)').run();
}

export async function handleSave(request, env) {
  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
  if (!env.DB) return new Response('no db', { status: 500, headers: cors });
  try {
    await ensure(env.DB);
    if (request.method === 'GET') {
      const code = (new URL(request.url).searchParams.get('code') || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
      if (!CODE_RE.test(code)) return new Response(null, { status: 400, headers: cors });
      const r = await env.DB.prepare('SELECT data FROM saves WHERE code=?').bind(code).first();
      if (!r) return new Response(null, { status: 404, headers: cors });
      return new Response(r.data, { status: 200, headers: { ...cors, 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
    }
    if (request.method === 'POST') {
      const raw = await request.text();
      if (raw.length < 5 || raw.length > MAX_BYTES) return new Response(null, { status: 413, headers: cors });
      let d; try { d = JSON.parse(raw); } catch (e) { return new Response(null, { status: 400, headers: cors }); }
      const code = String((d && d.code) || '').toUpperCase();
      if (!CODE_RE.test(code) || !d.kv || typeof d.kv !== 'object') return new Response(null, { status: 400, headers: cors });
      const prev = await env.DB.prepare('SELECT updated FROM saves WHERE code=?').bind(code).first();
      if (prev && Date.now() - Date.parse(prev.updated) < 5000) return new Response(null, { status: 429, headers: cors });
      await env.DB.prepare('INSERT OR REPLACE INTO saves (code,data,updated) VALUES (?,?,?)').bind(code, JSON.stringify(d.kv), new Date().toISOString()).run();
      return new Response(null, { status: 204, headers: cors });
    }
    return new Response(null, { status: 405, headers: cors });
  } catch (e) {
    return new Response(null, { status: 500, headers: cors });
  }
}
