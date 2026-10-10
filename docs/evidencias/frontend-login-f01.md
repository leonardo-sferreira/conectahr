# Evidências — fluxo de entrada (Figma F01) no Streamlit

Fluxo F01 do protótipo (<https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn>, página "Fluxos — apresentação")
construído em `frontend/` na branch `feature/frontend-login-f01`: login do dia a dia, primeiro acesso com troca da
senha temporária e Onboarding, e os erros e exceções (senha nova inválida, sessão terminou).

## Como repetir

```
python tools/testar_login_f01.py     # 51 verificações, sem rede e sem .streamlit/secrets.toml
python tools/smoke_frontend.py       # a tela Entrar renderiza
```

O teste usa o AppTest do Streamlit com uma API simulada (contas fictícias, sem dado real) e roda também no
GitHub, no workflow `Validar`. **Resultado em 10/10/2026: 51 de 51 verificações ok** e o smoke ok.

## Casos cobertos

| Estado de UI | Caso | Esperado | Resultado |
|---|---|---|---|
| Sucesso | E-mail e senha certos, código certo | Abre o Início, sem Onboarding | ok |
| Sucesso | Primeiro acesso: código, troca da senha, "Enviar documentos" | Onboarding (13 etapas em 6 linhas) e depois Início com o card do onboarding; o item "Trocar a senha temporária" fica concluído | ok |
| Erro | Credencial inválida | Alerta dentro do cartão, sem dizer se a conta existe | ok |
| Erro | E-mail ou senha fora do formato | A validação local barra; a API não é chamada | ok |
| Erro | Código fora do formato | Não chega à API (não gasta uma das 5 tentativas) | ok |
| Erro | Código errado | Mensagem do backend com as tentativas que restam | ok |
| Erro | Senha nova curta, confirmação diferente, igual à temporária | Mensagem do que falta; a API não é chamada | ok |
| Erro | Senha temporária errada | "A senha temporária está incorreta." (texto do Figma 224:583) e borda vermelha no campo | ok |
| Erro | Onboarding não carrega | Alerta no cartão e botão "Continuar para o início" | ok |
| Bloqueado | Muitas tentativas de login | Mensagem do backend dentro do cartão | ok |
| Permissão negada | Resposta 403 | Mensagem no cartão, sem exceção | ok |
| Vazio | Conta sem colaborador vinculado | Vai direto ao Início | ok |
| Vazio | Colaborador sem checklist (404) | Vai direto ao Início | ok |
| Carregando | Spinner "Carregando seu onboarding..." dentro do cartão | Visível até o checklist chegar | verificado no navegador |
| Sessão | 401 numa chamada autenticada | Volta ao login com "Sua sessão terminou" e o e-mail preenchido | ok |
| Sessão | `auth/me` responde 401 logo depois do login | Mesmo aviso | ok |
| Sessão | Prazo do token vencido pelo relógio | Mesmo aviso | ok |
| Sessão | 401 sem token (senha errada no login) | **Não** conta como sessão encerrada | ok |
| Reenvio | Reenviar antes de 60 s | "Aguarde N segundos..."; a API não é chamada | ok |
| Reenvio | Reenviar depois de 60 s | Chama `auth/otp/reenviar` | ok |
| Sair | "Sair" na troca de senha | Chama `auth/logout`, descarta o token pendente e volta ao login | ok |

**Contra a API real** (dados fictícios, só os casos que não precisam do código por e-mail): `auth/login` com
credencial inexistente responde 403 "E-mail ou senha inválidos."; `auth/me` com token inválido responde 401
"Invalid token." e o cliente trata como "Sua sessão terminou". **Não verificado:** o ciclo completo com o código
recebido por e-mail, porque não há caixa de e-mail de teste neste ambiente. Esse trecho foi verificado só com
a API simulada.

## Verificado no navegador (Chrome, API simulada)

- A tecla Enter no campo de senha envia o login (o link "Esqueci minha senha", que fica antes do botão
  "Entrar" no Figma, não o intercepta) e, no código, valida o código.
- A legenda "Expira em MM:SS" do código conta de 5 minutos para zero (04:59 → 04:56 em 3 s).
- Sem sessão, abrir `/inicio` mostra a tela Entrar.
- O menu lateral do Início continua cinza com o item ativo em âmbar (uma regra de link nova chegou a pintá-lo
  de âmbar e foi corrigida).

## Comparação com o Figma

Prints lado a lado (esquerda o nó do Figma, direita o app) em
[`frontend-f01/`](frontend-f01/): `1-login`, `2-codigo-de-acesso`, `3-trocar-senha`, `4-senha-invalida`,
`5-sessao-terminou` e, só com o app, `6-onboarding`, `7-meu-onboarding` e `8-inicio-com-onboarding` (ver
[`frontend-onboarding.md`](frontend-onboarding.md)). No Passo 2 o e-mail de exemplo do Figma foi coberto, porque o protótipo
ainda tem um e-mail de pessoa real (tarefa 60 da change).

| Nó do Figma | Tela |
|---|---|
| 224:198 | Login — Passo 1 |
| 224:228 | Login — Passo 2 (código de acesso, seis caixas) |
| 224:389 | Login — Passo 3 (trocar senha temporária) |
| 224:583 | Login — Passo 3, erro |
| 224:619 | Login — Sessão expirada |
| 310:2477 | Onboarding (boas-vindas, desenho de 10/10/2026) |

## Diferenças em relação ao protótipo

- **Onboarding:** desde 10/10/2026 o desenho segue as 13 etapas do backend (nó 310:2477). A tela foi refeita e
  tem evidência própria em [`frontend-onboarding.md`](frontend-onboarding.md). A saudação usa "Bem-vindo(a)"
  (o exemplo do Figma é de uma pessoa: "Bem-vinda"), porque o cadastro não guarda gênero.
- **Mostrar a senha:** os campos de senha mantêm o botão do olho do Streamlit, em tom neutro. O Figma não o
  desenha; ele ajuda a conferir a nova senha.
- **Código de acesso:** é um único campo desenhado como seis caixas (algarismos de largura fixa); colar os seis
  dígitos de uma vez funciona.
- **Contraste:** o texto do alerta de erro (`#DC2626` sobre vermelho claro) e o do botão "Esqueci minha senha"
  seguem o protótipo; as medidas abaixo de 4,5:1 estão na tarefa 61 da change.
