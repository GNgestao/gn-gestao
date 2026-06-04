import json, urllib.request, urllib.error, os, base64

N8N_KEY = os.environ['N8N_KEY']
N8N_URL = "http://localhost:5678"

def deletar(wid):
    req = urllib.request.Request(
        f"{N8N_URL}/api/v1/workflows/{wid}",
        headers={"X-N8N-API-KEY": N8N_KEY},
        method="DELETE"
    )
    try:
        urllib.request.urlopen(req)
        return True
    except:
        return False

def criar(wf):
    data = json.dumps(wf).encode()
    req = urllib.request.Request(
        f"{N8N_URL}/api/v1/workflows", data=data,
        headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read())
            return res.get('id'), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()

def ativar(wid):
    req = urllib.request.Request(
        f"{N8N_URL}/api/v1/workflows/{wid}/activate",
        headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"},
        method="POST"
    )
    try:
        urllib.request.urlopen(req)
        return True
    except:
        return False

usuario_b64 = base64.b64encode(b"PE2158").decode()
senha_b64 = base64.b64encode(b"Initpass1*").decode()

js_extrair_cookies = """
// Extrair cookies da resposta de login
const headers = $json.headers || {};
const setCookie = headers['set-cookie'] || '';
const cookies = Array.isArray(setCookie) ? setCookie.join('; ') : setCookie;

// Extrair valores relevantes
const sessionMatch = cookies.match(/ASP\\.NET_SessionId=([^;]+)/);
const loginMatch = cookies.match(/LOGIN=([^;]+)/);
const tkeMobileMatch = cookies.match(/TKEMobile=([^;]+)/);

const sessionId = sessionMatch ? sessionMatch[1] : '';
const login = loginMatch ? loginMatch[1] : '';
const tkeMobile = tkeMobileMatch ? tkeMobileMatch[1] : '';

const cookieStr = `ASP.NET_SessionId=${sessionId}; LOGIN=${login}; TKEMobile=${tkeMobile}`;

return [{json: {cookieStr}}];
"""

js_montar_mensagem = """
const body = $json;
const lista = Array.isArray(body) ? body : (body.d ? JSON.parse(body.d) : (body.data || body.chamados || []));

if (!lista || lista.length === 0) {
  return [{json: {mensagem: null}}];
}

let texto = '🔧 *Chamados em Aberto — TK Mobile*\\n';
texto += '📅 ' + new Date().toLocaleString('pt-BR', {timeZone: 'America/Recife'}) + '\\n\\n';

lista.forEach((c, i) => {
  texto += '*' + (i+1) + '.* ' + (c.Numero || c.numero || c.NumeroChamado || c.id || '') + '\\n';
  texto += '📍 ' + (c.Local || c.local || c.Endereco || c.endereco || c.Cliente || c.cliente || '') + '\\n';
  texto += '🔴 ' + (c.Tipo || c.tipo || c.Descricao || c.descricao || c.Status || c.status || '') + '\\n\\n';
});

texto += 'Total: *' + lista.length + ' chamado(s)*';

return [{json: {mensagem: texto, total: lista.length}}];
"""

def wf_tac_v3():
    return {
        "name": "Fluxo 1 - TAC Mobile",
        "nodes": [
            {
                "parameters": {
                    "rule": {"interval": [{"field": "cronExpression", "expression": "*/30 * * * *"}]}
                },
                "id": "55555555-5555-5555-5555-555555555501",
                "name": "Cron 30min",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [240, 300]
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "https://mobile.br.tkelevator.com/TKEMobile/Default.aspx/EfetuarLogin",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "Content-Type", "value": "application/json; charset=UTF-8"},
                        {"name": "X-Requested-With", "value": "XMLHttpRequest"},
                        {"name": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    ]},
                    "sendBody": True,
                    "contentType": "raw",
                    "rawContentType": "application/json",
                    "body": "{\"usuario\":\"" + usuario_b64 + "\",\"senha\":\"" + senha_b64 + "\"}",
                    "options": {
                        "response": {
                            "response": {
                                "fullResponse": True
                            }
                        }
                    }
                },
                "id": "55555555-5555-5555-5555-555555555502",
                "name": "Login TK Mobile",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [460, 300]
            },
            {
                "parameters": {"jsCode": js_extrair_cookies},
                "id": "55555555-5555-5555-5555-555555555503",
                "name": "Extrair Cookies",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [680, 300]
            },
            {
                "parameters": {
                    "method": "GET",
                    "url": "https://mobile.br.tkelevator.com/TKEMobile/Default.aspx/ObterChamadosAbertos",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "Cookie", "value": "={{ $json.cookieStr }}"},
                        {"name": "X-Requested-With", "value": "XMLHttpRequest"},
                        {"name": "Content-Type", "value": "application/json"},
                        {"name": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    ]},
                    "options": {}
                },
                "id": "55555555-5555-5555-5555-555555555504",
                "name": "Buscar Chamados",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [900, 300]
            },
            {
                "parameters": {"jsCode": js_montar_mensagem},
                "id": "55555555-5555-5555-5555-555555555505",
                "name": "Montar Mensagem",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [1120, 300]
            },
            {
                "parameters": {
                    "conditions": {
                        "options": {"caseSensitive": True},
                        "conditions": [
                            {
                                "leftValue": "={{ $json.mensagem }}",
                                "rightValue": "",
                                "operator": {"type": "string", "operation": "notEmpty"}
                            }
                        ]
                    }
                },
                "id": "55555555-5555-5555-5555-555555555506",
                "name": "Tem Chamados?",
                "type": "n8n-nodes-base.if",
                "typeVersion": 2,
                "position": [1340, 300]
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
                "id": "55555555-5555-5555-5555-555555555507",
                "name": "Enviar WhatsApp",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [1560, 200]
            }
        ],
        "connections": {
            "Cron 30min": {"main": [[{"node": "Login TK Mobile", "type": "main", "index": 0}]]},
            "Login TK Mobile": {"main": [[{"node": "Extrair Cookies", "type": "main", "index": 0}]]},
            "Extrair Cookies": {"main": [[{"node": "Buscar Chamados", "type": "main", "index": 0}]]},
            "Buscar Chamados": {"main": [[{"node": "Montar Mensagem", "type": "main", "index": 0}]]},
            "Montar Mensagem": {"main": [[{"node": "Tem Chamados?", "type": "main", "index": 0}]]},
            "Tem Chamados?": {"main": [
                [{"node": "Enviar WhatsApp", "type": "main", "index": 0}],
                []
            ]}
        },
        "settings": {"executionOrder": "v1"}
    }

deletar("LrwvcCowtAmztJIH")
print("Fluxo antigo removido")

wid, err = criar(wf_tac_v3())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
