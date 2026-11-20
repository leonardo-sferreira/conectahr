# Design — F18 parcial

Figma lido pelo MCP antes de codificar: seção 248:2671, tela 248:2694, período 248:2747,
CSV 248:2749, cards 248:2751, gráficos 248:2766/248:2794, clima 248:2814; escuro 315:3925.

## Decisões

1. Só Gestor. Reutilizar topbar, hero, indicadores, cartões, barras e tokens de theme.py.
   Acrescentar nesse tema apenas a apresentação das barras verticais do F18.
2. Período único Últimos 6 meses: mês corrente e cinco anteriores, do primeiro dia do primeiro
   mês até hoje em Brasília. Seletor representa somente essa opção verificada no Figma.
   Horas extras no mês usa o mês corrente até hoje; não é a soma dos seis meses.
3. Folha: pessoas retornadas por folha_ponto/pessoas, exceto o próprio e desligados. Não aplicar
   o filtro de subordinados diretos do F14 nem anunciar cobertura departamental completa.
   Snapshot atual de pessoas visíveis, não quadro histórico da organização.
4. Cada mês soma exclusivamente horas_extras gravadas dos IDs desse recorte. Ausência de
   registros de qualquer membro, valor nulo/inválido, resposta malformada ou erro deixa o mês
   indisponível. Zero só é mostrado quando há registros válidos para todos e a soma é zero.
   Não implica fechamento do mês, aprovação de horas extras ou ausência de dias sem marcação.
5. Ausências: quantidade de registros/solicitações Aprovada ou Registrado que sobrepõem o
   período, deduplicados por id; não dias nem pessoas. Fundamentação: ausência é entidade de
   solicitação; docs/indicadores.md e calcular_indicadores contam registros, sem ponderar duração.
   Não copiar a fórmula de absenteísmo. Qualquer mês ausente ou registro elegível inválido ou
   conflitante impede o gráfico completo; não apresentar contagem parcial como total.
6. Banco: organograma identifica exatamente um departamento cujo gestor_colaborador_id é o
   colaborador autenticado. Somar somente seus colaboradores não desligados, exceto o próprio,
   consultando cada id no endpoint autorizado. Não usar user_id como colaborador_id. Sem
   identificação inequívoca, catálogo válido ou todas as respostas numéricas, usar indisponível.
   Saldo corrente do contrato (créditos menos débitos), sem recorte temporal nem soma do saldo
   diário da folha. Não aplicar expiração ou regras novas aos lançamentos.
7. Coberturas separadas com quantidade e descrição. Nunca unir bancos e folha por suposição.
   A spec Indicadores sem identificação de pessoas exige mínimo padrão de cinco por grupo;
   aplicar esse piso na apresentação de cada recorte, sem consultar configuração administrativa.
   Isso não substitui autorização do backend nem configura o mínimo do Xano.
8. Absenteísmo e clima sempre —. Manter a frase de privacidade do Figma e esclarecer ausência
   de consulta autorizada. CSV desabilitado: exportação precisa ser auditada e o contrato é
   RH/Admin. Nenhuma geração local, comentário de pesquisa ou chamada a endpoint restrito.
9. Cache curto de 60 s por endpoint e sessão, somente projeções necessárias; botão Atualizar.
   Falhas não viram listas vazias; 401 interrompe carregamento e segue o tratamento do app.
   Cada fonte/mês falha isoladamente. Cliente atual já retenta 429; consultas sequenciais e
   cache evitam rajadas adicionais. Logout e troca de conta descartam filtros e dados F18.

## Divergências e dependências abertas

Figma prevê absenteísmo, horas extras, banco, clima e CSV. Backend permite horas/ausências
no escopo autorizado da folha e banco departamental. Não garante o departamento inteiro na
folha, jornada histórica para absenteísmo, clima ao Gestor ou exportação auditada do F18.
Não misturar calendário (departamento da ficha) nem indicadores globais com os recortes.
Nomes de pessoas, IDs técnicos, documentos, dados bancários e respostas de clima não aparecem.

## Verificação

Modelo, contratos simulados e AppTest: perfil, menu, seis meses/virada de ano, sinais de banco,
somatório, deduplicação, fonte parcial, ausência de cobertura, mês vazio, grupos pequenos,
privacidade, indicadores bloqueados e CSV desabilitado. Chrome/Streamlit em claro/escuro e
comparação ao Figma. Regressões: folha, ponto, ponto mensal, clima, F14, F15, F17 e login.
HTTP real por perfil permanece não verificado sem sessão de teste disponibilizada.

