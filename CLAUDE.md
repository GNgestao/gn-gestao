# GN Gestão — Notas de Sessão

**Histórico de sessões antigas (23/06 a 07/07/2026):** ver /root/CLAUDE-HISTORICO.md

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

