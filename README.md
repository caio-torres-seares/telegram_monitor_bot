# 🤖 Telegram Message Monitor (Userbot)

Um bot de monitoramento flexível e personalizável escrito em Python.

Este projeto funciona como um Userbot (usa sua conta pessoal de usuário, não uma conta de bot), permitindo automatizar a leitura de mensagens em tempo real. Embora o exemplo padrão seja para "monitorar promoções", este código pode ser adaptado para qualquer finalidade.

# ⚠️ Como funciona (O Conceito)
É fundamental entender que este bot "enxerga" exatamente o que você enxerga.

✅ O que ele faz: Monitora mensagens novas que chegam na sua conta do Telegram (em grupos, canais ou conversas privadas onde você está presente).

❌ O que ele NÃO faz: Ele não consegue ler mensagens de grupos privados onde você não é membro, nem "invadir" canais fechados.

🛠 O Poder do Userbot: Diferente de bots tradicionais (que precisam ser administradores para ler mensagens em grupos), este script tem permissão de leitura em qualquer lugar que sua conta pessoal tenha.

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Possíveis Usos](#-possiveis-usos)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Como Usar](#-como-usar)
- [Personalizações](#-personalizações)
- [Troubleshooting](#-troubleshooting)

## ✨ Funcionalidades

- ✅ Monitora múltiplos grupos do Telegram simultaneamente
- ✅ Busca por palavras-chave personalizáveis
- ✅ Organização de grupos por categorias (Hardware, Ofertas Gerais, Periféricos)
- ✅ Notificações automáticas via Telegram
- ✅ Notificações automáticas via WhatsApp (CallMeBot)
- ✅ Sistema de categorias para monitoramento seletivo
- ✅ Fácil configuração via arquivo `.env`

## 💡 Possíveis Usos (Ideias)
Você pode adaptar as palavras-chave e a lógica para monitorar qualquer coisa:

- 🔍 Monitor de Promoções: (Configuração padrão) Encontre "RTX 4060" ou "Erro de Preço" instantaneamente.

- 💼 Vagas de Emprego: Monitore grupos de vagas por termos como "Java Senior", "Remoto" ou "Freelance".

- 📰 Notícias e Finanças: Receba alertas sobre "Dólar", "Bitcoin" ou notícias específicas em canais de informação.

- 🎓 Acadêmico: Fique de olho em grupos da faculdade por termos como "Prova", "Nota" ou "Edital".

## 📦 Pré-requisitos

- Python 3.8 ou superior
- Conta do Telegram (Obrigatório)
- Número de WhatsApp (para receber notificações, mas pode desativar o envio por WhatsApp)
- API Key do CallMeBot (para WhatsApp)

## 🚀 Instalação

### 1. Clone o repositório ou baixe os arquivos

```bash
git clone <seu-repositorio>
cd monitor-promocoes-telegram
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Obtenha suas credenciais do Telegram (API_ID e API_HASH)

#### Passo 1: Acesse o site do Telegram
1. Abra seu navegador e acesse: [https://my.telegram.org](https://my.telegram.org)
2. Você verá uma tela pedindo seu número de telefone

#### Passo 2: Faça login
1. Digite seu número de telefone **com código do país** (ex: +5511999999999)
2. Clique em "Next"
3. Você receberá um código de verificação no seu Telegram
4. Digite o código recebido

#### Passo 3: Crie um aplicativo
1. Após fazer login, clique em **"API development tools"**
2. Você verá um formulário. Preencha:
   - **App title:** `Monitor de Promoções` (ou qualquer nome)
   - **Short name:** `monitor_promo` (sem espaços)
   - **Platform:** Selecione `Desktop`
   - **Description:** (opcional) `Bot para monitorar promoções`
3. Clique em **"Create application"**

#### Passo 4: Copie suas credenciais
Após criar, você verá uma tela com suas credenciais:

```
App api_id: 12345678
App api_hash: abcdef1234567890abcdef1234567890
```

**⚠️ IMPORTANTE:**
- Guarde essas credenciais em local seguro
- **NUNCA** compartilhe com ninguém
- Você pode usar essas mesmas credenciais em múltiplos projetos
- Se precisar ver novamente, basta acessar [my.telegram.org](https://my.telegram.org) novamente

---

### 4. Configure o CallMeBot para WhatsApp (NOTIFICATION_API_ID)

O CallMeBot permite enviar mensagens para seu WhatsApp gratuitamente através de uma API simples.

#### Passo 1: Verifique o número atual do CallMeBot

⚠️ **IMPORTANTE:** O CallMeBot costuma mudar de número com frequência!

Antes de adicionar aos contatos, **sempre verifique o número atual** em:
- 🌐 Site oficial: [https://www.callmebot.com/blog/free-api-whatsapp-messages/](https://www.callmebot.com/blog/free-api-whatsapp-messages/)

**Número atual (verificado em Nov/2025):** `+34 644 87 21 57`

#### Passo 2: Adicione o bot aos contatos
1. Abra seu WhatsApp
2. Adicione o número verificado no site aos seus contatos
   - Salve como "CallMeBot" ou qualquer nome
3. **Importante:** O número deve estar salvo nos contatos!

#### Passo 2: Envie a mensagem de ativação
1. Abra uma conversa com o número do CallMeBot (**+34 644 87 21 57**)
2. Envie **exatamente** esta mensagem:
   ```
   I allow callmebot to send me messages
   ```
3. **Atenção:** 
   - A mensagem deve ser em inglês
   - Deve ser exatamente como está escrito
   - Não adicione emojis ou pontos extras

#### Passo 3: Aguarde a resposta
Você receberá uma mensagem automática em alguns segundos como esta:

```
CallMeBot API Activated for 5511999999999
Your apikey is: 1234567

You can now send messages using the API.
https://api.callmebot.com/whatsapp.php?phone=5511999999999&text=This+is+a+test&apikey=1234567


Send Stop to pause the Bot.
Send Resume to enable it again.
```

#### Passo 4: Anote sua API Key
- Copie o número que aparece em **"Your APIKEY is"**
- No exemplo acima, seria: `1234567`
- Essa será sua `NOTIFICATION_API_ID`

#### Passo 5: Teste se funciona
Copie a URL que o bot enviou e cole no seu navegador, substituindo `[seu_numero]` pelo seu número com código do país:

```
https://api.callmebot.com/whatsapp.php?phone=+5511999999999&text=teste&apikey=1234567
```

Se tudo estiver correto, você receberá uma mensagem de "teste" no WhatsApp!

**⚠️ PROBLEMAS COMUNS:**

❌ **Não recebi a mensagem do bot:**
- Verifique se salvou o número nos contatos
- Aguarde até 5 minutos
- Tente enviar a mensagem novamente
- Certifique-se de que copiou a mensagem exatamente

❌ **API Key não funciona:**
- Verifique se copiou o número correto
- Teste com a URL fornecida pelo bot
- Seu número deve estar com código do país (+55 para Brasil)

❌ **"Invalid API Key":**
- Você pode ter digitado errado no arquivo `.env`
- Solicite uma nova API Key enviando a mensagem novamente

**💡 DICA:** O CallMeBot é gratuito mas tem limites:
- Máximo de mensagens por dia
- Pode ter delay de alguns segundos
- Para uso profissional, considere APIs pagas

## ⚙️ Configuração

### 1. Crie o arquivo `.env`

Copie o arquivo `.env.example` e renomeie para `.env`:

```env
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890

NOTIFICATION_PHONE_NUMBER=5511999999999
NOTIFICATION_API_ID=1234567
```

**Importante:** 
- `NOTIFICATION_PHONE_NUMBER` deve incluir o código do país (ex: 55 para Brasil)
- Não compartilhe seu arquivo `.env` publicamente

### 2. Configure as palavras-chave

Edite o arquivo `config.py` e defina as palavras-chave que deseja monitorar:

```python
KEYWORDS = ['5060 ti', '5070', 'rtx 4090', 'watercooler']
```

**Dica:** Para maior precisão, inclua variações da mesma palavra:
```python
KEYWORDS = ['water cooler', 'watercooler', 'water-cooler']
```

### 3. Escolha a categoria

No arquivo `config.py`, defina qual categoria monitorar:

```python
CATEGORIA_ATIVA = Categoria.HARDWARE  # ou OFERTAS_GERAIS, PERIFERICOS, TODOS
```

## 📁 Estrutura do Projeto

```
monitor-promocoes-telegram/
├── main.py                 # Arquivo principal do bot
├── config.py              # Configurações de grupos e keywords
├── enums/
│   └── categorias.py      # Enum com categorias disponíveis
├── .env                   # Variáveis de ambiente (NÃO COMMITAR!)
├── .env.example          # Exemplo de configuração
├── README.md             # Esta documentação
└── minha_sessao.session  # Sessão do Telegram (gerado automaticamente)
```

### Arquivos principais

#### `main.py`
Contém a lógica principal do bot:
- Monitoramento de mensagens
- Detecção de palavras-chave
- Envio de notificações

#### `config.py`
Configurações do usuário:
- Lista de palavras-chave
- Categoria ativa
- IDs dos grupos organizados por categoria

#### `enums/categorias.py`
```python
from enum import Enum

class Categoria(Enum):
    HARDWARE = "hardware"
    OFERTAS_GERAIS = "ofertas_gerais"
    PERIFERICOS = "perifericos"
    TODOS = "todos"
```

## 🎯 Como Usar

### Primeira execução

1. Execute o script:
```bash
python main.py
```

2. Na primeira vez, será solicitado:
   - Seu número de telefone do Telegram
   - Código de verificação enviado pelo Telegram
   - (Opcional) Senha de 2FA, se configurada

3. O bot começará a monitorar automaticamente

### Descobrir IDs de grupos do Telegram

Existem 3 métodos para descobrir os IDs dos grupos. Escolha o que preferir:

---

#### 🔹 Método 1: Usando o próprio bot (RECOMENDADO)

Este é o método mais fácil e preciso.

**Passo 1:** No arquivo `main.py`, **descomente** esta linha dentro da função `monitor_messages`:

```python
@client.on(events.NewMessage(chats=grupos_para_monitorar))
async def monitor_messages(event):
    # Descomente a linha abaixo ↓
    print(f"Nome: {event.chat.title} | ID: {event.chat_id}")
```

**Passo 2:** Execute o bot:
```bash
python main.py
```

**Passo 3:** O bot começará a mostrar no console TODOS os grupos onde ele recebe mensagens:

```
Nome: Ofertas Tech Brasil | ID: -1001234567890
Nome: Pelando Promoções | ID: -1001079131412
Nome: Hardware Barato | ID: -1001592709849
```

**Passo 4:** Copie os IDs que você quer monitorar e adicione no `config.py`

**Passo 5:** Depois de coletar os IDs, **comente a linha novamente** para não poluir o console:
```python
# print(f"Nome: {event.chat.title} | ID: {event.chat_id}")
```

**💡 DICA:** Deixe o bot rodando por alguns minutos para capturar IDs de grupos com menos movimento.

---

#### 🔹 Método 2: Através de bots especializados

Use bots públicos que mostram informações de grupos:

**Passo 1:** No Telegram, adicione o bot **@getidsbot** ao grupo que você quer descobrir o ID

**Passo 2:** Envie o comando `/start` no grupo

**Passo 3:** O bot responderá com as informações:
```
Chat info:
ID: -1001234567890
Type: supergroup
Title: Ofertas Tech Brasil
```

**Passo 4:** Copie o ID e remova o bot do grupo (se quiser)

**Outros bots úteis:**
- `@userinfobot`
- `@RawDataBot`
- `@JsonDumpBot`

---

#### 🔹 Método 3: Através da API do Telegram (Avançado)

**Passo 1:** Encaminhe uma mensagem do grupo para o bot **@userinfobot**

**Passo 2:** Ele mostrará as informações incluindo o ID

**OU**

**Passo 1:** Acesse no navegador (substitua SEU_TOKEN pelo token de um bot seu):
```
https://api.telegram.org/botSEU_TOKEN/getUpdates
```

**Passo 2:** Procure no JSON retornado por `"chat":{"id":-100XXXXXXX}`

---

### 📝 Notas sobre IDs de grupos:

- ✅ **Grupos privados:** Você precisa estar participando para monitorar
- ✅ **Canais públicos:** Você pode usar o @ também (ex: `@ofertas_tech`)
- ⚠️ **IDs nunca mudam**, mesmo se o grupo mudar de nome


## 🔧 Personalizações

### Adicionar novo grupo

No arquivo `config.py`:

```python
GRUPOS = {
    Categoria.HARDWARE: [
        -1001592709849,  # Grupo existente
        -1001234567890,  # Novo grupo aqui
    ],
}
```

### Criar nova categoria

1. Adicione no `enums/categorias.py`:
```python
class Categoria(Enum):
    NOTEBOOKS = "notebooks"
```

2. Configure no `config.py`:
```python
GRUPOS = {
    Categoria.NOTEBOOKS: [
        -1001111111111,
        -1001222222222,
    ],
}
```

### Desativar WhatsApp

Comente a linha no `main.py`:

```python
async def enviar_mensagem(texto):
    await enviar_telegram(texto)
    # await enviar_whatsapp(texto)  # Desativado
```

### Personalizar mensagem de alerta

Edite a variável `texto_alerta` no `main.py`:

```python
texto_alerta = (
    f"🚨 OFERTA: {matched.capitalize()}\n"
    f"📢 {event.chat.title}\n"
    f"💰 {event.raw_text}\n"
    f"🔗 Link: https://t.me/c/{event.chat_id}/{event.id}"
)
```

## 🐛 Troubleshooting

### Erro: "No module named 'telethon'"
```bash
pip install telethon
```

### Erro: "API_ID not found"
Verifique se o arquivo `.env` está na raiz do projeto e configurado corretamente.

### Não recebe notificações no WhatsApp
1. Confirme que completou o processo do CallMeBot
2. Verifique se a API Key está correta no `.env`
3. Teste manualmente acessando:
```
https://api.callmebot.com/whatsapp.php?phone=SEU_NUMERO&text=teste&apikey=SUA_KEY
```

### Bot desconecta sozinho
Isso pode ocorrer se você fizer login em outro dispositivo. Mantenha apenas uma sessão ativa ou recrie a sessão:
```bash
rm minha_sessao.session
python main.py
```

### Mensagens não são detectadas
1. Verifique se o grupo está na lista da categoria ativa
2. Confirme que as palavras-chave estão em minúsculas
3. Teste com uma palavra-chave simples primeiro

## 📝 Notas Importantes

- ⚠️ **Nunca compartilhe** seu arquivo `.env` ou `minha_sessao.session`
- ⚠️ Respeite os termos de uso do Telegram
- ⚠️ Não faça spam ou abuse do bot
- ⚠️ O CallMeBot tem limite de mensagens gratuitas
- ✅ Mantenha o bot rodando em um servidor ou computador sempre ligado para monitoramento 24/7

## 📄 Licença

Este projeto é de código aberto para uso pessoal.


**Sinta-se livre para fazer um fork e adaptar para suas necessidades!**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/caio-seares)