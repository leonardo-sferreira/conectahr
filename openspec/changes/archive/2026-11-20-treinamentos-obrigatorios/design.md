# Design

## Context

Ver proposal.md. O registro de treinamento é dado de carreira (finalidade F12, como avaliações e PDI) e não tem dado sensível.

## Decisions

### D1. Dados

- **`treinamento`:**
  - nome, descrição e categoria (`legal`, `seguranca`, `compliance`, `integracao`, `desenvolvimento`);
  - carga horária e validade em meses (0 = sem validade);
  - se é obrigatório e para quem: `publico` `todos` ou `departamentos`, com `departamento_ids` como texto ",1,4,", o mesmo padrão já usado para conjuntos de ids;
  - `ativo`.
- **`treinamento_conclusao`:** treinamento, pessoa, `concluido_em`, `valido_ate` (calculado), instrutor, link do certificado e quem registrou. Só inclusão.

### D2. Catálogo

`treinamentos` GET devolve numa chamada o catálogo, as conclusões, as pessoas não desligadas e os departamentos; a matriz é montada na tela. POST e `{id}` PATCH:
- validam o nome, a categoria, os limites e pelo menos um departamento quando o público é por setor;
- PATCH também desativa;
- são auditados.

### D3. Conclusões

`treinamentos/{id}/conclusoes` POST recebe uma lista de pessoas, a data, o instrutor e o certificado.
- Recusa:
  - data futura;
  - lista vazia;
  - treinamento inativo.
- `valido_ate` = data + validade em meses, por ano e mês, com o dia limitado a 28. Evita data inexistente (31/02); a perda de até 3 dias é a favor da segurança.
- Pula quem foi desligado e quem já tem registro na mesma data.
- Avisa cada pessoa no sino.
- Audita uma linha por turma, com as quantidades.

### D4. Situação (na tela)

- Pela conclusão mais recente de cada treinamento:
  - **pendente:** nunca registrado;
  - **em dia;**
  - **vencendo:** até 30 dias para vencer;
  - **vencido.**
- Sem validade, uma conclusão basta.
- Obrigatório para a pessoa: ativo, obrigatório, e para todos ou para o departamento dela.

### D5. Telas (Figma, seção 22, 549:1319)

- **"Treinamentos"** (menu RH):
  - **Matriz** (549:1321): indicadores, filtro de departamento, busca e a tabela pessoa × obrigatório;
  - **Catálogo:** tabela com "Editar", e o catálogo sugerido quando vazio;
  - **Registrar conclusão:** o formulário do modal 550:1370, como aba;
  - **Vencimentos;**
  - o modal "Novo treinamento" (550:1325).
- **"Meus treinamentos"** (550:1415, menu de todos): os obrigatórios com a situação e o histórico com o link do certificado.

## Risks / Trade-offs

- [Registro errado não se apaga] → registrar de novo vale (a mais recente conta); a auditoria guarda tudo.
- [Validade com o dia limitado a 28] → até 3 dias antes do exato, a favor da segurança.
- [Erro de execução do XanoScript na aritmética de datas] → `tools/testar_conformidade_http.py` e um registro de teste com login.

## Migration Plan

1. Tabelas (`CREATE`).
2. Endpoints (`CREATE`).

Rollback: apagar os endpoints.
