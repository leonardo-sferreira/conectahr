# Política de retenção de dados pessoais

**Referência:** LGPD (Lei nº 13.709/2018), arts. 15 e 16, e art. 6º, III e X (necessidade e responsabilização).
**Situação:** análise técnica de projeto acadêmico. **Todos os prazos abaixo são sugestões, "a confirmar com o jurídico"** da empresa que usa o ConectaRH. Nenhum prazo foi validado.
**Fonte:** as finalidades vêm do [registro de operações](registro-de-operacoes.md) (F01 a F19). Ao mudar uma finalidade lá, revise esta tabela.

## Princípios

- **Nada é apagado fisicamente.** No fim do prazo, o dado pessoal é **anonimizado** (nome, CPF, contato, endereço, data de nascimento e dados bancários são substituídos), e o histórico agregado e a auditoria permanecem sem identificar a pessoa. Ver `colaboradores/{id}/anonimizar` e o design L10 da change `adequacao-lgpd`.
- **A guarda legal prevalece.** Enquanto houver prazo legal de guarda (trabalhista, fiscal, SST), o pedido de eliminação do titular é recusado com a justificativa do art. 16, I.
- **Contagem do prazo.** Salvo indicação em contrário, o prazo conta do **desligamento** do colaborador. Para dados sem vínculo com o desligamento (sessões, e-mails, códigos), conta da criação do registro.
- **Guarda curta para dado técnico.** IP, dispositivo e conteúdo de e-mail já enviado não precisam de guarda longa.

## Prazos por finalidade

| Cód. | Categoria | Prazo sugerido (a confirmar) | Contagem | Tratamento no fim do prazo | Situação no sistema |
|---|---|---|---|---|---|
| F01 | Sessão: IP e dispositivo (`sessao`) | 6 meses, se vierem a ser gravados | Do encerramento ou expiração da sessão | Anular `endereco_ip` e `dispositivo` | Limpeza na rotina diária (tarefa 4.21); **hoje os campos ficam vazios**, o login não os grava |
| F01 | Código de acesso e de redefinição (`user`) | Minutos: 5 (login) e 15 (redefinição) | Da geração | O código vira vazio ao ser usado ou ao expirar; só o hash é guardado | Em vigor (hash dos códigos, tarefa 4.13) |
| F01 | Conta de acesso (`user`) | Enquanto houver vínculo; depois, até o fim da guarda do colaborador | Do desligamento | Desativar e anonimizar nome e e-mail | Desativação em vigor; anonimização na tarefa 4.22 |
| F02 | Auditoria (`auditoria`) | Prazo longo, igual ao da guarda trabalhista mais longa (ver F10) | Do evento | Mantida; já guarda dado mascarado | Em vigor (mascaramento, tarefa 4.9) |
| F03 | Cadastro e identificação do colaborador | 5 anos | Do desligamento (prescrição trabalhista) | Anonimizar | Anonimização na tarefa 4.22 |
| F04 | Documentos pessoais e obrigatórios | Por tipo de documento; em geral 5 anos | Do desligamento | Anonimizar o registro e eliminar o arquivo, quando houver | `documento.retencao_ate` preenchido pela regra do tipo (tarefa 3.27); listagem `documentos/retencao_vencida` |
| F05 | Remuneração, pagamento e dados bancários | 5 anos (trabalhista); o FGTS e as obrigações fiscais podem exigir mais | Do desligamento | Anonimizar dados bancários; manter valores agregados | Anonimização na tarefa 4.22 |
| F06 | Contrato, cargo e histórico profissional | 5 anos | Do desligamento | Anonimizar; manter o histórico sem identificar | Anonimização na tarefa 4.22 |
| F07 | Controle de jornada (ponto e banco de horas) | 5 anos | Do desligamento | Anonimizar; manter o agregado | Anonimização na tarefa 4.22 |
| F08 | Férias | 5 anos | Do desligamento | Anonimizar | Anonimização na tarefa 4.22 |
| F09 | Ausências e atestados (**saúde**) | 5 anos para o registro | Do desligamento | Anonimizar o registro | O sistema não guarda o arquivo do atestado (sem upload no plano atual, decisão da tarefa 4.27) |
| F10 | SST: ASO, laudos e eventos (**saúde**) | **20 anos** (referência: NR-7, guarda do ASO depois do desligamento) | Do desligamento | Anonimizar ao fim | `retencao_ate` do documento; regra por tipo |
| F11 | Desligamento (solicitação, motivo, decisão) | 5 anos | Da conclusão | Anonimizar o texto livre | Anonimização na tarefa 4.22 |
| F12 | Avaliações, metas, PDI e reuniões | 2 anos depois do ciclo, ou 5 anos do desligamento, o que vier primeiro | Do fim do ciclo | Anonimizar; manter notas agregadas | Anonimização na tarefa 4.22 |
| F13 | Reconhecimento (mural) | 1 ano | Da publicação | Anonimizar remetente e destinatário | A implementar; o titular já pode sair do mural (tarefa 4.18) |
| F14 | Aniversariantes do mês | Enquanto houver vínculo | Do desligamento | Sai da lista ao desligar | Em vigor (filtra desligados); preferência de ocultar na tarefa 4.18 |
| F15 | Pesquisa de clima | Resultado agregado: 5 anos | Do encerramento da pesquisa | Manter só o agregado; não há dado individual | Em vigor (resposta gravada só como contagem) |
| F16 | Solicitações ao RH, comunicados e notificações | 2 anos | Da decisão ou do envio | Anonimizar o texto livre | A implementar |
| F17 | E-mail transacional (`email_outbox`) | 6 meses para mensagens enviadas | Do envio | Anular destinatário e corpo | Limpeza na rotina diária (tarefa 4.21) |
| F18 | Regras e instrumentos normativos | Prazo legal do instrumento | Do fim da vigência | Mantidos (sem dado pessoal direto) | Em vigor |
| F19 | Onboarding, pendências de documento e delegações | 2 anos | Da conclusão | Anonimizar | A implementar |

## Como o sistema aplica os prazos

1. **`documento.retencao_ate`:** ao cadastrar um documento, o sistema calcula a data pela regra de `documento_obrigatorio_regra` do tipo (prazo em dias e evento inicial: emissão, validade ou desligamento). `GET documentos/retencao_vencida` lista, só para leitura (RH e Admin), os documentos com a data vencida. A decisão de eliminar ou anonimizar é humana.
2. **Rotina diária:** `rotinas/processar_diarias` anula IP e dispositivo de sessões antigas e o destinatário e o corpo de e-mails enviados com prazo vencido, e lista ao RH os desligados com prazo de guarda cumprido (tarefa 4.21).
3. **Anonimização:** `colaboradores/{id}/anonimizar` (RH e Admin, com justificativa) recusa a operação enquanto houver documento com prazo de guarda vigente (tarefa 4.22).

## Pendências

- Validar **todos** os prazos com o jurídico. Os números acima servem para o sistema ter um valor de partida, não como orientação jurídica.
- Se um dia houver upload de arquivo (outro plano do Xano), definir o prazo de guarda do atestado e rever a linha F09.
- Implementar as linhas marcadas "A implementar" (F13, F16 e F19), que dependem da rotina de anonimização por categoria.
