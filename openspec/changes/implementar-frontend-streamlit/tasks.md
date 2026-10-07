## 1. Fundação (já concluída nesta sessão)

- [x] 1.1 Configurar ambiente Streamlit (venv, `requirements.txt`, `.streamlit/config.toml` com tema grafite+âmbar); verificado com `streamlit run` limpo e `streamlit.testing.v1.AppTest` sem exceção.
- [x] 1.2 Criar `frontend/theme.py` com os tokens de cor/tipografia extraídos do Figma (nós 28:27/31:6) e as funções `inject_base_styles`/`render_header`/`card_marker`/`render_card_title`, usando `st.html()` (nunca `st.markdown(unsafe_allow_html=True)`); verificado visualmente contra o screenshot do Figma.
- [x] 1.3 Criar `frontend/api_client.py` com `ApiError`/`_post` genéricos e as funções de autenticação (`login`, `validar_otp`, `reenviar_otp`, `esqueci_senha`, `redefinir_senha`).
- [x] 1.4 Implementar a tela de Login + Código de Acesso + Esqueci minha senha/Redefinir senha, integradas de verdade com `auth/login`, `auth/otp/validar`, `auth/otp/reenviar`, `auth/senha/esqueci`, `auth/senha/redefinir`; verificado com conta real (`leonardo.2503461@aluno.impacta.edu.br`, perfil Admin) recebendo o código por e-mail via Brevo.

- [x] 1.5 Legibilidade da tela Entrar. Três ajustes no `theme.py`:
  - placeholder legível nos campos;
  - borda visível em volta do grupo de campos (`st.form`);
  - campo de senha sem a moldura grafite herdada do tema escuro.

  Verificado em 2026-10-06 por screenshot headless e medição no DOM:
  - placeholder de `rgba(236,234,228,0.6)` para `#6B7280`;
  - borda do form de `rgba(236,234,228,0.2)` para `#C9C7C1`;
  - moldura do campo de `#1F222A` para `MARFIM` com borda `BORDA`.

  Pendente: incluir `PLACEHOLDER` e `BORDA_FORM` na página "Design System" do Figma (ver `design.md`).
- [x] 1.6 QA dos 7 campos da tela Entrar (login, código de acesso, esqueci minha senha, redefinir senha). As entradas testadas foram emoji, acento, HTML/`<script>`, SQL, só espaços, 5.000 caracteres, formato inválido e senha/código fora do tamanho. Nenhuma derrubou o app. Os 8 problemas encontrados foram corrigidos, em ordem de gravidade, conforme o requisito "Validação dos campos antes do envio":
  1. (alta) código com letras/emoji gastava as tentativas do OTP → validação de 6 dígitos no cliente;
  2. mensagens do Xano em inglês → traduzidas no `api_client`;
  3. campo só com espaços chegava ao backend → tratado como vazio;
  4. falha de conexão mostrava a exceção técnica → mensagem amigável, detalhe só no log;
  5. campos sem limite de tamanho → `max_chars` (254/64/6);
  6. e-mail com acento recusado sem explicação → mensagem específica;
  7. e-mail exibido sem normalizar → `trim`+`lower` antes do envio;
  8. e-mail no subtítulo sem escape de HTML → `html.escape` em `render_header`/`render_card_title`.

  Verificado em 2026-10-06:
  - funções de `validacao.py` e a tradução conferidas isoladamente;
  - os 30 casos repetidos no navegador real (Playwright), todos com mensagem em português e sem envio indevido, incluindo 5 códigos inválidos sem gastar tentativa;
  - falha de conexão simulada exibiu a mensagem amigável;
  - colagem de texto acima do limite: o campo recusa o conteúdo.

## 2. Navegação multi-página e guarda de sessão

- [ ] 2.1 Migrar `frontend/app.py` para `st.Page`/`st.navigation`, mantendo o fluxo de autenticação (login/OTP/esqueci senha) como um wizard interno de estados dentro de uma única página "Entrar", conforme decidido em `design.md`; verificar que sem sessão só a página de autenticação é acessível.
- [ ] 2.2 Implementar a função de guarda de sessão (redireciona para "Entrar" se `st.session_state.token` ausente) e o filtro de páginas por perfil (Auditoria/Regras só para RH/ADMIN); verificar com uma conta de cada perfil que a lista de páginas visível muda corretamente.

## 3. Início

- [x] 3.1 Buscar o node "Início" no Figma via MCP e conferir elementos/tokens antes de codar; construir a UI (saudação, atalhos principais) reaproveitando `theme.py`; verificar contra o screenshot do node. Feito a partir do nó 62:38 (sidebar, barra superior, saudação, 4 indicadores, comunicados, aniversariantes, FAQ); conferido por screenshot headless com dados simulados e medição das posições no DOM (sidebar 16px/208px, topo em 40px). "Dias de férias" mostra "—": não existe endpoint de saldo de férias no backend.
- [ ] 3.2 Integrar com `central_de_tarefas` (seção de pendências pessoais); verificar que os campos batem com a resposta real do endpoint.
- [ ] 3.3 Testar os estados carregando/vazio/erro da tela e os diferentes contextos (com e sem colaborador vinculado, com e sem pendências).

## 4. Central de Pendências

- [ ] 4.1 Buscar o node "Central de Pendências" no Figma (inclui o componente "trilha de conexão") e conferir antes de codar; construir a UI, incluindo o componente de trilha reutilizável em `theme.py` se ainda não existir.
- [ ] 4.2 Integrar com `central_de_tarefas` (filas de férias/documentos/desligamentos pendentes) e com o dashboard do gestor quando aplicável.
- [ ] 4.3 Testar o escopo por perfil (RH/ADMIN vê tudo, Gestor só o próprio departamento, Colaborador não vê a fila) e os 6 estados de UI.

## 5. Perfil

- [ ] 5.1 Buscar o node "Perfil" no Figma e conferir antes de codar; construir a UI (dados pessoais + dados bancários).
- [ ] 5.2 Integrar com `meu_perfil_colaborador` (GET/PATCH) e `meus_dados_bancarios` (PATCH).
- [ ] 5.3 Testar que dados bancários só aparecem para o próprio colaborador (nunca para Gestor, mesmo por engano de UI — o backend já bloqueia, mas a tela não deve nem tentar mostrar).

## 6. Onboarding

- [ ] 6.1 Buscar o node "Onboarding" no Figma e conferir antes de codar; construir o checklist por categoria com responsável e percentual concluído.
- [ ] 6.2 Integrar com `colaboradores/{id}/onboarding` (GET) e `onboarding_item/{id}/concluir` (POST); testar autorização por item (responsável rh/colaborador/gestor) e os 6 estados de UI.

## 7. Ponto

- [ ] 7.1 Buscar o node "Ponto" no Figma e conferir antes de codar; construir marcação, espelho do dia/período e solicitação de correção, incluindo o aviso de "controle interno experimental".
- [ ] 7.2 Integrar com `ponto/marcar`, `ponto/{id}/solicitar_correcao`, `correcoes_ponto` (aprovar/rejeitar, visível a RH/ADMIN/Gestor) e consulta de banco de horas.
- [ ] 7.3 Testar a ordem estrita de marcação (entrada → intervalo → saída) e a aprovação de correção restrita ao Gestor do departamento certo.

## 8. Férias

- [ ] 8.1 Buscar o node "Férias" no Figma e conferir antes de codar — se houver um calendário visual interativo além de lista/tabela, registrar em `design.md` (seção "Limitações identificadas") antes de prosseguir, conforme o processo decidido lá.
- [ ] 8.2 Construir a UI de solicitação de férias/ausência e a verificação de conflito (informativa).
- [ ] 8.3 Integrar com `ferias/solicitacoes`, `ferias/{id}/aprovar-rejeitar-cancelar`, `ferias/{id}/verificar_conflito` e o equivalente de ausências.
- [ ] 8.4 Testar bloqueio de segunda solicitação pendente, exigência de senha já trocada, e os 6 estados de UI.

## 9. Documentos

- [ ] 9.1 Buscar o node "Documentos" no Figma e conferir antes de codar; construir upload/listagem por status.
- [ ] 9.2 Integrar com `documentos` (POST/GET/PATCH), `documentos/{id}/aprovar-rejeitar-arquivar`, `pendencias_documento` e a consulta de documentos obrigatórios pendentes.
- [ ] 9.3 Testar que não existe opção de exclusão física (só arquivamento) e que o acesso ao arquivo respeita dono/RH/ADMIN.

## 10. Pagamento

- [ ] 10.1 Buscar o node "Pagamento" no Figma e conferir antes de codar; construir a aba de holerite/informe de rendimentos, reaproveitando a integração de Documentos (mesmo módulo de backend).
- [ ] 10.2 Testar que holerite/informe de rendimentos aparece só para o colaborador dono (consulta) e que o upload continua restrito ao RH.

## 11. Trajetória (avaliação, metas, PDI, plano de carreira)

- [ ] 11.1 Buscar o node "Trajetória" no Figma e conferir antes de codar; construir avaliação (respostas por competência, contestação), metas com check-in, PDI e o painel de plano de carreira.
- [ ] 11.2 Integrar com `avaliacoes`, `avaliacoes/{id}/respostas`, `avaliacoes/{id}/enviar-contestar`, `metas`, `metas/{id}/checkin`, `pdi`, `reconhecimentos` e `colaboradores/{id}/plano_carreira`.
- [ ] 11.3 Testar a visibilidade automática de reconhecimento (público/privado por relação gestor-colaborador) e confirmar que a tela nunca oferece uma ação de "promover" automaticamente.

## 12. Auditoria

- [ ] 12.1 Buscar o node "Auditoria" no Figma e conferir antes de codar; construir o painel de consulta com os filtros disponíveis (recurso, registro, usuário, ação, resultado).
- [ ] 12.2 Integrar com `GET auditoria`; testar que a tela é inacessível (via guarda de perfil) para quem não é RH/ADMIN.

## 13. Regras

- [ ] 13.1 Buscar o node "Regras" no Figma e conferir antes de codar; construir a gestão de instrumentos normativos e regras de override, incluindo a tela de simulação de impacto antes de publicar.
- [ ] 13.2 Integrar com `instrumentos_normativos` (CRUD + aprovação), `regras_override` (CRUD + aprovação), `regras_override/resolver`, `regras_override/aplicar` e `regras_override/{id}/simular`.
- [ ] 13.3 Testar o bloqueio de autoaprovação, a exigência de número Mediador/MTE para instrumentos coletivos, e o bloqueio de "aplicar" quando há conflito não resolvido.

## 14. Acessibilidade e revisão final

- [ ] 14.1 Revisar todas as telas construídas contra os critérios de acessibilidade do design system do Figma (contraste WCAG AA, foco visível, navegação por teclado, cor nunca como único indicador de estado); verificar navegando o app inteiro só com teclado.
- [ ] 14.2 Conferir que toda tela trata os 6 estados de UI obrigatórios (carregando, vazio, sucesso, erro, bloqueado, permissão negada) de forma consistente entre si; verificar por inspeção cruzada das telas já implementadas.
- [ ] 14.3 Atualizar `docs/regras-de-negocio.md` e `AGENTS.md` com qualquer padrão de frontend que se tornou definitivo nesta change (ex.: proibição de `st.markdown(unsafe_allow_html=True)` para HTML/CSS, uso de `st.Page`/`st.navigation`).
