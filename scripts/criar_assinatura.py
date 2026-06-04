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

def wf_assinatura():
    return {
        "name": "GN Assinatura",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "gn-assinatura",
                    "responseMode": "responseNode",
                    "options": {}
                },
                "id": "77777777-7777-7777-7777-777777777701",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [240, 300],
                "webhookId": "gn-assinatura"
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "http://187.127.26.136:5052/assinar",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "Content-Type", "value": "application/json"}
                    ]},
                    "sendBody": True,
                    "contentType": "raw",
                    "rawContentType": "application/json",
                    "body": "={{ JSON.stringify($json.body) }}",
                    "options": {}
                },
                "id": "77777777-7777-7777-7777-777777777702",
                "name": "Autentique API",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [460, 300]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={{ JSON.stringify($json) }}",
                    "options": {}
                },
                "id": "77777777-7777-7777-7777-777777777703",
                "name": "Retornar Resultado",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [680, 300]
            }
        ],
        "connections": {
            "Webhook": {"main": [[{"node": "Autentique API", "type": "main", "index": 0}]]},
            "Autentique API": {"main": [[{"node": "Retornar Resultado", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1"}
    }

wid, err = criar(wf_assinatura())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
