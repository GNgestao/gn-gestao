import json, urllib.request, urllib.error, os

N8N_KEY = os.environ['N8N_KEY']
POSTGRES_ID = os.environ['POSTGRES_ID']
ANTHROPIC_KEY = os.environ['ANTHROPIC_KEY']
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

def wf_assistente():
    return {
        "name": "GN Assistente Inteligente",
        "nodes": [
            {
                "parameters": {"httpMethod": "POST", "path": "gn-assistente", "responseMode": "responseNode", "options": {}},
                "id": "11111111-1111-1111-1111-111111111101",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [240, 300],
                "webhookId": "gn-assistente"
            },
            {
                "parameters": {"operation": "executeQuery", "query": "SELECT role, conteudo FROM jarvis_memoria ORDER BY criado_em DESC LIMIT 20", "options": {}},
                "id": "11111111-1111-1111-1111-111111111102",
                "name": "Buscar Memoria",
                "type": "n8n-nodes-base.postgres",
                "typeVersion": 2.5,
                "position": [460, 300],
                "credentials": {"postgres": {"id": POSTGRES_ID, "name": "Conta Postgres"}}
            },
            {
                "parameters": {"jsCode": "const mem=$('Buscar Memoria').all();const cmd=$('Webhook').first().json.body.comando||'';const hist=[...mem].reverse().map(m=>({role:m.json.role,content:m.json.conteudo}));const sys='Voce e Jarvis, assistente de Gabriel Nascimento, Supervisor TK Elevator Recife. Chame de Chefe ou Senhor alternando. Respostas curtas em portugues sem markdown.';return [{json:{system:sys,historico:hist,comando:cmd}}];"},
                "id": "11111111-1111-1111-1111-111111111103",
                "name": "Montar Prompt",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [680, 300]
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "https://api.anthropic.com/v1/messages",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "x-api-key", "value": ANTHROPIC_KEY},
                        {"name": "anthropic-version", "value": "2023-06-01"},
                        {"name": "content-type", "value": "application/json"}
                    ]},
                    "sendBody": True,
                    "contentType": "raw",
                    "rawContentType": "application/json",
                    "body": "={\"model\":\"claude-sonnet-4-5\",\"max_tokens\":1024,\"system\":{{ JSON.stringify($json.system) }},\"messages\":{{ JSON.stringify([...$json.historico,{\"role\":\"user\",\"content\":$json.comando}]) }}}",
                    "options": {}
                },
                "id": "11111111-1111-1111-1111-111111111104",
                "name": "API Claude",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [900, 300]
            },
            {
                "parameters": {"jsCode": "const r=$json.content[0].text;const c=$('Montar Prompt').first().json.comando;return [{json:{resposta:r,comando:c}}];"},
                "id": "11111111-1111-1111-1111-111111111105",
                "name": "Extrair Resposta",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [1120, 300]
            },
            {
                "parameters": {"respondWith": "json", "responseBody": "={\"resposta\":{{ JSON.stringify($json.resposta) }}}", "options": {}},
                "id": "11111111-1111-1111-1111-111111111106",
                "name": "Responder ao Webhook",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [1340, 180]
            },
            {
                "parameters": {"operation": "executeQuery", "query": "=INSERT INTO jarvis_memoria (role, conteudo) VALUES ('user', '{{ $json.comando.replace(/'/g, \"''\") }}'), ('assistant', '{{ $json.resposta.replace(/'/g, \"''\") }}')", "options": {}},
                "id": "11111111-1111-1111-1111-111111111107",
                "name": "Salvar Memoria",
                "type": "n8n-nodes-base.postgres",
                "typeVersion": 2.5,
                "position": [1340, 420],
                "credentials": {"postgres": {"id": POSTGRES_ID, "name": "Conta Postgres"}}
            }
        ],
        "connections": {
            "Webhook": {"main": [[{"node": "Buscar Memoria", "type": "main", "index": 0}]]},
            "Buscar Memoria": {"main": [[{"node": "Montar Prompt", "type": "main", "index": 0}]]},
            "Montar Prompt": {"main": [[{"node": "API Claude", "type": "main", "index": 0}]]},
            "API Claude": {"main": [[{"node": "Extrair Resposta", "type": "main", "index": 0}]]},
            "Extrair Resposta": {"main": [
                [{"node": "Responder ao Webhook", "type": "main", "index": 0}],
                [{"node": "Salvar Memoria", "type": "main", "index": 0}]
            ]}
        },
        "settings": {"executionOrder": "v1"}
    }

wid, err = criar(wf_assistente())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
