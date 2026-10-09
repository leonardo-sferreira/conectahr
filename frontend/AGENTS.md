# AGENTS.md — frontend (Streamlit)

Regras específicas desta pasta. Todo o resto (fluxo de trabalho, segredos, LGPD, testes e
idioma) está no [`AGENTS.md` da raiz](../AGENTS.md) e vale aqui. Não repita regras da raiz neste arquivo.

## Regras de tela (Figma)

O protótipo oficial é <https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn>. As 7 regras estão
na seção 6 da raiz. Em resumo: ler o nó antes de codar; nada visual fora de `theme.py`; tela
que não existe no Figma é desenhada antes; textos idênticos; os 6 estados de UI; PR com o link
do nó e prints lado a lado; menu por perfil é só conveniência.

Os alertas de erro e de sucesso ficam **dentro do card**, abaixo do título, como no Figma.

## Como rodar

Na raiz do repositório (o Streamlit lê `.streamlit/` a partir da pasta em que é iniciado):

```
python -m venv .venv
.venv\Scripts\activate          # Windows; no Linux/Mac: source .venv/bin/activate
pip install -r frontend/requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # Linux/Mac: cp
# edite .streamlit/secrets.toml e informe a URL da API do grupo de autenticação
streamlit run frontend/app.py
```

`.streamlit/secrets.toml` **não é versionado**. O modelo `.streamlit/secrets.toml.example` não
tem valor real:

```toml
[xano]
# URL de qualquer grupo da API da instância; o cliente troca o identificador do grupo.
auth_base_url = "https://SUA-INSTANCIA.n7.xano.io/api:ID_DO_GRUPO_DE_AUTENTICACAO"
```

Sem esse arquivo, ou com uma URL que não começa com `https://`, a tela mostra uma mensagem de
configuração, em vez de quebrar.

## Cliente de API (`api_client.py`)

Todo acesso à API passa por `frontend/api_client.py`. Não chame `requests` direto de uma tela.

- Uma função por endpoint (ex.: `login`, `central_de_tarefas`), usando `_post` e `_get`, que
  recebem o grupo da API (`GRUPO_*`, o identificador canônico do grupo em
  `xano-workspace/api/<grupo>/<grupo>.xs`).
- Erros viram `ApiError(mensagem, status_code)`. A mensagem já vem em português; mensagens em
  inglês geradas pelo Xano passam por `_traduzir`. A tela mostra `ApiError` dentro do card.
- A base URL vem de `st.secrets["xano"]["auth_base_url"]`.
- O token fica em `st.session_state` e é enviado em `Authorization: Bearer`. Respostas 401
  (sessão encerrada, expirada ou revogada) devem levar o usuário de volta a "Entrar" com uma
  mensagem.
- Validação de campos antes do envio em `frontend/validacao.py`. Ela é conveniência de
  usabilidade: o backend sempre valida de novo.

## Tema e HTML

- Cores, fontes e componentes visuais ficam em `frontend/theme.py` (`GRAFITE`, `AMBAR`, `MARFIM`,
  `BORDA`, `SUCESSO`, `ERRO` e as funções `inject_base_styles`, `render_header`,
  `render_card_title`…). **Não** crie cor, fonte ou CSS solto em uma página.
- HTML próprio só com `st.html()`, sempre escapando texto vindo de usuário ou da API
  (`html.escape`). Nunca use `unsafe_allow_html` com texto não escapado.
- Fontes: Sora e Manrope. Hoje são carregadas do Google Fonts, o que envia o IP do usuário ao
  Google; servir localmente está na tarefa 4 da change `concluir-frontend-streamlit` (origem 3.50).

## Os 6 estados de UI

Toda tela trata, seguindo o Figma: **carregando**, **vazio**, **sucesso**, **erro**,
**bloqueado** e **permissão negada**. O estado de permissão negada reflete a resposta 403 do
backend; esconder um botão não substitui a regra.

## Estrutura

- `app.py`: ponto de entrada; `st.navigation`/`st.Page`, guarda de sessão e sidebar.
- `pagina_*.py`: uma página por tela (`pagina_entrar.py`, `pagina_inicio.py`…).
- `theme.py`, `api_client.py`, `validacao.py`, `assets/`.

Uma tela nova entra com: nó do Figma conferido → página → função(ões) no `api_client.py` →
teste dos 6 estados e do escopo por perfil.
