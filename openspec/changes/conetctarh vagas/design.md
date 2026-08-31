## Context

O ConectaRH já tem um padrão estabelecido para dados protegidos (armazenamento privado de anexos, ex.: `documento`), para autorização por perfil (Admin/RH/Gestor/Colaborador) e para auditoria genérica de decisões (tabela `auditoria`). Este módulo é o primeiro ponto do sistema com um ator externo sem conta — o candidato visitante — e com endpoints deliberadamente públicos, além de ser o primeiro ponto que autoriza uma sessão fora do próprio ConectaRH (RH no ConectaRH Vagas). Ver proposal.md para a motivação e o escopo (somente o lado ConectaRH; o ConectaRH Vagas em si fica de fora).

## Goals / Non-Goals

**Goals:**

- Reaproveitar os padrões já existentes do ConectaRH (armazenamento privado de anexo, tabela `auditoria` para histórico de decisão, convenções de nomeação e de autorização por perfil) em vez de criar mecanismos paralelos.
- Definir um mecanismo seguro de identificação do candidato sem exigir conta ou senha.
- Deixar a API pública, a de colaborador autenticado e a de handoff de RH claras o suficiente para que o ConectaRH Vagas (futuro, fora de escopo) possa ser construído contra elas sem ambiguidade.

**Non-Goals:**

- Triagem automática de currículo, pontuação ou recomendação de candidatos.
- Agendamento de entrevistas, integração com calendário ou videoconferência.
- Integração com portais de vagas externos (LinkedIn, Gupy, etc.) ou publicação automática.
- Vincular automaticamente uma candidatura `contratado` ao pré-cadastro de colaborador — fica como ação manual do RH, possível extensão futura.
- Construir o site público de vagas em si.

## Decisions

### Identificação do candidato sem conta

Cada candidatura recebe, na criação, um `token_acompanhamento` único (UUID), gerado pelo backend e nunca reaproveitado. O candidato consulta o status enviando esse token (mais o e-mail usado na candidatura, como segundo fator) para um endpoint público de consulta. O token é devolvido na resposta da submissão e deve ser enviado também por e-mail ao candidato (mesmo mecanismo de e-mail transacional — SendGrid via outbox — já decidido para o `conectahr`; o template correspondente está sendo produzido em paralelo por outra frente de trabalho). Alternativas consideradas: exigir criação de conta para o candidato, rejeitada por adicionar fricção e por candidato não ser um ator do ConectaRH; enviar link de consulta sem token (só e-mail), rejeitada por permitir que qualquer pessoa com o e-mail do candidato veja a candidatura.

Nota de integração: o template de e-mail de notificação de candidatura (`email-templates/03-notificacao-candidatura.html`, produzido por outra frente de trabalho antes desta proposta existir) hoje usa `{{cta_url}}` genérico e `{{status_label}}`/`{{status_color}}`/`{{status_bg}}` como texto livre, além de `{{unsubscribe_url}}`/`{{preferences_url}}`, que não se aplicam a um fluxo sem conta. Quando a implementação desta capability avançar, o template precisará ser ajustado para usar `{{status_url}}` com o `token_acompanhamento` embutido, mapear os seis estados fixos definidos em `specs/recrutamento/spec.md` (`recebida`/`em_triagem`/`em_entrevista`/`em_oferta`/`contratado`/`rejeitada`) em vez de texto livre, e remover os links de descadastro/preferências.

### Autorização de RH no ConectaRH Vagas (handoff/SSO)

RH gerencia vagas e candidaturas nas telas do ConectaRH Vagas, não em telas dentro do ConectaRH — o ConectaRH entrega apenas a API que essas telas consomem. Para RH não precisar logar duas vezes, o ConectaRH emite um token de handoff de curta duração (ex.: 60 segundos, UUID assinado, uso único) quando RH clica na opção de gestão de vagas no menu principal; o link de redirecionamento para o ConectaRH Vagas carrega esse token; o ConectaRH Vagas troca o token por uma sessão válida chamando um endpoint de validação no ConectaRH, que confirma perfil (RH/Admin) e invalida o token imediatamente após o uso. Alternativas consideradas: reusar diretamente o token de sessão do ConectaRH (mesmo Bearer token usado nas outras APIs), rejeitada por expor um token de sessão de longa duração (1h, ver `conectahr`) em uma URL de redirecionamento, aumentando o risco de vazamento; implementar login separado no ConectaRH Vagas para RH, rejeitada por duplicar credenciais e contrariar o pedido de handoff sem segundo login.

### Vaga aberta visível e candidatável por colaborador, independente do tipo

Diferente da visibilidade pública (só `externa`), a listagem para colaborador autenticado retorna todas as vagas `aberta`, `interna` e `externa` — um colaborador pode se candidatar a qualquer uma. O campo `vaga.tipo` controla exclusivamente o que aparece na API pública do ConectaRH Vagas, não o que um colaborador já autenticado enxerga. Alternativa considerada: restringir colaborador a ver somente vagas `interna`, rejeitada porque o pedido original é "ver vagas da empresa" de forma geral, e não faria sentido esconder de um colaborador uma vaga que qualquer visitante externo já consegue ver.

### Reaproveitar a tabela `auditoria` para histórico de candidatura

Em vez de criar uma tabela nova só para o histórico de transições de estado da candidatura, cada mudança de estado grava um evento em `auditoria` (`recurso = "candidatura"`, `registro_id`, `valor_anterior`, `valor_novo`, `user_id` nulo quando a origem é a submissão pública). Isso reaproveita a infraestrutura de auditoria já validada no restante do sistema em vez de duplicar o conceito.

### Vagas internas x externas: quem cadastra vê o quê

O campo `vaga.tipo` define só a origem/intenção da vaga (recrutamento interno ou externo) e a visibilidade pública — não restringe o que um colaborador autenticado vê (ver decisão acima). Sem escopo adicional por departamento nesta primeira versão: qualquer colaborador ativo pode ver e se candidatar a qualquer vaga aberta. Alternativa considerada: escopar por departamento do colaborador, rejeitada por complexidade desnecessária agora; pode virar exceção futura se o RH pedir.

### Anexo de currículo

Reaproveita o mesmo padrão de `documento`: armazenamento privado (`storage.create_attachment`/`create_image` com `access = "private"`), validado por tipo e tamanho antes de aceitar. Acesso ao arquivo somente por RH, Admin ou pelo próprio candidato via token de acompanhamento (candidatura de visitante) ou pelo próprio colaborador autenticado (candidatura de colaborador) — nunca por link direto público. Currículo é obrigatório na candidatura de visitante externo e opcional na candidatura de colaborador, já que o RH já tem os dados dele.

### Endpoints públicos e superfície de ataque

Os três endpoints públicos (listar vagas externas abertas, submeter candidatura, consultar status) não exigem autenticação por definição — são o contrato com o site externo. Isso introduz uma superfície nova de abuso (spam de candidaturas, upload malicioso). Mitigação nesta mudança: mesma validação de arquivo já usada em `documento` (tipo, tamanho), limite de candidaturas ativas por e-mail por vaga (já coberto no requirement de duplicidade), e desenho dos três endpoints para não vazar informação por enumeração (a consulta de status por token inválido não revela se a candidatura existe). Rate limiting e CAPTCHA ficam como reforço futuro, a aplicar quando o site externo estiver em produção.

## Risks / Trade-offs

- [Endpoints públicos sujeitos a spam/abuso] -> Validação de arquivo, bloqueio de duplicidade por e-mail+vaga, resposta que não enumera candidaturas; rate limiting como reforço futuro.
- [Token de acompanhamento vazado expõe uma candidatura] -> Exigir e-mail como segundo fator na consulta, não incluir o token em URLs logadas publicamente, tratar o token como segredo (mesma cautela já aplicada a tokens de redefinição de senha no `conectahr`).
- [Ausência de agendamento/triagem automática pode frustrar RH que espera um ATS completo] -> Escopo definido explicitamente na proposta como gestão de vagas/candidaturas, não um ATS completo; funcionalidades adicionais ficam para mudanças futuras.
- [Token de handoff de RH interceptado autoriza acesso de gestão no ConectaRH Vagas] -> Vida curta (segundos), uso único, invalidado imediatamente após a troca, e a validação exige o perfil RH/Admin no momento da troca, não no momento da emissão.

## Migration Plan

Tabelas novas (`vaga`, `candidatura`) e endpoints novos, sem alteração em tabelas existentes do `conectahr`. Não há dados a migrar. Implantar o CRUD de vaga primeiro, depois a candidatura de colaborador autenticado, depois a submissão pública e a consulta de status, e por último o handoff de RH e a gestão de candidatura — cada fatia é demonstrável isoladamente, e a ordem prioriza o que já é usável dentro do próprio ConectaRH antes do que depende do ConectaRH Vagas existir. Rollback é remover os endpoints e desativar o(s) grupo(s) de API sem impacto no restante do sistema, já que não há dependência de outras capabilities.
