# CLAUDE.md — Projeto GN Gestão / Jarvis

## CONTEXTO DO PROJETO
Sistema de gestão operacional pessoal e profissional de Gabriel Nascimento, gestor de manutenção de elevadores da ThyssenKrupp em Recife-PE. Inclui app web, automações n8n e assistente de voz inteligente chamado Jarvis.

## INFRAESTRUTURA
- VPS: Hostinger, IP 187.127.26.136, Ubuntu 24.04
- n8n: https://n8n.srv1610251.hstgr.cloud (container n8n-n8n-1)
- App: https://gngestao.github.io/gn-gestao/
- GitHub: github.com/GNgestao/gn-gestao (arquivo principal: index.html, ~9200+ linhas)
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
- Documentação — Carta Técnica ✅ concluída; Ata de Reunião ✅ concluída (bug pendente)

### Módulos futuros:
- Gestão da Equipe

### Hub:
Rede neural animada. GN no centro, módulos ao redor flutuando. Fundo estrelado global.

## JARVIS — ASSISTENTE DE VOZ

### Configuração atual:
- Wake words reconhecidas: jarvis, charles, chaves, jarves, jarvi
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
- Sites mapeados: TK Mobile (https://mobile.br.tkelevator.com/TKEMobile/Default.aspx), Gmail, YouTube, WhatsApp, Google, n8n, GitHub, Autentique, ChatGPT, Claude
- Sites não mapeados: extrai domínio e tenta https://dominio.com
- Pesquisa em sites: "pesquisar X no YouTube/Google/Spotify/Maps" com encodeURIComponent
- Limpeza de XML nas respostas: 5 passes de regex (function_calls, invoke, trigger, url, tags genéricas)
- Detecção em gnExecutar() (voz) e globalJarvisSend() (texto), antes do webhook

### Memória e API ✅
- Memória permanente funcionando: conversas salvas no PostgreSQL
- Créditos API Anthropic recarregados: USD 5,98 disponíveis

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
- **autentique-api.service** (porta 5052) — /root/autentique-api.js, systemd, restart automático
- **jarvis-restart-api** (porta 5051) — restart do Jarvis via webhook
- **Kokoro TTS** (porta 5050) — /usr/local/bin/jarvis-tts-server.py
- **n8n** (Docker) — https://n8n.srv1610251.hstgr.cloud

## INFRA VPS — Instalações (26-27/05/2026)
- wkhtmltopdf instalado para conversão HTML→PDF (Autentique)
- node-fetch@2 instalado para Autentique API (/root/autentique-api.js)

## PENDÊNCIAS GERAIS

### Módulos novos
- [ ] Módulo Gestão de Equipe + férias + escala de plantões (~40k tokens)
- [ ] Módulo Perito Judicial / Gestão de ARTs e Laudos (~50k tokens)
- [ ] Ata CIPA via Jarvis (~20k tokens) — modelo analisado

### Jarvis / Integrações
- [ ] Integração TK Mobile com Jarvis — fluxo base: Fluxo 1 - TAC Mobile (~20k tokens)
- [ ] Fluxo Sênior — consulta HE em tempo real via Jarvis (~15k tokens)
- [ ] Lista de clientes — endereços memorizados no Jarvis (~5k tokens)
- [ ] Integração Gmail + Google Calendar (~40k tokens)
- [ ] TTS streaming / melhorar latência (~20k tokens)
- [ ] Whisper local — substituir Deepgram (~15k tokens)
- [ ] Memória permanente de fatos + aumentar limite para 50 msgs (~10k tokens)
- [ ] Autentique: assinatura automática via API (opcional)

### Hub / App / Visual
- [ ] Hub 3D estilo Obsidian (~30k tokens)
- [ ] Tela de login futurista (~15k tokens)
- [ ] PWA — transformar GN Gestão em app instalável (~8k tokens)
- [ ] Rebrand: remover menções Zona Vip (~3k tokens)
- [ ] Rebrand Jarvis → Ultron: nome, wake word, visual (~3k tokens) — Gabriel ainda decidindo

### Segurança / Infra
- [ ] Senha mestra antes do login (~10k tokens)
- [ ] Rotacionar API keys e tokens expostos
