# 🤖 Remnant Bot

Bot para Discord desenvolvido em Python com suporte a comandos de prefixo (`*`) e slash commands (`/`).

---

## ⚙️ Tecnologias

- [Python](https://www.python.org/) — linguagem principal
- [discord.py](https://discordpy.readthedocs.io/) — framework do bot
- [aiosqlite](https://aiosqlite.omnilib.dev/) — banco de dados assíncrono
- [python-dotenv](https://pypi.org/project/python-dotenv/) — variáveis de ambiente

---

## 📦 Funcionalidades

### 🛡️ Moderação (`admin`)
- `*clear` / `/clear` — apaga mensagens do canal
- `*kick` / `/kick` — expulsa um membro do servidor
- `*ban` / `/ban` — bane um membro do servidor
- `*reloadall` — recarrega todos os módulos do bot

### 📢 Avisos (`embed_builder`)
- `/aviso` — cria e envia um embed personalizado para um canal *(apenas administradores)*
- `*embed` — versão por prefixo do criador de embeds

### 🔍 Informações (`info`)
- `*scan` / `/scan` — exibe perfil detalhado de um usuário
- `*avatar` / `/avatar` — mostra o avatar ampliado de um membro
- `*server` / `/server` — exibe informações do servidor

### 🛠️ Geral (`geral`)
- `*ping` / `/ping` — latência e uptime do bot
- `/help` — lista todos os comandos disponíveis
- `/info` — estatísticas técnicas do bot

### 📋 Logs (`logs`)
- Registra automaticamente mensagens apagadas
- Registra edições de mensagens
- Registra bans e saídas de membros

---

## 🗂️ Estrutura do Projeto

```
📁 meu bot/
├── bot.py               # Inicialização e configuração principal
├── .env                 # Variáveis de ambiente (não versionar)
├── bot.db               # Banco de dados SQLite
└── cogs/
    ├── admin/
    │   ├── admin.py
    │   └── embed_builder.py
    ├── system/
    │   ├── events.py
    │   └── logs.py
    └── utility/
        ├── geral.py
        └── info.py
```

---

## 🚀 Como Rodar

**1. Clone o repositório**
```bash
git clone https://github.com/InnerVoid4635/remnant-bot.git
cd remnant-bot
```

**2. Instale as dependências**
```bash
pip install -r requirements.txt
```

**3. Configure o `.env`**
```env
TOKEN=seu_token_aqui
LOG_CHANNEL_ID=id_do_canal_de_logs
```

**4. Inicie o bot**
```bash
python bot.py
```

---

## 📝 Changelog

### v2.0.0
- Migração completa para `aiosqlite` (banco assíncrono)
- Adicionados slash commands em todos os módulos
- Refatoração: events movidos para `cogs/system/events.py`
- Reorganização das pastas de cogs em `admin/`, `system/` e `utility/`
- Adicionado `embed_builder` com suporte a modal interativo
- `reloadall` agora suporta sincronização opcional da árvore (`*reloadall True`)
- Remoção do `database.py` legado

### v1.0.0
- Estrutura inicial do bot
- Comandos de prefixo: `clear`, `kick`, `ban`
- Log básico de comandos com `sqlite3`
