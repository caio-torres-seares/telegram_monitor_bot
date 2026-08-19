# Deploy na VM (Google Cloud, Always Free)

Passo a passo completo pra tirar o bot do seu PC pessoal e deixar rodando 24/7 numa VM gratuita
do Google Cloud, com segurança em camadas (sessão do Telegram protegida + proteção contra
cobrança inesperada).

---

## Etapa 0 — Preparar localmente (antes de mexer na VM)

**0.1. Gerar a StringSession** (evita deixar `.session` solto no servidor):

```powershell
.venv\Scripts\Activate.ps1
python generate_session.py
```

Vai pedir número/código/2FA como um login novo. No final, copia a linha
`TELEGRAM_STRING_SESSION=...` que ele imprime — guarde num lugar seguro (nunca em texto solto,
nunca compartilhado).

**0.2. Criar o bot de notificação** (se ainda não fez):

- Fale com **@BotFather** no Telegram → `/newbot` → escolha nome/username → copie o token
- Abra o chat com o bot que você criou e mande `/start`
- Rode: `python get_chat_id.py` → copia a linha `TELEGRAM_BOT_CHAT_ID=...`

**0.3. Montar o `.env` final** num bloco de notas local, juntando tudo que a VM vai precisar:

```
TELEGRAM_API_ID=<seu api id>
TELEGRAM_API_HASH=<seu api hash>
TELEGRAM_STRING_SESSION=<gerado no passo 0.1>
OWNER_NAME=<seu nome, igual está em PESSOA0X_NAME>
TELEGRAM_BOT_TOKEN=<gerado no passo 0.2>
TELEGRAM_BOT_CHAT_ID=<gerado no passo 0.2>

PESSOA01_NAME=...
PESSOA01_PHONE_NUMBER=...
PESSOA01_WHATSAPP_API_ID=...
PESSOA01_KEYWORDS=...

# (repita PESSOA02, 03... pra cada pessoa que você já tem)
```

Copie exatamente o que já está no seu `.env` local pras pessoas — só adiciona as 4 linhas novas
(`STRING_SESSION`, `OWNER_NAME`, `BOT_TOKEN`, `BOT_CHAT_ID`).

---

## Etapa 1 — Criar a VM no Google Cloud, sem levar cobrança de susto

### 1.1 — Criar o projeto e ativar o faturamento

1. Acesse [console.cloud.google.com](https://console.cloud.google.com) e crie um projeto novo
   (ex: `telegram-bot-monitor`)
2. Ao tentar usar o Compute Engine pela primeira vez, o Google exige vincular uma conta de
   faturamento — não tem como usar VM sem isso, nem pros recursos do Always Free
3. No cadastro, ele dá um **teste grátis de US$300/90 dias**: durante esse período, qualquer
   cobrança sai desse crédito, nunca do cartão direto. Segundo o próprio Google, passado o prazo
   (ou o crédito) ele não cobra automaticamente — pausa os recursos e só continua se você clicar
   manualmente em "Fazer upgrade". **Não confie só nisso** — as camadas abaixo existem justamente
   pra não depender de eu (ou a documentação do Google) estar 100% certo sobre os detalhes exatos
   da política, que muda com o tempo.

### 1.2 — ANTES de criar a VM: configurar um alerta de orçamento

Faça isso assim que o faturamento for ativado, antes de criar qualquer recurso:

1. Menu → **Faturamento** → **Orçamentos e alertas** → **Criar orçamento**
2. Escopo: selecione só o projeto `telegram-bot-monitor`
3. Valor do orçamento: **R$1** (ou o mínimo aceito)
4. Regras de alerta: mantenha 50%/90%/100% do valor, com e-mail marcado
5. Salvar

Isso avisa por e-mail se algo sair do free tier — mas por padrão só *notifica*, não desliga nada
sozinho. (Existe um "kill switch" automático via Cloud Function que desvincula o faturamento do
projeto ao estourar o orçamento — não implementamos ainda; se quiser essa camada extra, é só
pedir.)

### 1.3 — Backstop financeiro: cartão de limite baixo

Cadastre um **cartão virtual com limite baixíssimo ou zero** como forma de pagamento (Nubank,
Wise, PicPay e a maioria dos bancos digitais permitem cartão virtual com limite ajustável). Se por
algum motivo uma cobrança real fosse tentada, ela simplesmente falha — proteção que não depende de
nenhuma configuração do Google funcionar certo.

### 1.4 — Criar a instância, com atenção a duas armadilhas

Compute Engine → Instâncias de VM → Criar instância:

| Campo | Valor | Por quê |
|---|---|---|
| Nome | `telegram-bot` | livre |
| Região | `us-central1` (ou `us-west1`/`us-east1`) | únicas regiões elegíveis ao Always Free |
| Zona | Automática | sem impacto no custo |
| Série/Tipo de máquina | `E2` → `e2-micro` | única série/tamanho coberto pelo Always Free |
| Disco de inicialização | **Standard persistent disk** (⚠️ não "Balanceado"), 30GB, Debian 12 | só o disco **padrão (HDD)** é gratuito — "Balanceado" (o padrão que o Google sugere) é SSD e **é cobrado** |
| Firewall | Nenhuma porta marcada | o bot só faz conexão de saída, não precisa de porta aberta |

**Armadilha 1 (a que já pegamos)**: o Google seleciona "Disco permanente balanceado" por padrão
na tela de criação — isso não é Always Free. Troque manualmente para "Disco permanente padrão"
antes de criar.

**Armadilha 2**: mesmo com a config 100% correta, a "Estimativa mensal" que aparece na tela **não
reflete o crédito do Always Free** — ela mostra o preço de tabela (sticker price), não o valor que
efetivamente sai na fatura. Ver um número tipo "US$6,11" ali **não** significa que você vai pagar
isso; o crédito é aplicado depois, direto na fatura.

### 1.5 — Confirmar de verdade, sem confiar cegamente em ninguém

Antes de criar, se quiser eliminar a dúvida por completo:
- Confira a [documentação oficial do Always Free](https://cloud.google.com/free/docs/free-cloud-features) com a data de hoje
- Ou abra o chat de suporte do Google Cloud (ícone "?" no console) e pergunte se a config específica está dentro do Always Free

Depois de criar:
1. Espere 1-2 dias
2. **Faturamento → Relatórios**, filtre pelo projeto
3. Deve aparecer o custo bruto da VM + disco, mais uma linha de crédito "Free Tier" cancelando os
   dois → total **US$0,00**
4. Se aparecer qualquer valor > $0, o alerta de orçamento (1.2) te avisa, e o cartão de limite
   baixo (1.3) é a trava final

---

## Etapa 2 — Conectar na VM

Direto no navegador (mais simples, sem precisar configurar chave SSH):

- Na lista de instâncias, clique no botão **SSH** ao lado da VM → abre um terminal no navegador

---

## Etapa 3 — Rodar o setup automático

Dentro do terminal SSH da VM:

```bash
git clone https://github.com/caio-torres-seares/telegram_monitor_bot.git /tmp/setup
bash /tmp/setup/deploy/setup_gcp.sh
```

Isso instala Python/venv/git, cria o usuário de sistema `telegrambot` (sem shell, sem
privilégios), clona o projeto em `/opt/telegram_bot`, cria o virtualenv, instala as dependências e
registra o serviço systemd — mas **ainda não inicia** (falta o `.env`).

---

## Etapa 4 — Colocar o `.env` na VM

Ainda no SSH:

```bash
sudo nano /opt/telegram_bot/.env
```

Cole o conteúdo montado na Etapa 0.3 (botão direito → colar, no terminal SSH do navegador). Salve
com `Ctrl+O`, `Enter`, `Ctrl+X`.

Trave a permissão pra só o usuário de serviço poder ler:

```bash
sudo chown telegrambot:telegrambot /opt/telegram_bot/.env
sudo chmod 600 /opt/telegram_bot/.env
```

---

## Etapa 5 — Ligar o serviço

```bash
sudo systemctl enable --now telegram-bot
sudo systemctl status telegram-bot
```

Deve aparecer `active (running)` em verde. Se aparecer `failed`, ver a tabela de troubleshooting
no fim.

---

## Etapa 6 — Validar que está tudo funcionando

```bash
sudo journalctl -u telegram-bot -f
```

Deve mostrar a lista de pessoas carregadas e "Iniciando monitoramento...". Deixe rodando e, no seu
celular:

- Mande `/kw list` em **Mensagens Salvas** → deve responder na hora
- Force um match de keyword (se tiver como) → deve chegar notificação no chat do bot criado na
  Etapa 0.2

`Ctrl+C` só fecha o acompanhamento dos logs — o serviço continua rodando em background.

---

## Etapa 7 — Limpeza e segurança pós-deploy

- No seu PC, apague o `.env` temporário montado na Etapa 0.3 (ou guarde num gerenciador de
  senhas, nunca em texto solto)
- Confira no Telegram (**Configurações → Dispositivos**) que a nova sessão da VM aparece listada
  — é normal, é o dispositivo novo. Se algo parecer errado no futuro, dá pra encerrar essa sessão
  específica direto por lá, sem afetar seu celular/PC
- Pode desligar o script rodando localmente (`Ctrl+C`) — a VM já assumiu o monitoramento 24/7

---

## Etapa 8 — Atualizando o código depois (sem CI/CD)

Não existe pipeline automático — o `setup_gcp.sh` da Etapa 3 é só o bootstrap inicial, rodado uma
vez. Pra refletir mudanças novas, **não precisa recriar a VM nem rodar o setup de novo**. O fluxo
é:

1. No seu PC: edite, teste localmente, `git commit` + `git push` (como sempre)
2. Na VM (via SSH): `bash /opt/telegram_bot/deploy/update.sh`

Esse script dá `git pull`, reinstala dependências se `requirements.txt` mudou, e reinicia o
serviço. Como `.env` e `data/keywords.json` não são versionados, o `git pull` nunca sobrescreve o
que já está configurado ali — só atualiza código.

Se um dia isso virar chato de fazer manualmente toda vez, dá pra automatizar com GitHub Actions
(workflow que faz SSH na VM e roda o `update.sh` a cada push na `main`) — mas isso exige guardar
uma chave SSH privada como secret do GitHub, ou seja, mais um segredo pra proteger. Pra um projeto
de uma pessoa só, o comando manual costuma valer mais a pena que a superfície extra.

---

## Troubleshooting rápido

| Sintoma | Causa provável | Comando |
|---|---|---|
| `systemctl status` mostra `failed` | Erro no `.env` ou dependência faltando | `sudo journalctl -u telegram-bot -n 50 --no-pager` (mostra o erro exato) |
| Erro `Permission denied` no `.env` | Dono/permissão errados | Repita o `chown`/`chmod` da Etapa 4 |
| Bot conecta mas não reage a `/kw` | `data/keywords.json` sem permissão de escrita | `sudo chown -R telegrambot:telegrambot /opt/telegram_bot` |
| Precisa atualizar o código depois | — | `bash /opt/telegram_bot/deploy/update.sh` (ver Etapa 8) |
