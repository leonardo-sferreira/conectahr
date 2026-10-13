# Proposal

## Why

A tela Benefícios do colaborador mostra quatro indicadores (ativos, quanto a empresa paga, desconto e encerrados) e cartões com valores. O usuário pediu (13/10/2026) uma tela de apresentação: só o número de benefícios ativos e, abaixo, um cartão por benefício no formato da FAQ, com o nome e o que ele é; ao clicar, a descrição, os links úteis e os materiais que o RH anexou (ex.: guia do plano de saúde). O RH precisa cadastrar esse conteúdo.

## What Changes

- **Colaborador:** fica só o indicador "Benefícios ativos"; somem "A empresa paga por mês", "Desconto no seu pagamento", "Encerrados", os valores dos cartões e o histórico. Cada benefício ativo vira um item que abre e fecha (como a FAQ): o nome e o tipo; aberto, a descrição, os links e os materiais.
- **RH e Admin:** "Editar" no Catálogo, com nome, tipo, operadora, descrição (até 2000 caracteres), links (até 10, só https) e materiais (anexar e remover arquivos PDF, JPG ou PNG de até 10 MB).
- **Materiais no Supabase Storage** (D1): o mesmo bucket privado e o mesmo fluxo de `anexo-de-arquivos`, na pasta `beneficios/`; abre por link assinado de 5 minutos, com auditoria.
- **Backend:** `beneficio.links` (json) e a descrição até 2000; tabela `beneficio_arquivo`; `beneficios/{id}/arquivos/envio` POST, `beneficios/{id}/arquivos` POST, `beneficio_arquivos/{id}/remover` POST e `beneficio_arquivos/{id}/abrir` GET; `meus_beneficios` e `beneficios` GET devolvem links e materiais (sem o endereço do arquivo).

## Non-goals

- A FAQ por benefício (tarefa 85) segue sem tela.
- Valores e descontos continuam na aba "Por colaborador" do RH.
- Figma: registrado em `docs/figma-pendencias.md`.

## Impact

- Backend: `table/beneficio.xs`, `table/beneficio_arquivo.xs` (nova), `api/conecta_rh_colaboradores/beneficios/id_PATCH.xs`, `beneficios_POST.xs`, `beneficios_GET.xs`, `meus_beneficios_GET.xs` e os quatro endpoints novos.
- Frontend: `pagina_beneficios.py`, `beneficios_modelo.py`, `api_client.py`.
- Documentação: `docs/regras-de-negocio.md`, `docs/lgpd/operadores.md`, `docs/figma-pendencias.md`.
