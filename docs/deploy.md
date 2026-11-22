# Deploy, flags e plano de rollback — ConectaRH

**Situação:** o backend já roda no Xano (o workspace de desenvolvimento é o mesmo que serve o
frontend). **Decisão de 22/11/2026: o frontend fica no Streamlit Community Cloud.** Publicado em 22/11/2026:
<https://conectahr-wtdxtqbzz4lyrpjv8a48nt.streamlit.app/>. O teste de fumaça está em `docs/evidencias/deploy-streamlit-cloud.md`.

## Ambientes

| Ambiente | Backend | Frontend |
|---|---|---|
| Desenvolvimento | Workspace Xano 147338 (plano gratuito) | `streamlit run frontend/app.py` na máquina de cada pessoa |
| Demonstração | O mesmo workspace, com dados sintéticos | Streamlit Community Cloud, ligado a este repositório (branch `master`): <https://conectahr-wtdxtqbzz4lyrpjv8a48nt.streamlit.app/> |

O plano gratuito do Xano tem um workspace só, então **demonstração e desenvolvimento dividem o banco**.
Por isso os dados são sempre sintéticos: contas `@conectarh.test`, nomes fictícios, CPFs gerados que
passam na validação. **Nenhum registro real é importado** (nem de imagens, planilhas ou outro sistema).

## Configuração de produção

Variáveis de ambiente do Xano (painel *Settings → Environment variables*; nunca no repositório):

| Variável | Para quê | Obrigatória |
|---|---|---|
| `BREVO_API_KEY` | Envio de e-mail transacional | Sim |
| `CODIGO_ACESSO_PEPPER` | Segredo do hash dos códigos de acesso (valor aleatório longo) | Sim |
| `ARQUIVOS_DOMINIOS_APROVADOS` | Domínios aceitos em links de documentos (separados por vírgula) | Não (vale só a instância) |
| `INDICADORES_MINIMO_PESSOAS` | Mínimo de pessoas por grupo nos indicadores | Não (padrão 5) |
| `SESSAO_RETENCAO_DIAS`, `EMAIL_RETENCAO_DIAS`, `DESLIGADO_RETENCAO_DIAS` | Prazos de retenção da rotina diária | Não (180, 180 e 1825) |

Segredos do Streamlit (`.streamlit/secrets.toml` na máquina ou nos *Secrets* do serviço de
hospedagem): `xano.auth_base_url`, a URL da API do grupo de autenticação, e (opcional) `google.drive_api_key`,
a chave de API do Google para os vídeos dos treinamentos (change `treinamento-em-video`). Sem ela, o resto funciona e
"Meus treinamentos" mostra um aviso no lugar do vídeo. Para criar a chave:

1. No Google Cloud (da conta da empresa), crie um projeto e ligue a **Google Drive API**.
2. Em *Credenciais*, crie uma **chave de API**. Restrinja a chave à Google Drive API e, em *Restrições de aplicativo*,
   a *Referenciadores HTTP* com o endereço do app (por exemplo `https://seu-app.streamlit.app/*`).
3. Cole a chave nos *Secrets* da hospedagem, na seção `[google]`. Nunca no repositório.
4. No Drive, cada vídeo fica como "qualquer pessoa com o link", em MP4 (H.264); 720p basta.

Sem o Google Cloud, a outra opção é o **YouTube**: o RH sobe o vídeo como "não listado" e cola o link no mesmo
campo. Não precisa de chave nem de configuração.

## Publicar no Streamlit Community Cloud

Feito uma vez, por quem é dono do repositório no GitHub:

1. Em `share.streamlit.io`, entre com o GitHub e escolha **Create app → Deploy a public app from GitHub**.
2. **Repository:** `leonardo-sferreira/conectahr`. **Branch:** `master`. **Main file path:** `frontend/app.py`.
3. Em **Advanced settings**:
   - **Python:** 3.12. O app e os testes foram conferidos nessa versão em 22/11/2026; o desenvolvimento usa 3.14.
   - **Secrets:** cole o conteúdo do `.streamlit/secrets.toml` local, no formato do `.streamlit/secrets.toml.example`:
     - a seção `[xano]` com `auth_base_url`, obrigatória;
     - a seção `[google]` com `drive_api_key`, opcional.
4. **Deploy.** O serviço:
   - instala `frontend/requirements.txt`, que fica na pasta do arquivo principal;
   - lê `.streamlit/config.toml` da raiz, com o tema e o `enableStaticServing`;
   - serve `frontend/static`, com as fontes e as capas dos treinamentos.
5. Com o endereço final (`https://….streamlit.app`), restrinja a chave do Google a ele, se houver chave (seção acima).
6. Faça o teste de fumaça do roteiro abaixo e registre em `docs/evidencias/deploy-streamlit-cloud.md`, sem dado pessoal.

**Como funciona depois:**
- Cada merge em `master` republica o app sozinho.
- Os segredos ficam só no painel. As chaves do Supabase e da Brevo continuam no Xano, nunca no Streamlit.
- No plano gratuito, o app dorme depois de um tempo sem uso; o primeiro acesso depois disso demora alguns segundos.

### Configuração de produção (registrada em 22/11/2026)

| Item | Valor |
|---|---|
| Endereço | <https://conectahr-wtdxtqbzz4lyrpjv8a48nt.streamlit.app/> |
| Repositório e branch | `leonardo-sferreira/conectahr`, `master` (republica a cada merge) |
| Arquivo principal | `frontend/app.py` |
| Dependências | `frontend/requirements.txt` |
| Configuração | `.streamlit/config.toml`: tema e `enableStaticServing`, que serve `frontend/static` |
| Segredos (só no painel) | `[xano] auth_base_url`; `[google] drive_api_key`, opcional |
| Segredos que ficam no Xano | Brevo, Supabase e o pepper dos códigos de acesso (seção "Configuração de produção") |

O Streamlit Cloud abre o app dentro da própria página: o endereço passa pelo `share.streamlit.io`, que entrega um cookie de sessão, sem pedir login. Para conferir o app de fora, use um navegador; o `curl` recebe só essa página de passagem.

## Feature flags

O sistema não tem um mecanismo de feature flag. O equivalente hoje é:

- **Variáveis de ambiente** (tabela acima) para limites e prazos;
- **Página no menu:** uma tela só aparece se estiver em `frontend/app.py`, então uma tela nova pode
  ficar fora do menu até estar validada;
- **Rotas do backend** só existem depois do push; publicar o backend antes do frontend não expõe nada
  novo ao usuário.

Se for preciso uma flag real, o caminho é uma variável de ambiente lida pelo endpoint e pelo `st.secrets`.

## Roteiro de publicação

1. `python tools/checar_endpoints.py`, `python tools/smoke_frontend.py`, `python tools/testar_login_f01.py` e
   `python tools/testar_onboarding.py` passam (rodam também no GitHub, no workflow `Validar`).
2. Backend: `xano workspace push --dry-run`, conferir a lista, `push`, depois `pull` e diff
   (ver `xano-workspace/AGENTS.md`).
3. Frontend: merge do Pull Request em `master`; o Streamlit Community Cloud republica a partir do `master`.
4. **Teste de fumaça** em ambiente controlado: entrar com uma conta de teste (senha + código por
   e-mail), abrir o início e sair. Registrar o resultado em `docs/evidencias/`.

## Plano de rollback

| O que deu errado | Como voltar |
|---|---|
| Frontend | Reverter o commit no `master` (`git revert`): o Streamlit Community Cloud republica sozinho. Se o app não sobe, o painel (*Manage app*) mostra o log e permite *Reboot* |
| Endpoint do backend | Reverter o arquivo `.xs` no Git e fazer novo `push` do arquivo; o `pull` anterior à mudança serve de referência |
| Mudança de schema (campo novo) | Campos novos são aditivos e opcionais: o rollback é deixar de usá-los. Remover campo só com cópia do backup (ver `docs/monitoramento.md`) |
| Dados de teste incorretos | Não há exclusão física; corrigir por novo registro. Em último caso, restaurar o backup |
| Segredo vazado | Gerar um novo na Brevo, trocar no Xano, invalidar sessões (desativar e reativar os usuários afetados) |

Antes de qualquer publicação grande, tire um backup (`xano workspace pull`) e guarde a pasta fora do
repositório se ela contiver dados.
