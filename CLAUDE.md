# CLAUDE.md — Projeto GN Gestão / Jarvis

## CONTEXTO DO PROJETO
Sistema de gestão operacional pessoal e profissional de Gabriel Nascimento, gestor de manutenção de elevadores da ThyssenKrupp em Recife-PE. Inclui app web, automações n8n e assistente de voz inteligente chamado Jarvis.

## INFRAESTRUTURA
- VPS: Hostinger, IP 187.127.26.136, Ubuntu 24.04
- n8n: https://n8n.srv1610251.hstgr.cloud (container n8n-n8n-1)
- App: https://gngestao.github.io/gn-gestao/
- GitHub: github.com/GNgestao/gn-gestao (arquivo principal: index.html, 7500+ linhas)
- Evolution API (WhatsApp): http://187.127.26.136:8081, instância gn-whatsapp, apikey gn-evolution-2026, número 5581982381146
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

### Módulos futuros:
- Gestão da Equipe
- Documentação

### Hub:
Rede neural animada. GN no centro, módulos ao redor flutuando. Fundo estrelado global.

## JARVIS — ASSISTENTE DE VOZ

### Configuração atual:
- Wake words reconhecidas: jarvis, charles, chaves, jarves, jarvi
- Chama Gabriel de "Chefe" ou "Senhor" (alterna aleatoriamente)
- Webhook principal: POST https://n8n.srv1610251.hstgr.cloud/webhook/gn-assistente (body: {comando: texto})
- Webhook TTS: POST https://n8n.srv1610251.hstgr.cloud/webhook/gn-tts (body: {texto: resposta})

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

### CÉREBRO — CLAUDE API
- Modelo: claude-sonnet-4-5
- API Key: no nó API Claude do n8n (x-api-key)
- Fluxo n8n: Webhook → Buscar Memória → Código JS → API Claude → Responder ao Webhook + Salvar Memória

### FLUXO N8N — GN Assistente Inteligente
Sequência:
1. Webhook recebe {comando: texto}
2. Buscar Memória: SELECT role, conteudo FROM jarvis_memoria ORDER BY criado_em DESC LIMIT 20
3. Código JS: monta system prompt com histórico + mensagem atual
4. API Claude: chama https://api.anthropic.com/v1/messages
5. Responder ao Webhook: retorna {resposta: texto}
6. Salvar Memória: INSERT INTO jarvis_memoria (role, conteudo) VALUES (user, comando), (assistant, resposta)

### FLUXO N8N — GN Texto para Fala
- Webhook recebe {texto: resposta}
- Nó Code: substitui vírgulas por pontos (evita bug de pronúncia)
- HTTP Request: POST http://187.127.26.136:5050/tts
- ATENÇÃO: usar {{ $json.body.texto }} SEM o = antes
- Retorna: audio/wav binário

## FLUXOS N8N

### Fluxo 2 — Autorização Automática HE Sênior
- Cron: 0 8 * * 1-5 (seg-sex 8h)
- Login: POST https://platform.senior.com.br/auth/LoginServlet
- Usuário: 10583194@thyssenkrupp.com / Senha: Initpass*1
- Empresa: 8550-1, codigoCalculo: 1370
- Autoriza HE ≤ 2h, códigos 613→663, 614→664
- IMPORTANTE: funciona apenas em horário comercial

### Fluxo 3 — Saldo Banco de Horas
- Cron: 0 14 * * 5 (toda sexta 14h)
- Busca saldo via /bancos-horas/saldo-mensal

## 24 TÉCNICOS (matrícula: nome)
55007445: ADRIANO FRANCISCO DA SILVA
55013039: ADRIANO ROGERIO BRAZ DA SILVA
55016328: ALISSON MENDES CHAGAS
55007813: ANTONIO AMARO BARRETO FILHO
55006085: BRUNO DANILO FIRMINO DA SILVA
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
55000153: MOISES SEVERINO DA SILVA
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

## PENDÊNCIAS ABERTAS
- [x] Busca web no n8n para o Jarvis responder perguntas atuais (notícias, dados em tempo real)
- [x] Systemd para iniciar Kokoro TTS e jarvis-proxy automaticamente no reboot da VPS
- [ ] Campo de texto no módulo Jarvis para comandos sem voz
- [ ] Monitoramento créditos Deepgram com alerta via WhatsApp
- [ ] Agente Windows para abrir sites/Chrome via comando de voz
- [ ] Integração TK Mobile — OS abertas e demandas operacionais
- [ ] Fluxo Sênior para consulta de horas extras em tempo real via Jarvis
- [ ] Módulo Gestão da Equipe
- [ ] Módulo Documentação
- [ ] Upgrade ElevenLabs para voz Adam (quando quiser qualidade premium)
- [ ] Fluxo de monitoramento de prazos (tokens, credenciais) via Jarvis
- [x] Integrar busca web no n8n para Jarvis ter acesso à internet em tempo real
- [ ] Verificar possibilidade do Jarvis abrir aplicativos no Windows via comando de voz
- [ ] Melhorias de layout no app GN Gestão (detalhes a definir)
- [ ] Retirar mensagem de status quando Jarvis está falando
- [ ] TTS streaming para reduzir tempo de resposta em textos longos
- [ ] Memória permanente de fatos e perfil do Gabriel (separada das conversas)
- [ ] Aumentar limite de memória de 20 para 50 mensagens no contexto do Claude
