# AGENTS.md — ConectaRH

Este é o **arquivo único de instruções** para agentes de IA (Codex, Gemini CLI, Claude Code e
outros) que trabalham neste repositório. Ele define **como** trabalhar. Os arquivos
`CLAUDE.md` e `GEMINI.md` só apontam para cá, e os `AGENTS.md` de `frontend/` e
`xano-workspace/` trazem apenas o que é específico de cada pasta, sem repetir estas regras.

Para entender **o que é** o projeto, leia primeiro:

- [`docs/project-overview.md`](docs/project-overview.md) — visão geral, objetivo, escopo.
- [`docs/domain-model.md`](docs/domain-model.md) — conceitos do domínio e relacionamentos.
- [`docs/regras-de-negocio.md`](docs/regras-de-negocio.md) — regras já implementadas, mapeadas do código.
- [`openspec/config.yaml`](openspec/config.yaml) — contexto e regras que o OpenSpec injeta em cada workflow.

## 1. Visão e perfis

ConectaRH é uma plataforma de RH que centraliza o ciclo de vida do colaborador: admissão,
jornada e ponto, documentos, férias e ausências, avaliação e desenvolvimento, e desligamento,
com decisões auditáveis e um motor de regras trabalhistas (norma legal, instrumento coletivo e
exceção individual). É um trabalho acadêmico, desenvolvido em grupo.

Quatro perfis, com escopo diferente:

| Perfil | Escopo |
|---|---|
| **Admin** | Acesso administrativo amplo, equivalente a RH na maioria das ações |
| **RH** | Cadastros, documentos, regras, decisões de férias, ausências, desligamentos e solicitações |
| **Gestor** | Só o próprio departamento (`departamento.gestor_colaborador_id`): aprova férias e correções de ponto da equipe, acompanha metas e avaliações |
| **Colaborador** | Só os próprios dados: ponto, férias, ausências, documentos, avaliações, PDI |

## 2. Fora de escopo

- **ConectaRH Vagas** (recrutamento e candidatos): proposta retirada deste repositório.
- Integração real com eSocial, CTPS Digital e Sistema Mediador/MTE: o sistema só registra os
  dados e prazos.
- Upload de arquivo privado (imagem e comprovante): não é suportado no plano atual do Xano; os
  documentos entram por link de domínio aprovado.
- Tarefas agendadas (Background Tasks): o plano do Xano não as inclui; as rotinas são
  acionadas manualmente por RH/Admin.
- Parecer jurídico: bases legais e prazos de guarda são sugestões, "a confirmar com o jurídico".

## 3. Stack e pastas

Respeitar a stack definida. Não introduzir tecnologia alternativa sem justificativa explícita
no `design.md` da change.

- **Backend:** Xano com XanoScript, em `xano-workspace/` (`table/`, `function/`, `api/` com 10
  grupos, `task/`). Workspace 147338; sempre usar o perfil `-p ConectaRH` da CLI.
- **Frontend:** Streamlit, em `frontend/` (tema e componentes em `theme.py`, cliente de API em
  `api_client.py`).
- **E-mail transacional:** Brevo (variável de ambiente `BREVO_API_KEY` no Xano).
- **Design:** Figma, arquivo `fph1M5tB4rA4gqfIysSmkn`.
- **Planejamento:** OpenSpec, em `openspec/` (`specs/` consolida o comportamento; `changes/`
  traz o plano em andamento; `changes/archive/` o histórico).
- **Documentação:** `docs/` (regras de negócio, LGPD em `docs/lgpd/`, evidências em
  `docs/evidencias/`). **Ferramentas:** `tools/checar_endpoints.py`.

O backend é responsável por regras de negócio, autorização e persistência. O frontend nunca é
mecanismo de segurança. Seguir os padrões já existentes no código (guarda de acesso replicada
em cada endpoint, escopo por departamento, append-only para banco de horas e check-ins) em vez
de criar um padrão novo para o mesmo problema.

## 4. Fluxo de trabalho

O projeto é desenvolvido com OpenSpec: **Explore → Propose → Review → Apply → Archive**.
Mudança funcional relevante é especificada (proposal, specs, design e tasks) antes de ser
implementada; mudança só de documentação pode declarar `skip_specs: true`.

1. **Antes de mexer:** consultar os documentos de contexto acima e o `design.md` da change.
2. **Branch:** `feature/CON-XX-descricao`, uma por tarefa ou grupo de tarefas. `CON-XX` é o
   número do card do Jira. Enquanto não houver card, usar a tarefa do `tasks.md` no lugar
   (ex.: `feature/lgpd-backend-parte2`).
3. **Commit:** `CON-XX descrição (tarefa)`; sem card, citar só a tarefa de `tasks.md` (ex.: `4.12`).
   A mensagem descreve o que mudou e por quê.
4. **Pull Request:** integra em `master`, com `CON-XX` no título e pelo menos uma revisão do
   grupo. **Nunca** fazer push direto no `master`.
5. **Sem atribuição de IA:** commits e descrições de PR não levam "Co-Authored-By" nem rodapé de
   ferramenta de IA.
6. **Arquivar:** só quando toda a spec e a documentação da change estiverem fechadas.

Regras de negócio novas ou alteradas por uma change entram em `docs/regras-de-negocio.md`
depois da implementação (ou ficam marcadas para revisão). Não modificar funcionalidade fora do
escopo da change sem justificativa na proposta ou no design.

## 5. Checklist de endpoint do Xano

Todo endpoint autenticado (`auth = "user"`) precisa, **nesta ordem e antes da primeira escrita
no banco**:

1. carregar o usuário com `db.get user` pelo `$auth.id`;
2. `precondition ($usuario.ativo)`;
3. `precondition ($usuario.senha_primeiro_acesso == false)`, exceto nas rotas de troca de senha,
   `auth/me`, logout e sessões;
4. validar a sessão do token: `db.get sessao` pelo `$auth.extras.sessao_id` e `precondition`
   de sessão ativa, do próprio usuário, não revogada e não expirada.

Em seguida:

5. aplicar a **autorização por perfil e escopo** no backend (perfil normalizado com
   `|trim|to_upper`; Gestor só pelo próprio departamento; ninguém decide uma solicitação em
   que é o próprio colaborador);
6. **auditar** toda ação de escrita (`db.add auditoria`) com autor, ação, recurso, registro e
   resultado, sem senha, token, código nem dado pessoal inteiro (mascarar);
7. devolver só o necessário: `output` explícito em consultas com dado sensível; campos
   privados continuam privados;
8. mensagens de erro em português, sem revelar se uma conta existe;
9. antes de publicar, rodar `python tools/checar_endpoints.py` (confere os itens 1 a 4) e
   testar por HTTP um caso que deve passar e um que deve falhar.

O detalhe dos padrões de XanoScript está em [`xano-workspace/AGENTS.md`](xano-workspace/AGENTS.md).

## 6. Frontend e Figma

O frontend é construído **só** a partir do protótipo oficial:
<https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn> (mapa de seções e nós no `design.md`,
decisão C3, da change `concluir-mvp-conectarh`). Regras:

1. ler o nó no Figma, pelo MCP ou pelo Dev Mode, antes de codar;
2. não criar nada visual fora dos tokens e componentes de `frontend/theme.py`;
3. tela inexistente no Figma é desenhada primeiro;
4. textos idênticos aos do protótipo;
5. os 6 estados de UI (carregando, vazio, sucesso, erro, bloqueado, permissão negada) seguem o Figma;
6. o PR traz o link do nó e os prints lado a lado;
7. o menu por perfil é só conveniência: a autorização é do backend.

Como rodar e o padrão do cliente de API: [`frontend/AGENTS.md`](frontend/AGENTS.md).

## 7. Segredos e dados pessoais

- **O repositório é público.** Nenhum segredo, token, senha, chave de serviço, dado pessoal real
  nem exportação do banco pode ser commitado, nem em evidências de teste.
- `BREVO_API_KEY` e demais variáveis ficam no ambiente do Xano. `.streamlit/secrets.toml` não é
  versionado (use `.streamlit/secrets.toml.example` como modelo). `xano workspace pull --env`
  escreve os segredos em arquivo: não commitar e não colar a saída em lugar nenhum.
- Se um segredo aparecer em um terminal, log ou conversa, trate como vazado e gere um novo.
- **Assistentes de IA não recebem dado pessoal real.** `xano workspace pull --records` traz dados
  pessoais: use só localmente, nunca em ferramentas externas.
- Dados sensíveis (senha, código de acesso, dados bancários, documentos, feedback privado)
  seguem o padrão do código: campos privados e acesso por dono do registro ou por RH/Admin,
  nunca por Gestor quando o domínio já exclui esse acesso.

### LGPD

A documentação está em [`docs/lgpd/`](docs/lgpd/); comece pelo
[registro de operações](docs/lgpd/registro-de-operacoes.md).

- **Campo de dado sensível novo** (saúde, biometria, filiação sindical, raça, religião etc.) não
  é criado sem antes atualizar o registro de operações e o [RIPD](docs/lgpd/ripd.md). O sistema
  não coleta raça, sexo, religião, filiação sindical nem biometria.
- **Dados pessoais são mascarados** em auditoria e em logs (conta bancária, CPF, salário,
  telefone, endereço e e-mail nunca inteiros).
- **Serviço externo novo** que receba dados entra em [`docs/lgpd/operadores.md`](docs/lgpd/operadores.md)
  antes de receber o primeiro dado.
- Prazos de guarda e anonimização: [`docs/lgpd/retencao.md`](docs/lgpd/retencao.md).

## 8. Testes e evidências

O Xano não tem um test runner tradicional. Por isso:

- Toda mudança funcional tem, no `tasks.md`, uma estratégia de verificação (o que testar e como
  confirmar).
- **Teste contra o Xano real**, por HTTP, com um caso que deve passar e um que deve falhar,
  por perfil (Admin, RH, Gestor e Colaborador). Não conclua uma tarefa só pela leitura do código.
- O código de acesso de login é guardado como hash: para obter um token em teste, é preciso o
  código recebido por e-mail. O token vale 1 hora. O plano gratuito limita a 10 requisições por
  20 segundos (HTTP 429): espere entre as chamadas.
- Registre o resultado em [`docs/evidencias/`](docs/evidencias/) seguindo o
  [README da pasta](docs/evidencias/README.md): contas pelo papel, sem e-mail, token ou dado
  pessoal. Teste que não foi possível fazer entra como "não verificado", com o motivo.

## 9. Idioma e estilo

- Documentação, mensagens de erro, textos de tela, comentários e commits em **português do Brasil**.
- Código, nomes de tabelas, campos e rotas seguem o que já existe (português, sem acento nos
  identificadores).
- Estilo igual ao do código ao redor: densidade de comentários, nomes e idioma.

## 10. MCP do Figma nos agentes

Para ler os nós do Figma, configure o servidor MCP remoto do Figma
(`https://mcp.figma.com/mcp`) e autentique com a sua conta. Os comandos abaixo seguem a
documentação do Figma; **confira-a se algo mudar**, e a autenticação (OAuth) é feita por cada
pessoa.

- **Claude Code:** `claude mcp add --transport http figma https://mcp.figma.com/mcp` e, na
  primeira vez, `/mcp` para autenticar.
- **Codex:** `codex mcp add figma --url https://mcp.figma.com/mcp`, ou em
  `~/.codex/config.toml`: `[mcp_servers.figma]` com `url = "https://mcp.figma.com/mcp"`.
- **Gemini CLI:** em `~/.gemini/settings.json`, em `mcpServers`:
  `"figma": { "httpUrl": "https://mcp.figma.com/mcp" }`.
- **Alternativa sem MCP:** abrir o nó no Figma em **Dev Mode** e copiar medidas, cores e textos
  a mão, ou colar o link do nó para a pessoa responsável conferir.

Se o MCP não conectar, não invente o visual: use o Dev Mode ou peça o nó.
