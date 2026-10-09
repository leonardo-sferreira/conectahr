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

#### Scenario: Troca de senha no primeiro acesso
- **WHEN** um usuário com senha temporária conclui o código de acesso
- **THEN** o sistema mostra a troca de senha como etapa seguinte do login, com a confirmação da nova senha, e mantém o restante do app bloqueado até a troca
- **THEN** depois da troca, o usuário volta para "Entrar" com o aviso de que a senha foi alterada, e "Sair" encerra a sessão em qualquer momento

#### Scenario: Sessão revogada ou expirada
- **WHEN** o backend recusa uma requisição com a sessão encerrada, expirada ou revogada (por exemplo, usuário desativado ou "encerrar outras sessões")
- **THEN** o frontend descarta o token, volta o usuário para "Entrar" e mostra uma mensagem de que a sessão terminou, sem mostrar dados da sessão anterior

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

### Requirement: Validação dos campos antes do envio
O frontend SHALL validar e normalizar cada campo de entrada antes de chamar o backend, aplicando as mesmas regras que o backend já aplica, e SHALL recusar no próprio cliente, com mensagem em português, toda entrada que o backend com certeza recusaria. Na tela "Entrar" as regras são:
- e-mail: espaços nas pontas removidos, letras minúsculas, até 254 caracteres, só ASCII e formato `nome@dominio.tld`;
- senha do login: de 8 a 64 caracteres e não pode ser só espaços;
- código de acesso e código de redefinição: exatamente 6 dígitos numéricos;
- nova senha: de 8 a 64 caracteres e igual à confirmação.

A validação no cliente é só conveniência: o backend continua validando e recusando as mesmas entradas, conforme o requisito "Frontend não decide autorização".

#### Scenario: E-mail com emoji, acento ou caractere especial
- **WHEN** o usuário informa um e-mail com emoji (ex.: `teste😀@empresa.com`) ou acento (ex.: `joão@empresa.com`)
- **THEN** o sistema não envia a requisição e informa que o e-mail não pode ter acentos, emojis ou outros caracteres especiais

#### Scenario: E-mail fora do formato
- **WHEN** o usuário informa um e-mail sem `@`, com HTML/script (ex.: `<script>alert(1)</script>`) ou com SQL (ex.: `' OR '1'='1`)
- **THEN** o sistema não envia a requisição e pede um e-mail no formato `nome@empresa.com`

#### Scenario: Campo só com espaços
- **WHEN** o usuário preenche e-mail, senha, código ou nova senha só com espaços
- **THEN** o sistema trata o campo como vazio e pede o preenchimento, sem enviar a requisição

#### Scenario: E-mail com espaços nas pontas ou maiúsculas
- **WHEN** o usuário informa um e-mail válido com espaços nas pontas ou letras maiúsculas
- **THEN** o sistema remove os espaços, converte para minúsculas, envia o e-mail normalizado e o exibe assim nas etapas seguintes

#### Scenario: Senha fora do tamanho
- **WHEN** a senha do login tem menos de 8 caracteres (ex.: só 3 emojis)
- **THEN** o sistema informa que a senha tem entre 8 e 64 caracteres e não envia a tentativa, que contaria para o bloqueio por senha errada

#### Scenario: Texto acima do limite do campo
- **WHEN** o usuário cola num campo um texto maior que o limite (254 para e-mail, 64 para senha, 6 para código)
- **THEN** o campo não aceita o conteúdo colado e, ao enviar, o sistema informa que o campo está vazio

#### Scenario: Código de acesso sem formato
- **WHEN** o usuário digita um código com letras, emoji, espaço, HTML ou menos de 6 dígitos
- **THEN** o sistema informa que o código tem exatamente 6 números e não envia a requisição, preservando as 5 tentativas de validação do código

#### Scenario: Confirmação de senha diferente
- **WHEN** a nova senha e a confirmação não coincidem
- **THEN** o sistema informa que a confirmação não corresponde à nova senha, sem enviar a requisição

#### Scenario: Mensagem técnica do backend
- **WHEN** o backend recusa uma entrada com mensagem técnica em inglês (ex.: `Invalid email format.`, `Missing param: ...`, `Input does not meet minimum length requirement of 8 characters`)
- **THEN** o sistema exibe a mensagem equivalente em português

#### Scenario: Falha de conexão com o servidor
- **WHEN** a chamada ao backend falha por rede, TLS ou tempo esgotado
- **THEN** o sistema exibe uma mensagem amigável pedindo para tentar de novo, e o detalhe técnico vai só para o log do servidor

#### Scenario: Reenviar o código de redefinição
- **WHEN** o usuário está na tela de redefinir senha e pede "Reenviar código"
- **THEN** o sistema envia um novo código, que substitui o anterior, só se tiver passado pelo menos 60 segundos desde o último envio; antes disso, pede para aguardar, e o backend também ignora o pedido, sem enviar e-mail

#### Scenario: Senha redefinida com sucesso
- **WHEN** o usuário redefine a senha com um código válido
- **THEN** o sistema volta para a tela de login exibindo a confirmação de sucesso, e o login com a nova senha funciona mesmo que a conta estivesse bloqueada por senhas erradas

#### Scenario: Dado digitado exibido na tela
- **WHEN** a tela exibe um valor informado pelo usuário (ex.: o e-mail no passo do código de acesso)
- **THEN** o valor é exibido como texto escapado, sem ser interpretado como HTML

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
