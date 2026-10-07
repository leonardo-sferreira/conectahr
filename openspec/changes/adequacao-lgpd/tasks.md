# Tasks

Convenções:
- Commit: `<descrição> (<tarefa>)`, com Pull Request para `master`.
- Push no Xano: `python tools/checar_endpoints.py` → `xano workspace push --dry-run -p ConectaRH` → push → `pull` e diff limpo.
- Evidências: vão para `docs/evidencias/lgpd.md`, sem nome, CPF, e-mail ou token completo (regra da 4.6).
- Bases legais e prazos: "a confirmar com o jurídico" até haver validação.

## 1. Documentação e governança (Parte 1, só documentos)

- [ ] 1.1 Criar `docs/lgpd/registro-de-operacoes.md` (arts. 7, 11 e 37), com uma linha por finalidade. Colunas: finalidade, dados, titular, base legal, quem acessa, operador, prazo de retenção e medidas de segurança. O ponto de partida é o inventário do proposal. Verificar: toda tabela de `xano-workspace/table/` com dado pessoal aparece em pelo menos uma linha, conferido com uma lista das 49 tabelas anexada ao documento.
- [ ] 1.2 Criar `docs/lgpd/aviso-de-privacidade.md` (arts. 6, VI, e 9), em linguagem simples, com:
  - dados coletados e por quê;
  - compartilhamento com os operadores da 1.6;
  - prazos de guarda;
  - direitos do titular e como exercê-los;
  - registro de IP e dispositivo no login e na auditoria;
  - contato do encarregado.

  Verificar: cada finalidade da 1.1 é citada no aviso.
- [ ] 1.3 Definir o encarregado (art. 41; Res. CD/ANPD 18/2024; sugestão: Matheus) e um e-mail de contato. Publicar no aviso da 1.2 e no `README.md`. Verificar: o mesmo contato aparece nos dois arquivos.
- [ ] 1.4 Criar `docs/lgpd/plano-de-incidentes.md` (art. 48; Res. CD/ANPD 15/2024), com:
  - quem detecta e quem avalia;
  - critérios de risco;
  - modelo de comunicação à ANPD e aos titulares em até 3 dias úteis;
  - registro interno de todo incidente;
  - ligação com os alertas de `docs/monitoramento.md`.

  Verificar: um incidente simulado (token vazado) percorre o plano do começo ao fim e fica registrado em `docs/evidencias/lgpd.md`.
- [ ] 1.5 Criar `docs/lgpd/ripd.md` (art. 38) para dados de saúde, adolescentes aprendizes e controle de jornada, com riscos, probabilidade, impacto e medidas. Incluir os riscos residuais do `design.md`: auditoria antiga com dados completos e, se for o caso, campos `image` públicos. Verificar: cada risco aponta para uma tarefa desta change ou da `corrigir-brechas-e-alinhar-documentacao`.
- [ ] 1.6 Criar `docs/lgpd/operadores.md` (arts. 33 a 39; Res. CD/ANPD 19/2024), com Xano, Brevo, hospedagem do Streamlit, GitHub e o serviço usado em `arquivo_url`. Para cada um: dados recebidos, região, termos de tratamento e mecanismo de transferência internacional. Verificar: todo domínio externo encontrado por `grep -rhoE "https://[a-z0-9.-]+" xano-workspace frontend README.md` está na lista ou é justificado como não recebedor de dados pessoais.
- [ ] 1.7 Criar `docs/lgpd/legitimo-interesse.md` (arts. 7, IX, e 10), com o teste de balanceamento para aniversariantes, mural de reconhecimento, pesquisa de clima e logs de segurança: finalidade, necessidade, expectativa do colaborador e salvaguardas, incluindo a oposição da 3.3. Verificar: cada linha da 1.1 com base em legítimo interesse tem seu teste.
- [ ] 1.8 Integrar a LGPD aos documentos do projeto:
  - registrar no `docs/regras-de-negocio.md` que os requisitos da seção 12 (delta desta change) passam a valer;
  - acrescentar ao `AGENTS.md` três regras: campo sensível novo atualiza a 1.1 e a 1.5; dados pessoais são mascarados em auditoria e logs; serviço externo novo atualiza a 1.6;
  - no `docs/project-overview.md` e no `openspec/config.yaml`, trocar a frase genérica sobre LGPD por um link para `docs/lgpd/`.

  Verificar: `openspec validate adequacao-lgpd` passa, e cada cenário da seção 12 tem tarefa correspondente (tabela cenário → tarefa anexada ao fim deste arquivo).

## 2. Ajustes no backend (Parte 2, antes da demonstração de dezembro)

- [ ] 2.1 Mascarar dados pessoais na auditoria (design L3):
  - em `meus_dados_bancarios PATCH`, mascarar agência, conta e dígito (ex.: `banco=341; agencia=****; conta=****1234`);
  - procurar no código todas as auditorias que gravam CPF, salário, telefone, endereço ou e-mail inteiros e aplicar a mesma regra, listando os endpoints alterados no commit.

  Verificar por HTTP: alterar dados bancários e cadastro de uma conta de teste e consultar `auditoria GET`. Nenhuma linha nova contém conta, CPF, salário, telefone, endereço ou e-mail completos.
- [ ] 2.2 Auditar a abertura de arquivos sensíveis (design L4): `acessar_arquivo_documento` em `documentos/{id}/arquivo GET`, na abertura do comprovante de ausência e na do documento de `evento_sst`. Se não houver endpoint de leitura, criar um, e retirar a URL do arquivo das listagens. Verificar por HTTP: cada abertura gera um evento com autor, recurso, registro e data, e as listagens não devolvem mais a URL.
- [ ] 2.3 Motivo da ausência sem diagnóstico (design L5):
  - adicionar `ausencia.motivo_tipo` (enum) com push isolado do schema;
  - tornar `ausencia.motivo` privado e sem novas gravações;
  - migrar os registros existentes com uma function idempotente (`motivo_tipo = "outro"`);
  - recusar código CID na observação.

  Verificar:
  - texto livre no motivo e `J11` na observação são recusados;
  - a migração, rodada duas vezes, não altera nada na segunda;
  - por HTTP com conta Gestor: nenhum endpoint acessível a ele devolve motivo, observação ou comprovante.
- [ ] 2.4 Links de arquivos controlados (design L6): `documento.arquivo_url` e `evento_sst.documento_url` aceitam só o armazenamento do Xano ou hosts de `$env.ARQUIVOS_DOMINIOS_APROVADOS`. Confirmar se os campos `image` (`ausencia.comprovante`, `documento.imagem_frente`) são privados; se forem públicos, corrigir nesta tarefa e registrar na 1.5. Verificar: um link público de drive é recusado com mensagem clara, e uma URL do armazenamento do Xano é aceita.
- [ ] 2.5 Códigos de acesso com hash (design L7):
  - spike: testar se o mecanismo de hash da senha funciona para um texto qualquer; senão, usar `|md5` com `$env.CODIGO_ACESSO_PEPPER` e o id do usuário; registrar o resultado no `design.md`;
  - aplicar em `auth/login`, `auth/otp/reenviar`, `auth/otp/validar`, `auth/senha/esqueci` e `auth/senha/redefinir`, num push separado, fora do horário de testes.

  Verificar:
  - `xano workspace pull --records` não mostra códigos de 6 dígitos em `otp_codigo` nem em `reset_senha_codigo`;
  - login com OTP e redefinição de senha continuam funcionando ponta a ponta;
  - o limite de 5 tentativas continua valendo.
- [ ] 2.6 Mínimo de pessoas nos indicadores (design L8): `indicadores GET` e `indicadores/exportar_csv GET` omitem grupos com menos de `$env.INDICADORES_MINIMO_PESSOAS` (padrão 5) e aplicam a supressão complementar do total. Verificar por HTTP: com dados de teste, um departamento com 2 pessoas não aparece na consulta nem no CSV, e o total some quando só um grupo é omitido.
- [ ] 2.7 Registrar no `design.md` (L13) e no `docs/regras-de-negocio.md` a dependência das tarefas 1.4 a 1.9 da `corrigir-brechas-e-alinhar-documentacao` e conferir o andamento delas. Verificar: os endpoints novos e alterados desta change passam no `python tools/checar_endpoints.py`.

## 3. Direitos do titular (Parte 3, endpoints e telas)

- [ ] 3.1 Criar `meus_dados GET` (art. 18, II e V; design L9), só para o próprio colaborador, com `formato=json|csv`. Inclui:
  - cadastro, contrato e histórico;
  - metadados de documentos;
  - férias, ausências, ponto e banco de horas;
  - avaliações, metas e PDI;
  - solicitações e notificações;
  - sessões.

  Não inclui respostas de clima nem dados de terceiros, e grava `exportar_meus_dados` na auditoria. Verificar por HTTP: o arquivo de uma conta de teste contém todas as categorias da 1.1 que se aplicam a ela, o evento aparece na auditoria e outra conta não consegue obter esses dados.
- [ ] 3.2 Pedidos LGPD na central de solicitações (arts. 18 e 19; design L9):
  - schema: `privacidade_lgpd` no enum `solicitacao_rh.tipo`, mais `subtipo_lgpd` e `prazo_resposta` (abertura + 15 dias);
  - alerta na `central_de_tarefas` do RH quando faltarem 3 dias ou menos;
  - resposta e decisão pelo `atender`/`indeferir`, já auditados.

  Verificar por HTTP: um pedido criado aparece na fila do RH com o prazo, o alerta aparece quando o prazo se aproxima (dados de teste) e a resposta gera notificação ao colaborador.
- [ ] 3.3 Preferências de privacidade (art. 18, § 2º; design L9): tabela `preferencia_privacidade` e endpoints `minhas_preferencias_privacidade GET/PATCH`. `colaboradores/aniversariantes` e `mural_reconhecimento` passam a respeitá-las. Verificar por HTTP: depois de sair das duas listas, o colaborador não aparece em nenhuma delas para outro usuário, e os reconhecimentos dele continuam visíveis para ele e para o RH.
- [ ] 3.4 Tela "Privacidade" (design L12):
  - desenhar no Figma (protótipo `fph1M5tB4rA4gqfIysSmkn`) antes de codar;
  - construir no Streamlit com aviso, "Baixar meus dados", formulário de pedido LGPD, preferências da 3.3 e contato do encarregado;
  - adicionar à tela Entrar um link para o aviso, legível sem login.

  Verificar:
  - prints lado a lado com o nó do Figma;
  - os 6 estados de UI (carregando, vazio, sucesso, erro, bloqueado, permissão negada);
  - o link da tela Entrar abre o aviso sem login;
  - a tela só mostra dados do próprio colaborador.

## 4. Retenção, anonimização e adolescentes (Parte 4, pós-MVP se não couber até dezembro)

- [ ] 4.1 Criar `docs/lgpd/retencao.md` com o prazo de guarda de cada categoria, marcado "a confirmar com o jurídico". Guarda longa para documentos trabalhistas, ASO e registros de SST; sugestão de 6 a 12 meses para IP e dispositivo de `sessao`, `email_outbox` enviado e códigos expirados. Ligar à regra de `documento.retencao_ate` (tarefa 2.13 da `corrigir-brechas`). Verificar: cada linha da 1.1 tem um prazo neste documento.
- [ ] 4.2 Incluir em `rotinas/processar_diarias` (pré-requisito: tarefa 2.4 da `corrigir-brechas`):
  - a limpeza de IP e dispositivo de sessões e de destinatário e corpo do `email_outbox` com prazo vencido;
  - a listagem ao RH dos desligados com prazo de guarda cumprido.

  A rotina é idempotente e auditada com contagens. Verificar por HTTP com dados de teste: a primeira execução limpa e conta, e a segunda devolve contagens zeradas.
- [ ] 4.3 Criar `colaboradores/{id}/anonimizar POST` (arts. 15, 16 e 18, IV; design L10), para RH e Admin, com justificativa:
  - substitui nome, CPF, contato, endereço, data de nascimento e dados bancários, e desativa o usuário;
  - preserva histórico agregado e auditoria sem valores;
  - recusa a operação com prazo de guarda vigente ou processo em aberto.

  Verificar por HTTP:
  - depois de anonimizar um colaborador de teste desligado, nenhum endpoint devolve dado que o identifique e os indicadores continuam com a mesma contagem;
  - a tentativa com prazo vigente é recusada;
  - nenhum registro é excluído.
- [ ] 4.4 Adolescentes aprendizes (art. 14; ECA Digital; design L11):
  - a ativação do contrato de menor de 18 anos exige documento de responsável legal aprovado;
  - as preferências nascem com `ocultar_aniversario` e `ocultar_mural` verdadeiros;
  - registrar na 1.5.

  Verificar por HTTP: o cadastro de um aprendiz de 16 anos sem responsável legal é bloqueado, e ele não aparece entre os aniversariantes nem no mural.
- [ ] 4.5 Confirmar no painel do Xano se o banco tem criptografia em repouso e em que região está, e registrar na 1.6. Se não houver criptografia, criar tarefa de criptografia de campo para CPF e conta bancária antes de fechar esta. Verificar: a 1.6 traz a resposta com a data da consulta.
- [ ] 4.6 Criar `docs/evidencias/README.md` com a regra de mascaramento (sem nome, CPF, e-mail ou token completo) e um checklist de revisão antes de cada commit nessa pasta. Fazer isto antes da primeira evidência desta change, mesmo estando na Parte 4. Se a tarefa 3.7 da `corrigir-brechas` já tiver criado o arquivo, só completar com o checklist. Verificar: `grep -rE "@|Bearer |[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}" docs/evidencias` não encontra dado real.

## 5. Integração final

- [ ] 5.1 Rodar `python tools/checar_endpoints.py` e um teste HTTP por perfil (Admin, RH, Gestor e Colaborador) cobrindo `meus_dados`, as preferências, um pedido LGPD, a abertura de um arquivo e uma consulta de indicadores. Verificar: zero falhas no script, o resultado esperado em todas as chamadas e registro em `docs/evidencias/lgpd.md`.
- [ ] 5.2 Rodar `openspec validate adequacao-lgpd` e conferir que o arquivamento desta change fica depois do `conectarh.gestao`, do `implementar-frontend-streamlit` e da `corrigir-brechas-e-alinhar-documentacao` (design, Migration Plan). Verificar: a validação passa sem erros.
