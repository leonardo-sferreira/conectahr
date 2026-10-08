# Plano de resposta a incidentes com dados pessoais

**Referência:** LGPD, art. 48; Resolução CD/ANPD nº 15/2024 (comunicação de incidente de segurança em até **3 dias úteis**).
**Situação:** plano técnico de projeto acadêmico. Prazos e critérios devem ser validados com o jurídico.

Um **incidente** é qualquer evento que possa expor, alterar, perder ou tornar inacessíveis dados pessoais sem autorização. Exemplos: token de acesso vazado, conta invadida, e-mail enviado à pessoa errada, chave de serviço publicada no repositório, backup perdido.

## 1. Quem faz o quê

| Papel | Quem | Responsabilidade |
|---|---|---|
| **Detecta** | Qualquer pessoa do grupo, o RH, um colaborador, ou um alerta do sistema | Avisa o encarregado **no mesmo dia**, sem tentar investigar sozinha |
| **Avalia** | Encarregado, com o responsável técnico do backend | Classifica o risco (seção 3), decide se há comunicação obrigatória e conduz o plano |
| **Contém** | Responsável técnico do backend (Admin) | Executa as ações da seção 4 |
| **Comunica** | Encarregado, com apoio do jurídico | Avisa a ANPD e os titulares (seção 5) |
| **Registra** | Encarregado | Faz o registro interno (seção 6), mesmo quando **não** comunica |

O contato do encarregado está no [aviso de privacidade](aviso-de-privacidade.md). Enquanto ele for provisório, o ponto de contato é o responsável técnico do grupo.

## 2. Como um incidente é detectado

Fontes que o sistema já oferece:

- **Alerta de acesso suspeito:** quando alguém entra com sucesso depois de 3 ou mais senhas erradas, o sistema avisa o titular por e-mail e grava `alerta_acesso_suspeito` na auditoria (ver [monitoramento.md](../monitoramento.md)).
- **`GET auditoria`** (RH e Admin): filtra por usuário, ação e resultado. Procure rajadas de `login_senha_invalida`, `login_codigo_invalido`, `autoaprovacao_bloqueada` e `acessar_arquivo_documento` fora do padrão.
- **`GET status_operacional`:** filas acumuladas, falhas de e-mail e tentativas bloqueadas.
- **Avisos externos:** o titular que recebe um e-mail de segurança que não reconhece, um colega que viu um dado indevido, ou um aviso de um fornecedor (Xano, Brevo, GitHub).

## 3. Como avaliar o risco

Responda, nesta ordem:

1. **Dados pessoais foram afetados?** Se não (por exemplo, só a documentação da API), registre e encerre.
2. **Que dados?** Dados de **saúde** (atestados, ASO, laudos), **financeiros** (conta, salário), **documentos** (CPF, RG, CTPS) e de **menores de 18 anos** elevam o risco.
3. **Quantas pessoas?** Uma pessoa, um departamento ou todos.
4. **Os dados estavam protegidos?** Senha em hash e IP não permitem uso direto; documento e conta bancária permitem fraude.
5. **Há risco ou dano relevante ao titular?** Fraude, discriminação, constrangimento, perda de emprego, dano à imagem.

| Nível | Quando | O que fazer |
|---|---|---|
| **Baixo** | Sem risco relevante (ex.: aviso enviado ao colaborador errado, sem dado sensível, e-mail recuperado) | Contém, registra internamente, **não comunica** a ANPD. Decisão e justificativa ficam no registro |
| **Médio** | Dados pessoais comuns de poucas pessoas, sem sinal de uso indevido | Contém, registra, avalia com o jurídico se comunica e avisa os titulares afetados |
| **Alto** | Dado sensível, financeiro ou de documentos, ou de muitas pessoas, ou de menores, ou com uso indevido confirmado | Contém **na hora** e comunica a ANPD e os titulares em até **3 dias úteis** |

Na dúvida entre dois níveis, **trate como o mais alto** e decida depois com mais informação.

## 4. Como conter (ações que o sistema já oferece)

| Situação | Ação | Como |
|---|---|---|
| **Token de acesso vazado** | Revogar a sessão do token | O titular usa `auth/sessoes/{id}/encerrar` ou "encerrar outras sessões"; o Admin pode desativar a conta com `usuarios/{id}/status`, que **revoga todas as sessões**. O token passa a ser recusado na hora |
| **Conta invadida** | Desativar a conta e redefinir a senha | `usuarios/{id}/status` (desativa e revoga as sessões); depois reativar e o titular redefine a senha em "Esqueci minha senha" |
| **E-mail da conta trocado de forma indevida** | O alerta chega ao e-mail anterior; reverter a troca | `usuarios/{id}` (PATCH); a auditoria `atualizar_usuario` mostra o valor anterior e o novo |
| **Chave de serviço exposta (ex.: `BREVO_API_KEY`)** | Gerar chave nova no serviço e atualizar o segredo do Xano | Painel do Brevo e variáveis de ambiente do Xano; revogar a chave antiga |
| **Segredo commitado no repositório** | Revogar o segredo no serviço de origem. Reescrever o histórico do git **não** basta (o repositório é público e foi copiado) | Trocar o segredo; só então tratar o histórico |
| **Token de swagger ou documentação exposta** | Manter `swagger = {active: false}` em todos os grupos | `python tools/checar_endpoints.py` reprova swagger ligado ou token no arquivo |
| **Arquivo sensível acessado indevidamente** | Identificar quem abriu e quando | `GET auditoria`, filtro `acessar_arquivo_documento` (quando a auditoria de acesso a arquivos estiver publicada) |

Depois de conter, **preserve as evidências**: exporte o trecho da auditoria e anote horários. Não apague registros.

## 5. Como comunicar

**Prazo:** até **3 dias úteis** a partir do conhecimento do incidente com risco ou dano relevante, para a ANPD e para os titulares afetados.

**À ANPD** (pelo canal de comunicação de incidentes da autoridade), informe:

- a descrição do incidente e as datas (ocorrência, descoberta);
- a natureza e a categoria dos dados afetados, e se há dados sensíveis ou de menores;
- o número de titulares afetados (ou estimativa);
- os riscos e danos possíveis;
- as medidas de contenção e de prevenção adotadas;
- o contato do encarregado.

**Aos titulares**, em linguagem simples:

> Identificamos um incidente de segurança no ConectaRH em **[data]**. **[O que aconteceu, em uma frase.]** Os dados envolvidos foram: **[lista]**. Já tomamos estas medidas: **[contenção]**. O risco para você é: **[descrição]**. Recomendamos: **[o que a pessoa deve fazer, como trocar a senha]**. Dúvidas: **[contato do encarregado]**.

A mensagem não deve repetir o dado exposto (por exemplo, o número do documento).

## 6. Registro interno

Todo incidente é registrado, **inclusive os que não são comunicados**. O registro **não contém dados pessoais**, só descrições e identificadores internos. Modelo:

| Campo | Conteúdo |
|---|---|
| Identificador | `INC-AAAA-NNN` |
| Datas | Ocorrência, descoberta, contenção, encerramento |
| Quem detectou e como | Papel, não nome |
| Descrição | O que aconteceu, sem dados pessoais |
| Dados e titulares afetados | Categorias e quantidade |
| Nível de risco e justificativa | Baixo, médio ou alto, conforme a seção 3 |
| Contenção | Ações e horários |
| Comunicação | ANPD: sim/não e por quê. Titulares: sim/não e por quê |
| Causa e prevenção | O que será mudado para não repetir |

Os registros reais ficam fora do repositório público. Os **exercícios** (simulações) são registrados em [../evidencias/lgpd.md](../evidencias/lgpd.md).

## 7. Exercício

Pelo menos uma vez por ciclo, o grupo simula um incidente e percorre este plano do começo ao fim. O primeiro exercício, de **token de acesso vazado**, está registrado em [../evidencias/lgpd.md](../evidencias/lgpd.md).
