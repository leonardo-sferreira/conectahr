# Evidências — Benefícios (tarefa 82)

> **A conferir com o Figma.** O Figma estava fora do ar. A tela segue o padrão das telas já aprovadas (cartões do
> Onboarding e tabelas do RH) e precisa ser desenhada lá.

## O que a tela faz (`frontend/pagina_beneficios.py`, menu "Benefícios", para todos)

- **Meus benefícios** (todos os perfis): os ativos, cada um com o tipo, a operadora, desde quando, quanto a empresa
  paga e quanto é descontado; o histórico dos encerrados; e os totais do mês.
- **Catálogo** (RH e Admin): cadastrar um benefício (nome, tipo, operadora e descrição) e ativar ou desativar.
  Desativado não aceita novos vínculos; os atuais continuam.
- **Por colaborador** (RH e Admin): os benefícios da pessoa, "Vincular benefício" (do catálogo, com o valor da empresa,
  o desconto do colaborador, o início e o fim opcional) e "Encerrar", que não apaga: preenche o fim e o benefício vai
  para o histórico.

Regras de apresentação em `frontend/beneficios_modelo.py`.

## Backend: o que foi criado e como foi conferido

**Tabelas** (push separado, antes dos endpoints):
- `beneficio` (o catálogo);
- `colaborador_beneficio` (o vínculo, com valor da empresa, desconto do colaborador, vigência e quem criou ou encerrou).

**Endpoints**, todos com sessão conferida e auditoria nas escritas:

| Endpoint | Quem | O que faz |
|---|---|---|
| `meus_beneficios` (GET) | qualquer perfil com ficha | Só os da própria pessoa |
| `beneficios` (GET e POST) | RH e Admin | Catálogo; nome repetido é recusado |
| `beneficios/{id}/status` (PATCH) | RH e Admin | Ativa ou desativa |
| `colaboradores/{id}/beneficios` (GET e POST) | RH e Admin | Lista e vincula. Benefício ativo, pessoa não desligada, sem outro vínculo vigente do mesmo benefício, fim depois do início |
| `colaborador_beneficios/{id}/encerrar` (POST) | RH e Admin | Fim e desativação, sem apagar |

**Como foi conferido:**
- **Tabelas:** o dry-run só criou as 2 novas.
- **Endpoints:** o dry-run criou 7 endpoints e não alterou nenhum existente.
- **Publicação:** push, e o `pull` seguinte trouxe tudo.
- **HTTP:** 401 sem token e com token inválido nos 7.
- **`checar_endpoints.py`:** 198 endpoints, nenhuma falha.

**Não houve teste com dados reais.**

## Como repetir

```
python tools/testar_beneficios.py   # 21 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 11/10/2026: 21 de 21.** Toda a bateria do frontend continua passando.

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Moeda em reais; ativos e histórico; totais só dos ativos; fim no passado conta como encerrado | ok |
| Sucesso | O colaborador vê só os seus, sem catálogo nem abas do RH | ok |
| Sucesso | RH: catálogo com situação; desativar; cadastrar | ok |
| Sucesso | RH: só pessoas não desligadas; vincular só benefício ativo, com valor, desconto e início; encerrar com a data de fim | ok |
| Erro | Sem tipo, sem benefício e fim antes do início: mensagem, sem chamar a API | ok |
| Erro | Recusa do backend (benefício já vigente) no modal, que continua aberto | ok |
| Erro | Conta sem ficha; erro ao carregar vira alerta | ok |
| Vazio | "Você ainda não tem benefício ativo." | ok |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-beneficios/`](frontend-beneficios/):
- `1-meus-beneficios`;
- `2-catalogo`;
- `3-por-colaborador`;
- `4-vincular`;
- `5-meus-escuro`.
