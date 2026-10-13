# Primeiros passos no ConectaRH

Guia para quem vai começar a trabalhar no projeto: instalar as ferramentas, baixar o repositório, rodar o sistema na
sua máquina, rodar os testes e abrir o primeiro Pull Request. Os comandos são para **Windows** (PowerShell); quando
muda no Mac ou no Linux, está indicado.

> **Duas trilhas.** Para mexer só nas telas, siga as partes 1 a 6. Para mexer também no backend (Xano), faça
> também a parte 7.

---

## 1. Acessos que você precisa pedir

Peça ao responsável pelo backend (Leonardo) antes de começar:

| Acesso | Para quê | Obrigatório? |
|---|---|---|
| Convite no repositório do GitHub (`leonardo-sferreira/conectahr`) | Criar branches e abrir Pull Requests | Sim |
| A **URL da API** do Xano (vai no `secrets.toml`, parte 4) | O frontend conversar com o backend | Sim |
| Uma **conta de teste** no ConectaRH (RH, Gestor ou Colaborador), com um e-mail seu | Entrar no sistema: o código de acesso chega por e-mail | Sim |
| Convite no arquivo do **Figma** (`fph1M5tB4rA4gqfIysSmkn`) | Ver o protótipo antes de mexer numa tela | Para quem mexe em tela |
| Convite no **workspace do Xano** (workspace 147338) | Ver e publicar o backend | Só na trilha de backend |
| Acesso ao **Supabase** e ao **Streamlit Cloud** | Arquivos e o app publicado | Normalmente não (só o responsável) |

**Nunca peça nem mande senha, token ou chave por WhatsApp ou e-mail.** As chaves ficam só no painel de cada serviço
(veja a parte 10).

---

## 2. Instalar as ferramentas

| Ferramenta | Versão | Onde baixar | Como conferir |
|---|---|---|---|
| **Git** | 2.40 ou mais nova | <https://git-scm.com/downloads> | `git --version` |
| **Python** | **3.12** ou mais nova (o pipeline usa 3.12) | <https://www.python.org/downloads/> — no instalador do Windows, marque **"Add python.exe to PATH"** | `python --version` |
| **VS Code** | qualquer recente | <https://code.visualstudio.com/> | — |
| **GitHub CLI** (`gh`) | 2.x | <https://cli.github.com/> | `gh --version` |
| **Node.js** | LTS (20 ou mais novo) | <https://nodejs.org/> | `node --version` |

No VS Code, instale as extensões **Python** e **Pylance** (Microsoft).

O Node.js só é necessário para as ferramentas de linha de comando do **Xano** e do **OpenSpec** (partes 7 e 8). Se você
vai só mexer em tela, pode deixar para depois.

Depois de instalar, **feche e abra de novo** o terminal para os comandos serem reconhecidos.

---

## 3. Baixar o repositório

```powershell
# 1. Entre no GitHub pelo terminal (abre o navegador)
gh auth login

# 2. Escolha uma pasta SEM acento e sem espaço, de preferência fora do OneDrive
cd C:\projetos

# 3. Baixe o repositório
gh repo clone leonardo-sferreira/conectahr
cd conectahr

# 4. Seu nome e e-mail nos commits (os mesmos da sua conta do GitHub)
git config user.name "Seu Nome"
git config user.email "seu-email-do-github@exemplo.com"
```

Abra a pasta no VS Code: `code .`

---

## 4. Rodar o sistema na sua máquina

### 4.1 Ambiente do Python (uma vez só)

```powershell
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r frontend/requirements.txt
```

Se o PowerShell recusar o `activate` ("execução de scripts foi desabilitada"), rode uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Com o ambiente ativo, o terminal mostra `(.venv)` no começo da linha. **Ative de novo sempre que abrir um terminal
novo** (`.venv\Scripts\activate`).

### 4.2 Configuração do frontend (uma vez só)

```powershell
copy .streamlit\secrets.toml.example .streamlit\secrets.toml     # Mac/Linux: cp
```

Abra `.streamlit/secrets.toml` e troque o exemplo pela **URL da API** que você recebeu (parte 1):

```toml
[xano]
auth_base_url = "https://...xano.io/api:..."
```

Esse arquivo **não vai para o GitHub** (está no `.gitignore`). Não tire ele de lá.

### 4.3 Subir o app

```powershell
streamlit run frontend/app.py
```

O navegador abre em <http://localhost:8501>. Para parar, `Ctrl + C` no terminal. Quando você salva um arquivo, a tela
oferece "Rerun" para recarregar.

### 4.4 Entrar no sistema

1. Use o e-mail e a senha temporária da sua conta de teste.
2. O **código de acesso** chega no seu e-mail (de 6 dígitos; olhe o spam).
3. No primeiro acesso, o sistema pede para trocar a senha.

Cada perfil vê um menu diferente: **Colaborador** (só os próprios dados), **Gestor** (a equipe), **RH** e **Admin**
(cadastros, documentos e regras). Para testar outro perfil, peça outra conta de teste.

> O plano gratuito do Xano aceita **10 requisições a cada 20 segundos**. Se aparecer "muitas requisições", espere
> alguns segundos e recarregue.

---

## 5. Rodar os testes

Os testes de tela rodam **sem internet e sem login**: simulam a API com dados fictícios.

```powershell
python tools/testar_ferias.py              # uma suíte
python tools/checar_endpoints.py           # guarda de acesso do backend (lê os arquivos .xs)
```

Rode **a suíte da tela que você mexeu** antes de abrir o PR. A lista completa está no
[README](../README.md#qualidade-e-testes) e no pipeline [`.github/workflows/validar.yml`](../.github/workflows/validar.yml),
que roda tudo sozinho em cada Pull Request.

Cada suíte termina com `N/N verificações ok.`. Se alguma falhar, ela mostra `FALHA:` e o nome do que quebrou.

---

## 6. Como a equipe trabalha (fluxo do dia a dia)

### 6.1 Antes de mexer

- **Tela nova ou mudança visual:** confira o nó no **Figma** antes de codar; os textos seguem o protótipo
  ([`docs/figma-prototipo.md`](figma-prototipo.md)). O que ainda não está no Figma fica em
  [`docs/figma-pendencias.md`](figma-pendencias.md).
- **Mudança de regra ou funcionalidade:** vira uma *change* do OpenSpec (parte 8) com proposta, design, spec e
  tarefas, antes do código.
- Leia o [`AGENTS.md`](../AGENTS.md): é a regra do projeto para pessoas e para assistentes de IA.

### 6.2 Branch, commit e Pull Request

```powershell
git switch master
git pull                                        # sempre comece do master atualizado
git switch -c feature/nome-curto-da-tarefa      # uma branch por tarefa

# ... edite, rode os testes ...

git add caminho/do/arquivo.py
git commit -m "Descrição do que mudou e por quê (tarefa X.Y)"
git push -u origin feature/nome-curto-da-tarefa
gh pr create --base master                      # abre o PR; descreva o que mudou e como testou
```

Regras:

- **Nunca** faça push direto no `master`. Tudo entra por Pull Request, com o pipeline **Validar** verde e pelo menos
  uma revisão de alguém do grupo.
- O commit cita a tarefa do `tasks.md` da change (ex.: `6.1`).
- Commits e PRs não levam "Co-Authored-By" de ferramenta de IA.
- O app publicado no **Streamlit Cloud** atualiza sozinho quando o PR entra no `master`. Antes disso, a mudança só
  existe na sua máquina e na branch.

### 6.3 Depois do merge

```powershell
git switch master
git pull
git branch -d feature/nome-curto-da-tarefa      # apaga a branch local
```

---

## 7. Trilha do backend (Xano)

O backend é o **Xano**, programado em **XanoScript**. Os arquivos ficam em `xano-workspace/` (`table/`, `function/`,
`api/`) e são publicados pela linha de comando. Leia antes o [`xano-workspace/AGENTS.md`](../xano-workspace/AGENTS.md):
ele tem o checklist de todo endpoint e as armadilhas conhecidas.

### 7.1 Instalar e entrar

```powershell
npm install -g @xano/cli
xano auth -p ConectaRH          # abre o navegador; escolha a instância e o workspace 147338
xano profile workspace -p ConectaRH
```

Use **sempre** `-p ConectaRH` nos comandos: o perfil padrão pode ser de outro projeto seu.

### 7.2 Publicar uma mudança

```powershell
cd xano-workspace

# 1. Sempre o dry-run antes: confira se só aparecem os arquivos que você mudou
xano workspace push -p ConectaRH -i "api/conecta_rh_ferias/**/*.xs" -e "api/*/conecta_rh_*.xs" --dry-run

# 2. Se estiver certo, publique
xano workspace push -p ConectaRH -i "api/conecta_rh_ferias/**/*.xs" -e "api/*/conecta_rh_*.xs" --force

cd ..
python tools/checar_endpoints.py     # confere a guarda de acesso
```

Cuidados:

- Os padrões `-i` e `-e` vão **entre aspas**.
- Mudança de tabela (campo novo) vai num push **separado**, e o dry-run só pode mostrar `ADD_FIELD`/`UPDATE_FIELD`.
- **Nunca** use `--sync --delete` nem `--truncate`.
- Uma função pode ser rodada direto para testar: `xano function run "ConectaHR/nome" -p ConectaRH --json "@caso.json"`.
- Não use `xano workspace pull --records`: ele baixa dados pessoais reais.

### 7.3 Variáveis de ambiente

As chaves (Brevo, Supabase, etc.) ficam em **Settings → Environment Variables** no painel do Xano, nunca no
repositório. A lista está no [README](../README.md#backend-xano) e em [`docs/deploy.md`](deploy.md).

---

## 8. Especificações (OpenSpec)

Toda mudança relevante passa por **Explorar → Propor → Revisar → Aplicar → Arquivar**.

```powershell
npm install -g @fission-ai/openspec
openspec list                         # changes em andamento e quantas tarefas faltam
openspec validate nome-da-change      # confere a change antes do PR
```

- `openspec/specs/` tem o comportamento do sistema; `openspec/changes/` as mudanças em andamento; `archive/`, as
  concluídas.
- Cada change tem `proposal.md` (por quê), `design.md` (decisões), `specs/.../spec.md` (requisitos e cenários) e
  `tasks.md` (tarefas, cada uma com "Verificar:").
- Quem usa o Claude Code tem os comandos `/opsx:explore`, `/opsx:propose`, `/opsx:apply` e `/opsx:archive`.

---

## 9. Assistentes de IA (opcional)

O projeto foi preparado para **Claude Code**, **Codex** e **Gemini CLI**:

- O [`AGENTS.md`](../AGENTS.md) é a instrução única; o `CLAUDE.md` e o `GEMINI.md` apontam para ele.
- Para o assistente ler o Figma, configure o MCP do Figma (seção 10 do `AGENTS.md`).
- **Não cole dado pessoal real** (nome, CPF, e-mail de pessoas reais) em nenhum assistente.

---

## 10. Regras de ouro (o repositório é público)

1. Nenhuma **senha, token, chave** ou URL com segredo no código, em commit, em print ou em evidência.
2. **Nenhum dado pessoal real** em teste, exemplo, print ou documento. Use dados fictícios.
3. Se um segredo vazar (terminal, conversa, commit), avise o responsável: a chave precisa ser **trocada**.
4. O frontend **nunca** é a segurança: quem decide o que cada perfil pode fazer é o backend.
5. Dado sensível novo (saúde, biometria etc.) só depois de atualizar a documentação de LGPD
   ([`docs/lgpd/`](lgpd/)).

---

## 11. Problemas comuns

| Sintoma | O que fazer |
|---|---|
| `python` não é reconhecido | Reinstale o Python marcando "Add python.exe to PATH" e abra um terminal novo |
| "execução de scripts foi desabilitada" ao ativar o `.venv` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `ModuleNotFoundError: streamlit` | O `.venv` não está ativo: `.venv\Scripts\activate` |
| "Configuração ausente: crie .streamlit/secrets.toml" | Faça a parte 4.2 |
| O código de acesso não chega | Olhe o spam; espere 1 minuto; peça para o responsável conferir o envio (Brevo) |
| "Muitas requisições" / erro 429 | Limite do plano gratuito do Xano: espere uns segundos |
| A tela volta para "Entrar" sozinha | A sessão dura 1 hora ou foi encerrada: entre de novo |
| "Port 8501 is already in use" | Já há um Streamlit aberto: feche-o ou rode `streamlit run frontend/app.py --server.port 8502` |
| O PR ficou vermelho no "Validar" | Abra o link do check no PR: ele mostra qual teste falhou |
| A mudança não aparece no app publicado | Ela só aparece depois que o PR entra no `master` |
| Conflito no PR | `git switch master`, `git pull`, `git switch sua-branch`, `git merge master`, resolva no VS Code e faça push |

---

## Onde está cada coisa

| Quero entender… | Leia |
|---|---|
| O que é o projeto | [`README.md`](../README.md) e [`docs/project-overview.md`](project-overview.md) |
| A arquitetura | [`docs/arquitetura.md`](arquitetura.md) |
| As regras de negócio (com o arquivo de cada uma) | [`docs/regras-de-negocio.md`](regras-de-negocio.md) |
| Os conceitos do domínio | [`docs/domain-model.md`](domain-model.md) |
| Como funciona o ponto (REP-P) | [`docs/ponto/rep-p.md`](ponto/rep-p.md) |
| LGPD | [`docs/lgpd/`](lgpd/) |
| Os resultados dos testes | [`docs/evidencias/`](evidencias/) |
| Como roteirizar uma demonstração | [`docs/demonstracao.md`](demonstracao.md) |
