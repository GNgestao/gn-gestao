import sqlite3, json, subprocess

result = subprocess.run(
    ["docker", "inspect", "n8n-n8n-1", "--format", "{{range .Mounts}}{{if eq .Destination \"/home/node/.n8n\"}}{{.Source}}{{end}}{{end}}"],
    capture_output=True, text=True
)
db_path = result.stdout.strip() + "/database.sqlite"

con = sqlite3.connect(db_path)
cur = con.cursor()

# Atualizar os dois fluxos HE
for wf_id, wf_name in [("1OsiYhDQKmzsyFB1", "HE Auth"), ("BeMZTNpQPwhP53JP", "HE Relatorio")]:
    cur.execute(f"SELECT nodes FROM workflow_entity WHERE id=?", (wf_id,))
    row = cur.fetchone()
    if not row:
        print(f"Fluxo {wf_name} não encontrado")
        continue

    nodes = json.loads(row[0])

    for n in nodes:
        if n.get('name') == 'Login Senior':
            # Nova URL de login
            n['parameters']['url'] = 'https://platform.senior.com.br/t/senior.com.br/bridge/1.0/rest/platform/authentication/actions/login'
            # Novo content-type JSON
            n['parameters']['sendHeaders'] = True
            n['parameters']['headerParameters'] = {'parameters': [
                {'name': 'Content-Type', 'value': 'application/json'}
            ]}
            # Novo body JSON
            n['parameters']['sendBody'] = True
            n['parameters']['contentType'] = 'raw'
            n['parameters']['rawContentType'] = 'application/json'
            n['parameters']['body'] = '{"username":"10583194@thyssenkrupp.com","password":"Initpass*1","tenantName":"thyssenkrupp"}'
            # Remover form-urlencoded
            if 'bodyParameters' in n['parameters']:
                del n['parameters']['bodyParameters']
            print(f"Login Senior atualizado em {wf_name}")

    # Atualizar nó que pega o token — agora é jsonToken > access_token
    for n in nodes:
        if n.get('type') == 'n8n-nodes-base.code' and 'jwt' in n['parameters'].get('jsCode', ''):
            old_js = n['parameters']['jsCode']
            # Substituir extração do token
            new_js = old_js.replace(
                "$('Login Senior').first().json.token",
                "JSON.parse($('Login Senior').first().json.jsonToken).access_token"
            ).replace(
                "$json.token",
                "JSON.parse($('Login Senior').first().json.jsonToken).access_token"
            )
            if new_js != old_js:
                n['parameters']['jsCode'] = new_js
                print(f"Token extraction atualizado em {n['name']} ({wf_name})")

    cur.execute("UPDATE workflow_entity SET nodes=? WHERE id=?", (json.dumps(nodes), wf_id))

con.commit()
con.close()
print("OK")
