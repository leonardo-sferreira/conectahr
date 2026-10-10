# Registro das operações de tratamento de dados pessoais

**Referência:** LGPD (Lei nº 13.709/2018), arts. 7º, 11 e 37.
**Situação:** análise técnica de projeto acadêmico. **Bases legais e prazos de guarda são sugestões, "a confirmar com o jurídico"** até haver validação formal.
**Fonte única:** este é o documento de partida da LGPD no projeto. O aviso de privacidade, o relatório de impacto, a lista de operadores, o teste de legítimo interesse e a política de retenção citam as finalidades pelo código (F01, F02…). Ao mudar uma finalidade aqui, revise os outros.

**Agente de tratamento (controlador):** a empresa que usa o ConectaRH. **Operadores:** ver [operadores.md](operadores.md). **Encarregado:** ver [aviso-de-privacidade.md](aviso-de-privacidade.md), seção "Fale com o encarregado".

## Como ler a tabela

- **Sensível?** indica dado pessoal sensível (art. 11), como saúde.
- **Quem acessa** vale para o backend: a regra é sempre aplicada no servidor, e a tela só reflete o resultado. "Próprio" é o titular dos dados; "RH" e "Admin" são os perfis administrativos; "Gestor" vê só a própria equipe.
- **Prazo de retenção** é uma sugestão a confirmar. Nada é apagado fisicamente: no fim do prazo, os dados pessoais são **anonimizados** (tarefa de retenção, ainda pendente).

## Operações de tratamento

| Cód. | Finalidade | Dados | Titular | Sensível? | Base legal (a confirmar) | Quem acessa | Operador | Prazo de retenção (a confirmar) | Medidas de segurança |
|---|---|---|---|---|---|---|---|---|---|
| F01 | Autenticação e controle de sessão | Nome, e-mail, senha (hash), código de acesso, tentativas de login, datas de acesso; **IP e dispositivo de cada login** (gravados em `sessao` desde 10/10/2026, tarefa 70) | Todo usuário | Não | Execução de contrato (art. 7º, V) e legítimo interesse em segurança (art. 7º, IX) | Próprio; RH e Admin (sessões na auditoria) | Xano; Brevo (envio do código) | Conta: enquanto ativa. IP e dispositivo: 6 meses | Senha em hash; código com validade curta e limite de tentativas; sessão ligada ao token; bloqueio por tentativas |
| F02 | Auditoria e prestação de contas | Quem fez o quê, quando, valores anteriores e novos (mascarados); a tabela tem campo de IP, que hoje não é preenchido | Todo usuário e colaborador | Não | Legítimo interesse (art. 7º, IX) e dever de segurança (art. 46) | RH e Admin | Xano | Prazo longo, a confirmar (a auditoria não é apagada) | Somente leitura; dados pessoais mascarados nos valores; acesso por perfil |
| F03 | Cadastro e identificação do colaborador | Nome, **CPF**, e-mail pessoal, telefone, endereço, data de nascimento | Colaborador | Não (risco alto) | Execução de contrato (art. 7º, V) e obrigação legal (art. 7º, II) | Próprio, RH, Admin. Organograma, busca e aniversariantes mostram só parte (ver F14) | Xano | Vínculo + prazo legal trabalhista | Escopo por perfil e propriedade; CPF validado localmente, sem API externa |
| F04 | Documentos pessoais e obrigatórios | RG, CPF, CNH, CTPS, reservista, documentação migratória, **responsável legal** (menores), comprovantes | Colaborador | Não (risco alto) | Obrigação legal (art. 7º, II) | Próprio, RH, Admin | Xano (armazenamento do arquivo) | Prazos legais por tipo (a confirmar) | Armazenamento privado; quarentena e verificação do arquivo; sem exclusão física |
| F05 | Remuneração e pagamento | Salário, **banco, agência, conta, dígito**, holerite, informe de rendimentos | Colaborador | Não (risco alto) | Execução de contrato e obrigação legal | Próprio, RH, Admin. **Nunca o Gestor** | Xano | Prazo legal trabalhista e fiscal (a confirmar) | Campos privados; dados bancários mascarados na auditoria |
| F06 | Contrato, cargo e carreira | Cargo, departamento, histórico profissional, contrato específico, regras aplicadas | Colaborador | Não | Execução de contrato e obrigação legal | RH, Admin; parte para o próprio | Xano | Vínculo + prazo legal | Histórico sem exclusão; alterações auditadas |
| F07 | Controle de jornada | Marcações de ponto, correções, banco de horas | Colaborador | Não (risco alto: monitora o trabalhador) | Obrigação legal (CLT, art. 74) | Próprio, Gestor da equipe, RH, Admin | Xano | Prazo legal trabalhista (a confirmar) | Ordem estrita de marcação; correção decidida por outra pessoa; auditoria |
| F08 | Férias | Período, status, observações | Colaborador | Não | Obrigação legal e execução de contrato | Próprio, Gestor da equipe (decisão), RH, Admin | Xano | Prazo legal trabalhista | Ninguém decide a própria solicitação |
| F09 | Ausências e atestados | Tipo, período, **motivo (lista fechada)**; o arquivo do atestado **não é guardado no sistema** | Colaborador | **Sim** (saúde) | Obrigação legal (art. 11, II, "a") | Próprio, RH, Admin. **Gestor vê só tipo, período e status** | Xano (armazenamento do arquivo) | Prazo legal (a confirmar) | Arquivo privado; Gestor sem acesso ao atestado; ver RIPD |
| F10 | Saúde e segurança do trabalho (SST) | Tipo de evento, **resultado do ASO**, médico responsável, documento; laudo de deficiência | Colaborador | **Sim** (saúde) | Obrigação legal: NR-7, eSocial e cota de PcD (art. 11, II, "a") | RH e Admin (laudo: também o próprio) | Xano | Longo, definido por norma (a confirmar) | Só metadados operacionais, nunca prontuário; acesso restrito; ver RIPD |
| F11 | Desligamento | Solicitação, motivo, decisão, data efetiva | Colaborador | Não | Execução de contrato e obrigação legal | Próprio (a sua), Gestor (da equipe), RH, Admin | Xano | Prazo legal trabalhista | Decisão por outra pessoa; conta desativada e sessões revogadas |
| F12 | Avaliação e desenvolvimento | Avaliações, respostas, metas, check-ins, PDI, contestações, reuniões individuais | Colaborador | Não | Legítimo interesse (art. 7º, IX); ver [legitimo-interesse.md](legitimo-interesse.md) | Participantes e RH; feedback privado só do autor e do RH | Xano | Ciclo + prazo a confirmar | Revisão humana; nenhuma decisão automática de promoção ou punição |
| F13 | Reconhecimento (mural) | Mensagem de reconhecimento, remetente, destinatário | Colaborador | Não | Legítimo interesse (art. 7º, IX) | **Todos os colaboradores** (mural público) | Xano | Prazo a confirmar | Só reconhecimento positivo; moderação; opção de sair do mural |
| F14 | Aniversariantes do mês | Nome e dia/mês de nascimento | Colaborador | Não | Legítimo interesse (art. 7º, IX) | Todos os colaboradores | Xano | Enquanto vínculo | Só dia e mês; opção de sair da lista |
| F15 | Pesquisa de clima (anônima) | Nota por pergunta e departamento; participação separada | Colaborador | Não (se anônima) | Legítimo interesse (art. 7º, IX) | RH e Admin, **só o agregado** | Xano | Agregado: prazo a confirmar | Resposta gravada só como contagem; grupo abaixo do mínimo suprimido; ver limitação conhecida no RIPD |
| F16 | Solicitações ao RH, comunicados e notificações | Descrição e decisão da solicitação, notificações internas, preferências | Colaborador | Não | Execução de contrato e legítimo interesse | Próprio e RH; comunicados conforme o público | Xano | Prazo a confirmar | Escopo por propriedade |
| F17 | Envio de e-mail transacional | Nome, e-mail, conteúdo da mensagem (código, avisos) | Usuário | Não | Execução de contrato e legítimo interesse | Sistema; RH e Admin processam a fila | **Brevo** | Mensagens enviadas: 6 a 12 meses (a confirmar) | Fila com chave de idempotência; avisos de segurança não podem ser desativados |
| F18 | Regras e conformidade trabalhista | Instrumentos normativos, regras e exceções por contrato, regra aplicada a cada colaborador | Colaborador (vínculo) | Não | Obrigação legal (art. 7º, II) | RH e Admin | Xano | Prazo legal | Aprovação por outra pessoa; versionamento |
| F19 | Onboarding, documentos pendentes e delegações | Etapas e responsáveis, pendências de documento, delegações de aprovação | Colaborador, Gestor | Não | Execução de contrato | Próprio, Gestor, RH, Admin | Xano | Prazo a confirmar | Delegação com vigência e bloqueio de autodelegação |

## Decisão de minimização

O sistema **não coleta nem armazena** raça, sexo, religião, filiação sindical ou biometria. Nenhuma funcionalidade do escopo precisa desses dados. Criar qualquer campo desse tipo exige atualizar este registro e o [RIPD](ripd.md) antes.

## Cobertura: todas as 49 tabelas

A tabela abaixo liga cada tabela do Xano (`xano-workspace/table/`) a uma finalidade. "Sem dado pessoal" significa que a tabela guarda só regras, catálogos ou conteúdo geral.

| Tabela | Finalidade | Tabela | Finalidade |
|---|---|---|---|
| `artigo_faq` | Sem dado pessoal | `onboarding` | F19 |
| `auditoria` | F02 | `onboarding_item` | F19 |
| `ausencia` | F09 | `parametro_protegido` | Sem dado pessoal |
| `avaliacao` | F12 | `pdi` | F12 |
| `banco_horas_lancamento` | F07 | `pendencia_documento` | F19 |
| `cargo` | Sem dado pessoal | `pergunta_clima` | Sem dado pessoal |
| `ciclo_avaliacao` | Sem dado pessoal | `pesquisa_clima` | Sem dado pessoal |
| `colaborador` | F03, F05, F14 | `preferencia_notificacao` | F16 |
| `competencia_avaliacao` | Sem dado pessoal | `reconhecimento` | F13 |
| `comunicado` | F16 | `registro_ponto` | F07 |
| `contestacao_avaliacao` | F12 | `regra_aplicada` | F18 |
| `contrato_especifico` | F06 | `regra_contrato` | Sem dado pessoal |
| `correcao_ponto` | F07 | `regra_override` | Sem dado pessoal |
| `delegacao_aprovacao` | F19 | `resposta_avaliacao` | F12 |
| `departamento` | Sem dado pessoal | `resposta_clima` | F15 (legado, não é mais lida) |
| `documento` | F04, F05 | `resposta_clima_agregado` | F15 |
| `documento_obrigatorio_regra` | Sem dado pessoal | `resposta_clima_participacao` | F15 |
| `email_outbox` | F17 | `reuniao_individual` | F12 |
| `evento_sst` | F10 | `sessao` | F01 |
| `feriado` | Sem dado pessoal | `solicitacao_desligamento` | F11 |
| `ferias` | F08 | `solicitacao_rh` | F16 |
| `historico_gestor_departamento` | F06 | `user` | F01 |
| `historico_profissional` | F06 | `instrumento_normativo` | F18 |
| `meta_avaliacao` | F12 | `meta_checkin` | F12 |
| `notificacao_interna` | F16 | | |

## Pendências conhecidas

- **Prazos de retenção** ainda são sugestões. A política por categoria (`retencao.md`) é uma tarefa pendente.
- **Região onde o Xano guarda os dados** e **criptografia em repouso**: a confirmar no painel do Xano, ver [operadores.md](operadores.md).
- **Respostas de clima antigas** (`resposta_clima`) continuam no banco, sem ser lidas por nenhum endpoint. A decisão sobre anonimizá-las fica registrada no [RIPD](ripd.md).
