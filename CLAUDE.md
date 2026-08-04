# GN Gestão — Notas de Sessão

## ⚠️ INCIDENTE CRÍTICO — NUNCA REPETIR

**O que aconteceu:** uma edição manual do arquivo /home/node/.n8n/config causou travamento (lockup) do n8n, exigindo reinstalação completa do VPS do zero. Todos os workflows n8n foram perdidos e precisaram ser recriados manualmente.

**Regras permanentes para evitar repetição (NUNCA violar):**
1. NUNCA editar manualmente /home/node/.n8n/config
2. NUNCA rodar docker run que monte o volume do n8n diretamente
3. SEMPRE fazer backup do docker-compose antes de qualquer alteração: cp /docker/n8n/docker-compose.yml /docker/n8n/docker-compose.yml.bak
4. Configurar o n8n APENAS via variáveis de ambiente no docker-compose.yml
5. O encryptionKey do n8n NUNCA deve ser deletado ou substituído manualmente
6. Antes de qualquer comando que toque em arquivos de configuração de sistema, containers, ou infraestrutura (não código da aplicação), parar e confirmar com Gabriel explicitamente

Essa seção não deve ser removida ou movida em nenhuma atualização futura do arquivo.

## PENDÊNCIAS REAIS ATUAIS

> Esta é a única lista de pendências com validade. As listas nas seções de sessões anteriores são históricas e estão desatualizadas.

- [ ] 1. Completar SIGEO AJ/JT TRT-6 — aguardando ISS Paulista (ir presencialmente)
- [x] 2. Cockpit TKE — cockpit-api.js porta 5063 funcionando (análise de falhas, histórico, Jarvis integrado) ✓ IMPLEMENTADO E VALIDADO PONTA A PONTA 02/08/2026
- [ ] 3. Power BI corporativo TKE — a implementar após Cockpit
- [ ] 4. Melhorar fontes de prospecção — Indeed, Catho, TJ-PE
- [ ] 5. Envio de e-mail automático para empresas prospectadas
- [x] 6. Tela visual MAX no Hub 2D ✓ IMPLEMENTADO 01/08/2026 — nó MAX (PROJETOS), tela #screenMax com histórico de consultas
- [x] 7. Capacidade #12 Jarvis — análise de falhas do Cockpit por voz ✓ IMPLEMENTADO 01/08/2026
- [x] 8. Bug onclick cards MAX + botões Editar/Excluir ✓ IMPLEMENTADO 02/08/2026
- [x] 9. Base de conhecimento MCP TKE (217 códigos E/A, tabela gn_causas_falha, origemCausa) ✓ IMPLEMENTADO 02/08/2026 — **MIGRADO** 04/08/2026 para planilhas oficiais CT42/CT88
- [x] 10. acaoSugerida derivada de seções reais do manual MAC-DECA-0035 (fonteAcao, keyword search GIN) ✓ IMPLEMENTADO 02/08/2026

## STATUS SESSÃO — 04/08/2026

### Migração base de causas — planilhas oficiais TKE CT42 FDN e CT88 EOX/MHC2 — IMPLEMENTADA

**Motivação:** a base antiga (`gn_causas_falha`) tinha 289 registros cobrindo apenas os códigos MCP Frequencedyne (formato 1000+N / 2000+N). Os equipamentos CT88 (MC5 Belt Elevator) e CT71 (GC-MHC2) retornavam `origemCausa: 'desconhecido'` para todos os seus códigos. Duas planilhas oficiais TKE foram importadas para cobrir a carteira completa.

**Investigação de controllerType (Passo 1):**
- Sondados 3 equipamentos reais na Assets API via `/cockpit/debug/raw/:unitId`
- **Correção de documentação anterior:** 157333 foi incorretamente documentado como "Frequencedyne" — é na verdade `CT71 / GC-MHC2`. Somente 99051 é `CT42 / FREQUENCEDYNE`.
- Varredura da carteira completa (100 equip. MAX):

| controllerType | controllerTypeName | Qtd. |
|---|---|---|
| CT42 | FREQUENCEDYNE | 290 |
| CT88 | MC5 Belt Elevator | 66 |
| CT71 | GC-MHC2 | 17 |
| CT51 | TAC 32T - ETH | 1 |
| CT73 | OTIS LCB II TCB | 1 |

- CT71 (GC-MHC2) confirmado por Gabriel como coberto pela planilha CT88 ("EOX **e MHC2**") — tratado como `EOX_MHC2`.

**Nova tabela `gn_causas_falha` (PostgreSQL `n8n-postgres-1`/`evolution`):**
- Backup da tabela antiga: `gn_causas_falha_backup_20260804` (289 linhas — preservado)
- Schema novo: `id BIGSERIAL PK`, `codigo INT`, `categoria_equipamento VARCHAR(20)`, `descricao_falha TEXT`, `causa TEXT`, `acao_sugerida TEXT`, `peso_erro INT`, `bloqueia_controlador BOOLEAN`, `idioma VARCHAR(10)`, `fonte VARCHAR(30)`
- Índices: `idx_gcf_codigo_cat ON (codigo, categoria_equipamento)`, `idx_gcf_categoria ON (categoria_equipamento)`
- **353 linhas FDN** (categoria=`'FDN'`, idioma=`'pt-BR'`, fonte=`'ct42_fdn'`, 263 códigos únicos, 35 com múltiplas entradas)
- **1460 linhas EOX_MHC2** (categoria=`'EOX_MHC2'`, idioma=`'en-US'`, fonte=`'ct88_eox_mhc2'`, 1131 códigos únicos, 188 com múltiplas entradas)
- **Total: 1813 linhas**
- Planilhas fonte: `/root/ErrorCodes_CT42 FDN.xlsx` e `/root/ErrorCodes_CT88 EOX e MHC2.xlsx`
- Script de importação: `/tmp/import_causas_falha.py`
- Colunas das planilhas usadas: `ErrorCode→codigo`, `FaultDescription→descricao_falha`, `ErrorWeight→peso_erro`, `ControllerBlocked→bloqueia_controlador`, `MaintenanceFailure→causa`, `TroubleShootingAction→acao_sugerida`, `LanguageCultureName→idioma`
- Múltiplas causas/ações para o mesmo código concatenadas com `' | '` via `string_agg(DISTINCT ...)` na query

**cockpit-api.js — mudanças (Passo 4):**
- `_controllerTypeMap` adicionado ao lado de `_unitIdMap` — cache `{ unitId → controllerType }`
- Populado em `buscarEquipamentoDireto()` (busca direta) e `buscarTodosEquipamentosRaw()` (carteira completa) via `eq.controllerType`
- Mapeamento `CT42→'FDN'`, `CT71+CT88→'EOX_MHC2'`, outros→`null`
- Query `gn_causas_falha` atualizada: filtra por `(codigo, categoria_equipamento)`, agrega múltiplas linhas com `string_agg(DISTINCT ...)`
- `buildEpisodio()` atualizado: usa `causaDB.causa` (era `causa_provavel`), `origemCausa='planilha_tke'` (era `'tabela_oficial_tke'`), novo campo `idiomaFonte` no retorno
- Dicionário fixo `CAUSAS` **removido** — todos os 6 códigos que continha (5702, 3269, 1894, 1046, 2027, 1030) agora cobertos pelas planilhas
- Fallback MAC-DECA-0035 mantido apenas para FDN (`categoriaEquipamento === 'FDN'`) quando código não encontrado na planilha
- Resposta da rota agora inclui: `controllerType` e `categoriaEquipamento` no nível raiz; `idiomaFonte` em cada falha

**Testes ponta a ponta (todos ✓):**

| unitId | controllerType | categoriaEquipamento | Código validado | origemCausa | idiomaFonte |
|--------|---------------|---------------------|-----------------|-------------|-------------|
| 99051 | CT42 | FDN | 1037 (BKF=0) | planilha_tke | pt-BR |
| 206830 | CT88 | EOX_MHC2 | 1105, 4851, 1683 | planilha_tke | en-US |
| 157333 | CT71 | EOX_MHC2 | 5702 (LW) | planilha_tke | en-US |

- 99051 / código 1037 — causa: `"Contato BK não ajustado | Falha nos contatos 43 e 44 | ..."` (múltiplas causas agregadas, pt-BR) ✓
- 206830 / código 1105 — causa: `"Defective Hall Door lock | Wrong wiring and connector"` (en-US) ✓
- 157333 / código 5702 — causa: `"Loadweigher reporting negative load"`, ação: `"Run the loadweigher calibration procedure again"` (en-US) ✓

## STATUS SESSÃO — 02/08/2026

### MAX — Bug onclick + Editar/Excluir — IMPLEMENTADO

**Root cause do bug de clique:** o `div` do card era um único elemento com `display:grid` sendo o click target, mas o `div.onclick` era atribuído corretamente. Testes com Playwright confirmaram que o padrão básico funcionava. O fix real foi refatorar a estrutura do card para deixar claro quais áreas abrem o modal e quais são os botões de ação (com `stopPropagation`).

**Nova estrutura dos cards:**
- `wrap` (container com borda): envolve tudo
  - `cardBody` (área clicável → abre modal): usa `addEventListener('click', ...)` em vez de `div.onclick`
  - `acoesBar` (barra inferior): botões Editar e Excluir com `e.stopPropagation()`
- `try/catch` em `maxAbrirRelatorio` com erro visível no DOM (antes era silencioso)
- `falhasJson` tratado com `Array.isArray` + fallback `JSON.parse` para robustez

**Botão ✏️ Editar observação:**
- Abre textarea inline na `acoesBar` (não abre modal)
- Salva via `POST /webhook/gn-max-atualizar` → `PATCH cockpit-api:5063/cockpit/max/historico/:id`
- Observação exibida em dourado/itálico no card e no modal

**Botão 🗑 Excluir:**
- Confirmação via `confirm()` antes de deletar
- `POST /webhook/gn-max-excluir` → `DELETE cockpit-api:5063/cockpit/max/historico/:id`
- Fade-out (opacity 0 → remove) após exclusão bem-sucedida

**Backend (cockpit-api.js):**
- `ALTER TABLE gn_max_analises ADD COLUMN IF NOT EXISTS observacao TEXT`
- Rotas: `PATCH /cockpit/max/historico/:id` (atualiza observacao) e `DELETE /cockpit/max/historico/:id`
- `rotaMaxHistorico` inclui campo `observacao` no SELECT e no retorno JSON

**n8n workflows criados e ativos:**
- **GN MAX Atualizar** (ID `aLDBJ9NLH20secKV`, webhook `gn-max-atualizar`, POST) — proxy para PATCH cockpit-api
- **GN MAX Excluir** (ID `TgAAVZQREx0J2MQ3`, webhook `gn-max-excluir`, POST) — proxy para DELETE cockpit-api

**Commit:** `39c0e33` → pushed main.

### Modal #maxRelatorioModal — Scroll interno com cabeçalho fixo — IMPLEMENTADO 02/08/2026

- Cabeçalho (título + botões Exportar/Fechar) permanece fixo no topo com `flex-shrink:0`
- Corpo (gráfico + lista de falhas) rola internamente com `#maxRelBody { flex:1; min-height:0; overflow-y:auto }`
- `max-height:90vh` no card container impede que o modal ultrapasse a tela
- `scrollTop` resetado em `maxRelBody`, não no modal externo
- Validado com Playwright: 18 falhas renderizadas, header fixo, body scroll

**Commit:** `14b5eab` → pushed main.

### Base de conhecimento MCP TKE — IMPLEMENTADO 02/08/2026

**Tabela `gn_causas_falha` (PostgreSQL `n8n-postgres-1`/`evolution`):**
- 217 registros da tabela oficial TKE (documento `3Z.0006.XH` — fornecido por Gabriel)
- 128 erros (E001–E239, campo `codigo_orig` tipo "E037", código MAX = 1000+N) + 89 advertências (A002–A255, código MAX = 2000+N)
- Campos: `codigo INT PK`, `fonte VARCHAR`, `codigo_orig VARCHAR(10)`, `descricao_oficial TEXT`, `causa_provavel TEXT`, `acao_sugerida TEXT`
- Fonte de todos os registros: `'mcp_oficial'`

**Hipótese validada (80% aderência nos dados reais):**
- Padrão: `eventId 1000+N = Erro EN da MCP`, `eventId 2000+N = Advertência AN da MCP`
- 8/10 códigos observados em `gn_max_analises` batem perfeitamente com o padrão
- Exceções: `1894` (ACCEL_DISCONTINUITY — N=894, fora do range E001-E255, subsistema de acionamento) e `5702` (LW — Load Weigher, prefixo 5xxx, sistema de pesagem separado)

**Conflitos com dicionário fixo antigo (3 códigos sobrepostos → versionados para MCP oficial):**
- `1046` (E046): dicionário fixo → MCP oficial "P28=0: falha no circuito de segurança"
- `2027` (A027): dicionário fixo → MCP oficial "Falha no fechamento de porta"
- `1030` (E030): dicionário fixo → MCP oficial "Erro na MCINV"
- `1894`, `3269`, `5702` — **NÃO** cobertos pela tabela MCP, permanecem no dicionário fixo `CAUSAS`

**cockpit-api.js — Lógica de resolução de causa (3 camadas, por prioridade):**
1. `gn_causas_falha` (origemCausa: `'tabela_oficial_tke'`) — batch-query antes do loop de episódios
2. Dicionário fixo `CAUSAS` em memória (origemCausa: `'dicionario_fixo'`) — para 1894/3269/5702
3. Ausência total (origemCausa: `'desconhecido'`) — código não mapeado em nenhuma fonte
- `buildEpisodio(codigo, descricao, evs, causaDB)` — 4° param recebe linha do banco pré-carregada
- Campo `origemCausa` adicionado ao JSON de cada falha retornado pela API

**Teste pós-deploy (elevador 99051, 24h):** 12 episódios retornados, **todos com `origemCausa: tabela_oficial_tke`** ✓

### Base de conhecimento técnico — gn_conhecimento_manuais — IMPLEMENTADO 02/08/2026

**Tabela `gn_conhecimento_manuais` (PostgreSQL `n8n-postgres-1`/`evolution`):**
- Campos: `id SERIAL PK`, `documento VARCHAR(200)`, `secao VARCHAR(200)`, `categoria VARCHAR(100)`, `conteudo TEXT`, `palavras_chave TEXT[]`, `criado_em TIMESTAMP`
- Índices: por `documento`, por `categoria`, GIN em `palavras_chave`

**Registros inseridos (3 entradas, 2 documentos):**

| id | documento | seção | categoria | kws |
|----|-----------|-------|-----------|-----|
| 1 | MOD-DEQC-0010 - Relatório de Defeito do Encoder | Formulário completo | formulario_relatorio | 10 |
| 2 | 3Z.0006.PS - Teclas do TLS e Códigos de Estado | Teclado TLS | referencia_tls | 7 |
| 3 | 3Z.0006.PS - Teclas do TLS e Códigos de Estado | Códigos de estado da MCINV | referencia_tls | 16 |

**LOTE 1 — 3Z.0006.PS (MCINV4/MCINV5SL/MCINV6S) — INSERIDO 02/08/2026:**
- 52 registros, fonte=`'mcinv_tls'`, códigos TLS literais (ex: 670, 691, 694)
- codigo_orig = prefixo display (ex: "E0", "EA", "F4", "CC", "CF", "n0"...)
- Inclui o código 694 com 2 entradas (EF e CC — ambas válidas, sem colisão pois PK agora é `id BIGSERIAL`)
- Cobre falhas de IGBT (EU/EV/EW), encoder, limite linear, freio, CAN, renivelamento, resgate automático

**LOTE 2 — NTEE-055 Tabela A (Frequencedyne/MCINV2) — INSERIDO 02/08/2026:**
- 20 registros, fonte=`'frequencedyne_display'`, codigo=NULL, codigo_display='E0'..'F4'
- Cobre E0-EF e F1-F4 (falhas de fase, carga, tensão, encoder, freio, sinais, segurança)

**Migração de schema em `gn_causas_falha` (realizada para suportar LOTE 2):**
- `id BIGSERIAL` adicionado como nova PK (serial, substitui `codigo INT PK`)
- `codigo INT` permanece (agora nullable) com índice parcial `WHERE codigo IS NOT NULL`
- `codigo_display VARCHAR(20)` adicionado (usado por frequencedyne_display; NULL nos demais)
- Índices adicionais: `idx_gcf_codigo_display`, `idx_gcf_fonte`
- `cockpit-api.js` não sofreu alteração: query `WHERE codigo = ANY($1)` exclui NULLs automaticamente ✓

**MAC-DECA-0035 (Manual de Manutenção Preventiva) — PROCESSADO 02/08/2026:**
- 271 páginas, 9,4 MB — extraído com `pdftotext -layout` (poppler-utils)
- **135 entradas inseridas** em `gn_conhecimento_manuais`, documento=`'MAC-DECA-0035'`
- Script de processamento em `/tmp/process_mac_deca.py` (reutilizável)
- Boilerplate removido: tabelas de aplicação (Passageiro/Cargueiro/meses), rodapés, referências de figuras
- Conteúdo preservado: procedimentos, resultados esperados, não conformidades, tabelas de medidas
- Valores técnicos exatos mantidos: medidas em mm, torques em Nm, tensões em V, %

| categoria | entradas |
|-----------|----------|
| maquinario_comando | 51 |
| poco | 28 |
| cabina_em_cima | 19 |
| caixa_corrida | 17 |
| cabina_interna | 11 |
| pavimento | 7 |
| seguranca_geral | 1 |
| objetivo | 1 |
| **total** | **135** |

- Seções verificadas: 5.7 (Êmbolo do Freio), 5.11 (Teste de Deslize — inclui tabela AC2/Ômicron/SDN com velocidades 22-150m/min e distâncias 160-3582mm), 6.1 (Freio do Operador de Porta)

**Fora do escopo de ingestão (decisão permanente):**
- `NBR 16734`, `NBR 16858-1`, `NBR 16858-2` (normas ABNT): direitos autorais da ABNT — não reproduzir nem armazenar conteúdo. Referência apenas por título/número.

### acaoSugerida derivada do manual MAC-DECA-0035 — IMPLEMENTADO 02/08/2026

**Objetivo:** para códigos `mcp_oficial`, substituir ações genéricas por procedimentos reais do manual de manutenção.

**Lógica em `cockpit-api.js`:**

1. `extrairKeywords(descricaoOficial, codigoOrig)` — tokeniza a descrição oficial + código, remove stop-words PT, aplica mapa de expansão semântica (`EXPANSAO`):
   - `bkf` → `['freio','bk','êmbolo','partida']`
   - `mcinv` → `['inversor','mcinv','drive','frequência']`
   - `door`/`porta` → `['porta','operador','corrediça','batente']`
   - `limit` → `['limite','parada','linear']`
   - `lw`/`load` → `['carga','pesagem','balança']`
   - E outros 15+ mapeamentos

2. Batch-query `gn_conhecimento_manuais` (GIN index `idx_gncm_kwarray`) para todos os `mcp_oficial` distintos em paralelo (`Promise.all`), usando `palavras_chave && $1::text[]` + ordenação por `COUNT(*) FROM unnest(palavras_chave) k WHERE k = ANY($1::text[])`.

3. `composeAcaoFromManual(secao)` — extrai trecho após "Procedimento:", limita a ~320 chars cortando na última frase, anexa `(ref: MAC-DECA-0035, seção X.Y)`.

4. `buildEpisodio(codigo, descricao, evs, causaDB, manualSecao)` — novo 5° param:
   - `mcp_oficial` + match no manual → `acaoSugerida = composeAcaoFromManual(...)`, `fonteAcao = 'manual_tke'`
   - `mcp_oficial` sem match → `acaoSugerida = descricao_oficial`, `fonteAcao = 'descricao_oficial'`
   - `dicionario_fixo` → sem mudança, `fonteAcao = 'dicionario_fixo'`
   - desconhecido → `fonteAcao = 'desconhecido'`

**Matches validados (query direta ao banco):**
- E037 (BKF=0: falha na partida) → **5.7 - Êmbolo do Freio** — proc. de desmontagem, limpeza, lubrificação ✓
- E028 (Falha na abertura de porta) → **4.7 - Soleiras e Corrediças de Porta** — inspeção e limpeza ✓
- E046 (P28=0: circuito de segurança) → **5.31 - Teste do Limitador de Velocidade** ✓
- E030 (Erro na MCINV) → **5.4 - Isolamento e Aterramento do Motor** (melhor match disponível no manual)

**Nota:** token TKE MAX expirou (SPA 24h) durante o teste — não foi possível testar com elevador 99051 em tempo real. Sintaxe validada com `node --check`. Lógica validada com queries diretas ao banco. Re-testar com `curl http://localhost:5063/cockpit/equipamento/99051/falhas?horas=24` após Gabriel se autenticar no MAX via browser.

### Monitoramento de expiração do token TKE MAX — IMPLEMENTADO 02/08/2026

**Rota `GET /cockpit/max/token-status` (cockpit-api.js):**
- Consulta `cockpit_tokens`, calcula `horasRestantes` até 24h expirarem
- Referência preferencial: `session_started_at` (definido via `POST /cockpit/max/token-nova-sessao` após browser login)
- Fallback: `updated_at` como proxy (última rotação bem-sucedida do refresh_token)
- Retorna: `{ valido, expiraEm, horasRestantes, fonteReferencia, alertaParaEnviar }`
- `alertaParaEnviar` só é não-null quando: tipo cruzou limiar E (tipo mudou OU ≥6h desde último alerta do mesmo tipo)
- Dedup persistido em `ultimo_alerta_tipo` / `ultimo_alerta_at` na tabela `cockpit_tokens`

**Rota `POST /cockpit/max/token-nova-sessao` (cockpit-api.js):**
- Gabriel chama após fazer login no TKE MAX via browser para zerar o timer de 24h
- Body: `{ session_started_at: "ISO8601" }` (opcional, default = NOW())
- Limpa `ultimo_alerta_tipo` e `ultimo_alerta_at` (reseta dedup)

**Colunas adicionadas a `cockpit_tokens`:**
- `session_started_at TIMESTAMP` — quando o browser login real aconteceu
- `ultimo_alerta_tipo VARCHAR(20)` — 'aviso' ou 'expirado'
- `ultimo_alerta_at TIMESTAMP` — quando o último alerta foi enviado

**Workflow n8n `GN MAX Token Alerta` (ID `9oGljFxImF5S4NfP`, ativo):**
- Cron: `0 * * * *` (a cada hora)
- Webhook manual: `POST /webhook/gn-max-token-alerta-run`
- Fluxo: Cron/Webhook → Buscar Token Status → IF Tem Alerta? → Montar Mensagem → Enviar WhatsApp `gn-pessoal`
- Mensagem "aviso" (< 3h): "o acesso ao TKE MAX vai expirar em aproximadamente {h}h. Abra o site..."
- Mensagem "expirado": "o acesso ao TKE MAX expirou. Sem urgência — mas as análises do Jarvis ficam pausadas..."
- Dedup: alerta enviado apenas quando tipo muda OU ≥6h do mesmo tipo

**Teste ponta a ponta (execução #11251):** session_started_at simulado a 22h atrás → `alertaParaEnviar: {tipo:'aviso', horasRestantes:2}` → mensagem enviada ao WhatsApp (messageId `BAE598300A5C77CA`) ✓

**Como usar após renovar acesso ao MAX:**
```bash
curl -X POST http://localhost:5063/cockpit/max/token-nova-sessao -H "Content-Type: application/json" -d '{}'
```
Ou via Jarvis: (ainda não mapeado — pode adicionar como capacidade futura)

### Incidente: refresh_token SPA expirado de vez + rota de recuperação manual — RESOLVIDO 02/08/2026

**O que aconteceu:** o `refresh_token` salvo em `cockpit_tokens` expirou de fato — não apenas o timer de alerta, o token em si. Todas as rotas que dependem do MAX (`/cockpit/debug/raw/:unitId`, `/cockpit/equipamento/:unitId/falhas`) passaram a retornar erro da Microsoft: `AADSTS700084 — The refresh token was issued to a single page app (SPA), and therefore has a fixed, limited lifetime of 1.00:00:00, which cannot be extended. It is now expired and a new sign in request must be sent by the SPA to the sign in page.`

**Causa raiz — limitação do Azure AD, não bug do código:** apps registrados como SPA têm `refresh_token` com validade fixa de 24h que **não pode ser estendida indefinidamente** só por rotação automática. A rotação (`salvarRefreshToken()` chamada a cada `renovarToken()` bem-sucedido, dentro de `cockpit-api.js`) mantém o ciclo vivo indefinidamente **enquanto nunca para por mais de 24h seguidas**. Se o ciclo parar (sem nenhuma consulta ao MAX por 24h+), o token morre e não existe caminho automático para reanimá-lo — precisa de um novo login manual no navegador.

**Confirmado por investigação de código:** não existe nenhum fluxo automatizado de login/captura de token no servidor (sem Playwright/Selenium/Puppeteer — confirmado via grep em `/root`). As únicas funções que tocam `refresh_token` em `cockpit-api.js` são `carregarRefreshToken()` (lê da tabela) e `salvarRefreshToken()` (UPDATE, chamada só internamente após renovação bem-sucedida). Não havia (até esta sessão) nenhuma rota HTTP para injetar um token novo de fora — a semente inicial da tabela `cockpit_tokens` só pode ter entrado via captura manual + INSERT/UPDATE SQL direto, no momento em que a integração foi montada (01/08/2026).

**Processo de recuperação manual (documentado para reuso futuro — vai se repetir):**
1. Gabriel faz login normalmente em `https://ams-dsc.max.tkelevator.com` no navegador (usuário/senha + MFA).
2. Abrir DevTools (F12) → aba **Network** → filtrar por `token` (ou pelo domínio `login.microsoftonline.com`).
3. Localizar a requisição `POST https://login.microsoftonline.com/prodtkemax.onmicrosoft.com/oauth2/v2.0/token`.
4. Abrir a aba Response/Preview dessa requisição e copiar o valor do campo `refresh_token` (string longa, formato `1.AS...`).
5. Enviar esse valor para a nova rota `POST /cockpit/max/token-set` (ver abaixo).

**Nova rota `POST /cockpit/max/token-set` (cockpit-api.js) — criada nesta sessão:**
- Recebe `{ refreshToken: "..." }` no body.
- Faz `UPDATE cockpit_tokens SET refresh_token = $1, ...` — mesmo campo usado por `salvarRefreshToken()`.
- Também reseta `session_started_at` para `NOW()` e limpa `ultimo_alerta_tipo`/`ultimo_alerta_at` (mesma lógica do `token-nova-sessao`) — não precisa mais chamar as duas rotas separadamente.
- Invalida o `_accessToken` em cache (`_accessToken = null; _tokenExpires = 0`) para forçar renovação real com o novo refresh_token na próxima chamada.
- Retorna `{ok:true}`.
- Uso:
  ```bash
  curl -X POST http://localhost:5063/cockpit/max/token-set \
    -H "Content-Type: application/json" \
    -d '{"refreshToken":"VALOR_REAL_CAPTURADO_NO_DEVTOOLS"}'
  ```

**Teste ponta a ponta confirmado:** `node --check` ok, serviço reiniciado, rota testada primeiro com valor fake (`"teste"`, confirmado gravado no banco), depois com o refresh_token real capturado por Gabriel. `GET /cockpit/debug/raw/99627` retornou HTTP 200 com dados reais do gateway TKE, e `GET /cockpit/equipamento/99051/falhas?horas=24` retornou 9 episódios reais (predominantemente `1037 BKF=0: departure fault`, com causa/ação vindas do manual MAC-DECA-0035) — confirma que toda a cadeia (auth → assets → eventos → causas → ações) voltou a funcionar.

**Nota permanente:** esse tipo de expiração **vai se repetir** sempre que o ciclo de renovação ficar 24h+ sem nenhuma chamada bem-sucedida (ex: VPS reiniciada, dias sem consultar o MAX). Não existe solução automática possível — é limitação do Azure AD para apps SPA, não do código. Sempre vai exigir: login manual de Gabriel no navegador → captura do `refresh_token` no DevTools → `POST /cockpit/max/token-set`.

### Processos Node.js de depuração travados — RESOLVIDO 02/08/2026

Dois processos Node.js de depuração (scripts de análise de divs do `index.html`, usados em sessões anteriores para checagem estática de HTML) ficaram presos em loop infinito por aproximadamente 3 horas, consumindo 96% de CPU e disparando a limitação de recursos da Hostinger na VPS. Identificados e encerrados com `kill -9`.

*(Pendências consolidadas na seção PENDÊNCIAS REAIS ATUAIS no topo.)*

## STATUS SESSÃO — 01/08/2026

### Cockpit API (TKE MAX) — IMPLEMENTADO E FUNCIONANDO

**Backend:**
- `/root/cockpit-api.js` (porta 5063, systemd `cockpit-api.service`, ativo)
- Rotas: `GET /cockpit/equipamentos` (100 equipamentos reais com status/conectividade/alertas/OS), `GET /cockpit/analise` (análise Claude com críticos + recomendações), `GET /health`

**Autenticação OAuth2 Microsoft (Azure AD / TKE MAX):**
- Tenant: `prodtkemax.onmicrosoft.com` | Client ID: `cea9b4a3-bd02-41c8-a4d8-787290439d31`
- O app está registrado como **SPA** no Azure — tokens SPA só são aceitos com `Origin` header da URL registrada. Sem esse header, retorna `AADSTS9002327`. **Headers obrigatórios no POST de token:**
  - `Origin: https://ams-dsc.max.tkelevator.com`
  - `Referer: https://ams-dsc.max.tkelevator.com/`
  - `X-AnchorMailbox: Oid:a5171edf-e70e-4850-bc1f-1371f97e2dc3@84d9a216-e285-4aac-b163-0dfd0c074546`
- Endpoint: `POST https://login.microsoftonline.com/prodtkemax.onmicrosoft.com/oauth2/v2.0/token`
- `access_token` em cache memória, renovado quando faltam <5min para expirar (~90min de validade)
- `refresh_token` rotativo — o Azure emite novo a cada uso; **salvo na tabela `cockpit_tokens` (PostgreSQL `n8n-postgres-1`/`evolution`)**. Sempre ler do banco antes de renovar, sempre salvar o novo token após renovar.
- **Bug de shell descoberto:** aspas simples `'558197818685'` dentro de `curl -d '...'` são comidas pelo shell, convertendo string em inteiro no jsCode do n8n. Gerar JSON com Python (`urllib.request`) ou usar heredoc para evitar.

**Assets API (equipamentos):**
- `GET https://gateway.grayforest-f0dbef97.eastus.azurecontainerapps.io/assets/asset/state?tenantId=BR&take=100`
- Header: `Authorization: Bearer {access_token}`
- Campos relevantes do response: `unitId` (número), `nickname`/`buildingName` (apelido/prédio), `equipmentSpecificStatus` ("Normal"→Operacional, "Fault"→Falha, "Standby"), `equipmentStatusNonMax`, `isOutOfService`, `isMaxUnit` (0=Sem MAX, 1=Tem MAX), `ioTHubConnectivityStatus` ("DeviceConnected"→Online), `currentOpenAlertsCount`, `currentOpenTicketsCount`, `predictionResult.currentPredictionScore`, `maintenanceRoute`, `supervisorName`

**Carteira real (100 equipamentos, Recife):** 94 Operacionais, 4 Fora de serviço, 1 Falha, 1 Standby | 19 com MAX Online, 11 com MAX Offline, 70 sem MAX | 3 com alertas ativos, 75 com OS abertas

**Workflow n8n GN Cockpit** (ID `9i9gin2urESI0RLC`, ativo):
- Cron `50 10 * * 1-5` (07h50 Recife / 10h50 UTC) — envia análise diária via WhatsApp `gn-pessoal` (558197818685)
- Webhook manual: `POST /webhook/gn-cockpit-run`
- Fluxo: Cron/Webhook → `GET http://172.17.0.1:5063/cockpit/analise` (timeout 120s) → Code (monta payload WPP) → Evolution API `gn-pessoal`
- Testado ponta a ponta com sucesso (execução `11163` → `success`, mensagem entregue)

**Rota `GET /cockpit/equipamento/:unitId/falhas?horas=N`** — análise de falhas de um equipamento específico:

- **Busca direta por unitId** (`isDscSearch=true&unitId={X}&take=25&tenantId=BR`) — retorna exatamente 1 item sem varrer a carteira inteira. Nunca usa `buscarTodosEquipamentosRaw` para resolver unitId→deviceId. Cache `_unitIdMap` em memória para evitar chamadas repetidas.
- **Eventos**: `GET .../assets/event/events/BR/{deviceId}?eventTypeFilter=ElevatorErrorCodeEvent`, paginado até 1000 eventos (while loop, page < 100 itens = fim). Parâmetro `horas` limitado a `[1, 168]`.
- **Agrupamento em episódios**: eventos com mesmo `eventId` separados por ≤ 60 segundos = mesmo episódio; gap > 60s = novo episódio. Cada episódio acumula contagem de ocorrências (`vezes`) e timestamps de primeira/última vez.
- **Campo `pavimento`**: extraído de `ev0.startFloorName` / `endFloorName`. Se iguais → um único valor; se diferentes → `"X e Y"`. Incluído na `acaoSugerida` quando o padrão `P\d+=` aparece na descrição (ex: "parado no P3").
- **Campo `estadoNoMomento`**: contexto do elevador no instante da primeira falha do episódio. Busca retroativa em `ElevatorTripEvent` + `ElevatorOpModeEvent` (carregados em paralelo, ordenados crescente por `finalizedAt`). Último evento encontrado antes do timestamp da falha determina o estado: TripEvent `tripDirection "Down"/"Up"` → "em movimento (descendo/subindo)"; OpModeEvent `"STANBY"` → "parado/standby", `"NORMAL"` → "parado, aguardando chamada", outros → `"parado ({desc})"`. Sem evento anterior → `null`.
- **Dicionário `CAUSAS`** (6 códigos mapeados; `null` para desconhecidos):
  - `5702`: sensor/célula de carga descalibrado — verificar calibração LW
  - `3269`: sensor ou encoder de posição/porta com falha intermitente — inspecionar feedback
  - `1894`: variação anormal de aceleração — verificar sistema de tração/acionamento
  - `1046`: falha em contato/dispositivo do circuito de segurança — inspecionar portas/limitador
  - `2027`: obstrução ou motor de porta com problema — verificar operador de porta
  - `1030`: falha no inversor/drive do motor — verificar MCINV
- **Sem ranking de prioridade** — todos os episódios retornados, ordenados por `ultimaVez` decrescente (mais recente primeiro).
- **Resposta sempre HTTP 200** com `{ok:false, erro:"..."}` em caso de falha (padrão projeto).

**Como o Jarvis decide qual ação chamar (não é function calling):**

O mecanismo é **prompt engineering + JSON pattern matching**, não Claude function calling/tools:
1. O nó **Montar Prompt** constrói um `sysBase` com 11 capacidades numeradas e blocos `PRIORIDADE XXXX` com gatilhos por palavra-chave (ex: `PRIORIDADE OS REVISAO`: gatilhos "gere OS", "abre OS", "ordem de serviço de revisão" → responde com `{"acao":"os_revisao",...}`).
2. O nó **API Claude** chama a Anthropic API com `max_tokens: 200` — o modelo retorna texto livre OU um JSON puro (sem markdown).
3. O nó **Extrair Resposta** (Code node) faz `JSON.parse` no retorno (com strip de code fences), e um `if/else if` por `parsed.acao` despacha a chamada HTTP real: `os_revisao` → tac-api:5053, `os_peca` → tac-api:5053, `calendar` → webhook gn-calendar, `investimento` → webhook gn-investimentos. Texto livre cai no `else` (resposta direta ao usuário).

**Para adicionar capacidade de falhas do cockpit ao Jarvis:** adicionar capacidade #12 no `sysBase` + regra `PRIORIDADE COCKPIT` com gatilhos ("falhas do equipamento", "erros do equipamento", "analyse o elevador", etc.) → resposta JSON `{"acao":"cockpit_falhas","unitId":"NUMERO","horas":24}`. No `Extrair Resposta`, adicionar handler `acao === 'cockpit_falhas'` que chama `http://172.17.0.1:5063/cockpit/equipamento/{unitId}/falhas?horas={horas}` e formata a resposta para WhatsApp.

**Módulo MAX — IMPLEMENTADO 01/08/2026:**
- Tabela PostgreSQL `gn_max_analises` (id, unit_id, device_id, horas_periodo, total_falhas, falhas_json JSONB, origem, criado_em) em `n8n-postgres-1`/`evolution`.
- `cockpit-api.js`: `rotaFalhas` agora aceita `?origem=` e persiste resultado em `gn_max_analises` de forma assíncrona (fire-and-forget). Nova rota `GET /cockpit/max/historico?limit=N` retorna últimas N análises com unitId, dataHora, totalFalhas, resumo (códigos únicos), origem.
- n8n workflow **GN MAX Historico** (ID `F3EwosQzfEK2RSH9`, webhook `gn-max-historico`, ativo) — proxy GET para cockpit-api:5063/cockpit/max/historico.
- n8n **GN Assistente Inteligente** (`mVZ1RyggUw9mnVgF`): URL do branch `cockpit_falhas` atualizada para `?horas=${horas}&origem=jarvis_texto`.
- `index.html`: nó MAX adicionado ao quadrante PROJETOS; MODULE_ACTIONS `'MAX': enterMax()`; tela `#screenMax` (tema azul/ciano `#38bdf8`) com dica de uso + tabela de histórico carregada de `gn-max-historico`; `enterMax()`/`backFromMax()`; adicionado a `sobrepostas[]` e enter/back wraps.
- Commit: `078306b` → pushed main.
- Nó MAX movido do quadrante PROJETOS para TRABALHO (verde `#4ade80`). Commit: `752cb4c`.

**UX atualizada — Jarvis resposta curta + relatório visual na aba MAX (01/08/2026):**
- Branch `cockpit_falhas` do Jarvis: retorna apenas confirmação curta — `"Análise feita, Senhor. Relatório do elevador {X} já se encontra na aba MAX."` (ou "não encontrado" / "sem falhas") em vez de listar todas as falhas em texto corrido no WhatsApp. A análise completa persiste em `gn_max_analises` e fica disponível na tela MAX.
- Cada card do histórico é clicável → abre modal `#maxRelatorioModal` (z-index 11000, fora de screenMax) com:
  - Cabeçalho: equipamento, data/hora, período, total de falhas
  - Gráfico de barras Canvas 2D nativo (`maxDrawBars`) — ocorrências por código, cores `#38bdf8`/`#fbbf24`/`#e2504a` por volume (≤10/≤30/>30); versão dark para tela, versão light para PDF
  - Lista detalhada: cada falha com código (`#38bdf8`), descrição, ocorrências coloridas, pavimento, estado no momento, causa provável e ação sugerida
  - Botão "Exportar PDF" (`maxExportarPDF`): abre `window.open` com HTML completo — gráfico embutido como `canvas.toDataURL` (offscreen 660×200, fundo branco), tabela de falhas, orientação A4 landscape
- `backFromMax()` fecha o modal antes de sair da tela
- `cockpit-api.js` `/cockpit/max/historico` agora inclui `falhasJson` (array completo de falhas) em cada registro — necessário para o modal renderizar sem chamada extra
- Commit: `d59098c` → pushed main.

*(Pendências do cockpit consolidadas na seção PENDÊNCIAS REAIS ATUAIS no topo do arquivo.)*

**Capacidade #12 Jarvis (cockpit_falhas) — IMPLEMENTADA 01/08/2026:**
- Nó "Montar Prompt": capacidade #12 + `PRIORIDADE COCKPIT FALHAS` adicionados ao `sysBase`. Gatilhos: "analise o elevador", "falhas do elevador", "erros do elevador", "problemas no elevador" e variações. Claude extrai `unitId` e `horas` da mensagem e retorna `{"acao":"cockpit_falhas","unitId":"NUMERO","horas":24}`.
- Nó "Extrair Resposta": handler `acao === 'cockpit_falhas'` chama `GET http://172.17.0.1:5063/cockpit/equipamento/{unitId}/falhas?horas={horas}`. Monta resposta em texto corrido com código, descrição, ocorrências, pavimento, estado no momento e causa/ação. Campos corretos da API: `resp.falhas[]`, `f.ocorrencias` (não `vezes`/`episodios`).
- Testado: "analise o elevador 157333 nas ultimas 24 horas" → 3 tipos de falha (5702 LW 1×pav14, 1894 ACCEL 5×pav16, 5702 LW 62×pav15) com causa e ação sugerida. ✓

## STATUS SESSÃO — 25/07/2026

### Módulo de Investimentos — IMPLEMENTADO E FUNCIONANDO COM DADOS REAIS

**Backend:**
- `/root/investimentos-api.js` (porta 5062, systemd `investimentos-api.service`, ativo) — rotas: `GET /investimentos/carteira` (cotações + P&L + preço teto + sinal 🟢🟡🔴), `GET /investimentos/dividendos` (12 meses), `GET /investimentos/cambio` (USD/EUR via AwesomeAPI + média 30d), `GET /investimentos/meta` (projeção R$1M, aporte R$1.600/mês, 0,9%/mês), `GET /investimentos/sugestao`, `GET /investimentos/compras`, `POST /investimentos/compra` (recalcula preço médio ponderado), `POST /investimentos/ativo` (upsert direto).
- Todas as rotas dependentes de API externa degradam graciosamente (HTTP 200 com `avisoBrapi`/valores nulos em vez de 500) quando uma fonte externa falha — segue o padrão de resiliência do projeto (tac-api, oportunidades-api).
- Preço teto = dividendo médio 12m ÷ 1% (taxa mínima mensal).
- Tabelas PostgreSQL `gn_investimentos` (PK ticker) e `gn_investimentos_compras` (histórico) criadas e populadas com a carteira real: VGIR11 (2000@9,67), RURA11 (1570@8,37), MXRF11 (1000@9,70), VGHF11 (1011@8,00), TGAR11 (100@92,19), BBAS3 (100@19,03).

**Cotação (preço/variação) — Brapi:** token gratuito de Gabriel em `BRAPI_TOKEN` (topo do arquivo). **Duas limitações do plano gratuito descobertas e contornadas:**
1. Só aceita 1 ticker por requisição (não aceita lista separada por vírgula) → `brapiQuoteBatch` faz uma chamada por ticker em paralelo (`Promise.allSettled`).
2. Não libera o módulo `dividendsData` (`MODULES_NOT_AVAILABLE`, só `summaryProfile` no free tier) → `brapiQuoteOne` tenta com `modules` e, se recusado, refaz sem `modules` automaticamente (preço ainda vem, só não os dividendos).

**Dividendos (preço teto, sinal, tela Dividendos, sugestão de aporte) — Yahoo Finance, não Brapi:** como a Brapi free não dá dividendos, testei 4 fontes gratuitas (Funds Explorer — SPA, dado só carrega via JS, não dá pra confiar em curl; Investidor10 — scraping HTML funcionaria mas frágil a redesign; HG Brasil — key `demo` rejeitada, exige cadastro; **Yahoo Finance venceu**: `https://query1.finance.yahoo.com/v8/finance/chart/TICKER.SA?range=1y&interval=1d&events=div` retorna JSON limpo com data+valor por cota, testado nos 6 ativos da carteira, sem necessidade de token/cadastro). **Único requisito: precisa de header `User-Agent` de navegador** — sem ele a Yahoo bloqueia com `429 "Edge: Too Many Requests"` já na primeira chamada (não é rate-limit real, é bloqueio de tráfego sem UA). Implementado em `yahooDividendos12m`/`yahooDividendosBatch` (`YAHOO_UA` constante no topo do arquivo).
- **Bug corrigido nesta sessão:** o Dividend Yield (`dyAtual`) estava calculado errado — dividia o total recebido pela *posição inteira* (dividendo por cota × quantidade de cotas) pelo preço de 1 cota, dando valores absurdos tipo 23000%. Corrigido para usar o dividendo *por cota* (sem multiplicar pela quantidade) sobre o preço atual — DYs agora saem na faixa realista (12–20% ao ano para os FIIs da carteira, 2,7% para BBAS3).

**Nota:** a AwesomeAPI (câmbio) retornou `429 QuotaExceeded` durante toda a sessão — não exige token, parece limite temporário do IP compartilhado da VPS. A rota `/investimentos/cambio` já degrada graciosamente (retorna `{USD:null,EUR:null}` em vez de quebrar); deve se normalizar sozinho. Se persistir por muito tempo, vale investigar uma fonte alternativa de câmbio.

**Webhooks n8n criados (todos ativos, proxy HTTP→172.17.0.1:5062, padrão Webhook→HTTP Request→Respond):**
`gn-investimentos-load` (GET carteira), `gn-investimentos-save` (POST → `/ativo`), `gn-investimentos-compra` (POST → `/compra`), `gn-investimentos-dividendos`, `gn-investimentos-cambio`, `gn-investimentos-meta`, `gn-investimentos-sugestao`, `gn-investimentos-compras` (histórico).

**Workflow GN Investimentos Diario** (cron `30 11 * * 1-5`, 08h30 Recife) — busca carteira, monta resumo com P&L/sinais/sugestão de aporte, envia WhatsApp `gn-pessoal` (558197818685). Testado manualmente via `gn-investimentos-diario-run` — **atenção:** esse teste realmente enviou uma mensagem real ao WhatsApp do Gabriel com valores zerados (efeito da pendência do token Brapi acima), não é um bug do workflow.

**Workflow GN Investimentos Jarvis** (`gn-investimentos`, POST) — dispatcher único que roteia por `operacao` (carteira/dividendos/sugestao/compra) para a rota certa da investimentos-api; é o que o Jarvis chama.

**Telas no `index.html`** — uma única `#screenInvestimentos` com abas internas (padrão igual ao Gestão de Equipe): Carteira, Aportes, Dividendos, Metas Fin., Câmbio. Acessível pelos nós do quadrante INVESTIMENTOS no Hub (`Carteira`, `Aportes`, `Dividendos`, `Metas Fin.`, `Câmbio` — os outros itens do quadrante como Ações/FIIs/Criptos continuam "Em breve"). Câmbio com auto-refresh a cada 5 min. Tema azul naval (`#080e1f`/`#6ab4ff`), igual ao TK Mobile/Perito Judicial.
- Validação feita via checagem estática (sintaxe JS, ids/funções cruzados) — **não há chromium-cli/jsdom disponíveis nesta VPS**, então não foi possível fazer teste visual em navegador real. Recomenda-se Gabriel conferir visualmente na primeira vez que abrir o módulo.

**Jarvis integrado** (`mVZ1RyggUw9mnVgF`, nós Montar Prompt/Extrair Resposta) — capacidade #11 + `PRIORIDADE INVESTIMENTOS`. Gatilhos testados ponta a ponta com sucesso: "comprei X cotas de TICKER a RY", "como está minha carteira", "quanto recebi de dividendos", "sugestão de aporte".

**Commit:** `d4d0f39` — "Adiciona Módulo de Investimentos (Carteira, Aportes, Dividendos, Metas Fin., Câmbio)", pushed para `main`.

### Mapeamento Ações/FIIs no Hub — IMPLEMENTADO

Nós "Ações" e "FIIs" do quadrante INVESTIMENTOS (que caíam no toast "Em breve, Senhor.") agora abrem a mesma aba Carteira (`enterInvestimentos('carteira')`), junto com os 5 nós já mapeados na sessão (Carteira, Aportes, Dividendos, Metas Fin., Câmbio). Trecho de roteamento fica em `MODULE_ACTIONS`/`nodeClick()` dentro da IIFE `hub2D()` do `index.html`. Commit `b48051e`.

### Edição e venda de ativos (Carteira/Aportes) — IMPLEMENTADO

- `/root/investimentos-api.js`: nova rota `POST /investimentos/venda` — reduz a quantidade de cotas sem alterar o preço médio, remove o ativo de `gn_investimentos` se a quantidade zerar, e sempre grava no histórico (`gn_investimentos_compras`) com quantidade **negativa**. `salvarAtivo` (`/investimentos/ativo`) também passou a remover o ativo quando `quantidade <= 0`.
- **Migração de banco:** removida a `FK ON DELETE CASCADE` entre `gn_investimentos_compras.ticker` e `gn_investimentos.ticker` — sem isso, zerar/remover um ativo apagava todo o histórico de compras/vendas dele junto. Agora o histórico sobrevive independente do ativo ainda estar na carteira.
- **Padrão de resiliência reforçado:** o handler HTTP da API agora **sempre responde 200** (mesmo em erro de validação, ex: "vender mais cotas do que possui"), com `{ok:false, erro:"..."}` no corpo. Antes retornava 500, e como os nós HTTP Request do n8n tratam qualquer status fora de 2xx como falha do node (sem repassar o corpo pro `Responder ao Webhook`), o app recebia uma resposta vazia sem nenhuma explicação do erro.
- Novo webhook n8n `gn-investimentos-venda` (proxy para `/investimentos/venda`).
- `index.html`: botão "✏️ Editar" em cada card da Carteira abre modal com quantidade/preço médio editáveis (Salvar → `/gn-investimentos-save`) e uma seção separada de venda (quantidade a vender + preço → `/gn-investimentos-venda`) — campos separados de propósito para não confundir "corrigir a posição toda" com "vender uma parte". Histórico de Aportes agora rotula cada linha como COMPRA (verde) ou VENDA (vermelho, quantidade negativa). Commit `9b845cc`.

## STATUS SESSÃO — 25/07/2026 (continuação) — Módulo Perito Judicial: Honorários e Financeiro

### Controle financeiro de honorários — IMPLEMENTADO

**Banco (`/root/perito-api.js`, porta 5061):** 5 colunas novas em `gn_pericias` — `data_pedido_honorarios`, `valor_adiantamento`, `data_recebimento_adiantamento`, `data_recebimento_final`, `status_pagamento` (default `'Pendente'`). `listar()`/`salvar()` atualizados para expor/persistir os novos campos em camelCase (`dataPedidoHonorarios`, `valorAdiantamento`, `dataRecebimentoAdiantamento`, `dataRecebimentoFinal`, `statusPagamento`).

**Tela de Nomeação (`index.html`, `screenPerito`):** nova seção "💰 Honorários e Controle Financeiro" com status de pagamento (select: Pendente / Adiantamento recebido / Pago integral / Inadimplente) + as 4 datas/valores novos. Label do campo antigo "Valor Recebido" renomeado para "Valor Final Recebido".

**Nova tela Financeiro** (botão "💰 Financeiro" no cabeçalho, ao lado de "+ Nova Nomeação" e do novo botão "👤 Perfil") — terceiro estado de `_periView` (`'financeiro'`, além de `'list'`/`'detail'`): 4 cards (Total Solicitado, Total Recebido, Total Pendente, Média por Perícia), tabela clicável filtrável por status de pagamento, botão "Exportar Relatório" que gera PDF (mesmo padrão `window.open`+`print()` dos outros documentos do módulo).

**Alertas:**
- Banner no topo da lista (`#periAlertaBanner`) resumindo contagem de laudos vencidos (🔴) e honorários pendentes há mais de 30 dias (🟠); cada card também ganha borda vermelha (prazo vencido) e/ou aviso laranja individual.
- Workflow n8n **GN Perito Alertas** (`bO71SYUwEF2yueKj`) atualizado — nó "Montar Alerta" agora também varre `statusPagamento !== 'Pago integral'` com base em `dataPedidoHonorarios` (fallback `dataNomeacao`) e inclui um segundo bloco "💰 Honorários pendentes há mais de 30 dias" na mesma mensagem de WhatsApp (`gn-pessoal`, 558197818685). Testado disparando manualmente (`gn-perito-alertas-run`) — confirmado pegando um prazo real vencendo em 5 dias e um registro de teste com 85 dias de honorários pendentes.

**Documentos com dados bancários:** os dois modelos de pedido de honorários ("com adiantamento" e "sem adiantamento") passaram a incluir um bloco "Dados bancários para depósito" (Nome, CPF, Banco, Chave PIX).

**Modal de Perfil do Perito** (novo botão "👤 Perfil"): nome completo, CPF, banco e chave PIX, persistidos em `localStorage` (`peri_perfil`) e usados automaticamente nos documentos gerados — evita hardcode no código, dá pra editar pelo próprio app. Valores padrão: Nome "Gabriel da Silva Nascimento", CPF `098.089.724-62`, Banco Santander, **Chave PIX `098.089.724-62`** (corrigido nesta sessão — a chave PIX é o CPF, não o telefone; valor inicial errado `(81) 99781-8685` foi trocado no commit `40ca504`).

**Commits:** `60c0e80` (controle financeiro completo) e `40ca504` (correção da chave PIX padrão).

Validação em ambos os módulos desta sessão (Investimentos e Perito): checagem de sintaxe JS (`node --check`) + verificação cruzada de ids/funções via script Python + parser HTML real (`html.parser`) confirmando zero tags desbalanceadas — sem chromium-cli/jsdom na VPS, não foi possível fazer teste visual em navegador de verdade.

*(Lista de pendências desta sessão — obsoleta, ver PENDÊNCIAS REAIS ATUAIS no topo.)*

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

