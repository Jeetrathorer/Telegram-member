# 🤖 Telegram Master Bot — All-in-One Edition

> Broadcast + Scrape + TagAll + Reply Raid + AutoReply + Profile Clone

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/Jeetrathorer/Telegram-member)

---

## ✨ Features

| Feature | Command |
|---|---|
| 📢 Dialog Broadcast | `/broadcast` |
| ⚡ Quick Broadcast | `/quicksend` |
| 🔍 Group Scrape | `/scrape` |
| 🎯 Targeted DM | `/targeted` |
| 🏷 Tag All Members | `/tagall` |
| 📣 Group Promo | `/promo` |
| ⚔️ Reply Raid | `/replyraid` |
| 🤖 AI Auto-Reply | `/autoreply` |
| 👤 Profile Clone | `/cloneprofile` |
| 🧹 Auto Clean | `/autoclean` |

---

## 🚀 Heroku Deploy (Ek Click!)

1. **Upar wala "Deploy to Heroku" button dabao**
2. Yeh cheezein fill karo:
   - `BOT_TOKEN` → @BotFather se banao
   - `API_ID` → https://my.telegram.org/apps
   - `API_HASH` → https://my.telegram.org/apps
   - `ADMIN_ID` → @userinfobot se apna ID pata karo
3. **"Deploy app"** dabao
4. Deploy hone ke baad **"Manage App"** → **Resources** → Worker dyno ON karo

---

## ⚔️ Reply Raid — Kaise Use Karo?

```
1. Kisi user ke message pe reply karo
2. /replyraid likho — raid chalu!
3. Ab jab bhi wo user kuch bhi bhejega, bot automatic gali reply karega

Band karne ke liye:
• Us user ke message pe reply karke /stopraid
• Sab band karne ke liye: /stopraid all
• Raid list dekhne ke liye: /raidlist
```

---

## 📱 Local Run

```bash
pip install -r requirements.txt
python3 bot.py
```

---

## ⚙️ All Commands

```
/broadcast    — dialog broadcast wizard
/quicksend    — jaldi text broadcast
/scrape       — group members scrape
/members      — scraped members list
/targeted     — targeted DM
/replyraid    — reply raid chalu karo
/stopraid     — raid band karo
/raidlist     — active raids list
/autoreply    — AI auto-reply ON/OFF
/tagall       — ek group ke sab members tag karo
/tagallgroups — sabhi groups mein auto tag
/setpromo     — group promo setup
/promo        — groups mein promote karo
/cloneprofile — profile clone
/autoclean    — inactive groups chhodo
/add          — account add karo (OTP)
/accounts     — accounts list
/stats        — statistics
/status       — system status
/myid         — apna Telegram ID
/help         — sab commands
```
