import json, urllib.request, urllib.error, os, base64
from datetime import datetime

N8N_KEY = os.environ['N8N_KEY']
N8N_URL = "http://localhost:5678"

TECNICOS = [
    "55000153","55000585","55001880","55004902","55004915","55005485",
    "55006085","55007445","55007813","55010850","55012128","55012352",
    "55012621","55012623","55013039","55013040","55013171","55015003",
    "55015783","55015944","55016328","55016383","55018679","55018736",
    "55018937","55019049","55019550","55019560","55020261","55020770",
    "55021085"
]

def deletar(wid):
    req = urllib.request.Request(f"{N8N_URL}/api/v1/workflows/{wid}", headers={"X-N8N-API-KEY": N8N_KEY}, method="DELETE")
    try: urllib.request.urlopen(req); return True
    except: return False

def criar(wf):
    data = json.dumps(wf).encode()
    req = urllib.request.Request(f"{N8N_URL}/api/v1/workflows", data=data, headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as r: return json.loads(r.read()).get('id'), None
    except urllib.error.HTTPError as e: return None, e.read().decode()

def ativar(wid):
    req = urllib.request.Request(f"{N8N_URL}/api/v1/workflows/{wid}/activate", headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"}, method="POST")
    try: urllib.request.urlopen(req); return True
    except: return False

tecnicos_json = json.dumps(TECNICOS)

js_processar_he = f"""
const tecnicos = {tecnicos_json};
const hoje = new Date().toISOString().split('T')[0];

// Step 1: Login Senior
let tokenResp;
try {{
  tokenResp = await $http.request({{
    method: 'POST',
    url: 'https://platform.senior.com.br/t/senior.com.br/bridge/1.0/rest/platform/authentication/actions/login',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{username: '10583194@thyssenkrupp.com', password: 'Initpass*1', tenantName: 'thyssenkrupp'}}),
    returnFullResponse: false
  }});
}} catch(e) {{ return [{{json: {{erro: 'Login Senior falhou: ' + e.message}}}}]; }}

const accessToken = JSON.parse(tokenResp.jsonToken).access_token;

// Step 2: Auth g7
let g7Resp;
try {{
  g7Resp = await $http.request({{
    method: 'POST',
    url: 'https://web25.seniorcloud.com.br:31601/gestaoponto-backend/api/senior/auth/g7',
    headers: {{'Content-Type': 'application/json', 'token': accessToken, 'expires': '604800'}},
    body: '{{}}',
    returnFullResponse: false
  }});
}} catch(e) {{ return [{{json: {{erro: 'Auth g7 falhou: ' + e.message}}}}]; }}

const assertion = g7Resp.token;

// Step 3: Para cada tecnico, buscar HE do dia e autorizar se <= 2h
const resultados = [];

for (const numCad of tecnicos) {{
  const colabId = '8550-1-' + numCad;
  
  let ponto;
  try {{
    ponto = await $http.request({{
      method: 'GET',
      url: `https://web25.seniorcloud.com.br:31601/gestaoponto-backend/api/acertoPontoColaboradorPeriodo/colaborador/${{colabId}}?codigoCalculo=1370&dataFinal=${{hoje}}&dataInicial=${{hoje}}&filtraPendencias=GESTOR&gestor=S&orderby=-dataApuracao`,
      headers: {{'assertion': assertion}},
      returnFullResponse: false
    }});
  }} catch(e) {{ resultados.push({{numCad, erro: 'Consulta ponto falhou'}}); continue; }}

  const apuracoes = ponto.apuracao || [];
  if (!apuracoes.length) continue;

  for (const ap of apuracoes) {{
    if (ap.dataApuracao !== hoje) continue;

    const situacoesHE = ap.situacoesApuradas.filter(s => [613, 614].includes(s.situacao.codigo));
    if (!situacoesHE.length) continue;

    // Verificar se alguma HE > 2h
    let temHEAcima2h = false;
    for (const s of situacoesHE) {{
      const parts = s.quantidadeHoras.split(':');
      const mins = parseInt(parts[0]) * 60 + parseInt(parts[1]);
      if (mins > 120) {{ temHEAcima2h = true; break; }}
    }}

    if (temHEAcima2h) {{
      resultados.push({{numCad, status: 'IGNORADO - HE > 2h', data: hoje}});
      continue;
    }}

    // Montar payload de autorização
    const payload = ap.situacoesApuradas.map(s => {{
      const item = {{...s}};
      if (s.situacao.codigo === 613) {{
        item.situacao = {{codigo: 663, descricao: 'Hora Extra 60% Autorizada', excecao: false, id: '663', motivoAcertoObrigatorio: false, obrigatoriedadeAnexo: false, tipo: {{codigo: 17, descricao: 'Situação Apuração Ponto'}}}};
      }} else if (s.situacao.codigo === 614) {{
        item.situacao = {{codigo: 664, descricao: 'Hora Extra 60% Aut. Not', excecao: false, id: '664', motivoAcertoObrigatorio: false, obrigatoriedadeAnexo: false, tipo: {{codigo: 17, descricao: 'Situação Apuração Ponto'}}}};
      }}
      return item;
    }});

    const hashDB = encodeURIComponent(ap.hashDB);

    try {{
      await $http.request({{
        method: 'POST',
        url: `https://web25.seniorcloud.com.br:31601/gestaoponto-backend/api/colaboradores/${{colabId}}/apuracoes/${{hoje}}/situacoes-apuradas/lote?codigoCalculo=1370&gestor=S&hashDB=${{hashDB}}`,
        headers: {{'assertion': assertion, 'Content-Type': 'application/json'}},
        body: JSON.stringify(payload),
        returnFullResponse: false
      }});
      resultados.push({{numCad, status: 'AUTORIZADO', data: hoje}});
    }} catch(e) {{
      resultados.push({{numCad, status: 'ERRO ao autorizar: ' + e.message, data: hoje}});
    }}
  }}
}}

// Montar mensagem resumo
const autorizados = resultados.filter(r => r.status === 'AUTORIZADO').length;
const ignorados = resultados.filter(r => r.status && r.status.includes('IGNORADO')).length;
const erros = resultados.filter(r => r.status && r.status.includes('ERRO')).length;

const msg = '✅ *HE Autorização — GN Gestão*\\n' + hoje + '\\n\\n' +
  '✔️ Autorizados: ' + autorizados + '\\n' +
  '⚠️ Ignorados (>2h): ' + ignorados + '\\n' +
  (erros ? '❌ Erros: ' + erros + '\\n' : '') +
  '\\nTotal processados: ' + resultados.length;

return [{{json: {{mensagem: msg, detalhes: resultados}}}}];
"""

def wf_he_v2():
    return {
        "name": "Fluxo 2 - Autorizacao HE Senior",
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": "0 8 * * 1-5"}]}},
                "id": "66666666-6666-6666-6666-666666666601",
                "name": "Cron 8h seg-sex",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [240, 300]
            },
            {
                "parameters": {"jsCode": js_processar_he},
                "id": "66666666-6666-6666-6666-666666666602",
                "name": "Processar HE",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [460, 300]
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "http://187.127.26.136:8081/message/sendText/gn-whatsapp",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "apikey", "value": "gn-evolution-2026"},
                        {"name": "Content-Type", "value": "application/json"}
                    ]},
                    "sendBody": True,
                    "contentType": "raw",
                    "rawContentType": "application/json",
                    "body": "={\"number\":\"5581982381146\",\"textMessage\":{\"text\":{{ JSON.stringify($json.mensagem) }}}}",
                    "options": {}
                },
                "id": "66666666-6666-6666-6666-666666666603",
                "name": "Enviar WhatsApp",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [680, 300]
            }
        ],
        "connections": {
            "Cron 8h seg-sex": {"main": [[{"node": "Processar HE", "type": "main", "index": 0}]]},
            "Processar HE": {"main": [[{"node": "Enviar WhatsApp", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1"}
    }

deletar("1OsiYhDQKmzsyFB1")
print("Fluxo antigo removido")
wid, err = criar(wf_he_v2())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
