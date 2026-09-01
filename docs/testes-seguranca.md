# Testes de segurança — ConectaRH

Testes de segurança executados contra o backend real (item 7.3): credenciais, tokens,
código de acesso de login (OTP), uploads, logs/auditoria e feedback privado — com foco
em confirmar que nenhum segredo ou documento é exposto indevidamente.

## Credenciais

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Senha nunca retorna em nenhuma resposta de API (`usuarios`, `usuarios/{id}`, `auth/me`) | Campo `senha` ausente em todas as respostas verificadas | ✅ |
| Mensagem de erro de login não revela se o e-mail existe | `"E-mail ou senha inválidos."` idêntica para e-mail inexistente e senha errada | ✅ |
| Login com formato de e-mail malicioso (`admin' OR '1'='1@teste.com`) | Rejeitado por validação de formato antes de qualquer consulta | ✅ |
| **Rate limit de tentativas de senha** — achado corrigido nesta rodada, ver abaixo | Bloqueio temporário após tentativas repetidas | ✅ (corrigido) |

## Tokens

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Token adulterado (último caractere alterado) | Rejeitado (`Invalid token.`) | ✅ |
| Token ausente | Rejeitado (`Unauthorized - Authentication Required`) | ✅ |
| Token com string arbitrária | Rejeitado (`Invalid token.`) | ✅ |
| Token expirado (1h) | Rejeitado (`This token is expired.`), observado organicamente diversas vezes ao longo da sessão | ✅ |
| IDOR — Colaborador tentando acessar dados de outro colaborador via `colaboradores/{id}` | Bloqueado (`accessdenied`) | ✅ |
| `meu_perfil_colaborador` retorna somente o próprio registro do token | Confirmado — sempre o `colaborador_id` do token, nunca outro | ✅ |

## Código de acesso de login (OTP)

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Código nunca retorna na resposta de `auth/login` ou `auth/otp/reenviar` | Resposta contém só `aguardando_otp`/mensagem, nunca o código | ✅ |
| Código inválido | Rejeitado, incrementa `otp_tentativas` | ✅ |
| Bloqueio após 5 tentativas inválidas | Exige novo login | ✅ (validado em sessão anterior) |
| Expiração em 5 minutos | Confirmado pelo campo `otp_expira_em` | código revisado |

## Uploads (quarentena de arquivos — ver também item 5.7)

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Extensão perigosa (`.exe`) | Bloqueada antes da liberação | ✅ |
| Imagens (`imagem_frente`/`imagem_verso`) armazenadas como `access: "private"` | Confirmado por leitura de código (`storage.create_image`) | código revisado |
| Documento bloqueado não pode ser aprovado/usado | Confirmado (ver `docs/testes-integracao.md`) | ✅ |

## Logs e auditoria

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Nenhum `db.add auditoria` no código grava senha/token/código OTP | Confirmado por varredura estática em todo `api/` | ✅ |
| Injeção de SQL em campo de texto livre (busca de colaboradores, título de comunicado) | Tratado como texto literal, sem efeito no banco; tabela `user` permanece íntegra | ✅ |
| Consulta direta à tabela de auditoria | **Gap encontrado**: não existe endpoint GET para consultar `auditoria` — os registros são gravados mas não há como lê-los pela API hoje. Relevante para a tarefa 7.11 (auditoria formal), não corrigido nesta rodada. | gap documentado |

## Feedback privado

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Gestor envia feedback privado a colaborador do próprio departamento | Gravado com `visibilidade: "privado"` | ✅ |
| Feedback privado no mural público (`mural_reconhecimento`) | Ausente — mural retorna vazio, sem o registro privado | ✅ |
| Feedback privado em `meus_reconhecimentos_recebidos` do destinatário | Presente — o próprio destinatário consegue ver | ✅ |

## Achado corrigido: ausência de rate limit no login por senha

**Problema:** `auth/login` verificava a senha sem qualquer limite de tentativas — só o
código OTP subsequente tinha bloqueio (5 tentativas). Um atacante com um e-mail
conhecido podia tentar senhas indefinidamente sem ser bloqueado, mesmo que não
conseguisse passar do OTP no final.

**Correção aplicada:** dois campos novos em `user` (`senha_tentativas_invalidas`,
`senha_bloqueada_ate`), mesmo padrão já usado para OTP e redefinição de senha.
`auth/login` agora:
- Bloqueia (`toomanyrequests`) por 15 minutos após 5 tentativas de senha inválidas
  seguidas, mesmo com a senha correta na tentativa que estaria dentro da janela de
  bloqueio.
- Zera o contador ao acertar a senha antes de atingir o limite.
- Registra em auditoria cada tentativa de senha inválida (`login_senha_invalida`),
  nunca a senha em si.

**Verificado ao vivo** com contas de teste descartáveis (para não bloquear as contas
de teste principais usadas no restante da sessão): 5 tentativas erradas seguidas
bloqueiam a 6ª tentativa mesmo com a senha certa; uma conta separada, com 2 tentativas
erradas seguidas de uma correta, teve o contador zerado e o login prosseguiu
normalmente.

## Limitações desta rodada

- Não cobre teste de carga/DoS nem fuzzing sistemático de payloads.
- Não testa infraestrutura (TLS, headers HTTP de segurança, CORS) — fora do alcance do
  XanoScript nesta camada.
- O gap de "sem endpoint de consulta de auditoria" fica registrado, não corrigido — é
  escopo mais próximo da tarefa 7.11.
