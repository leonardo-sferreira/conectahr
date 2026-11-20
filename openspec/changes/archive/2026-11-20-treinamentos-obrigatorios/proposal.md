# Proposal

## Why

O usuário pediu (20/10/2026) a prioridade 1 da pesquisa de mercado: funções que a lei exige. Duas obrigações pedem treinamento com registro:
- a Lei 14.457/2022 exige orientação sobre assédio e violência no trabalho pelo menos uma vez por ano;
- as NRs exigem treinamentos com validade (NR-35, NR-10, NR-12...) para quem está exposto.

O ConectaRH não registra treinamento nenhum, então a empresa não sabe quem está em dia nem prova o que fez.

## What Changes

- **Dados** (D1): tabelas `treinamento` (catálogo com validade e público) e `treinamento_conclusao`.
- **Catálogo** (D2): listar, criar e editar; catálogo sugerido para começar.
- **Conclusões** (D3): registrar uma turma de uma vez, com a validade calculada no backend e aviso a cada pessoa.
- **A pessoa** (D4): "Meus treinamentos", com os obrigatórios, a situação e o histórico com certificado.
- **Telas** (D5): "Treinamentos" (RH: matriz, catálogo, registrar conclusão e vencimentos) e "Meus treinamentos".

## Non-goals

- Plataforma de cursos (vídeos, provas): o treinamento acontece fora; o sistema registra.
- Upload do certificado: guarda o link, como os demais documentos externos.
- Aviso automático de vencimento: o plano não tem tarefas agendadas; a matriz e a aba Vencimentos mostram.
- Turmas com agenda e lista de presença.

## Capabilities

### New Capabilities

### Modified Capabilities
- `conectahr`: catálogo de treinamentos obrigatórios, registro de conclusões com validade e situação por pessoa.

## Impact

- **Backend:**
  - tabelas novas: `treinamento` e `treinamento_conclusao`;
  - endpoints novos: `treinamentos` GET e POST, `treinamentos/{id}` PATCH, `treinamentos/{id}/conclusoes` e `meus_treinamentos`.
- **Frontend:** `api_client.py`, `treinamentos_modelo.py`, `pagina_treinamentos.py`, `pagina_meus_treinamentos.py`, `app.py` e `theme.py`.
- **Figma:** seção 22 (549:1319).
- **Testes:** `tools/testar_treinamentos.py` e `tools/testar_conformidade_http.py`, que cobre também o canal de denúncias e a NR-1.
- **Documentação:**
  - `docs/regras-de-negocio.md` (seção 21);
  - `docs/lgpd/registro-de-operacoes.md` (F12 e cobertura);
  - `docs/figma-pendencias.md`.
- **Dependência:** parte da branch da NR-1 (#87), que parte do canal de denúncias (#86).
