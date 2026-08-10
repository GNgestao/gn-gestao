# GN Gestão — Histórico de Sessões Antigas (23/06 a 07/07/2026)

> Consultar apenas quando precisar de detalhes técnicos de implementações já estáveis e concluídas. Para o estado atual do projeto, ver /root/CLAUDE.md.

## STATUS SESSÃO — 07/07/2026

### Correção do agendamento via Jarvis (PRIORIDADE CALENDAR) — IMPLEMENTADA

Workflow **GN Assistente Inteligente** (`mVZ1RyggUw9mnVgF`), nó **Montar Prompt** — `sysBase` atualizado via `PUT /api/v1/workflows/mVZ1RyggUw9mnVgF`:

**Problema:** Claude respondia com texto livre (`"Operacao realizada, Senhor."`) ao receber comandos como `"Jarvis agende vistoria no dia 08/07..."` em vez de retornar o JSON `{"acao":"calendar",...}`. Causa: `PRIORIDADE CALENDAR` listava apenas `"agendar"` (infinitivo), não cobrindo `"agende"` (imperativo) e outras variações. O histórico da conversa anterior com resposta de texto reforçou o padrão errado.

**Correção:** gatilhos da `PRIORIDADE CALENDAR` ampliados para: `agende, agendar, agenda, marque, marcar, marca, coloque na agenda, criar evento, ver agenda, listar eventos, deletar evento, remover evento`. Adicionada instrução explícita: `NUNCA responda com texto livre nesses casos. Retorne APENAS JSON puro, sem nenhum texto antes ou depois`.

### Reautorização OAuth2 Google — RENOVADA

Credencial `googleOAuth2Api` (ID `JlSrA18oCUPLxVug`) expirou — execução #8514 do workflow **GN Calendar API** (`V1jLYQ7jkpQEJ5nW`) falhou com `invalid_grant` no nó "Criar Evento". Token renovado automaticamente pelo n8n após reautorização; execução #8515 (teste manual via curl) confirmou funcionamento com evento criado com `status: confirmed` no Google Calendar de `gabrielnascimento1995@gmail.com`.

**Nota técnica:** o token OAuth2 do Google expira periodicamente. Se o GN Calendar API voltar a falhar com `invalid_grant`, acessar n8n → Credentials → `googleOAuth2Api` → Reconnect e refazer o fluxo OAuth.

### Restauração das cores roxo/laranja nos PDFs de Trabalho TK Elevator — IMPLEMENTADA

PDFs gerados pelo módulo de Trabalho (TK Elevator) tiveram as cores roxo/laranja do tema GN Gestão restauradas após regressão visual.

### Início do cadastro como Perito Judicial — EM ANDAMENTO

- **Cadastro como autônomo no GISS (Paulista-PE):** realizado — Gabriel registrado como prestador de serviços autônomo no sistema GISS do município de Paulista-PE.
- **Cadastro no SIGEO AJ/JT TRT-6 (Tribunal Regional do Trabalho 6ª Região):** iniciado. **Pendência:** aguardando número do ISS de Paulista após 09/07/2026 para concluir o cadastro de perito no sistema SIGEO.

**Próximo passo:** após receber o número ISS (depois de 09/07), retomar o cadastro no SIGEO AJ/JT TRT-6 para habilitar Gabriel como perito judicial na Justiça do Trabalho de Recife.

## STATUS SESSÃO — 02/07/2026

### Tentativa de grupo WhatsApp "GN Alertas" — ABANDONADA

Grupo `120363412627053088@g.us` criado e instância `gn-pessoal` adicionada via `GET /group/acceptInviteCode/gn-pessoal`. Fluxos 1, 2 e 3 foram temporariamente apontados para o JID do grupo, mas o envio travava indefinidamente no Evolution API v1.7.4: o Baileys tentava buscar `profilePictureUrl` do grupo antes de enviar e nunca recebia resposta. Foi aplicado patch em `whatsapp.baileys.service.js` (Promise.race com timeout de 5s), porém os restarts do container para aplicar o patch provocaram perda das **sender keys** do protocolo Signal para o grupo (`SessionError: No sessions` no libsignal), exigindo reconexão manual da sessão via QR code. Fluxos 1, 2 e 3 revertidos para o número pessoal `558197818685` e funcionando normalmente. Instância `gn-pessoal` reconectada e estável.

**Nota técnica:** envio para grupos no Evolution API v1.7.4 + Baileys requer que as sender keys estejam estabelecidas — elas são perdidas a cada restart do container ou logout da instância. Para retomar no futuro: após reiniciar o container, enviar uma mensagem pelo celular no grupo antes de tentar enviar via API.



### Migração WhatsApp empresa → pessoal nos workflows n8n — IMPLEMENTADA E TESTADA

Workflows **Fluxo 1 - TAC Mobile** (`egsKZ2811VPbqLZu`), **Fluxo 2 - Autorizacao HE Senior** (`TBRd8vtv0k6iZNCK`) e **Fluxo 3 - Relatorio Semanal HE** (`v6hwWcWGsScfDdEX`) atualizados via API n8n (PUT `/api/v1/workflows/{id}`):
- **Instância:** `gn-whatsapp` → `gn-pessoal`
- **Número:** `5581982381146` → `558197818685`
- **URL do nó "Enviar WhatsApp":** `http://187.127.26.136:8081/message/sendText/gn-pessoal`
- **Motivo:** WhatsApp da empresa não permitia vinculação em outros dispositivos

A instância `gn-whatsapp` permanece criada no Evolution API mas não é referenciada por nenhum workflow ativo. Todos os envios de WhatsApp do projeto agora usam `gn-pessoal`.

**Confirmação pós-migração:** execução 8060 do Fluxo 1 (02/07 00:00 UTC) → `success`, mensagem entregue em `558197818685@s.whatsapp.net` (messageId `BAE5D43B3776B63E`). Execuções anteriores (8058, 8059) falhavam com `500 Connection Closed` por apontar para `gn-whatsapp` desconectada.

**Nota técnica:** a API pública do n8n (`/api/v1/`) não suporta `POST /workflows/{id}/run` para workflows com ScheduleTrigger; o CLI `n8n execute` dentro do container conflita com o task broker na porta 5679. Para disparar manualmente: aguardar o ciclo do cron ou usar `curl` direto na Evolution API para testar o envio.

## STATUS SESSÃO — 30/06/2026

### Integração Gmail + Google Calendar via OAuth2 — IMPLEMENTADA E TESTADA

**Credencial Google:** `googleOAuth2Api`, ID `JlSrA18oCUPLxVug` — projeto **GN Gestão** no Google Cloud Console. Escopos: Gmail readonly + Calendar read/write. Usada via HTTP Request nodes com `authentication: "predefinedCredentialType"` + `nodeCredentialType: "googleOAuth2Api"` (nodes nativos `gmail`/`googleCalendar` do n8n requerem tipos de credencial diferentes e são incompatíveis).

**Nota técnica:** Code nodes no n8n 2.23.2 com task runner (`N8N_RUNNERS_ENABLED=true`) NÃO suportam `httpRequestWithAuthentication` nem `requestWithAuthentication` — erro explícito "not supported in the Code Node". Solução: HTTP Request nodes separados com OAuth2 configurado neles.

#### Workflow GN Gmail Resumo (`AeZNchxGuoMmfXVV`) — ativo
- **Cron:** `0 10 * * 1-5` (07h Recife / 10h UTC), segunda a sexta
- **Webhook manual:** `POST /webhook/gn-gmail-resumo-run`
- **Fluxo:** Cron/Webhook → HTTP Listar Emails (Gmail API, `is:unread newer_than:1d -category:promotions -category:social -in:spam`, maxResults=8) → IF Tem Emails? → Code Extrair IDs (fan-out) → HTTP Buscar Detalhes (por item, `format=metadata`) → Code Montar Resumo (alwaysOutputData, agrega com `$input.all()`, filtra 24h via `internalDate`, máx 10) → IF Tem Mensagem? → Code Montar Payload WPP → HTTP Enviar WhatsApp (`gn-pessoal`)
- **Bug Gmail:** parâmetros `metadataHeaders` com mesmo nome — n8n só envia o último, dropando `From`. Solução: remover `metadataHeaders`, `format=metadata` já retorna todos os headers
- **Parsing From:** RFC 2047 / `"Nome" <email>` tratado com `indexOf('<')` e strip de encoding `=?...?=`

#### Workflow GN Calendar Agenda (`tvFWyitV29MyVqX0`) — ativo
- **Cron:** `0 10 * * *` (07h Recife / 10h UTC), todo dia
- **Webhook manual:** `POST /webhook/gn-calendar-agenda-run`
- **Fluxo:** Cron/Webhook → HTTP Buscar Eventos Hoje (Calendar API, `timeMin`/`timeMax` hoje, `singleEvents=true`, `orderBy=startTime`) → Code Montar Mensagem → IF Tem Eventos? → Code Montar Payload WPP → HTTP Enviar WhatsApp

#### Workflow GN Calendar API (`V1jLYQ7jkpQEJ5nW`) — ativo
- **Webhook:** `POST /webhook/gn-calendar`, responseMode `responseNode`
- **Operações:** `criar` / `listar` / `deletar`
- **Roteamento:** IF chain (E Criar? → E Listar? → deletar por default) — Switch node v3 falha na ativação com "Missing or invalid required parameters: output"
- **Nó Preparar:** `parseDateBR(d)` converte DD/MM/YYYY → ISO; se ano ausente ou `< anoAtual`, usa `anoAtual`; armazena `dateISO` (corrigido) e `dataBR` (valor bruto)
- **Nó Resp Criar:** usa `prep.dateISO.split('-').reverse().join('/')` para exibir a data — não `prep.dataBR` que pode ter ano errado vindo do Claude
- **Nó Extrair Match (deletar):** filtra por título (includes, case-insensitive); se `dateISO` não vazio, aplica segundo filtro `dt.startsWith(dateISO)` sobre `start.dateTime` ou `start.date` — primeiro match por título quando sem data
- **Mensagem de erro com data:** `Evento "X" no dia DD/MM/YYYY não encontrado.`
- Todos os HTTP Request nodes: `authentication: "predefinedCredentialType"`, `nodeCredentialType: "googleOAuth2Api"`, credential ID `JlSrA18oCUPLxVug`

#### GN Assistente Inteligente (`mVZ1RyggUw9mnVgF`) — atualizado
- **Montar Prompt:** capability #10 — gerenciar agenda Google Calendar; regra `PRIORIDADE CALENDAR`; Claude responde com JSON `{"acao":"calendar","operacao":"criar/listar/deletar","titulo":"...","data":"DD/MM/YYYY","hora":"HH:MM","descricao":"..."}`
- **Extrair Resposta:** handler `acao === 'calendar'` chama `https://n8n.srv1610251.hstgr.cloud/webhook/gn-calendar` via `this.helpers.httpRequest` (sem OAuth — alvo é webhook n8n, não Google direto); log `console.log('[calendar] parsed recebido:', ...)` antes da chamada
- **Bug Claude + ano:** Claude às vezes retorna `"data":"07/07/2025"` (ano passado) para datas sem ano explícito. `parseDateBR` corrige na conversão ISO (2025 < 2026 → usa 2026), mas `dataBR` fica com o valor original — por isso `Resp Criar` usa `dateISO`, não `dataBR`

### Folder de Apresentação Profissional — CRIADO
- PDF + HTML gerados com perfil profissional de Gabriel Nascimento (engenheiro mecânico / perito)
- Armazenado localmente; conteúdo: formação, experiências TKE, competências técnicas, contato

### Prospecção de Empresas via DuckDuckGo — IMPLEMENTADA
- **`/root/oportunidades-api.js`** (porta 5060, mesmo serviço do GN Oportunidades) — rota adicional para prospecção de empresas
- **Tabela PostgreSQL `gn_empresas_prospecao`** — `n8n-postgres-1` / db `evolution`: empresas prospectadas com dedup por link
- Busca via `html.duckduckgo.com` (mesma técnica de warm-up + cookie das oportunidades)
- **Pendência:** ampliar fontes para Indeed/Catho e implementar envio de e-mail automático para empresas encontradas

*(Lista de pendências desta sessão — obsoleta, ver PENDÊNCIAS REAIS ATUAIS no topo.)*

## STATUS SESSÃO — 29/06/2026

### Segunda instância Evolution API (WhatsApp pessoal) — IMPLEMENTADA E TESTADA

- **Instância `gn-pessoal`** no Evolution API (porta 8081), número `558197818685`
- **Instance ID:** `dbaf9ffd-a602-40ce-801c-29f01a8d8447` | **API Key instância:** `B66FA8BE-853C-4766-83B7-255508655688`
- **API Key global:** `gn-evolution-2026` (mesma da instância `gn-whatsapp`)
- Status: `open` — conectada e testada (mensagem enviada com sucesso)
- Envio correto: `POST /message/sendText/gn-pessoal` com body `{"number":"558197818685","textMessage":{"text":"..."}}`
  - Campo é `textMessage.text` (não `text` no nível raiz — retorna 400 se errado)
- Variáveis adicionadas ao n8n (`/docker/n8n/docker-compose.yml`): `GN_EVOLUTION_URL`, `GN_EVOLUTION_APIKEY`, `GN_PESSOAL_INSTANCE`, `GN_PESSOAL_NUMBER`, `GN_PESSOAL_INSTANCE_APIKEY`, `GN_EMPRESA_INSTANCE`

### Workflow GN Oportunidades — IMPLEMENTADO E TESTADO

Monitoramento automático de oportunidades de engenharia mecânica/perícia, segunda a sexta às 08h (Recife). Notifica via WhatsApp pessoal (`gn-pessoal`) apenas quando há oportunidades novas.

**Componentes criados:**

**`/root/oportunidades-api.js`** — API local porta 5060, systemd `oportunidades-api.service` (ativo, enabled):
- `POST /oportunidades/processar` → busca 4 queries DuckDuckGo + LinkedIn, filtra, deduplica contra DB, insere novas, retorna `{novas, mensagem, erros, fontes_ok}`
- `MODO_ELEVADOR = false` no topo do arquivo — mudar para `true` quando Gabriel sair da TKE (libera resultados de elevadores que hoje são filtrados)
- **PALAVRAS_INCLUIR**: `engenheiro mecânico`, `engenheiro de segurança`, `laudo técnico`, `perícia técnica`, `perito`, `responsável técnico`, `caldeira`, `chiller`, `vaso de pressão`, `NR-12`, `NR-13`, `máquinas pesadas`, `automóvel`, `veículo`, `insalubridade`, `periculosidade`, `ergonomia`, `LTCAT`, `ART`, `Recife`, `Pernambuco`
- **PALAVRAS_EXCLUIR** (quando `MODO_ELEVADOR=false`): `elevador`, `elevadores`, `tke`, `thyssenkrupp`, `schindler`, `otis`, `kone`, `plataforma elevatória`
- Dedup: `SELECT link FROM gn_oportunidades` antes de inserir + `ON CONFLICT (link) DO NOTHING`
- `mensagem: ""` quando sem novas → n8n não envia WhatsApp

**Queries DuckDuckGo** (`html.duckduckgo.com/html/?q=...&kl=br-pt`, com cookie de sessão reaproveitado 30min):
1. `engenheiro mecânico laudo perícia Recife site:olx.com.br` → fonte `DDG/OLX-PE`
2. `perito engenheiro mecânico Recife Pernambuco site:creape.org.br OR site:tjpe.jus.br` → fonte `DDG/CREA-TJ-PE`
3. `consultor engenheiro mecânico elevador Recife` → fonte `DDG/Consultor-Elev`
4. `ART laudo técnico engenheiro Recife Pernambuco` → fonte `DDG/ART-Laudo`

Nota: `api.duckduckgo.com` (Instant Answer API) retorna 0 resultados para buscas complexas — descartado. `html.duckduckgo.com` requer warm-up request para obter cookie de sessão; IPs de datacenter são bloqueados sem cookie.

**Tabela PostgreSQL `gn_oportunidades`** — `n8n-postgres-1` / db `evolution`:
```sql
id SERIAL PK, titulo TEXT, link TEXT UNIQUE, fonte TEXT, descricao TEXT, data_encontrada TIMESTAMP DEFAULT NOW()
```

**Workflow n8n `GN Oportunidades`** (ID `hYmqh0WeVHqjR9qp`) — ativo, 6 nós:
1. **Cron** `0 11 * * 1-5` (08h Recife / 11h UTC)
2. **Webhook Manual** `POST /webhook/gn-oportunidades-run` — trigger alternativo para testes
3. **Processar Oportunidades** → `POST http://172.17.0.1:5060/oportunidades/processar` (timeout 120s)
4. **Tem Novas?** (IF) → `$json.mensagem` não vazio
5. **Montar Payload WhatsApp** (Code) → `{number: "558197818685", textMessage: {text: msg}}`
6. **Enviar WhatsApp Pessoal** → `POST http://172.17.0.1:8081/message/sendText/gn-pessoal` com `={{ JSON.stringify($json) }}`

**Bug corrigido na criação:** `jsonBody` com `JSON.stringify({... 'string' ...})` usando single quotes causa `invalid syntax` no parser de expressões do n8n. Solução: Code node monta o objeto nativo → HTTP node usa `={{ JSON.stringify($json) }}` (padrão comprovado no projeto).

**Teste ponta a ponta confirmado** (execução `6920`): todos os 6 nós `success`, 25 oportunidades encontradas, mensagem entregue no WhatsApp `558197818685`.

**Como disparar manualmente:**
```bash
curl -s -X POST http://localhost:5678/webhook/gn-oportunidades-run -H "Content-Type: application/json" -d '{}'
```

**Como ver última execução:**
```bash
API_KEY=$(sqlite3 /var/lib/docker/volumes/n8n_data/_data/database.sqlite "SELECT apiKey FROM user_api_keys WHERE label='Claude';")
curl -s "http://localhost:5678/api/v1/executions?workflowId=hYmqh0WeVHqjR9qp&limit=1&includeData=true" -H "X-N8N-API-KEY: $API_KEY" | python3 -m json.tool
```

*(Lista de pendências desta sessão — obsoleta, ver PENDÊNCIAS REAIS ATUAIS no topo.)*

## STATUS SESSÃO — 23/06/2026

### Abertura de OS de revisão via Jarvis por voz — IMPLEMENTADO E TESTADO

Comando: "gere OS de revisão para o técnico [nome] no equipamento [número]" (ou variações: "abre OS de revisão", "cria uma OS revisão", "ordem de serviço de revisão", etc.)

Fluxo completo:
1. **Frontend (`index.html`, função `gnExecutar`)** — regex intercepta o comando antes do bloco de abertura de sites externos e envia direto ao webhook `gn-assistente`, sem depender do fallback genérico.
2. **Webhook n8n `gn-assistente`** → workflow **GN Assistente Inteligente** (ID `mVZ1RyggUw9mnVgF`).
3. **Node "Montar Prompt"** — monta o system prompt (`sysBase`) com a lista de matrículas dos técnicos e a instrução: quando o Chefe pedir OS de revisão, responder APENAS com JSON puro no formato `{"acao":"os_revisao","tecnico":"NOME","matricula":"MATRICULA","equipamento":"NUMERO"}` (sem chamar webhook externo via texto — isso nunca funcionou de fato, era só o modelo "alucinando" sucesso).
4. **Node "API Claude"** — chama a Anthropic API com modelo **`claude-sonnet-4-6`** (atualizado nesta sessão; antes era `claude-sonnet-4-5`).
5. **Node "Extrair Resposta"** (Code node) — recebe o texto do Claude, remove eventuais code fences markdown (` ```json ... ``` `, que o modelo às vezes adiciona mesmo com instrução "sem markdown"), faz `JSON.parse`. Se `acao === 'os_revisao'`, chama de fato `http://172.17.0.1:5053/tac/os-revisao` via `this.helpers.httpRequest` (IP do gateway docker — `localhost` não funciona de dentro do container do n8n). Em caso de sucesso, responde **"OS de revisão aberta, Senhor."** (sem número/técnico/equipamento na mensagem, por pedido explícito). Em caso de falha na chamada HTTP, responde com mensagem de erro detalhada (técnico/equipamento/erro) para diagnóstico.
6. **tac-api.js** (porta 5053, `/root/tac-api.js`) — rota `POST /tac/os-revisao` faz login no TK Mobile, busca dados do equipamento, grava a OS de revisão real (`GravarOsDeRevisao`) e retorna o número da OS gerada.

### Correções importantes feitas nesta sessão
- O workflow Jarvis nunca teve um node HTTP que de fato chamasse o tac-api ou um webhook externo — o prompt antigo instruía o modelo a "chamar o webhook" via texto, mas isso é inexecutável; o modelo só inventava números de OS plausíveis. Corrigido: agora o Claude só estrutura dados em JSON, e o Code node ("Extrair Resposta") é quem efetivamente dispara a chamada HTTP.
- `http://localhost:5053` não é alcançável de dentro do container `n8n-n8n-1` (rede `n8n_default`, connection refused). Usar `http://172.17.0.1:5053` (gateway docker).
- Modelo da Anthropic API atualizado de `claude-sonnet-4-5` para `claude-sonnet-4-6` no node "API Claude".

### Workflows n8n relevantes
- **GN Assistente Inteligente** (`mVZ1RyggUw9mnVgF`) — fluxo principal do Jarvis (webhook `gn-assistente`), inclui memória, fatos, clientes e agora OS de revisão.
- **GN OS Revisao** (`dM0PLFOJZxVjZ2R4`) — webhook `gn-os-revisao` standalone que também chama `tac-api`; criado antes da abordagem JSON, não é mais o caminho usado pelo Jarvis.

### Backups
- `/root/tac-api.js.bak`

## STATUS SESSÃO — 25/06/2026

### Hub 2D estilo Obsidian — IMPLEMENTADO E TESTADO
Substituiu o hub 3D em Three.js (`index.html`, tela principal pós-login) por um canvas 2D próprio (`#hubCanvas`), reaproveitando o mesmo id para que a lógica de show/hide ao entrar/sair de módulos continuasse funcionando sem alterações.
- Fundo `#04030d` com 180 estrelas piscando, desenhado a cada frame.
- 4 quadrantes (cada um ocupando exatamente PI/2, sem lacuna): **PESSOAL** roxo `#c084fc` (top-left), **TRABALHO** verde `#4ade80` (top-right), **INVESTIMENTOS** laranja `#fb923c` (bottom-left), **PROJETOS** azul `#38bdf8` (bottom-right) — tags nos cantos, 8px, opacidade 0.2.
- 50 nós distribuídos em 3 anéis por quadrante, com algoritmo de repulsão (minDist 46px, 150 iterações) para evitar sobreposição. Linhas finas (0.3px) do centro até cada nó, cor do nó com opacidade 0.28, sem animação.
- Jarvis central arrastável (posição inicial W/2,H/2), halo + raios de estrela animados. Clique no Jarvis abre o painel de chat (`#hub2dChat`, 300×400, arrastável pelo header, fundo `rgba(8,8,20,.92)` com blur), conectado ao webhook real `GN_WEBHOOK` (reaproveita `gnSessionHistory` para contexto).
- Nós com módulo existente navegam direto (Escala/Férias → `enterGestaoEquipe()`+`geTabEscala()`/`geTabFerias()`, Clientes → `cliAbrir()`, Documentos → `enterDocumentacao()`, Reparo → `enterReparo()`, Reconhece+ → `enterReconhece()`, Plano Ação → `enterPlano()`, CIPA → `enterCIPA()`, Manutenção Pred. → `enterModule('preditiva')`). Os demais ~41 nós (incluindo **HE**, que ainda não tem tela própria no app) mostram toast "Em breve, Senhor." por 2s.
- **Botão flutuante do Jarvis nos módulos** (`#hubModuleJarvisBtn`): círculo 48px, borda azul `rgba(106,180,255,.4)`, letra "J", visível em qualquer módulo (inclusive nas telas-overlay Clientes/Gestão de Equipe) e oculto no Hub — controlado por polling leve (400ms) sobre o `display` computado do `#hubScreen`, sem precisar encapsular cada função `enter*`/`back*`. Abre o mesmo `#hub2dChat` do Hub (painel movido para fora de `#hubScreen` para ficar acessível também nos módulos). z-index ajustado para `10010` (telas de módulo usam `10000` com `isolation:isolate`; `9999` deixava o botão coberto e inclicável).
- Removido o antigo widget `#globalJarvis` (botão flutuante roxo/laranja "abas de módulo" + seu painel `#globalJarvisChat` dedicado) — ficou redundante e colidia visualmente com o novo botão/chat. Removidos junto: `initGlobalJarvis`, `globalJarvisSend`, `showGJ`/`hideGJ` e os wraps que os disparavam. Mantidas as classes `.gj-msg`/`.gj-msg-user`/`.gj-msg-bot` (reaproveitadas pelo chat novo) e os fallbacks para `#globalJarvisChatResp` em outros fluxos (Ata, CIPA, Plano, assinatura) — já protegidos com checagem de null, não dependiam exclusivamente do widget removido.

### Tela de login futurista — IMPLEMENTADA E TESTADA
`index.html`, `#loginScreen` redesenhado mantendo 100% da lógica de autenticação Firebase original (mesmos ids `loginEmail`/`loginPassword`/`loginName`/`loginBtn`/`loginMsg`/`loginForgot`/`tabLogin`/`tabRegister`/`registerNameField`, mesmas funções `doLogin`/`switchLoginTab`/`forgotPassword`/`showLogin`/`showApp` — nada de JS de auth foi tocado).
- `#loginCanvas`: gradiente radial `rgba(6,10,30)→rgba(4,3,13)`, 200 estrelas piscando, 40 partículas azuis flutuantes, grade a cada 60px em `rgba(106,180,255,.04)`.
- Scan line horizontal animada em loop (6s, topo→base) e arcos decorativos rotativos atrás do painel (dois anéis, velocidades/direções diferentes).
- Logo "GN GESTÃO" 38px/700/letter-spacing 0.15em com glow azul neon; tagline "Sistema de Supervisão Inteligente" 10px/letter-spacing 0.4em.
- Formulário 300px: labels "IDENTIFICAÇÃO"/"AUTENTICAÇÃO" 9px, inputs com cantos decorativos (`.lcorner` nos 4 cantos) e glow azul no focus, botão "ACESSAR SISTEMA" com gradiente azul escuro + efeito shine animado, status "Sistema online — Recife, PE" com dot verde pulsante.
- Removidos os overrides de `body.light-mode` para `#loginScreen`/`.login-box` (a tela agora é sempre escura/neon, independente do tema do app).

### Correções no fluxo Jarvis (n8n + frontend)

**Bug do "obrigado" sem resposta no chat de texto** — `index.html`, função `gnExecutar()`, blocos `_aguardandoNovaOs` e `_encerramentoTermos` (intercepta "obrigado", "valeu", "ok", etc.). O `else` (modo texto) escrevia em `hubJarvisChatResp`, um elemento que **nunca existiu no DOM** — era um no-op silencioso. Corrigido para usar o mesmo mecanismo do resto do fluxo de texto (`window._gjModoTexto` + `window._gjAddMessage`). *Nota de continuidade*: como o widget `#globalJarvis` (único lugar que setava `_gjModoTexto = true`) foi removido depois, na prática esse branch só é alcançado hoje pelo caminho de voz (`gnModoVoz`); o chat novo do Hub 2D/botão flutuante não passa por `gnExecutar()` (é um fetch isolado), então não depende dessa correção.

**Ordenação da memória do Jarvis** — workflow n8n **GN Assistente Inteligente** (`mVZ1RyggUw9mnVgF`), nó **"Buscar Memoria"**: query alterada de `SELECT role, conteudo FROM jarvis_memoria ORDER BY criado_em DESC LIMIT 50` para `ORDER BY id DESC LIMIT 50`. Causa raiz: o nó "Salvar Memoria" insere as linhas `user` e `assistant` no mesmo `INSERT...VALUES`, e `criado_em DEFAULT now()` é avaliado uma única vez por statement — as duas linhas ficam com timestamp idêntico, e sem critério de desempate o Postgres retorna a ordem de forma indefinida (confirmado com dados reais: ids 193/194 com `criado_em` igual até o microssegundo). `id` é serial e reflete a ordem real de inserção.

**Parsing de JSON duplicado** — mesmo workflow, nó **"Extrair Resposta"**: o Claude às vezes ecoa o JSON da requisição anterior antes do JSON da requisição atual (efeito colateral da bagunça de ordenação acima, que já foi corrigida). O código antigo fazia `JSON.parse` no texto inteiro e falhava silenciosamente nesse caso, caindo no fallback que nunca chama a API de OS. Corrigido: o texto é dividido em blocos por linha em branco/newline, cada bloco é testado com `JSON.parse`, e o **último bloco válido** é o usado (o mais recente é sempre o da requisição atual).

**tac-api.js** — confirmado timeout de 35s (`req.setTimeout(35000, ...)`) e retry automático de 3 tentativas já configurados no arquivo atual (`/root/tac-api.js`).

### Otimização mobile — IMPLEMENTADA E TESTADA
`index.html`, função global `detectMobile()` (`/Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)`), com classe `html.is-mobile-light` aplicada no boot para CSS condicional.
- **Login (`#loginCanvas`)**: 80 estrelas (200 no desktop), 15 partículas (40), grade em opacidade 0.02 (0.04), arcos rotativos e scan line ocultos via CSS.
- **Hub 2D (`#hubCanvas`)**: 80 estrelas (180), repulsão em 50 iterações (150), pulso do Jarvis fixo em 1 (sem oscilação), `requestAnimationFrame` com throttle a ~30fps via checagem de `performance.now()` (60fps no desktop).
- **VAD por voz** (`gnListen`, bloco `checkSilence`): threshold de silêncio 25 (15 no desktop) e tempo mínimo antes de processar áudio 2500ms (2000ms) — evita cortes prematuros em microfones de celular com piso de ruído mais alto (provável efeito do `autoGainControl` amplificando ruído ambiente).
- Testado com Playwright simulando user agent de iPhone vs desktop: detecção correta, contagens reduzidas aplicadas, arcos/scan line ocultos só no mobile.

### PWA instalável — IMPLEMENTADA E TESTADA
- `manifest.json` (raiz do repo): `name`/`short_name` "GN Gestão", `start_url` `/gn-gestao/`, `display` standalone, `background_color`/`theme_color` `#04030d`, ícones SVG "GN" em azul `#6ab4ff` sobre fundo escuro em `icons/icon-192.svg` e `icons/icon-512.svg`.
- `sw.js`: cache `gn-gestao-v1`, pré-cache de `index.html`/`manifest.json`, **cache-first** para assets estáticos, **network-first** para chamadas a `https://n8n.srv1610251.hstgr.cloud` (tenta a rede primeiro, cai no cache se falhar), fallback para `index.html` quando offline (inclusive em navegação).
- `index.html` `<head>`: `<link rel="manifest">`, `<meta name="theme-color" content="#04030d">`, `apple-mobile-web-app-capable`/`apple-mobile-web-app-status-bar-style` (iOS), registro do service worker no `DOMContentLoaded` (`navigator.serviceWorker.register('/gn-gestao/sw.js')`).
- Testado com Playwright servindo o repo na estrutura real do GitHub Pages (`/gn-gestao/...`): service worker registra sem erro de console.

### Correção do auto-start da escuta por voz — IMPLEMENTADA E TESTADA
Investigação pedida pelo Chefe sobre qual botão ativava o modo voz revelou duas coisas:
1. O elemento original (`.hub-hex-wrap`, `onclick="enterGN()"`, hub hexagonal antigo) já tinha sido removido há muito tempo (commit `da40479`, redesign para o hub neural 3D) — não relacionado a esta sessão. `enterGN()`/`#screenGN`/`#gnMicBtn` continuam órfãos (sem nenhum gatilho no DOM).
2. **Regressão causada nesta sessão**: a remoção do `#globalJarvis` (ver acima) também removeu `showGJ()`, que tinha uma segunda responsabilidade escondida além de mostrar o botão — chamava `gnStartContinuous()` automaticamente após o login e em toda entrada/saída de módulo. Sem isso, o Jarvis parou de ligar a escuta por wake-word em qualquer lugar do app.

Corrigido com `gnAutoStartVoz()` (mesma regra de acesso do código antigo: só `superadmin`, não religa se `gnContinuousMode` já estiver ativo), chamada em:
- `showApp`, 1200ms após o login (mesmo timing de antes).
- `enterModule`/`enterReconhece`/`enterReparo`/`enterPlano`/`enterDocumentacao`/`enterGN`/`enterCIPA` (entrar em módulo).
- `backToHub`/`backFromReconhece`/`backFromReparo`/`backFromDocumentacao`/`backFromGN`/`gnVoltarHub`/`backToModule`/`backFromCIPA` (voltar ao hub).

Reaproveita o wrapping que já existia no Hub 2D para esconder/mostrar o `hubCanvas` nessas mesmas funções, em vez de duplicar lógica. Testado com Playwright: `gnContinuousMode` liga automaticamente após login e volta a `true` ao entrar/sair de módulo, sem `#globalJarvis` no DOM.

*(Lista de pendências desta sessão — obsoleta, ver PENDÊNCIAS REAIS ATUAIS no topo.)*

## STATUS SESSÃO — 27-28/06/2026

### Fechamento de OS de Troca de Peça via tac-api — IMPLEMENTADO E TESTADO

Função `fecharOsTrocaPeca(numeroOS)` adicionada em `/root/tac-api.js`, rota `POST /tac/os-troca-peca`.

**Fluxo completo (sequência de etapas):**
1. **Login** — `EfetuarLogin` → captura cookies `ASP.NET_SessionId`, `LOGIN`, `TKEMobile`, `USER` (único login; reutilizado por todas as etapas via closure).
2. **BuscarListaDeOS** — `BuscarListaDeOSDeTrocaDePeca` → extrai `equipamento.numero` e `equipamento.temMax` da OS.
3. **AceitarOS** — `AtualizarStatusOSDeTrocaDePeca` com `status: 5` (inteiro), `latitude: -8.0522`, `longitude: -34.9286` (float).
4. **RegistrarEstouAqui** — mesmo endpoint com `status: 6`.
5. **BuscarEquipamento** — login próprio + `FormStatusElevador.aspx/BuscarEquipamento` (informativo, try/catch, não bloqueia).
6. **BuscarRelacao** — login próprio + `FormConcluidaOS.aspx/BuscarRelacao` (informativo, try/catch, não bloqueia).
7. **EncerrarOS** — `EncerrarOSDeTrocaDePeca` com payload completo de 30 campos (`statusOS:'8'`, `situacao:'funcionando'`, `responsavel:'1'`, `risco:'0'`, lat/long float, etc.) — retorna `statusAtual:'8'` quando bem-sucedido.

**Bugs corrigidos durante desenvolvimento:**
- `status: 'A'`/`'I'` (string) → `status: 5`/`6` (inteiro): com strings, servidor retornava `statusAtual:0` e `equipamento:0`; com inteiros, retorna corretamente o equipamento e o `statusAtual` esperado.
- `latitude`/`longitude` como string (`'-8.0522'`) → float (`-8.0522`): idem, necessário para o servidor processar corretamente.
- `BuscarEquipamento` e `BuscarRelacao` usavam `FormTrocaDePeca.aspx` como BASE — corrigido para `FormStatusElevador.aspx` e `FormConcluidaOS.aspx` respectivamente, cada um com login próprio.
- Payload `EncerrarOSDeTrocaDePeca`: substituído payload antigo (campos PascalCase `NumeroOs`, `SemAssinatura`, etc.) pelo payload real capturado do browser (campos camelCase lowercase com 30 campos).

**Headers finais (chamarEtapa):**
- `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36`
- `Accept: application/json, text/javascript, */*; q=0.01`
- `Accept-Language: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7`
- `sec-fetch-dest: empty` / `sec-fetch-mode: cors` / `sec-fetch-site: same-origin`

**Rota HTTP** (`/tac/os-troca-peca`): aceita `{numeroOs}` (string ou array), retry 3×, retorna `{sucesso, numeroOs}` ou `{sucesso:false, mensagem, etapa}`.

### Integração com Jarvis por voz — IMPLEMENTADO

**n8n — GN Assistente Inteligente** (`mVZ1RyggUw9mnVgF`):
- **Montar Prompt**: instrução #9 adicionada ao `sysBase` — quando o Chefe pedir fechar/encerrar OS de peças, responder APENAS com `{"acao":"os_peca","numeroOs":"NUMERO"}`. Regra de prioridade `PRIORIDADE OS PECA` adicionada.
- **Extrair Resposta**: handler `acao === 'os_peca'` chama `http://172.17.0.1:5053/tac/os-troca-peca` via `this.helpers.httpRequest`, retorna `"OS NUMERO encerrada, Senhor."` ou mensagem de erro.

Comandos reconhecidos: "fecha OS de peças NUMERO", "encerra OS NUMERO", "fechar OS de troca de peça NUMERO" e variações.

### Tela TK Mobile no Hub — IMPLEMENTADO

**index.html** — nó "TK Mobile" do Hub 2D agora abre `#screenTkMobile` em vez do toast "Em breve".

Funcionalidades:
- Upload drag-and-drop de planilha Excel (`.xlsx`/`.xls`) ou CSV — usa SheetJS (já carregado no projeto).
- Detecção automática da coluna de OS: aceita `"Nº OS"`, `"N° OS"`, `"numeroOs"`, `"nos"` e variações; fallback para primeira coluna com 5+ dígitos.
- Tabela de progresso em tempo real: `— Pendente` (cinza) → `⟳ Processando…` (amarelo) → `✔ Concluída` (verde) / `✖ Erro` (vermelho).
- Botão "Processar Todas" envia OS sequencialmente (uma por uma) para o webhook n8n via HTTPS (Mixed Content bloquearia chamada direta ao tac-api).
- Barra de progresso animada com percentual e contagem `X / total`.
- Resumo contador (total / pendente / processando / concluídas / erros) atualizado a cada OS.
- Reset automático ao entrar na tela; botão muda para "✔ Concluído" (verde) ao finalizar.
- Wiring: `enterTkMobile`/`backFromTkMobile` registrados nos wraps de canvas/autoVoz; `screenTkMobile` adicionado à lista `sobrepostas` do botão Jarvis flutuante.

### Workflow n8n GN OS Peças — CRIADO E ATIVO

- **ID:** `nTlAEehkwm31RH6L`
- **Webhook:** `POST /webhook/gn-os-peca`
- **Fluxo:** Webhook → Fechar OS (`POST http://172.17.0.1:5053/tac/os-troca-peca` com `{numeroOs}`) → Responder com JSON.
- Testado ponta a ponta: webhook alcança tac-api e retorna resposta correta.

*(Lista de pendências desta sessão — obsoleta, ver PENDÊNCIAS REAIS ATUAIS no topo.)*

## STATUS SESSÃO — 28/06/2026

### Migração Plano de Ação 5W1H: localStorage → PostgreSQL via n8n — IMPLEMENTADO E TESTADO

**Infraestrutura criada:**
- Tabelas PostgreSQL (`n8n-postgres-1`, db `evolution`):
  - `gn_planos` (id VARCHAR PK, client, addr, name, why, resp, start_date DATE, end_date DATE, status, added_at BIGINT)
  - `gn_plano_items` (id VARCHAR PK, plano_id FK CASCADE, why, what, how, who, where_field, start_date, end_date, how_much NUMERIC, tipo, status, concluido BOOLEAN)
  - Índice em `plano_id` para performance da JOIN
- `/root/planos-api.js` — API local porta 5059, systemd `planos-api.service`
  - `GET /planos` → JOIN completo retorna `{planos:[...]}` (wrapper objeto evita bug n8n com array vazio)
  - `POST /planos` → upsert plan + upsert/delete itens em cascata
  - `POST /planos/delete` → DELETE plan (CASCADE remove itens automaticamente)

**Workflows n8n criados e ativos:**
- **GN Planos Load** (`QnXoHq56aMeZvBXl`) — GET `/webhook/gn-planos-load`
- **GN Planos Save** (`QdckeiX7YkKNBzV9`) — POST `/webhook/gn-planos-save`
- **GN Planos Delete** (`M4mg9umymOrgMksq`) — POST `/webhook/gn-planos-delete`

**Padrão dos nós HTTP nos workflows POST:**
- `specifyBody: "json"` + `jsonBody: "={{ JSON.stringify($json.body) }}"` (não `contentType:"json"` + `body:...` — esse não funciona)
- `respondWith: "text"` + `responseBody: "={{ JSON.stringify($json) }}"`

**Mudanças no index.html:**
- `_plans = []` (não mais `JSON.parse(localStorage...)`)
- `_loadPlans()` — async, chamado em `enterPlano()`, mostra "⏳ Carregando..."
- `_savePlan(planId)` — fire-and-forget, salva apenas o plano modificado (não todos)
- `_delPlanRemote(planId)` — DELETE via webhook
- `savePlans()` → redireciona para `_savePlan(_currentPlanId)` (compatibilidade com toggles/edições de itens inline)
- `savePlan()`, `saveImportedPlan()`, `saveAiPlan()` → chamam `_savePlan(plan.id)` explicitamente
- `deletePlan()` → chama `_delPlanRemote(planId)` em vez de `savePlans()`
- `updatePlanStatus()` → chama `_savePlan(planId)` explicitamente
- Zero referências ao `localStorage` para dados de plano

**Bug n8n com array vazio:** quando httpRequest retorna `[]`, n8n cria 0 itens e `respondToWebhook` não executa — solução: API retorna `{planos:[]}` e workflow usa `$input.first().json.planos || []`.

### Pronúncia TTS corrigida — IMPLEMENTADO

Pré-processamento adicionado no início de `gnSpeak()` (`index.html`), antes do fetch ao webhook TTS:
```javascript
texto = texto
  .replace(/\bOS\b/g,  'Ó Ésse')
  .replace(/\bHE\b/g,  'Agá É')
  .replace(/\bTKE\b/g, 'TêKá É')
  .replace(/\bVPS\b/g, 'Vê Pê Ésse')
  .replace(/\bPDF\b/g, 'Pê Dê Éfe')
  .replace(/\bAPI\b/g, 'Á Pê Í')
  .replace(/\bJarvis\b/gi, 'Járvis');
```
Regex case-sensitive com `\b` — não afeta `os`, `he` etc. minúsculos. Flag `gi` no Jarvis para cobrir variações de capitalização do modelo.

### Apresentações do Jarvis — IMPLEMENTADO

Nó "Montar Prompt" do workflow **GN Assistente Inteligente** (`mVZ1RyggUw9mnVgF`) atualizado com bloco `APRESENTACAO`:
- **Rápida** (`"apresentacao rapida"`, `"se apresente"`, `"apresentacao curta"`, `"quem e voce"`): resposta fixa de 2 frases
- **Completa** (`"apresentacao completa"`, `"apresentacao detalhada"`): resposta detalhada com 4 frentes (Trabalho, Investimentos, Projetos, Pessoal)
- **Com pessoa/reunião** (`"se apresente para [nome]"`, `"estou em reuniao com [nome/grupo]"`): inicia com "Boa tarde, [nome]." ou "Boa tarde a todos." e usa versão completa
- **Rápida com pessoa**: "Boa tarde, [nome]. Sou o Jarvis, assistente de supervisão inteligente do Supervisor Gabriel Nascimento. É um prazer."

### Service Worker — cache invalidado automaticamente por timestamp de build

`sw.js` — `CACHE_NAME` migrado de versão manual (`v1`, `v2`) para timestamp de data (`gn-gestao-20260628`). A cada modificação do `sw.js` basta atualizar a data; o browser detecta mudança byte a byte, apaga o cache antigo no `activate` e força download do `index.html` atualizado.

*(Lista de pendências desta sessão — obsoleta, ver PENDÊNCIAS REAIS ATUAIS no topo.)*
