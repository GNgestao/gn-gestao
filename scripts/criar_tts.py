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

def wf_tts():
    return {
        "name": "GN Text to Speech",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "gn-tts",
                    "responseMode": "responseNode",
                    "options": {}
                },
                "id": "22222222-2222-2222-2222-222222222201",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [240, 300],
                "webhookId": "gn-tts"
            },
            {
                "parameters": {
                    "jsCode": "const texto = $('Webhook').first().json.body.texto || '';\nconst limpo = texto.replace(/,/g, '.');\nreturn [{json:{texto: limpo}}];"
                },
                "id": "22222222-2222-2222-2222-222222222202",
                "name": "Tratar Texto",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [460, 300]
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "http://187.127.26.136:5050/v1/audio/speech",
                    "sendHeaders": True,
                    "headerParameters": {
                        "parameters": [
                            {"name": "Content-Type", "value": "application/json"}
                        ]
                    },
                    "sendBody": True,
                    "contentType": "raw",
                    "rawContentType": "application/json",
                    "body": "={\"model\":\"kokoro\",\"voice\":\"pm_alex\",\"input\":{{ JSON.stringify($json.texto) }},\"response_format\":\"wav\"}",
                    "options": {
                        "response": {
                            "response": {
                                "responseFormat": "file"
                            }
                        }
                    }
                },
                "id": "22222222-2222-2222-2222-222222222203",
                "name": "Kokoro TTS",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [680, 300]
            },
            {
                "parameters": {
                    "respondWith": "binary",
                    "options": {
                        "responseHeaders": {
                            "entries": [
                                {"name": "Content-Type", "value": "audio/wav"}
                            ]
                        }
                    }
                },
                "id": "22222222-2222-2222-2222-222222222204",
                "name": "Retornar Audio",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [900, 300]
            }
        ],
        "connections": {
            "Webhook": {"main": [[{"node": "Tratar Texto", "type": "main", "index": 0}]]},
            "Tratar Texto": {"main": [[{"node": "Kokoro TTS", "type": "main", "index": 0}]]},
            "Kokoro TTS": {"main": [[{"node": "Retornar Audio", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1"}
    }

wid, err = criar(wf_tts())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
