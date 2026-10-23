# Decisões — F16 parcial

## Referência visual
Figma `fph1M5tB4rA4gqfIysSmkn`: seção 248:1405; tela clara 248:1427; abas 248:1479; filtro 248:1487; Nova meta 248:1489; tabela 248:1491; reuniões 248:1561; PDI 248:1579; tela escura 315:3642. Ambos os temas foram consultados via MCP antes da implementação. Usar componentes e tokens existentes de `theme.py`, sem CSS novo.

## Domínios independentes
F16 representa `meta_avaliacao`, `meta_checkin`, `pdi` e `reuniao_individual`. O ciclo anual representa `ciclo_metas`, `pergunta_meta`, `formulario_meta`, `resposta_meta` e `feedback_meta`. A seção “Ciclo anual de metas e feedback” preserva seleção, busca, etapas, respostas e feedback; nenhum dado anual preenche o F16. O modal continua compartilhado com a página administrativa. Menu e destinos de notificações permanecem os existentes.

## Contratos consumidos
Somente os contratos anuais já utilizados: `GET meu_ciclo_metas`, `GET formularios_meta`, `GET formularios_meta/{id}` e `POST formularios_meta/{id}/feedback`. As permissões de feedback continuam determinadas pela resposta e pelo backend. O ciclo individual mantém seus contratos de respostas e envio.

## Bloqueios explícitos
- Não consultar `colaboradores/{id}/plano_carreira`: devolve informações profissionais além das necessárias, incluindo risco de exposição salarial.
- Não chamar `POST metas`: autorização departamental incompleta para Gestor.
- Não chamar check-in sobre liderados: contrato autoriza somente dono ou RH/Admin.
- Não usar `meu_pdi` como fonte de outras pessoas, nem montar PDI da equipe com contratos excessivos.
- Reuniões não fornecem horário/status de agendamento compatíveis com o desenho; não inventar dados nem formulário.
- Filtro Pessoa fica desabilitado, pois não há listagem segura do domínio F16; a busca anual permanece operacional e independente.

Abas alternam apenas os estados de apresentação indisponíveis. Nova meta, Check-in e Registrar reunião permanecem desabilitados. Não apresentar lista vazia como prova de inexistência de metas, nem porcentagem zero como progresso conhecido. Explicações de produto são curtas; detalhes técnicos ficam nesta documentação.

## Isolamento e invalidação
Camada de dados anual em `metas_equipe_dados.py`: caches de 20 segundos com titularidade `(token, usuario_id)`. Verificar identidade antes de desenhar campos; na troca, limpar caches, modal, seleção e campos anuais. Cada entrada também registra identidade, impedindo reutilização isolada de entrada antiga. Erros não são cacheados. Ao salvar feedback, invalidar o formulário e a listagem anual; manter as assinaturas compartilhadas usadas por RH/Admin. Logout remove também estados `cm_*`, `mf_*` e os estados específicos do F16.

## Verificação
AppTest com API simulada e dados exclusivamente sintéticos: navegação, regressão anual, feedback, permissões fornecidas pelo backend, falhas, identidade e limpeza. Streamlit em navegador para comparação clara/escura com estados indisponíveis. Não validar escrita no Xano nesta tarefa: testes HTTP reais do ciclo anual e seus avisos por e-mail ficam não verificados nesta execução. Não declarar F16 integral concluído.
