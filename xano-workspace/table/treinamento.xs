// Catalogo de treinamentos (change treinamentos-obrigatorios, D1): os obrigatorios por lei (NRs, a
// orientacao anual sobre assedio da Lei 14.457/2022), de compliance e de desenvolvimento. validade_meses = 0
// significa sem validade (vale uma vez). publico: todos ou so os departamentos de departamento_ids (",1,4,").
// Video (change treinamento-em-video): de onde vem (video_fonte: drive ou youtube), o id do video (o nome
// video_drive_id ficou da primeira versao, so com o Drive; vale para as duas fontes), a duracao em segundos (lida
// do Drive ou da previa do YouTube ao salvar) e quanto a pessoa precisa assistir, em %, para concluir sozinha.
table treinamento {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    timestamp? updated_at?
    text nome filters=trim|max:200
    text? descricao filters=trim|max:1000
    enum categoria {
      values = ["legal", "seguranca", "compliance", "integracao", "desenvolvimento"]
    }

    int carga_horas?=0
    int validade_meses?=0
    bool obrigatorio?=true
    enum publico?=todos {
      values = ["todos", "departamentos"]
    }

    text? departamento_ids filters=trim|max:500
    bool ativo?=true
    text? video_drive_id filters=trim|max:100
    enum video_fonte?=drive {
      values = ["drive", "youtube"]
    }

    int video_duracao?=0
    int video_percentual_minimo?=95
    int criado_por_user_id {
      table = "user"
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
  ]

  guid = "conectahr-treinamento-0001"
}
