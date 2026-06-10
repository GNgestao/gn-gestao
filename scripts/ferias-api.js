const http = require('http');
const { Pool } = require('pg');
const PORT = 5057;

const pool = new Pool({host:'172.18.0.4',port:5432,database:'evolution',user:'postgres',password:'evo123'});

const MESES = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];

function parseBody(req){
  return new Promise((resolve,reject)=>{
    let b=''; req.on('data',c=>b+=c); req.on('end',()=>{try{resolve(JSON.parse(b||'{}'))}catch(e){resolve({})}});
  });
}

async function listar(ano){
  const r = await pool.query('SELECT * FROM gestao_ferias WHERE ano=$1 ORDER BY mes,nome',[ano]);
  return r.rows;
}

async function salvar(d){
  const id = d.id || 'fe_'+Date.now();
  await pool.query(`INSERT INTO gestao_ferias (id,nome,ano,mes,inicio,fim,previsto,atualizado_em)
    VALUES ($1,$2,$3,$4,$5,$6,$7,NOW())
    ON CONFLICT (id) DO UPDATE SET nome=$2,ano=$3,mes=$4,inicio=$5,fim=$6,previsto=$7,atualizado_em=NOW()`,
    [id, d.nome, d.ano, d.mes, d.inicio||null, d.fim||null, d.previsto||false]);
  return {ok:true, id};
}

async function deletar(id){
  await pool.query('DELETE FROM gestao_ferias WHERE id=$1',[id]);
  return {ok:true};
}

async function buscarPorNome(nome, ano){
  const r = await pool.query('SELECT * FROM gestao_ferias WHERE LOWER(nome) LIKE LOWER($1) AND ano=$2',[`%${nome}%`, ano]);
  return r.rows;
}

const server = http.createServer(async (req,res)=>{
  const url = req.url.split('?')[0];
  const params = Object.fromEntries(new URLSearchParams(req.url.split('?')[1]||''));
  res.setHeader('Content-Type','application/json');
  try{
    if(req.method==='GET' && url==='/ferias'){
      const rows = await listar(parseInt(params.ano)||2026);
      res.writeHead(200); res.end(JSON.stringify(rows));
    } else if(req.method==='POST' && url==='/ferias'){
      const body = await parseBody(req);
      const r = await salvar(body);
      res.writeHead(200); res.end(JSON.stringify(r));
    } else if(req.method==='DELETE' && url==='/ferias'){
      const body = await parseBody(req);
      const r = await deletar(body.id);
      res.writeHead(200); res.end(JSON.stringify(r));
    } else if(req.method==='POST' && url==='/ferias/jarvis'){
      // Endpoint especial para o Jarvis — recebe linguagem natural processada
      const body = await parseBody(req);
      // body: {nome, inicio, fim, ano}
      const nome = body.nome;
      const ano = parseInt(body.ano) || new Date().getFullYear();
      const inicio = body.inicio; // formato YYYY-MM-DD
      const fim = body.fim;
      if(!nome||!inicio||!fim){res.writeHead(400);res.end(JSON.stringify({erro:'nome, inicio e fim obrigatorios'}));return;}
      const mesNum = new Date(inicio).getMonth()+1;
      const r = await salvar({nome, ano, mes:mesNum, inicio, fim, previsto:false});
      res.writeHead(200); res.end(JSON.stringify({...r, mensagem:`Férias de ${nome} programadas de ${inicio} a ${fim}`}));
    } else if(req.method==='GET' && url==='/ferias/buscar'){
      const rows = await buscarPorNome(params.nome||'', parseInt(params.ano)||2026);
      res.writeHead(200); res.end(JSON.stringify(rows));
    } else {
      res.writeHead(404); res.end(JSON.stringify({erro:'not found'}));
    }
  } catch(e){
    res.writeHead(500); res.end(JSON.stringify({erro:e.message}));
  }
});

server.listen(PORT,()=>console.log('Ferias API porta '+PORT));
