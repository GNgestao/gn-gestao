import json, urllib.request, urllib.error, os, base64

N8N_KEY = os.environ['N8N_KEY']
N8N_URL = "http://localhost:5678"

def deletar(wid):
    req = urllib.request.Request(f"{N8N_URL}/api/v1/workflows/{wid}", headers={"X-N8N-API-KEY": N8N_KEY}, method="DELETE")
    try:
        urllib.request.urlopen(req)
        return True
    except:
        return False

def criar(wf):
    data = json.dumps(wf).encode()
    req = urllib.request.Request(f"{N8N_URL}/api/v1/workflows", data=data, headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read())
            return res.get('id'), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()

def ativar(wid):
    req = urllib.request.Request(f"{N8N_URL}/api/v1/workflows/{wid}/activate", headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req)
        return True
    except:
        return False

usuario_b64 = base64.b64encode(b"PE2158").decode()
senha_b64 = base64.b64encode(b"Initpass1*").decode()

js_montar_mensagem = """
const body = $json;
let lista = [];
try {
  const d = typeof body.d === 'string' ? JSON.parse(body.d) : body.d;
  lista = d.Response || [];
} catch(e) { lista = []; }

const agora = new Date().toLocaleString('pt-BR', {timeZone: 'America/Recife'});
const cab = '🔧 *OS ABERTAS — GN Gestão*\\n' + agora + '\\n\\n';

if (!lista || lista.length === 0) {
  return [{json: {mensagem: cab + '✅ Nenhuma OS aberta no momento.'}}];
}

let texto = cab;
lista.forEach((c, i) => {
  const num = c.Numero || '';
  const status = c.Status || '';
  const edificio = c.NomeEdificio || '';
  const elev = c.Equipamento || '';
  const apelido = c.Apelido ? (' (' + c.Apelido + ')') : '';
  const tec = c.NomeTecnico || 'Indefinido';
  const prior = c.Prioridade || '';
  const hora = c.DataHoraAbertura || '';
  const relato = c.Relato ? c.Relato.substring(0, 80) : '';
  texto += (i+1) + '. OS ' + num + ' — 🔴 ' + status + '\\n';
  texto += '🏢 ' + edificio + '\\n';
  texto += '🛗 Elevador: ' + elev + apelido + '\\n';
  texto += '👷 ' + tec + '\\n';
  texto += '⚡ Prioridade: ' + prior + ' | 🕐 ' + hora + '\\n';
  if (relato) texto += '📋 ' + relato + '\\n';
  texto += '\\n';
});
texto += 'Total: *' + lista.length + ' OS aberta(s)*';
return [{json: {mensagem: texto}}];
"""

def wf_tac_v9():
    return {
        "name": "Fluxo 1 - TAC Mobile",
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": "*/30 * * * *"}]}},
                "id": "55555555-5555-5555-5555-555555555501",
                "name": "Cron 30min",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [240, 300]
            },
            {
                "parameters": {
                    "command": "curl -s -c /tmp/tkcookies.txt -X POST 'https://mobile.br.tkelevator.com/TKEMobile/Default.aspx/EfetuarLogin' -H 'Content-Type: application/json; charset=UTF-8' -H 'X-Requested-With: XMLHttpRequest' -H 'User-Agent: Mozilla/5.0' -d '{\"usuario\":\"" + usuario_b64 + "\",\"senha\":\"" + senha_b64 + "\"}' && curl -s -b /tmp/tkcookies.txt -X POST 'https://mobile.br.tkelevator.com/TKEMobile/FormOSAberta.aspx/BuscarOsAberta' -H 'Content-Type: application/json; charset=UTF-8' -H 'X-Requested-With: XMLHttpRequest' -H 'User-Agent: Mozilla/5.0' -H 'Origin: https://mobile.br.tkelevator.com' -H 'Referer: https://mobile.br.tkelevator.com/TKEMobile/FormOSAberta.aspx' -d '{\"filial\":5008,\"zonas\":[3]}'"
                },
                "id": "55555555-5555-5555-5555-555555555502",
                "name": "Buscar OS via curl",
                "type": "n8n-nodes-base.executeCommand",
                "typeVersion": 1,
                "position": [460, 300]
            },
            {
                "parameters": {
                    "jsCode": "const output = $json.stdout || '';\nconst parts = output.split('{\"d\":\"{\\\\\"Response');\nconst jsonStr = parts.length > 1 ? '{\"d\":\"{\\\\\"Response' + parts[1] : output;\ntry {\n  const parsed = JSON.parse(jsonStr.trim());\n  return [{json: parsed}];\n} catch(e) {\n  const match = output.match(/\\{\"d\":\".*?(?=\"}$)/s);\n  if (match) return [{json: JSON.parse(match[0] + '\"}')}];\n  return [{json: {d: output}}];\n}"
                },
                "id": "55555555-5555-5555-5555-555555555503",
                "name": "Extrair JSON",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
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
                "id": "55555555-5555-5555-5555-555555555505",
                "name": "Enviar WhatsApp",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [1120, 300]
            }
        ],
        "connections": {
            "Cron 30min": {"main": [[{"node": "Buscar OS via curl", "type": "main", "index": 0}]]},
            "Buscar OS via curl": {"main": [[{"node": "Extrair JSON", "type": "main", "index": 0}]]},
            "Extrair JSON": {"main": [[{"node": "Montar Mensagem", "type": "main", "index": 0}]]},
            "Montar Mensagem": {"main": [[{"node": "Enviar WhatsApp", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1"}
    }

deletar("FmVIscaT8G6pt5bL")
print("Fluxo antigo removido")
wid, err = criar(wf_tac_v9())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
