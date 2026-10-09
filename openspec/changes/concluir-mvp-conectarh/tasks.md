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
- [ ] 1.6 [GE 7.6] Preparar a entrega final com README, arquitetura, especificacoes OpenSpec, evidencias de testes (`docs/evidencias/`) e demonstracao; verificar que um avaliador consegue reproduzir o fluxo principal.
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
- [ ] 2.41 [CB 4.3] Tela "Expiração do token e sessão revogada": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `auth/me` e qualquer 401 com "Sessao encerrada ou expirada." → testar os 6 estados de UI e o escopo por perfil. **Prioridade:** a expiração do token e a sessão revogada voltam o usuário para "Entrar" com mensagem (cenário na spec principal).
- [ ] 2.42 [CB 4.3] Tela "Organograma": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `organograma GET` → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.43 [CB 4.3] Tela "Comunicados e FAQ": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `comunicados`, `meus_comunicados`, `artigos_faq` → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.44 [CB 4.3] Tela "Solicitações ao RH": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `solicitacoes`, `minhas_solicitacoes` → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.45 [CB 4.3] Tela "Pesquisa de clima": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `pesquisas_clima`, `perguntas_clima` e as respostas → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.46 [CB 4.3] Tela "Indicadores": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `indicadores GET` e `indicadores/exportar_csv GET` → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.47 [CB 4.3] Tela "Gestão de usuários": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `usuarios` (criar, editar, status) → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.48 [CB 4.3] Tela "Cargos": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `cargos`, `listar_cargos` → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.49 [CB 4.3] Tela "Departamentos": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `departamentos`, `listar_departamentos` → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.50 [CB 4.3] Tela "Colaboradores (lista e cadastro)": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `colaboradores` e `colaboradores/{id}` → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.51 [CB 4.3] Tela "Desligamento": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `solicitacoes_desligamento`, `minhas_solicitacoes_desligamento` → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.52 [CB 4.3] Tela "Delegações": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `delegacoes`, `minhas_delegacoes` → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.53 [CB 4.3] Tela "Calendário": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `calendario GET` → testar os 6 estados de UI e o escopo por perfil.
- [ ] 2.54 [CB 4.3] Tela "Minha equipe e dashboard do gestor": conferir no Figma (desenhar antes, se faltar; ver a tabela do `design.md` do frontend arquivado) → construir → integrar com `minha_equipe GET` (tarefa 3.24) e o dashboard em `central_de_tarefas` (tarefa 3.25) → testar os 6 estados de UI e o escopo por perfil.

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
- [x] 3.6 [CB 1.8] Guarda de acesso nos grupos Ponto, Férias, Ausências, Documentos, Desligamentos, Cargos e Departamentos. Verificar: o script não aponta nenhuma falha em todo o `xano-workspace/api`. Por HTTP, depois de desativar um usuário de teste, o token antigo dele é negado em `ponto/marcar` e em `ferias/solicitacoes`.
  - Publicado em 2026-10-08 (68 endpoints de Ponto, Férias, Ausências, Documentos, Desligamentos, Cargos e Departamentos). `python tools/checar_endpoints.py` em todo o `xano-workspace/api`: **173 endpoints autenticados, 0 falhas**. Por HTTP:
    - Admin: 14 de 15 leituras sem parâmetro obrigatório em 200; a exceção é `minhas_solicitacoes_desligamento`, que responde 403 por regra (só colaborador ou gestor);
    - conta de teste desativada, com o token emitido antes: `ponto/marcar` e `ferias/solicitacoes` → 401 "Usuario inativo.", antes de qualquer gravação.
  - Ao conferir o `--dry-run`, os padrões `-i` sem aspas foram expandidos pelo shell e o preview mostrou 17 dos 68 arquivos. Sempre citar `"api/<grupo>/**/*.xs"` entre aspas e conferir a contagem de `Matched`.
- [x] 3.7 [CB 1.9] Revogação em massa: `usuarios/{id}/status PATCH` (ao desativar), `solicitacoes_desligamento/{id}/aprovar` (desligamento imediato) e `.../concluir` encerram todas as sessões do usuário, com `revogada_em` preenchido. Verificar por HTTP: o usuário com duas sessões ativas tem os dois tokens recusados depois da desativação.
  - Publicado em 2026-10-08. A revogação entra logo depois de desativar a conta, nos três endpoints; nos dois de desligamento fica dentro da mesma transação. Por HTTP, com a conta de teste (usuário 15) em duas sessões ativas (40 e 41): o Admin desativa a conta e os dois tokens passam a responder 401 "Sessao encerrada ou expirada" (e não "Usuario inativo", o que prova a revogação). Depois de reativar, as sessões antigas seguem revogadas e um login novo funciona (sessão 42).
  - **Não exercitado ao vivo:** os caminhos de `solicitacoes_desligamento/{id}/aprovar` (desligamento imediato) e `.../concluir`. Usam o mesmo bloco de código, mas testá-los desliga um colaborador de forma irreversível. Ficam para a integração final com um colaborador de teste dedicado.
- [x] 3.8 [CB 1.11] Bloqueio de autoaprovação (item 1.5 da auditoria, design D4) em todos os endpoints de decisão listados no D4, com a auditoria `autoaprovacao_bloqueada` gravada antes da recusa. Verificar por HTTP com uma conta RH que tem colaborador vinculado:
  - aprovar as próprias férias, ausência e documento retorna acesso negado e gera o evento consultável em `auditoria GET`;
  - um Gestor aprovando a própria correção de ponto é negado;
  - decidir solicitações de outro colaborador continua funcionando.
  - Parcial em 2026-10-06 (código publicado no workspace 147338). Com a conta Admin (colaborador 2):
    - `ferias/5/aprovar|rejeitar`, `ausencias/8/aprovar` e `documentos/18/aprovar` → 403 "Voce nao pode decidir uma solicitacao propria.";
    - os status continuam inalterados;
    - os 4 eventos `autoaprovacao_bloqueada` (falha) aparecem em `auditoria GET`;
    - as férias 6, de outro colaborador, passam pelo bloqueio e param na validação de status (400), sem alterar dados.

    Falta o cenário do Gestor com a própria correção de ponto (não há conta Gestor de teste) e uma decisão positiva efetivamente aplicada.
  - Verificado por HTTP em 2026-10-07 e 2026-10-08, com a conta Admin (colaborador 2) e uma conta de teste (usuário 15, colaborador 21):
    - o Admin aprovando as próprias férias, ausência e documento → 403 "Voce nao pode decidir uma solicitacao propria.", status inalterados e 4 eventos `autoaprovacao_bloqueada` (falha) em `auditoria GET`;
    - a conta de teste, com perfil Gestor, aprovando a própria correção de ponto (id 4) → 403 e 1 evento `autoaprovacao_bloqueada` para `correcao_ponto`. A checagem vem antes do escopo, então vale mesmo para um Gestor sem departamento;
    - o Admin aprovando a correção do colaborador 21 (outra pessoa) → 200, sem regressão.
  - O perfil da conta de teste foi alterado só durante o teste e devolvido a Colaborador. Uma correção de ponto e um registro de ponto de teste ficaram no colaborador 21.
- [x] 3.9 [CB 1.12] Anonimato da pesquisa de clima (item 1.6 da auditoria, design D5): `perguntas_clima/{id}/responder` grava a participação e incrementa `resposta_clima_agregado`, sem gravar em `resposta_clima`. Também valida pesquisa `ativo`, período, colaborador não desligado e a guarda completa. `pesquisas_clima/{id}/resultados` passa a ler o agregado. Verificar por HTTP:
  - resposta fora do período, de pesquisa inativa ou de colaborador desligado é recusada sem gravar participação;
  - resposta válida incrementa o agregado e nenhuma linha nova aparece em `resposta_clima`;
  - os resultados continuam suprimindo grupos abaixo de `minimo_respostas`.
  - Publicado em 2026-10-08 (os endpoints `perguntas_clima/{id}/responder` e `pesquisas_clima/{id}/resultados` estavam só no git). Verificado por HTTP com uma conta Colaborador de teste e conferido no banco com `xano workspace pull --records`:
    - resposta válida (nota 4) → 200; o agregado ganhou a linha (pergunta 1, departamento 4, nota 4, quantidade 1) e `resposta_clima` continuou com as 2 linhas antigas, **sem nenhuma individual nova**;
    - resposta repetida → "Voce ja respondeu esta pergunta."; nota 6 → "A nota deve estar entre 1 e 5.";
    - pesquisa de teste com período encerrado → "Esta pesquisa esta fora do periodo de respostas." e **nenhuma participação gravada**;
    - `resultados` (Admin): pergunta 1 com quantidade 3 e média 4, por departamento e geral; a pergunta 2, abaixo do mínimo de 2, não aparece.
  - **Não exercitado ao vivo:** (a) pesquisa inativa, porque não há como encerrar uma pesquisa antes da tarefa de `pesquisas_clima/{id}/encerrar`; (b) colaborador desligado, porque o desligamento desativa a conta e a guarda barra antes da checagem; (c) supressão de um grupo que tem respostas, mas menos que o mínimo, por falta de dados.
  - Os vazamentos por complemento e por diferença seguem abertos, na tarefa [novo] da seção 3.
- [x] 3.10 [CB 1.13] Function idempotente para consolidar as linhas legadas de `resposta_clima` em `resposta_clima_agregado`, executada uma vez com `xano function run`. Responder à Open Question do `design.md` sobre dados reais. Verificar: a soma das quantidades no agregado é igual ao total de linhas legadas por pergunta, e uma segunda execução não altera nada.
  - Function publicada e executada em 2026-10-08 com `xano function run`. 1ª execução: 2 linhas consolidadas. 2ª: `ja_executada_antes: true` e 0 linhas. Conferido no banco: soma dos agregados (2) igual às linhas legadas, nota por nota; 1 evento na auditoria.
  - Resposta à pergunta em aberto do design: existem 2 linhas em `resposta_clima`, ambas do departamento 4 (notas 5 e 3). Pelo conteúdo parecem dados de teste; o risco residual (as linhas continuam correlacionáveis no banco, mas nenhum endpoint as lê) fica registrado para a decisão do grupo.
- [x] 3.11 [CB 1.14] Troca de e-mail de conta (item 1.7 da auditoria, design D9): `usuarios/{id} PATCH` passa a enfileirar no `email_outbox` um alerta para o e-mail anterior e a auditar os valores anterior e novo. Verificar por HTTP: a troca de e-mail de uma conta de teste gera a linha no outbox para o endereço antigo e o evento de auditoria.
  - O código já estava no git desde o PR #3, mas só foi publicado no Xano junto com o `usuarios/{id} PATCH` (guarda da 3.3). Verificado em 2026-10-08: trocar o e-mail de uma conta de teste gerou 1 linha no `email_outbox` para o **e-mail antigo** (status `pendente`, sem o endereço novo no texto) e o evento `atualizar_usuario` na auditoria, com os valores anterior e novo.
  - **Correção de 2026-10-08, ao testar a máscara da 4.9:** a verificação acima só exercitou a **primeira** troca de e-mail da conta. A segunda troca, e qualquer segundo alerta de acesso suspeito no `auth/login`, devolvia **HTTP 500 "Duplicate record"**. A causa era a chave do `email_outbox`, montada com `(now|to_text)`, que gera o texto literal "now" (`alerta_troca_email_16_now`); a coluna é única. No e-mail, a troca era aplicada e ficava **sem alerta e sem auditoria**. No login, o contador de tentativas **não era zerado** e a conta ficava presa em 500. Corrigido nos dois endpoints com `now|format_timestamp:"YmdHisv":"UTC"`, publicado e verificado: duas trocas seguidas de e-mail (200 e 200) e 3 rodadas de "3 senhas erradas e 1 certa" na mesma conta (200, 200, 200). Antes da correção a 2ª rodada falhava.
- [x] 3.12 [CB 1.15] Swagger (item 1.7 da auditoria, design D9): regenerar os tokens de swagger de todos os grupos no Xano e desativar o swagger público. Fazer `pull` para atualizar os `api/*/conecta_rh_*.xs`. Verificar: os tokens antigos do histórico do git não abrem mais a documentação (teste no navegador) e o diff pós-pull mostra os tokens novos ou o swagger desativado.
  - Feito em 2026-10-08 pela CLI, sem passar pela interface do Xano. Antes: os tokens de 7 grupos abriam a documentação (`apispec`, HTTP 200) e os 3 grupos sem o campo `swagger` estavam **abertos para qualquer pessoa**, com ou sem token. O repositório é **público**. Depois:
    - `swagger = {active: false}` em todos os 10 grupos: o `apispec` responde 404 com o token antigo, sem token e com qualquer token;
    - os tokens guardados no Xano foram trocados por valores novos, enviados de uma pasta temporária que foi apagada; nenhum dos 7 tokens do histórico do git continua no servidor;
    - o `pull` confirma `active: false` nos 10 grupos.
  - Atenção: um `xano workspace pull` reescreve os arquivos de grupo com o token novo do Xano. Antes de commitar, descarte essa linha. O `tools/checar_endpoints.py` agora reprova swagger ligado, grupo sem a configuração e token no arquivo.
  - Os tokens antigos continuam no histórico público do git, mas não valem mais. Reescrever o histórico não é necessário e seria destrutivo para os clones do grupo.
- [x] 3.13 [CB 1.16] Documentar em `docs/regras-de-negocio.md`:
  - as regras novas da Parte 1 (guarda de acesso, sessão no token, reenvio de OTP, autoaprovação, troca de e-mail e swagger);
  - a reescrita da seção 11.6 (anonimato por agregação);
  - o risco aceito do bloqueio por senha errada (D9).

  Verificar: cada regra cita o endpoint correspondente, e a seção 2.6 e a 11.6 não contradizem o código.
  - Feito em 2026-10-08 em `docs/regras-de-negocio.md`: itens 2 a 4 da 1.3 (reenvio e validação do código, troca de senha), a 1.4 (logout, `encerrar_outras` e revogação ao desativar), a 2.1, a 2.6 e a 11.6 (anonimato por agregação) foram reescritos, e a nova subseção **2.7** reúne guarda de acesso, rotas de primeiro acesso, autoaprovação, troca de e-mail, redefinição de senha, swagger e o risco aceito do bloqueio por senha errada. Cada regra cita o endpoint; os trechos reescritos foram conferidos contra o comportamento testado por HTTP.
- [x] 3.14 [CB 1.17] Registrar as evidências da Parte 1 em `docs/evidencias/seguranca.md`, com o cenário, a requisição (sem token completo) e o resultado esperado e obtido de cada verificação das tarefas 1.4 a 1.15. Verificar: o arquivo não contém e-mail, CPF nem token reais.
  - Criado `docs/evidencias/seguranca.md`, com cenário, esperado e obtido de cada verificação das tarefas 1.1 a 1.15. `grep` por e-mail, `Bearer`, token JWT e CPF: nada encontrado. As contas de teste aparecem só pelo papel.

**2. Requisitos da spec não cumpridos (Parte 2)**

- [x] 3.15 [CB 2.1] Gestor decide férias (item 2.1 da auditoria, design D6): `ferias/{id}/aprovar|rejeitar` aceitam RH/Admin e o Gestor do departamento do colaborador. Verificar por HTTP: o Gestor aprova férias da própria equipe, recebe acesso negado para outro departamento e não consegue aprovar as próprias férias.
  - Feito e publicado em 2026-10-08. Verificado por HTTP: o Gestor do departamento aprovou férias da equipe (200); sem escopo, aprovar e rejeitar dão 403; a autoaprovação continua bloqueada (403). Como a conta de teste de Admin atingiu o máximo de períodos de férias, os testes seguintes usaram um período já decidido: a autorização vem antes do estado, então 403 é sem escopo e "400 somente pendentes" é autorização concedida. Não verificado: o Gestor decidindo as próprias férias (a conta de Gestor de teste não pode pedir férias). Detalhes em `docs/evidencias/rotinas-e-fluxos.md`.
- [x] 3.16 [CB 2.2] Delegação vigente (item 2.2 da auditoria, design D6) em `ferias/{id}/aprovar|rejeitar` e `correcoes_ponto/{id}/aprovar|rejeitar`. A auditoria registra o titular. Verificar por HTTP: o substituto decide durante a vigência; depois do cancelamento, ou com `data_fim` passada, é negado; uma delegação com escopo incompatível é ignorada.
  - Feito e publicado em 2026-10-08, em `ferias/{id}/aprovar|rejeitar` e `correcoes_ponto/{id}/aprovar|rejeitar`. Verificado por HTTP: o substituto com delegação `correcao_ponto` vigente rejeitou a correção (200) e a auditoria registrou `decisao por delegacao do titular user_id=<titular>`; delegação cancelada 403; escopo incompatível (`documento`) 403; em férias a delegação vigente passa da autorização (400 "somente pendentes"). Não verificado: a delegação com `data_fim` passada (a criação recusa datas passadas) e o substituto concluindo uma solicitação de **férias** pendente. Perfis e gestor do departamento restaurados ao fim do teste.
- [x] 3.17 [CB 2.3] Gestor nas ausências (item 2.1 da auditoria): conferir que nenhuma resposta acessível ao Gestor (`calendario`, `central_de_tarefas` e `minha_equipe`) inclui documento, atestado ou observação clínica da ausência. Verificar: inspeção do `output` de cada endpoint e uma chamada HTTP com conta Gestor.
  - Feito junto com a 4.11, em 2026-10-08. **Achado:** `calendario GET` e `central_de_tarefas GET`, que o Gestor alcança dentro do escopo do departamento, copiavam o **registro inteiro** da ausência (motivo, observação e comprovante) para a resposta. Agora entregam só `id`, `colaborador_id`, `tipo`, `data_inicio`, `data_fim` e `status`.
  - Verificado por HTTP: o calendário devolve exatamente esses 6 campos para Admin, para a conta de teste como Gestor e como RH. `ausencias GET` é só RH e Admin, e `ausencias/{id}` e o comprovante são RH, Admin ou o dono, então o Gestor não os alcança.
  - **Ressalva:** na `central_de_tarefas` a lista `equipe_ausencias` veio vazia nas contas de teste (nenhuma é gestora de departamento com uma ausência aprovada na equipe), então o objeto restrito não foi observado com dados; o código é o mesmo do calendário. O endpoint responde 200 nos 4 perfis.
- [ ] 3.18 [CB 2.4] Criar `rotinas/processar_diarias POST` (item 2.3 da auditoria, design D7), com as 6 transições na ordem do design, idempotente e auditado com contagens. Verificar por HTTP com dados sintéticos de cada caso:
  - todas as transições são aplicadas;
  - a segunda execução retorna contagens zeradas;
  - um colaborador `Desligado` não é reativado;
  - Gestor e Colaborador são negados.
- [ ] 3.19 [CB 2.5] Estender `status_operacional GET` com a contagem pendente de cada transição da rotina diária. Verificar: os números batem com o que a rotina aplica logo em seguida.
- [x] 3.20 [CB 2.6] Criar `ciclos_avaliacao/{id}/status PATCH`, aceitando só as transições válidas e auditado. `metas POST` e `avaliacoes POST` passam a exigir ciclo `em_andamento`. Verificar por HTTP: `planejamento → concluido` é rejeitado, a sequência válida é aceita e criar uma meta em ciclo `planejamento` é rejeitado.
  - Feito e publicado em 2026-10-08. Verificado por HTTP: `planejamento → concluido` 400, sequência válida 200, meta em ciclo `planejamento` 400 e em `em_andamento` 200, volta de `fechamento` 400, ciclo inexistente 404. `avaliacoes POST` recebeu a mesma exigência, sem exercício por HTTP. Evidências em `docs/evidencias/rotinas-e-fluxos.md`.
- [x] 3.21 [CB 2.7] Criar `pesquisas_clima/{id}/encerrar POST` (RH/Admin, auditado). Verificar: depois de encerrar, `perguntas_clima/{id}/responder` recusa novas respostas.
  - Feito e publicado em 2026-10-08. Verificado por HTTP: encerrar 200, encerrar de novo 400 e responder depois de encerrar 400. Evidências em `docs/evidencias/rotinas-e-fluxos.md`.
- [x] 3.22 [CB 2.8] Em `onboarding_item/{id}/concluir`, concluir o onboarding quando não restar nenhum item pendente. Verificar por HTTP: concluir o último item muda `onboarding.status` para `concluido`, e concluir um item intermediário não muda.
  - Feito e publicado em 2026-10-08. Verificado por HTTP num onboarding de 13 itens: os itens 1 a 12 devolvem `onboarding_concluido = false`, o 13 devolve `true` e o status final é `concluido`. Evidências em `docs/evidencias/rotinas-e-fluxos.md`.
- [ ] 3.23 [CB 2.9] Em `organograma GET` e `colaboradores/aniversariantes GET` (item 2.4 da auditoria), trocar o filtro para `status != "Desligado"`. Verificar por HTTP: um colaborador com status `Ferias` aparece nos dois, e um `Desligado` não aparece.
  - **Em aberto (código publicado em 2026-10-08).** `organograma` e `aniversariantes` agora filtram `status != "Desligado"` e respondem 200. **Falta** a verificação com um colaborador em `Ferias`: nenhum endpoint define esse status e a alteração direta no banco foi bloqueada pelo ambiente. Para fechar, mudar o status de um colaborador de teste pela interface do Xano, conferir nos dois endpoints e voltar.
- [ ] 3.24 [CB 2.10] Criar `minha_equipe GET` (item 2.5 da auditoria, design D8): só Gestor, escopo do departamento, `output` explícito sem CPF, salário, dados bancários nem contato. Verificar por HTTP: o Gestor recebe só a própria equipe sem campos sensíveis, e RH, Admin e Colaborador são negados.
- [ ] 3.25 [CB 2.11] Completar o dashboard do gestor em `central_de_tarefas` com as avaliações pendentes da equipe, reaproveitando as consultas já existentes. Verificar: os campos do cenário "Dashboard do gestor" da spec aparecem na resposta para uma conta Gestor.
- [x] 3.26 [CB 2.12] Deixar `task/concluir_desligamentos_agendados.xs` com `active = false` (item 2.6 da auditoria) e documentar no cabeçalho do arquivo que ele é backlog até o upgrade do plano. Verificar: o dry-run completo não mostra operação pendente para a task.
  - Feito em 2026-10-08: o arquivo está com `active = false` e com o cabeçalho que explica o backlog. **Ressalva:** o Xano recusa publicar qualquer task neste plano ("Please upgrade to access tasks"), mesmo desligada, então a task nunca existiu no workspace e o dry-run mostra um `CREATE` que nunca será aplicado. Não há operação pendente real; o arquivo só fica como referência.
- [x] 3.27 [CB 2.13] Retenção (item 2.7 da auditoria, design D10): `documentos POST` preenche `retencao_ate` a partir de `documento_obrigatorio_regra` quando houver regra aplicável. Criar `documentos/retencao_vencida GET` (RH/Admin, só leitura). Verificar por HTTP: um documento com regra de retenção recebe a data, e a listagem mostra os vencidos sem alterar nenhum.
  - Feito e publicado em 2026-10-08. Verificado por HTTP: regra de 365 dias a partir da emissão e documento emitido em 10/01/2025 geram `retencao_ate = 2026-01-10`; `documentos/retencao_vencida` lista só leitura, sem arquivo, link, imagem nem número. Regras com faixa de idade não são avaliadas no cadastro. Evidências em `docs/evidencias/rotinas-e-fluxos.md`.
- [ ] 3.28 [CB 2.14] Backup (item 2.7 da auditoria, design D10): documentar em `docs/monitoramento.md` o procedimento (`xano workspace pull` versionado mais a exportação de dados) e executar uma restauração num workspace de teste. Verificar: o resultado da restauração fica registrado em `docs/evidencias/backup.md`.
- [ ] 3.29 [CB 2.15] Registrar no `design.md` do `conectarh.gestao` as decisões da Parte 2: Gestor decide férias, delegação por vigência, rotina diária manual, ciclo de avaliação, versionamento pelo grupo de API, rastreamento no backlog, backup e retenção. Atualizar `docs/regras-de-negocio.md` (seções de férias, ponto, delegação, avaliação, onboarding, documentos e organograma). Verificar: nenhuma regra do documento contradiz os endpoints alterados nas tarefas 2.1 a 2.13.
- [ ] 3.30 [CB 2.16] Registrar as evidências da Parte 2 em `docs/evidencias/rotinas-e-fluxos.md`. Verificar: há um cenário por tarefa de 2.1 a 2.13, sem dados pessoais.

**3. Documentação desatualizada ou contraditória (Parte 3)**

- [x] 3.31 [CB 3.1] No `tasks.md` do `conectarh.gestao`:
  - trocar SendGrid e `SENDGRID_API_KEY` por Brevo e `BREVO_API_KEY` nas tarefas 2.3, 3.2, 4.5, 5.3, 5.4, 5.5 e 5.6;
  - corrigir a nota "todos os 62 endpoints" da 2.3 para refletir a auditoria e a tarefa 1.8 desta change;
  - remover `/api/v1/` da 7.10;
  - reabrir a 4.6, com nota apontando para a tarefa 2.2 desta change.

  Verificar: `grep -i sendgrid` no arquivo não retorna nada, e a 4.6 está `[ ]`.
  - Feito em 2026-10-08 no `tasks.md` arquivado do `conectarh.gestao`: SendGrid trocado por Brevo (`grep -i sendgrid` não retorna nada), nota dos "62 endpoints" corrigida, `/api/v1/` removido da 7.10 e a 4.6 reaberta, com nota apontando para a tarefa 3.16 desta change (a numeração "2.2" do texto original é a `[CB 2.2]`).
- [x] 3.32 [CB 3.2] Marcar de novo a 4.6 do `conectarh.gestao` como concluída, com referência à tarefa 2.2 desta change, depois que a 2.2 estiver concluída. Verificar: a nota da 4.6 não descreve mais o gap de integração com os endpoints de aprovação.
  - **Bloqueada:** depende da 3.16 (delegação vigente nas decisões de férias), que ainda não foi feita. Nada a remarcar antes disso.
  - Feito em 2026-10-08, depois da 3.16: a 4.6 do `tasks.md` arquivado do `conectarh.gestao` voltou a `[x]` e a nota descreve a delegação amarrada às decisões de férias e de correção de ponto, sem o gap de integração.
- [x] 3.33 [CB 3.3] Em `docs/figma-prototipo.md`, trocar a seção "Handoff para Reflex" por "Handoff para Streamlit", com as regras da Parte 4 e o link oficial do protótipo. Verificar: `grep -i reflex` no arquivo não retorna nada, e o link abre o arquivo `fph1M5tB4rA4gqfIysSmkn`.
  - Feito em 2026-10-08: a seção virou "Handoff para Streamlit", com o link oficial e as regras de implementação (Figma antes da tela, 6 estados, alertas dentro do card, fontes, acessibilidade, frontend não é segurança). `grep -i reflex` não retorna nada. O link abrir o arquivo `fph1M5tB4rA4gqfIysSmkn` não foi aberto daqui; o Figma não estava conectado nesta sessão.
- [x] 3.34 [CB 3.4] No `design.md` do `conectarh.gestao`:
  - atualizar a contagem de endpoints para 178;
  - remover a afirmação "nenhum endpoint aceita uma requisição fora do escopo autorizado";
  - depois da tarefa 1.8, substituir essa afirmação pela garantia verificada pelo `tools/checar_endpoints.py`.

  Verificar: a contagem bate com `find xano-workspace/api -name "*.xs"`, sem contar os arquivos de grupo.
  - Feito em 2026-10-08 no `design.md` arquivado: a contagem atual é 180 endpoints (190 arquivos `.xs` menos 10 de grupo; 175 autenticados e 5 públicos). Atenção: o texto da tarefa pedia 178, mas `find` dá 180, então vale o `find`. A frase "nenhum endpoint aceita..." foi trocada pela garantia verificada por `tools/checar_endpoints.py`.
- [x] 3.35 [CB 3.5] Em `docs/domain-model.md`, remover a frase que diz que RegraContrato e RegraAplicada não têm endpoint, citando `resolver_regra` e `regras_override/aplicar`. Verificar: a seção "RegraContrato / RegraAplicada" bate com o código.
  - Feito em 2026-10-08: a seção "RegraContrato / RegraAplicada" de `docs/domain-model.md` cita `resolver_regra` e `regras_override/aplicar`, `resolver` e `simular`. A afirmação sobre ponto e documentos pendentes foi conferida no código; a de férias não, e foi omitida.
- [x] 3.36 [CB 3.6] Atualizar o README (design D11): explicar que os grupos refletem a ordem histórica de criação, incluir a tabela de domínio por grupo de API e remover "organizados por domínio". Verificar: cada um dos 10 grupos aparece na tabela com seus módulos.
  - Feito em 2026-10-08: o README explica que os grupos seguem a ordem histórica e traz a tabela com os 10 grupos e seus módulos; "organizados por domínio" foi removido.
- [x] 3.37 [CB 3.7] Criar `docs/evidencias/`, versionada, com um `README.md` de regras (sem dados pessoais, mascaramento de e-mail e token). Migrar o conteúdo não sensível de `docs/testes-integracao.md`, `docs/testes-seguranca.md` e `docs/auditoria.md`. Ajustar a tarefa 7.6 do `conectarh.gestao` para apontar para essa pasta. Verificar: `git status` mostra `docs/evidencias/` rastreada, e `grep -E "@|Bearer "` na pasta não encontra dado real.
  - Feito em 2026-10-08: `docs/evidencias/README.md` com as regras (sem dado pessoal, e-mail mascarado, token nunca). `testes-integracao.md`, `testes-seguranca.md` e `auditoria.md` estavam no `.gitignore` e foram movidos para a pasta e passaram a ser versionados, depois de uma varredura que não achou e-mail, token nem CPF reais (só 2 exemplos fictícios). As entradas no `.gitignore` foram removidas e as referências em `AGENTS.md` e `openspec/config.yaml` atualizadas. A 7.6 do `conectarh.gestao` virou a 1.6, que agora aponta para `docs/evidencias/`.
- [ ] 3.38 [CB 3.8] Remover do workspace e do Xano `function/getting_started_template/*` e `ai/agent`, que são exemplos do Xano sem uso. Verificar: `grep` não encontra referência a eles em `api/` nem em `function/conectahr/`; o dry-run com `--sync --delete` lista só esses itens, e o diff pós-pull está limpo.
  - **Parcial (2026-10-08).** Os 4 arquivos locais (`function/getting_started_template/*` e `ai/agent`) foram apagados do repositório, sem nenhuma referência em `api/`, `function/conectahr/`, `table/` ou `task/`. **Falta apagar no Xano.** A CLI não apaga um objeto isolado: só o `push --sync --delete`, e o dry-run completo, além dos 5 itens esperados (as 3 funções do template, o agente e a função de depuração `ConectaHR/depuracao_regex`), também mostra `UPDATE` na tabela `contrato_especifico` (diferença só de formatação e do default `estagio_termo_compromisso_valido?=false`, que o remoto não tem), nos 10 arquivos de grupo (o remoto guarda o token do swagger desligado; o local não) e `CREATE` da task (que o plano recusa e derruba o push). Excluir `api/**`, `task/**` e `table/**` do push é **perigoso**: o dry-run passa a apagar as 49 tabelas e os 180 endpoints. Não empurrar assim.

**4. Frontend segue o protótipo do Figma (Parte 4)**

- [x] 3.39 [CB 4.1] No `design.md` do `implementar-frontend-streamlit`, registrar a decisão "Protótipo Figma como fonte única", com o link oficial e as 7 regras do design D13 desta change. Verificar: o link e as regras aparecem numa decisão própria do documento.
  - Feito em 2026-10-08: decisão "Protótipo Figma como fonte única" no `design.md` arquivado do `implementar-frontend-streamlit`, com o link oficial e as 7 regras do D13.
- [x] 3.40 [CB 4.2] Conferir no Figma quais destas telas existem: troca de senha no primeiro acesso, logout e expiração do token, organograma, comunicados e FAQ, solicitações ao RH, pesquisa de clima, indicadores, gestão de usuários, cargos, departamentos e colaboradores, desligamento, delegações, sessões, notificações e preferências, calendário, minha equipe e dashboard do gestor. Registrar a lista das que faltam como pendência no `design.md` do frontend. Verificar: cada tela aparece com o nó do Figma ou com a marcação "a desenhar".
  - Feito em 2026-10-08, com ressalva: o Figma não estava conectado (o MCP falhou), então a conferência partiu do mapa do `design.md` (C3). A tabela no `design.md` do frontend marca cada tela com o nó do Figma ou "A desenhar"; **reconferir no Figma antes de construir cada tela.**
- [x] 3.41 [CB 4.3] Adicionar ao `tasks.md` do `implementar-frontend-streamlit` uma seção por tela da 4.2, no ciclo "conferir no Figma (desenhar antes, se faltar) → construir → integrar → testar". A troca de senha no primeiro acesso e a expiração do token entram como prioridade. Verificar: `openspec status --change implementar-frontend-streamlit` mostra as tarefas novas, e cada tela tem uma tarefa de conferência no Figma.
  - Feito em 2026-10-08: 14 tarefas novas na seção 2 desta change (2.41 a 2.54), uma por tela da lista, cada uma começando por conferir no Figma. A expiração do token e a sessão revogada (2.41) têm prioridade. O `tasks.md` arquivado do frontend ganhou a seção 15 com remissões para elas. `openspec status` não se aplica, porque a change do frontend está arquivada.
- [x] 3.42 [CB 4.4] Adicionar ao spec do `implementar-frontend-streamlit` o cenário de tela para a troca de senha no primeiro acesso e a sessão revogada (o usuário volta para "Entrar" com mensagem). Verificar: `openspec validate implementar-frontend-streamlit` passa.
  - Feito em 2026-10-08: cenários "Troca de senha no primeiro acesso" e "Sessão revogada ou expirada" na spec principal (`openspec/specs/conectahr/spec.md`) e na spec arquivada do frontend. `openspec validate --specs` passa.

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
  - **Em aberto (código publicado em 2026-10-08).** `resultados` só responde depois do encerramento (aberta: 400; encerrada: 200) e a supressão complementar considera todos os departamentos e o grupo sem departamento. **Falta** exercitar a supressão complementar com dados: é preciso pelo menos 3 respondentes em departamentos diferentes, e só há uma conta de teste utilizável. Detalhes em `docs/evidencias/lgpd.md`.
- [ ] 3.50 [novo] Servir as fontes Sora e Manrope pelo próprio aplicativo, em vez do Google Fonts (`frontend/theme.py` carrega `fonts.googleapis.com`): hoje o navegador de cada usuário consulta o Google e entrega o IP, uma transferência internacional sem necessidade (LGPD, `docs/lgpd/operadores.md`). Verificar: a aba de rede do navegador não mostra nenhuma requisição a `googleapis.com` ou `gstatic.com` e as telas mantêm a tipografia do Figma.

## 4. Adequação à LGPD [LG]

**1. Documentação e governança (Parte 1, só documentos)**

- [x] 4.1 [LG 1.1] Criar `docs/lgpd/registro-de-operacoes.md` (arts. 7, 11 e 37), com uma linha por finalidade. Colunas: finalidade, dados, titular, base legal, quem acessa, operador, prazo de retenção e medidas de segurança. O ponto de partida é o inventário do proposal. Verificar: toda tabela de `xano-workspace/table/` com dado pessoal aparece em pelo menos uma linha, conferido com uma lista das 49 tabelas anexada ao documento.
  - Criado `docs/lgpd/registro-de-operacoes.md`: 19 finalidades (F01 a F19). Conferido por script: as **49 tabelas** de `xano-workspace/table/` aparecem no documento, 12 delas marcadas "sem dado pessoal". Inclui a decisão de minimização (sem raça, sexo, religião, filiação sindical nem biometria). Bases legais e prazos ficam "a confirmar com o jurídico".
- [x] 4.2 [LG 1.2] Criar `docs/lgpd/aviso-de-privacidade.md` (arts. 6, VI, e 9), em linguagem simples, com:
  - dados coletados e por quê;
  - compartilhamento com os operadores da 1.6;
  - prazos de guarda;
  - direitos do titular e como exercê-los;
  - registro de IP e dispositivo no login e na auditoria;
  - contato do encarregado.

  Verificar: cada finalidade da 1.1 é citada no aviso.
  - Criado `docs/lgpd/aviso-de-privacidade.md`, em linguagem simples. Conferido por script: as 19 finalidades do registro são citadas. Só promete o que o sistema faz hoje: enquanto a tela "Privacidade" não existe, o pedido é feito ao encarregado, com prazo de 15 dias.
- [x] 4.3 [LG 1.3] Definir o encarregado (art. 41; Res. CD/ANPD 18/2024; sugestão: Matheus) e um e-mail de contato. Publicar no aviso da 1.2 e no `README.md`. Verificar: o mesmo contato aparece nos dois arquivos.
  - Aviso e README trazem o mesmo contato, conferido por script. **O contato é provisório:** `privacidade@conectarh.com` é um endereço sugerido, a caixa precisa ser criada, e o encarregado ainda está "a definir" (sugestão: o responsável pela documentação). O grupo disse que a definição é indiferente neste momento; confirmar antes de uso com dados reais.
- [x] 4.4 [LG 1.4] Criar `docs/lgpd/plano-de-incidentes.md` (art. 48; Res. CD/ANPD 15/2024), com:
  - quem detecta e quem avalia;
  - critérios de risco;
  - modelo de comunicação à ANPD e aos titulares em até 3 dias úteis;
  - registro interno de todo incidente;
  - ligação com os alertas de `docs/monitoramento.md`.

  Verificar: um incidente simulado (token vazado) percorre o plano do começo ao fim e fica registrado em `docs/evidencias/lgpd.md`.
  - Criado `docs/lgpd/plano-de-incidentes.md`, só com ações que o sistema já oferece. O exercício `EX-2026-001` (token vazado) percorreu o plano por HTTP: detecção pela auditoria, avaliação como risco baixo, contenção revogando a sessão e verificação de que o token vazado passou a ser recusado e o do titular continuou válido. Registrado em `docs/evidencias/lgpd.md`, sem token, e-mail ou nome.
- [x] 4.5 [LG 1.5] Criar `docs/lgpd/ripd.md` (art. 38) para dados de saúde, adolescentes aprendizes e controle de jornada, com riscos, probabilidade, impacto e medidas. Incluir os riscos residuais do `design.md`: auditoria antiga com dados completos e, se for o caso, campos `image` públicos. Verificar: cada risco aponta para uma tarefa desta change ou da `corrigir-brechas-e-alinhar-documentacao`.
  - Criado `docs/lgpd/ripd.md` para dados de saúde, adolescentes aprendizes e controle de jornada, com 18 riscos, cada um com medida, tarefa e situação (feita, planejada ou a verificar). Conferido: todas as tarefas citadas existem. **Conclusão do RIPD:** os riscos altos que ainda dependem de implementação (diagnóstico em texto livre, link público de arquivo, abertura de arquivo sem auditoria, exposição de menores e possível URL pública das imagens) devem ser concluídos antes de uso com dados reais.
- [x] 4.6 [LG 1.6] Criar `docs/lgpd/operadores.md` (arts. 33 a 39; Res. CD/ANPD 19/2024), com Xano, Brevo, hospedagem do Streamlit, GitHub e o serviço usado em `arquivo_url`. Para cada um: dados recebidos, região, termos de tratamento e mecanismo de transferência internacional. Verificar: todo domínio externo encontrado por `grep -rhoE "https://[a-z0-9.-]+" xano-workspace frontend README.md` está na lista ou é justificado como não recebedor de dados pessoais.
  - Criado `docs/lgpd/operadores.md` (Xano, Brevo, hospedagem do Streamlit, Google Fonts, GitHub, Figma e assistentes de IA). A busca por endereços externos em `xano-workspace/`, `frontend/`, `README.md` e `.streamlit/config.toml` está registrada no documento, e todo host encontrado está na lista ou justificado. **Achado:** `frontend/theme.py` carrega o Google Fonts do navegador, o que entrega o IP de cada usuário ao Google; criada a tarefa 3.50.
  - **Pendente de confirmação** (marcado "a confirmar" no documento): região do Xano, do Brevo e da hospedagem; contratos de tratamento de dados; mecanismo de transferência internacional. O protótipo do Figma tem um e-mail de pessoa real num texto e deve ser trocado por exemplo fictício.
- [x] 4.7 [LG 1.7] Criar `docs/lgpd/legitimo-interesse.md` (arts. 7, IX, e 10), com o teste de balanceamento para aniversariantes, mural de reconhecimento, pesquisa de clima e logs de segurança: finalidade, necessidade, expectativa do colaborador e salvaguardas, incluindo a oposição da 3.3. Verificar: cada linha da 1.1 com base em legítimo interesse tem seu teste.
  - Criado `docs/lgpd/legitimo-interesse.md` com um teste para cada linha do registro que usa legítimo interesse: F01 e F02, F12, F13, F14, F15, F16 e F17 (conferido por script). Todos "aprovados", alguns com condição: aniversariantes e mural dependem da opção de sair (tarefa 4.18), e a pesquisa de clima depende da tarefa 3.49.
- [x] 4.8 [LG 1.8] Integrar a LGPD aos documentos do projeto:
  - registrar no `docs/regras-de-negocio.md` que os requisitos da seção 12 (delta desta change) passam a valer;
  - acrescentar ao `AGENTS.md` três regras: campo sensível novo atualiza a 1.1 e a 1.5; dados pessoais são mascarados em auditoria e logs; serviço externo novo atualiza a 1.6;
  - no `docs/project-overview.md` e no `openspec/config.yaml`, trocar a frase genérica sobre LGPD por um link para `docs/lgpd/`.

  Verificar: `openspec validate adequacao-lgpd` passa, e cada cenário da seção 12 tem tarefa correspondente (tabela cenário → tarefa anexada ao fim deste arquivo).
  - Feito em 2026-10-08: `AGENTS.md` com as três regras pedidas (campo sensível novo, mascaramento, serviço externo novo), mais duas (repositório público e assistentes de IA); `docs/project-overview.md`, `openspec/config.yaml` e `README.md` trocaram a frase genérica por links para `docs/lgpd/`; nova seção 18 em `docs/regras-de-negocio.md`. O OpenSpec lê o `config.yaml` sem erro e `openspec validate concluir-mvp-conectarh --strict` passa. O anexo no fim deste arquivo liga os **28 cenários** de LGPD da spec principal a tarefas. A change `adequacao-lgpd` já foi arquivada, então a validação foi feita na change consolidada.

**2. Ajustes no backend (Parte 2, antes da demonstração de dezembro)**

- [x] 4.9 [LG 2.1] Mascarar dados pessoais na auditoria (design L3):
  - em `meus_dados_bancarios PATCH`, mascarar agência, conta e dígito (ex.: `banco=341; agencia=****; conta=****1234`);
  - procurar no código todas as auditorias que gravam CPF, salário, telefone, endereço ou e-mail inteiros e aplicar a mesma regra, listando os endpoints alterados no commit.

  Verificar por HTTP: alterar dados bancários e cadastro de uma conta de teste e consultar `auditoria GET`. Nenhuma linha nova contém conta, CPF, salário, telefone, endereço ou e-mail completos.
  - Publicado em 2026-10-08. A busca por `valor_anterior`/`valor_novo` em todos os endpoints achou 4 que gravavam dado pessoal inteiro: `meus_dados_bancarios` (agência, conta, dígito), `colaboradores/{id}/vinculo` (salário) e `usuarios` POST e PATCH (e-mail). Os endpoints de cadastro (`colaboradores` POST e PATCH) gravam só a ação, sem valores, e `compliance_admissao` grava só status de CTPS e eSocial; nada a mascarar. CPF, telefone e endereço nunca entraram em valores de auditoria.
  - Máscaras: agência `****`, dígito `*`, conta `****` + 4 últimos dígitos, salário `***` (e `alterado`/`inalterado` no valor novo), e-mail primeira letra + domínio. Verificado por HTTP, lendo a auditoria: `banco=341; agencia=****; conta=****3210; digito=*; tipo_conta=corrente`; `salario=*** -> salario=inalterado`; `email=q***@conectarh.test`. Dos 10 valores gravados depois da publicação, nenhum tinha conta, e-mail ou salário completos.
  - **Não exercitado ao vivo:** `usuarios` POST (o código é o mesmo padrão do PATCH, e o parser o aceitou), porque todos os colaboradores ativos já têm conta. As linhas antigas da auditoria (ids até 258) continuam com os dados completos, como previsto no RIPD.
- [ ] 4.10 [LG 2.2] Auditar a abertura de arquivos sensíveis (design L4): `acessar_arquivo_documento` em `documentos/{id}/arquivo GET`, na abertura do comprovante de ausência e na do documento de `evento_sst`. Se não houver endpoint de leitura, criar um, e retirar a URL do arquivo das listagens. Verificar por HTTP: cada abertura gera um evento com autor, recurso, registro e data, e as listagens não devolvem mais a URL.
  - **Em aberto (parcial), 2026-10-08.** Publicado: as listagens e o detalhe de documentos, de ausências e de eventos de SST deixam de devolver `arquivo_url`, `imagem_frente`, `imagem_verso`, `comprovante` e `documento_url` (`output` explícito). A abertura passa a ser só pelos endpoints `documentos/{id}/arquivo` (agora também com links assinados das imagens), `ausencias/{id}/comprovante` (novo) e `eventos_sst/{id}/documento` (novo), todos gravando `acessar_arquivo_documento`.
  - **Verificado por HTTP:** as 7 leituras não expõem mais nenhum campo de arquivo; o documento com link aberto pelo Admin gera o evento (usuário, `documento`, registro); o documento de SST aberto pelo dono e pelo Admin gera 2 eventos, e outro colaborador recebe 403; no comprovante, outro colaborador recebe 403 e o dono e o Admin recebem 404 quando não há comprovante (o escopo vem antes).
  - **Falta exercitar:** o link assinado e o evento do **comprovante** e das **imagens** do documento. Não foi possível, porque o upload de arquivo privado está quebrado (ver a tarefa 4.27): nenhuma ausência ou documento tem arquivo. O código foi aceito pelo Xano, mas `storage.sign_private_url` ainda não rodou de verdade.
- [x] 4.11 [LG 2.3] Motivo da ausência sem diagnóstico (design L5):
  - adicionar `ausencia.motivo_tipo` (enum) com push isolado do schema;
  - tornar `ausencia.motivo` privado e sem novas gravações;
  - migrar os registros existentes com uma function idempotente (`motivo_tipo = "outro"`);
  - recusar código CID na observação.

  Verificar:
  - texto livre no motivo e `J11` na observação são recusados;
  - a migração, rodada duas vezes, não altera nada na segunda;
  - por HTTP com conta Gestor: nenhum endpoint acessível a ele devolve motivo, observação ou comprovante.
  - Publicado em 2026-10-08: `ausencia.motivo_tipo` (enum, push isolado de schema só com `ADD_FIELD` e `UPDATE_FIELD`), `motivo` antigo privado e sem novas gravações, `ausencias POST` e `PATCH` recebem `motivo_tipo`, e a `observacao` recusa código CID em criar, editar, aprovar, registrar e rejeitar. As leituras trocaram `motivo` por `motivo_tipo`.
  - Verificado por HTTP: texto livre no campo antigo → 400 "Missing param: motivo_tipo"; `motivo_tipo` fora da lista → 400; observações com `J11`, `F32.1` e `j11` → 400 em todos os endpoints, e "Consulta de rotina agendada" → 200. Migração: 1ª execução migrou 9 registros e a 2ª, 0; os 9 textos antigos continuam no banco, só fora das respostas.
  - **A checagem de CID não usa regex.** O primeiro desenho (`regex_matches`) foi publicado e **deixou passar** `J11` sem erro algum: os filtros regex_* não funcionam neste workspace (ver `design.md`, C7). Foi trocada por uma checagem por palavras, validada com 10 textos (6 com CID e 4 sem falso positivo).
  - **Sobrou lixo de teste:** a função `ConectaHR/depuracao_regex` (pode ser apagada pela interface do Xano) e cerca de 9 ausências de teste da conta do colaborador 21, algumas com CID na observação gravado antes da correção.
- [ ] 4.12 [LG 2.4] Links de arquivos controlados (design L6): `documento.arquivo_url` e `evento_sst.documento_url` aceitam só o armazenamento do Xano ou hosts de `$env.ARQUIVOS_DOMINIOS_APROVADOS`. Confirmar se os campos `image` (`ausencia.comprovante`, `documento.imagem_frente`) são privados; se forem públicos, corrigir nesta tarefa e registrar na 1.5. Verificar: um link público de drive é recusado com mensagem clara, e uma URL do armazenamento do Xano é aceita.
  - **Em aberto (parcial), 2026-10-08.** Feito e publicado: `documentos POST`, `documentos/{id}` PATCH e `eventos_sst POST` só aceitam link `https` cujo host seja o da própria instância do Xano ou esteja em `$env.ARQUIVOS_DOMINIOS_APROVADOS` (lista separada por vírgula; sem a variável, vale só a instância). A comparação do host é exata, sem regex (ver `design.md`, C7).
  - **Verificado por HTTP (10 casos):** link público de drive e de Dropbox → 400 com a mensagem "Link de arquivo nao aceito. Envie o arquivo pelo sistema ou use um endereco https de um dominio aprovado..."; `http://` e `dominio-aprovado.evil.com` → 400; URL do armazenamento do Xano (inclusive com o host em maiúsculas) → 200, em criação, edição e no evento de SST; evento sem link → 200. Sem a variável de ambiente definida, a leitura vem nula e não dá erro.
  - **Falta confirmar:** se os campos de imagem (`ausencia.comprovante`, `documento.imagem_frente` e `imagem_verso`) ficam privados. O código grava com `access = "private"`, mas o upload está com defeito (tarefa 4.27) e nenhum registro tem arquivo; sem isso não há como inspecionar. O risco R1.5 do RIPD continua "a verificar". Os registros antigos (`youtube.com`, `example.com`, `w3.org`) são dados de teste e não foram alterados, porque a regra vale só na gravação.
- [x] 4.13 [LG 2.5] Códigos de acesso com hash (design L7):
  - spike: testar se o mecanismo de hash da senha funciona para um texto qualquer; senão, usar `|md5` com `$env.CODIGO_ACESSO_PEPPER` e o id do usuário; registrar o resultado no `design.md`;
  - aplicar em `auth/login`, `auth/otp/reenviar`, `auth/otp/validar`, `auth/senha/esqueci` e `auth/senha/redefinir`, num push separado, fora do horário de testes.

  Verificar:
  - `xano workspace pull --records` não mostra códigos de 6 dígitos em `otp_codigo` nem em `reset_senha_codigo`;
  - login com OTP e redefinição de senha continuam funcionando ponta a ponta;
  - o limite de 5 tentativas continua valendo.
  - **Concluída em 2026-10-08.** Feito e publicado (schema isolado, depois os 5 endpoints): função `ConectaHR/hash_codigo_acesso` (HMAC-SHA256), `otp_codigo` e `reset_senha_codigo` guardam só o hash (64 caracteres, `max:64`). Resultado do spike em `design.md`, C8.
  - **Verificado por HTTP, ponta a ponta:** login → o banco passou a guardar 64 caracteres, não 6 dígitos; código errado → 403; código certo → 200 com token e `otp_codigo` zerado; `esqueci` → hash de 64 caracteres; `redefinir` com código errado → 403 e com o código certo passou da conferência (parou em 400 "nova senha deve ser diferente da senha atual", porque o teste reutilizou a senha, que não foi alterada).
  - **Pepper definido** (`CODIGO_ACESSO_PEPPER`, pelo responsável, na interface do Xano). Verificado depois: o hash do mesmo código mudou, a quebra offline sem o segredo deixou de funcionar e um login real com código recebido por e-mail deu 200 com token; reusar o mesmo código deu 403.
- [ ] 4.14 [LG 2.6] Mínimo de pessoas nos indicadores (design L8): `indicadores GET` e `indicadores/exportar_csv GET` omitem grupos com menos de `$env.INDICADORES_MINIMO_PESSOAS` (padrão 5) e aplicam a supressão complementar do total. Verificar por HTTP: com dados de teste, um departamento com 2 pessoas não aparece na consulta nem no CSV, e o total some quando só um grupo é omitido.
  - **Em aberto (código publicado em 2026-10-08).** `ConectaHR/calcular_indicadores` omite os departamentos com menos de `$env.INDICADORES_MINIMO_PESSOAS` (padrão 5) e, com um único grupo omitido, omite `headcount` (e `omitido` no CSV); a resposta traz `minimo_pessoas`, `grupos_omitidos` e `totais_omitidos`. Verificado: o departamento com 10 aparece e os dois grupos pequenos não, nos dois endpoints. **Falta** o caso de um único grupo omitido, que os dados de teste não produzem com o mínimo 5. Para fechar: definir `INDICADORES_MINIMO_PESSOAS=3` no Xano, conferir (deve restar 1 grupo omitido e o total sumir) e voltar a variável. Os percentuais de turnover e absenteísmo não são suprimidos.
- [x] 4.15 [LG 2.7] Registrar no `design.md` (L13) e no `docs/regras-de-negocio.md` a dependência das tarefas 1.4 a 1.9 da `corrigir-brechas-e-alinhar-documentacao` e conferir o andamento delas. Verificar: os endpoints novos e alterados desta change passam no `python tools/checar_endpoints.py`.
  - Feito em 2026-10-08: decisão C9 no `design.md` e nota de dependência na seção 18 de `docs/regras-de-negocio.md`. As tarefas `[CB 1.4]` a `[CB 1.9]` (3.2 a 3.7) estão concluídas e `tools/checar_endpoints.py` passa (175 endpoints, 0 falhas).

**3. Direitos do titular (Parte 3, endpoints e telas)**

- [x] 4.16 [LG 3.1] Criar `meus_dados GET` (art. 18, II e V; design L9), só para o próprio colaborador, com `formato=json|csv`. Inclui:
  - cadastro, contrato e histórico;
  - metadados de documentos;
  - férias, ausências, ponto e banco de horas;
  - avaliações, metas e PDI;
  - solicitações e notificações;
  - sessões.

  Não inclui respostas de clima nem dados de terceiros, e grava `exportar_meus_dados` na auditoria. Verificar por HTTP: o arquivo de uma conta de teste contém todas as categorias da 1.1 que se aplicam a ela, o evento aparece na auditoria e outra conta não consegue obter esses dados.
  - Feito e publicado em 2026-10-08. Verificado por HTTP: `meus_dados` em json devolve todas as categorias, sem campo de senha nem de código; `formato=csv` devolve o resumo (cabeçalho `categoria,id,tipo,status,data`); formato inválido 400; cada exportação grava `exportar_meus_dados` (2 eventos). A rota só devolve os dados do próprio usuário (não recebe id). Respostas de clima e dados de terceiros ficam de fora, e as avaliações recebidas trazem só metadados. O CSV é um resumo; o json é a exportação completa.
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
  - **Em aberto (2026-10-08).** Não dá para responder pela CLI nem pelo repositório: `xano workspace get` e `xano platform list` não informam região nem criptografia em repouso. Precisa de quem tem acesso ao painel do Xano: (1) a região da instância, (2) se há criptografia em repouso. Registrar a resposta e a data na `docs/lgpd/operadores.md`. Sem criptografia, abrir a tarefa de criptografia de campo para CPF e conta bancária.
- [x] 4.25 [LG 4.6] Criar `docs/evidencias/README.md` com a regra de mascaramento (sem nome, CPF, e-mail ou token completo) e um checklist de revisão antes de cada commit nessa pasta. Fazer isto antes da primeira evidência desta change, mesmo estando na Parte 4. Se a tarefa 3.7 da `corrigir-brechas` já tiver criado o arquivo, só completar com o checklist. Verificar: `grep -rE "@|Bearer |[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}" docs/evidencias` não encontra dado real.
  - Feito em 2026-10-08: o `docs/evidencias/README.md` (criado na 3.37) ganhou o checklist de revisão antes de cada commit. A varredura só encontra dois exemplos fictícios.

**5. Integração final**

- [ ] 4.26 [LG 5.1] Rodar `python tools/checar_endpoints.py` e um teste HTTP por perfil (Admin, RH, Gestor e Colaborador) cobrindo `meus_dados`, as preferências, um pedido LGPD, a abertura de um arquivo e uma consulta de indicadores. Verificar: zero falhas no script, o resultado esperado em todas as chamadas e registro em `docs/evidencias/lgpd.md`.
- [ ] 4.27 [novo] Corrigir o upload de arquivos privados: `ausencias POST` (comprovante) e `documentos POST` (imagem_frente e imagem_verso) devolvem HTTP 400 "Missing param: path" (payload `comprovante.path`) quando recebem o arquivo por multipart; os campos `attachment` e `image` parecem esperar um objeto de arquivo. Nenhuma ausência ou documento existente tem arquivo, então o upload provavelmente nunca funcionou. Verificar: criar uma ausência com comprovante e um documento com imagem pelo upload, abrir pelos endpoints de acesso, conferir o link assinado e o evento de auditoria, confirmar que o arquivo fica privado (sem link público) e só então fechar a 4.10.
  - **Causa encontrada (2026-10-08): é limite do plano, não do código.** O mesmo `POST documentos` com `imagem_frente` por multipart dá 400 "Missing param: path" com o campo `image` e 403 "Not supported. Please upgrade your Xano instance." com o campo `file`; só com `arquivo_url` aprovado dá 200. Ou seja, o upload de arquivo privado não é suportado neste plano. Testado só em `documentos POST`; `ausencias POST` usa `attachment` e tem o mesmo desenho. O `documentos POST` foi restaurado e republicado como estava.
  - **Decisão pendente:** (a) fazer o upgrade do plano, ou (b) aceitar que documentos e comprovantes entram só por link de domínio aprovado (4.12) e retirar `imagem_frente`, `imagem_verso` e `comprovante` dos endpoints para não deixar um campo que sempre falha. Com (b), a 4.10 e a 4.12 podem ser fechadas sem a parte de imagens.

## 5. Integração final

- [ ] 5.1 Rodar `python tools/checar_endpoints.py` e um teste HTTP por perfil (Admin, RH, Gestor e Colaborador) cobrindo os fluxos alterados por esta change, e `openspec validate concluir-mvp-conectarh`. Verificar: zero falhas, resultado esperado em todas as chamadas e registro em `docs/evidencias/`.

## Anexo: cenários de LGPD da spec e as tarefas que os cobrem

Gerado a partir de `openspec/specs/conectahr/spec.md` (14 requisitos da proteção de dados). Todo cenário aponta para pelo menos uma tarefa deste arquivo.

| Requisito | Cenário | Tarefa(s) |
|---|---|---|
| Transparência sobre o tratamento de dados | Aviso acessível antes do login | 4.19 |
| Transparência sobre o tratamento de dados | Contato do encarregado | 4.3 |
| Transparência sobre o tratamento de dados | Nova finalidade sem aviso | 4.8 (regra no AGENTS.md) |
| Acesso e portabilidade dos próprios dados | Colaborador baixa os próprios dados | 4.16 |
| Acesso e portabilidade dos próprios dados | Sem dados de terceiros | 4.16 |
| Acesso e portabilidade dos próprios dados | Exportação de outra pessoa | 4.16 |
| Pedidos do titular de dados | Pedido criado entra na fila do RH | 4.17 |
| Pedidos do titular de dados | Pedido perto do prazo | 4.17 |
| Pedidos do titular de dados | Resposta ao titular | 4.17 |
| Oposição a tratamentos por legítimo interesse | Colaborador sai da lista de aniversariantes | 4.18, 4.19 |
| Oposição a tratamentos por legítimo interesse | Colaborador sai do mural público | 4.18, 4.19 |
| Minimização e dados sensíveis de saúde | Motivo de ausência escolhido de lista | 4.11 |
| Minimização e dados sensíveis de saúde | Diagnóstico na observação | 4.11 |
| Minimização e dados sensíveis de saúde | Gestor consulta ausência da equipe | 3.17, 4.11 |
| Acesso a arquivos sensíveis auditado | RH abre o arquivo de um documento | 4.10 |
| Dados pessoais mascarados na auditoria | Alteração de dados bancários | 4.9 |
| Dados pessoais mascarados na auditoria | Nenhum dado completo em auditoria nova | 4.9 |
| Arquivos só em armazenamento controlado | Link público de drive | 4.12 |
| Códigos de acesso protegidos | Código não legível no banco | 4.13 |
| Indicadores sem identificação de pessoas | Departamento pequeno | 4.14 |
| Indicadores sem identificação de pessoas | Dedução pela diferença | 4.14 |
| Retenção e anonimização | Limpeza de dados vencidos | 4.21 |
| Retenção e anonimização | Anonimização de desligado | 4.22 |
| Retenção e anonimização | Anonimização antes do prazo | 4.22 |
| Dados de adolescentes | Aprendiz sem responsável legal | 4.23 |
| Dados de adolescentes | Aprendiz fora da exposição pública | 4.23, 4.18 |
| Resposta a incidentes de segurança | Incidente simulado | 4.4 |
| Operadores e transferência internacional | Novo serviço externo | 4.8 (regra no AGENTS.md), 4.6 |
