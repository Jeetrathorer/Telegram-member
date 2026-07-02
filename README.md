# 🤖 Telegram Master Bot — All-in-One Edition

A powerful Telegram bot for group scraping, targeted DM, broadcast, and member management.

## ✨ Features

- **📢 Dialog Broadcast** — media + text + buttons → all dialogs
- **🎯 Targeted DM** — scraped members ko DM bhejo (auto-delete after send)
- **🔍 Group Scraper** — members + active chatters + poll voters
- **🏷 Tag All Members** — greeting / shayri se mention karo
- **📣 Group Promo** — apna group sabhi groups mein promote karo
- **🤖 AI Auto-Reply** — mentions pe automatic smart reply
- **👤 Profile Clone** — kisi ki profile sabhi accounts pe copy karo
- **🎵 Music Bot Join** — scrape se pehle bots group mein auto-add
- **🔗 Force Join** — bot start pe 3 groups auto-join
- **🚫 Blacklist** — groups blacklist karo (na scrape, na join)

## 👑 Two-Tier Master System

### Main Master (Full Access)
- Sabhi accounts dekh sakta hai
- User Masters add/remove kar sakta hai
- Force join groups set kar sakta hai
- Music bots set kar sakta hai
- Group blacklist manage kar sakta hai
- Sabhi scrape jobs aur members dekh sakta hai

### User Master (Limited Access)
- Sirf apne add kiye accounts use kar sakta hai
- Scrape, Broadcast, DM — sirf apne accounts se
- Max 5 DM per account enforce hota hai
- Sirf apni scrape jobs dikhti hain

## 🚀 Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. First run (setup wizard)
```bash
python3 bot.py
```

Setup wizard mein yeh set karo:
- Telegram API ID & Hash (my.telegram.org se)
- Bot Token (BotFather se)
- Main Master Telegram ID (apna)

### 3. Bot commands (Main Master)

| Command | Description |
|---------|-------------|
| `/setmainmaster <ID>` | Main Master change karo |
| `/addusermaster <ID>` | User Master add karo |
| `/removeusermaster <ID>` | User Master remove karo |
| `/listusermaster` | User Masters list |
| `/setforcejoin @g1,@g2,@g3` | Force join groups set karo |
| `/forcejoin` | Abhi force join karwao |
| `/setmusicbots @bot1,@bot2` | Music bots set karo |
| `/blacklist @group` | Group blacklist karo |
| `/unblacklist @group` | Blacklist se hatao |
| `/listblacklist` | Blacklisted groups list |

## 📁 Data Storage

- **Accounts** → `~/tg_master/data.json` (JSON)
- **Members/Scrape Jobs** → `~/tg_master/master.db` (SQLite)
- **Sessions** → `~/tg_master/sessions/`

> ⚠️ In files ko `.gitignore` mein add kar diya gaya hai — ye GitHub pe push nahi honge.

## 🌐 Deploy on Heroku / Replit

### Heroku
```bash
heroku create
git push heroku main
heroku ps:scale worker=1
```

### Replit
Simply run `python3 bot.py` — Replit mein background run hota rahega.

> **Note:** Sessions `~/tg_master/` mein save hote hain. Heroku pe disk restart pe delete ho sakti hain — persistent storage ke liye MongoDB atlas free tier recommend hai.

## ⚠️ Important

- `data.json` aur `sessions/` folder kabhi GitHub pe push mat karo
- Har account ki session file sensitive hoti hai
- Ye bot Telegram ke rules ke anusaar use karo
