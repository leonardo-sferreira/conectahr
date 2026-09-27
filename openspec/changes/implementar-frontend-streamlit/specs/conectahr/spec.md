## Purpose

Define o comportamento observável do frontend Streamlit do ConectaRH: quais telas devem existir, com que fidelidade ao design system do protótipo Figma, e quais estados/garantias de acessibilidade toda tela precisa oferecer.

## ADDED Requirements

### Requirement: Cobertura das telas do protótipo Figma
O frontend SHALL implementar uma tela ou fluxo correspondente para cada tela navegável definida no protótipo Figma "ConectaRH — Protótipo" (`fph1M5tB4rA4gqfIysSmkn`), cobrindo o conteúdo e a hierarquia de informação documentados ali para cada rota.

#### Scenario: Login e código de acesso
- **WHEN** um usuário acessa o app sem sessão ativa
- **THEN** o sistema apresenta a tela de login (e-mail/senha) e, após senha válida, a tela de código de acesso (OTP de 6 dígitos), na sequência definida no protótipo

#### Scenario: Início
- **WHEN** um usuário autenticado acessa o app
- **THEN** o sistema apresenta uma tela de início/dashboard com saudação e atalhos principais

#### Scenario: Central de pendências
- **WHEN** um usuário autenticado navega para a central de pendências
- **THEN** o sistema apresenta a fila de aprovação aplicável ao perfil do usuário (RH/ADMIN vê todas; Gestor vê só o próprio departamento; Colaborador não vê a fila administrativa)

#### Scenario: Perfil
- **WHEN** um usuário autenticado navega para o próprio perfil
- **THEN** o sistema apresenta os dados pessoais e, quando aplicável, a edição dos próprios dados bancários

#### Scenario: Pagamento
- **WHEN** um colaborador navega para a área de pagamento
- **THEN** o sistema apresenta os documentos do tipo holerite/informe de rendimentos anexados pelo RH, disponíveis para consulta e download

#### Scenario: Onboarding
- **WHEN** um usuário autenticado com onboarding em andamento acessa a tela de onboarding
- **THEN** o sistema apresenta o checklist por categoria com responsável e percentual concluído

#### Scenario: Ponto
- **WHEN** um colaborador acessa a tela de ponto
- **THEN** o sistema apresenta a marcação do dia, o espelho de ponto e a opção de solicitar correção, incluindo o aviso de que o registro é controle interno experimental

#### Scenario: Férias
- **WHEN** um usuário autenticado acessa a tela de férias/ausências
- **THEN** o sistema apresenta a solicitação de férias/ausência e, para RH/ADMIN, a fila de decisão

#### Scenario: Documentos
- **WHEN** um usuário autenticado acessa a tela de documentos
- **THEN** o sistema apresenta o envio e a listagem de documentos por status, incluindo pendências abertas

#### Scenario: Auditoria
- **WHEN** um usuário com perfil RH ou ADMIN acessa a tela de auditoria
- **THEN** o sistema apresenta a consulta à trilha de auditoria com os filtros disponíveis; um usuário com outro perfil não vê essa tela

#### Scenario: Regras
- **WHEN** um usuário com perfil RH ou ADMIN acessa a tela de regras
- **THEN** o sistema apresenta a gestão de instrumentos normativos e regras de override, incluindo a simulação de impacto antes de publicar

#### Scenario: Trajetória
- **WHEN** um usuário autenticado acessa a tela de trajetória
- **THEN** o sistema apresenta avaliação, metas, PDI e o painel de plano de carreira (nível atual, próximo nível, lacunas), sem nenhuma ação de promoção automática

### Requirement: Fidelidade ao design system do Figma
O frontend SHALL aplicar os tokens de cor e tipografia definidos na página "Design System" do protótipo Figma (paleta grafite `#16181D` + âmbar `#F5A623` como acento único; tipografia Sora para títulos e Manrope para texto corrente) de forma consistente em todas as telas, e SHALL reutilizar os componentes de assinatura do protótipo ("crachá de acesso", "trilha de conexão") onde o protótipo os emprega, em vez de criar um padrão visual alternativo por tela.

#### Scenario: Divergência de cor ou tipografia
- **WHEN** uma tela implementada usa uma cor ou fonte fora dos tokens do design system
- **THEN** isso é tratado como um defeito da implementação, não como uma variação aceitável

### Requirement: Estados de UI obrigatórios
Cada tela do frontend SHALL tratar explicitamente os 6 estados exigidos pelo design system do protótipo: carregando, vazio, sucesso, erro, bloqueado e permissão negada.

#### Scenario: Requisição em andamento
- **WHEN** uma tela está aguardando resposta de um endpoint do backend
- **THEN** o sistema comunica visualmente o estado de carregamento em vez de apresentar uma tela em branco ou travada

#### Scenario: Ausência de dados
- **WHEN** uma listagem não tem nenhum item para exibir
- **THEN** o sistema apresenta um estado vazio explicativo, não uma tabela ou lista em branco sem contexto

#### Scenario: Erro do backend
- **WHEN** uma chamada ao backend retorna erro
- **THEN** o sistema apresenta a mensagem de erro retornada pela API de forma compreensível, sem expor detalhes técnicos internos (stack trace, payload bruto)

#### Scenario: Acesso negado por perfil
- **WHEN** um usuário autenticado sem o perfil necessário tenta acessar uma tela restrita
- **THEN** o sistema apresenta um estado de permissão negada em vez de tentar renderizar a tela com dados incompletos

### Requirement: Acessibilidade
O frontend SHALL seguir os critérios de acessibilidade documentados na página "Design System" do protótipo: contraste mínimo WCAG AA entre texto e fundo, foco visível em todo elemento navegável por teclado, navegação completa por teclado nos fluxos principais, e nenhuma informação transmitida exclusivamente por cor.

#### Scenario: Navegação por teclado
- **WHEN** um usuário navega o formulário de login usando somente o teclado
- **THEN** todos os campos e botões são alcançáveis em ordem lógica, com indicação visual clara de qual elemento está focado

#### Scenario: Informação de estado sem depender só de cor
- **WHEN** o sistema indica o status de um item (ex.: pendente/aprovado/rejeitado)
- **THEN** o status é indicado por texto ou ícone além da cor, para permanecer compreensível a usuários com daltonismo

### Requirement: Frontend não decide autorização
O frontend SHALL tratar toda decisão de autorização (o que um perfil pode ver ou fazer) como resultado vindo do backend, nunca como lógica decidida ou replicada no cliente — consistente com a arquitetura já estabelecida em `AGENTS.md`.

#### Scenario: Ocultação de tela restrita
- **WHEN** o app decide esconder ou desabilitar uma ação restrita a determinado perfil
- **THEN** essa decisão reflete o perfil e os dados retornados pelo backend na sessão autenticada, e o backend também rejeita a mesma ação caso seja tentada diretamente pela API
