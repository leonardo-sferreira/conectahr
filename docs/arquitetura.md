# Arquitetura — ConectaRH

Visão de uma página para quem avalia ou entra no projeto. O detalhe das regras está em
[`regras-de-negocio.md`](regras-de-negocio.md), o modelo de dados em
[`domain-model.md`](domain-model.md) e as decisões em `openspec/changes/`.

## Visão geral

```
 Navegador ──► Frontend Streamlit ──HTTPS + Bearer──► API Xano (10 grupos) ──► Banco do Xano
              (frontend/)                              (xano-workspace/api)      (50 tabelas)
                                                           │
                                                           └──► Brevo (e-mail transacional)
```

- **Frontend (`frontend/`):** Streamlit. Só apresenta e coleta dados; **nunca decide** quem pode
  fazer o quê. Guarda o token em `st.session_state` e chama a API por `api_client.py`.
- **Backend (`xano-workspace/`):** Xano com XanoScript. Concentra regra de negócio, autorização,
  auditoria e persistência. Versionado como arquivos `.xs` (tabelas, funções, endpoints) e publicado
  pela CLI.
- **E-mail:** Brevo, para o código de acesso, a redefinição de senha e os avisos.
- **Design:** Figma é a fonte única das telas (ver `AGENTS.md`).
- **Especificação:** OpenSpec em `openspec/`. `specs/` consolida o comportamento; `changes/` é o
  plano em andamento; `changes/archive/` é o histórico.

## Autenticação e autorização

1. `POST auth/login` valida e-mail e senha e envia um **código de 6 dígitos** por e-mail (guardado
   como hash HMAC-SHA256 no banco, com um segredo de ambiente).
2. `POST auth/otp/validar` confere o código, cria uma **sessão** e emite o token (1 hora). Cada
   token carrega o id da sessão.
3. **Todo endpoint autenticado** repete a mesma guarda: recarrega o usuário, exige usuário ativo,
   senha já trocada e sessão do token ativa, não revogada e não expirada. Desativar um usuário,
   desligar um colaborador ou "encerrar outras sessões" revoga as sessões.
4. A autorização por **perfil** (Admin, RH, Gestor, Colaborador) e por **escopo** (departamento do
   Gestor, dono do registro, delegação vigente) é aplicada no backend, endpoint a endpoint. Ninguém
   decide uma solicitação em que é o próprio colaborador.

`tools/checar_endpoints.py` confere a guarda em todos os endpoints.

## Grupos de API

Os 10 grupos refletem a ordem histórica de criação (ver tabela no README): autenticação, gestão de
usuários, colaboradores (o maior), departamentos, cargos, ponto, férias, ausências, documentos e
desligamentos. O versionamento é pelo grupo de API: uma mudança incompatível cria um grupo novo, em
vez de um prefixo `/v1/` nas rotas.

## Padrões que se repetem

- **Auditoria inline:** toda escrita grava `auditoria` com autor, ação, recurso e resultado, com
  dados pessoais mascarados.
- **"Registra e depois falha":** tentativa bloqueada (ex.: autoaprovação) deixa rastro antes de falhar.
- **Append-only:** banco de horas, check-ins e histórico profissional não são editados nem apagados.
- **Outbox de e-mail:** e-mail assíncrono vai para `email_outbox` com chave de idempotência.
- **Rotina manual:** o plano gratuito do Xano não tem tarefas agendadas; o que depende de data é
  acionado por RH/Admin em `rotinas/processar_diarias`, e `status_operacional` mostra o pendente.
- **Motor de regras:** a regra de jornada, banco de horas e férias vem da matriz de contrato, que
  pode ser sobrescrita por norma legal, instrumento coletivo ou exceção individual
  (`ConectaHR/resolver_regra`), sempre com histórico da regra aplicada.

## Proteção de dados (LGPD)

Registro de operações, aviso de privacidade, RIPD, operadores, teste de legítimo interesse, plano
de incidentes e política de retenção estão em [`docs/lgpd/`](lgpd/). No sistema: dados sensíveis em
campos privados, mascaramento na auditoria, anonimato da pesquisa de clima por agregação, mínimo de
pessoas nos indicadores, exportação dos dados do titular, preferências de privacidade, anonimização
de colaborador desligado e regras para menores de 18 anos.

## Limites conhecidos

- Plano gratuito do Xano: 10 requisições a cada 20 segundos, sem tarefas agendadas e **sem upload de
  arquivo privado** (documento entra por link de domínio aprovado; o atestado não é guardado).
- Bases legais e prazos de guarda são sugestões, "a confirmar com o jurídico".
- O ponto do MVP é controle interno experimental, sem certificação (ver [`backlog-rep.md`](backlog-rep.md)).
