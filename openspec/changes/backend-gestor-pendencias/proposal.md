# Pendências de backend das telas do Gestor

## Why

As changes `indicadores-da-equipe`, `delegacoes-do-gestor` e `avaliacoes-da-equipe` entregaram telas parciais do Gestor, só com o que o backend já autoriza. O que o Figma prevê e o backend ainda não permite ficou como "dependência futura" na última tarefa de cada uma. Esta change recebe essas dependências, para que aquelas três possam ser arquivadas com o escopo parcial que entregaram.

Esta proposta só registra o escopo. Specs e design são escritos antes da implementação (tarefa 1.1).

## What Changes

**Indicadores da equipe (F18; vinha de `indicadores-da-equipe`, tarefa 9):**
- cobertura do departamento inteiro na folha (hoje a folha segue o superior direto e só pega quem não tem superior);
- jornada histórica para calcular o absenteísmo;
- clima da equipe ao Gestor, agregado e com supressão de grupos pequenos;
- exportação CSV auditada.

**Delegações do Gestor (F17; vinha de `delegacoes-do-gestor`, tarefa 9):**
- catálogo autorizado de substitutos para o Gestor criar delegação sem informar IDs;
- filas delegadas na Central;
- efeito da delegação nos demais escopos (ausência, documento, desligamento e solicitação ao RH; hoje só férias e correção de ponto);
- alinhar a hierarquia: superior direto e gestor do departamento.

**Avaliações da equipe (F15; vinha de `avaliacoes-da-equipe`, tarefa 8):**
- confirmar a autoavaliação para o Gestor;
- prazos;
- contestação respondida pelo Gestor, com manter ou revisar a nota.

**Achado no teste com login (20/11/2026):**
- não há competência de avaliação ativa no banco nem rota para cadastrar uma. Sem isso, nenhum avaliador consegue preencher uma avaliação: o formulário volta vazio.

## Impact

- Backend no Xano: rotas do Gestor, com escopo por departamento e auditoria.
- Frontend: as telas `pagina_indicadores_equipe.py`, `pagina_delegacoes.py` e `pagina_avaliacoes_equipe.py` deixam de mostrar esses itens como indisponíveis.
- LGPD: o clima ao Gestor e a exportação CSV precisam de revisão do registro de operações.
