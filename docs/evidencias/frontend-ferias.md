# Evidências — Férias (tarefas 22 a 25)

Tela construída em 10/10/2026 no frontend Streamlit, a partir do Figma (área do colaborador e fluxo F07
"Férias").

| Nó do Figma | O que é | Código |
|---|---|---|
| 40:22 | Férias: limite por pedido, fracionamento, período aquisitivo e histórico | `frontend/pagina_ferias.py` |
| 221:230 | Modal "Solicitar férias" | idem |
| 108:445 | Férias no escuro | `frontend/theme.py` (`_ESCURO_CSS`) |

As regras de apresentação ficam em `frontend/ferias_modelo.py` (sem Streamlit).

**Endpoints usados**
- `minhas_ferias`;
- `minha_situacao_ferias` (**novo**, só leitura, publicado no Xano em 10/10/2026);
- `ferias/solicitacoes`, que agora aceita a observação opcional para o gestor;
- `ferias/{id}/cancelar`.

## Backend: o que mudou e como foi conferido

- **`minha_situacao_ferias` (GET).** Devolve os números que o pedido de férias já confere, calculados do mesmo
  jeito que no `ferias/solicitacoes`:
  - o limite de dias por pedido (proporcional ao tempo de casa, até o limite da matriz);
  - os períodos já usados e o máximo permitido;
  - o mínimo de dias do próximo período e a antecedência mínima;
  - se já existe um pedido pendente.

  **Não é um saldo de férias:** o backend ainda não desconta os dias já tirados (tarefa 74).
- **`ferias/solicitacoes` (POST).** Ganhou a entrada opcional `observacao` (até 500 caracteres), gravada em
  `observacao_colaborador`. Ela é a "Observação para o gestor" do Figma.
- **Como foi publicado e conferido:**
  - `--dry-run` mostrou só essas duas mudanças (1 endpoint criado, 1 atualizado), e o `push` publicou as duas;
  - o `pull` seguinte só diferiu do repositório na formatação;
  - por HTTP, sem token e com token inválido, a resposta foi 401;
  - `python tools/checar_endpoints.py`: 185 endpoints autenticados, nenhuma falha.
- **O que não foi testado.** Não houve teste com uma conta real, porque o login pede um código enviado por e-mail.
  O cálculo é o mesmo trecho do POST, que já foi testado por HTTP (`docs/evidencias/testes-integracao.md`).

## Como repetir

```
python tools/testar_ferias.py   # 31 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 10/10/2026: 31 de 31.**

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Cartões com "Até 23 dias" por pedido e "2 de 3 usados", e a data do próximo período aquisitivo | ok |
| Sucesso | Histórico com a data certa por situação (solicitada, aprovada, rejeitada, concluída) e a quantidade de dias | ok |
| Sucesso | "Cancelar" só no pedido pendente; cancela o pedido certo | ok |
| Sucesso | Modal: dias pedidos, limite e "2º de 3 permitidos"; envia início, fim, quantidade de dias e observação | ok |
| Bloqueado (25) | Com pedido pendente, "Solicitar férias" fica desligado e a tela explica; o mesmo vale para contrato sem férias e para todos os períodos usados | ok |
| Erro | Antes de enviar, a tela recusa: mais de 30 dias, acima do limite, abaixo do mínimo do período e sem a antecedência mínima. A API não é chamada | ok |
| Erro | Recusa do backend ao pedir (mensagem no modal, que continua aberto) e ao cancelar (alerta) | ok |
| Vazio | Sem pedidos ("Você ainda não pediu férias."); conta sem colaborador | ok |
| Erro | Erro ao carregar vira alerta; sem a situação, o histórico continua e o pedido fica desligado | ok |
| Senha já trocada (25) | Garantida pelo login: a área logada só abre depois da troca da senha temporária (testado em `testar_login_f01.py`); o backend também confere | ok |
| Carregando | Spinner enquanto as férias carregam | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-ferias/`](frontend-ferias/):

| Print | Compare com |
|---|---|
| `1-ferias-com-pedido-pendente` | 40:22 |
| `2-pedido-cancelado` | depois de cancelar: o pedido fica "Cancelada" e o pedido novo é liberado |
| `3-solicitar-ferias` | 221:230 |
| `4-ferias-escuro` e `5-solicitar-ferias-escuro` | 108:445 |

## Decisões e diferenças em relação ao Figma

- **"Dias por pedido" em vez de "Dias disponíveis".** O primeiro cartão mostra "Até N dias", porque o backend não
  tem saldo de férias. Foi decidido em 10/10/2026 mostrar o que existe e abrir a tarefa 74.
- **Calendário.** "Ver calendário" leva à tela Calendário, que ainda não existe (tarefa 56). Por enquanto mostra
  "em construção". A tela Férias não tem calendário próprio (pedido da tarefa 22).
- **Cancelar.** É direto, como no Figma: um pedido cancelado pode ser feito de novo.
- **Aprovar e verificar conflito.** A aprovação, a recusa e a verificação de conflito são do gestor e do RH, em
  outra tela que ainda não existe. Por isso a tarefa 24 fica em parte aberta.
