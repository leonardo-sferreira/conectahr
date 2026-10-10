# Evidências — Conferência de documentos do RH (tarefa 27)

Tela construída em 10/10/2026 no frontend Streamlit, a partir da seção 18 do Figma
("RH: conferência de documentos — decidir, arquivar e regras"). Só RH e Admin acessam.

| Nó do Figma (claro / escuro) | O que é | Código |
|---|---|---|
| 418:1108 | Aba "Para conferir" | `frontend/pagina_conferencia_documentos.py` |
| 418:1276 | Aba "Pendências pedidas" | idem |
| 418:1461 | Aba "Obrigatórios por cargo" | idem |
| 418:1642 / 244:1035 / 418:1666 | Modais Aprovar, Recusar e Arquivar | idem |
| 244:1059 / 418:1723 / 418:1692 | Modais Pedir documento, Vencidos processados e Nova regra | idem |
| 420:1010 | A seção inteira no escuro | `frontend/theme.py` (`_ESCURO_CSS`) |

O que cada linha oferece fica em `frontend/conferencia_modelo.py`, um módulo sem Streamlit.

**Endpoints usados**
- `documentos`;
- `pendencias_documento` (GET e POST);
- `documentos_obrigatorios` (GET e POST);
- `documentos/{id}/aprovar`, `rejeitar`, `arquivar` e `arquivo`;
- `documentos/processar_vencimentos`;
- `organograma`, para o nome e o departamento de cada pessoa.

**Menu**
- O menu lateral ganhou o grupo "RH", só para RH e Admin, com os itens da seção 18.
- Por enquanto só "Conferência de documentos" abre; os outros itens mostram "em construção".

## Como repetir

```
python tools/testar_conferencia_documentos.py   # 52 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 10/10/2026: 52 de 52.**

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Indicadores: aguardando análise, vencidos para processar (aprovado com validade passada), pendências abertas e aprovados no mês | ok |
| Sucesso | Nome e departamento de cada pessoa vêm do `organograma`; filtro por tipo de documento | ok |
| Sucesso | "Aprovar" envia o id e a observação; o modal fecha e a linha sai da lista | ok |
| Sucesso | "Recusar" envia o motivo, que o colaborador vê | ok |
| Sucesso | "Arquivar" explica que nada é apagado; a linha sai da lista | ok |
| Sucesso | "Abrir" pede o link a `documentos/{id}/arquivo`, e a abertura é auditada | ok |
| Sucesso | "Pedir documento" envia pessoa, documento, prazo (padrão de 10 dias) e observação | ok |
| Sucesso | "Processar vencidos" mostra quantos documentos venceram e quantos alertas saíram; "Fechar" não processa de novo | ok |
| Sucesso | "Nova regra" envia documento, contrato, prazo de envio e guarda (5 anos depois do desligamento); sem cargo vale para todos | ok |
| Sucesso | "Pendências pedidas": cancelada não aparece, prazo vencido vira "Atrasada", atendidas no fim | ok |
| Regra | Ninguém decide o próprio documento: a linha mostra "Seu: outro RH decide", sem botões | ok |
| Regra | Arquivo bloqueado: sem "Abrir" e sem "Aprovar"; "Recusar" mostra o motivo do bloqueio | ok |
| Regra | "Arquivar" só em documento recusado, vencido ou substituído; aprovado e arquivado não aparecem | ok |
| Regra | Nenhuma opção de excluir | ok |
| Erro | Motivo com menos de 5 caracteres, pedido sem pessoa: mensagem no modal, sem chamar a API | ok |
| Erro | Recusa negada pelo backend: a mensagem aparece no modal, que continua aberto | ok |
| Erro | Erro ao carregar as regras fica na aba | ok |
| Permissão negada | Colaborador que abre o endereço: "Esta tela é só do RH e do Admin.", sem chamar a API, e sem o grupo "RH" no menu | ok |
| Permissão negada | 403 do backend vira mensagem; 403 ao abrir o arquivo também | ok |
| Vazio | Abas sem linhas mostram uma frase ("Nada para conferir agora.") | no código |
| Carregando | Spinner na página e no processamento de vencidos | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-conferencia-documentos/`](frontend-conferencia-documentos/):

| Print | Compare com |
|---|---|
| `1-para-conferir` | 418:1108 |
| `2-aprovar` | 418:1642 |
| `3-recusar` | 244:1035 |
| `4-arquivar` | 418:1666 |
| `5-pedir-documento` | 244:1059 |
| `6-vencidos-processados` | 418:1723 |
| `7-depois-de-aprovar` | a linha sai e aparece o aviso |
| `8-pendencias-pedidas` | 418:1276 |
| `9-obrigatorios-por-cargo` | 418:1461 |
| `10-nova-regra` | 418:1692 |
| `11-para-conferir-escuro` e `12-nova-regra-escuro` | 420:1010 |

## Decisões e diferenças em relação ao Figma

- **"Pedido por":** mostra "Você" ou "RH", e não o nome de quem pediu. O único endpoint com nomes de usuários
  (`usuarios`) devolve também o e-mail de todos, e a tela não precisa desse dado (minimização).
- **"Nova regra":** o Figma mostra "Vale para" e "Guardar por" num campo só cada. Na tela, cada um virou dois campos
  (contrato e cargo; anos e evento), porque o backend guarda esses dados separados. A regra entra como obrigatória.
- **Ações que o backend não tem:** não há como cancelar uma pendência nem editar uma regra.
- **Para conferir:** a lista traz os documentos em análise e os que podem ser arquivados (recusados, vencidos e
  substituídos).
