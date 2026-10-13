# Design

## Contexto

`documento` tem `numero_documento`, `estado_de_emissao`, `data_emissao`, `data_validade` e `observacao`, iguais para todo tipo. O modal pede tipo, número, data de emissão e o arquivo. A conferência do RH mostra pessoa, documento e data de envio, sem o número nem as datas.

## Decisões

### D1. Campos por tipo (pedido do usuário, 13/10/2026)

As colunas existentes continuam para o que é comum (número, UF, emissão, validade); o resto vai em `dados`. "Obr." = obrigatório.

| Tipo | Campos |
|---|---|
| RG | Número (obr.), órgão emissor (obr.), UF (obr.), data de expedição (obr.) |
| CPF | Número do CPF (obr.; dígitos verificadores; igual ao da ficha) |
| CIN | Número, que é o CPF (obr.; igual ao da ficha), órgão emissor (obr.), UF (obr.), data de expedição (obr.), validade (obr.) |
| CNH | Número de registro, 11 dígitos (obr.), categoria (obr.: A, B, AB, C, D, E, AC, AD, AE, ACC), UF (obr.), data de emissão (obr.), validade (obr.) |
| CTPS | Número (obr.; na digital é o CPF), série e UF (opcionais, só na carteira de papel) |
| ASO admissional | Data do exame (obr.), resultado (obr.: Apto ou Inapto), CRM do médico (obr.) |
| Laudo de deficiência | Data do laudo (obr.), CRM do médico (obr.) |
| Certificado profissional | Curso ou certificação (obr.), instituição (obr.), data de conclusão (obr.), validade (opcional) |
| Comprovante de residência | Data de emissão (obr.; dos últimos 90 dias) |
| Comprovante de escolaridade | Nível (obr.: fundamental, médio, técnico, superior, pós-graduação, mestrado, doutorado), curso (opcional), instituição (obr.), data de conclusão ou da declaração (obr.) |
| Registro profissional | Conselho (obr.; ex.: CRC, CREA, OAB), número (obr.), UF (obr.), validade (opcional) |
| Documentação migratória | Número do RNM (obr.), data de emissão (obr.), validade (opcional; há RNM por prazo indeterminado) |
| Certificado de reservista | Número do certificado (obr.), data de emissão (obr.) |
| Documentação do responsável legal | Nome do responsável (obr.), CPF do responsável (obr.; dígitos verificadores), vínculo (obr.: pai, mãe, tutor, curador, outro) |
| Outro | Que documento é (obr.), número, data de emissão e validade (opcionais) |

### D2. Minimização (LGPD)

Laudo de deficiência e ASO não pedem CID, diagnóstico nem tipo de deficiência: o RH confere no arquivo. Do ASO, só o resultado que a admissão precisa (apto ou inapto). Do responsável legal, só nome, CPF e vínculo.

### D3. Validação no backend

`ConectaHR/validar_campos_documento` recebe o tipo, as colunas comuns e `dados`, e devolve `erro` (a primeira falha, em português) e `dados` montado só com as chaves do tipo (texto aparado, até 100 caracteres). `documentos` POST chama a função e, quando há CPF a conferir (tipo CPF, CIN ou responsável legal), também `ConectaHR/validar_cpf`, nos dois casos a partir do endpoint (padrão do workspace: função não chama função). O CPF do tipo CPF e o da CIN precisam ser iguais ao da ficha. Holerite e informe (lançados pelo RH) não passam pela função.

### D4. Datas

Datas comparadas como texto "Y-m-d" no dia de Brasília: emissão não pode ser futura; validade não pode ser anterior à emissão (regra que já existia); comprovante de residência com emissão nos últimos 90 dias (prática comum de RH, para o endereço estar atual).

### D5. Frontend

O catálogo de D1 fica em `documentos_modelo.CAMPOS` e a tela monta os campos a partir dele; a validação da tela repete a do backend para o aviso sair antes do envio, e o backend continua sendo a regra. A conferência do RH mostra os campos preenchidos do tipo, com os mesmos rótulos.
