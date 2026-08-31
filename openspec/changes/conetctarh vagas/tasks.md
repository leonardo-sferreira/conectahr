## 1. Fundacao

- [ ] 1.1 Criar a tabela `vaga` (titulo, tipo interna/externa, cargo_id, departamento_id, descricao, requisitos, quantidade_posicoes, status rascunho/aberta/pausada/encerrada/cancelada, criado_por_user_id); verificar chaves estrangeiras para cargo e departamento e restricao do enum de status.
- [ ] 1.2 Criar a tabela `candidatura` (vaga_id, colaborador_id opcional, nome, email, telefone, curriculo opcional, status recebida/em_triagem/em_entrevista/em_oferta/contratado/rejeitada, token_acompanhamento unico, decidido_por_user_id, data_decisao); verificar indice unico em token_acompanhamento, indice por vaga_id+email e indice por vaga_id+colaborador_id.
- [ ] 1.3 Criar o grupo de API `ConectaRH - Vagas` (autenticado, RH/Admin e colaborador) e um grupo separado para os endpoints publicos; verificar que o grupo publico nao exige token de usuario e que o grupo autenticado aceita qualquer perfil quando aplicavel.

## 2. Vagas (RH e colaborador)

- [ ] 2.1 Implementar criacao e edicao de vaga em rascunho (RH/Admin); verificar validacao de cargo/departamento ativos e campos obrigatorios.
- [ ] 2.2 Implementar publicar, pausar, reabrir, encerrar e cancelar vaga, respeitando as transicoes validas do status; verificar bloqueio de transicoes invalidas (ex.: reabrir vaga cancelada).
- [ ] 2.3 Implementar listagem e consulta de vaga para RH/Admin, incluindo vagas em qualquer status; verificar filtro por status e por tipo.
- [ ] 2.4 Implementar listagem de todas as vagas abertas (interna e externa) para qualquer colaborador autenticado ativo; verificar que vagas fora do status aberta nao aparecem para quem nao e RH/Admin.
- [ ] 2.5 Implementar candidatura de colaborador autenticado a uma vaga aberta, sem reenvio de contato, com curriculo opcional; verificar vinculo por colaborador_id, bloqueio de candidatura duplicada do mesmo colaborador na mesma vaga e bloqueio para colaborador inativo/desligado.

## 3. API publica

- [ ] 3.1 Implementar listagem publica de vagas externas abertas, sem autenticacao; verificar que vagas internas, em rascunho, pausadas, encerradas ou canceladas nunca aparecem.
- [ ] 3.2 Implementar submissao publica de candidatura (nome, email, telefone, curriculo) para uma vaga aberta; verificar bloqueio de candidatura para vaga fechada, validacao de arquivo de curriculo (tipo e tamanho) e geracao do token_acompanhamento unico.
- [ ] 3.3 Implementar bloqueio de candidatura duplicada (mesmo e-mail, mesma vaga, candidatura ativa); verificar que uma candidatura anterior rejeitada nao bloqueia nova submissao.
- [ ] 3.4 Implementar consulta publica de status por token_acompanhamento + e-mail; verificar que token invalido ou de outra candidatura nao revela se a candidatura existe, e que o historico de estados e retornado.
- [ ] 3.5 Implementar protecao de acesso ao arquivo de curriculo, liberando somente para RH, Admin ou o candidato dono via token; verificar bloqueio de acesso direto sem autorizacao.

## 4. Gestao de candidaturas (RH)

- [ ] 4.1 Implementar listagem e filtro de candidaturas por vaga e por status para RH/Admin; verificar que os dados do candidato (incluindo link do curriculo) sao retornados somente para esse escopo.
- [ ] 4.2 Implementar a transicao de status da candidatura pelo RH (recebida -> em_triagem -> em_entrevista -> em_oferta -> contratado), registrando responsavel e data; verificar bloqueio de pular etapas.
- [ ] 4.3 Implementar rejeicao de candidatura a partir de qualquer estado anterior a contratado; verificar preservacao do historico de estados anteriores.
- [ ] 4.4 Implementar o registro de cada transicao de candidatura na tabela `auditoria` (recurso "candidatura", valores anterior/novo, responsavel quando houver); verificar consulta do historico completo de uma candidatura via auditoria.

## 5. Handoff de RH para o ConectaRH Vagas

- [ ] 5.1 Implementar emissao de token de handoff de curta duracao para usuario RH/Admin (UUID assinado, uso unico, expiracao curta definida no design); verificar que outros perfis nao conseguem solicitar o token.
- [ ] 5.2 Implementar endpoint de validacao/troca do token pelo ConectaRH Vagas, retornando perfil e identificacao do RH; verificar recusa de token expirado, ja usado ou invalido, e invalidacao imediata apos a troca.

## 6. Integracao e entrega

- [ ] 6.1 Publicar as tabelas e endpoints no workspace Xano com push incremental e dry-run antes de cada publicacao; verificar ausencia de operacoes destrutivas nao intencionais.
- [ ] 6.2 Testar o fluxo completo (RH publica vaga -> colaborador ou visitante se candidata -> RH avanca/rejeita via handoff -> candidato consulta status) com dados sinteticos via `xano function run` ou endpoints reais; verificar cada transicao, a protecao do curriculo e a expiracao do token de handoff.
- [ ] 6.3 Documentar no README o contrato das APIs (publica, colaborador autenticado, gestao RH e handoff) para orientar a construcao do ConectaRH Vagas, que fica fora desta mudanca.
