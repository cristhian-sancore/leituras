# 💧 SAEMI SaaS

**Sistema de Leitura de Água como Serviço**

Plataforma SaaS multi-tenant para empresas de saneamento (SAEs/DAEs/SAAEs) gerenciarem leituras de hidrômetros, cálculo tarifário e geração de arquivos de retorno.

## 🚀 Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | HTML + Vanilla JS + CSS |
| Backend | FastAPI (Python 3.11) |
| Banco | PostgreSQL 15 |
| Proxy | Nginx |
| Deploy | Docker Compose |

## 📦 Como Rodar

```bash
# 1. Clonar
git clone https://github.com/cristhian-sancore/leituras.git
cd leituras

# 2. Configurar
cp .env.example .env
# Editar .env com suas senhas

# 3. Subir
docker-compose up -d --build

# 4. Acessar
# http://localhost:8080
```

## 🔐 Features

- ✅ Multi-tenant (várias empresas isoladas)
- ✅ Autenticação JWT com 3 roles (admin, supervisor, leiturista)
- ✅ Importação de arquivos .REM
- ✅ Cálculo tarifário por faixas progressivas
- ✅ Exportação de arquivos .RET (formato D01/SIA)
- ✅ Dashboard com progresso por rota
- ✅ Persistência de leituras no PostgreSQL
- ✅ GPS do leiturista
- ✅ Log de auditoria

## 📋 API Docs

Após subir, acesse: `http://localhost:8080/api/docs`

## 📁 Estrutura

```
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── models.py
│       ├── auth/
│       ├── routers/
│       └── services/
├── frontend/
│   ├── index.html (login)
│   ├── register.html
│   ├── app.html (dashboard)
│   ├── css/
│   └── js/
└── nginx/
    ├── Dockerfile
    └── nginx.conf
```

## 📄 Licença

Propriedário - Todos os direitos reservados.
