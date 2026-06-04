import json, urllib.request, urllib.error, os

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

js_montar_mensagem = """
const dados = $input.all();
const chamados = dados[0].json;

// Adaptar conforme estrutura real da API TK Mobile
const lista = Array.isArray(chamados) ? chamados : (chamados.data || chamados.chamados || []);

if (!lista || lista.length === 0) {
  return [{json: {mensagem: null}}];
}

let texto = `🔧 *Chamados em Aberto — TK Mobile*\\n`;
texto += `📅 ${new Date().toLocaleString('pt-BR', {timeZone: 'America/Recife'})}\\n\\n`;

lista.forEach((c, i) => {
  texto += `*${i+1}.* ${c.numero || c.id || ''}\\n`;
  texto += `📍 ${c.local || c.endereco || c.cliente || ''}\\n`;
  texto += `🔴 ${c.tipo || c.descricao || c.status || ''}\\n\\n`;
});

texto += `Total: *${lista.length} chamado(s)*`;

return [{json: {mensagem: texto, total: lista.length}}];
"""

def wf_tac_v2():
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
                    "url": "https://platform.senior.com.br/auth/LoginServlet",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "Content-Type", "value": "application/x-www-form-urlencoded"}
                    ]},
                    "sendBody": True,
                    "contentType": "form-urlencoded",
                    "bodyParameters": {"parameters": [
                        {"name": "username", "value": "10583194@thyssenkrupp.com"},
                        {"name": "password", "value": "Initpass*1"},
                        {"name": "tenantName", "value": "thyssenkrupp"}
                    ]},
                    "options": {}
                },
                "id": "55555555-5555-5555-5555-555555555502",
                "name": "Login Senior",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [460, 300]
            },
            {
                "parameters": {
                    "method": "GET",
                    "url": "https://mobile.br.tkelevator.com/TKEMobile/api/tac/abertos",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "Authorization", "value": "={{ $json.token }}"},
                        {"name": "Content-Type", "value": "application/json"}
                    ]},
                    "options": {}
                },
                "id": "55555555-5555-5555-5555-555555555503",
                "name": "Buscar Chamados",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [680, 300]
            },
            {
                "parameters": {"jsCode": js_montar_mensagem},
                "id": "55555555-5555-5555-5555-555555555504",
                "name": "Montar Mensagem",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [900, 300]
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
                "id": "55555555-5555-5555-5555-555555555505",
                "name": "Tem Chamados?",
                "type": "n8n-nodes-base.if",
                "typeVersion": 2,
                "position": [1120, 300]
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
                "id": "55555555-5555-5555-5555-555555555506",
                "name": "Enviar WhatsApp",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [1340, 200]
            }
        ],
        "connections": {
            "Cron 30min": {"main": [[{"node": "Login Senior", "type": "main", "index": 0}]]},
            "Login Senior": {"main": [[{"node": "Buscar Chamados", "type": "main", "index": 0}]]},
            "Buscar Chamados": {"main": [[{"node": "Montar Mensagem", "type": "main", "index": 0}]]},
            "Montar Mensagem": {"main": [[{"node": "Tem Chamados?", "type": "main", "index": 0}]]},
            "Tem Chamados?": {"main": [
                [{"node": "Enviar WhatsApp", "type": "main", "index": 0}],
                []
            ]}
        },
        "settings": {"executionOrder": "v1"}
    }

# Deletar versão antiga
deletar("LYOkVH2ubuF9IGle")
print("Fluxo antigo removido")

# Criar novo
wid, err = criar(wf_tac_v2())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
