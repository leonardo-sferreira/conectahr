# Design

## D1. Documentos por contrato (pesquisa de 13/10/2026)

"Obr." gera pendência; "opc." aparece na lista do RH, mas não gera pendência. Prazo de envio em dias depois da admissão.

| Documento | CLT, Temporário e Aprendiz | Estágio | PJ | Base |
|---|---|---|---|---|
| CPF | Obr. (5) | Obr. (5) | Obr. (5) | Identificação no eSocial |
| RG (ou CIN) | Obr. (5) | Obr. (5) | Obr. (5, do representante) | Identificação |
| CTPS | Obr. (5; a digital é o CPF) | — | — | CLT, art. 41 |
| Comprovante de residência | Obr. (5) | Obr. (5) | Obr. (5, da empresa) | Cadastro |
| Comprovante de escolaridade | Obr. (10) | Obr. (5; declaração de matrícula) | — | Cadastro; Lei 11.788/2008 (estágio) |
| ASO admissional | Obr. (1; antes de começar) | — | — | CLT, art. 168; NR-7 |
| Título de eleitor | Obr. de 18 a 70 anos (10) | — | — | Código Eleitoral, art. 7º |
| Certificado de reservista | Opc. de 18 a 45 anos | — | — | Lei 4.375/1964; o sistema não coleta sexo |
| Certidão de nascimento ou casamento | Opc. | — | — | Cadastro e dependentes |
| Termo de compromisso de estágio | — | Obr. (5; com a apólice do seguro) | — | Lei 11.788/2008, arts. 3º e 9º |
| Cartão CNPJ | — | — | Obr. (5) | Cadastro do prestador |
| Contrato social ou CCMEI | — | — | Obr. (5) | Cadastro do prestador |
| Documentação do responsável legal | Obr. até 17 anos, em qualquer contrato (5) | | | CLT, art. 439; LGPD, art. 14 |

Guarda: 5 anos depois do desligamento; ASO, 20 anos (`docs/lgpd/retencao.md`, F04 e F10), com revisão manual.

Fontes consultadas: [Gupy](https://www.gupy.io/blog/checklist-14-documentos-para-admissao-de-um-funcionario), [Convenia](https://blog.convenia.com.br/documentos-para-admissao/), [Jornal Contábil](https://jornalcontabil.com.br/noticia/documentos-para-admissao-esta-pensando-em-contratar-conheca-os-obrigatorios/), [vagas.com.br](https://www.vagas.com.br/blog/?p=768), Lei 11.788/2008 ([cópia da FURG](https://prograd.furg.br/images/Documentos/lei_estagios.pdf)), [cartilha de Jovem Aprendiz do Nube](https://www.nube.com.br/media/arquivos/portal/informacoes/Cartilha_J-A.pdf) e [Managefy](https://managefy.com.br/blog/cadastro-pj/) (PJ). São referências de mercado e a lei de estágio; a lista é sugestão acadêmica, a confirmar com o jurídico e a convenção coletiva de cada empresa.

## D2. Regras geradas por função, sem duplicar

`ConectaHR/semear_documentos_obrigatorios` (rodada pela CLI) grava a regra só se não houver regra ativa geral (sem cargo nem departamento) para o mesmo documento e contrato. Autor: o primeiro Admin ativo ou, sem ele, o primeiro RH. Auditada (`semear_documentos_obrigatorios`).

## D3. RG e CIN

A Carteira de Identidade Nacional substitui o RG. Na lista de pendentes obrigatórios, um RG aprovado cumpre a regra da CIN e vice-versa.

## D4. Campos dos tipos novos

| Tipo | Campos |
|---|---|
| Título de eleitor | Número (12 dígitos), zona, seção, UF |
| Certidão | Nascimento ou casamento; matrícula e data opcionais |
| Termo de compromisso de estágio | Instituição de ensino, início (pode ser futuro), fim, nº da apólice do seguro |
| Cartão CNPJ | CNPJ (14 dígitos), razão social; data da consulta opcional |
| Contrato social ou CCMEI | Tipo da empresa (MEI, Ltda., SLU, S.A., outra), data do registro ou da última alteração |
