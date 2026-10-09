# Deploy, flags e plano de rollback — ConectaRH

**Situação:** o backend já roda no Xano (o workspace de desenvolvimento é o mesmo que serve o
frontend). O frontend Streamlit ainda não foi publicado: este documento descreve como será e como
voltar atrás. Nada aqui foi executado em produção.

## Ambientes

| Ambiente | Backend | Frontend |
|---|---|---|
| Desenvolvimento | Workspace Xano 147338 (plano gratuito) | `streamlit run frontend/app.py` na máquina de cada pessoa |
| Demonstração | O mesmo workspace, com dados sintéticos | Streamlit Community Cloud (sugestão), ligado a este repositório |

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
hospedagem): `xano.auth_base_url`, a URL da API do grupo de autenticação.

## Feature flags

O sistema não tem um mecanismo de feature flag. O equivalente hoje é:

- **Variáveis de ambiente** (tabela acima) para limites e prazos;
- **Página no menu:** uma tela só aparece se estiver em `frontend/app.py`, então uma tela nova pode
  ficar fora do menu até estar validada;
- **Rotas do backend** só existem depois do push; publicar o backend antes do frontend não expõe nada
  novo ao usuário.

Se for preciso uma flag real, o caminho é uma variável de ambiente lida pelo endpoint e pelo `st.secrets`.

## Roteiro de publicação

1. `python tools/checar_endpoints.py` e `python tools/smoke_frontend.py` passam (rodam também no
   GitHub, no workflow `Validar`).
2. Backend: `xano workspace push --dry-run`, conferir a lista, `push`, depois `pull` e diff
   (ver `xano-workspace/AGENTS.md`).
3. Frontend: merge do Pull Request em `master`; o serviço de hospedagem publica a partir do `master`.
4. **Teste de fumaça** em ambiente controlado: entrar com uma conta de teste (senha + código por
   e-mail), abrir o início e sair. Registrar o resultado em `docs/evidencias/`.

## Plano de rollback

| O que deu errado | Como voltar |
|---|---|
| Frontend | Reverter o commit no `master` (`git revert`) e republicar; ou apontar a hospedagem para o commit anterior |
| Endpoint do backend | Reverter o arquivo `.xs` no Git e fazer novo `push` do arquivo; o `pull` anterior à mudança serve de referência |
| Mudança de schema (campo novo) | Campos novos são aditivos e opcionais: o rollback é deixar de usá-los. Remover campo só com cópia do backup (ver `docs/monitoramento.md`) |
| Dados de teste incorretos | Não há exclusão física; corrigir por novo registro. Em último caso, restaurar o backup |
| Segredo vazado | Gerar um novo na Brevo, trocar no Xano, invalidar sessões (desativar e reativar os usuários afetados) |

Antes de qualquer publicação grande, tire um backup (`xano workspace pull`) e guarde a pasta fora do
repositório se ela contiver dados.
