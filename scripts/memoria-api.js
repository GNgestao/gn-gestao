const http = require('http');
const https = require('https');
const { Pool } = require('pg');

const PORT = 5056;
const VOYAGE_KEY = 'pa-ETTEm-tehUgEhdHqfyuTGP8BJoHJqyTIlp56M2UQ9Rc';

const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'evolution',
  user: 'postgres',
  password: 'evo123'
});

function voyageReq(body) {
  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: 'api.voyageai.com',
      path: '/v1/embeddings',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + VOYAGE_KEY,
        'Content-Length': Buffer.byteLength(body)
      }
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        try { resolve(JSON.parse(d)); }
        catch(e) { reject(e); }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function getEmbedding(text) {
  const body = JSON.stringify({ model: 'voyage-3', input: [text] });
  const r = await voyageReq(body);
  if (!r.data || !r.data[0]) throw new Error('Embedding falhou: ' + JSON.stringify(r));
  return r.data[0].embedding;
}

async function salvar(conteudo, tipo) {
  const emb = await getEmbedding(conteudo);
  const embStr = '[' + emb.join(',') + ']';
  await pool.query(
    'INSERT INTO jarvis_memoria_v2 (conteudo, embedding, tipo) VALUES ($1, $2::vector, $3)',
    [conteudo, embStr, tipo || 'conversa']
  );
  return { ok: true };
}

async function buscar(query, limite) {
  const emb = await getEmbedding(query);
  const embStr = '[' + emb.join(',') + ']';
  const r = await pool.query(
    'SELECT conteudo, tipo, criado_em, 1 - (embedding <=> $1::vector) as sim FROM jarvis_memoria_v2 ORDER BY embedding <=> $1::vector LIMIT $2',
    [embStr, limite || 5]
  );
  return r.rows;
}

const server = http.createServer((req, res) => {
  let body = '';
  req.on('data', c => body += c);
  req.on('end', async () => {
    try {
      const d = body ? JSON.parse(body) : {};
      if (req.method === 'POST' && req.url === '/salvar') {
        const r = await salvar(d.conteudo, d.tipo);
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify(r));
      } else if (req.method === 'POST' && req.url === '/buscar') {
        const r = await buscar(d.query, d.limite);
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify(r));
      } else {
        res.writeHead(404); res.end();
      }
    } catch(e) {
      res.writeHead(500);
      res.end(JSON.stringify({erro: e.message}));
    }
  });
});

server.listen(PORT, () => console.log('Memoria API porta ' + PORT));
