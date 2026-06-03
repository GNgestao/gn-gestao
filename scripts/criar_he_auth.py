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

# Gera o código JS para autorizar HE de todos os técnicos
js_autorizar = """
const jwt = $('Login Senior').first().json.token;
const hoje = new Date();
const dd = String(hoje.getDate()).padStart(2,'0');
const mm = String(hoje.getMonth()+1).padStart(2,'0');
const yyyy = hoje.getFullYear();
const dataHoje = `${yyyy}-${mm}-${dd}`;

const tecnicos = """ + json.dumps(TECNICOS) + """;
const empresa = '8550-1';
const codigoCalculo = '1370';
const pares = [['613','663'],['614','664']];

const resultados = [];
for (const [mat, nome] of tecnicos) {
  for (const [orig, dest] of pares) {
    resultados.push({matricula: mat, nome: nome, tipoOrig: orig, tipoDest: dest, data: dataHoje, jwt: jwt, empresa: empresa, codigoCalculo: codigoCalculo});
  }
}
return resultados.map(r => ({json: r}));
"""

def wf_he_auth():
    return {
        "name": "Fluxo 2 - Autorizacao HE Senior",
        "nodes": [
            {
                "parameters": {
                    "rule": {"interval": [{"field": "cronExpression", "expression": "0 8 * * 1-5"}]}
                },
                "id": "33333333-3333-3333-3333-333333333301",
                "name": "Cron 8h Seg-Sex",
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
                "id": "33333333-3333-3333-3333-333333333302",
                "name": "Login Senior",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [460, 300]
            },
            {
                "parameters": {"jsCode": js_autorizar},
                "id": "33333333-3333-3333-3333-333333333303",
                "name": "Preparar Autorizacoes",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [680, 300]
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "=https://platform.senior.com.br/t/senior.com.br/bridge/1.0/rest/hcm/calcfolha/entities/apontamentoHe/autorizar",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "Authorization", "value": "={{ $json.jwt }}"},
                        {"name": "Content-Type", "value": "application/json"}
                    ]},
                    "sendBody": True,
                    "contentType": "raw",
                    "rawContentType": "application/json",
                    "body": "={\"empresa\":\"{{ $json.empresa }}\",\"codigoCalculo\":\"{{ $json.codigoCalculo }}\",\"matricula\":\"{{ $json.matricula }}\",\"data\":\"{{ $json.data }}\",\"tipoHoraOrigem\":\"{{ $json.tipoOrig }}\",\"tipoHoraDestino\":\"{{ $json.tipoDest }}\"}",
                    "options": {}
                },
                "id": "33333333-3333-3333-3333-333333333304",
                "name": "Autorizar HE",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [900, 300]
            }
        ],
        "connections": {
            "Cron 8h Seg-Sex": {"main": [[{"node": "Login Senior", "type": "main", "index": 0}]]},
            "Login Senior": {"main": [[{"node": "Preparar Autorizacoes", "type": "main", "index": 0}]]},
            "Preparar Autorizacoes": {"main": [[{"node": "Autorizar HE", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1"}
    }

wid, err = criar(wf_he_auth())
if wid:
    ok = ativar(wid)
    print(f"OK id:{wid} ativo:{ok}")
else:
    print(f"ERRO:{err}")
