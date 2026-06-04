import sqlite3, json, subprocess

result = subprocess.run(
    ["docker", "inspect", "n8n-n8n-1", "--format", "{{range .Mounts}}{{if eq .Destination \"/home/node/.n8n\"}}{{.Source}}{{end}}{{end}}"],
    capture_output=True, text=True
)
db_path = result.stdout.strip() + "/database.sqlite"

con = sqlite3.connect(db_path)
cur = con.cursor()
cur.execute("SELECT nodes FROM workflow_entity WHERE id='HL37sGAYpiHg4IlY'")
nodes = json.loads(cur.fetchone()[0])

novo_js = "const body=$json;let lista=[];try{const d=typeof body.d==='string'?JSON.parse(body.d):body.d;lista=d.Response||[];}catch(e){lista=[];}const agora=new Date().toLocaleString('pt-BR',{timeZone:'America/Recife'});const cab='\\u{1F527} *OS ABERTAS \\u2014 GN Gest\\u00e3o*\\n'+agora+'\\n\\n';if(!lista||lista.length===0){return [{json:{mensagem:cab+'\\u2705 Nenhuma OS aberta no momento.'}}];}let texto=cab;lista.forEach((c,i)=>{const num=c.Numero||'';const status=c.Status||'';const edificio=c.NomeEdificio||'';const elev=c.Equipamento||'';const apelido=c.Apelido?(' ('+c.Apelido+')'):'';const tec=c.NomeTecnico||'Indefinido';const prior=c.Prioridade||'';const hora=c.DataHoraAbertura||'';const relato=c.Relato?c.Relato.substring(0,80):'';texto+=(i+1)+'. OS '+num+' \\u2014 \\uD83D\\uDD34 '+status+'\\n';texto+='\\uD83C\\uDFE2 '+edificio+'\\n';texto+='\\uD83D\\uDEE7 Elevador: '+elev+apelido+'\\n';texto+='\\uD83D\\uDC77 '+tec+'\\n';texto+='\\u26A1 Prioridade: '+prior+' | \\uD83D\\uDD50 '+hora+'\\n';if(relato)texto+='\\uD83D\\uDCCB '+relato+'\\n';texto+='\\n';});texto+='Total: *'+lista.length+' OS aberta(s)*';return [{json:{mensagem:texto}}];"

for n in nodes:
    if n['name'] == 'Montar Mensagem':
        n['parameters']['jsCode'] = novo_js
        print("Atualizado: Montar Mensagem")

cur.execute("UPDATE workflow_entity SET nodes=? WHERE id='HL37sGAYpiHg4IlY'", (json.dumps(nodes),))
con.commit()
con.close()
print("OK")
