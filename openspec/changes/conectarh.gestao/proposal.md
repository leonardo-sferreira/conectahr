## Why

O ConectaRH precisa centralizar rotinas de RH que hoje ficam dispersas: controle de jornada, cadastro de colaboradores, documentos, ferias, ausencias e desenvolvimento. A mudanca cria uma base funcional unica, com autenticacao forte e regras de acesso compativeis com os papeis de Admin, RH, Gestor e Colaborador.

O planejamento precisa produzir um MVP demonstravel, documentado e implantavel, alinhado ao uso de Xano, Script Xano, Reflex, GitHub e OpenSpec.

## What Changes

- Criar autenticacao com token de acesso valido por uma hora, encerramento explicito de sessao, redefinicao de senha e senha temporaria obrigatoria no primeiro acesso.
- Adicionar validacao de login por codigo de acesso de 6 digitos enviado por e-mail (SendGrid), obrigatoria em todo login, com reenvio e bloqueio apos tentativas invalidas.
- Implementar autorizacao por perfil e escopo organizacional, incluindo vinculo de colaborador com gestor e gestor com departamento.
- Criar gestao de colaboradores, cargos, departamentos e historico profissional, respeitando os tipos de contrato, niveis e status definidos no dominio.
- Permitir que o colaborador cadastre e atualize os proprios dados bancarios (banco, agencia, conta e tipo), para consulta do RH na realizacao de pagamentos, sem acesso do Gestor a essa informacao.
- Permitir registro de ponto, acompanhamento da jornada e solicitacoes de correcao com aprovacao ou recusa pelos responsaveis autorizados.
- Permitir envio de documentos pelo colaborador e solicitacao de pendencias pelo RH, com notificacoes por e-mail e rastreabilidade.
- Permitir que o RH anexe holerites (folha de pagamento) e informes de rendimentos para imposto de renda ao cadastro do colaborador, para consulta e download pelo proprio colaborador — usando o mesmo modulo de documentos ja existente, sem implementar calculo ou emissao de folha de pagamento (o arquivo e gerado fora do ConectaRH).
- Implementar solicitacao e decisao de ferias por RH e gestor, alem do registro e acompanhamento de ausencias.
- Implementar ciclos de avaliacao, competencias, avaliacoes privadas entre gestor e colaborador, feedbacks publicos entre colaboradores, metas anuais e planos de desenvolvimento.
- Manter todas as transicoes de status, decisoes, observacoes e responsaveis auditaveis.
- Nao importar nem incluir registros de teste apresentados nas imagens; os enums e a estrutura relacional informados serao usados como referencia de dominio.
- Implementar o fluxo completo de solicitacao, analise e decisao de desligamento (imediato ou aviso previo) como parte do MVP, incluindo aprovacao exclusiva do RH, desativacao do acesso, registro no historico profissional e conclusao automatica dos desligamentos agendados quando a data efetiva chegar.
- Organizar o desenvolvimento colaborativo em entregas incrementais, com validacao parcial, testes, documentacao e apresentacao final.
- Adotar Reflex no frontend, SendGrid para disparo de e-mails e regras parametrizadas de jornada e ferias conforme o tipo de contrato.
- Adicionar estados de documento `pendente_analise`, `aprovado`, `rejeitado`, `vencido`, `substituido` e `arquivado`, com vencimento automatico diario e retencao do arquivo vencido.
- Incluir no MVP uma central de tarefas e pendencias (incluindo dashboard do gestor e alertas de cadastro incompleto e ponto nao finalizado), onboarding de colaboradores, painel de auditoria (com indicadores de headcount, turnover, admissoes, desligamentos e absenteismo), matriz administrativa de regras por contrato e excecoes individuais auditadas.
- Implementar central de solicitacoes do colaborador ao RH (alteracao cadastral, declaracao, documento avulso e outras demandas), com decisao do RH e sem alterar o cadastro automaticamente na aprovacao.
- Implementar organograma da empresa, pesquisa global de colaboradores, tempo de empresa, aniversariantes do mes e timeline do colaborador, todos como vistas sobre dados ja existentes.
- Implementar central de notificacoes internas no sistema, alem do envio por e-mail ja previsto.
- Implementar comunicados internos publicados por RH/Admin e uma base de conhecimento (FAQ) para colaboradores.
- Validar CPF localmente pelo algoritmo dos digitos verificadores, sem API externa.
- Implementar delegacao temporaria de aprovacao com expiracao automatica, controle de prazos com escalonamento de pendencias atrasadas e calendario organizacional com deteccao de conflitos de ferias.
- Implementar consulta e encerramento de sessoes/dispositivos com alerta de acesso suspeito, matriz de documentos obrigatorios, quarentena de arquivos antes da liberacao e politica de retencao parametrizada por tipo de documento.
- Implementar reunioes individuais, check-ins de metas, reconhecimento publico exclusivamente positivo, feedback corretivo privado, pesquisa anonima de clima, matriz de competencias e plano de carreira sem promocao automatica.
- Implementar indicadores, exportacoes CSV/PDF, preferencias de notificacao, versionamento de API sob `/api/v1/` com identificador de rastreamento por requisicao, monitoramento operacional, backup/recuperacao e acessibilidade do frontend Reflex.
- Formalizar regras de contrato por meio de `instrumento_normativo` e `regra_override`, com documento de origem, abrangencia, vigencia, prioridade, aprovacao, versionamento e simulacao antes da publicacao.
- Utilizar validacao local de CPF por calculo dos digitos verificadores, sem integracao externa.
- Utilizar Figma para criar o design system, prototipos e especificacoes visuais antes da implementacao das telas em Reflex.

## Capabilities

### New Capabilities

- `conectahr`: plataforma integrada de RH para identidade, autorizacao, estrutura organizacional, jornada, documentos, ferias, ausencias, desligamento e desenvolvimento de colaboradores.

### Modified Capabilities

Nenhuma. O workspace ainda nao possui especificacoes existentes.

## Impact

- Novos modulos de dominio, API e interface para os fluxos de RH descritos.
- Persistencia para usuarios, colaboradores, cargos, departamentos, historico profissional, ponto, documentos, ferias, ausencias e avaliacao.
- Servico de e-mail para notificacoes e pendencias, alem de armazenamento protegido para anexos.
- Integracao com o SendGrid para o codigo de acesso de login e mecanismo seguro de hash de senhas e tokens.
- Auditoria e autorizacao devem proteger dados pessoais, documentos e feedbacks privados.
- O projeto integrador deve incluir repositorio GitHub, documentacao de setup e decisoes, backend em Xano/Script Xano, frontend em Reflex, integracao por API, deploy e validacao inicial de mercado.
- O frontend adotara Reflex e os e-mails transacionais usarao SendGrid.
- O design system devera documentar cores, tipografia, espacamentos, componentes, estados, acessibilidade, responsividade e handoff para o frontend.
- A rotina diaria do Xano marcara documentos aprovados com validade encerrada como vencidos, sem apagar o registro ou desativar o colaborador.
- A resolucao de regras seguira a matriz contratual, normas vigentes, instrumentos coletivos, regras de cargo/departamento e excecao individual, sem decidir automaticamente conflitos juridicos.
- Instrumentos coletivos guardarao separadamente numero da solicitacao Mediador, numero de registro no MTE e numero do processo, exigindo registro no MTE, documento oficial e aprovacao interna antes de ficarem vigentes.
- Aplicar regras operacionais distintas para CLT, estagio, trabalho temporario e prestador PJ, sem presumir vinculo ou direitos de empregado apenas pelo cadastro.
- Tratar o registro de ponto do MVP como controle interno experimental; eventual conformidade como REP-P, REP-A ou REP-C sera uma evolucao sujeita a Portaria nº 671/2021.
- Proteger dados pessoais e sensiveis conforme a LGPD, com minimizacao, finalidade, acesso por necessidade e retencao controlada.
