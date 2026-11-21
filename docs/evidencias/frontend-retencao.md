# Retenção e anonimização (tarefa 64 da change `concluir-frontend-streamlit`)

**Data:** 21/11/2026. **Figma:** [290:902](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=290-902), modais
[290:1187](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=290-1187) e
[290:1213](https://www.figma.com/design/fph1M5tB4rA4gqfIysSmkn?node-id=290-1213).

## O que entrou

- **`retencao` GET** (novo, só RH e Admin, só leitura): numa chamada, devolve os documentos com guarda vencida, as pessoas
  da tela (desligados e donos desses documentos), os prazos de guarda e quem tem processo em aberto. Usa as mesmas
  condições que `colaboradores/{id}/anonimizar` confere. Não devolve CPF, contato, arquivo nem número de documento.
  `checar_endpoints`: 295, sem falha.
- **Página "Retenção e anonimização"** no menu RH (`frontend/pagina_retencao.py` e `retencao_modelo.py`):
  - abas com as contagens;
  - documentos ("Para revisar" ou "Retido: processo em aberto");
  - desligados (pronto, prazo vigente, processo em aberto ou anonimizado);
  - modal de anonimizar, com o aviso de que não há volta e a justificativa de pelo menos 5 caracteres;
  - modal "Não dá para anonimizar", com o motivo e o atalho para os documentos retidos;
  - "Ver registro" dos anonimizados.

## Testes

| Teste | Resultado |
|---|---|
| `python tools/testar_retencao.py`: regras, abas, modais, justificativa curta, recusa do backend, vazio, erro, acesso | 24/24 |
| `testar_menu`, `medir_contraste`, `smoke_frontend`, `testar_pagina_rep_p` | 12/12, 0 pares, ok, 28/28 |

Prints com API simulada e dados fictícios, em [`frontend-retencao/`](frontend-retencao/), para comparar com o Figma
(`figma-290-902`): `1-documentos`, `2-desligados`, `3-modal-anonimizar` e `4-modal-recusa`.

Diferenças do Figma:
- "Ver registro" mostra a data e diz onde a operação ficou registrada (auditoria, `anonimizar_colaborador`), sem abrir a
  auditoria, que é do Admin;
- o tipo do documento usa os rótulos do cadastro, e não as categorias "Cadastro", "Contrato" e "Saúde".

**HTTP com login (21/11/2026), contas de teste Admin e Colaborador:**
- `retencao` GET: Admin 200 com `hoje`, `documentos`, `pessoas`, `guardas` e `processo_aberto`; nenhuma pessoa traz CPF ou
  contato e nenhum documento traz arquivo ou número;
- Colaborador 403 e, com a conta promovida a Gestor só durante o teste, Gestor 403;
- `colaboradores/{id}/anonimizar` de quem não está desligado: 400 com "desligado" na mensagem, antes de gravar; justificativa
  de 3 caracteres: 400. Nenhuma anonimização foi executada.
