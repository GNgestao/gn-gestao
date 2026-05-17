# CLAUDE.md — Projeto GN Gestão / Jarvis

## CONTEXTO DO PROJETO
Sistema de gestão operacional pessoal e profissional de Gabriel Nascimento, gestor de manutenção de elevadores da ThyssenKrupp em Recife-PE. Inclui app web, automações n8n e assistente de voz inteligente chamado Jarvis.

## INFRAESTRUTURA
- VPS: Hostinger, IP 187.127.26.136, Ubuntu 24.04
- n8n: https://n8n.srv1610251.hstgr.cloud (container n8n-n8n-1)
- App: https://gngestao.github.io/gn-gestao/
- GitHub: github.com/GNgestao/gn-gestao (arquivo principal: index.html)
- Evolution API (WhatsApp): http://187.127.26.136:8081, instância gn-whatsapp, apikey gn-evolution-2026, número 5581982381146
- SSH: ssh root@187.127.26.136

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

## JARVIS (ASSISTENTE DE VOZ)
- Wake word: "Jarvis"
- Chama Gabriel de "Chefe"
- Webhook principal: POST https://n8n.srv1610251.hstgr.cloud/webhook/gn-assistente (body: {comando: texto})
- Webhook TTS: POST https://n8n.srv1610251.hstgr.cloud/webhook/gn-tts (body: {texto: resposta})
- ElevenLabs Voice ID: EXAVITQu4vr4xnSDxMaL (Bella — plano free)
- ElevenLabs API Key: sk_*** (ver em ElevenLabs → Desenvolvedores)
- Modelo ElevenLabs: eleven_multilingual_v2
- Cérebro: Claude API (claude-sonnet-4-5) via n8n
- Anthropic API Key: sk-ant-api03-*** (ver no n8n, nó Claude API)
- Acesso: exclusivo superadmin (gabrielnascimento1995@gmail.com)

## FLUXOS N8N

### Fluxo 2 — Autorização Automática HE Sênior
- Cron: 0 8 * * 1-5 (seg-sex 8h)
- Login: POST https://platform.senior.com.br/auth/LoginServlet (form-urlencoded)
- Usuário: 10583194@thyssenkrupp.com / Senha: Initpass*1
- Empresa: 8550-1, codigoCalculo: 1370
- Autoriza HE ≤ 2h, códigos 613→663, 614→664
- IMPORTANTE: funciona apenas em horário comercial (token G5 fora do horário)

### Fluxo 3 — Saldo Banco de Horas
- Cron: 0 14 * * 5 (toda sexta 14h)
- Webhook teste: https://n8n.srv1610251.hstgr.cloud/webhook-test/teste-ranking
- Busca saldo via /bancos-horas/saldo-mensal?codigoCalculo=1370&projecaoMeses=3&gestor=S
- Período: dia 11 do mês atual até dia 10 do próximo (se dia >= 11)

### GN — Assistente Inteligente
- Webhook: POST /webhook/gn-assistente
- Body recebido: {comando: texto}
- Resposta: {resposta: texto}

### GN — Texto para fala
- Webhook: POST /webhook/gn-tts
- Body recebido: {texto: resposta}
- Retorna: audio/mpeg binário via ElevenLabs

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
55018679: GILIARD FELIPE FILGUEIRA NASCIMENTO
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
- Push sempre com token: git push https://ghp_***@github.com/GNgestao/gn-gestao.git main (renovar quando necessário)
- Git config: user.email gabrielnascimento1995@gmail.com / user.name GNgestao
- Nunca hardcodar JWT do Sênior — sempre dinâmico
- Testes do Fluxo 2 apenas em horário comercial
- ElevenLabs plano free: usar apenas vozes padrão (não de biblioteca)

## PENDÊNCIAS
- [ ] Wake word "Jarvis" ativando automaticamente ao entrar no módulo
- [ ] Voz Jarvis em português brasileiro (model eleven_multilingual_v2)
- [ ] Fluxo de monitoramento de prazos (tokens, credenciais) via Jarvis
- [ ] Módulo Gestão da Equipe
- [ ] Módulo Documentação
- [ ] Upgrade ElevenLabs para voz masculina Adam
