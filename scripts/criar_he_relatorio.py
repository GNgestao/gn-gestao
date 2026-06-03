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

TECNICOS = [
    ("55007445","ADRIANO FRANCISCO DA SILVA"),("55013039","ADRIANO ROGERIO BRAZ DA SILVA"),
    ("55016328","ALISSON MENDES CHAGAS"),("55007813","ANTONIO AMARO BARRETO FILHO"),
    ("55006085","BRUNO DANILO FIRMINO DA SILVA"),("55004902","DURVAL SILVA DE LIMA"),
    ("55010850","EDVALDO WILSON TEIXEIRA DE LIMA"),("55016383","ELENILDO TEOFILO DE JESUS"),
    ("55015944","GEORGE BERNARDINO DA SILVA"),("55018679","GILIARD FELIPE FIGUEIRA NASCIMENTO"),
    ("55013171","HUMBERTO JOSE DE LIMA"),("55004915","JOAZ JOSE BEZERRA"),
    ("55018937","JOSE CHARLYTONBERG CORREA LINS"),("55001880","KLEBSON ANDRADE DA SILVA"),
    ("55012621","KLEBSON RAMOS DA SILVA"),("55012128","LAERCIO SIMIAO LUPERCINIO"),
    ("55012623","LUCIANO FELIX DOS SANTOS"),("55015003","MARCELO DE BARROS ALMEIDA"),
    ("55000153","MOISES SEVERINO DA SILVA"),("55015783","PAULO ANDRE LAURENTINO DE OLIVEIRA"),
    ("55000585","RODOLFO MARTINIANO DE S CAMPOS"),("55012352","RODRIGO DE OLIVEIRA CUNHA"),
    ("55021085","TONE GABRIEL DE ARAUJO MARQUES"),("55013040","WELLINGTON JOSE DO REGO BARRETO")
]

js_preparar = """
const jwt = $('Login Senior').first().json.token;
const hoje = new Date();
const inicioSemana = new Date(hoje);
inicioSemana.setDate(hoje.getDate() - hoje.getDay() + 1);
const fimSemana = new Date(hoje);

const fmt = d => {
  const dd = String(d.getDate()).padStart(2,'0');
  const mm = String(d.getMonth()+1).padStart(2,'0');
  const yyyy = d.getFullYear();
  return `${yyyy}-${mm}-${dd}`;
};

const tecnicos = """ + json.dumps(TECNICOS) + """;
return tecnicos.map(([mat, nome]) => ({
  json: {jwt, matricula: mat, nome, startdate: fmt(inicioSemana), enddate: fmt(fimSemana), empresa: '8550-1', codigocalculo: '1370'}
}));
"""

js_montar_relatorio = """
const itens = $input.all();
let linhas = '';
let totalMinutos = 0;

for (const item of itens) {
  const d = item.json;
  const saldo = d.saldoMinutos || 0;
  totalMinutos += saldo;
  const h = Math.floor(Math.abs(saldo)/60);
  const m = Math.abs(saldo)%60;
  const sinal = saldo < 0 ? '-' : '';
  linhas += `${d.nome}: ${sinal}${h}h${String(m).padStart(2,'0')}min\\n`;
}

const th = Math.floor(Math.abs(totalMinutos)/60);
const tm = Math.abs(totalMinutos)%60;
const tsinal = totalMinutos < 0 ? '-' : '+';

const relatorio = `📊 *Relatório Semanal de HE*\\n\\n${linhas}\\n*Total equipe: ${tsinal}${th}h${String(tm).padStart(2,'0')}min*`;
return [{json:{relatorio}}];
"""

def wf_he_relatorio():
    return {
        "name": "Fluxo 3 - Relatorio Semanal HE",
        "nodes": [
            {
                "parameters": {
                    "rule": {"interval": [{"field": "cronExpression", "expression": "0 14 * * 5"}]}
                },
                "id": "44444444-4444-4444-4444-444444444401",
                "name": "Cron Sexta 14h",
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
                "id": "44444444-4444-4444-4444-444444444402",
                "name": "Login Senior",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [460, 300]
            },
            {
                "parameters": {"jsCode": js_preparar},
                "id": "44444444-4444-4444-4444-444444444403",
                "name": "Preparar Consultas",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [680, 300]
            },
            {
                "parameters": {
                    "method": "GET",
                    "url": "=https://platform.senior.com.br/t/senior.com.br/bridge/1.0/rest/hcm/calcfolha/entities/bancoHoras/saldoMensal",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "Authorization", "value": "={{ $json.jwt }}"}
                    ]},
                    "sendQuery": True,
                    "queryParameters": {"parameters": [
                        {"name": "empresa", "value": "={{ $json.empresa }}"},
                        {"name": "matricula", "value": "={{ $json.matricula }}"},
                        {"name": "startdate", "value": "={{ $json.startdate }}"},
                        {"name": "enddate", "value": "={{ $json.enddate }}"},
                        {"name": "codigocalculo", "value": "={{ $json.codigocalculo }}"}
                    ]},
                    "options": {}
                },
                "id": "44444444-4444-4444-4444-444444444404",
                "name": "Buscar Saldo HE",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [900, 300]
            },
            {
                "parameters": {"jsCode": js_montar_relatorio},
                "id": "44444444-4444-4444-4444-444444444405",
                "name": "Montar Relatorio",
                "type": "n8n-nodes-base.code",
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
                    "body": "={\"number\":\"5581997818685\",\"textMessage\":{\"text\":{{ JSON.stringify($json.relatorio) }}}}",
                    "options": {}
                },
                "id": "44444444-4444-4444-4444-444444444406",
                "name": "Enviar WhatsApp",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [1340, 300]
            }
        ],
        "connections": {
            "Cron Sexta 14h": {"main": [[{"node": "Login Senior", "type": "main", "index": 0}]]},
            "Login Senior": {"main": [[{"node": "Preparar Consultas", "type": "main", "index": 0}]]},
            "Preparar Consultas": {"main": [[{"node": "Buscar Saldo HE", "type": "main", "index": 0}]]},
            "Buscar Saldo HE": {"main": [[{"node": "Montar Relatorio", "type": "main", "index": 0}]]},
            "Montar Relatorio": {"main": [[{"node": "Enviar WhatsApp", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1"}
    }

wid, err = criar(wf_he_relatorio())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
