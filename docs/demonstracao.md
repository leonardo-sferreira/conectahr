# Roteiro de demonstração — ConectaRH

Roteiro para um avaliador reproduzir o fluxo principal. O frontend hoje tem a **tela de entrada** e o
**início**; as demais telas dependem do protótipo do Figma. Por isso o roteiro usa a tela para entrar
e a **API** (HTTP) para o resto, e cada passo diz o que esperar. As evidências de cada comportamento
estão em [`docs/evidencias/`](evidencias/).

## Antes de começar

1. Siga "Como rodar" em [`frontend/AGENTS.md`](../frontend/AGENTS.md) (ambiente virtual, `pip install`,
   `.streamlit/secrets.toml` a partir do exemplo e `streamlit run frontend/app.py`).
2. Tenha contas de teste (dados fictícios) para os quatro perfis: Admin, RH, Gestor e Colaborador. O
   código de acesso chega **por e-mail**; sem uma caixa de e-mail real, o login não conclui.
3. Base da API: `https://<instancia>.n7.xano.io/api:<grupo>/<rota>`, com `Authorization: Bearer <token>`.
   O identificador de cada grupo está no arquivo `xano-workspace/api/<grupo>/<grupo>.xs` (campo
   `canonical`). Limite do plano gratuito: 10 requisições a cada 20 segundos.

## 1. Entrar (tela e API)

- Na tela **Entrar**, informe e-mail e senha: o sistema envia um código de 6 dígitos ao e-mail. Informe o
  código e o início abre.
- Pela API: `POST auth/login` → `{aguardando_otp: true}`; `POST auth/otp/validar` → `{token}` (vale 1 hora).
- Esperado: senha errada 5 vezes bloqueia por 15 minutos; código errado 5 vezes exige novo login;
  conta com senha temporária só consegue trocar a senha.

## 2. Central de tarefas

`GET central_de_tarefas` com o token. Esperado: RH vê as filas de férias, documentos e desligamentos
pendentes; o Gestor vê só o próprio departamento e o painel da equipe; o Colaborador vê só as pendências
dele.

## 3. Cadastro e acesso (RH)

1. `POST colaboradores` (nome, CPF válido, e-mail, nascimento, cargo, departamento, contrato…).
2. `POST usuarios` com o `colaborador_id` e uma senha temporária. Esperado: conta criada; um menor de 18
   anos só ganha acesso com um documento de responsável legal aprovado.

## 4. Ponto e correção

1. Colaborador: `POST ponto/marcar` (entrada → intervalo → saída, nessa ordem).
2. `POST ponto/{id}/solicitar_correcao`; o **Gestor do departamento** (ou RH) decide em
   `POST correcoes_ponto/{id}/aprovar` ou `rejeitar`.
3. Esperado: quem pediu a correção **não** consegue aprová-la (403); o Gestor de outro departamento
   também não.

## 5. Férias

1. Colaborador: `POST ferias/solicitacoes`.
2. Gestor do departamento ou RH: `POST ferias/{id}/aprovar`. Esperado: uma segunda solicitação
   pendente é recusada; ninguém decide a própria solicitação; com delegação vigente, o substituto
   decide e a auditoria registra o titular.

## 6. Rotina diária e status

RH/Admin: `GET status_operacional` mostra o que a rotina aplicaria; `POST rotinas/processar_diarias`
aplica. Esperado: a contagem aplicada é a mesma do pendente, e uma segunda execução devolve tudo zerado.

## 7. Privacidade (LGPD)

- Colaborador: `GET meus_dados` (JSON ou CSV), `PATCH minhas_preferencias_privacidade`, e
  `POST solicitacoes` com tipo `privacidade_lgpd` (prazo de 15 dias).
- RH: `POST colaboradores/{id}/anonimizar` num colaborador desligado, sem documento em prazo de guarda.
  Esperado: nome, CPF, contato e dados bancários viram marcadores; nada é excluído.

## 8. Auditoria

RH/Admin: `GET auditoria`. Esperado: cada passo acima aparece com autor, ação e resultado, sem senha,
token nem dado pessoal inteiro.

## O que não aparece na demonstração

Upload de arquivo (o plano gratuito do Xano não suporta; documento entra por link), e as telas de
férias, ponto, documentos, perfil e demais áreas, que dependem do Figma.
