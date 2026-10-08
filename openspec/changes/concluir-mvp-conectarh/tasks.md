# Tasks

Tarefas movidas das quatro changes arquivadas em 2026-10-08. O prefixo `[XX x.y]` identifica a tarefa de origem (`GE` conectarh.gestao, `FE` implementar-frontend-streamlit, `CB` corrigir-brechas-e-alinhar-documentacao, `LG` adequacao-lgpd); `[novo]` marca tarefas identificadas na consolidação. Como ler as referências: `design.md`, decisão C1.

## 1. Pendências da conectarh.gestao [GE]

**1. Fundacao e ambiente**

- [ ] 1.1 [GE 1.1] Criar e organizar o repositorio GitHub, README inicial, estrategia de branches e responsabilidades do grupo; verificar clone limpo, primeiro pull request e instrucoes de setup. (Feito nesta sessao: repositorio git local inicializado, README com stack/setup/estrategia de branches, .gitignore e primeiro commit. Falta: criar o repositorio remoto no GitHub (nao ha `gh` CLI autenticado neste ambiente), configurar o remote, abrir o primeiro Pull Request e preencher a tabela de responsabilidades do grupo.)
- [ ] 1.2 [GE 1.2] Definir a estrutura do aplicativo, configurar Streamlit, ambientes e pipeline de validacao; verificar que build, lint e testes executam em ambiente limpo.

**7. Integracao e entrega**

- [ ] 1.3 [GE 7.1] Criar telas e endpoints dos fluxos por fatia vertical, aplicando estados de carregamento, erro, sucesso e acesso negado; verificar os principais caminhos por perfil.
- [ ] 1.4 [GE 7.4] Preparar deploy com feature flags, dados sinteticos e plano de rollback sem importar registros das imagens; verificar smoke test em ambiente controlado e registrar a configuracao de producao.
- [ ] 1.5 [GE 7.5] Realizar validacao inicial de mercado com usuarios/testadores, coletar feedback e medir uso basico; verificar relatorio de achados e backlog priorizado.
- [ ] 1.6 [GE 7.6] Preparar a entrega final com README, arquitetura, especificacoes OpenSpec, evidencias de testes e demonstracao; verificar que um avaliador consegue reproduzir o fluxo principal.
- [ ] 1.7 [GE 7.10] Garantir acessibilidade do frontend Streamlit e versionamento `/api/v1/`; verificar teclado, contraste, labels, foco, responsividade, textos alternativos, erros compreensiveis e compatibilidade da API.
- [ ] 1.8 [GE 7.12] Documentar no README que o ponto do MVP e controle interno experimental e criar backlog de conformidade REP-P, REP-A e REP-C conforme Portaria nº 671/2021; verificar que a interface nao declara certificacao inexistente.

## 2. Frontend Streamlit [FE]

**1. Fundação (já concluída nesta sessão)**

- [ ] 2.1 [FE 1.5] Legibilidade da tela Entrar: deixar mais visíveis o texto de exemplo (placeholder) dos campos e a borda do card que agrupa e-mail e senha.
  - Primeira tentativa (2026-10-06) **revertida a pedido** em 2026-10-07: as cores `#6B7280`/`#C9C7C1` e a moldura marfim do campo não ficaram como esperado.
  - O `theme.py` voltou ao visual anterior; só o escape de HTML de `render_header`/`render_card_title` foi mantido.
  - Antes de tentar de novo, alinhar com o time o resultado esperado, de preferência com referência no Figma.

**2. Navegação multi-página e guarda de sessão**

- [ ] 2.2 [FE 2.1] Migrar `frontend/app.py` para `st.Page`/`st.navigation`, mantendo o fluxo de autenticação (login/OTP/esqueci senha) como um wizard interno de estados dentro de uma única página "Entrar", conforme decidido em `design.md`; verificar que sem sessão só a página de autenticação é acessível.
- [ ] 2.3 [FE 2.2] Implementar a função de guarda de sessão (redireciona para "Entrar" se `st.session_state.token` ausente) e o filtro de páginas por perfil (Auditoria/Regras só para RH/ADMIN); verificar com uma conta de cada perfil que a lista de páginas visível muda corretamente.

**3. Início**

- [ ] 2.4 [FE 3.2] Integrar com `central_de_tarefas` (seção de pendências pessoais); verificar que os campos batem com a resposta real do endpoint.
- [ ] 2.5 [FE 3.3] Testar os estados carregando/vazio/erro da tela e os diferentes contextos (com e sem colaborador vinculado, com e sem pendências).

**4. Central de Pendências**

- [ ] 2.6 [FE 4.1] Buscar o node "Central de Pendências" no Figma (inclui o componente "trilha de conexão") e conferir antes de codar; construir a UI, incluindo o componente de trilha reutilizável em `theme.py` se ainda não existir.
- [ ] 2.7 [FE 4.2] Integrar com `central_de_tarefas` (filas de férias/documentos/desligamentos pendentes) e com o dashboard do gestor quando aplicável.
- [ ] 2.8 [FE 4.3] Testar o escopo por perfil (RH/ADMIN vê tudo, Gestor só o próprio departamento, Colaborador não vê a fila) e os 6 estados de UI.

**5. Perfil**

- [ ] 2.9 [FE 5.1] Buscar o node "Perfil" no Figma e conferir antes de codar; construir a UI (dados pessoais + dados bancários).
- [ ] 2.10 [FE 5.2] Integrar com `meu_perfil_colaborador` (GET/PATCH) e `meus_dados_bancarios` (PATCH).
- [ ] 2.11 [FE 5.3] Testar que dados bancários só aparecem para o próprio colaborador (nunca para Gestor, mesmo por engano de UI — o backend já bloqueia, mas a tela não deve nem tentar mostrar).

**6. Onboarding**

- [ ] 2.12 [FE 6.1] Buscar o node "Onboarding" no Figma e conferir antes de codar; construir o checklist por categoria com responsável e percentual concluído.
- [ ] 2.13 [FE 6.2] Integrar com `colaboradores/{id}/onboarding` (GET) e `onboarding_item/{id}/concluir` (POST); testar autorização por item (responsável rh/colaborador/gestor) e os 6 estados de UI.

**7. Ponto**

- [ ] 2.14 [FE 7.1] Buscar o node "Ponto" no Figma e conferir antes de codar; construir marcação, espelho do dia/período e solicitação de correção, incluindo o aviso de "controle interno experimental".
- [ ] 2.15 [FE 7.2] Integrar com `ponto/marcar`, `ponto/{id}/solicitar_correcao`, `correcoes_ponto` (aprovar/rejeitar, visível a RH/ADMIN/Gestor) e consulta de banco de horas.
- [ ] 2.16 [FE 7.3] Testar a ordem estrita de marcação (entrada → intervalo → saída) e a aprovação de correção restrita ao Gestor do departamento certo.

**8. Férias**

- [ ] 2.17 [FE 8.1] Buscar o node "Férias" no Figma e conferir antes de codar — se houver um calendário visual interativo além de lista/tabela, registrar em `design.md` (seção "Limitações identificadas") antes de prosseguir, conforme o processo decidido lá.
- [ ] 2.18 [FE 8.2] Construir a UI de solicitação de férias/ausência e a verificação de conflito (informativa).
- [ ] 2.19 [FE 8.3] Integrar com `ferias/solicitacoes`, `ferias/{id}/aprovar-rejeitar-cancelar`, `ferias/{id}/verificar_conflito` e o equivalente de ausências.
- [ ] 2.20 [FE 8.4] Testar bloqueio de segunda solicitação pendente, exigência de senha já trocada, e os 6 estados de UI.

**9. Documentos**

- [ ] 2.21 [FE 9.1] Buscar o node "Documentos" no Figma e conferir antes de codar; construir upload/listagem por status.
- [ ] 2.22 [FE 9.2] Integrar com `documentos` (POST/GET/PATCH), `documentos/{id}/aprovar-rejeitar-arquivar`, `pendencias_documento` e a consulta de documentos obrigatórios pendentes.
- [ ] 2.23 [FE 9.3] Testar que não existe opção de exclusão física (só arquivamento) e que o acesso ao arquivo respeita dono/RH/ADMIN.

**10. Pagamento**

- [ ] 2.24 [FE 10.1] Buscar o node "Pagamento" no Figma e conferir antes de codar; construir a aba de holerite/informe de rendimentos, reaproveitando a integração de Documentos (mesmo módulo de backend).
- [ ] 2.25 [FE 10.2] Testar que holerite/informe de rendimentos aparece só para o colaborador dono (consulta) e que o upload continua restrito ao RH.

**11. Trajetória (avaliação, metas, PDI, plano de carreira)**

- [ ] 2.26 [FE 11.1] Buscar o node "Trajetória" no Figma e conferir antes de codar; construir avaliação (respostas por competência, contestação), metas com check-in, PDI e o painel de plano de carreira.
- [ ] 2.27 [FE 11.2] Integrar com `avaliacoes`, `avaliacoes/{id}/respostas`, `avaliacoes/{id}/enviar-contestar`, `metas`, `metas/{id}/checkin`, `pdi`, `reconhecimentos` e `colaboradores/{id}/plano_carreira`.
- [ ] 2.28 [FE 11.3] Testar a visibilidade automática de reconhecimento (público/privado por relação gestor-colaborador) e confirmar que a tela nunca oferece uma ação de "promover" automaticamente.

**12. Auditoria**

- [ ] 2.29 [FE 12.1] Buscar o node "Auditoria" no Figma e conferir antes de codar; construir o painel de consulta com os filtros disponíveis (recurso, registro, usuário, ação, resultado).
- [ ] 2.30 [FE 12.2] Integrar com `GET auditoria`; testar que a tela é inacessível (via guarda de perfil) para quem não é RH/ADMIN.

**13. Regras**

- [ ] 2.31 [FE 13.1] Buscar o node "Regras" no Figma e conferir antes de codar; construir a gestão de instrumentos normativos e regras de override, incluindo a tela de simulação de impacto antes de publicar.
- [ ] 2.32 [FE 13.2] Integrar com `instrumentos_normativos` (CRUD + aprovação), `regras_override` (CRUD + aprovação), `regras_override/resolver`, `regras_override/aplicar` e `regras_override/{id}/simular`.
- [ ] 2.33 [FE 13.3] Testar o bloqueio de autoaprovação, a exigência de número Mediador/MTE para instrumentos coletivos, e o bloqueio de "aplicar" quando há conflito não resolvido.

**14. Acessibilidade e revisão final**

- [ ] 2.34 [FE 14.1] Revisar todas as telas construídas contra os critérios de acessibilidade do design system do Figma (contraste WCAG AA, foco visível, navegação por teclado, cor nunca como único indicador de estado); verificar navegando o app inteiro só com teclado.
- [ ] 2.35 [FE 14.2] Conferir que toda tela trata os 6 estados de UI obrigatórios (carregando, vazio, sucesso, erro, bloqueado, permissão negada) de forma consistente entre si; verificar por inspeção cruzada das telas já implementadas.
- [ ] 2.36 [FE 14.3] Atualizar `docs/regras-de-negocio.md` e `AGENTS.md` com qualquer padrão de frontend que se tornou definitivo nesta change (ex.: proibição de `st.markdown(unsafe_allow_html=True)` para HTML/CSS, uso de `st.Page`/`st.navigation`).

**Novas tarefas**

- [x] 2.37 [novo] Construir o Passo 3 do login, "Trocar senha temporária" (design C2; Figma 193:55 e 193:241): depois do código de acesso, se `senha_primeiro_acesso` for verdadeiro, mostrar senha temporária, nova senha e confirmação, chamar `auth/senha PATCH` e só então liberar o Início; "Sair" encerra a sessão. Verificar com uma conta de teste com senha temporária: o restante do app fica inacessível antes da troca, a senha errada mostra o alerta da 193:241 e, depois da troca, o Início abre e o primeiro acesso aparece concluído.
  - Verificado em 2026-10-08 com a conta de teste `qa.primeiro.acesso@conectarh.test` (usuário 15, colaborador 21, perfil Colaborador), criada por `usuarios POST`. No navegador (Playwright):
    - depois do código, o app abre o Passo 3, sem barra lateral nem Início;
    - senha temporária errada → "A senha atual está incorreta." dentro do card;
    - nova senha igual à temporária e confirmação diferente → recusadas na própria tela;
    - "Sair" volta ao login;
    - novo login volta ao Passo 3, e a troca correta abre o Início.

    Pela API, a senha temporária passa a ser recusada (403) e a nova é aceita; no banco, `senha_primeiro_acesso = false`.
  - Diferenças em relação ao Figma, iguais às outras telas do app: moldura escura do campo e alerta no estilo nativo do Streamlit.
- [x] 2.38 [novo] Levar os alertas de erro e de sucesso da tela Entrar para dentro do card, abaixo do título, como no Figma (design C3; nós 193:241 e 193:139). Verificar por screenshot lado a lado com os nós.
  - Verificado em 2026-10-08 no navegador (Playwright), conferindo no DOM que cada alerta fica dentro do card, abaixo do título e acima do formulário, nos 6 casos:
    - login: e-mail inválido e credencial recusada;
    - código: formato inválido;
    - esqueci: e-mail com acento;
    - redefinir: reenvio antes de 60 s e confirmação diferente.

    O aviso de sucesso após redefinir usa o mesmo espaço reservado, mas não foi reexecutado (exige um código de redefinição real).
  - A conexão com o Figma caiu nesta sessão. A comparação foi feita com as capturas dos nós 193:139 e 193:241 tiradas em 2026-10-07.
- [ ] 2.39 [novo] Construir o painel de notificações e o menu da conta da barra superior (Figma, seção 5, nó 197:74): lista de `minhas_notificacoes` com o total de não lidas, `notificacoes/{id}/marcar_lida` ao abrir, estado vazio, e menu só com "Configurações" e "Sair da conta". Verificar os estados com e sem notificações e que "Sair da conta" volta ao Login.
- [ ] 2.40 [novo] Desenhar no Figma e depois construir as telas de Configurações: troca de senha, sessões e dispositivos, e preferências de notificação, sobre `auth/senha PATCH`, `auth/minhas_sessoes`, `auth/sessoes/*` e `minhas_preferencias_notificacao`. Verificar prints lado a lado com os nós e os 6 estados de UI.

## 3. Brechas de segurança e documentação [CB]

**1. Brechas de segurança (Parte 1)**

- [x] 3.1 [CB 1.1] Spike de sessão no token (design D2): emitir um token de teste com `extras = {perfil, sessao_id}` e ler o `sessao_id` num endpoint temporário. Se não houver acessor confiável, testar a alternativa por hash do token. Registrar o resultado em `design.md` (D2). Verificar: o endpoint temporário devolve o `sessao_id` correto para dois tokens diferentes e é removido do workspace ao final. Se as duas abordagens falharem, parar a 1.4 e rever o design antes de seguir.
  - Verificado em 2026-10-08: dois tokens da conta de teste devolveram, em `auth/me`, as sessões 30 e 31, as duas conferidas no banco (ativas, usuário 15). O resultado está no `design.md` (C5). Não houve endpoint temporário: o spike usou o `auth/me`, que mantém o `sessao_id`.
- [x] 3.2 [CB 1.4] Sessão no token (item 1.3 da auditoria):
  - `auth/otp/validar` cria a sessão antes do token e inclui o `sessao_id` em `extras`;
  - `auth/logout` encerra exatamente a sessão do token;
  - `auth/sessoes/encerrar_outras` preserva a sessão do token;
  - `auth/sessoes/{id}/encerrar` só encerra sessão do próprio usuário.

  Verificar por HTTP com duas sessões do mesmo usuário: depois do logout na sessão A, o token A é recusado e o token B continua aceito; depois de `encerrar_outras` chamado com B, A é recusado e B continua aceito.
  - Código publicado no workspace 147338 em 2026-10-08. Verificado por HTTP com duas sessões da conta de teste (sessões 30 e 31):
    - logout com a sessão A → o token A passa a ser recusado (401) e o B continua aceito;
    - `encerrar_outras` chamado com D → o token E é recusado e o D continua aceito;
    - o usuário 15 tentando encerrar uma sessão do Admin → 403 "Voce so pode encerrar as proprias sessoes", e a sessão do Admin segue válida;
    - encerrar a própria sessão → o token seguinte é recusado.
  - O plano gratuito do Xano limita a 10 requisições por 20 s (429). Testes automatizados precisam de pausa entre as chamadas.
- [x] 3.3 [CB 1.5] Guarda de acesso (itens 1.1, 1.2 e 1.3 da auditoria) nos grupos "ConectaRH — Autenticação" e "ConectaRH — Gestão de Usuários": usuário ativo, senha trocada (com as exceções do D1) e sessão válida. Verificar: o script da 1.2 passa para esses grupos. Por HTTP: um usuário com senha temporária só consegue usar `auth/senha PATCH`, `auth/me`, `auth/logout` e as rotas de sessão.
  - Publicado em 2026-10-08. `tools/checar_endpoints.py --grupo conecta_rh_autenticacao --grupo conecta_rh_gestao_de_usuarios`: 16 endpoints, 0 falhas. Por HTTP, com a conta de teste ainda com senha temporária:
    - `auth/me`, `auth/minhas_sessoes`, `auth/sessoes/encerrar_outras` e `auth/senha PATCH` funcionam;
    - `usuarios GET`, `minhas_delegacoes` e `status_operacional` → 401 "Troque a senha temporaria antes de continuar.";
    - depois da troca, `minhas_delegacoes` abre (200);
    - com a conta desativada, `auth/me` e as demais rotas → 401 "Usuario inativo.", e o login também é recusado.
  - O `logout` e o `encerrar_outras` agora encerram exatamente a sessão do token (antes usavam "a mais recente").
- [x] 3.4 [CB 1.6] Guarda de acesso no grupo "ConectaRH — Colaboradores", parte 1: cadastro, organograma, busca, onboarding, contratos, banco de horas, solicitações, comunicados e FAQ. Verificar: o script passa para esses arquivos e o smoke test HTTP funciona com um endpoint por perfil.
  - A guarda foi aplicada ao grupo "ConectaRH — Colaboradores" inteiro (89 endpoints, as partes 1 e 2 juntas) e publicada em 2026-10-08. `tools/checar_endpoints.py --grupo conecta_rh_colaboradores`: 89 endpoints, 0 falhas. Por HTTP:
    - Admin: 28 de 28 leituras sem parâmetro obrigatório respondem 200;
    - amostra de 10 leituras por perfil (RH, Gestor e Colaborador, trocando o perfil de uma conta de teste e devolvendo ao final): nenhum 401; RH 10 em 200, Gestor e Colaborador 4 em 200 e 6 em 403 (rotas que exigem outro perfil).
  - O `tools/checar_endpoints.py` passou a ignorar comentários: um cabeçalho que cita "db.add auditoria" era lido como escrita anterior à guarda.
- [x] 3.5 [CB 1.7] Guarda de acesso no grupo "ConectaRH — Colaboradores", parte 2: avaliação, metas, PDI, clima, reconhecimento, regras, instrumentos, indicadores, auditoria, delegações e calendário. Verificar: o script passa para o grupo inteiro. Por HTTP, com um usuário de senha temporária, `auditoria GET`, `indicadores GET`, `instrumentos_normativos/{id}/aprovar`, `metas POST`, `pdi POST` e `perguntas_clima/{id}/responder` são negados.
  - Coberta pelo mesmo push da 3.4. Com uma conta de teste ainda com senha temporária (usuário 17), por HTTP em 2026-10-08, todas negadas com 401 "Troque a senha temporaria antes de continuar.": `auditoria GET`, `indicadores GET`, `instrumentos_normativos/{id}/aprovar`, `metas POST`, `pdi POST` e `perguntas_clima/{id}/responder`, além de `central_de_tarefas` e `meu_perfil_colaborador`.
  - Para `metas` e `pdi`, o corpo precisa ter todos os campos obrigatórios; com campos faltando o Xano devolve 400 antes de executar a guarda.
- [ ] 3.6 [CB 1.8] Guarda de acesso nos grupos Ponto, Férias, Ausências, Documentos, Desligamentos, Cargos e Departamentos. Verificar: o script não aponta nenhuma falha em todo o `xano-workspace/api`. Por HTTP, depois de desativar um usuário de teste, o token antigo dele é negado em `ponto/marcar` e em `ferias/solicitacoes`.
- [ ] 3.7 [CB 1.9] Revogação em massa: `usuarios/{id}/status PATCH` (ao desativar), `solicitacoes_desligamento/{id}/aprovar` (desligamento imediato) e `.../concluir` encerram todas as sessões do usuário, com `revogada_em` preenchido. Verificar por HTTP: o usuário com duas sessões ativas tem os dois tokens recusados depois da desativação.
- [ ] 3.8 [CB 1.11] Bloqueio de autoaprovação (item 1.5 da auditoria, design D4) em todos os endpoints de decisão listados no D4, com a auditoria `autoaprovacao_bloqueada` gravada antes da recusa. Verificar por HTTP com uma conta RH que tem colaborador vinculado:
  - aprovar as próprias férias, ausência e documento retorna acesso negado e gera o evento consultável em `auditoria GET`;
  - um Gestor aprovando a própria correção de ponto é negado;
  - decidir solicitações de outro colaborador continua funcionando.
  - Parcial em 2026-10-06 (código publicado no workspace 147338). Com a conta Admin (colaborador 2):
    - `ferias/5/aprovar|rejeitar`, `ausencias/8/aprovar` e `documentos/18/aprovar` → 403 "Voce nao pode decidir uma solicitacao propria.";
    - os status continuam inalterados;
    - os 4 eventos `autoaprovacao_bloqueada` (falha) aparecem em `auditoria GET`;
    - as férias 6, de outro colaborador, passam pelo bloqueio e param na validação de status (400), sem alterar dados.

    Falta o cenário do Gestor com a própria correção de ponto (não há conta Gestor de teste) e uma decisão positiva efetivamente aplicada.
- [ ] 3.9 [CB 1.12] Anonimato da pesquisa de clima (item 1.6 da auditoria, design D5): `perguntas_clima/{id}/responder` grava a participação e incrementa `resposta_clima_agregado`, sem gravar em `resposta_clima`. Também valida pesquisa `ativo`, período, colaborador não desligado e a guarda completa. `pesquisas_clima/{id}/resultados` passa a ler o agregado. Verificar por HTTP:
  - resposta fora do período, de pesquisa inativa ou de colaborador desligado é recusada sem gravar participação;
  - resposta válida incrementa o agregado e nenhuma linha nova aparece em `resposta_clima`;
  - os resultados continuam suprimindo grupos abaixo de `minimo_respostas`.
- [ ] 3.10 [CB 1.13] Function idempotente para consolidar as linhas legadas de `resposta_clima` em `resposta_clima_agregado`, executada uma vez com `xano function run`. Responder à Open Question do `design.md` sobre dados reais. Verificar: a soma das quantidades no agregado é igual ao total de linhas legadas por pergunta, e uma segunda execução não altera nada.
- [x] 3.11 [CB 1.14] Troca de e-mail de conta (item 1.7 da auditoria, design D9): `usuarios/{id} PATCH` passa a enfileirar no `email_outbox` um alerta para o e-mail anterior e a auditar os valores anterior e novo. Verificar por HTTP: a troca de e-mail de uma conta de teste gera a linha no outbox para o endereço antigo e o evento de auditoria.
  - O código já estava no git desde o PR #3, mas só foi publicado no Xano junto com o `usuarios/{id} PATCH` (guarda da 3.3). Verificado em 2026-10-08: trocar o e-mail de uma conta de teste gerou 1 linha no `email_outbox` para o **e-mail antigo** (status `pendente`, sem o endereço novo no texto) e o evento `atualizar_usuario` na auditoria, com os valores anterior e novo.
- [ ] 3.12 [CB 1.15] Swagger (item 1.7 da auditoria, design D9): regenerar os tokens de swagger de todos os grupos no Xano e desativar o swagger público. Fazer `pull` para atualizar os `api/*/conecta_rh_*.xs`. Verificar: os tokens antigos do histórico do git não abrem mais a documentação (teste no navegador) e o diff pós-pull mostra os tokens novos ou o swagger desativado.
- [ ] 3.13 [CB 1.16] Documentar em `docs/regras-de-negocio.md`:
  - as regras novas da Parte 1 (guarda de acesso, sessão no token, reenvio de OTP, autoaprovação, troca de e-mail e swagger);
  - a reescrita da seção 11.6 (anonimato por agregação);
  - o risco aceito do bloqueio por senha errada (D9).

  Verificar: cada regra cita o endpoint correspondente, e a seção 2.6 e a 11.6 não contradizem o código.
- [ ] 3.14 [CB 1.17] Registrar as evidências da Parte 1 em `docs/evidencias/seguranca.md`, com o cenário, a requisição (sem token completo) e o resultado esperado e obtido de cada verificação das tarefas 1.4 a 1.15. Verificar: o arquivo não contém e-mail, CPF nem token reais.

**2. Requisitos da spec não cumpridos (Parte 2)**

- [ ] 3.15 [CB 2.1] Gestor decide férias (item 2.1 da auditoria, design D6): `ferias/{id}/aprovar|rejeitar` aceitam RH/Admin e o Gestor do departamento do colaborador. Verificar por HTTP: o Gestor aprova férias da própria equipe, recebe acesso negado para outro departamento e não consegue aprovar as próprias férias.
- [ ] 3.16 [CB 2.2] Delegação vigente (item 2.2 da auditoria, design D6) em `ferias/{id}/aprovar|rejeitar` e `correcoes_ponto/{id}/aprovar|rejeitar`. A auditoria registra o titular. Verificar por HTTP: o substituto decide durante a vigência; depois do cancelamento, ou com `data_fim` passada, é negado; uma delegação com escopo incompatível é ignorada.
- [ ] 3.17 [CB 2.3] Gestor nas ausências (item 2.1 da auditoria): conferir que nenhuma resposta acessível ao Gestor (`calendario`, `central_de_tarefas` e `minha_equipe`) inclui documento, atestado ou observação clínica da ausência. Verificar: inspeção do `output` de cada endpoint e uma chamada HTTP com conta Gestor.
- [ ] 3.18 [CB 2.4] Criar `rotinas/processar_diarias POST` (item 2.3 da auditoria, design D7), com as 6 transições na ordem do design, idempotente e auditado com contagens. Verificar por HTTP com dados sintéticos de cada caso:
  - todas as transições são aplicadas;
  - a segunda execução retorna contagens zeradas;
  - um colaborador `Desligado` não é reativado;
  - Gestor e Colaborador são negados.
- [ ] 3.19 [CB 2.5] Estender `status_operacional GET` com a contagem pendente de cada transição da rotina diária. Verificar: os números batem com o que a rotina aplica logo em seguida.
- [ ] 3.20 [CB 2.6] Criar `ciclos_avaliacao/{id}/status PATCH`, aceitando só as transições válidas e auditado. `metas POST` e `avaliacoes POST` passam a exigir ciclo `em_andamento`. Verificar por HTTP: `planejamento → concluido` é rejeitado, a sequência válida é aceita e criar uma meta em ciclo `planejamento` é rejeitado.
- [ ] 3.21 [CB 2.7] Criar `pesquisas_clima/{id}/encerrar POST` (RH/Admin, auditado). Verificar: depois de encerrar, `perguntas_clima/{id}/responder` recusa novas respostas.
- [ ] 3.22 [CB 2.8] Em `onboarding_item/{id}/concluir`, concluir o onboarding quando não restar nenhum item pendente. Verificar por HTTP: concluir o último item muda `onboarding.status` para `concluido`, e concluir um item intermediário não muda.
- [ ] 3.23 [CB 2.9] Em `organograma GET` e `colaboradores/aniversariantes GET` (item 2.4 da auditoria), trocar o filtro para `status != "Desligado"`. Verificar por HTTP: um colaborador com status `Ferias` aparece nos dois, e um `Desligado` não aparece.
- [ ] 3.24 [CB 2.10] Criar `minha_equipe GET` (item 2.5 da auditoria, design D8): só Gestor, escopo do departamento, `output` explícito sem CPF, salário, dados bancários nem contato. Verificar por HTTP: o Gestor recebe só a própria equipe sem campos sensíveis, e RH, Admin e Colaborador são negados.
- [ ] 3.25 [CB 2.11] Completar o dashboard do gestor em `central_de_tarefas` com as avaliações pendentes da equipe, reaproveitando as consultas já existentes. Verificar: os campos do cenário "Dashboard do gestor" da spec aparecem na resposta para uma conta Gestor.
- [ ] 3.26 [CB 2.12] Deixar `task/concluir_desligamentos_agendados.xs` com `active = false` (item 2.6 da auditoria) e documentar no cabeçalho do arquivo que ele é backlog até o upgrade do plano. Verificar: o dry-run completo não mostra operação pendente para a task.
- [ ] 3.27 [CB 2.13] Retenção (item 2.7 da auditoria, design D10): `documentos POST` preenche `retencao_ate` a partir de `documento_obrigatorio_regra` quando houver regra aplicável. Criar `documentos/retencao_vencida GET` (RH/Admin, só leitura). Verificar por HTTP: um documento com regra de retenção recebe a data, e a listagem mostra os vencidos sem alterar nenhum.
- [ ] 3.28 [CB 2.14] Backup (item 2.7 da auditoria, design D10): documentar em `docs/monitoramento.md` o procedimento (`xano workspace pull` versionado mais a exportação de dados) e executar uma restauração num workspace de teste. Verificar: o resultado da restauração fica registrado em `docs/evidencias/backup.md`.
- [ ] 3.29 [CB 2.15] Registrar no `design.md` do `conectarh.gestao` as decisões da Parte 2: Gestor decide férias, delegação por vigência, rotina diária manual, ciclo de avaliação, versionamento pelo grupo de API, rastreamento no backlog, backup e retenção. Atualizar `docs/regras-de-negocio.md` (seções de férias, ponto, delegação, avaliação, onboarding, documentos e organograma). Verificar: nenhuma regra do documento contradiz os endpoints alterados nas tarefas 2.1 a 2.13.
- [ ] 3.30 [CB 2.16] Registrar as evidências da Parte 2 em `docs/evidencias/rotinas-e-fluxos.md`. Verificar: há um cenário por tarefa de 2.1 a 2.13, sem dados pessoais.

**3. Documentação desatualizada ou contraditória (Parte 3)**

- [ ] 3.31 [CB 3.1] No `tasks.md` do `conectarh.gestao`:
  - trocar SendGrid e `SENDGRID_API_KEY` por Brevo e `BREVO_API_KEY` nas tarefas 2.3, 3.2, 4.5, 5.3, 5.4, 5.5 e 5.6;
  - corrigir a nota "todos os 62 endpoints" da 2.3 para refletir a auditoria e a tarefa 1.8 desta change;
  - remover `/api/v1/` da 7.10;
  - reabrir a 4.6, com nota apontando para a tarefa 2.2 desta change.

  Verificar: `grep -i sendgrid` no arquivo não retorna nada, e a 4.6 está `[ ]`.
- [ ] 3.32 [CB 3.2] Marcar de novo a 4.6 do `conectarh.gestao` como concluída, com referência à tarefa 2.2 desta change, depois que a 2.2 estiver concluída. Verificar: a nota da 4.6 não descreve mais o gap de integração com os endpoints de aprovação.
- [ ] 3.33 [CB 3.3] Em `docs/figma-prototipo.md`, trocar a seção "Handoff para Reflex" por "Handoff para Streamlit", com as regras da Parte 4 e o link oficial do protótipo. Verificar: `grep -i reflex` no arquivo não retorna nada, e o link abre o arquivo `fph1M5tB4rA4gqfIysSmkn`.
- [ ] 3.34 [CB 3.4] No `design.md` do `conectarh.gestao`:
  - atualizar a contagem de endpoints para 178;
  - remover a afirmação "nenhum endpoint aceita uma requisição fora do escopo autorizado";
  - depois da tarefa 1.8, substituir essa afirmação pela garantia verificada pelo `tools/checar_endpoints.py`.

  Verificar: a contagem bate com `find xano-workspace/api -name "*.xs"`, sem contar os arquivos de grupo.
- [ ] 3.35 [CB 3.5] Em `docs/domain-model.md`, remover a frase que diz que RegraContrato e RegraAplicada não têm endpoint, citando `resolver_regra` e `regras_override/aplicar`. Verificar: a seção "RegraContrato / RegraAplicada" bate com o código.
- [ ] 3.36 [CB 3.6] Atualizar o README (design D11): explicar que os grupos refletem a ordem histórica de criação, incluir a tabela de domínio por grupo de API e remover "organizados por domínio". Verificar: cada um dos 10 grupos aparece na tabela com seus módulos.
- [ ] 3.37 [CB 3.7] Criar `docs/evidencias/`, versionada, com um `README.md` de regras (sem dados pessoais, mascaramento de e-mail e token). Migrar o conteúdo não sensível de `docs/testes-integracao.md`, `docs/testes-seguranca.md` e `docs/auditoria.md`. Ajustar a tarefa 7.6 do `conectarh.gestao` para apontar para essa pasta. Verificar: `git status` mostra `docs/evidencias/` rastreada, e `grep -E "@|Bearer "` na pasta não encontra dado real.
- [ ] 3.38 [CB 3.8] Remover do workspace e do Xano `function/getting_started_template/*` e `ai/agent`, que são exemplos do Xano sem uso. Verificar: `grep` não encontra referência a eles em `api/` nem em `function/conectahr/`; o dry-run com `--sync --delete` lista só esses itens, e o diff pós-pull está limpo.

**4. Frontend segue o protótipo do Figma (Parte 4)**

- [ ] 3.39 [CB 4.1] No `design.md` do `implementar-frontend-streamlit`, registrar a decisão "Protótipo Figma como fonte única", com o link oficial e as 7 regras do design D13 desta change. Verificar: o link e as regras aparecem numa decisão própria do documento.
- [ ] 3.40 [CB 4.2] Conferir no Figma quais destas telas existem: troca de senha no primeiro acesso, logout e expiração do token, organograma, comunicados e FAQ, solicitações ao RH, pesquisa de clima, indicadores, gestão de usuários, cargos, departamentos e colaboradores, desligamento, delegações, sessões, notificações e preferências, calendário, minha equipe e dashboard do gestor. Registrar a lista das que faltam como pendência no `design.md` do frontend. Verificar: cada tela aparece com o nó do Figma ou com a marcação "a desenhar".
- [ ] 3.41 [CB 4.3] Adicionar ao `tasks.md` do `implementar-frontend-streamlit` uma seção por tela da 4.2, no ciclo "conferir no Figma (desenhar antes, se faltar) → construir → integrar → testar". A troca de senha no primeiro acesso e a expiração do token entram como prioridade. Verificar: `openspec status --change implementar-frontend-streamlit` mostra as tarefas novas, e cada tela tem uma tarefa de conferência no Figma.
- [ ] 3.42 [CB 4.4] Adicionar ao spec do `implementar-frontend-streamlit` o cenário de tela para a troca de senha no primeiro acesso e a sessão revogada (o usuário volta para "Entrar" com mensagem). Verificar: `openspec validate implementar-frontend-streamlit` passa.

**5. Instruções para agentes de IA (Parte 5)**

- [ ] 3.43 [CB 5.1] Reescrever o `AGENTS.md` da raiz como fonte única, com:
  - visão e perfis;
  - fora de escopo;
  - stack e pastas;
  - fluxo OpenSpec → branch `feature/CON-XX-descricao` → commit `CON-XX` → PR com revisão, sem push direto no `master`;
  - checklist de endpoint do Xano;
  - regras do frontend com o link do Figma;
  - segredos;
  - testes contra o Xano real e evidências em `docs/evidencias/`;
  - idioma pt-BR;
  - configuração do MCP do Figma no Codex, no Gemini CLI e no Claude, com o Dev Mode como alternativa.

  Verificar: cada item da Parte 5.1 e da 5.4 do pedido tem uma seção correspondente.
- [ ] 3.44 [CB 5.2] Criar `frontend/AGENTS.md`, com:
  - as regras da Parte 4;
  - como rodar (venv, `requirements.txt`, `secrets.toml` de exemplo sem valores reais);
  - o padrão do `api_client.py`;
  - o uso obrigatório de `theme.py` e de `st.html()`;
  - os 6 estados de UI.

  O arquivo remete ao `AGENTS.md` da raiz. Verificar: seguir as instruções de execução num clone limpo sobe o Streamlit.
- [ ] 3.45 [CB 5.3] Criar `xano-workspace/AGENTS.md`, com:
  - o checklist de endpoint;
  - os padrões de XanoScript adotados (precondition, "registra e depois falha", auditoria inline, outbox de e-mail e rotina manual);
  - o fluxo de publicação (`push --dry-run` → push → `pull` e diff);
  - o uso do `tools/checar_endpoints.py`.

  Verificar: o checklist é igual ao da raiz e ao que o script confere.
- [ ] 3.46 [CB 5.4] Criar `.gemini/settings.json` com `{"contextFileName": "AGENTS.md"}`. Criar `GEMINI.md` e `CLAUDE.md` na raiz, cada um com a instrução única "Siga integralmente o AGENTS.md deste repositório." Conferir que `.agents/`, `skills-lock.json` e `.claude/scheduled_tasks.lock` continuam no `.gitignore`. Verificar: `git status` mostra os 3 arquivos novos rastreados e nenhum arquivo pessoal.
- [ ] 3.47 [CB 5.5] Com Codex, Gemini CLI e Claude Code, abrir o repositório e perguntar "Quais são as regras para criar um endpoint e uma tela neste projeto?". Verificar: as três respostas citam o checklist de endpoint e o link do Figma. Registrar as respostas resumidas em `docs/evidencias/agentes.md`.

**6. Integração final**

- [ ] 3.48 [CB 6.1] Rodar `tools/checar_endpoints.py` em todo o workspace e um smoke test HTTP por perfil (Admin, RH, Gestor e Colaborador), cobrindo login, um endpoint de leitura e um de decisão de cada módulo alterado. Verificar: zero falhas no script, resultado esperado em todas as chamadas e registro em `docs/evidencias/`.

**Novas tarefas**

- [ ] 3.49 [novo] Corrigir os vazamentos do resultado da pesquisa de clima (design C4): `pesquisas_clima/{id}/resultados` só responde depois que a pesquisa está encerrada (`ativo = false` ou `data_fim` passada) e aplica supressão complementar quando um único grupo é omitido. Verificar por HTTP: a consulta com a pesquisa aberta é recusada, e com um único departamento abaixo do mínimo o total geral também é omitido.

## 4. Adequação à LGPD [LG]

**1. Documentação e governança (Parte 1, só documentos)**

- [ ] 4.1 [LG 1.1] Criar `docs/lgpd/registro-de-operacoes.md` (arts. 7, 11 e 37), com uma linha por finalidade. Colunas: finalidade, dados, titular, base legal, quem acessa, operador, prazo de retenção e medidas de segurança. O ponto de partida é o inventário do proposal. Verificar: toda tabela de `xano-workspace/table/` com dado pessoal aparece em pelo menos uma linha, conferido com uma lista das 49 tabelas anexada ao documento.
- [ ] 4.2 [LG 1.2] Criar `docs/lgpd/aviso-de-privacidade.md` (arts. 6, VI, e 9), em linguagem simples, com:
  - dados coletados e por quê;
  - compartilhamento com os operadores da 1.6;
  - prazos de guarda;
  - direitos do titular e como exercê-los;
  - registro de IP e dispositivo no login e na auditoria;
  - contato do encarregado.

  Verificar: cada finalidade da 1.1 é citada no aviso.
- [ ] 4.3 [LG 1.3] Definir o encarregado (art. 41; Res. CD/ANPD 18/2024; sugestão: Matheus) e um e-mail de contato. Publicar no aviso da 1.2 e no `README.md`. Verificar: o mesmo contato aparece nos dois arquivos.
- [ ] 4.4 [LG 1.4] Criar `docs/lgpd/plano-de-incidentes.md` (art. 48; Res. CD/ANPD 15/2024), com:
  - quem detecta e quem avalia;
  - critérios de risco;
  - modelo de comunicação à ANPD e aos titulares em até 3 dias úteis;
  - registro interno de todo incidente;
  - ligação com os alertas de `docs/monitoramento.md`.

  Verificar: um incidente simulado (token vazado) percorre o plano do começo ao fim e fica registrado em `docs/evidencias/lgpd.md`.
- [ ] 4.5 [LG 1.5] Criar `docs/lgpd/ripd.md` (art. 38) para dados de saúde, adolescentes aprendizes e controle de jornada, com riscos, probabilidade, impacto e medidas. Incluir os riscos residuais do `design.md`: auditoria antiga com dados completos e, se for o caso, campos `image` públicos. Verificar: cada risco aponta para uma tarefa desta change ou da `corrigir-brechas-e-alinhar-documentacao`.
- [ ] 4.6 [LG 1.6] Criar `docs/lgpd/operadores.md` (arts. 33 a 39; Res. CD/ANPD 19/2024), com Xano, Brevo, hospedagem do Streamlit, GitHub e o serviço usado em `arquivo_url`. Para cada um: dados recebidos, região, termos de tratamento e mecanismo de transferência internacional. Verificar: todo domínio externo encontrado por `grep -rhoE "https://[a-z0-9.-]+" xano-workspace frontend README.md` está na lista ou é justificado como não recebedor de dados pessoais.
- [ ] 4.7 [LG 1.7] Criar `docs/lgpd/legitimo-interesse.md` (arts. 7, IX, e 10), com o teste de balanceamento para aniversariantes, mural de reconhecimento, pesquisa de clima e logs de segurança: finalidade, necessidade, expectativa do colaborador e salvaguardas, incluindo a oposição da 3.3. Verificar: cada linha da 1.1 com base em legítimo interesse tem seu teste.
- [ ] 4.8 [LG 1.8] Integrar a LGPD aos documentos do projeto:
  - registrar no `docs/regras-de-negocio.md` que os requisitos da seção 12 (delta desta change) passam a valer;
  - acrescentar ao `AGENTS.md` três regras: campo sensível novo atualiza a 1.1 e a 1.5; dados pessoais são mascarados em auditoria e logs; serviço externo novo atualiza a 1.6;
  - no `docs/project-overview.md` e no `openspec/config.yaml`, trocar a frase genérica sobre LGPD por um link para `docs/lgpd/`.

  Verificar: `openspec validate adequacao-lgpd` passa, e cada cenário da seção 12 tem tarefa correspondente (tabela cenário → tarefa anexada ao fim deste arquivo).

**2. Ajustes no backend (Parte 2, antes da demonstração de dezembro)**

- [ ] 4.9 [LG 2.1] Mascarar dados pessoais na auditoria (design L3):
  - em `meus_dados_bancarios PATCH`, mascarar agência, conta e dígito (ex.: `banco=341; agencia=****; conta=****1234`);
  - procurar no código todas as auditorias que gravam CPF, salário, telefone, endereço ou e-mail inteiros e aplicar a mesma regra, listando os endpoints alterados no commit.

  Verificar por HTTP: alterar dados bancários e cadastro de uma conta de teste e consultar `auditoria GET`. Nenhuma linha nova contém conta, CPF, salário, telefone, endereço ou e-mail completos.
- [ ] 4.10 [LG 2.2] Auditar a abertura de arquivos sensíveis (design L4): `acessar_arquivo_documento` em `documentos/{id}/arquivo GET`, na abertura do comprovante de ausência e na do documento de `evento_sst`. Se não houver endpoint de leitura, criar um, e retirar a URL do arquivo das listagens. Verificar por HTTP: cada abertura gera um evento com autor, recurso, registro e data, e as listagens não devolvem mais a URL.
- [ ] 4.11 [LG 2.3] Motivo da ausência sem diagnóstico (design L5):
  - adicionar `ausencia.motivo_tipo` (enum) com push isolado do schema;
  - tornar `ausencia.motivo` privado e sem novas gravações;
  - migrar os registros existentes com uma function idempotente (`motivo_tipo = "outro"`);
  - recusar código CID na observação.

  Verificar:
  - texto livre no motivo e `J11` na observação são recusados;
  - a migração, rodada duas vezes, não altera nada na segunda;
  - por HTTP com conta Gestor: nenhum endpoint acessível a ele devolve motivo, observação ou comprovante.
- [ ] 4.12 [LG 2.4] Links de arquivos controlados (design L6): `documento.arquivo_url` e `evento_sst.documento_url` aceitam só o armazenamento do Xano ou hosts de `$env.ARQUIVOS_DOMINIOS_APROVADOS`. Confirmar se os campos `image` (`ausencia.comprovante`, `documento.imagem_frente`) são privados; se forem públicos, corrigir nesta tarefa e registrar na 1.5. Verificar: um link público de drive é recusado com mensagem clara, e uma URL do armazenamento do Xano é aceita.
- [ ] 4.13 [LG 2.5] Códigos de acesso com hash (design L7):
  - spike: testar se o mecanismo de hash da senha funciona para um texto qualquer; senão, usar `|md5` com `$env.CODIGO_ACESSO_PEPPER` e o id do usuário; registrar o resultado no `design.md`;
  - aplicar em `auth/login`, `auth/otp/reenviar`, `auth/otp/validar`, `auth/senha/esqueci` e `auth/senha/redefinir`, num push separado, fora do horário de testes.

  Verificar:
  - `xano workspace pull --records` não mostra códigos de 6 dígitos em `otp_codigo` nem em `reset_senha_codigo`;
  - login com OTP e redefinição de senha continuam funcionando ponta a ponta;
  - o limite de 5 tentativas continua valendo.
- [ ] 4.14 [LG 2.6] Mínimo de pessoas nos indicadores (design L8): `indicadores GET` e `indicadores/exportar_csv GET` omitem grupos com menos de `$env.INDICADORES_MINIMO_PESSOAS` (padrão 5) e aplicam a supressão complementar do total. Verificar por HTTP: com dados de teste, um departamento com 2 pessoas não aparece na consulta nem no CSV, e o total some quando só um grupo é omitido.
- [ ] 4.15 [LG 2.7] Registrar no `design.md` (L13) e no `docs/regras-de-negocio.md` a dependência das tarefas 1.4 a 1.9 da `corrigir-brechas-e-alinhar-documentacao` e conferir o andamento delas. Verificar: os endpoints novos e alterados desta change passam no `python tools/checar_endpoints.py`.

**3. Direitos do titular (Parte 3, endpoints e telas)**

- [ ] 4.16 [LG 3.1] Criar `meus_dados GET` (art. 18, II e V; design L9), só para o próprio colaborador, com `formato=json|csv`. Inclui:
  - cadastro, contrato e histórico;
  - metadados de documentos;
  - férias, ausências, ponto e banco de horas;
  - avaliações, metas e PDI;
  - solicitações e notificações;
  - sessões.

  Não inclui respostas de clima nem dados de terceiros, e grava `exportar_meus_dados` na auditoria. Verificar por HTTP: o arquivo de uma conta de teste contém todas as categorias da 1.1 que se aplicam a ela, o evento aparece na auditoria e outra conta não consegue obter esses dados.
- [ ] 4.17 [LG 3.2] Pedidos LGPD na central de solicitações (arts. 18 e 19; design L9):
  - schema: `privacidade_lgpd` no enum `solicitacao_rh.tipo`, mais `subtipo_lgpd` e `prazo_resposta` (abertura + 15 dias);
  - alerta na `central_de_tarefas` do RH quando faltarem 3 dias ou menos;
  - resposta e decisão pelo `atender`/`indeferir`, já auditados.

  Verificar por HTTP: um pedido criado aparece na fila do RH com o prazo, o alerta aparece quando o prazo se aproxima (dados de teste) e a resposta gera notificação ao colaborador.
- [ ] 4.18 [LG 3.3] Preferências de privacidade (art. 18, § 2º; design L9): tabela `preferencia_privacidade` e endpoints `minhas_preferencias_privacidade GET/PATCH`. `colaboradores/aniversariantes` e `mural_reconhecimento` passam a respeitá-las. Verificar por HTTP: depois de sair das duas listas, o colaborador não aparece em nenhuma delas para outro usuário, e os reconhecimentos dele continuam visíveis para ele e para o RH.
- [ ] 4.19 [LG 3.4] Tela "Privacidade" (design L12):
  - desenhar no Figma (protótipo `fph1M5tB4rA4gqfIysSmkn`) antes de codar;
  - construir no Streamlit com aviso, "Baixar meus dados", formulário de pedido LGPD, preferências da 3.3 e contato do encarregado;
  - adicionar à tela Entrar um link para o aviso, legível sem login.

  Verificar:
  - prints lado a lado com o nó do Figma;
  - os 6 estados de UI (carregando, vazio, sucesso, erro, bloqueado, permissão negada);
  - o link da tela Entrar abre o aviso sem login;
  - a tela só mostra dados do próprio colaborador.

**4. Retenção, anonimização e adolescentes (Parte 4, pós-MVP se não couber até dezembro)**

- [ ] 4.20 [LG 4.1] Criar `docs/lgpd/retencao.md` com o prazo de guarda de cada categoria, marcado "a confirmar com o jurídico". Guarda longa para documentos trabalhistas, ASO e registros de SST; sugestão de 6 a 12 meses para IP e dispositivo de `sessao`, `email_outbox` enviado e códigos expirados. Ligar à regra de `documento.retencao_ate` (tarefa 2.13 da `corrigir-brechas`). Verificar: cada linha da 1.1 tem um prazo neste documento.
- [ ] 4.21 [LG 4.2] Incluir em `rotinas/processar_diarias` (pré-requisito: tarefa 2.4 da `corrigir-brechas`):
  - a limpeza de IP e dispositivo de sessões e de destinatário e corpo do `email_outbox` com prazo vencido;
  - a listagem ao RH dos desligados com prazo de guarda cumprido.

  A rotina é idempotente e auditada com contagens. Verificar por HTTP com dados de teste: a primeira execução limpa e conta, e a segunda devolve contagens zeradas.
- [ ] 4.22 [LG 4.3] Criar `colaboradores/{id}/anonimizar POST` (arts. 15, 16 e 18, IV; design L10), para RH e Admin, com justificativa:
  - substitui nome, CPF, contato, endereço, data de nascimento e dados bancários, e desativa o usuário;
  - preserva histórico agregado e auditoria sem valores;
  - recusa a operação com prazo de guarda vigente ou processo em aberto.

  Verificar por HTTP:
  - depois de anonimizar um colaborador de teste desligado, nenhum endpoint devolve dado que o identifique e os indicadores continuam com a mesma contagem;
  - a tentativa com prazo vigente é recusada;
  - nenhum registro é excluído.
- [ ] 4.23 [LG 4.4] Adolescentes aprendizes (art. 14; ECA Digital; design L11):
  - a ativação do contrato de menor de 18 anos exige documento de responsável legal aprovado;
  - as preferências nascem com `ocultar_aniversario` e `ocultar_mural` verdadeiros;
  - registrar na 1.5.

  Verificar por HTTP: o cadastro de um aprendiz de 16 anos sem responsável legal é bloqueado, e ele não aparece entre os aniversariantes nem no mural.
- [ ] 4.24 [LG 4.5] Confirmar no painel do Xano se o banco tem criptografia em repouso e em que região está, e registrar na 1.6. Se não houver criptografia, criar tarefa de criptografia de campo para CPF e conta bancária antes de fechar esta. Verificar: a 1.6 traz a resposta com a data da consulta.
- [ ] 4.25 [LG 4.6] Criar `docs/evidencias/README.md` com a regra de mascaramento (sem nome, CPF, e-mail ou token completo) e um checklist de revisão antes de cada commit nessa pasta. Fazer isto antes da primeira evidência desta change, mesmo estando na Parte 4. Se a tarefa 3.7 da `corrigir-brechas` já tiver criado o arquivo, só completar com o checklist. Verificar: `grep -rE "@|Bearer |[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}" docs/evidencias` não encontra dado real.

**5. Integração final**

- [ ] 4.26 [LG 5.1] Rodar `python tools/checar_endpoints.py` e um teste HTTP por perfil (Admin, RH, Gestor e Colaborador) cobrindo `meus_dados`, as preferências, um pedido LGPD, a abertura de um arquivo e uma consulta de indicadores. Verificar: zero falhas no script, o resultado esperado em todas as chamadas e registro em `docs/evidencias/lgpd.md`.

## 5. Integração final

- [ ] 5.1 Rodar `python tools/checar_endpoints.py` e um teste HTTP por perfil (Admin, RH, Gestor e Colaborador) cobrindo os fluxos alterados por esta change, e `openspec validate concluir-mvp-conectarh`. Verificar: zero falhas, resultado esperado em todas as chamadas e registro em `docs/evidencias/`.
