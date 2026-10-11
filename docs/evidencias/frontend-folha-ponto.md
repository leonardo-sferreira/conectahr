# Evidências — Folha de ponto do gestor e do RH, e hierarquia (tarefa 81)

> **A conferir com o Figma.** O Figma estava fora do ar. A folha reaproveita o espelho mensal do colaborador e o
> padrão das telas de RH; o grupo "Equipe" do menu segue o Figma do gestor (241:560).

## O que mudou

- **Hierarquia.** Cada ficha ganha o **superior direto** (Colaboradores → ficha → "Definir superior", só RH e Admin).
  - A lista de candidatos não oferece a própria pessoa, quem está abaixo dela (ciclo) nem desligados, e o backend
    confere de novo.
  - Sem superior, vale o Gestor do departamento, como antes.
- **Quem aprova as correções de ponto.**
  - Com superior definido, decidem o superior, o RH ou o Admin.
  - Sem superior, decidem o Gestor do departamento (ou o substituto com delegação), o RH ou o Admin.
  - Ninguém decide o próprio pedido. Assim, **as correções do gestor vão para o superior dele**.
- **Folha de ponto** (`frontend/pagina_folha_ponto.py`): "Folha de ponto da equipe" no grupo Equipe do gestor e
  "Folha de ponto" no grupo RH.
  - **Resumo do mês:** uma linha por pessoa visível, com horas, dias com marcação, dias sem registro, faltas
    injustificadas e atestados (quem tem falta aparece primeiro). Filtro de departamento para RH e Admin, e CSV para o
    fechamento.
  - **Por pessoa:** a folha mensal (o mesmo espelho do colaborador), desde o primeiro ponto, com:
    - os pedidos pendentes, para aprovar ou recusar com motivo;
    - "Ajustar" em qualquer dia: ajuste direto, com motivo, que vale na hora, fica no histórico do dia e na
      auditoria, e avisa a pessoa;
    - o CSV da pessoa.
  - **A própria folha** aparece só para consulta.

Regras de apresentação em `frontend/folha_modelo.py`; a ficha em `frontend/cadastro_modelo.py`.

## Backend: o que mudou e como foi conferido

**Tabelas** (push separado, antes dos endpoints):
- `colaborador.superior_colaborador_id` (opcional);
- tipo de notificação `ponto_ajustado`.

**Endpoints novos:**
- `colaboradores/{id}/superior` (PATCH): RH e Admin; sem a própria pessoa, sem desligado, sem ciclo; auditado.
- `folha_ponto/pessoas` (GET): quem quem pede pode ver, com a data do primeiro ponto.
- `folha_ponto/mes` (GET): os registros, as ausências (só tipo, período e situação), as férias e, de uma pessoa, as
  correções.
- `folha_ponto/ajustar` (POST): o ajuste direto. Tem as mesmas conferências da correção (janela do dia, futuro e
  ordem); recusa o próprio ponto e marcação com pedido pendente; cria o registro do dia se faltar; recalcula as horas;
  grava o histórico; audita e avisa.

**Escopo dos endpoints novos:**
- RH e Admin veem todos;
- os demais veem a si mesmos, quem os tem como superior direto e, de quem não tem superior, o departamento que
  gerenciam.

**Endpoints alterados:** `correcoes_ponto/{id}/aprovar` e `rejeitar` (decisão pela hierarquia) e `correcoes_ponto`
(GET), em que a fila do Gestor segue a mesma regra e nunca traz a própria correção.

**Como foi conferido:**
- **Tabelas:** o dry-run mostrou só o campo novo e o tipo novo, sem remoção.
- **Endpoints:** o dry-run mostrou 4 criados e 3 atualizados.
- **Publicação:** o `pull` seguinte trouxe tudo.
- **HTTP:** 401 sem token e com token inválido nos quatro endpoints novos.
- **`checar_endpoints.py`:** 191 endpoints, nenhuma falha.

**Não houve teste com contas reais**, porque o login pede código por e-mail.

## Como repetir

```
python tools/testar_folha_ponto.py   # 28 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 11/10/2026: 28 de 28.** Toda a bateria do frontend continua passando.

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Hierarquia | Candidatos a superior sem a própria pessoa, sem quem está abaixo (ciclo) e sem desligados; a ficha mostra o superior; salvar chama o backend | ok |
| Sucesso | Resumo do mês: horas, faltas injustificadas e atestados; quem tem falta primeiro; CSV | ok |
| Sucesso | A folha da pessoa começa no dia 1 mesmo quando o primeiro registro do mês é depois | ok |
| Sucesso | "Abrir folha" leva à pessoa; aprovar e recusar com motivo; ajuste direto com data, horário de Brasília e motivo | ok |
| Próprio ponto | Na própria folha não há "Ajustar" nem decisão | ok |
| Escopo | Gestor sem equipe e colaborador: explica onde está a própria folha; o RH tem filtro de departamento; o menu do gestor tem o grupo Equipe | ok |
| Erro | Recusa do backend no modal de ajuste; erro ao carregar vira alerta | ok |
| Carregando | Spinner enquanto o mês carrega | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-folha-ponto/`](frontend-folha-ponto/):
- `1-resumo-do-mes`;
- `2-folha-da-pessoa`;
- `3-ajustar`;
- `4-folha-escuro`.
