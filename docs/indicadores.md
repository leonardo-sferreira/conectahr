# Painel de indicadores e exportações — ConectaRH

Documentação da implementação do item 7.7: indicadores e exportação CSV/PDF
respeitando permissões e auditoria.

## Endpoints

- **`GET indicadores`** (RH/ADMIN): painel completo. Aceita `data_inicio`/`data_fim`
  opcionais (padrão: últimos 12 meses) para as métricas de período.
- **`GET indicadores/exportar_csv`** (RH/ADMIN): mesmo conjunto de dados, formatado
  como texto CSV no campo `csv` da resposta.

Ambos exigem perfil RH/ADMIN e geram evento de auditoria (`consultar_indicadores` /
`exportar_indicadores_csv`), com o período consultado na justificativa.

## Cobertura de indicadores

- **Headcount**: colaboradores ativos e total.
- **Turnover**: admissões e desligamentos no período, percentual (desligamentos /
  headcount ativo atual — fórmula simples, não pondera pelo headcount médio do
  período).
- **Absenteísmo**: ausências aprovadas no período / headcount ativo, em percentual.
- **Distribuição por departamento**: colaboradores ativos por departamento.
- **Horas extras**: soma de `registro_ponto.horas_extras` no período.
- **Ponto, férias, ausências, documentos, auditoria, avaliações, metas, PDIs**:
  contagem por status/resultado relevante de cada domínio.

Implementação: `db.query { return: {type: "count"} }` para contagens diretas (evita
buscar listas inteiras só para contar), confirmado funcionando nesta plataforma. O
cálculo fica em uma function reutilizável (`ConectaHR/calcular_indicadores`), chamada
tanto pelo painel quanto pela exportação, para não duplicar a lógica.

## Limitação: exportação PDF

Não implementada. XanoScript, nesta plataforma, não tem um filtro ou primitiva nativa
de renderização de PDF — gerar um PDF real exigiria um serviço externo de
renderização (ex.: um endpoint HTML→PDF de terceiros chamado via `api.request`), que
está fora do escopo desta mudança. A exportação CSV cobre o requisito de "exportações
respeitando permissões e auditoria" de forma completa e verificada.

## Verificado ao vivo

- Painel retorna valores coerentes com os dados reais do workspace (headcount,
  distribuição por departamento, contagens por status em todos os domínios).
- Filtro de período explícito (`data_inicio`/`data_fim`) funciona.
- Exportação CSV gera texto bem formado, consistente com o painel.
- Ambos geram evento de auditoria consultável via `GET auditoria` (item 7.11).
