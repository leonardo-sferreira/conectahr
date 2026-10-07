# Design

## Context

A motivação está em `proposal.md` e os requisitos estão em `specs/conectahr/spec.md` (seção 12). Este documento registra só as restrições e as decisões que definem **como** a adequação será feita:

- **Autorização replicada endpoint a endpoint.** Não há function ou middleware compartilhado. É uma decisão do `design.md` do `conectarh.gestao`, confirmada no D1 da `corrigir-brechas-e-alinhar-documentacao`. Toda regra nova de backend desta change (mascaramento, auditoria de leitura, filtros de preferência) é replicada inline, como as guardas atuais.
- **Sem tarefas agendadas.** O plano do Xano não tem Background Tasks. A limpeza por prazo de guarda entra na rotina manual `rotinas/processar_diarias`, que **ainda não existe** (tarefa 2.4 da `corrigir-brechas`).
- **Padrões já existentes que esta change reaproveita:**
  - `preferencia_notificacao`, para guardar preferências por colaborador;
  - `pesquisa_clima.minimo_respostas` (padrão 5), para supressão de grupos pequenos;
  - `indicadores/exportar_csv`, para montar CSV;
  - `email_outbox`, para notificações;
  - a sequência "registra e depois falha", para auditar recusas;
  - `$env.BREVO_API_KEY`, para segredos fora do banco.
- **Estado atual dos dados**, conferido no código em 07/10/2026:
  - `ausencia.motivo` é texto livre;
  - `ausencia.comprovante` e `documento.imagem_frente` são campos `image`;
  - `documento.arquivo_url` e `evento_sst.documento_url` aceitam qualquer texto;
  - `user.otp_codigo` e `user.reset_senha_codigo` são texto puro;
  - `sessao` guarda `endereco_ip` e `dispositivo`;
  - `meus_dados_bancarios PATCH` grava banco, agência, conta e dígito completos em `valor_anterior` e `valor_novo`;
  - `documentos/{id}/arquivo GET` não grava auditoria.

## Goals / Non-Goals

**Goals:**
- Um único inventário (o registro de operações, `docs/lgpd/registro-de-operacoes.md`) é a fonte para todos os outros documentos de LGPD. O aviso, o RIPD, os operadores, o legítimo interesse e a retenção apontam para linhas dele, em vez de repetir conteúdo.
- Cada correção de backend é verificável por HTTP e registrada em `docs/evidencias/` sem dados pessoais.
- A Parte 4 é separável: se não couber até dezembro, as Partes 1 a 3 continuam coerentes sozinhas.

**Non-Goals:**
- Centralizar autorização ou mascaramento numa function compartilhada. Continua como débito técnico, pelo mesmo motivo do D1 da `corrigir-brechas`.
- Detectar diagnóstico em texto livre por inteligência artificial ou heurística ampla. Só o padrão de código CID é recusado.
- Criptografia de campo como trabalho padrão. Ela só entra se a 4.5 mostrar que o banco não tem criptografia em repouso.

## Decisions

### L1. `docs/lgpd/` com o registro de operações como fonte única

Todos os documentos de LGPD ficam em `docs/lgpd/`, versionados:
- `registro-de-operacoes.md`
- `aviso-de-privacidade.md`
- `plano-de-incidentes.md`
- `ripd.md`
- `operadores.md`
- `legitimo-interesse.md`
- `retencao.md`

O registro de operações tem uma linha por finalidade. Os demais documentos citam a finalidade pelo nome, para que uma mudança no registro mostre o que precisa ser revisto nos outros.

Bases legais e prazos ficam marcados **"a confirmar com o jurídico"** até haver validação. É uma análise técnica de projeto acadêmico.

O `AGENTS.md`, o `project-overview.md` e o `openspec/config.yaml` deixam de repetir a frase genérica sobre LGPD e passam a apontar para `docs/lgpd/`.

- **Alternativa: um único documento grande de LGPD.** Rejeitada. Cada documento tem um leitor diferente (colaborador, RH, ANPD, equipe técnica), e o aviso precisa ser curto e simples.

### L2. Minimização: campos que não serão criados

O sistema não terá campos de raça, sexo, religião, filiação sindical ou biometria. Nenhuma funcionalidade do escopo precisa deles: o eSocial do MVP não é transmitido, e a cota de PcD usa só o laudo.

O `AGENTS.md` passa a exigir que qualquer campo de dado sensível novo atualize antes o registro de operações e o RIPD.

### L3. Mascaramento inline na auditoria

Cada endpoint que audita um dado pessoal monta `valor_anterior` e `valor_novo` já mascarados, no mesmo `var` que hoje monta o resumo:

| Dado | Como fica na auditoria |
|---|---|
| Conta | `****` mais os 4 últimos dígitos |
| Agência e dígito | `****` |
| Banco | código do banco, sem máscara (não identifica a pessoa) |
| CPF | `***.***.***-NN` |
| Salário | `alterado`, sem valor |
| Telefone | 2 últimos dígitos |
| E-mail | primeira letra e domínio (`l***@empresa.com`) |
| Endereço | `alterado`, sem valor |

As linhas antigas da auditoria não são reescritas: a auditoria é append-only. A exposição dessas linhas fica registrada no RIPD como risco residual, e o acesso a elas continua restrito a RH e Admin.

O levantamento de quais auditorias gravam esses dados é feito por busca no código (`valor_anterior`/`valor_novo` com esses campos) e registrado na tarefa.

### L4. Auditoria de leitura de arquivos sensíveis

`documentos/{id}/arquivo GET`, a abertura do comprovante de ausência e a do documento de `evento_sst` gravam `acessar_arquivo_documento`, com `recurso` (`documento`, `ausencia` ou `evento_sst`), `registro_id` e autor. O registro é feito **depois** das checagens de permissão e **antes** de entregar o arquivo.

Recusas de acesso continuam seguindo o padrão já existente.

Se o comprovante de ausência ou o documento de SST não tiverem endpoint próprio de leitura, a tarefa cria um, no mesmo modelo do `documentos/{id}/arquivo GET`. A URL do arquivo deixa de ser devolvida nas listagens.

### L5. Motivo de ausência em lista fechada, com migração sem perda

O motivo vira um campo novo, `ausencia.motivo_tipo` (enum: `consulta`, `doenca`, `acompanhamento_familiar`, `outro`). O campo antigo, `ausencia.motivo`, não é removido (sem migração destrutiva):
- deixa de ser gravado;
- passa a ter `visibility = "private"`;
- só RH e Admin conseguem lê-lo, para consulta histórica.

Uma function idempotente, executada uma vez, preenche `motivo_tipo = "outro"` nos registros antigos.

A observação continua texto livre, até 500 caracteres. Ela é recusada quando contém um padrão de código CID (letra seguida de 2 dígitos, com decimal opcional, ex.: `J11`, `F32.1`), com uma mensagem que orienta a deixar o diagnóstico só no atestado. A tela mostra o mesmo aviso antes do envio.

- **Alternativa: apagar o texto antigo.** Rejeitada. Seria exclusão sem prazo de guarda cumprido, e os textos antigos podem ser necessários para cumprir obrigação trabalhista.
- **Alternativa: recusar qualquer termo médico na observação.** Rejeitada. Haveria falsos positivos demais. O padrão CID é objetivo e testável.

### L6. Lista de domínios aprovados para arquivos

`documento.arquivo_url` e `evento_sst.documento_url` só aceitam:
- URLs do armazenamento do próprio Xano;
- URLs cujo host esteja em `$env.ARQUIVOS_DOMINIOS_APROVADOS`, uma lista separada por vírgula, gerida como segredo de ambiente, igual ao `BREVO_API_KEY`.

A lista começa vazia. Qualquer outra URL é recusada.

A tarefa também confirma se os campos `image` (`ausencia.comprovante`, `documento.imagem_frente`) ficam em armazenamento privado ou se são acessíveis por URL pública. Se forem públicos, isso vira um risco no RIPD e uma tarefa de correção (ver Open Questions).

### L7. Códigos de acesso só com hash

`otp_codigo` e `reset_senha_codigo` passam a guardar só o hash do código. A comparação é feita pelo hash.

Um código de 6 dígitos tem só 1 milhão de combinações. Por isso, um hash simples sem segredo seria quebrado em segundos por quem tivesse uma cópia do banco. A ordem de preferência é:
1. o mesmo mecanismo de hash lento da senha (`security.check_password`), se o spike mostrar que ele funciona com um texto qualquer;
2. senão, `|md5` (o que já se confirmou funcionar neste workspace) sobre o código concatenado a um segredo fora do banco, `$env.CODIGO_ACESSO_PEPPER`, e ao id do usuário.

O e-mail continua mandando o código em claro, porque só ele sai do sistema.

Os códigos pendentes no momento do deploy deixam de valer. O impacto é aceitável, porque eles expiram em 5 a 15 minutos.

### L8. Supressão de grupos pequenos nos indicadores

`indicadores GET` e `indicadores/exportar_csv GET` omitem grupos com menos de `minimo_pessoas_indicador` pessoas. O padrão é 5, o mesmo de `pesquisa_clima.minimo_respostas`, configurável por `$env.INDICADORES_MINIMO_PESSOAS` (sem env, vale 5).

Supressão complementar: se exatamente um grupo for omitido e o total geral for exibido, o total também é omitido. É o mesmo vazamento por diferença apontado na pesquisa de clima durante a `corrigir-brechas`.

### L9. Direitos do titular sobre a estrutura existente

- **`meus_dados GET`:** só o próprio colaborador. Recebe o parâmetro `formato` (`json` ou `csv`). Reaproveita as consultas dos endpoints "meus_*" existentes e monta o CSV como o `indicadores/exportar_csv`, com uma seção por categoria. Grava `exportar_meus_dados` na auditoria. Não inclui respostas de clima nem dados pessoais de terceiros.
- **Pedido LGPD:** o enum `solicitacao_rh.tipo` ganha `privacidade_lgpd`. A tabela ganha `subtipo_lgpd` (enum dos 7 subtipos) e `prazo_resposta` (data, abertura + 15 dias). O fluxo de `atender`/`indeferir` já existente faz a resposta e a auditoria. A `central_de_tarefas` destaca os pedidos com 3 dias ou menos até o prazo.
- **Preferências:** nova tabela `preferencia_privacidade` (`colaborador_id`, `ocultar_aniversario`, `ocultar_mural`), no mesmo modelo de `preferencia_notificacao`. Quando não há linha, valem os padrões: falso para adultos e verdadeiro para menores de 18 anos (L11). `colaboradores/aniversariantes` e `mural_reconhecimento` filtram por elas.

### L10. Retenção e anonimização (Parte 4)

- **Prazos:** ficam em `docs/lgpd/retencao.md`, por categoria, marcados "a confirmar com o jurídico". Sugestão de guarda curta de 6 a 12 meses para IP e dispositivo de `sessao`, para `email_outbox` enviado e para códigos expirados.
- **Limpeza:** entra em `rotinas/processar_diarias` (pré-requisito: tarefa 2.4 da `corrigir-brechas`). Anula `endereco_ip`/`dispositivo` das sessões encerradas há mais que o prazo e o corpo e o destinatário do `email_outbox` enviado. Lista ao RH os desligados com prazo de guarda cumprido. É idempotente e auditada com contagens.
- **`colaboradores/{id}/anonimizar POST`** (RH/Admin, justificativa obrigatória):
  - substitui o nome por `Colaborador anonimizado #<id>` e anula CPF, contato, endereço, data de nascimento e dados bancários, no colaborador e no usuário vinculado;
  - desativa o usuário;
  - grava auditoria sem os valores;
  - recusa a operação se `documento.retencao_ate` de algum documento ainda estiver no futuro ou se houver bloqueio por processo.

  Nada é excluído fisicamente. Os indicadores continuam corretos porque usam ids e agregados, não nomes.

### L11. Adolescentes

A idade vem de `colaborador.data_nascimento`. Para menores de 18 anos:
- a ativação do contrato exige um documento de responsável legal aprovado;
- as preferências de privacidade nascem com `ocultar_aniversario` e `ocultar_mural` verdadeiros.

O tratamento é registrado no RIPD (art. 14 e ECA Digital).

### L12. Tela "Privacidade"

Segue as regras do frontend: a tela é desenhada no protótipo do Figma antes de ser codada. Ela reúne:
- o aviso de privacidade;
- "Baixar meus dados";
- o formulário de pedido LGPD;
- as preferências;
- o contato do encarregado.

A tela Entrar ganha um link para o aviso, legível sem login. A tela trata os 6 estados de UI. O backend restringe tudo ao próprio colaborador, e a tela não é usada como controle de acesso.

### L13. Dependência da `corrigir-brechas-e-alinhar-documentacao`

As tarefas 1.4 a 1.9 daquela change são pré-requisito de segurança desta (art. 46):
- sessão vinculada ao token;
- guarda de usuário ativo e de primeiro acesso em todos os endpoints;
- revogação de sessões.

Sem elas, um usuário desativado ou com senha temporária ainda opera parte dos endpoints que esta change protege. Por isso:
- esta change é arquivada **depois** da `corrigir-brechas`;
- os endpoints novos (`meus_dados`, `minhas_preferencias_privacidade`, `anonimizar`) já nascem com a guarda completa do D1 daquela change e passam no `tools/checar_endpoints.py`.

## Risks / Trade-offs

- [Linhas antigas da auditoria continuam com dados bancários completos] → A auditoria é append-only e não é reescrita. Fica registrado como risco residual no RIPD, com acesso restrito a RH e Admin. A anonimização (L10) também não altera a auditoria antiga, o que fica explícito no aviso.
- [O padrão CID não pega diagnóstico escrito por extenso] → Aviso na tela, motivo em lista fechada e Gestor sem acesso à observação. O texto livre que sobra só é visto por RH e Admin.
- [`md5` com segredo é mais fraco que um hash lento] → Só é usado se o spike mostrar que não há como usar o hash lento da senha. O segredo fica fora do banco. A combinação de código de vida curta (5 a 15 minutos) com limite de 5 tentativas reduz o ganho de quebrar o hash.
- [A supressão de grupos esconde dados úteis de departamentos pequenos] → É uma troca aceita. RH ainda vê o dado individual pelos fluxos operacionais, com auditoria.
- [Mudar o motivo de ausência quebra telas e integrações que enviam texto livre] → Marcado como **BREAKING** no proposal. O frontend de ausência ainda não foi construído, o que reduz o impacto.
- [A Parte 4 pode não caber até dezembro] → As tarefas da Parte 4 não são pré-requisito das Partes 1 a 3, e os documentos registram o que ficou pendente.

## Migration Plan

1. Documentos da Parte 1 (sem deploy).
2. Schema aditivo, num push isolado:
   - `ausencia.motivo_tipo`;
   - `solicitacao_rh.subtipo_lgpd` e `prazo_resposta`, e o valor `privacidade_lgpd` no enum;
   - tabela `preferencia_privacidade`.

   Primeiro o `push --dry-run`, sem operação destrutiva, depois o push e o diff do `pull`.
3. Function de migração de `ausencia.motivo_tipo`, executada uma vez e idempotente.
4. Ajustes de backend da Parte 2 e endpoints da Parte 3, um grupo de API por commit.
5. Hash dos códigos (L7) num push separado, fora do horário de testes do grupo, porque invalida os códigos pendentes.
6. Tela "Privacidade" depois do desenho no Figma.
7. Parte 4 depois da tarefa 2.4 da `corrigir-brechas`.

**Rollback:** cada grupo é um commit e um push separados. Campos e tabelas novos são aditivos e podem ficar no schema depois de um rollback de código. O hash dos códigos é revertido com o push da versão anterior dos endpoints de autenticação; os códigos pendentes expiram sozinhos.

**Ordem de arquivamento:** `conectarh.gestao` → `implementar-frontend-streamlit` → `corrigir-brechas-e-alinhar-documentacao` → esta change.

## Open Questions

- **Encarregado:** o e-mail de contato ainda precisa ser definido. A sugestão para o nome é Matheus, responsável pela documentação. A resposta só preenche um valor na tarefa 1.3.
- **Campos `image`:** os arquivos de `ausencia.comprovante` e `documento.imagem_frente` ficam em armazenamento privado do Xano? A resposta não muda a abordagem. Se forem públicos, a correção entra na tarefa 2.4 já prevista e o risco vai para o RIPD.
- **Criptografia em repouso e região do banco do Xano** (tarefa 4.5): só define se a criptografia de campo entra.
