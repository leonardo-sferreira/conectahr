# Evidências — Hierarquia em férias e ausências e prazo de correção (tarefas 83 e 79)

> **A conferir com o Figma.** O Figma estava fora do ar. As telas seguem o padrão das já aprovadas (Central de
> Pendências e Folha de ponto) e precisam ser desenhadas lá.

## O que mudou

**Hierarquia (tarefa 83).** Férias, ausências e correções de ponto agora seguem a mesma regra:
- RH e Admin decidem todos;
- se a pessoa tem superior direto na ficha, só esse superior decide;
- se não tem, decide o gestor do departamento;
- ninguém decide o próprio pedido.

O perfil não importa: quem é superior direto de alguém vê a fila de aprovação, mesmo com o perfil Colaborador.

- **Central de Pendências** (`frontend/pagina_central.py`):
  - abre as filas para quem é superior (o backend devolve `e_superior`);
  - aba nova **Ausências**, com Aprovar e Rejeitar. Rejeitar exige justificativa.
  - A fila mostra só o tipo e o período. O comprovante continua só com o RH, e registrar a ausência aprovada também.
- **Menu:** quem tem equipe e não é Gestor vê o grupo "Equipe" só com "Folha de ponto da equipe". O app confere isso uma
  vez por sessão, em `folha_ponto/pessoas`.

**Prazo para pedir correção (tarefa 79).**
- **Quem define:** o RH (ou o Admin), em Folha de ponto → Resumo do mês → "Alterar prazo".
- **Valores:** de 1 a 3650 dias, ou sem limite, que é como começa.
- **No espelho mensal do colaborador:** os dias fora do prazo ficam sem o botão de correção e com a nota "Fora do prazo
  para pedir correção.". Um aviso acima da tabela explica que o gestor ou o RH podem ajustar.
- **No backend:** o pedido fora do prazo é recusado do mesmo jeito.
- **Ajuste direto:** o do gestor e o do RH não têm prazo.

Regras de apresentação em `frontend/decisoes_modelo.py` (`linhas_ausencias_fila`) e `frontend/ponto_mensal_modelo.py`
(`limite_prazo`, `aplicar_prazo`, `aviso_prazo`, `texto_prazo`).

## Backend: o que foi alterado e como foi conferido

| Endpoint | Mudança |
|---|---|
| `ferias/{id}/aprovar` e `rejeitar` | Hierarquia para qualquer perfil; a delegação continua valendo |
| `ferias/{id}/verificar_conflito` (GET) | Só quem decide pela hierarquia, e não o próprio |
| `ausencias/{id}/aprovar` e `rejeitar` | Antes, só RH e Admin; agora, pela hierarquia |
| `ausencias/{id}/registrar` | Sem mudança: só RH e Admin |
| `correcoes_ponto/{id}/aprovar` e `rejeitar` e `correcoes_ponto` (GET) | A regra do departamento não exige mais o perfil Gestor |
| `central_de_tarefas` (GET) | Escopo pela hierarquia; devolve `e_superior` e `fila_ausencias_pendentes` (só `id`, `colaborador_id`, `tipo`, `data_inicio`, `data_fim` e `status`) |
| `ponto/prazo_correcao` (GET e PATCH), novo | GET para todos. PATCH só para RH e Admin, auditado |
| `ponto/{id}/solicitar_correcao` e `ponto/solicitar_correcao_dia` | Recusam o dia anterior a hoje − prazo (data de Brasília) |

Tabela nova: `configuracao` (chave única), publicada separadamente, antes dos endpoints.

**Como foi conferido:**
- **Dry-run:** antes de cada publicação.
- **Pull:** o `pull` seguinte trouxe tudo.
- **HTTP:** 401 sem token nos endpoints alterados e no novo.
- **`checar_endpoints.py`:** 200 endpoints autenticados, nenhuma falha.

**Não houve teste com dados reais**, porque ele precisa de um código de acesso.

## Como repetir

```
python tools/testar_decisoes.py      # 60 verificações
python tools/testar_folha_ponto.py   # 36 verificações
python tools/testar_ponto_mensal.py  # 44 verificações
```

Os testes rodam sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.

**Resultado em 11/10/2026:** todos passaram. A bateria inteira do frontend também passou: 14 arquivos, 636 verificações.

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Colaborador que é superior direto vê as filas, com a aba Ausências | ok |
| Sucesso | Aprovar uma ausência; rejeitar com justificativa | ok |
| Sucesso | Superior sem o perfil Gestor: menu Equipe só com a folha | ok |
| Sucesso | Prazo: limite = hoje − prazo; os dias fora dele ficam sem botão, com aviso | ok |
| Sucesso | Prazo: os pedidos em análise continuam visíveis | ok |
| Sucesso | RH salva o prazo em dias e volta para sem limite | ok |
| Erro | Rejeitar sem justificativa: mensagem, sem chamar a API | ok |
| Erro | Recusa do backend (fora da hierarquia) vira alerta | ok |
| Erro | Prazo inválido: a recusa aparece no modal, que continua aberto | ok |
| Erro | Erro ao ler o prazo: a tela segue, e o backend confere | ok |
| Erro | Erro na central: o colaborador continua vendo as próprias pendências | ok |
| Vazio | Quem não é superior vê só Minhas pendências | ok |
| Vazio | O Gestor não vê o "Alterar prazo" | ok |
| Privacidade | A fila de ausências não traz motivo nem comprovante; a própria ausência não tem botão | ok |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-hierarquia-prazo/`](frontend-hierarquia-prazo/):
- `1-superior-central`: colaboradora que é superior, com o grupo Equipe no menu;
- `2-superior-ausencias`;
- `3-rejeitar-ausencia`;
- `4-espelho-fora-do-prazo`;
- `5-rh-prazo`;
- `6-rh-alterar-prazo`;
- `7-ausencias-escuro`;
- `8-prazo-escuro`.
