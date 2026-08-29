table user {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }
  
    timestamp? updated_at?
    timestamp? ultimo_acesso?
    email email filters=trim|lower
    password senha filters=max:64|min:8 {
      sensitive = true
      visibility = "private"
    }
  
    bool senha_primeiro_acesso?=true
    text? otp_codigo filters=trim|max:6 {
      sensitive = true
      visibility = "private"
    }

    timestamp? otp_expira_em {
      visibility = "private"
    }

    int? otp_tentativas?=0 {
      visibility = "private"
    }

    text nome filters=trim|min:2|max:100
    enum perfil?=Colaborador {
      values = ["Admin", "RH", "Colaborador", "Gestor"]
    }
  
    bool ativo
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
    {type: "btree|unique", field: [{name: "email", op: "asc"}]}
  ]

  guid = "YgL5OL4NN8Yj4CKod78Qr-X_mJk"
}