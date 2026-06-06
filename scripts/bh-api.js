
const http = require('http');
const https = require('https');
const PORT = 5055;

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
  ["55007445","ADRIANO FRANCISCO DA SILVA"],
  ["55013039","ADRIANO ROGERIO BRAZ DA SILVA"],
  ["55016328","ALISSON MENDES CHAGAS"],
  ["55007813","ANTONIO AMARO BARRETO FILHO"],
  ["55006085","BRUNO DANILO FIRMINO DA SILVA"],
  ["55004902","DURVAL SILVA DE LIMA"],
  ["55010850","EDVALDO WILSON TEIXEIRA DE LIMA"],
  ["55016383","ELENILDO TEOFILO DE JESUS"],
  ["55015944","GEORGE BERNARDINO DA SILVA"],
  ["55018679","GILIARD FELIPE FIGUEIRA NASCIMENTO"],
  ["55013171","HUMBERTO JOSE DE LIMA"],
  ["55004915","JOAZ JOSE BEZERRA"],
  ["55018937","JOSE CHARLYTONBERG CORREA LINS"],
  ["55001880","KLEBSON ANDRADE DA SILVA"],
  ["55012621","KLEBSON RAMOS DA SILVA"],
  ["55012128","LAERCIO SIMIAO LUPERCINIO"],
  ["55012623","LUCIANO FELIX DOS SANTOS"],
  ["55015003","MARCELO DE BARROS ALMEIDA"],
  ["55015783","PAULO ANDRE LAURENTINO DE OLIVEIRA"],
  ["55000585","RODOLFO MARTINIANO DE S CAMPOS"],
  ["55012352","RODRIGO DE OLIVEIRA CUNHA"],
  ["55013040","WELLINGTON JOSE DO REGO BARRETO"],
  ["55021085","TONE GABRIEL DE ARAUJO MARQUES"],
  ["55019788","DIEGO ASSIS SANTOS DA ROCHA"]
];

function horasParaMinutos(h) {
  if (!h || h === '00:00') return 0;
  const neg = h.startsWith('-');
  const parts = h.replace('-','').split(':');
  const mins = parseInt(parts[0])*60 + parseInt(parts[1]);
  return neg ? -mins : mins;
}

async function consultarBH() {
  const loginBody = JSON.stringify({username:'10583194@thyssenkrupp.com',password:'Initpass1*',tenantName:'thyssenkrupp'});
  const loginR = await httpsReq({
    hostname:'platform.senior.com.br',
    path:'/t/senior.com.br/bridge/1.0/rest/platform/authentication/actions/login',
    method:'POST',
    headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(loginBody)}
  }, loginBody);
  const accessToken = JSON.parse(loginR.body.jsonToken).access_token;

  const g7R = await httpsReq({
    hostname:'web25.seniorcloud.com.br',port:31601,
    path:'/gestaoponto-backend/api/senior/auth/g7',
    method:'POST',
    headers:{'Content-Type':'application/json','token':accessToken,'expires':'604800','Content-Length':2}
  }, '{}');
  const assertion = g7R.body.token;

  const resultados = [];

  for (const [matricula, nome] of TECNICOS) {
    const colabId = '8550-1-' + matricula;
    try {
      const r = await httpsReq({
        hostname:'web25.seniorcloud.com.br',port:31601,
        path:'/gestaoponto-backend/api/colaborador/' + colabId + '/bancos-horas/saldo-mensal?codigoCalculo=1370&projecaoMeses=3&gestor=S',
        method:'GET',
        headers:{'assertion':assertion}
      });
      const saldo = r.body.saldoAtual || r.body.saldo || '00:00';
      resultados.push({nome, saldo, mins: horasParaMinutos(saldo)});
    } catch(e) {
      resultados.push({nome, saldo: '??:??', mins: -9999});
    }
  }

  resultados.sort((a,b) => b.mins - a.mins);

  const hoje = new Date().toLocaleDateString('pt-BR', {timeZone:'America/Recife'});
  let msg = '\u23F0 *Banco de Horas \u2014 GN Gest\u00e3o*\n' + hoje + '\n\n';
  resultados.forEach((r, i) => {
    const sinal = r.mins > 0 ? '\u2795' : r.mins < 0 ? '\u2796' : '\u25AA\uFE0F';
    msg += (i+1) + '. ' + r.nome + '\n   ' + sinal + ' ' + r.saldo + '\n';
  });

  return {mensagem: msg};
}

const server = http.createServer(async (req, res) => {
  if (req.method !== 'GET' || req.url !== '/bh') { res.writeHead(404); res.end(); return; }
  try {
    const result = await consultarBH();
    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify(result));
  } catch(e) {
    res.writeHead(500);
    res.end(JSON.stringify({erro: e.message}));
  }
});

server.listen(PORT, () => console.log('BH API na porta ' + PORT));
