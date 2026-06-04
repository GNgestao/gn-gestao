import json, urllib.request, urllib.error, os

N8N_KEY = os.environ['N8N_KEY']
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

def wf_documentos():
    return {
        "name": "GN Documentos",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "gn-documentos",
                    "responseMode": "responseNode",
                    "options": {}
                },
                "id": "66666666-6666-6666-6666-666666666601",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [240, 300],
                "webhookId": "gn-documentos"
            },
            {
                "parameters": {
                    "jsCode": (
                        "const body = $('Webhook').first().json.body;\n"
                        "const tipo = body.tipo || 'carta';\n"
                        "const titulo = body.titulo || '';\n"
                        "const cliente = body.cliente || '';\n"
                        "const endereco = body.endereco || '';\n"
                        "const detalhes = body.detalhes || '';\n"
                        "\n"
                        "let prompt = '';\n"
                        "if (tipo === 'carta') {\n"
                        "  prompt = `Gere uma carta tecnica profissional da TK Elevator com os seguintes dados:\\n"
                        "Titulo: ${titulo}\\nCliente: ${cliente}\\nEndereco: ${endereco}\\nDetalhes: ${detalhes}\\n\\n"
                        "Formato HTML. Cabecalho com logo TKE no canto superior direito. Bloco AO a esquerda. "
                        "Ref centralizada em italico. Saudacao Prezado Cliente. Corpo justificado. "
                        "Assinatura: Gabriel Nascimento / Supervisor de Servicos - TK Elevator. "
                        "Rodape apenas TK Elevator. Sem data de geracao.`;\n"
                        "} else if (tipo === 'ata') {\n"
                        "  prompt = `Gere uma ata de reuniao profissional com os seguintes dados:\\n${detalhes}\\n\\n"
                        "Formato HTML profissional com cabecalho TK Elevator.`;\n"
                        "}\n"
                        "return [{json: {prompt, tipo, titulo, cliente, endereco, detalhes}}];"
                    )
                },
                "id": "66666666-6666-6666-6666-666666666602",
                "name": "Preparar Prompt",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [460, 300]
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
                    "body": "={\"model\":\"claude-sonnet-4-5\",\"max_tokens\":4096,\"messages\":[{\"role\":\"user\",\"content\":{{ JSON.stringify($json.prompt) }}}]}",
                    "options": {}
                },
                "id": "66666666-6666-6666-6666-666666666603",
                "name": "API Claude",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [680, 300]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": "={\"html\":{{ JSON.stringify($json.content[0].text) }}}",
                    "options": {}
                },
                "id": "66666666-6666-6666-6666-666666666604",
                "name": "Retornar Documento",
                "type": "n8n-nodes-base.respondToWebhook",
                "typeVersion": 1.1,
                "position": [900, 300]
            }
        ],
        "connections": {
            "Webhook": {"main": [[{"node": "Preparar Prompt", "type": "main", "index": 0}]]},
            "Preparar Prompt": {"main": [[{"node": "API Claude", "type": "main", "index": 0}]]},
            "API Claude": {"main": [[{"node": "Retornar Documento", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1"}
    }

wid, err = criar(wf_documentos())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
