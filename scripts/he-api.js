
const http = require('http');
const https = require('https');
const PORT = 5054;

function httpsReq(options, body) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve({body: JSON.parse(data), status: res.statusCode}); }
        catch(e) { resolve({body: data, status: res.statusCode}); }
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

const TECNICOS = [
  "55000153","55000585","55001880","55004902","55004915","55005485",
  "55006085","55007445","55007813","55010850","55012128","55012352",
  "55012621","55012623","55013039","55013040","55013171","55015003",
  "55015783","55015944","55016328","55016383","55018679","55018736",
  "55018937","55019049","55019550","55019560","55020261","55020770",
  "55021085"
];

async function processarHE() {
  const hoje = new Date().toISOString().split('T')[0];

  const loginBody = JSON.stringify({username:'10583194@thyssenkrupp.com',password:'Initpass*1',tenantName:'thyssenkrupp'});
  const loginR = await httpsReq({
    hostname:'platform.senior.com.br',
    path:'/t/senior.com.br/bridge/1.0/rest/platform/authentication/actions/login',
    method:'POST',
    headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(loginBody)}
  }, loginBody);
  const accessToken = JSON.parse(loginR.body.jsonToken).access_token;

  const g7Body = '{}';
  const g7R = await httpsReq({
    hostname:'web25.seniorcloud.com.br',port:31601,
    path:'/gestaoponto-backend/api/senior/auth/g7',
    method:'POST',
    headers:{'Content-Type':'application/json','token':accessToken,'expires':'604800','Content-Length':2}
  }, g7Body);
  const assertion = g7R.body.token;

  const resultados = [];

  for (const numCad of TECNICOS) {
    const colabId = '8550-1-' + numCad;
    try {
      const pontoR = await httpsReq({
        hostname:'web25.seniorcloud.com.br',port:31601,
        path:'/gestaoponto-backend/api/acertoPontoColaboradorPeriodo/colaborador/' + colabId + '?codigoCalculo=1370&dataFinal=' + hoje + '&dataInicial=' + hoje + '&filtraPendencias=GESTOR&gestor=S&orderby=-dataApuracao',
        method:'GET',
        headers:{'assertion':assertion}
      });

      const apuracoes = pontoR.body.apuracao || [];
      const ap = apuracoes.find(a => a.dataApuracao === hoje);
      if (!ap) continue;

      const situacoesHE = ap.situacoesApuradas.filter(s => [613,614].includes(s.situacao.codigo));
      if (!situacoesHE.length) continue;

      let temAcima2h = false;
      for (const s of situacoesHE) {
        const parts = s.quantidadeHoras.split(':');
        const mins = parseInt(parts[0])*60 + parseInt(parts[1]);
        if (mins > 120) { temAcima2h = true; break; }
      }

      if (temAcima2h) { resultados.push({numCad, status:'IGNORADO >2h'}); continue; }

      const payload = ap.situacoesApuradas.map(s => {
        const item = JSON.parse(JSON.stringify(s));
        if (s.situacao.codigo === 613) {
          item.situacao = {codigo:663,descricao:'Hora Extra 60% Autorizada',excecao:false,id:'663',motivoAcertoObrigatorio:false,obrigatoriedadeAnexo:false};
        } else if (s.situacao.codigo === 614) {
          item.situacao = {codigo:664,descricao:'Hora Extra 60% Aut. Not',excecao:false,id:'664',motivoAcertoObrigatorio:false,obrigatoriedadeAnexo:false};
        }
        return item;
      });

      const hashDB = encodeURIComponent(ap.hashDB);
      const payloadStr = JSON.stringify(payload);
      const authR = await httpsReq({
        hostname:'web25.seniorcloud.com.br',port:31601,
        path:'/gestaoponto-backend/api/colaboradores/' + colabId + '/apuracoes/' + hoje + '/situacoes-apuradas/lote?codigoCalculo=1370&gestor=S&hashDB=' + hashDB,
        method:'POST',
        headers:{'assertion':assertion,'Content-Type':'application/json','Content-Length':Buffer.byteLength(payloadStr)}
      }, payloadStr);

      if (authR.status === 200) resultados.push({numCad, status:'AUTORIZADO'});
      else resultados.push({numCad, status:'ERRO '+authR.status});

    } catch(e) {
      resultados.push({numCad, status:'ERRO: '+e.message});
    }
  }

  const aut = resultados.filter(r => r.status === 'AUTORIZADO').length;
  const ign = resultados.filter(r => r.status && r.status.includes('IGNORADO')).length;
  const err = resultados.filter(r => r.status && r.status.includes('ERRO')).length;

  const msg = '\u2705 *HE Autorizacao \u2014 GN Gestao*\n' + hoje + '\n\n' +
    '\u2714\uFE0F Autorizados: ' + aut + '\n' +
    '\u26A0\uFE0F Ignorados (>2h): ' + ign + '\n' +
    (err ? '\u274C Erros: ' + err + '\n' : '') +
    '\nTotal: ' + resultados.length;

  return {mensagem: msg, detalhes: resultados};
}

const server = http.createServer(async (req, res) => {
  if (req.method !== 'GET' || req.url !== '/he') { res.writeHead(404); res.end(); return; }
  try {
    const result = await processarHE();
    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify(result));
  } catch(e) {
    res.writeHead(500);
    res.end(JSON.stringify({erro: e.message}));
  }
});

server.listen(PORT, () => console.log('HE API na porta ' + PORT));
