import { onRequestPost, onRequestOptions } from './collect.js';
import { onRequestGet } from './admin.js';
import { handleSave } from './save.js';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/api/collect') {
      if (request.method === 'OPTIONS') return onRequestOptions();
      if (request.method === 'POST') return onRequestPost({ request, env });
      return new Response(null, { status: 405 });
    }
    if (url.pathname === '/api/save') return handleSave(request, env);
    if (url.pathname === '/api/admin') {
      if (request.method === 'GET') return onRequestGet({ request, env });
      return new Response(null, { status: 405 });
    }
    return env.ASSETS.fetch(request);
  },
};
