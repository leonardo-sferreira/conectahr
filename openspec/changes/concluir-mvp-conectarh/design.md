# Design

## Context

A motivação está em `proposal.md`. Esta change não tem spec própria (`skip_specs: true`): os requisitos estão em `openspec/specs/conectahr/spec.md`, gerado pelo arquivamento das quatro changes de origem. As decisões técnicas de cada tarefa continuam nos `design.md` arquivados:

| Origem | Prefixo | Pasta depois do arquivamento |
|---|---|---|
| `conectarh.gestao` | `GE` | `openspec/changes/archive/2026-10-08-conectarh.gestao/` |
| `implementar-frontend-streamlit` | `FE` | `openspec/changes/archive/2026-10-08-implementar-frontend-streamlit/` |
| `corrigir-brechas-e-alinhar-documentacao` | `CB` | `openspec/changes/archive/2026-10-08-corrigir-brechas-e-alinhar-documentacao/` |
| `adequacao-lgpd` | `LG` | `openspec/changes/archive/2026-10-08-adequacao-lgpd/` |

## Goals / Non-Goals

**Goals:**
- Um único `tasks.md` com todo o trabalho restante, sem perder a ligação com a tarefa e a decisão de origem.
- Spec principal sincronizada, que é o que o professor pediu.

**Non-Goals:**
- Reescrever tarefas ou decisões de origem. O texto é copiado como estava; só a numeração muda.

## Decisions

### C1. Como ler as referências

- `[CB 1.4]` no início de uma tarefa é a identificação da tarefa de origem. Quando um texto de origem diz "tarefa 1.4 da `corrigir-brechas`", "D1" ou "design L13", a referência aponta para a tarefa ou decisão com esse número no `tasks.md` ou no `design.md` arquivado daquela origem.
- Tarefas de origem que mandam editar o `tasks.md`, o `design.md` ou a spec de outra change passam a valer assim:
  - requisitos: editar `openspec/specs/conectahr/spec.md`, por meio de uma change nova, porque a spec principal não é editada à mão;
  - tarefas e decisões ainda abertas: editar este `tasks.md` e este `design.md`;
  - registros históricos de changes arquivadas: não são reescritos. Uma correção de texto nelas, como trocar SendGrid por Brevo, é registrada como nota neste `design.md`.
- Dependências entre tarefas continuam valendo pela origem. Exemplos: `[LG 2.7]` depende de `[CB 1.4]` a `[CB 1.9]`; `[LG 4.2]` depende de `[CB 2.4]`.

### C2. Troca de senha no primeiro acesso (decisão A1, 07/10/2026)

A troca da senha temporária é o **Passo 3 do login**, mostrado logo depois do código de acesso quando `senha_primeiro_acesso` é verdadeiro. O restante do app fica bloqueado até a troca, e "Sair" encerra a sessão. Ela não depende do Onboarding: contas de RH ou Admin sem colaborador vinculado também recebem senha temporária. Quando o Onboarding for construído, a etapa "Trocar senha temporária" só mostra "Concluído".

- **Alternativa: Onboarding completo** (nó 38:16). Rejeitada porque é muito maior e não cobre contas sem colaborador.

### C3. Mapa do protótipo Figma (`fph1M5tB4rA4gqfIysSmkn`)

Desde 07/10/2026, o protótipo está organizado em seções. Os IDs dos frames originais não mudaram.

| Seção | Nó | Telas |
|---|---|---|
| 1. Acesso e primeiro uso | 195:74 | Login Passo 1 (28:27), Passo 2 (31:6), Onboarding (38:16) |
| 2. Fluxos de senha | 193:54 | Passo 3 (193:55), Passo 3 com erro (193:241), Esqueci minha senha (193:97), Redefinir senha (193:118), Login com senha redefinida (193:139) |
| 3. Área do colaborador | 195:75 | Início (62:38), Perfil (74:50), Ponto (39:18), Férias (40:22), Documentos (41:26), Pagamento (70:46), Trajetória (64:42) |
| 4. Pendências e gestão | 195:76 | Central de Pendências (31:37), Auditoria (41:107), Regras (42:34) |
| 5. Barra superior | 197:74 | Início com notificações abertas (197:77), Início com o menu da conta aberto (197:156), cards avulsos e estado vazio |

Cada seção tem um diagrama do fluxo, com as regras do backend. No Figma, os alertas de erro e de sucesso ficam **dentro do card**, abaixo do título; o app deve seguir isso.

### C4. Vazamentos no resultado da pesquisa de clima

A agregação de `[CB 1.12]` evita correlacionar resposta e participação. Mas o endpoint de resultados ainda permite deduzir respostas de duas formas:
- **por complemento:** um único departamento suprimido pode ser calculado como o total geral menos os departamentos visíveis;
- **por diferença:** consultando antes e depois de uma resposta, com a pesquisa ainda aberta.

A correção libera os resultados só depois que a pesquisa é encerrada e aplica supressão complementar. É o mesmo critério do design L8 da `adequacao-lgpd` para os indicadores.

### C5. Resultado do spike de sessão no token (`[CB 1.1]`, 2026-10-08)

O acessor `$auth.extras.sessao_id` funciona neste workspace. Teste com dois logins da conta de teste (usuário 15):
- o token A devolveu `sessao_id = 30` e o token B, `sessao_id = 31`;
- as duas sessões existem no banco (`xano workspace pull --records`), ativas e com `user_id = 15`.

A alternativa por hash do token, prevista no D2 da `corrigir-brechas`, não é necessária.

O spike usou o próprio `auth/me` em vez de um endpoint temporário. O `sessao_id` **continua** na resposta de `auth/me`, por dois motivos: ele não é sensível (só identifica a sessão do próprio usuário) e a tela de sessões e dispositivos o usa para marcar "esta sessão".

### C6. Swagger desligado e repositório público (`[CB 1.15]`, 2026-10-08)

O repositório `leonardo-sferreira/conectahr` é **público**, então todo o código do backend e qualquer segredo commitado são visíveis a qualquer pessoa. Isso torna o swagger um risco maior do que o previsto no D9 da `corrigir-brechas`:
- um grupo de API **sem** o campo `swagger` fica com a documentação aberta, e um grupo com token só é aberto por quem o conhece (e os tokens estavam no repositório);
- `swagger = {active: false}` desliga de verdade: o `apispec` responde 404, e o campo é aceito pelo XanoScript.

Decisão: todo grupo declara `swagger = {active: false}` no repositório. Os tokens ficam só no Xano e nunca são commitados. O `tools/checar_endpoints.py` garante isso.

### C7. Filtros de regex não funcionam neste workspace (2026-10-08)

Os filtros `regex_matches`, `regex_get_first_match`, `regex_get_all_matches` e `regex_replace` são aceitos pelo parser, mas **devolvem falso, lista vazia ou nulo para qualquer padrão**, inclusive `.*J11.*`, com e sem delimitadores `/.../` e com os argumentos invertidos. Já `contains`, `replace`, `split`, `substr`, `strlen` e `to_upper` funcionam. Uma checagem que parece protegida por regex falha **em silêncio** (um padrão com CID passou como se fosse válido).

Decisão: toda validação de formato de texto é feita sem regex, por palavras: `split`, `substr` e `contains`. A detecção de código CID segue esse modelo (letra, dois dígitos e fim da palavra ou `.`), testada com 10 textos. Qualquer nova validação deve ser exercitada com um caso que deve falhar, antes de ser dada como pronta.

## Risks / Trade-offs

- [Referências cruzadas antigas podem confundir] → A regra C1 e os prefixos `[XX x.y]` mantêm cada tarefa ligada à origem.
- [Um `tasks.md` com mais de 120 tarefas fica longo] → As tarefas ficam agrupadas por origem, na mesma ordem e com os mesmos títulos de grupo.
