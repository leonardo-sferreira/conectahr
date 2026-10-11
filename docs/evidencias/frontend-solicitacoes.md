# Evidências — Solicitações ao RH (tarefa 47)

Tela construída em 11/10/2026 no frontend Streamlit, depois de um problema real: um colaborador pediu a
correção do CPF pelo Perfil, e o pedido não aparecia em nenhuma tela do RH. O pedido estava gravado
(`solicitacoes` POST), mas a tela do RH não existia, e o menu do RH nem tinha esse item.

> **A conferir com o Figma.** O Figma (225:5299 "RH — Solicitações ao RH" e 206:1072 "RH — Aplicar mudança no
> cadastro") estava fora do ar quando a tela foi feita. A tela segue o padrão das telas de RH já aprovadas
> (Ausências 243:846 e Conferência 418:1108) e a descrição da seção 8: *"O RH vê todos os pedidos dos colaboradores
> na fila de Solicitações ao RH, com prazo de 15 dias. Ao abrir um pedido, compara o valor atual com o novo e
> decide"*. As diferenças que aparecerem na conferência entram no `design.md`.

| O que é | Código |
|---|---|
| Lista: abas Em aberto, Atendidas e Indeferidas; filtros de tipo e departamento; prazo de 15 dias | `frontend/pagina_solicitacoes.py` |
| Modal "Analisar solicitação": o antes e o depois; "Aplicar e atender"; "Indeferir" | idem |
| Central de Pendências do RH e do Admin: quantas estão em aberto, com atalho | `frontend/pagina_central.py` |

As regras de apresentação ficam em `frontend/solicitacoes_modelo.py` (sem Streamlit).

**Endpoints usados** (nenhuma mudança no backend)
- `solicitacoes` (GET, RH e Admin);
- `solicitacoes/{id}/atender` e `solicitacoes/{id}/indeferir`;
- `colaboradores/{id}` (PATCH, só o RH), para aplicar a alteração cadastral;
- `colaboradores` e `organograma`.

## Como a alteração cadastral é aplicada

1. O pedido do Perfil é um texto com "Campo:", "Valor atual:", "Novo valor:" e "Motivo:". A tela lê esse texto e
   mostra o antes e o depois.
2. O campo pedido (nome, CPF, e-mail, nascimento ou telefone) já vem preenchido com o valor novo. No caso do
   endereço, o RH ajusta os campos um a um. Se o texto não seguir o formato, aparecem todos os campos.
3. **"Aplicar e atender"** grava o cadastro completo (`colaboradores/{id}` PATCH, com as validações do backend, como
   CPF repetido) e **só então** atende o pedido. Se o cadastro for recusado, o pedido continua em aberto.
4. "Indeferir" exige justificativa e não mexe no cadastro.
5. O Admin vê e pode indeferir, mas não aplica no cadastro, porque o backend só deixa o RH. Ninguém decide o próprio
   pedido.

Os pedidos LGPD ficam fora desta tela: eles têm a tela "Pedidos LGPD".

## Como repetir

```
python tools/testar_solicitacoes.py   # 34 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 11/10/2026: 34 de 34.** Os outros testes do frontend continuam passando.

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Lê campo, valor atual, novo e motivo; texto fora do formato não inventa campos | ok |
| Sucesso | Em aberto: o prazo mais curto primeiro, sem pedidos LGPD; prazo de 15 dias e atrasados destacados | ok |
| Sucesso | Filtros de tipo e departamento; aba Atendidas com "Ver" | ok |
| Sucesso | CPF: o valor novo já vem preenchido; grava o cadastro completo e só depois atende | ok |
| Sucesso | Endereço: mostra o pedido e os campos para o RH ajustar | ok |
| Sucesso | Declaração: atende com justificativa, sem formulário de cadastro | ok |
| Sucesso | Central do RH mostra "N solicitações ao RH em aberto", com atalho | ok |
| Erro | CPF inválido: mensagem, nada é gravado | ok |
| Erro | Recusa ao gravar o cadastro (CPF repetido): o pedido não é atendido | ok |
| Erro | Indeferir sem justificativa: mensagem | ok |
| Erro | Erro ao carregar vira alerta | ok |
| Próprio pedido | Quem fez o pedido não tem "Analisar" | ok |
| Escopo | O Admin não aplica no cadastro; o colaborador não abre a tela | ok |
| Vazio | "Nenhum pedido nesta aba." | ok |
| Carregando | Spinner enquanto os pedidos carregam | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-solicitacoes/`](frontend-solicitacoes/):
- `1-central-atalho`: o aviso na Central do RH;
- `2-solicitacoes`: a lista;
- `3-analisar-cpf`: o pedido de CPF, com o antes e o depois;
- `4-analisar-declaracao`: um pedido de declaração;
- `5` e `6`: tema escuro.
