# Testes de integração — ConectaRH

Registro dos testes de integração executados contra o backend real (Xano, workspace de
produção), via chamadas HTTP autenticadas com tokens reais obtidos pelo fluxo de login
completo (senha + OTP por e-mail). Cobre autenticação, autorização, ponto, férias,
documentos, e-mail e avaliação, incluindo isolamento entre departamentos e perfis
(item 7.2).

## Como reexecutar

Não há suíte automatizada de ponta a ponta: o login do ConectaRH exige um código OTP de
6 dígitos enviado por e-mail a cada tentativa (por design — ver `spec.md`, "Autenticação
por código"), o que impede automação sem um humano no loop para ler o código. O Xano
também oferece testes nativos (`unit_test`/`workflow_test`), mas só podem ser criados
pela interface web — não há comando de criação na CLI usada neste projeto.

Para reexecutar manualmente: `POST auth/login` com e-mail/senha → ler o código OTP no
e-mail cadastrado → `POST auth/otp/validar` → usar o `token` retornado como
`Authorization: Bearer <token>` (válido por 1h) nas chamadas seguintes. Contas de teste
usadas nesta rodada: uma conta RH, uma segunda conta RH (necessária para testar
aprovações que bloqueiam autoaprovação) e uma conta Colaborador/PJ (necessária para
testar fluxos de autoatendimento e o bloqueio de férias para PJ).

## 1. Autenticação

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Login com senha correta | Retorna `aguardando_otp: true` e envia código por e-mail | ✅ |
| Validação de OTP correto | Retorna token Bearer válido por 3600s | ✅ |
| Reenvio de OTP | Gera novo código, invalida o anterior | ✅ |
| Troca de senha obrigatória no primeiro acesso | Bloqueia ações funcionais até `auth/senha` PATCH ser chamado | ✅ |
| Esqueci minha senha | Envia código de redefinição sem revelar se o e-mail existe | ✅ |
| Redefinir senha com código inválido | Bloqueia com `accessdenied`, sem consumir o código real | ✅ |
| Redefinir senha com código correto | Redefine e permite login com a nova senha | ✅ |
| `auth/me` | Retorna identidade do token atual | ✅ |
| Listar minhas sessões | Retorna sessões ativas e encerradas do usuário autenticado | ✅ |
| Logout | Encerra a sessão mais recente; token JWT continua criptograficamente válido até expirar (limitação documentada em `logout_POST.xs`) | ✅ |
| Encerrar outras sessões | Preserva a mais recente, encerra as demais | ✅ |
| Encerrar sessão específica | Só o dono pode encerrar; tentativa de encerrar sessão de outro usuário é negada | ✅ |

## 2. Autorização e isolamento entre perfis/departamentos

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| RH/ADMIN agindo sobre qualquer colaborador | Permitido nos endpoints administrativos | ✅ |
| Colaborador tentando ação exclusiva de RH | Negado (`accessdenied`) | ✅ |
| Autoaprovação em `instrumentos_normativos`/`regras_override` | Bloqueada — quem cria não pode aprovar; segunda conta RH aprova com sucesso | ✅ |
| Colaborador solicitando desligamento de outro colaborador | Negado — só o próprio desligamento é permitido | ✅ |
| Gestor solicitando desligamento fora do próprio departamento | Negado (verificado por leitura de código; mesmo padrão de escopo usado e confirmado em outros endpoints) | código revisado |
| Onboarding: concluir item fora do próprio papel de responsável | Restrito ao perfil/relação correta (`rh`/`colaborador`/`gestor`) | ✅ |
| Comunicado com público-alvo por departamento | Visível só para colaboradores do departamento informado | ✅ |

## 3. Ponto

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Ciclo completo: entrada → início/fim de intervalo → saída | Calcula `horas_trabalhadas` corretamente, status final `Completo` | ✅ |
| Intervalo mínimo (regra CLT) violado | Bloqueia o fim do intervalo antes do mínimo | ✅ |
| Solicitar correção de marcação | Registra `valor_original` e `valor_solicitado`, status `pendente` | ✅ |
| Aprovar correção | Aplica o novo valor, status `aprovada` | ✅ |
| Rejeitar correção | Mantém o valor original, status `rejeitada` | ✅ |
| Banco de horas — tipo de contrato sem permissão | Bloqueado pela matriz `regra_contrato.permite_banco_horas` (nenhum tipo seedado permite por padrão — comportamento intencional) | ✅ |

## 4. Férias

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Solicitação dentro da antecedência mínima | Aceita | ✅ |
| Solicitação abaixo da antecedência mínima | Bloqueada | ✅ |
| Quantidade de dias acima do limite proporcional acumulado | Bloqueada | ✅ |
| Fracionamento: 2º e 3º período após aprovação do anterior | Aceito enquanto abaixo do `maximo_periodos` da matriz | ✅ |
| Tentativa de novo período com um pendente | Bloqueada — só uma solicitação pendente por vez | ✅ |
| 4º período além do máximo permitido | Bloqueado | ✅ |
| Bloqueio de férias para PJ | Negado — `permite_solicitacao_ferias` da matriz | ✅ |
| Verificação de conflito de agenda | Endpoint dedicado testado (código revisado e exercitado) | ✅ |
| Aprovar/rejeitar/cancelar solicitação | Transições de status corretas | ✅ |

## 5. Documentos

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Upload com `arquivo_url`, hash calculado (`md5`) | Documento criado com `hash_arquivo` preenchido | ✅ |
| Upload duplicado (mesmo link, mesmo colaborador) | Bloqueado por duplicidade | ✅ |
| Quarentena — extensão não permitida (ex.: `.exe`) | `estado_verificacao: bloqueado`, com motivo | ✅ |
| Quarentena — arquivo válido e acessível | `estado_verificacao: liberado` | ✅ |
| Aprovar documento bloqueado na quarentena | Negado, expõe o motivo do bloqueio | ✅ |
| Substituir arquivo bloqueado por um válido (PATCH) | Reprocessa a verificação e libera | ✅ |
| Aprovar / arquivar / rejeitar documento | Transições de status corretas | ✅ |
| `documentos/{id}` e `ausencias/{id}` DELETE | Bloqueado permanentemente por design (`precondition(false)`) | ✅ |
| Processar vencimentos — documento já vencido | Transiciona para `vencido`, dispara alerta "venceu hoje" | ✅ |
| Processar vencimentos — reexecução no mesmo dia | Idempotente, não duplica alerta | ✅ |
| Documentos obrigatórios e pendências | Criação de pendência com prazo futuro válido; prazo passado bloqueado | ✅ |

## 6. E-mail e notificações

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Fila de e-mail (`email_outbox`) processada | Envia via Brevo, marca como `enviado` | ✅ |
| Notificação interna criada junto com evento de negócio | Aparece em `minhas_notificacoes` | ✅ |
| Marcar notificação como lida | Atualiza `lida`/`lida_em` | ✅ |
| Redefinição de senha por e-mail | Código real recebido e validado (ver seção 1) | ✅ |

## 7. Avaliação de desempenho

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Registrar resposta de avaliação por competência | Nota registrada | ✅ |
| Enviar avaliação | Calcula a nota final como média das respostas | ✅ |
| Contestar avaliação enviada | Abre contestação sem alterar a avaliação original | ✅ |
| Revisar contestação (RH) | Registra resposta da revisão | ✅ |
| Check-in de meta | Preserva progresso, comentário, evidência, histórico | ✅ |
| Concluir meta | Registra resultado final | ✅ |
| Progresso de PDI até 100% | Conclui automaticamente | ✅ |
| Pesquisa de clima: resposta duplicada | Bloqueada (uma resposta por colaborador por pergunta) | ✅ |
| Pesquisa de clima: resultado abaixo do mínimo de respostas | Não exibido (verificado com o mínimo atingido corretamente) | ✅ |

## 8. Desligamento

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Colaborador solicita o próprio desligamento | Aceito | ✅ |
| Colaborador tenta solicitar desligamento de outro | Bloqueado | ✅ |
| Cancelar solicitação própria pendente | Aceito | ✅ |
| Iniciar análise, aprovar (imediato) | Conclui na hora, desativa acesso, encerra histórico profissional | ✅ |
| Iniciar análise, aprovar (aviso prévio) | Agenda para a data efetiva, sem concluir imediatamente | ✅ |
| Concluir manualmente antes da data efetiva | Bloqueado | ✅ |
| Concluir manualmente após a data efetiva | Conclui, desativa acesso | ✅ |
| Rejeitar solicitação em análise | Status `rejeitada`, colaborador não é afetado | ✅ |

## 9. Conformidade normativa

| Cenário | Resultado esperado | Status |
| --- | --- | --- |
| Instrumento coletivo com dados MTE reais | Aprovado por segunda conta RH, fica `vigente` | ✅ |
| Instrumento com formato MTE inválido | Bloqueado com mensagem de formato esperado | ✅ |
| Suspender / revogar instrumento vigente | Transições de status corretas | ✅ |
| Rejeitar instrumento pendente | Status `rejeitado` | ✅ |
| Regra de override: criação, envio, aprovação por 2ª conta | Autoaprovação bloqueada; segunda conta aprova e a regra fica `vigente` | ✅ |
| Nova versão da mesma regra (mesmo parâmetro/escopo) | Encerra a versão anterior automaticamente | ✅ |
| Resolução (`resolver_regra`) com override vigente | Aplica o override no nível correto (exceção individual), sem falso conflito | ✅ |

## 10. Outros módulos

Reconhecimentos (envio, mural público, moderação), pesquisa de clima (perguntas,
respostas anônimas, agregação), comunicados, FAQ, onboarding (checklist de 13 itens,
conclusão por responsável), delegações de aprovação (bloqueio de autodelegação),
dados bancários, solicitações gerais ao RH (atender/indeferir), escalonamento de
pendências atrasadas (com idempotência) — todos testados via HTTP real, sem bugs
encontrados.

## Bugs encontrados e corrigidos durante esta rodada de testes

Detalhes completos na memória do projeto (`conectahr_xano_platform_quirks`). Resumo:

- Opcionalidade de campo em input de query precisa de `?` duplo (`tipo? nome?`), não
  simples — corrigido em 28 arquivos.
- Coluna `documento.estado_de_emissao` com `NOT NULL` real que a declaração `?` do
  schema não remove — corrigido no nível da query (coalesce/preservação).
- `db.get` com `field_value` nulo quebra em vez de retornar "não encontrado" — corrigido
  em `usuarios_POST.xs` (criação de acesso para colaborador nunca vinculado).
- Comparação de `date` contra `"now"` faz comparação de texto, não de data — corrigido
  em `pendencias_documento_POST.xs` e na conclusão de desligamento agendado.
- `0`, `""` e `false` são tratados como iguais a `null` em `==`/`!=` — corrigido no
  alerta de vencimento de documento e na ordem de pergunta de pesquisa de clima.

## Limitações conhecidas desta rodada

- Sem suíte automatizada executável por CI: depende de OTP real por e-mail a cada login.
- Testes de fluxos que exigem uma segunda conta com perfil diferente (autoaprovação,
  colaborador solicitando o próprio desligamento) dependeram de contas de teste criadas
  especificamente para esta rodada, vinculadas a e-mails reais fornecidos pelo usuário.
- Não cobre carga/performance nem testes de segurança dedicados (força bruta, injeção,
  fuzzing) — isso é o escopo da tarefa 7.3, não desta.
