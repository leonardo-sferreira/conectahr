# Tasks

## 1. Figma

- [x] 1.1 Desenhar a seção 21 "Ponto REP-P": "Hoje" (relógio com segundos, botão de marcar, marcações do dia com NSR e "Comprovante (PDF)"), "Mês" em planilha (uma linha por dia, marcações em colunas, "(I)" e "(D)" com legenda, dias antes da admissão em branco), o comprovante em PDF com os campos do art. 79, o modal de correção com "Incluir marcação" e "Desconsiderar marcação", e os 6 estados. Verificar: nós anotados no `design.md` desta change e prints conferidos.
- [x] 1.2 Desenhar a seção 22 "Férias pela CLT": pedido com período, "Vender dias (até 10)", saldo e o que ainda pode ser pedido, calendário mensal com feriados e pontos facultativos (com legenda), mensagens de cada regra recusada e os 6 estados. Verificar: nós anotados no `design.md`.
- [x] 1.3 Desenhar a tela do RH "Ponto eletrônico (REP-P)": dados do empregador e do REP-P, registro de indisponibilidade do serviço, "Gerar AFD" e "Gerar AEJ" com intervalo de datas e o aviso de que a assinatura ICP-Brasil não é feita; e a aba "Feriados" na estrutura da empresa (tipo feriado ou ponto facultativo, abrangência). Verificar: nós anotados no `design.md`.
- [x] 1.4 Fazer as versões escuras das seções 21 e 22 e da tela do RH, com a mesma conversão de cores das seções 18 e 20. Verificar: prints no modo escuro sem texto escuro sobre fundo escuro.

## 2. Base do REP-P no backend

- [x] 2.1 Criar as tabelas `empregador`, `marcacao_ponto` (índice único em `nsr`) e `tratamento_ponto`, e os campos novos (`correcao_ponto.tipo`, `marcacao_id`, `data_hora`; `feriado.tipo`; `ferias.dias_abono`; `regra_contrato.maximo_abono`). Verificar: `xano workspace push --dry-run` mostra só inclusões, sem remoção, e a publicação passa.
- [x] 2.2 Confirmar o SHA-256 no XanoScript com uma função de teste que devolve o hash de "abc". Verificar: o resultado é `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`; se não for, parar e revisar a decisão D3 com o grupo.
- [ ] 2.3 Criar a função `ConectaHR/gravar_registro_rep` (próximo NSR com até 3 tentativas, campos no formato do AFD, hash encadeado do registro 7) e a função `ConectaHR/dia_de_ponto` (pares, horas, status, atualização de `registro_ponto`). Verificar: `tools/testar_rep_p.py` recalcula em Python o hash de marcações gravadas por HTTP e confere a cadeia.
  - **Em andamento (12/10/2026):** funções publicadas (`sha256_hex`, `data_hora_afd`, `hash_registro_rep`, `calcular_dia_ponto`, `gravar_registro_rep`, `atualizar_dia_ponto`). `tools/testar_rep_p.py --xano`: 9/9, com o hash do backend igual ao do Python. `calcular_dia_ponto` conferido em 4 casos (desconsiderada, incluída, extra, ímpar). Primeiro registro da ARP: NSR 1, evento 07. Falta conferir a cadeia de marcações gravadas, que existem a partir da 3.1 e da 3.4.
- [ ] 2.4 Criar `empregador` GET e PUT (só RH e Admin, auditado, grava o registro 2) e `rep/eventos` POST para indisponibilidade e disponibilidade (registro 6, códigos 08 e 07). Verificar: um caso que passa e um que falha por HTTP (Gestor recebe 403) e `python tools/checar_endpoints.py` sem falhas.
  - **Em andamento (12/10/2026):** publicados; `checar_endpoints.py` sem falhas; sem token, 401. Falta o teste com sessão (RH grava, Gestor 403), que depende do código de acesso por e-mail.
- [ ] 2.5 Gerar o registro 5 em `colaboradores` POST, em `colaboradores/{id}` PATCH quando mudar nome ou CPF e na conclusão do desligamento ("E"). Verificar: cadastrar um colaborador de teste grava o registro 5 com CPF e nome.
  - **Em andamento (12/10/2026):** `ConectaHR/registrar_empregado_rep` e as quatro chamadas publicadas. Falta o teste com sessão (cadastrar um colaborador de teste).
- [x] 2.6 Fazer `tools/checar_endpoints.py` falhar se algum endpoint tiver `db.edit` ou `db.del` em `marcacao_ponto` ou `tratamento_ponto`, ou se a rotina de anonimização tocar nelas. Verificar: o script acusa um arquivo de teste com `db.del marcacao_ponto` e passa no código real.
- [x] 2.7 Documentar o REP-P em `docs/ponto/rep-p.md` (fontes oficiais com link e data, o que é feito, o que fica fora, como conferir a cadeia de hash) e atualizar `docs/regras-de-negocio.md`. Verificar: os links dos leiautes abrem e o documento cita os arts. 74 a 91 usados.

## 3. Marcação, tratamento e migração

- [ ] 3.1 Reescrever `ponto/marcar`: recusa sem empregador e antes da admissão, grava o registro 7, recalcula o dia e devolve a marcação com NSR, hash e os dados do comprovante. Verificar: por HTTP, cinco marcações no mesmo dia viram três pares (o último aberto) e uma marcação com data anterior à admissão é recusada.
- [ ] 3.2 Trocar a sobrescrita por tratamento em `ponto/{id}/solicitar_correcao`, `ponto/solicitar_correcao_dia`, `correcoes_ponto/{id}/aprovar` e `folha_ponto/ajustar` (inclusão ou desconsideração, com motivo obrigatório). Verificar: depois de aprovar uma correção, a marcação original continua na ARP, o tratamento existe e o dia fica AJUSTADO; `tools/testar_decisoes.py` e `tools/testar_folha_ponto.py` atualizados e passando.
- [ ] 3.3 Ajustar `meu_ponto`, `folha_ponto/mes` e a rotina diária para devolver as marcações com NSR e os tratamentos de cada dia, e criar `ponto/comprovantes` GET (marcações das últimas 48 horas, só do próprio usuário). Verificar: por HTTP, o comprovante de outra pessoa não aparece e a lista tem as marcações de ontem.
- [ ] 3.4 Criar a migração (endpoint de uso único, só Admin, auditado): registros 5 dos colaboradores ativos, marcações de `registro_ponto` para a ARP em ordem, correções aprovadas como tratamentos e o relatório com as contagens. Verificar: rodar na base de desenvolvimento, conferir a cadeia com `tools/testar_rep_p.py` e anotar as contagens no `design.md`.

## 4. Tela de ponto

- [ ] 4.1 Adicionar `fpdf2` ao `requirements.txt` e criar `frontend/comprovante_ponto.py`, que monta o PDF do comprovante com os campos do art. 79. Verificar: teste confere que o texto do PDF tem título, NSR, CNPJ, local, nome, CPF, data e hora, INPI e hash.
- [ ] 4.2 Refazer `pagina_ponto.py` com "Hoje" (relógio, marcar, marcações do dia com NSR e comprovante, comprovantes das últimas 48 horas) e "Mês" em `st.dataframe` (colunas de marcações, "(I)" e "(D)", horas, situação, legenda, correção pela seleção da linha), sem a visão semanal. Verificar: `tools/testar_ponto.py` e `tools/testar_ponto_mensal.py` atualizados e passando, e prints lado a lado com o Figma da seção 21.
- [ ] 4.3 Mudar `primeiro_dia()` para a admissão e deixar em branco os dias anteriores a ela e os futuros, em `ponto_mensal_modelo.py` e `folha_modelo.py`. Verificar: teste com admissão em 15/10 mostra os dias 1 a 14 sem situação e nenhuma falta antes do dia 15.
- [ ] 4.4 Pôr o cabeçalho do art. 84 no espelho do mês (empregador, trabalhador com admissão e cargo, emissão, período, horário contratual) e no CSV. Verificar: teste confere os campos no cabeçalho e no CSV.
- [ ] 4.5 Atualizar a folha da equipe (`pagina_folha_ponto.py`) para mostrar marcações e tratamentos na mesma planilha e o ajuste como inclusão ou desconsideração. Verificar: `tools/testar_folha_ponto.py` passando e prints com o Figma.
- [ ] 4.6 Registrar as evidências em `docs/evidencias/frontend-ponto-rep-p.md` (prints, estados, testes). Verificar: o documento lista os nós do Figma e os testes executados com os números.

## 5. AFD e AEJ

- [ ] 5.1 Criar `frontend/rep_modelo.py` com CRC-16/KERMIT, os registros 1, 2, 5, 6, 7 e 9 e o registro de assinatura do AFD, e os registros 01 a 08 e 99 e o de assinatura do AEJ, em ISO 8859-1 com CR LF. Verificar: `tools/testar_rep_p.py` confere o CRC de "123456789" = "2189", o tamanho de cada tipo de linha e os campos de um arquivo de exemplo.
- [ ] 5.2 Criar `rep/afd` GET e `rep/aej` GET (intervalo de datas, só RH e Admin, auditados) que devolvem os registros do intervalo. Verificar: Gestor recebe 403 por HTTP e `tools/checar_endpoints.py` sem falhas.
- [ ] 5.3 Construir a tela do RH "Ponto eletrônico (REP-P)" com o empregador, o REP-P, os eventos do serviço e os botões de gerar os arquivos, com o nome no padrão do leiaute. Verificar: o AFD de um mês de teste baixado pela tela passa pela conferência de `tools/testar_rep_p.py` (tamanhos, CRC, hash e trailer) e prints com o Figma.

## 6. Férias pela CLT

- [ ] 6.1 Atualizar a matriz `regra_contrato` da CLT (antecedência 45, mínimo 5, principal 14, até 3 períodos, abono até 10) e mudar `ferias/solicitacoes` para: saldo do período aquisitivo, algum período de 14 dias (não o primeiro), saldo restante utilizável, abono de até 10 uma vez por período e início fora dos dois dias antes de feriado ou do repouso semanal. Verificar: `tools/testar_ferias.py` cobre os cenários da spec por HTTP ou com a regra isolada, e um caso de cada regra é recusado com a mensagem certa.
- [ ] 6.2 Ampliar `minha_situacao_ferias` com saldo, períodos pedidos, dias vendidos, se já há período de 14 e o mínimo do próximo. Verificar: por HTTP, depois de vender 10 dias e pedir 5, a resposta mostra saldo 15 e mínimo do próximo 14.
- [ ] 6.3 Refazer `pagina_ferias.py` e `ferias_modelo.py` com venda de dias, saldo e as mensagens antecipadas das regras. Verificar: `tools/testar_ferias.py` passando e prints com o Figma da seção 22.
- [ ] 6.4 Atualizar `docs/regras-de-negocio.md` (férias) e fechar a tarefa 74 da `concluir-frontend-streamlit` (saldo) com referência a esta change. Verificar: a seção de férias descreve as cinco regras e a tarefa 74 está marcada.

## 7. Feriados e calendário

- [ ] 7.1 Criar `tools/feriados.py` (Páscoa e datas móveis) e carregar 2026 e 2027: nacionais, facultativos federais, estado de São Paulo e cidade de São Paulo. Verificar: o teste confere Páscoa de 2026 em 05/04 e de 2027 em 28/03, Corpus Christi em 04/06/2026 e 27/05/2027, e a lista bate com a portaria federal de pontos facultativos de 2026.
- [ ] 7.2 Ajustar `calendario` GET para devolver o tipo, e o CRUD de feriados (RH e Admin, auditado) para aceitar o tipo. Verificar: por HTTP, Gestor recebe 403 ao incluir feriado e o tipo volta na consulta.
- [ ] 7.3 Mostrar o calendário mensal na tela de férias e a aba "Feriados" na estrutura da empresa; tratar ponto facultativo no espelho do ponto. Verificar: teste com 9 de julho mostra "Feriado estadual (SP)" sem falta, e prints com o Figma.

## 8. LGPD e integração

- [ ] 8.1 Atualizar `docs/lgpd/registro-de-operacoes.md`, `retencao.md` e o aviso de privacidade (documento e cópias no Figma) com o CPF no comprovante, no AFD e no AEJ e a ARP fora da anonimização pelo prazo legal. Verificar: documento e Figma com os mesmos textos.
- [ ] 8.2 Conferência de ponta a ponta: marcar, pedir correção, aprovar, ver o espelho com "(I)", gerar AFD e AEJ e pedir férias com venda, num ambiente de teste. Verificar: o roteiro executado com os resultados em `docs/evidencias/frontend-ponto-rep-p.md`, e `openspec validate ponto-rep-p-e-ferias-clt` passando.
