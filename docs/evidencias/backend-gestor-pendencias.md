# Telas do Gestor: indicadores, delegações e avaliações (change `backend-gestor-pendencias`)

**Data:** 20/11/2026. **Ambiente:** Xano da equipe (workspace 147338). Contas pelo papel: Admin, RH e uma conta de teste, que virou Gestor do setor de RH só durante o teste e voltou a Colaborador no fim. O setor voltou a ter o gestor de antes. O ciclo de avaliação de teste (5) foi cancelado.

## Com login (27/27)

| Decisão | Cenário | Esperado | Obtido |
|---|---|---|---|
| D2 | Gestor abre os indicadores do setor (2 pessoas) | Números ocultos, com o motivo, sem dado de pessoa | Igual |
| D2 | RH e Admin chamam a rota do Gestor | 403 | 403 e 403 |
| D2 | Gestor exporta | Mesmos agregados; `exportar_indicadores_equipe` na auditoria | Igual |
| D3 | Escopos e catálogo do Gestor | Férias, correção de ponto e todas; quem é do setor, sem o titular, só nome e setor | Igual |
| D3 | Gestor delega desligamento ou solicitação ao RH | 400 | 400 e 400 |
| D3 | Substituto fora do catálogo | 400 | 400 |
| D3 | Delegação válida | Criada e depois cancelada | Igual |
| D4 | Avaliação do Gestor | Prazo = fim do ciclo; autoavaliação pendente, depois enviada, sem notas | Igual |
| D5 | Contestação da pessoa avaliada | O Gestor vê a contestação; outra conta 403; revisar sem nota 400 | Igual |
| D5 | Gestor revisa a nota de 2 para 3 | Nota 3; original 2 guardada; contestação continua aberta; responder de novo 400 | Igual |
| D5 | RH fecha com nota final 4 | Nota 4; original continua 2; contestação revisada | Igual |

## Sem login

- **Dias úteis dos 6 meses** (`ConectaHR/indicadores_setor`, pela CLI):
  - junho 22, porque Corpus Christi é ponto facultativo e não conta;
  - julho 23;
  - agosto 21;
  - setembro 21, sem o 7/9;
  - outubro 21, sem o 12/10;
  - novembro 13 até 20/11, sem 2/11 e 20/11.
- **Telas:**
  - `tools/testar_indicadores_equipe.py` 34/34;
  - `tools/testar_delegacoes.py` 31/31;
  - `tools/testar_avaliacoes_equipe.py` 32/32;
  - `tools/testar_clima_avaliacao.py` 66/66;
  - `tools/testar_decisoes.py` 64/64.

  Os 36 passos de teste do CI passam.

## Não conferido

- **Pedidos delegados na Central do substituto (D3):** o teste precisa de uma terceira pessoa no setor do titular, que não seja o titular nem o substituto, com pedido pendente. A base tem 2 pessoas nesse setor.
- **Somas de horas extras e ausências:** os dados do período estão zerados, então as somas só foram conferidas com zero.
