# Evidências de teste

Esta pasta guarda o resultado das verificações do ConectaRH: testes de integração, testes de
segurança, auditoria e as evidências de cada lote de tarefas. É a pasta que o README e a entrega
final apontam como "evidências de testes".

## Regras (o repositório é público)

Evidência é versionada e visível a qualquer pessoa, então **não entra**:

- nome, e-mail, CPF, telefone, endereço, dados bancários ou salário de pessoa real;
- senha, token (`Bearer ...`), código de acesso, chave de serviço ou segredo de ambiente;
- exportação do banco (`xano workspace pull --records`) nem trecho dela;
- print de tela com dado pessoal.

Como escrever:

- Contas aparecem **pelo papel** ("Admin", "conta de teste A, perfil Colaborador"), nunca pelo
  e-mail. Quando for preciso um e-mail, usar um mascarado (`l***@exemplo.com`).
- Ids de registro só se forem de dado de teste.
- Cada linha diz o **cenário**, a **requisição**, o **esperado** e o **obtido**. Um teste que
  deveria falhar entra com o resultado de falha.
- Nunca colar a resposta inteira de uma API: só os campos que provam o resultado.
- Antes de commitar, conferir a pasta com
  `grep -rnE "[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|Bearer [A-Za-z0-9]|eyJ" docs/evidencias`;
  só devem sobrar exemplos fictícios.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `testes-integracao.md` | Testes de integração por HTTP: autenticação, autorização, ponto, férias, documentos, e-mail e avaliação |
| `testes-seguranca.md` | Testes de segurança: credenciais, tokens, código de acesso, uploads, logs e feedback privado |
| `auditoria.md` | Levantamento da auditoria obrigatória dos endpoints de ação |
| `seguranca.md` | Evidências da Parte 1 da `concluir-mvp-conectarh` (sessão no token, guarda de acesso, revogação) |
| `lgpd.md` | Evidências da adequação à LGPD (mascaramento, auditoria de arquivos, dados de saúde, hash dos códigos) |
| `rotinas-e-fluxos.md` | Evidências da Parte 2: Gestor e delegação, rotina diária, ciclo, clima, equipe, retenção |
| `backup.md` | Backup de código e schema e a restauração (pendente) |
| `smoke-final.md` | Teste final por perfil (Admin, RH, Gestor e Colaborador) |
| `frontend-login-f01.md` | Fluxo de entrada do frontend (Figma F01): casos, estados de UI e prints lado a lado em `frontend-f01/` |
| `frontend-onboarding.md` | Onboarding do primeiro acesso, "Meu onboarding" e o card do Início (tarefa 68) |

## Checklist antes de cada commit nesta pasta

- [ ] Nenhum nome, e-mail, CPF, telefone, endereço, conta bancária ou salário de pessoa real.
- [ ] Nenhuma senha, token, código de acesso ou chave de serviço (nem parcial).
- [ ] Contas citadas pelo papel; e-mail, quando indispensável, mascarado.
- [ ] Respostas de API reduzidas aos campos que provam o resultado.
- [ ] A varredura abaixo não achou dado real:
  `grep -rnE "[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|Bearer [A-Za-z0-9]|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}" docs/evidencias`
  (os exemplos fictícios que sobram são aceitos, como o e-mail de injeção de teste em `testes-seguranca.md`).

Limite do plano gratuito do Xano: 10 requisições a cada 20 segundos (HTTP 429). Os testes
automatizados esperam entre as chamadas.
