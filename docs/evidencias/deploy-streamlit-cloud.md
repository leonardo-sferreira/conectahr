# Deploy no Streamlit Community Cloud

**Data:** 22/11/2026. **Endereço:** <https://conectahr-wtdxtqbzz4lyrpjv8a48nt.streamlit.app/>. **Change:** `concluir-frontend-streamlit`, tarefa 2.

## Teste de fumaça

| Verificação | Como | Resultado |
|---|---|---|
| O app abre na tela Entrar | Chrome, de fora, sem login | Ok. Aparecem o logotipo, "Bem-vindo de volta", e-mail, senha, "Entrar", "Esqueci minha senha" e os links do aviso de privacidade e do canal de denúncias. Print em `deploy-streamlit-cloud/entrar-no-ar.png` |
| Arquivos estáticos servidos pelo app | Fontes carregadas na página | Ok. Sora e Manrope vêm de `frontend/static`, sem Google Fonts |
| Sem erro na página | Elementos de erro do Streamlit | Nenhum |
| Entrar com conta de teste, abrir o Início e sair | Feito pelo dono do produto no app publicado | Ok, informado em 22/11/2026 |

**Versão publicada:** o master com as mudanças até o PR #133. O app foi conferido antes no Python 3.12, a versão escolhida no painel (`docs/deploy.md`).

**Rollback:** reverter o commit no `master`; o Streamlit Cloud republica sozinho. O painel ("Manage app") mostra o log e permite reiniciar.
