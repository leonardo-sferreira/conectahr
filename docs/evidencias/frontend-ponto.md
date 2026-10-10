# Evidências — Ponto (tarefas 19 a 21)

Tela construída em 10/10/2026 no frontend Streamlit, a partir do Figma (área do colaborador e fluxo F06
"Ponto e ausências").

| Nó do Figma | O que é | Código |
|---|---|---|
| 39:18 | Ponto: hoje, saldo, aviso experimental e espelho da semana | `frontend/pagina_ponto.py` |
| 233:1500 | Espelho com o dia justificado por ausência | idem |
| 221:196 | Modal "Solicitar correção de ponto" | idem |
| 221:285 | Modal "Registrar ausência" | idem |
| 108:310 | Ponto no escuro | `frontend/theme.py` (`_ESCURO_CSS`) |

As regras de apresentação ficam em `frontend/ponto_modelo.py` (sem Streamlit).

**Endpoints usados**
- `meu_ponto`;
- `ponto/marcar`;
- `minhas_correcoes_ponto` e `ponto/{id}/solicitar_correcao`;
- `meu_banco_horas`;
- `minhas_ausencias` e `ausencias` (POST).

Todos são do próprio colaborador. O único id enviado é o do registro de ponto na correção, e o backend confere
que o registro é da pessoa.

## Como repetir

```
python tools/testar_ponto.py   # 36 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 10/10/2026: 36 de 36.**

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Horários em milissegundos UTC aparecem no horário de Brasília; horas trabalhadas e saldo por extenso | ok |
| Sucesso | Caixas do dia, saldo do banco de horas, aviso de controle experimental e espelho só da semana atual | ok |
| Ordem (21) | Há um só "Marcar agora", na próxima marcação da ordem; depois de marcar, a próxima passa a ser a seguinte | ok |
| Ordem (21) | Dia completo: sem botão; sem registro hoje: a próxima é a entrada | ok |
| Ordem (21) | Recusa do backend (por exemplo, intervalo mínimo não cumprido) aparece como alerta | ok |
| Sucesso | Correção: envia registro, marcação, horário (17:30 de Brasília = 20:30 UTC, em ms) e motivo; "Editar" já escolhe a marcação | ok |
| Sucesso | Pedido de correção pendente: a linha mostra "Correção em análise" | ok |
| Sucesso | Ausência: envia tipo, datas, motivo da lista do backend e observação; ausência aprovada aparece como dia "JUSTIFICADO" | ok |
| Erro | Correção sem marcação, horário ou motivo, e ausência sem motivo ou com datas invertidas: mensagem no modal, sem chamar a API | ok |
| Erro | Recusa do backend (correção já pendente, CID na observação): mensagem no modal, que continua aberto | ok |
| Erro | Erro ao carregar vira alerta; sem o saldo, o resto da tela continua | ok |
| Vazio | Semana sem marcações; conta sem colaborador ("não marca ponto") | ok |
| Carregando | Spinner enquanto o ponto carrega | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-ponto/`](frontend-ponto/):

| Print | Compare com |
|---|---|
| `1-ponto` | 39:18 |
| `2-depois-de-marcar` | a volta do almoço registrada e o botão passando para a saída |
| `3-solicitar-correcao` | 221:196 |
| `4-registrar-ausencia` | 221:285 |
| `5-ponto-escuro` e `6-correcao-escuro` | 108:310 |

## Decisões e diferenças em relação ao Figma

- **Ausência sem anexo.** O modal não tem o upload do atestado, porque o sistema não recebe arquivo. A tela pede
  que o atestado seja entregue ao RH. O "Motivo" é a lista do backend (consulta, doença, acompanhamento familiar,
  outro) mais uma observação, que não pode ter diagnóstico nem CID.
- **Saldo do banco de horas.** É o saldo total, como o backend calcula, e não "do mês", como no Figma.
- **"Ver atestado".** Não aparece no dia justificado, porque não há arquivo.
- **Data do dia (UTC).** O `ponto/marcar` usa a data em UTC para o registro do dia: no horário de Brasília, o
  "dia" vira às 21h. A tela mostra o registro que o backend de fato altera e o título com a data de Brasília. A
  correção está na tarefa 73.
- **Ainda sem tela.** A aprovação e a recusa das correções e das ausências pelo gestor ou pelo RH são de outra
  tela, que ainda não foi construída. Por isso as tarefas 20 e 21 ficam em parte abertas.
