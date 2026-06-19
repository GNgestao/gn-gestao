# CLAUDE.md — Projeto GN Gestão / Jarvis

## CONTEXTO DO PROJETO
Sistema de gestão operacional pessoal e profissional de Gabriel Nascimento, gestor de manutenção de elevadores da ThyssenKrupp em Recife-PE. Inclui app web, automações n8n e assistente de voz inteligente chamado Jarvis.

## INFRAESTRUTURA
- VPS: Hostinger, IP 187.127.26.136, Ubuntu 24.04 — **reinstalada em 03/06/2026 (tudo reconfigurado do zero)**
- n8n: https://n8n.srv1610251.hstgr.cloud (Docker, funcionando)
- n8n encryptionKey: f8H8OM+uM7ktt7iUygzgW8YHlwNdy+yJ — **NUNCA apagar manualmente**
- Kokoro TTS: porta 5050 (Docker, funcionando)
- Evolution API v1.7.4: porta 8081 (Docker, gn-whatsapp conectado no 5581982381146)
- App: https://gngestao.github.io/gn-gestao/
- GitHub: github.com/GNgestao/gn-gestao (arquivo principal: index.html, ~9700+ linhas)
- SSH: ssh root@187.127.26.136
- GitHub token (sem expiração): ghp_*** (ver com Gabriel)

## FIREBASE
- Projeto: gn-gestao
- apiKey: AIzaSyDyszR3OIEnsbLYNBEeX5ooE7np9TJDEnY
- authDomain: gn-gestao.firebaseapp.com
- appId: 1:921732753600:web:c45f44fde1a9f11a296525
- SuperAdmin: gabrielnascimento1995@gmail.com
- Roles: superadmin (acesso total), admin, viewer

## APP GN GESTÃO
Single-page HTML/CSS/JS puro. Tema escuro roxo/laranja, fontes Syne + DM Sans.

### Módulos ativos:
- Manutenção Preditiva — controle de vencimentos de peças/serviços de elevadores (Firebase)
- Reconhece+ — avaliação de desempenho da equipe
- Plano de Ação 5W1H — planos de ação
- Reparo — serviços subcontratados com calendário (localStorage)
- Jarvis — assistente de voz inteligente (só superadmin)
- Documentação — Carta Técnica ✅ concluída; Ata de Reunião ✅ concluída
- CIPA ✅ — Ata CIPA completa; formulário, PDF, envio Autentique, integração Jarvis

### Módulos em desenvolvimento:
- Gestão de Equipe (aba Férias + aba Escala de Plantões) — **Escala funcional com autosave; Férias com novo layout tabela anual**

### Hub:
Rede neural animada. GN no centro, módulos ao redor flutuando. Fundo estrelado global.

## JARVIS — ASSISTENTE DE VOZ

### Configuração atual:
- Wake words reconhecidas (16 variações): jarvis, charles, chaves, jarves, jarvi, jabez, jalvez, jalvis, jarvy + demais variações
- Chama Gabriel de "Chefe" ou "Senhor" (alterna aleatoriamente)
- Webhook principal: POST https://n8n.srv1610251.hstgr.cloud/webhook/gn-assistente (body: {comando: texto})
- Webhook TTS: POST https://n8n.srv1610251.hstgr.cloud/webhook/gn-tts (body: {texto: resposta})

### PROTEÇÃO CONTRA TRAVAMENTOS
- Camada 1: comando "reiniciar" chama webhook n8n → Restart API: http://187.127.26.136:5051/restart-tts (systemd: jarvis-restart-api)
- Camada 2: duplo clique no Jarvis (hub) zera flags e reinicia o frontend imediatamente
- Camada 3: Watchdog automático — verifica a cada 5s, reinicia loop se travado por 45s sem atividade

### NAVEGAÇÃO POR VOZ (gnAcoes)
- Módulos: reconhece, reparo, plano, preditiva, manutenção preditiva, documentação, gestão de equipe
- Hub: central, base, tela principal, menu principal, início, voltar, home
- Sessão: encerrar, encerrar sessão, desligar → fala despedida e faz logoff
- Reload automático 1,5s após logoff para garantir login limpo

### STT — DEEPGRAM
- API Key: bd90f336d163b04c49e60474af21737e635396f4
- Modelo: nova-2, pt-BR, punctuate=true
- Chamada direta da API no frontend (sem passar pela VPS)
- Custo: $0,0043/minuto de áudio transcrito
- Crédito inicial: $200 grátis
- Implementação: MediaRecorder grava WebM, envia ao Deepgram após silêncio

### VAD — DETECÇÃO DE SILÊNCIO
- Implementado via AudioContext + analyser no frontend
- Threshold de silêncio: 10 (volume médio abaixo disso = silêncio)
- Tempo de silêncio para processar: 2000ms
- Delay pós-resposta (antes de reativar microfone): 2000ms
- Timeout de conversa: 5 minutos sem interação encerra a sessão

### TTS — KOKORO
- Servidor: /usr/local/bin/jarvis-tts-server.py rodando na porta 5050
- Voz: pm_alex (masculina, português brasileiro)
- Iniciar: nohup python3 /usr/local/bin/jarvis-tts-server.py > /var/log/jarvis-tts.log 2>&1 &
- Dependências: kokoro, soundfile, flask, espeak-ng
- Retorna: audio/wav
- ATENÇÃO: no n8n o campo texto deve ser {{ $json.body.texto }} SEM o = antes

### JARVIS PROXY HTTPS
- Container Docker: jarvis-jarvis-api-1 em /docker/jarvis
- Rota: https://n8n.srv1610251.hstgr.cloud/jarvis/stt e /tts
- Traefik gerencia SSL via Let's Encrypt
- Iniciar: cd /docker/jarvis && docker compose up -d

### MEMÓRIA — POSTGRESQL
- Container: evolution-postgres
- Credenciais: host=evolution-postgres, db=evolution, user=postgres, password=evo123
- Tabela: jarvis_memoria (id, role, conteudo, criado_em)
- Credencial n8n: jarvis-postgres
- Guarda TODAS as conversas permanentemente
- Busca as últimas 20 mensagens como contexto para o Claude

### BUSCA WEB — SERPER API
- API Key: 8c08a1872542c56d51ca5fe6f6780a434157ea35
- Detecta gatilhos automáticos na pergunta: hoje, dólar, notícia, clima, cotação, preço, agora, atual, previsão, temperatura
- Quando detectado, faz busca antes de chamar o Claude e injeta resultado no contexto
- Endpoint: https://google.serper.dev/search

### MEMÓRIA SEMÂNTICA — PGVECTOR + VOYAGE AI
- Tabela: `jarvis_memoria_v2` no PostgreSQL com embeddings de 1024 dimensões (pgvector)
- Serviço: `memoria-api.service` na porta 5056 — /root/memoria-api.js
- API Key Voyage AI: pa-ETTEm-tehUgEhdHqfyuTGP8BJoHJqyTIlp56M2UQ9Rc
- Conta Voyage AI: dashboard.voyageai.com, organização GN Gestão
- Endpoint buscar: POST http://187.127.26.136:5056/buscar (body: {query: texto})
- Endpoint salvar: POST http://187.127.26.136:5056/salvar (body: {conversa: texto})

### CÉREBRO — CLAUDE API
- Modelo: claude-sonnet-4-5
- API Key: no nó API Claude do n8n (x-api-key)
- Fluxo n8n: Webhook → Buscar Memória → Buscar Fatos → Montar Prompt → API Claude → Extrair Resposta → Responder + Salvar Memória + Salvar Memória Semântica

### FLUXO N8N — GN Assistente Inteligente
Sequência:
1. Webhook recebe {comando: texto}
2. Buscar Memória: SELECT role, conteudo FROM jarvis_memoria ORDER BY criado_em DESC LIMIT 20
3. Buscar Fatos: POST http://187.127.26.136:5056/buscar com {query: comando} — retorna memórias semânticas relevantes
4. Montar Prompt: Código JS monta system prompt com histórico + fatos semânticos + mensagem atual
5. API Claude: chama https://api.anthropic.com/v1/messages
6. Extrair Resposta: extrai texto da resposta Claude
7. Responder ao Webhook: retorna {resposta: texto}
8. Salvar Memória: INSERT INTO jarvis_memoria (role, conteudo)
9. Salvar Memória Semântica: POST http://187.127.26.136:5056/salvar com conversa

### FLUXO N8N — GN Texto para Fala
- Webhook recebe {texto: resposta}
- Nó Code: substitui vírgulas por pontos (evita bug de pronúncia)
- HTTP Request: POST http://187.127.26.136:5050/tts
- ATENÇÃO: usar {{ $json.body.texto }} SEM o = antes
- Retorna: audio/wav binário

## FLUXOS N8N

### Fluxo 1 — TAC Mobile
- ID: egsKZ2811VPbqLZu
- Cron: */30 * * * * (a cada 30 minutos)
- Login: POST https://mobile.br.tkelevator.com/TKEMobile/Default.aspx/EfetuarLogin
- Usuário TK Mobile: PE2158 (em base64: UEUyMTU4) / Senha: Initpass1* (em base64: SW5pdHBhc3MxKg==)
- Autenticação via cookies (ASP.NET_SessionId, LOGIN, TKEMobile, USER)
- **Cookie USER truncado**: n8n trunca cookies >2000 chars — por isso usa serviço local tac-api.js
- Serviço local: GET http://187.127.26.136:5053/tac (tac-api.js, porta 5053, systemd tac-api.service)
- Busca chamados: POST https://mobile.br.tkelevator.com/TKEMobile/FormOSAberta.aspx/BuscarOsAberta
- Body: {"filial": 5008, "zonas": [3]}
- Resposta: {"d": "{"Response": [...], "Success": true}"}
- Envia para WhatsApp 5581982381146 sempre (com OS ou "Nenhuma OS aberta no momento.")
- Inclui: número OS, status, condomínio, elevador, técnico, prioridade, horário

### Fluxo 2 — Autorização Automática HE Sênior
- ID: TBRd8vtv0k6iZNCK
- Cron: 0 8 * * 1-5 (seg-sex 8h)
- Serviço local: GET http://187.127.26.136:5054/he (he-api.js, porta 5054, systemd he-api.service)
- **Nova autenticação (3 etapas):**
  1. POST platform.senior.com.br/login → access_token
  2. POST web25.seniorcloud.com.br:31601/gestaoponto-backend/api/senior/auth/g7 com header `token: access_token` → JWT assertion
  3. Usar header `assertion` em todas as chamadas subsequentes
- Usuário: 10583194@thyssenkrupp.com / Senha Sênior: Initpass1*
- Empresa: 8550-1, codigoCalculo: 1370
- **Período de ponto:** se dia >= 11 → dataInicial = dia 11 do mês atual; se dia < 11 → dataInicial = dia 11 do mês anterior; dataFinal = ontem
- Autoriza HE ≤ 2h, códigos 613→663, 614→664
- **Estagiários NÃO incluídos no fluxo HE:** 55020261 Rodrigo Nascimento e 55020770 Weston Cardoso
- IMPORTANTE: funciona apenas em horário comercial

### Fluxo 3 — Banco de Horas Diário
- Cron: seg-sex 8h
- Banco de Horas diário 8h seg-sex, serviço bh-api.js porta 5055, ID v6hwWcWGsScfDdEX

## 24 TÉCNICOS (matrícula: nome)
55007445: ADRIANO FRANCISCO DA SILVA
55013039: ADRIANO ROGERIO BRAZ DA SILVA
55016328: ALISSON MENDES CHAGAS
55007813: ANTONIO AMARO BARRETO FILHO
55006085: BRUNO DANILO FIRMINO DA SILVA
55019788: DIEGO ASSIS SANTOS DA ROCHA
55004902: DURVAL SILVA DE LIMA
55010850: EDVALDO WILSON TEIXEIRA DE LIMA
55016383: ELENILDO TEOFILO DE JESUS
55015944: GEORGE BERNARDINO DA SILVA
55018679: GILIARD FELIPE FIGUEIRA NASCIMENTO
55013171: HUMBERTO JOSE DE LIMA
55004915: JOAZ JOSE BEZERRA
55018937: JOSE CHARLYTONBERG CORREA LINS
55001880: KLEBSON ANDRADE DA SILVA
55012621: KLEBSON RAMOS DA SILVA
55012128: LAERCIO SIMIAO LUPERCINIO
55012623: LUCIANO FELIX DOS SANTOS
55015003: MARCELO DE BARROS ALMEIDA
55015783: PAULO ANDRE LAURENTINO DE OLIVEIRA
55000585: RODOLFO MARTINIANO DE S CAMPOS
55012352: RODRIGO DE OLIVEIRA CUNHA
55021085: TONE GABRIEL DE ARAUJO MARQUES
55013040: WELLINGTON JOSE DO REGO BARRETO

## REGRAS DE DESENVOLVIMENTO
- App: HTML/CSS/JS puro, sem frameworks
- Sempre usar git pull antes de editar
- Push sempre com token: git push https://ghp_***@github.com/GNgestao/gn-gestao.git main
- Git config: user.email gabrielnascimento1995@gmail.com / user.name GNgestao
- Nunca hardcodar JWT do Sênior — sempre dinâmico
- Testes do Fluxo 2 apenas em horário comercial
- TTS agora via Kokoro na VPS (porta 5050) — ElevenLabs descontinuado
- No n8n expressões dentro de campos Raw: usar {{ }} SEM o = antes
- Claude Code: versão fixada em 2.1.100 (versão 2.1.167 quebra cópia no terminal Hostinger)

## INFORMAÇÕES PESSOAIS DO GABRIEL
- Nome completo: Gabriel Nascimento
- Esposa: Sheila
- Filha: Lara
- Formação: Engenheiro Mecânico, Pós-graduação em Engenharia de Segurança do Trabalho
- Cargo: Supervisor de Serviços
- Empresa: TK Elevator (falar sempre TK Elevator, não ThyssenKrupp)
- Localização: Recife-PE, mora no Janga em Paulista-PE
- WhatsApp pessoal: 5581997818685
- Email: gabrielnascimento1995@gmail.com

## MÓDULO PLANO DE AÇÃO 5W1H — NOTAS
- Rodapé: apenas "TK Elevator" — sem "GN Gestão", sem "Gerado em...", sem data/hora do browser

## MÓDULO DOCUMENTAÇÃO — STATUS ATUAL ✅

### Integração Autentique (assinatura eletrônica) ✅ — 24/05/2026
- Conta criada em autentique.com.br
- Token API: configurado no autentique-api.js no VPS
- Script /root/autentique-api.js rodando na porta 5052 como serviço systemd (autentique-api.service)
- wkhtmltopdf instalado no VPS para conversão HTML→PDF
- Fluxo n8n "GN — Assinatura" criado com webhook gn-assinatura
- Resposta do webhook vem como array: [{ sucesso: true, gabrielLink: "..." }]
- Gabriel TKE (gabriel.nascimento@tkelevator.com) recebe link direto que abre automaticamente no browser
- Outros participantes recebem convite por email
- Gabriel deve sempre se adicionar como participante com email TKE nas atas/cartas

### Carta Técnica — CONCLUÍDA
- Fluxo Jarvis por voz funcionando: coleta título → cliente → endereço → detalhes (uma pergunta por vez)
- Layout da carta: logo TKE (tke_logotipo.png) no canto superior direito, bloco AO à esquerda, Ref. centralizada em itálico, "Prezado Cliente,", corpo justificado, assinatura "Gabriel Nascimento / Supervisor de Serviços — TK Elevator"
- Capitalização automática dos campos de voz (title case no endereço, capitalize no título)
- Rodapé: apenas "TK Elevator" — sem "GN Gestão", sem "Documento gerado em..."
- Gatilhos de voz: "gerar carta", "nova carta", "fazer carta", "escrever carta", "elaborar carta", "montar carta"
- Botão ■ de stop + comando de voz ("para", "silêncio", "stop", "cala boca") + ESC/ESPAÇO para interromper fala
- TTS corrigido: AudioContext (ArrayBuffer) em vez de <audio> — eliminou ERR_REQUEST_RANGE_NOT_SATISFIABLE
- n8n fluxo gn-documentos: modelo claude-sonnet-4-5, campos titulo/cliente/endereco/detalhes
- Arquivo tke_logotipo.png adicionado ao repositório

### Ata de Reunião — CONCLUÍDA ✅
- Fluxo Jarvis por voz: título → local → participantes em loop → itens em loop → confirmação
- Gatilhos de voz: "nova ata", "gerar ata", "criar ata", "ata de reunião", "fazer ata"
- "Repita / pode repetir / não ouvi / hein" funciona em qualquer step (1–10) sem avançar o fluxo
- Prazo convertido automaticamente para dd/mm/aaaa (por extenso, dígito ou misto)
- Step 5: aceita nome direto do próximo participante sem precisar dizer "sim"
- Palavras negativas explícitas ("não", "nenhum", "só", "acabou") encerram o loop de participantes
- Layout da ata: logo TKE | cabeçalho | tabela de participantes | tabela de itens/responsável/prazo | tabela de assinaturas | assinatura Gabriel | rodapé TK Elevator
- Tabela de assinaturas: 3 colunas (Participante | E-mail | Assinatura), Gabriel excluído (tem assinatura dedicada)
- Ata gerada 100% dos dados do formulário — sem chamada ao n8n / sem texto de IA
- Funções auxiliares: _converterNumerosExtenso() (extenso→dígito, ordinais), _ataConverterData(), _ataConverterEmail()
- _ataUltimaPergunta: rastreia última pergunta para suporte ao "repita"

## MÓDULO CIPA — STATUS ATUAL ✅ (28/05/2026)

- Formulário completo com 7 itens pré-carregados (EPI, Ergonomia, Acidentes, etc.)
- Geração de PDF formatado com layout profissional
- Envio para assinatura via Autentique integrado
- Integração com Jarvis por voz e texto (gatilhos: "nova ata cipa", "gerar ata cipa", "cipa")
- Nó CIPA adicionado ao hub neural
- Header com gradiente laranja/roxo igual aos outros módulos
- Botão "← GN Gestão" (logo TKE e referências Zona Vip removidos)

## REBRAND — GN Gestão (28/05/2026)

- "Zona Vip" removido de todos os módulos (título, login, hub, botões, PDF, JS strings)
- Todos os botões "← Zona Vip" substituídos por "← GN Gestão"
- Logo TKE removido da interface CIPA (app é pessoal, sem branding corporativo)

## JARVIS — MELHORIAS RECENTES (24/05/2026)
- Silêncio: interceptado imediatamente no início de gnExecutar, antes do webhook e respostas fixas
- Triggers de silêncio: ['silêncio', 'silencio', 'stop', 'cala boca', 'cale-se', 'cala', 'basta'] — só ativa com menos de 4 palavras
- "para" e "chega" removidos da lista (causavam falsos positivos em "enviar para assinatura")
- Após silêncio: gnModoVoz=false, gnConversationMode=false — só acorda com "Jarvis"
- gnVoltarHub(): função universal de retorno ao hub para todos os módulos

## JARVIS — MELHORIAS RECENTES (26-27/05/2026)

### Chat de texto ✅
- Chat com histórico scrollável e bolhas estilo WhatsApp (gj-msg-user / gj-msg-bot)
- Histórico persiste na sessão via localStorage('jarvis_chat_history')
- Flag window._gjModoTexto: texto → sem TTS; voz → TTS normal
- globalJarvisSend() chama webhook gn-assistente diretamente (com memória PostgreSQL)
- enviarCartaAssinatura() e enviarAtaAssinatura() respeitam _gjModoTexto

### Abertura de sites e pesquisa ✅
- Abertura por voz/texto: "abrir X", "abre o X", "vai para X", "acessa X"
- Implementação: window.open() com fallback para location.href (resolve popup blocker do Chrome)
- Sites mapeados: TK Mobile (https://mobile.br.tkelevator.com/TKEMobile/Default.aspx), Gmail, YouTube, WhatsApp, Google, n8n, GitHub, Autentique, ChatGPT, Claude
- Sites não mapeados: extrai domínio e tenta https://dominio.com
- Pesquisa em sites: "pesquisar X no YouTube/Google/Spotify/Maps" com encodeURIComponent
- Limpeza de XML nas respostas: 5 passes de regex (function_calls, invoke, trigger, url, tags genéricas)
- Detecção em gnExecutar() (voz) e globalJarvisSend() (texto), antes do webhook

### Abertura de módulos GN Gestão ✅
- Bloco `_modulosGN` em gnExecutar(): verifica comandos de módulo ANTES do bloco _aberturaGatilhos (sites externos)
- Módulos mapeados: manutenção preditiva, preditiva, plano, reconhece, reparo, documentação, cipa, gestão de equipe, hub, voltar
- Suporta variações com e sem acento (ex: "documentacao" e "documentação")
- Funciona por voz e por texto via globalJarvisSend()
- Responde: "Abrindo [módulo], Chefe." antes de navegar

### Memória e API ✅
- Memória permanente funcionando: conversas salvas no PostgreSQL
- Créditos API Anthropic recarregados: USD 5,98 disponíveis

## JARVIS — MELHORIAS (28/05/2026)
- Silêncio filtrado: threshold 50KB — áudio silencioso não vai mais ao Deepgram
- TTS: timeout 25s, buffer limitado a 1,5MB com truncamento automático
- Microfone: echoCancellation, noiseSuppression, autoGainControl, sampleRate 16000
- Pesquisa em sites por texto funcionando
- Sites não mapeados: fallback para busca no Google automaticamente
- Jarvis abrindo sites por voz: PENDENTE (popup blocker Chrome)

## BUGS CORRIGIDOS (28/05/2026)
- Hub ficando em branco ao restaurar sessão com CIPA como última tela: `case 'cipa'` adicionado ao switch do DOMContentLoaded + guard no showApp()
- Fundo estrelado vazando atrás do módulo CIPA: `#screenCIPA` com `isolation:isolate` no CSS
- Fundo estrelado vazando atrás do Plano de Ação: `#screenPlano` com `isolation:isolate` no CSS

## RECONHECE+ — Correções (26-27/05/2026)
- Fórmula TOTAL corrigida: ptsIni + prod + assiduidade - marcacao + quaseAcidente + treinamento - manPrev
- Arredondamento para 2 casas decimais
- Coluna TOTAL sticky (sempre visível na tabela)
- PDF: produtividade aparecendo corretamente, centralizada
- Data de geração removida do PDF
- Login e tela ativa persistem após F5

## REPARO SUBCONTRATADO — Correções (26-27/05/2026)
- Botão "+ Serviço" funcionando
- Encaixe automático multi-dia corrigido
- Login e tela ativa persistem após F5

## HUB — Correções (26-27/05/2026)
- Jarvis duplicado (sol laranja) removido
- Jarvis móvel restaurado no hub
- Canvas Three.js não sobrepõe mais as telas dos módulos
- Fundo roxo (#1e1040) em todos os módulos
- Hub centralizado com tamanho correto

## SERVIÇOS VPS ATIVOS (187.127.26.136)
> ⚠️ VPS reinstalada em 03/06/2026 — serviços abaixo são os confirmados funcionando após reconfiguração
- **n8n** (Docker) — https://n8n.srv1610251.hstgr.cloud (funcionando)
- **Kokoro TTS** (Docker, porta 5050) — funcionando
- **Evolution API v1.7.4** (Docker, porta 8081) — gn-whatsapp conectado no 5581982381146
- **autentique-api.service** (porta 5052) — /root/autentique-api.js, systemd — **a reconfigurar**
- **jarvis-restart-api** (porta 5051) — restart do Jarvis via webhook — **a reconfigurar**
- **tac-api.service** (porta 5053) — /root/tac-api.js, systemd
- **he-api.service** (porta 5054) — /root/he-api.js, systemd
- **memoria-api.service** (porta 5056) — /root/memoria-api.js, systemd — memória semântica pgvector
- **ferias-api.service** (porta 5057) — /root/ferias-api.js — API férias PostgreSQL

## INFRA VPS — Instalações (26-27/05/2026)
- wkhtmltopdf instalado para conversão HTML→PDF (Autentique)
- node-fetch@2 instalado para Autentique API (/root/autentique-api.js)

## STATUS RECENTE — 04/06/2026

### VPS reinstalada do zero em 03/06/2026 — Totalmente restaurada em 04/06/2026

**Serviços funcionando:**
- n8n: https://n8n.srv1610251.hstgr.cloud (Docker)
- Kokoro TTS: porta 5050 (Docker)
- Evolution API v1.7.4: porta 8081 (Docker, gn-whatsapp conectado no 5581982381146)
- encryptionKey n8n: `f8H8OM+uM7ktt7iUygzgW8YHlwNdy+yJ` — **NUNCA apagar manualmente**
- PostgreSQL: container `n8n-postgres-1` na rede n8n_default (host: n8n-postgres-1, db: evolution, user: postgres, senha: evo123)
- Tabela `jarvis_memoria` criada e funcionando
- wkhtmltopdf instalado no host VPS
- autentique-api.service (porta 5052) — /root/autentique-api.js — rodando
- jarvis-restart-api (porta 5051) — /root/jarvis-restart-api.js — rodando
- tac-api.service (porta 5053) — /root/tac-api.js — rodando
- he-api.service (porta 5054) — /root/he-api.js — rodando
- memoria-api.service (porta 5056) — /root/memoria-api.js — rodando (memória semântica pgvector)
- node_modules em /root (express, node-fetch@2, form-data)

### Fluxos n8n restaurados (todos ativos)
- [x] GN Assistente Inteligente — ID: mVZ1RyggUw9mnVgF
- [x] GN Text to Speech — ID: CeXOWX6ob1j49nNq
- [x] Fluxo 2 — Autorização HE Sênior — ID: TBRd8vtv0k6iZNCK (cron: seg-sex 8h)
- [x] Fluxo 3 — Banco de Horas Diário — ID: v6hwWcWGsScfDdEX (cron: seg-sex 8h)
- [x] Fluxo 1 — TAC Mobile — ID: egsKZ2811VPbqLZu (cron: a cada 30min, envia para 5581982381146, envia mesmo quando vazio, inclui número do elevador)
- [x] GN Documentos — ID: 5KgsFjzHjpAJHtXk
- [x] GN Assinatura — ID: XU0S0i1FZUZSIG9x

### Credencial PostgreSQL n8n
- Nome: Conta Postgres
- ID: 0KDK2a9qvNkGe601

### Scripts de recriação dos fluxos
Salvos em /scripts/ no repositório GitHub para uso futuro em caso de nova reinstalação.

## STATUS RECENTE — 07/06/2026

### Memória semântica implementada ✅
- pgvector instalado no PostgreSQL (container evolution-postgres)
- Tabela `jarvis_memoria_v2` com embeddings 1024 dimensões (modelo voyage-3-lite)
- memoria-api.service (porta 5056) rodando com /root/memoria-api.js
- Fluxo n8n atualizado: adicionados nós "Buscar Fatos" e "Salvar Memória Semântica"
- Voyage AI: conta criada em dashboard.voyageai.com, organização GN Gestão

### Jarvis — melhorias ✅
- Abertura de sites por voz e texto funcionando: window.open() com fallback location.href (popup blocker resolvido)
- Bloco `_modulosGN` em gnExecutar(): módulos GN abertos antes da lógica de sites externos
- Wake words: 4 novas variações adicionadas (jabez, jalvez, jalvis, jarvy) — total 16 variações

## STATUS RECENTE — 08/06/2026

### Plano de Ação — importar PDF do laudo ✅ CONCLUÍDO
- Lê PDF automaticamente via FileReader base64 e envia para API Claude como documento nativo
- Modelo: claude-sonnet-4-6, max_tokens 8000

### Plano de Ação — campo data de início na análise por IA ✅
- Campo data de início adicionado no formulário de análise por IA
- Itens gerados herdam a data de início do plano em vez de ficarem com `start:''`

### Jarvis — abertura de módulos GN Gestão por voz e texto ✅
- Bloco `_modulosGN` implementado em gnExecutar()
- Módulos verificados antes do bloco de sites externos (_aberturaGatilhos)
- Funciona por voz e por texto via globalJarvisSend()

### Jarvis — wake words ✅
- 16 variações totais incluindo jabez, jalvez, jalvis, jarvy

### Jarvis — abertura de sites ✅
- window.open() com fallback location.href funcionando por voz e texto (popup blocker resolvido)

## STATUS 08/06/2026 — Módulo Gestão de Equipe (em desenvolvimento)

- Módulo criado e acessível pelo hub orbital e pelo Jarvis (voz/texto)
- **Aba Férias:** tabela por mês (linhas=meses, células=técnicos), adicionar/editar/deletar férias por técnico, dados salvos no localStorage (`ge_ferias`)
- **Aba Escala:** gerador automático 2x1, respeita férias, grupos laranja/azul/verde/fixo
- PENDENTE: layout das férias precisa ser melhorado para ficar igual ao modelo de referência
- PENDENTE: escala precisa de revisão e ajustes de regras de negócio

### Grupos da equipe:
- **Laranja:** Giliard, Humberto, Klebson Ramos, Elenildo, Klebson Andrade, Charlington, Rodrigo
- **Azul:** Evaldo, Wellington, Alisson, Adriano Fran, Joaz, Tone
- **Verde:** Bruno, Diego, Paulo Andre, Rodolfo, George, Durval
- **Fixos:** Laercio, Marcelo, Adriano Rog

### Regras de escala:
- Grupos coloridos: 2x1 (trabalha 2 fins de semana, folga 1)
- Fixos: trabalham todos os sábados 4h
- SRM sáb: Bruno 08-17h, Humberto 13-22h
- SBV: Paulo André (sub: Alisson, Giliard, Charlington)
- SPO sáb/dom: Wellington e Klebson Ramos alternados
- ERM: Adriano Rog (fixo) 08-12h
- TRF: Laercio 08-12h, Marcelo 12-17h (fixos)
- Noturno Filial dom: Rodrigo 22-07h (a cada 4 semanas)
- Domingos: Klebson Andrade (SRM/SPO), George (RHP/SPO), Adriano Fran (SRM/SPO/RHP)

## STATUS 10/06/2026 — Módulo Gestão de Equipe continuação

1. Tabela `gestao_ferias` criada no PostgreSQL (n8n-postgres-1, db evolution)
2. Serviço `ferias-api.service` criado na porta 5057 (/root/ferias-api.js)
3. Férias 2026 pré-populadas no banco com 22 técnicos
4. Fluxos n8n criados:
   - **GN Ferias** (ID: x5CHodNojPR73nIV) — POST webhook/gn-ferias — salva férias
   - **GN Ferias GET** (ID: 51HGqebHl422nAxM) — GET webhook/gn-ferias-get — busca férias
   - **GN Ferias Memoria** (ID: nEsQxUuPQmdk1fWt) — POST webhook/gn-ferias-memoria — salva na memória semântica
5. Jarvis consegue programar férias por voz/texto: "programe férias de X para DD/MM/YYYY até DD/MM/YYYY"
6. App busca férias via HTTPS (webhook n8n) para evitar mixed content
7. Cache do browser desativado via meta tags
8. Jarvis NÃO deve inventar respostas — se não sabe fazer algo deve informar

## STATUS 11/06/2026 - Correções

1. tac-api.js reescrito com retry automático (3 tentativas, timeout 15s, intervalo crescente 3s/6s)
2. Quando TK Mobile falha após 3 tentativas, retorna lista vazia em vez de erro — fluxo n8n nunca quebra
3. Fluxo TAC Mobile n8n configurado com neverError no nó Buscar OS
4. Plano de Ação max_tokens aumentado para 16000 para laudos grandes

## STATUS 11/06/2026 - Correção TAC Mobile

- tac-api.js reescrito completamente com tratamento robusto de encoding
- Problema raiz: TK Mobile retornava caracteres latin1 corrompidos no campo Relato das OS
- Solução: tac-api agora parseia o JSON da TK Mobile, limpa todos os campos string e reconstrói JSON limpo antes de retornar
- Retry automático: 3 tentativas com timeout 15s e intervalo crescente
- Falha total retorna lista vazia em vez de erro — fluxo n8n nunca quebra
- URL do nó Buscar OS atualizada para http://172.17.0.1:5053/tac (IP do host Docker)

## PENDÊNCIAS GERAIS

### Módulos novos
- [ ] Módulo Gestão de Equipe — em desenvolvimento (ver seção STATUS 08/06/2026 acima)
- [ ] Módulo Perito Judicial / Gestão de ARTs e Laudos (~50k tokens)

### Jarvis / Integrações
- [ ] Integração TK Mobile com Jarvis — fluxo base: Fluxo 1 - TAC Mobile (~20k tokens)
- [ ] Fluxo Sênior — consulta HE em tempo real via Jarvis (~15k tokens)
- [ ] Lista de clientes — endereços memorizados no Jarvis (~5k tokens)
- [ ] Integração Gmail + Google Calendar (~40k tokens)
- [ ] TTS streaming / melhorar latência (~20k tokens)
- [ ] Whisper local — substituir Deepgram (~15k tokens)
- [x] Memória semântica de fatos implementada via pgvector + Voyage AI (07/06/2026)
- [ ] Aumentar limite de memória convencional para 50 msgs (~5k tokens)

### Hub / App / Visual
- [ ] Hub 3D estilo Obsidian (~30k tokens)
- [ ] Tela de login futurista (~15k tokens)
- [ ] PWA — transformar GN Gestão em app instalável (~8k tokens)
- [ ] Rebrand Jarvis → Ultron: nome, wake word, visual (~3k tokens) — Gabriel ainda decidindo

### Segurança / Infra
- [ ] Senha mestra antes do login (~10k tokens)
- [ ] Rotacionar API keys e tokens expostos (~2k tokens)


## STATUS GESTÃO DE EQUIPE — 17/06/2026

### Aba Escala de Plantões — FUNCIONAL
- Layout por mês (cards de FDS), a partir de 13/06/2026
- Ciclo de cores verde→laranja→azul (grupo da cor folga naquele FDS); fixos sempre trabalham
- Alocação automática por regras (GE_REGRAS): cada técnico tem pode[]/titular[]/turno
- Setores: SRM(2 sáb/1 dom), RHP(2 sáb/2 dom), ERM(1 sáb), SPO(1 sáb/1 dom), SBV(1 sáb), TRF(2 sáb), NTF(sáb a cada 4 semanas desde 27/06, dom toda semana)
- Slots vazios mostram "— vago"; todos os campos (técnico, horário, supervisor) editáveis inline
- **Botão Salvar** salva tudo no PostgreSQL via n8n; recarrega dados salvos ao gerar
- Painel lateral de técnicos (botão 👥 Técnicos) com badge de folga, position:fixed
- Humberto bloqueado até 01/07/2026 (atestado); Edvaldo inativo (atestado, só SRM sáb quando voltar)
- Datas tratadas como string YYYY-MM-DD (evita bug de fuso UTC-3)

### Aba Férias — NOVO LAYOUT FUNCIONAL
- Tabela anual: 12 meses em colunas, técnicos empilhados nas células do mês
- Data início em vermelho, fim em verde (formato DD-MM)
- Múltiplos anos empilhados; botão "+ Adicionar ano" cria próximo ano
- Clique na célula abre modal para adicionar/editar; × remove
- PENDENTE: ajustes que Gabriel vai pedir (a definir)

### Infra Escala/Férias (n8n + ferias-api porta 5057)
- Tabela escala_plantoes: UNIQUE(sabado,dia,setor,horario); supervisor em setor='SUP'
- Webhooks n8n (todos retornam array via $input.all().map):
  - gn-escala-get?ano= (bBqprTaVHWU3MRJv)
  - gn-escala-post (yQ8eaTPjrEpXbxKe) — rota no body decide /escala/plantao ou /escala/supervisor
  - gn-ferias-get?ano= (51HGqebHl422nAxM)
  - gn-ferias-save (1keyNWJSpZaO3div)
  - gn-ferias-delete (NWsYrYvAHHdVjVZl)
- TODAS as chamadas do app passam por n8n HTTPS (nunca HTTP direto — Mixed Content)
- ferias-api roteia para 172.17.0.1:5057 (IP host Docker)

### Fluxo 2 HE — BLOQUEIO EXTERNO
- he-api (porta 5054) e código corretos; bug de período (dataFinal) foi corrigido e revertido
- Erro 500 "Usuário sem permissão para alterar marcações código 1370": bloqueio de permissão no Senior
- Gabriel confirmou que o bloqueio é real (não conseguia autorizar nem manualmente) — aguardando retorno da empresa
- Backup: /root/he-api.js.bak

### Regras dos técnicos na Escala (resumo GE_REGRAS)
- 24 técnicos: 7 laranja, 7 azul (Rodolfo é azul), 6 verde, 3 fixos (Laercio/Marcelo/Adriano Rog)
- Luciano é verde (matrícula 55012623)
- Regras completas de pode/titular por setor/dia/turno estão em GE_REGRAS no index.html


## STATUS FLUXOS HE/BH — 19/06/2026

### Fluxo 2 — Autorização HE — VOLTOU A FUNCIONAR
- O bloqueio de permissão no Senior foi resolvido (lado da empresa)
- Autorização de HE (códigos 613→663 diurno, 614→664 noturno) operando normalmente
- he-api porta 5054, lógica original mantida (dataFinal = ontem); backup em /root/he-api.js.bak

### Fluxo 3 — Banco de Horas — CORRIGIDO
- Bug: retornava 00:00 para todos os técnicos
- Causa: a API do Senior mudou a estrutura da resposta de saldo-mensal. O campo `saldo` no topo do JSON é só do mês corrente (sempre zerado até fechar). O saldo real do ponto vigente está dentro do array `horasVencendo`, por período (ex: {periodo:"Julho 2026", saldo:"04:23"})
- Correção em bh-api.js (porta 5055): em vez de ler r.body.saldo, agora calcula o período de referência do ponto vigente e busca em horasVencendo:
  - Se hoje >= dia 11 → período = mês seguinte (ponto 11/MM a 10/MM+1 refere-se ao mês seguinte)
  - Se hoje < dia 11 → período = mês atual
  - Ex: hoje 19/06 → ponto 11/06 a 10/07 → refere-se a "Julho 2026"
- Endpoint real do bh-api: GET /gestaoponto-backend/api/colaborador/{colabId}/bancos-horas/saldo-mensal?codigoCalculo=1370&projecaoMeses=3&gestor=S
- Auth G7: POST /api/senior/auth/g7
- Backup em /root/bh-api.js.bak
- Validado: Giliard 04:23, saldos variados (positivos/zerados/negativos), ordenados decrescente
