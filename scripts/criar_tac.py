import json, urllib.request, urllib.error, os

N8N_KEY = os.environ['N8N_KEY']
N8N_URL = "http://localhost:5678"

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

def wf_tac():
    return {
        "name": "Fluxo 1 - TAC Mobile",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "tac-mobile",
                    "responseMode": "responseNode",
                    "options": {}
                },
                "id": "55555555-5555-5555-5555-555555555501",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [240, 300],
                "webhookId": "tac-mobile"
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
                    "jsCode": (
                        "const jwt = $('Login Senior').first().json.token;\n"
                        "const body = $('Webhook').first().json.body;\n"
                        "return [{json: {jwt, ...body}}];"
                    )
                },
                "id": "55555555-5555-5555-5555-555555555503",
                "name": "Preparar Dados",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [680, 300]
            },
            {
                "parameters": {
                    "method": "GET",
                    "url": "=https://mobile.br.tkelevator.com/TKEMobile/api/tac",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "Authorization", "value": "={{ $json.jwt }}"},
                        {"name": "Content-Type", "value": "application/json"}
                    ]},
                    "sendQuery": True,
                    "queryParameters": {"parameters": [
                        {"name": "matricula", "value": "={{ $json.matricula }}"},
                        {"name": "data", "value": "={{ $json.data }}"}
                    ]},
                    "options": {}
                },
                "id": "55555555-5555-5555-5555-555555555504",
                "name": "Buscar TAC",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [900, 300]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ JSON.stringify($json) }}",
                    "options": {}
                },
                "id": "55555555-5555-5555-5555-555555555505",
                "name": "Responder",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [1120, 300]
            }
        ],
        "connections": {
            "Webhook": {"main": [[{"node": "Login Senior", "type": "main", "index": 0}]]},
            "Login Senior": {"main": [[{"node": "Preparar Dados", "type": "main", "index": 0}]]},
            "Preparar Dados": {"main": [[{"node": "Buscar TAC", "type": "main", "index": 0}]]},
            "Buscar TAC": {"main": [[{"node": "Responder", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1"}
    }

wid, err = criar(wf_tac())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
