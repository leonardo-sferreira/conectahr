## Context

Hoje `frontend/` só tem a tela de login (`app.py`, `theme.py`, `api_client.py`, `assets/logo-icon.svg`), construída nesta mesma sessão. Nesse processo já aprendemos, na prática, várias limitações reais do Streamlit que valem registrar aqui antes de escalar para as 12 telas restantes:

- `st.markdown(unsafe_allow_html=True)` sanitiza o HTML com um allowlist restrito — remove tags como `<style>` e `<link>` mantendo só o texto de dentro (isso já causou um bug visual real: CSS aparecendo como texto solto na página). `st.html()` não sanitiza dessa forma e é a API correta para HTML/CSS de página escrito pelo próprio time.
- Fontes do Google Fonts carregadas via `<link>` também são removidas pelo mesmo motivo; `@import` dentro do próprio bloco `<style>` sobrevive por ser só texto CSS.
- Streamlit não permite que uma tag HTML aberta numa chamada "abrace" um widget nativo (`st.button`, `st.text_input`) renderizado numa chamada seguinte — cada chamada de HTML vira um nó isolado no DOM. Para estilizar um widget nativo é preciso mirar seletores CSS que o próprio Streamlit expõe (`data-testid`, atributos como `kind="primary"`) ou usar a variante nativa mais próxima (ex.: `st.button(..., type="tertiary")` para botões estilo link, em vez de tentar envolver o botão numa `<div>` customizada).
- O protótipo Figma ("ConectaRH — Protótipo", `fph1M5tB4rA4gqfIysSmkn`) é acessível via MCP do Figma (`get_design_context`, `get_screenshot`, `download_assets`) — os tokens de cor/tipografia/espaçamento devem ser extraídos de lá node a node, não aproximados de memória. Foi assim que o bug de padding incorreto do card de login foi identificado e corrigido.

Ver `proposal.md` para o porquê desta change; ver `specs/conectahr/spec.md` para os requisitos que ela precisa satisfazer.

## Goals / Non-Goals

**Goals:**

- Estabelecer um padrão de implementação (estrutura de arquivos, injeção de CSS, cliente de API, guarda de sessão) que se repita nas 12 telas restantes sem redecidir a cada uma.
- Definir como e quando sinalizar uma limitação do Streamlit frente ao Figma, para isso acontecer de forma consistente em vez de ad-hoc.
- Deixar registrado, tela a tela, à medida que forem iniciadas, qualquer elemento do Figma que exija uma tecnologia além do Streamlit puro.

**Non-Goals:**

- Não é objetivo desta change migrar de framework (Streamlit continua sendo a escolha definida em `AGENTS.md`/`design.md` do `conectarh.gestao`) — tecnologia alternativa é para complementar pontos específicos, não substituir a base.
- Não é objetivo desta change alterar nenhum endpoint do backend — só consumir o que já existe.
- Não é objetivo desta change implementar a `Central de tarefas`/`Indicadores`/`Preferências de notificação` como telas próprias — essas funcionalidades já aparecem embutidas nas telas Início e Auditoria conforme o protótipo; não há tela dedicada a elas no Figma.

## Decisions

### Estrutura de navegação: `st.navigation`/`st.Page` com portão de autenticação

Usar a API nativa de multi-página do Streamlit (`st.Page` + `st.navigation`, disponível na 1.64) em vez de um único arquivo com `if/elif` gigante (o padrão usado na tela de login, que já está no limite do razoável com 5 estados). Um `app.py` na raiz decide, a cada execução, a lista de páginas visíveis com base em `st.session_state.get("token")`: sem token, só a página de autenticação (login/OTP/esqueci senha, que continua como um fluxo interno de estados — é um wizard linear, não faz sentido como navegação); com token, o conjunto de páginas correspondente ao perfil do usuário (ex.: Auditoria e Regras só aparecem para RH/ADMIN).

Alternativa considerada: manter tudo num arquivo só com mais estados em `auth_step`/`tela_atual` — rejeitada por não escalar para 12 telas e por perder a navegação lateral nativa que o próprio protótipo Figma usa (menu lateral com item ativo).

### Tema e design system: estender `frontend/theme.py`

Cada nova tela reutiliza `inject_base_styles()`, os tokens de cor (`GRAFITE`, `AMBAR`, etc.) e os componentes já validados (`card_marker`/`render_card_title` para o "crachá"). Antes de codar uma tela nova, buscar o node correspondente no Figma via MCP (`get_design_context` + `get_screenshot`) para extrair cor/tipografia/espaçamento reais, em vez de aproximar visualmente — foi a causa dos dois bugs já corrigidos na tela de login (fonte não carregando, padding errado). Componentes visuais novos que se repetem entre telas (ex.: a "trilha de conexão" usada em pendências/férias/documentos/avaliações/regras) viram uma função nova em `theme.py`, não são reimplementados tela a tela.

Toda injeção de HTML/CSS usa exclusivamente `st.html()`. `st.markdown(unsafe_allow_html=True)` fica proibido para esse fim neste projeto (registrar isso também em `AGENTS.md` ao aplicar esta change).

### Cliente de API: manter `frontend/api_client.py`, dividir por domínio quando crescer

Continuar adicionando funções a `api_client.py` (um `_post`/`_get` genérico já existe) enquanto o arquivo for gerenciável; quando ultrapassar ~300 linhas ou come çar a misturar muitos domínios (autenticação, pendências, ponto, férias, documentos...), dividir em módulos por domínio dentro de `frontend/api/` (ex.: `api/autenticacao.py`, `api/ponto.py`), todos reaproveitando o mesmo tratamento de erro (`ApiError`) e a mesma leitura de `st.secrets`. Cada grupo de API do Xano (ex.: "ConectaRH — Ponto") deve ter sua própria `base_url` em `.streamlit/secrets.toml`, adicionada conforme a tela correspondente for integrada — hoje só existe `xano.auth_base_url`.

### Guarda de sessão

Toda página que exige autenticação verifica `st.session_state.get("token")` no topo; sem token, redireciona para a página de autenticação (`st.switch_page`). Páginas restritas a perfil (Auditoria, Regras) verificam também `st.session_state.usuario["perfil"]` antes de montar qualquer conteúdo — sempre como conveniência de navegação, nunca como controle de acesso real: o backend segue sendo a única fonte de verdade de autorização (requisito "Frontend não decide autorização" do spec).

### Processo para limitações do Streamlit frente ao Figma

Antes de iniciar a implementação de UI de uma tela, revisar o node correspondente no Figma em busca de elementos que o Streamlit não tenha suporte nativo razoável (ex.: drag-and-drop, animações complexas, um calendário interativo rico). Se encontrado:

1. Registrar o achado nesta seção (subseção "Limitações identificadas" abaixo), citando a tela e o elemento específico.
2. Propor a alternativa antes de implementar — tipicamente um componente customizado via `streamlit.components.v1.html` (JS embutido, ainda dentro do mesmo processo Python/Streamlit) ou, em último caso, um componente React empacotado como Streamlit Custom Component.
3. Só implementar depois de a alternativa estar registrada — nunca entregar uma versão silenciosamente simplificada sem essa nota.

#### Limitações identificadas (atualizar conforme cada tela for iniciada)

Nenhuma até o momento — as duas telas já implementadas (Login, Código de Acesso) não exigiram nada além de Streamlit + CSS. Candidatos a observar ao iniciar as telas correspondentes (ainda não confirmados, só antecipados a partir da descrição do protótipo em `docs/figma-prototipo.md`):

- **Férias/Central de pendências** — o protótipo menciona verificação de conflito de agenda; se o Figma mostrar um calendário visual interativo (não só uma lista/tabela de datas), isso provavelmente excede os widgets nativos do Streamlit.
- **Auditoria/Indicadores** (se o protótipo detalhar gráficos) — Streamlit tem `st.line_chart`/`st.bar_chart`/suporte a Altair nativamente, então só seria uma limitação real se o Figma pedir uma visualização muito além disso.

Nenhuma decisão de tecnologia alternativa é tomada aqui adiantado — cada caso será revisado (e esta seção atualizada) no início da tarefa daquela tela específica, conforme o processo acima.

## Risks / Trade-offs

- **Seletores CSS não são API oficial do Streamlit** (`data-testid`, `kind="..."`) → podem mudar em atualizações futuras do Streamlit. Mitigação: versão pinada em `requirements.txt` (`streamlit==1.64.0`); qualquer upgrade de versão deve re-testar visualmente as telas antes de mesclar.
- **Modelo de execução do Streamlit (rerun completo do script a cada interação)** deixa fluxos com muitos passos (ex.: login) mais verbosos que em frameworks orientados a componentes → mitigação: o padrão de `st.session_state` + funções auxiliares em `theme.py` já absorve a maior parte dessa complexidade.
- **Fidelidade visual ao Figma depende de inspecionar cada node antes de codar** → se esse passo for pulado (como aconteceu nas duas primeiras vezes), o resultado diverge do protótipo sem ninguém perceber até alguém comparar lado a lado. Mitigação: o processo de "buscar o node via MCP antes de implementar" fica registrado como decisão formal aqui, não é mais opcional.

## Open Questions

- Quais telas, exatamente, vão precisar de tecnologia além do Streamlit puro só será conhecido ao inspecionar cada node do Figma no início da tarefa correspondente (ver "Limitações identificadas" acima). Isso não muda o approach nem o spec — só pode adicionar tarefas específicas de implementação quando identificado, seguindo o processo já decidido.
