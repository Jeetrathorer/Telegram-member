#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║         Telegram Master Bot — All-in-One Edition                 ║
║                                                                  ║
║  Features:                                                       ║
║   • Dialog Broadcast  — media + text + buttons → all dialogs    ║
║   • Group Scrape      — group members ko SQLite mein store karo  ║
║   • Targeted DM       — scraped members ko DM bhejo             ║
║   • Tag All Members   — greeting / shayri se mention karo        ║
║   • Group Promo       — apna group sabhi groups mein promote karo║
║   • AI Auto-Reply     — mentions pe automatic smart reply        ║
║   • Profile Clone     — kisi ki naam+photo sabhi accounts pe     ║
║   • Auto Clean        — inactive/banned groups chhodo            ║
║   • Account Manager   — OTP login via bot ya CLI                 ║
║                                                                  ║
║  INSTALL:                                                        ║
║    pkg install python -y                                         ║
║    pip install telethon pyTelegramBotAPI requests                ║
║                                                                  ║
║  RUN:                                                            ║
║    python3 tg_master.py                                          ║
║                                                                  ║
║  BOT COMMANDS:                                                   ║
║    /broadcast    — dialog broadcast wizard (media+text+buttons)  ║
║    /quicksend    — jaldi text broadcast (all dialogs)            ║
║    /scrape       — group members scrape karo                     ║
║    /members      — scraped members dekho                         ║
║    /targeted     — scraped members ko targeted DM bhejo          ║
║    /groupadd     — contact add karo → invite link bhejo          ║
║                    (privacy wale ko fallback DM, 5/acc limit)    ║
║    /tagall       — ek group ke sab members tag karo              ║
║    /tagallgroups — sabhi groups mein auto tag karo               ║
║    /setpromo     — group promo text + link set karo              ║
║    /promo        — sabhi groups mein promo bhejo                 ║
║    /autoreply    — AI auto-reply ON/OFF karo                     ║
║    /cloneprofile — kisi ki profile sabhi accounts pe copy karo   ║
║    /autoclean    — inactive/banned groups chhodo                 ║
║    /add          — naya account add karo (OTP via bot)           ║
║    /accounts     — accounts list                                 ║
║    /targets      — targets list                                  ║
║    /addtarget    — target add karo                               ║
║    /deltarget    — target delete karo                            ║
║    /history      — broadcast history                             ║
║    /stats        — statistics                                    ║
║    /status       — system status                                 ║
║    /listadmins   — admins list                                   ║
║    /addadmin     — admin add karo                                ║
║    /removeadmin  — admin remove karo                             ║
║    /myid         — apna Telegram ID                              ║
║    /help         — sab commands                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
import sys
import sqlite3
import time
import threading
import re
from datetime import datetime, timezone

# ── Dependency check ───────────────────────────────────────────────────────────
missing = []
try:
    from telethon import TelegramClient, events
    from telethon.sessions import StringSession
    from telethon.errors import (
        FloodWaitError, PhoneCodeExpiredError, PhoneCodeInvalidError,
        SessionPasswordNeededError, UserBannedInChannelError,
        ChatWriteForbiddenError, PeerFloodError, UserDeactivatedBanError,
        AuthKeyDuplicatedError, UserPrivacyRestrictedError,
        UserIsBlockedError, InputUserDeactivatedError,
    )
    from telethon.tl.types import (
        InputMediaUploadedPhoto, InputMediaUploadedDocument,
        DocumentAttributeVideo, DocumentAttributeFilename,
        InputUser,
    )
    from telethon.tl.functions.channels import (
        GetParticipantsRequest, InviteToChannelRequest,
    )
    from telethon.tl.functions.contacts import AddContactRequest
    try:
        from telethon.errors import (
            UserNotMutualContactError, UserChannelsTooMuchError,
            UserBannedInChannelError,
        )
    except ImportError:
        UserNotMutualContactError = Exception
        UserChannelsTooMuchError  = Exception
        UserBannedInChannelError  = Exception
    try:
        from telethon.tl.functions.messages import GetPollVotesRequest as GetPollVotersRequest
    except ImportError:
        from telethon.tl.functions.messages import GetPollVotersRequest
    from telethon.tl.types import (
        ChannelParticipantsSearch,
        UserStatusOnline, UserStatusOffline,
        Channel, Chat,
        MessageMediaPoll,
    )
    try:
        from telethon.tl.types import InputMessagesFilterPoll
    except ImportError:
        from telethon.tl.types import InputMessagesFilterEmpty as InputMessagesFilterPoll
except ImportError:
    missing.append("telethon")

try:
    import telebot
    from telebot import TeleBot
    from telebot.types import (
        InlineKeyboardMarkup, InlineKeyboardButton,
        ForceReply, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    )
    import requests
except ImportError:
    missing.append("pyTelegramBotAPI requests")

if missing:
    print(f"\n[✗] Install karo: pip install {' '.join(missing)}\n")
    sys.exit(1)

# ═══════════════════════════════════════════════════════
#  DIRECTORIES & CONFIG
# ═══════════════════════════════════════════════════════

BASE_DIR    = os.path.expanduser("~/tg_master")
SESSION_DIR = os.path.join(BASE_DIR, "sessions")
MEDIA_DIR   = os.path.join(BASE_DIR, "media")
DATA_FILE   = os.path.join(BASE_DIR, "data.json")
DB_FILE     = os.path.join(BASE_DIR, "master.db")

for _d in [BASE_DIR, SESSION_DIR, MEDIA_DIR]:
    os.makedirs(_d, exist_ok=True)

DELAY = 0.5   # seconds between sends (dialog broadcast)
DELAY_DM = 3  # seconds between sends (targeted DM)

# ── Colors (for CLI output) ───────────────────────────────────────────────────
R  = "\033[0;31m";  G  = "\033[0;32m";  Y  = "\033[1;33m"
C  = "\033[0;36m";  M  = "\033[0;35m";  W  = "\033[1;37m"
DIM= "\033[2m";     NC = "\033[0m"

def clr():    os.system("clear")
def ok(m):    print(f"  {G}✓{NC} {m}")
def err(m):   print(f"  {R}✗{NC} {m}")
def warn(m):  print(f"  {Y}!{NC} {m}")
def info(m):  print(f"  {C}→{NC} {m}")
def sep():    print(f"  {DIM}{'─'*50}{NC}")
def pause():  input(f"\n  {DIM}Enter dabao...{NC}")
def hdr(t):
    clr()
    print(f"\n{C}{'═'*54}{NC}")
    print(f"  {W}{t}{NC}")
    print(f"{C}{'═'*54}{NC}\n")

# ═══════════════════════════════════════════════════════
#  DATA — JSON (accounts, config, history)
# ═══════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════
#  MONGODB — Persistent Account Storage
#  Deploy ke baad /setmongouri command se URI set karo
#  Free Atlas cluster: mongodb.com/atlas/database
# ═══════════════════════════════════════════════════════

_mongo_client = None
_mongo_db     = None

def _get_mongo_db():
    """MongoDB connection return karo (singleton, thread-safe)."""
    global _mongo_client, _mongo_db
    if _mongo_db is not None:
        return _mongo_db
    uri = os.environ.get("MONGODB_URI", "")
    if not uri:
        return None
    try:
        from pymongo import MongoClient
        _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _mongo_client.admin.command("ping")   # connection test
        _mongo_db = _mongo_client["tg_master"]
        return _mongo_db
    except Exception as e:
        return None

def _heroku_save_config_var(key, value):
    """Heroku Config Var set karo — HEROKU_API_KEY + HEROKU_APP_NAME chahiye."""
    try:
        api_key  = os.environ.get("HEROKU_API_KEY", "")
        app_name = os.environ.get("HEROKU_APP_NAME", "")
        if not api_key or not app_name:
            return False
        import urllib.request
        body = json.dumps({key: value}).encode()
        req  = urllib.request.Request(
            f"https://api.heroku.com/apps/{app_name}/config-vars",
            data=body, method="PATCH",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept":        "application/vnd.heroku+json; version=3",
                "Content-Type":  "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status == 200
    except Exception:
        return False

def _mongo_set_uri(uri):
    """
    Runtime mein MongoDB URI set karo:
    1. os.environ update karo
    2. Connection reset karo (naya connection use karega)
    3. Heroku Config Var mein permanent save karo
    4. Local fallback file mein bhi save karo
    """
    global _mongo_client, _mongo_db
    uri = uri.strip()
    os.environ["MONGODB_URI"] = uri
    # Reset connection so next _get_mongo_db() call reconnects
    try:
        if _mongo_client:
            _mongo_client.close()
    except Exception:
        pass
    _mongo_client = None
    _mongo_db     = None
    # Heroku mein permanent save karo
    _heroku_save_config_var("MONGODB_URI", uri)
    # Local fallback file (ephemeral but helps current session)
    try:
        cfg_file = os.path.join(BASE_DIR, ".mongo_uri")
        os.makedirs(BASE_DIR, exist_ok=True)
        with open(cfg_file, "w") as f:
            f.write(uri)
    except Exception:
        pass
    # Test connection
    db = _get_mongo_db()
    return db is not None

def _mongo_save_account(acc, owner_id=""):
    """Ek account (with session_string) MongoDB mein save/update karo."""
    try:
        db = _get_mongo_db()
        if db is None:
            return
        acc_copy = dict(acc)
        acc_copy["owner_id"] = str(owner_id) if owner_id else acc_copy.get("owner_id", "")
        db["accounts"].replace_one(
            {"phone": acc_copy["phone"]},
            acc_copy,
            upsert=True,
        )
    except Exception:
        pass

def _mongo_delete_account(phone):
    """MongoDB se account delete karo."""
    try:
        db = _get_mongo_db()
        if db is None:
            return
        db["accounts"].delete_one({"phone": phone})
    except Exception:
        pass

def _mongo_load_accounts():
    """MongoDB se saare accounts load karo."""
    try:
        db = _get_mongo_db()
        if db is None:
            return []
        return list(db["accounts"].find({}, {"_id": 0}))
    except Exception:
        return []

def _mongo_save_config(cfg_dict):
    """Bot config MongoDB mein save karo."""
    try:
        db = _get_mongo_db()
        if db is None:
            return
        db["config"].replace_one({"_id": "main"}, {"_id": "main", **cfg_dict}, upsert=True)
    except Exception:
        pass

def _mongo_load_config():
    """MongoDB se config load karo."""
    try:
        db = _get_mongo_db()
        if db is None:
            return None
        doc = db["config"].find_one({"_id": "main"}, {"_id": 0})
        return doc
    except Exception:
        return None

def load():
    """
    Data load karo — priority order:
    1. Local data.json (agar exist karta hai)
    2. MongoDB (agar MONGODB_URI set hai) — restart-safe!
    3. Env vars (BOT_TOKEN, API_ID, API_HASH, ADMIN_ID)
    """
    d = None
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                d = json.load(f)
        except Exception:
            d = None
    if d is None:
        d = {
            "config": {
                "bot_token": "",
                "api_id": 0,
                "api_hash": "",
                "admin_ids": [],
                "main_master_id": 0,
                "user_masters": [],
                "force_join_groups": [],
                "music_bot_usernames": [],
                "blacklist_groups": [],
                "promo_text": "",
                "promo_link": "",
            },
            "accounts": [],
            "account_owners": {},
            "targets":  [],
            "history":  [],
            "templates": [],
        }
    # Config fields migration / defaults
    cfg = d.setdefault("config", {})
    cfg.setdefault("main_master_id", 0)
    cfg.setdefault("user_masters", [])
    cfg.setdefault("force_join_groups", [])
    cfg.setdefault("music_bot_usernames", [])
    cfg.setdefault("blacklist_groups", [])
    cfg.setdefault("promo_text", "")
    cfg.setdefault("promo_link", "")
    cfg.setdefault("welcome_photo_id", "")
    cfg.setdefault("welcome_caption", "")
    d.setdefault("account_owners", {})
    # ── MongoDB se accounts restore karo (Heroku restart pe file wipe hoti hai) ──
    if not d.get("accounts"):
        mongo_accs = _mongo_load_accounts()
        if mongo_accs:
            existing = {a["phone"] for a in d["accounts"]}
            owners   = d.setdefault("account_owners", {})
            for acc in mongo_accs:
                if acc.get("phone") and acc["phone"] not in existing:
                    d["accounts"].append(acc)
                    existing.add(acc["phone"])
                    owner = acc.get("owner_id")
                    if owner:
                        owners[acc["phone"]] = str(owner)
    # ── Local .mongo_uri fallback file se URI load karo ────────────────────────
    if not os.environ.get("MONGODB_URI"):
        try:
            cfg_file = os.path.join(BASE_DIR, ".mongo_uri")
            if os.path.exists(cfg_file):
                with open(cfg_file) as f:
                    uri_fb = f.read().strip()
                if uri_fb:
                    os.environ["MONGODB_URI"] = uri_fb
        except Exception:
            pass
    # ── Env vars se config load karo (agar data.json mein nahi hai) ────────────
    for env_key, cfg_key, cast in [
        ("BOT_TOKEN", "bot_token", str),
        ("API_ID",    "api_id",    int),
        ("API_HASH",  "api_hash",  str),
        ("ADMIN_ID",  "admin_ids", None),
    ]:
        val = os.environ.get(env_key, "")
        if val:
            if cfg_key == "admin_ids" and not cfg.get("admin_ids"):
                try: cfg["admin_ids"] = [int(v.strip()) for v in val.split(",") if v.strip()]
                except Exception: pass
            elif cast == int:
                try: cfg[cfg_key] = int(val)
                except Exception: pass
            elif cast == str and not cfg.get(cfg_key):
                cfg[cfg_key] = val
    return d

def save(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # MongoDB mein bhi save karo — fire-and-forget background thread
    def _bg():
        owners = data.get("account_owners", {})
        for acc in data.get("accounts", []):
            if acc.get("session_string"):
                acc_copy = dict(acc)
                phone = acc_copy.get("phone", "")
                acc_copy["owner_id"] = owners.get(phone, acc_copy.get("owner_id", ""))
                _mongo_save_account(acc_copy, owner_id=acc_copy["owner_id"])
    threading.Thread(target=_bg, daemon=True, name="mongo-save").start()

def load_cfg():
    """File-2 compat: returns flat dict with config fields + accounts list."""
    d = load()
    cfg = dict(d["config"])
    cfg["accounts"] = d["accounts"]
    return cfg

def save_cfg(cfg):
    """File-2 compat: saves flat cfg dict back into nested structure."""
    d = load()
    accs = cfg.pop("accounts", None)
    if accs is not None:
        d["accounts"] = accs
    for k, v in cfg.items():
        d["config"][k] = v
    save(d)

def gen_id():
    return str(int(time.time() * 1000))[-10:]

def sync_account_status(data):
    changed = False
    for a in data["accounts"]:
        safe = a["phone"].replace("+", "").replace(" ", "")
        has_session = os.path.exists(os.path.join(SESSION_DIR, safe + ".session"))
        if not has_session:
            if a.get("verified") or a.get("active"):
                a["verified"] = False
                a["active"]   = False
                changed = True
    return changed

# ═══════════════════════════════════════════════════════
#  DATABASE — SQLite (scrape jobs, members, broadcasts)
# ═══════════════════════════════════════════════════════

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS scrape_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_target TEXT NOT NULL,
            account_phone TEXT,
            owner_id TEXT,
            status TEXT DEFAULT 'pending',
            total_scraped INTEGER DEFAULT 0,
            error_msg TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scrape_id INTEGER NOT NULL,
            telegram_id TEXT NOT NULL,
            access_hash TEXT DEFAULT '0',
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            is_active INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            last_seen TEXT,
            broadcast_count INTEGER DEFAULT 0,
            last_broadcast_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(scrape_id, telegram_id)
        );
        -- access_hash column add karo agar pehle se nahi hai (upgrade)
        CREATE TABLE IF NOT EXISTS _dummy_upgrade_check (x INTEGER);
        CREATE TABLE IF NOT EXISTS broadcast_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scrape_id INTEGER,
            message TEXT NOT NULL,
            media_type TEXT,
            media_path TEXT,
            members_per_account INTEGER DEFAULT 5,
            status TEXT DEFAULT 'done',
            total_targeted INTEGER DEFAULT 0,
            total_sent INTEGER DEFAULT 0,
            total_failed INTEGER DEFAULT 0,
            total_skipped INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS broadcast_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            broadcast_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            account_phone TEXT,
            status TEXT NOT NULL,
            reason TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(broadcast_id, member_id)
        );
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id TEXT UNIQUE NOT NULL,
            label TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS contact_add_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scrape_id INTEGER NOT NULL,
            invite_link TEXT NOT NULL,
            broadcast_msg TEXT,
            max_per_acc INTEGER DEFAULT 5,
            status TEXT DEFAULT 'running',
            total_contact_added INTEGER DEFAULT 0,
            total_link_sent INTEGER DEFAULT 0,
            total_dm_sent INTEGER DEFAULT 0,
            total_privacy_skip INTEGER DEFAULT 0,
            total_failed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    # ── Migration: access_hash column add karo agar pehle se nahi hai ──────
    try:
        conn.execute("ALTER TABLE members ADD COLUMN access_hash TEXT DEFAULT '0'")
        conn.commit()
    except Exception:
        pass  # Column pehle se exist karta hai — ignore
    # ── Migration: owner_id column scrape_jobs mein ──────────────────────────
    try:
        conn.execute("ALTER TABLE scrape_jobs ADD COLUMN owner_id TEXT")
        conn.commit()
    except Exception:
        pass
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

# ═══════════════════════════════════════════════════════
#  TELETHON HELPERS
# ═══════════════════════════════════════════════════════

_account_locks = {}

def _get_account_lock(phone):
    if phone not in _account_locks:
        _account_locks[phone] = threading.Lock()
    return _account_locks[phone]

def _set_wal_mode(phone):
    safe    = phone.replace("+", "").replace(" ", "")
    db_path = os.path.join(SESSION_DIR, safe + ".session")
    if not os.path.exists(db_path):
        return
    try:
        con = sqlite3.connect(db_path, timeout=10)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA busy_timeout=10000;")
        con.commit()
        con.close()
    except Exception:
        pass

def get_client(phone, api_id, api_hash, session_string=None):
    """
    session_string diya toh StringSession use karo (Heroku/cloud restart safe).
    Nahi diya toh file-based session use karo.
    """
    safe = phone.replace("+", "").replace(" ", "")
    if not session_string:
        # data.json se session_string dhundho
        try:
            d = load()
            for acc in d.get("accounts", []):
                if acc["phone"] == phone and acc.get("session_string"):
                    session_string = acc["session_string"]
                    break
        except Exception:
            pass
    if session_string:
        return TelegramClient(
            StringSession(session_string),
            api_id, api_hash,
            connection_retries=5,
            retry_delay=2,
            request_retries=3,
            flood_sleep_threshold=20,
        )
    _set_wal_mode(phone)
    return TelegramClient(
        os.path.join(SESSION_DIR, safe),
        api_id, api_hash,
        connection_retries=5,
        retry_delay=2,
        request_retries=3,
        flood_sleep_threshold=20,
    )

def session_exists(phone):
    """Check karo: session file OR session_string (StringSession) exist karta hai."""
    safe = phone.replace("+", "").replace(" ", "")
    if os.path.exists(os.path.join(SESSION_DIR, safe + ".session")):
        return True
    # StringSession check karo data.json mein
    try:
        d = load()
        for acc in d.get("accounts", []):
            if acc["phone"] == phone and acc.get("session_string"):
                return True
    except Exception:
        pass
    return False

def active_accounts(cfg_or_none=None):
    if cfg_or_none is None:
        d = load()
        accs = d["accounts"]
    elif isinstance(cfg_or_none, dict) and "accounts" in cfg_or_none:
        accs = cfg_or_none["accounts"]
    else:
        accs = load()["accounts"]
    return [a for a in accs if a.get("verified") and a.get("active") and session_exists(a["phone"])]

def is_long_inactive(last_seen_str):
    if not last_seen_str:
        return False
    try:
        last = datetime.fromisoformat(last_seen_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - last).days > 30
    except Exception:
        return False

def safe_disconnect(client, loop):
    try:
        result = client.disconnect()
        if asyncio.iscoroutine(result) or asyncio.isfuture(result):
            loop.run_until_complete(result)
    except Exception:
        pass

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def check_account_spam(client):
    try:
        me = await client.get_me()
        if me is None:
            return {"ok": False, "status": "Account authorize nahi hai", "restricted": False,
                    "deactivated": False, "spam_bot": False}
        restricted  = getattr(me, "restricted", False) or False
        deactivated = getattr(me, "deleted",    False) or False
        if deactivated:
            return {"ok": False, "status": "Account delete/ban ho gaya hai!", "restricted": True,
                    "deactivated": True, "spam_bot": False}
        if restricted:
            reasons = []
            for r in (getattr(me, "restriction_reason", None) or []):
                reasons.append(getattr(r, "reason", ""))
            reason_str = ", ".join(reasons) if reasons else "unknown"
            return {"ok": False, "status": f"Account restricted: {reason_str}", "restricted": True,
                    "deactivated": False, "spam_bot": False}
        spam_bot_restricted = False
        try:
            async with client.conversation("@SpamBot", timeout=10) as conv:
                await conv.send_message("/start")
                resp = await conv.get_response()
                spamtext = (resp.text or "").lower()
                if "limit" in spamtext or "spam" in spamtext or "restricted" in spamtext:
                    spam_bot_restricted = True
        except Exception:
            pass
        status_msg = "Account clean ✅"
        if spam_bot_restricted:
            status_msg = "⚠️ SpamBot warning (lekin sending try karega)"
        return {"ok": True, "status": status_msg, "restricted": False,
                "deactivated": False, "spam_bot": spam_bot_restricted}
    except (UserDeactivatedBanError, AuthKeyDuplicatedError) as e:
        return {"ok": False, "status": f"Account banned/deactivated: {e}", "restricted": True,
                "deactivated": True, "spam_bot": False}
    except Exception as e:
        return {"ok": True, "status": f"Check skip (error): {str(e)[:50]}", "restricted": False,
                "deactivated": False, "spam_bot": False}

# ═══════════════════════════════════════════════════════
#  DIALOG BROADCAST ENGINE (sabhi dialogs mein bhejo)
# ═══════════════════════════════════════════════════════

async def fetch_dialogs(client, target_mode):
    from telethon.tl.types import User, Chat, Channel
    targets  = []
    seen_ids = set()
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        eid    = dialog.id
        if eid in seen_ids:
            continue
        seen_ids.add(eid)
        if isinstance(entity, User):
            if entity.bot or entity.is_self:
                continue
            if target_mode in ("all", "dm"):
                name = f"{entity.first_name or ''} {entity.last_name or ''}".strip() or str(entity.id)
                targets.append({"id": entity.id, "label": name, "type": "dm"})
        elif isinstance(entity, (Chat, Channel)):
            if isinstance(entity, Channel) and entity.broadcast and target_mode == "dm":
                continue
            if target_mode in ("all", "group"):
                targets.append({"id": dialog.id, "label": getattr(entity, "title", str(eid)), "type": "group"})
    return targets

async def run_broadcast(payload, progress_cb=None):
    """
    Dialog-based broadcast — account ke sabhi dialogs mein bhejo.
    payload = {
        "text": str, "media_path": str|None,
        "buttons": [{text, url},...], "target_mode": "all"|"group"|"dm",
        "parse_mode": "html"|"markdown"|None
    }
    """
    data     = load()
    cfg      = data["config"]
    api_id   = cfg.get("api_id", 0)
    api_hash = cfg.get("api_hash", "")
    if not api_id or not api_hash:
        return {"ok": False, "error": "API_ID / API_HASH set nahi hai!"}
    active_accs = [a for a in data["accounts"] if a.get("active") and a.get("verified")]
    if not active_accs:
        return {"ok": False, "error": "Koi active account nahi hai!"}

    text        = payload.get("text", "")
    media_path  = payload.get("media_path")
    buttons_raw = payload.get("buttons", [])
    parse_mode  = payload.get("parse_mode", "html")
    target_mode = payload.get("target_mode", "all")

    tl_buttons = None
    if buttons_raw:
        from telethon.tl.types import KeyboardButtonUrl, KeyboardButtonRow, ReplyInlineMarkup
        rows, row_btns = [], []
        for i, b in enumerate(buttons_raw):
            row_btns.append(KeyboardButtonUrl(text=b["text"], url=b["url"]))
            if (i + 1) % 2 == 0 or i == len(buttons_raw) - 1:
                rows.append(KeyboardButtonRow(buttons=row_btns))
                row_btns = []
        tl_buttons = ReplyInlineMarkup(rows=rows)

    total_sent   = 0
    total_failed = 0
    total_skipped = 0
    results      = []
    log_lines    = []
    acc_stats    = []
    global_sent_ids = set()

    for acc_idx, acc in enumerate(active_accs):
        phone     = acc["phone"]
        acc_label = acc.get("label") or acc.get("name") or phone
        client    = get_client(phone, api_id, api_hash)
        acc_sent    = 0
        acc_failed  = 0
        acc_skipped = 0

        try:
            await client.connect()
            if not await client.is_user_authorized():
                log_lines.append(f"⚠️ [{acc_label}] session expired — re-login karo")
                acc_stats.append({"label": acc_label, "phone": phone,
                                  "sent": 0, "failed": 0, "total": 0, "error": "Session expired"})
                await client.disconnect()
                continue

            if progress_cb:
                progress_cb(acc_label, 0, 0, 0, total_sent, total_failed, "Spam check ho raha hai...")
            spam_info = await check_account_spam(client)
            if not spam_info["ok"]:
                log_lines.append(f"🚫 [{acc_label}] SKIP — {spam_info['status']}")
                acc_stats.append({"label": acc_label, "phone": phone,
                                  "sent": 0, "failed": 0, "total": 0,
                                  "error": f"🚫 {spam_info['status']}"})
                await client.disconnect()
                continue
            log_lines.append(f"✅ [{acc_label}] Spam check OK — sending shuru")

            log_lines.append(f"📋 [{acc_label}] dialogs fetch ho rahe hain...")
            if progress_cb:
                progress_cb(acc_label, 0, 0, 0, total_sent, total_failed, "Dialogs fetch ho rahe hain...")

            all_targets = await fetch_dialogs(client, target_mode)
            targets     = [t for t in all_targets if t["id"] not in global_sent_ids]
            skipped_now = len(all_targets) - len(targets)
            acc_skipped += skipped_now
            total_skipped += skipped_now
            acc_total   = len(targets)

            if skipped_now:
                log_lines.append(f"⏭ [{acc_label}] {skipped_now} targets already covered — skip")

            if not targets:
                log_lines.append(f"⚠️ [{acc_label}] koi naya target nahi ({target_mode})")
                acc_stats.append({"label": acc_label, "phone": phone,
                                  "sent": 0, "failed": 0, "skipped": skipped_now,
                                  "total": len(all_targets), "error": "All already sent"})
                await client.disconnect()
                continue

            log_lines.append(f"📊 [{acc_label}] {acc_total} naye targets (+ {skipped_now} skip)")

            acc_peer_flooded = False
            for t_idx, target in enumerate(targets):
                if acc_peer_flooded:
                    acc_failed   += 1
                    total_failed += 1
                    continue

                chat_id = target["id"]
                t_label = target["label"]
                try:
                    if media_path and os.path.exists(media_path):
                        await client.send_file(
                            chat_id, media_path,
                            caption=text if text else None,
                            parse_mode=parse_mode,
                            buttons=tl_buttons,
                        )
                    else:
                        await client.send_message(
                            chat_id, text,
                            parse_mode=parse_mode,
                            buttons=tl_buttons,
                            link_preview=False,
                        )
                    acc_sent        += 1
                    total_sent      += 1
                    global_sent_ids.add(chat_id)
                    results.append({"account": phone, "target": str(chat_id), "success": True})
                    log_lines.append(f"✅ [{acc_label}] → {t_label}")
                    await asyncio.sleep(DELAY)

                except PeerFloodError:
                    acc_peer_flooded = True
                    log_lines.append(f"🚫 [{acc_label}] PeerFloodError — SPAM limit!")
                    acc_failed   += 1
                    total_failed += 1
                    results.append({"account": phone, "target": str(chat_id), "success": False, "error": "PeerFlood"})

                except FloodWaitError as e:
                    wait = min(e.seconds, 60)
                    log_lines.append(f"⏳ [{acc_label}] → {t_label} [Flood {e.seconds}s, wait {wait}s]")
                    if progress_cb:
                        progress_cb(acc_label, acc_sent, acc_failed, acc_total,
                                    total_sent, total_failed, f"FloodWait {wait}s...")
                    await asyncio.sleep(wait)
                    try:
                        if media_path and os.path.exists(media_path):
                            await client.send_file(chat_id, media_path, caption=text or None,
                                                   parse_mode=parse_mode, buttons=tl_buttons)
                        else:
                            await client.send_message(chat_id, text, parse_mode=parse_mode,
                                                      buttons=tl_buttons, link_preview=False)
                        acc_sent   += 1
                        total_sent += 1
                        global_sent_ids.add(chat_id)
                        results.append({"account": phone, "target": str(chat_id), "success": True})
                        log_lines.append(f"✅ [{acc_label}] → {t_label} (retry ok)")
                        await asyncio.sleep(DELAY)
                        continue
                    except PeerFloodError:
                        acc_peer_flooded = True
                        log_lines.append(f"🚫 [{acc_label}] PeerFlood on retry!")
                    except Exception:
                        pass
                    acc_failed   += 1
                    total_failed += 1
                    results.append({"account": phone, "target": str(chat_id), "success": False, "error": "FloodWait"})

                except (ChatWriteForbiddenError, UserBannedInChannelError):
                    acc_failed   += 1
                    total_failed += 1
                    log_lines.append(f"🚫 [{acc_label}] → {t_label} [Banned/No permission]")
                    results.append({"account": phone, "target": str(chat_id), "success": False, "error": "Banned"})

                except Exception as e:
                    err_msg = str(e)
                    if "database is locked" in err_msg.lower():
                        await asyncio.sleep(3)
                        try:
                            if media_path and os.path.exists(media_path):
                                await client.send_file(chat_id, media_path, caption=text or None,
                                                       parse_mode=parse_mode, buttons=tl_buttons)
                            else:
                                await client.send_message(chat_id, text, parse_mode=parse_mode,
                                                          buttons=tl_buttons, link_preview=False)
                            acc_sent   += 1
                            total_sent += 1
                            global_sent_ids.add(chat_id)
                            results.append({"account": phone, "target": str(chat_id), "success": True})
                            log_lines.append(f"✅ [{acc_label}] → {t_label} (db-retry ok)")
                            await asyncio.sleep(DELAY)
                            continue
                        except Exception as e2:
                            err_msg = str(e2)
                    acc_failed   += 1
                    total_failed += 1
                    err_short = err_msg[:60]
                    log_lines.append(f"❌ [{acc_label}] → {t_label} [{err_short}]")
                    results.append({"account": phone, "target": str(chat_id), "success": False, "error": err_short})

                if progress_cb and (acc_sent + acc_failed) % 10 == 0:
                    progress_cb(acc_label, acc_sent, acc_failed, acc_total,
                                total_sent, total_failed, f"{t_idx+1}/{acc_total} targets done")

            if acc_peer_flooded:
                log_lines.append(f"🚫 [{acc_label}] SPAM — {acc_sent} bheje, baaki skip")

        except Exception as e:
            err_txt = str(e)[:80]
            log_lines.append(f"❌ [{acc_label}] connect fail: {err_txt}")
            acc_stats.append({"label": acc_label, "phone": phone,
                              "sent": 0, "failed": 0, "total": 0, "error": err_txt})
            continue
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

        acc_stats.append({
            "label": acc_label, "phone": phone,
            "sent": acc_sent, "failed": acc_failed,
            "skipped": acc_skipped, "total": acc_total + acc_skipped,
        })
        log_lines.append(
            f"━━ [{acc_label}] DONE — ✅{acc_sent} ❌{acc_failed} ⏭{acc_skipped} skip / {acc_total} naye"
        )
        if progress_cb:
            progress_cb(acc_label, acc_sent, acc_failed, acc_total,
                        total_sent, total_failed, f"Account {acc_idx+1}/{len(active_accs)} complete")

    record = {
        "id":           gen_id(),
        "message":      text[:200],
        "hasMedia":     bool(media_path),
        "hasButtons":   bool(buttons_raw),
        "buttonCount":  len(buttons_raw),
        "targetMode":   target_mode,
        "sentAt":       datetime.now().isoformat(),
        "totalSent":    total_sent,
        "totalFailed":  total_failed,
        "totalSkipped": total_skipped,
        "uniqueTargets": len(global_sent_ids),
        "accStats":     acc_stats,
        "results":      results,
    }
    data["history"].insert(0, record)
    data["history"] = data["history"][:100]
    save(data)

    return {
        "ok": True,
        "sent": total_sent, "failed": total_failed, "skipped": total_skipped,
        "unique_targets": len(global_sent_ids),
        "log": log_lines, "acc_stats": acc_stats,
    }

# ═══════════════════════════════════════════════════════
#  TAG-ALL ENGINE — GROUP MEMBER GREETER
# ═══════════════════════════════════════════════════════

def _time_label():
    hour = datetime.now().hour
    if 5  <= hour < 12: return "🌅 Good Morning"
    if 12 <= hour < 17: return "☀️ Good Afternoon"
    if 17 <= hour < 21: return "🌆 Good Evening"
    return "🌙 Good Night"

def generate_greeting(mention):
    import random
    hour = datetime.now().hour
    if 5 <= hour < 12:
        templates = [
            "🌅 Good Morning {m}!\nAaj ka din khushiyon se bhara ho! ☀️",
            "🌞 Subah Mubarak {m}!\nNaya din, nayi energy — enjoy karo! 😊",
            "☀️ Wakey wakey {m}!\nBest wali subah ho teri aaj! 🌻",
            "🌄 Subah ki shubhkamnaen {m}!\nHar sapna aaj poora ho! 🙏",
        ]
    elif 12 <= hour < 17:
        templates = [
            "☀️ Good Afternoon {m}!\nUmmeed hai din khub acha ja raha hoga! 😊",
            "🌤 Dopahar Mubarak {m}!\nThoda rest lo, phir full energy se! 💪",
            "🌞 Hey {m}!\nGood Afternoon — din ka best waqt enjoy karo! 🎯",
        ]
    elif 17 <= hour < 21:
        templates = [
            "🌆 Good Evening {m}!\nShaam ki thandi hawa mein relax karo! 😌",
            "🌇 Shaam Mubarak {m}!\nDin bhar ki mehnat ke baad enjoy karo! ✨",
            "🌃 Good Evening {m}!\nAaj ka din kaisa raha? Hope it was great! 🌟",
        ]
    else:
        templates = [
            "🌙 Good Night {m}!\nMeethe sapne aao, kal phir milenge! 😴",
            "⭐ Shubh Ratri {m}!\nAram karo, kal naya din naya mauka! 🌟",
            "🌙 Good Night {m}!\nSo ja ab, kal phir milenge! 💫",
        ]
    return random.choice(templates).format(m=mention)

def generate_shayri(mention):
    import random
    openers = [
        "🌹 {m} ko salaam,", "💫 Aye {m},", "🌙 Sunte ho {m}?",
        "✨ {m} ke liye ek baat,", "🌸 Aye dost {m},",
    ]
    shayris = [
        "Zindagi mein har pal kuch seekhte hain hum,\nMuskurate rahe, aage badhte hain hum. 🌟",
        "Waqt ke saath chalna seekh,\nHar roz ek naya sapna dekhna seekh. 💫",
        "Dil mein ho ummeed to raste nikal aate hain,\nJo sochte hain karne ki, woh kar jaate hain. 🔥",
        "Khwab wo nahi jo neend mein aayein,\nKhwab wo hain jo neend na aane dein. 🌙",
        "Haar ke baad hi jeetna milta hai,\nKaante chubhne ke baad hi phool khilta hai. 🌹",
        "Har subah ek nayi umeed lekar aati hai,\nZindagi khud rasta dikhati jaati hai. 🌅",
        "Apne aap par bharosa rakho hamesha,\nManzil milegi, bas chalna padega beshak. 💪",
    ]
    closers = [
        "\n\n— Bas yahi kehna tha aaj 🙏",
        "\n\n— Dil se likhi, tum tak pahunchi 💌",
        "\n\n— Hamesha khush raho! 😊",
    ]
    opener = random.choice(openers).format(m=mention)
    body   = random.choice(shayris)
    closer = random.choice(closers)
    return f"{opener}\n\n{body}{closer}"

async def fetch_group_list_for_tagall():
    data     = load()
    cfg      = data["config"]
    api_id   = cfg.get("api_id", 0)
    api_hash = cfg.get("api_hash", "")
    active   = [a for a in data["accounts"] if a.get("active") and a.get("verified")]
    if not active or not api_id:
        return []
    acc    = active[0]
    client = get_client(acc["phone"], api_id, api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return []
        groups = await fetch_dialogs(client, "group")
        return groups
    except Exception:
        return []
    finally:
        try: await client.disconnect()
        except Exception: pass

async def run_tagall(payload, progress_cb=None):
    data     = load()
    cfg      = data["config"]
    api_id   = cfg.get("api_id", 0)
    api_hash = cfg.get("api_hash", "")
    active   = [a for a in data["accounts"] if a.get("active") and a.get("verified")]
    if not active or not api_id:
        return {"ok": False, "error": "Active account ya API credentials nahi hain!"}

    group_id   = payload["group_id"]
    group_name = payload["group_name"]

    client     = None
    used_label = None
    for acc in active:
        try:
            c = get_client(acc["phone"], api_id, api_hash)
            await c.connect()
            if await c.is_user_authorized():
                client     = c
                used_label = acc.get("label") or acc.get("name") or acc["phone"]
                break
            await c.disconnect()
        except Exception:
            continue

    if not client:
        return {"ok": False, "error": "Koi bhi account connect nahi kar paya!"}

    try:
        from telethon.tl.types import User as TLUser
        if progress_cb:
            progress_cb("Members fetch ho rahe hain...", 0, 0, 0)
        participants = await client.get_participants(group_id, aggressive=True)
        members      = [p for p in participants if isinstance(p, TLUser) and not p.bot and not p.is_self]
        total        = len(members)
        if not members:
            return {"ok": False, "error": "Group mein koi member nahi mila ya participant access nahi hai!"}

        sent   = 0
        failed = 0
        for i, member in enumerate(members):
            fname   = member.first_name or ""
            lname   = member.last_name  or ""
            name    = f"{fname} {lname}".strip() or member.username or "Friend"
            mention = f'<a href="tg://user?id={member.id}">{name}</a>'
            tag_mode = payload.get("mode", "greeting")
            msg_text = generate_shayri(mention) if tag_mode == "shayri" else generate_greeting(mention)
            try:
                await client.send_message(group_id, msg_text, parse_mode="html", link_preview=False)
                sent += 1
                await asyncio.sleep(DELAY)
            except FloodWaitError as e:
                wait = min(e.seconds, 60)
                if progress_cb:
                    progress_cb(f"⏳ FloodWait {wait}s...", sent, failed, total)
                await asyncio.sleep(wait)
                try:
                    await client.send_message(group_id, msg_text, parse_mode="html", link_preview=False)
                    sent += 1
                    await asyncio.sleep(DELAY)
                except Exception:
                    failed += 1
            except Exception:
                failed += 1
            if progress_cb and (i + 1) % 10 == 0:
                progress_cb(f"{i+1}/{total} members tagged", sent, failed, total)

        return {"ok": True, "sent": sent, "failed": failed, "total": total,
                "group": group_name, "account": used_label}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}
    finally:
        try: await client.disconnect()
        except Exception: pass

async def run_tagall_all_groups(payload, progress_cb=None):
    data     = load()
    cfg      = data["config"]
    api_id   = cfg.get("api_id", 0)
    api_hash = cfg.get("api_hash", "")
    active   = [a for a in data["accounts"] if a.get("active") and a.get("verified")]
    if not active or not api_id:
        return {"ok": False, "error": "Active account ya API credentials nahi hain!"}

    tag_mode     = payload.get("mode", "greeting")
    total_sent   = 0
    total_failed = 0
    groups_done  = 0
    log_lines    = []

    client     = None
    used_label = None
    for acc in active:
        try:
            c = get_client(acc["phone"], api_id, api_hash)
            await c.connect()
            if await c.is_user_authorized():
                client     = c
                used_label = acc.get("label") or acc.get("name") or acc["phone"]
                break
            await c.disconnect()
        except Exception:
            continue

    if not client:
        return {"ok": False, "error": "Koi bhi account connect nahi kar paya!"}

    try:
        from telethon.tl.types import User as TLUser
        if progress_cb:
            progress_cb("Groups fetch ho rahe hain...", 0, 0, 0, 0)
        groups = await fetch_dialogs(client, "group")
        total_groups = len(groups)
        log_lines.append(f"📋 {total_groups} groups mili — sabhi mein tagging shuru...")

        for g_idx, group in enumerate(groups):
            group_id   = group["id"]
            group_name = group["label"]
            if progress_cb:
                progress_cb(f"Group {g_idx+1}/{total_groups}: {group_name[:25]}",
                            total_sent, total_failed, groups_done, total_groups)
            try:
                participants = await client.get_participants(group_id, aggressive=True)
                members      = [p for p in participants
                                if isinstance(p, TLUser) and not p.bot and not p.is_self]
                if not members:
                    log_lines.append(f"⏭ {group_name} — koi member nahi / access nahi")
                    continue
                g_sent = g_failed = 0
                for member in members:
                    fname   = member.first_name or ""
                    lname   = member.last_name  or ""
                    name    = f"{fname} {lname}".strip() or member.username or "Friend"
                    mention = f'<a href="tg://user?id={member.id}">{name}</a>'
                    msg_text = generate_shayri(mention) if tag_mode == "shayri" else generate_greeting(mention)
                    try:
                        await client.send_message(group_id, msg_text, parse_mode="html", link_preview=False)
                        g_sent     += 1
                        total_sent += 1
                        await asyncio.sleep(DELAY)
                    except FloodWaitError as e:
                        wait = min(e.seconds, 60)
                        await asyncio.sleep(wait)
                        try:
                            await client.send_message(group_id, msg_text, parse_mode="html", link_preview=False)
                            g_sent     += 1
                            total_sent += 1
                            await asyncio.sleep(DELAY)
                        except Exception:
                            g_failed     += 1
                            total_failed += 1
                    except (ChatWriteForbiddenError, UserBannedInChannelError):
                        log_lines.append(f"🚫 {group_name} — write permission nahi, skip")
                        g_failed     += len(members)
                        total_failed += len(members)
                        break
                    except Exception:
                        g_failed     += 1
                        total_failed += 1
                groups_done += 1
                log_lines.append(f"✅ {group_name} — ✅{g_sent} ❌{g_failed} / {len(members)} members")
                if progress_cb:
                    progress_cb(f"✅ {group_name[:25]} done",
                                total_sent, total_failed, groups_done, total_groups)
            except Exception as e:
                log_lines.append(f"❌ {group_name}: {str(e)[:60]}")

        return {
            "ok": True, "groups_done": groups_done, "total_groups": total_groups,
            "total_sent": total_sent, "total_failed": total_failed,
            "account": used_label, "log": log_lines,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}
    finally:
        try: await client.disconnect()
        except Exception: pass

# ═══════════════════════════════════════════════════════
#  AUTO-LEAVE INACTIVE/BANNED GROUPS ENGINE
# ═══════════════════════════════════════════════════════

async def run_auto_leave_inactive(progress_cb=None, owner_uid=None):
    from telethon.tl.types import Channel, Chat as TLChat
    data     = load()
    cfg      = data["config"]
    api_id   = cfg.get("api_id", 0)
    api_hash = cfg.get("api_hash", "")
    if owner_uid is not None and not is_main_master(owner_uid):
        allowed = {a["phone"] for a in get_user_accounts(owner_uid)}
        active  = [a for a in data["accounts"]
                   if a.get("active") and a.get("verified") and a["phone"] in allowed]
    else:
        active = [a for a in data["accounts"] if a.get("active") and a.get("verified")]
    if not active or not api_id:
        return {"ok": False, "error": "Active account ya API credentials nahi hain!"}

    total_left = 0
    total_err  = 0
    log_lines  = []

    for acc in active:
        phone     = acc["phone"]
        acc_label = acc.get("label") or acc.get("name") or phone
        client    = get_client(phone, api_id, api_hash)
        acc_left  = 0
        try:
            await client.connect()
            if not await client.is_user_authorized():
                log_lines.append(f"⚠️ [{acc_label}] session expired — skip")
                continue
            if progress_cb:
                progress_cb(acc_label, 0, 0, "Groups fetch ho rahe hain...")
            groups = await fetch_dialogs(client, "group")
            log_lines.append(f"📋 [{acc_label}] {len(groups)} groups mili")
            for g in groups:
                chat_id   = g["id"]
                chat_name = g["label"]
                try:
                    entity    = await client.get_entity(chat_id)
                    forbidden = False
                    if isinstance(entity, Channel):
                        if entity.broadcast:
                            forbidden = True
                        elif hasattr(entity, "banned_rights") and entity.banned_rights:
                            br = entity.banned_rights
                            if getattr(br, "send_messages", False):
                                forbidden = True
                    elif isinstance(entity, TLChat):
                        if getattr(entity, "kicked", False) or getattr(entity, "left", False):
                            forbidden = True
                    if not forbidden:
                        continue
                    try:
                        await client.delete_dialog(entity, revoke=False)
                        log_lines.append(f"🚪🗑 [{acc_label}] Left + deleted: {chat_name}")
                    except Exception as le:
                        log_lines.append(f"⚠️ [{acc_label}] Leave fail {chat_name}: {str(le)[:40]}")
                    acc_left   += 1
                    total_left += 1
                    await asyncio.sleep(0.8)
                    if progress_cb:
                        progress_cb(acc_label, acc_left, total_err, f"Processing: {chat_name[:30]}")
                except Exception as e:
                    total_err += 1
                    log_lines.append(f"❌ [{acc_label}] {chat_name}: {str(e)[:50]}")
            log_lines.append(f"━━ [{acc_label}] {acc_left} groups left")
        except Exception as e:
            log_lines.append(f"❌ [{acc_label}] connect fail: {str(e)[:60]}")
        finally:
            try: await client.disconnect()
            except Exception: pass

    return {"ok": True, "left": total_left, "errors": total_err, "log": log_lines}

# ═══════════════════════════════════════════════════════
#  AI AUTO-REPLY ENGINE
# ═══════════════════════════════════════════════════════

def generate_ai_reply(text, promo_text="", promo_link=""):
    import random
    t = (text or "").lower().strip()

    def promo_msg():
        short_promo = promo_text[:80] if promo_text else "humara special group"
        link        = promo_link if promo_link else ""
        options = [
            f"Waise ek kaam ki baat batao 😊 humara group bahut mast hai — {short_promo}. Zaroor join karo! 🌸 {link}",
            f"Aur haan, ek cheez share karni thi 💕 {short_promo} — yeh group really helpful hai! Join karo: {link}",
            f"Btw ek special group hai mera {short_promo} 🌟 bahut log join kar rahe hain — aap bhi aao! {link}",
        ]
        return random.choice(options)

    should_push_promo = (promo_text and promo_link and random.random() < 0.40)

    greet_kw = ["hello", "hi ", "hii", "hey", "helo", "namaste", "salam", "assalam",
                "good morning", "good night", "good evening", "gm ", "gn "]
    if any(k in t for k in greet_kw):
        replies = [
            "Hello! 😊 Kaise ho aap? Main theek hoon, aap batao?",
            "Heyy! 👋 Kitna acha laga aapka message dekh ke 😄 Sab theek?",
            "Namaste jee! 🙏 Aaj ka din mast ho aapka~ kya haal hai?",
            "Hiiii! 💕 Aapko dekh ke dil khush ho gaya 😊",
        ]
        base = random.choice(replies)
        return (base + "\n\n" + promo_msg()) if should_push_promo else base

    hru_kw = ["kaise ho", "kya haal", "kaisi ho", "how are you", "how r u",
              "kya chal raha", "sab theek", "all good"]
    if any(k in t for k in hru_kw):
        replies = [
            "Main bilkul mast hoon! 😊 Aaj bahut acha feel ho raha hai~ Aap batao?",
            "Alhamdulillah! Sab theek hai mera 🌟 Aap ka kya haal hai janaab?",
            "Hehe achi hoon main! 💕 Aap ka message aate hi mood acha ho gaya 😄",
        ]
        base = random.choice(replies)
        return (base + "\n\n" + promo_msg()) if should_push_promo else base

    join_kw = ["join", "group", "channel", "link", "invite", "kahan", "konsa", "kya hai"]
    if any(k in t for k in join_kw) and promo_link:
        return random.choice([
            f"Haan haan! Zaroor 💕 Yahan aa jao: {promo_link}\n{promo_text[:100] if promo_text else ''}",
            f"Bilkul! Join karo yahan 🌸 {promo_link} — bahut kuch milega aapko!",
        ])

    ty_kw = ["thanks", "thank you", "shukriya", "dhanyawad", "thank", "tysm"]
    if any(k in t for k in ty_kw):
        replies = [
            "Koi baat nahi jee! 😊 Khushi hui madad karke 💕",
            "Always welcome! 🤝 Kabhi bhi puchho, main hoon na~",
            "Shukriya aapka bhi! 🙏 Aap bahut pyaare ho 🌸",
        ]
        base = random.choice(replies)
        return (base + "\n\n" + promo_msg()) if should_push_promo else base

    sad_kw = ["sad", "dukhi", "problem", "mushkil", "pareshan", "tension",
              "takleef", "dard", "rona", "cry", "hurt", "akela"]
    if any(k in t for k in sad_kw):
        replies = [
            "Arre kya hua? Batao mujhe, main sun rahi hoon 🤗 Tension mat lo~",
            "Sab theek ho jayega, pakka! Main hoon na!",
            "Dil chota mat karo! 💪 Aap strong ho — main aapke saath hoon 💕",
        ]
        base = random.choice(replies)
        return (base + "\n\n" + promo_msg()) if should_push_promo else base

    default_replies = [
        "Samajh gayi! 😊 Aur kuch batana chahoge?",
        "Interesting 🤔 Main sun rahi hoon, aur batao~",
        "Haan haan! Kya sochte ho iske baare mein? 💬",
        "Acha, theek hai! 😄 Koi aur baat?",
        "Main samajhti hoon 💕 Kya aap theek ho?",
        "Ji zaroor! Kya madad chahiye? 🤝",
    ]
    base = random.choice(default_replies)
    if promo_text and promo_link and random.random() < 0.55:
        return base + "\n\n" + promo_msg()
    return base

_autoreply_active  = {}
_autoreply_clients = {}
_autoreply_loops   = {}

# ═══════════════════════════════════════════════════════
#  REPLY RAID ENGINE
# ═══════════════════════════════════════════════════════

RAID_MESSAGES = [
    "madarchod teri maa ki chut me ghutka khaake thook dunga 🤣🤣",
    "teri maa ki chut me sutli bomb fod dunga 💣",
    "teri maaki chut me scooter daal duga👅",
    "teri maa ki chut kakte gali ke kutto me baat dunga 🦮",
    "dudh hilaaunga teri vaheen ke upr niche 🆙😙",
    "teri maa ki chut me hatth dalke bacche nikal dunga 😍",
    "teri behn ki chut me kele ke chilke 🍌😍",
    "teri vaheen dhandhe vaali 😋😛",
    "teri maa ke bhosde me ac laga dunga saari garmi nikal jaayegi",
    "teri vaheen ko horlicks peelaaunga madarchod😚",
    "teri maa ki gaand me sariya daal dunga madarchod 😱",
    "teri maa ko kolkata vaale jitu bhaiya ka lund mubarak 🤩",
    "teri mummy ki fantasy hu lawde, tu apni bhen ko smbhaal 😈",
    "tera pehla baap hu madarchod",
    "aukat me reh vrna gaand me danda daal ke muh se nikaal dunga 🙄",
    "teri mummy ke saath ludo khelte uske muh me loda de dunga😬",
    "teri maa ki chut mei battery laga ke powerbank bana dunga 🔋🔥",
    "teri maa ke gaand mei jhaadu dal ke mor bana dungaa 🦚🤩",
    "bhosdike teri maa ki chut mei 4 hole hai bhofsdike👊🤢",
    "teri bahen ki chut mei bargad ka ped uga dungaa 🤢🥳",
    "teri maa ka group vaalon saath milke gang bang krunga🙌☠️",
    "sun madarchod jyada na uchal maa chod denge ek min mei 🤣🔥",
    "apni amma se puchna us kaali raat mei kaun chodne aaya thaaa! 😂👿",
    "teri randi maa se puchna baap ka naam 🤩🥳",
    "tu aur teri maa dono ki bhosde mei metro chalwa dunga 🚇😱",
    "teri maa ki chut mei telegram ki sari randiyon ka randi khana khol dungaa👿😎",
    "teri bahen ka vps bana ke 24x7 chudai command de dungaa 🔥",
    "teri maa ki chut alexa dal ke dj bajaungaaa 🎶🤩",
    "sun teri maa ka bhosda aur teri bahen ka bhi bhosda 👿😎",
    "tu teri bahen tera khandan sab bahen ke lawde randi hai 🤢✅",
    "tera baap hu bhosdike teri maa ko randi khane pe chudwake daaru peeta hu 🍷🔥",
    "teri maa ko itna chodunga tera baap bhi usko pehchanane se mana kar dega👿",
    "teri mummy aur bahen ko dauda dauda ne chodunga 😎🤣",
    "teri maa ko itna chodunga ki sapne mei bhi meri chudai yaad karegi 💥",
    "tujhe dekh ke teri randi bahen pe taras aata hai mujhe 💥🔥",
    "teri maa ka naya randi khana kholunga chinta mat kar 👊🤣",
    "tohar bahin chodu bahen ke lawde usme mitti dal ke cement se bhar du 🏠💥",
    "tujhe ab nahi smjh aya ki mai hi hu tujhe paida karne wala bhosdikee 👊",
    "teri maa ki chut aur teri bahen ka bhosda dono band kar dunga 😤",
    "madarchod akal nahi hai kya teri? teri maa ne sikhaya nahi? 🤬",
]

# Reply Raid — global state
_replyraid_users   = set()   # target user_ids currently being raided
_replyraid_active  = {}      # phone -> bool (watcher thread running)
_replyraid_clients = {}      # phone -> Telethon client
_replyraid_loops   = {}      # phone -> event loop


def _notify_admin(text):
    """Admin ko message bhejo (replyraid errors ke liye)."""
    try:
        d    = load()
        aids = d["config"].get("admin_ids", [])
        for aid in aids:
            try: bot.send_message(aid, text, parse_mode="HTML")
            except Exception: pass
    except Exception:
        pass


def _fire_all_raid_replies(chat_id, reply_to_msg_id):
    """
    Sirf EK message bhejo — randomly chosen active account se.
    Message 30 seconds baad automatically delete ho jayega.
    Dedup guard: ek hi message pe sirf PEHLA detection fire karega.
    """
    import random as _rnd
    if _raid_already_fired(chat_id, reply_to_msg_id):
        return

    active_phones = [ph for ph, ok in list(_replyraid_active.items()) if ok]
    if not active_phones:
        return

    # Sirf EK account randomly choose karo
    chosen_phone = _rnd.choice(active_phones)

    def _send_one(phone):
        client = _replyraid_clients.get(phone)
        loop   = _replyraid_loops.get(phone)
        if not client or not loop:
            return
        async def _do():
            try:
                sent = await client.send_message(
                    chat_id,
                    _rnd.choice(RAID_MESSAGES),
                    reply_to=reply_to_msg_id,
                )
                # 30 seconds baad message delete karo
                await asyncio.sleep(30)
                try:
                    await client.delete_messages(chat_id, [sent.id])
                except Exception:
                    pass
            except Exception:
                pass
        try:
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(_do(), loop)
        except Exception:
            pass

    threading.Thread(target=_send_one, args=(chosen_phone,), daemon=True).start()


def _start_replyraid_thread(acc, api_id, api_hash, notify_chat_id=None):
    """Start a Telethon watcher for one account to auto-reply raided users."""
    phone = acc["phone"]

    # Session file exist karti hai?
    if not session_exists(phone):
        errmsg = (f"⚠️ <b>ReplyRaid:</b> <code>{phone}</code> ki session file nahi mili.\n"
                  f"Is account ko /add se dobara login karo.")
        _notify_admin(errmsg)
        if notify_chat_id:
            try: bot.send_message(notify_chat_id, errmsg, parse_mode="HTML")
            except Exception: pass
        return False

    # Already running?
    if _replyraid_active.get(phone):
        return True

    def _thread_fn():
        loop   = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = get_client(phone, api_id, api_hash)
        _replyraid_clients[phone] = client
        _replyraid_loops[phone]   = loop

        async def _run():
            try:
                await client.connect()
            except Exception as e:
                _replyraid_active[phone] = False
                _notify_admin(f"❌ <b>ReplyRaid connect fail:</b> <code>{phone}</code>\n<code>{e}</code>")
                return

            if not await client.is_user_authorized():
                _replyraid_active[phone] = False
                _notify_admin(
                    f"❌ <b>ReplyRaid auth fail:</b> <code>{phone}</code>\n"
                    f"Session expired ho gayi. /add se dobara login karo."
                )
                return

            @client.on(events.NewMessage(incoming=True))
            async def _raid_watch(event):
                if not _replyraid_active.get(phone):
                    raise events.StopPropagation
                try:
                    if event.message.out:
                        return
                    sid = event.message.sender_id
                    if sid not in _replyraid_users:
                        return
                    sender = await event.get_sender()
                    if sender and getattr(sender, "bot", False):
                        return
                    # ── Ye account ne detect kiya → SABHI accounts reply karein ──
                    chat_id        = event.chat_id
                    reply_to_msg   = event.message.id
                    threading.Thread(
                        target=_fire_all_raid_replies,
                        args=(chat_id, reply_to_msg),
                        daemon=True
                    ).start()
                except Exception:
                    pass

            await client.run_until_disconnected()

        try:
            loop.run_until_complete(_run())
        except Exception:
            pass
        finally:
            _replyraid_active[phone] = False
            try: loop.close()
            except Exception: pass

    _replyraid_active[phone] = True
    threading.Thread(target=_thread_fn, daemon=True, name=f"replyraid-{phone}").start()
    return True


def _stop_replyraid_thread(phone):
    _replyraid_active[phone] = False
    client = _replyraid_clients.get(phone)
    loop   = _replyraid_loops.get(phone)
    if client and loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(client.disconnect(), loop)


def _ensure_replyraid_running(uid, notify_chat_id=None):
    """
    uid ke hisab se accounts filter karke threads start karo.
    • Main Master  → sabhi users ke sabhi active accounts
    • User/Admin   → sirf unke apne accounts
    Returns (started, no_session, already_running).
    """
    d        = load()
    cfg      = d["config"]
    api_id   = cfg.get("api_id", 0)
    api_hash = cfg.get("api_hash", "")

    # Account selection: main_master = sab, baaki = apne
    accs = get_user_accounts(uid)

    started = no_sess = already = 0
    for acc in accs:
        if _replyraid_active.get(acc["phone"]):
            already += 1
            continue
        ok = _start_replyraid_thread(acc, api_id, api_hash, notify_chat_id)
        if ok: started += 1
        else:  no_sess += 1
    return started, no_sess, already


def _stop_all_replyraid():
    for phone in list(_replyraid_active.keys()):
        _stop_replyraid_thread(phone)


# ─── DEDUP: ek message pe ek hi baar fire ho ─────────────────────────────────
_raid_fired_msgs = {}   # (chat_id, msg_id) -> timestamp

def _raid_already_fired(chat_id, msg_id):
    """Return True if this (chat, msg) was already fired; else mark and return False."""
    import time
    key = (chat_id, msg_id)
    now = time.time()
    # Purane entries clean karo (> 30s)
    for k in list(_raid_fired_msgs.keys()):
        if now - _raid_fired_msgs[k] > 30:
            del _raid_fired_msgs[k]
    if key in _raid_fired_msgs:
        return True
    _raid_fired_msgs[key] = now
    return False


def _auto_start_userbot(acc, notify_chat_id=None):
    """
    Naya account add hone ke baad ya bot startup pe automatically
    Telethon userbot watcher thread shuru karo.
    Agar watcher pehle se chal raha hai toh kuch nahi karo.
    """
    d        = load()
    cfg      = d["config"]
    api_id   = cfg.get("api_id", 0)
    api_hash = cfg.get("api_hash", "")
    if not api_id or not api_hash:
        return False
    if not session_exists(acc["phone"]):
        return False
    return _start_replyraid_thread(acc, api_id, api_hash, notify_chat_id)


def _check_mongodb_on_startup():
    """
    Bot start pe check karo — agar MONGODB_URI nahi hai toh admin ko
    /setmongouri command bhejne ka instruction do.
    """
    def _run():
        import time
        time.sleep(5)   # bot settle hone do
        if _get_mongo_db() is not None:
            return   # already connected, no need to notify
        msg = (
            "⚠️ <b>MongoDB URI Set Nahi Hai!</b>\n\n"
            "Accounts Heroku restart ke baad wipe ho jaayenge.\n\n"
            "<b>Fix karo — bot ko yeh message bhejo:</b>\n"
            "<code>/setmongouri mongodb+srv://USER:PASS@cluster0.xxxx.mongodb.net/?retryWrites=true&amp;w=majority</code>\n\n"
            "🆓 Free cluster: mongodb.com/atlas\n"
            "📌 MONGODB_URI Heroku mein permanently save ho jaayegi — sirf ek baar karna hai!"
        )
        _notify_admin(msg)
    threading.Thread(target=_run, daemon=True, name="mongo-startup-check").start()

def _startup_all_userbots():
    """
    Bot start hone pe sab active accounts ka watcher thread shuru karo.
    Ye accounts 'userbot' ki tarah hamesha connected rahenge.
    """
    def _run():
        import time
        time.sleep(3)   # bot polling settle hone do
        d    = load()
        cfg  = d["config"]
        accs = [a for a in d["accounts"] if a.get("active") and a.get("verified")]
        if not accs:
            return
        ok_count = 0
        for acc in accs:
            if _auto_start_userbot(acc):
                ok_count += 1
            time.sleep(0.5)   # throttle
        if ok_count:
            _notify_admin(
                f"🤖 <b>Userbot Auto-Start</b>\n"
                f"✅ {ok_count}/{len(accs)} accounts connected & watching!\n"
                f"Ab /replyraid se kisi pe bhi raid chalaao."
            )
        # Force Join — startup pe automatically run karo
        groups = d["config"].get("force_join_groups", [])
        if groups and ok_count:
            time.sleep(2)
            run_force_join_all(chat_id_report=None)
    threading.Thread(target=_run, daemon=True, name="userbot-startup").start()



def _start_autoreply_thread(acc, api_id, api_hash):
    phone     = acc["phone"]

    def _thread_fn():
        loop   = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = get_client(phone, api_id, api_hash)
        _autoreply_clients[phone] = client
        _autoreply_loops[phone]   = loop

        async def _run():
            await client.connect()
            if not await client.is_user_authorized():
                return
            me = await client.get_me()

            @client.on(events.NewMessage(incoming=True))
            async def handler(event):
                if not _autoreply_active.get(phone):
                    raise events.StopPropagation
                try:
                    msg     = event.message
                    txt     = msg.text or ""
                    if msg.out:
                        return
                    sender = await event.get_sender()
                    if sender and getattr(sender, "bot", False):
                        return
                    is_private = event.is_private
                    if is_private:
                        should_reply = True
                    else:
                        mentioned = False
                        if msg.mentioned:
                            mentioned = True
                        elif me.username and f"@{me.username}".lower() in txt.lower():
                            mentioned = True
                        should_reply = mentioned
                    if not should_reply:
                        return
                    import random as _rand
                    await asyncio.sleep(_rand.uniform(1.2, 3.5))
                    d_cfg  = load()
                    p_text = d_cfg["config"].get("promo_text", "")
                    p_link = d_cfg["config"].get("promo_link", "")
                    reply  = generate_ai_reply(txt, promo_text=p_text, promo_link=p_link)
                    await event.reply(reply)
                except Exception:
                    pass

            await client.run_until_disconnected()

        try:
            loop.run_until_complete(_run())
        except Exception:
            pass
        finally:
            try:
                loop.close()
            except Exception:
                pass

    t = threading.Thread(target=_thread_fn, daemon=True, name=f"autoreply-{phone}")
    t.start()

def stop_autoreply(phone):
    _autoreply_active[phone] = False
    client = _autoreply_clients.get(phone)
    loop   = _autoreply_loops.get(phone)
    if client and loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(client.disconnect(), loop)

# ═══════════════════════════════════════════════════════
#  PROFILE CLONE ENGINE
# ═══════════════════════════════════════════════════════

async def run_clone_profile(target_id, progress_cb=None):
    from telethon.tl.functions.account import UpdateProfileRequest
    from telethon.tl.functions.photos  import UploadProfilePhotoRequest
    import io

    data     = load()
    cfg      = data["config"]
    api_id   = cfg.get("api_id", 0)
    api_hash = cfg.get("api_hash", "")
    active   = [a for a in data["accounts"] if a.get("active") and a.get("verified")]
    if not active or not api_id:
        return {"ok": False, "error": "Active account ya API credentials nahi hain!"}

    fetcher = get_client(active[0]["phone"], api_id, api_hash)
    try:
        await fetcher.connect()
        if not await fetcher.is_user_authorized():
            return {"ok": False, "error": "Pehla account authorize nahi hai!"}
        if progress_cb:
            progress_cb("Target profile fetch ho rahi hai...", 0, len(active))

        target      = None
        fetch_error = ""

        if target_id.startswith("@") or not target_id.lstrip("-").isdigit():
            try:
                target = await fetcher.get_entity(target_id)
            except Exception as e1:
                fetch_error = str(e1)
        if target is None:
            try:
                tid    = int(target_id)
                target = await fetcher.get_entity(tid)
            except Exception as e2:
                fetch_error = str(e2)
        if target is None:
            try:
                tid = int(target_id)
                async for dialog in fetcher.iter_dialogs():
                    ent = dialog.entity
                    if hasattr(ent, "id") and ent.id == tid:
                        target = ent
                        break
            except Exception as e3:
                fetch_error = str(e3)
        if target is None:
            return {
                "ok": False,
                "error": (f"User nahi mila! (ID: {target_id})\n\n"
                          "Fix karo:\n• @username use karo\n• Ya us user ko pehle message karo\n"
                          f"Detail: {fetch_error[:80]}")
            }

        first_name = getattr(target, "first_name", "") or ""
        last_name  = getattr(target, "last_name",  "") or ""

        about = ""
        try:
            from telethon.tl.functions.users import GetFullUserRequest
            full  = await fetcher(GetFullUserRequest(target))
            about = getattr(full.full_user, "about", "") or ""
        except Exception:
            pass

        photo_bytes = None
        try:
            buf = io.BytesIO()
            dl  = await fetcher.download_profile_photo(target, file=buf)
            if dl:
                photo_bytes = buf.getvalue()
        except Exception:
            pass

    except Exception as e:
        return {"ok": False, "error": f"Target fetch fail: {str(e)[:80]}"}
    finally:
        try: await fetcher.disconnect()
        except Exception: pass

    done   = 0
    failed = 0
    log    = []

    for idx, acc in enumerate(active):
        phone     = acc["phone"]
        acc_label = acc.get("label") or acc.get("name") or phone
        if progress_cb:
            progress_cb(f"Apply ho rahi hai: {acc_label}", idx, len(active))
        client = get_client(phone, api_id, api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                log.append(f"⚠️ [{acc_label}] session expired — skip")
                failed += 1
                continue
            await client(UpdateProfileRequest(
                first_name=first_name, last_name=last_name, about=about,
            ))
            if photo_bytes:
                import io as _io
                photo_buf      = _io.BytesIO(photo_bytes)
                photo_buf.name = "profile.jpg"
                uploaded       = await client.upload_file(photo_buf)
                await client(UploadProfilePhotoRequest(file=uploaded))
            done += 1
            bio_short = (about[:40] + "...") if len(about) > 40 else about
            log.append(f"✅ [{acc_label}] naam: {first_name} {last_name}"
                       f"{' | bio: ' + bio_short if bio_short else ''} + photo apply done!")
            await asyncio.sleep(1.0)
        except Exception as e:
            failed += 1
            log.append(f"❌ [{acc_label}] {str(e)[:60]}")
        finally:
            try: await client.disconnect()
            except Exception: pass

    return {
        "ok": True, "done": done, "failed": failed,
        "first_name": first_name, "last_name": last_name,
        "about": about, "had_photo": bool(photo_bytes), "log": log,
    }

# ═══════════════════════════════════════════════════════
#  GROUP PROMOTION ENGINE
# ═══════════════════════════════════════════════════════

async def run_group_promo(progress_cb=None):
    data       = load()
    cfg        = data["config"]
    api_id     = cfg.get("api_id", 0)
    api_hash   = cfg.get("api_hash", "")
    promo_text = cfg.get("promo_text", "")
    promo_link = cfg.get("promo_link", "")

    if not promo_text or not promo_link:
        return {"ok": False, "error": "Pehle promo set karo: /setpromo"}
    active = [a for a in data["accounts"] if a.get("active") and a.get("verified")]
    if not active or not api_id:
        return {"ok": False, "error": "Active account ya API credentials nahi hain!"}

    full_msg = (f"📢 <b>Join Our Group!</b>\n\n{promo_text}\n\n🔗 <b>Join karo:</b> {promo_link}")

    client     = None
    used_label = None
    for acc in active:
        try:
            c = get_client(acc["phone"], api_id, api_hash)
            await c.connect()
            if await c.is_user_authorized():
                client     = c
                used_label = acc.get("label") or acc.get("name") or acc["phone"]
                break
            await c.disconnect()
        except Exception:
            continue

    if not client:
        return {"ok": False, "error": "Koi account connect nahi kar paya!"}

    try:
        groups = await fetch_dialogs(client, "group")
        total  = len(groups)
        sent   = 0
        failed = 0
        log    = []

        for i, g in enumerate(groups):
            chat_id   = g["id"]
            chat_name = g["label"]
            if progress_cb:
                progress_cb(f"{i+1}/{total}: {chat_name[:25]}", sent, failed, total)
            try:
                from telethon.tl.types import (
                    KeyboardButtonUrl, KeyboardButtonRow, ReplyInlineMarkup
                )
                btn    = KeyboardButtonUrl(text="🔗 Join Group", url=promo_link)
                markup = ReplyInlineMarkup(rows=[KeyboardButtonRow(buttons=[btn])])
                await client.send_message(chat_id, full_msg, parse_mode="html",
                                          buttons=markup, link_preview=False)
                sent += 1
                log.append(f"✅ {chat_name}")
                await asyncio.sleep(DELAY)
            except FloodWaitError as e:
                wait = min(e.seconds, 60)
                await asyncio.sleep(wait)
                try:
                    await client.send_message(chat_id, full_msg, parse_mode="html", link_preview=False)
                    sent += 1
                    log.append(f"✅ {chat_name} (retry)")
                    await asyncio.sleep(DELAY)
                except Exception:
                    failed += 1
                    log.append(f"❌ {chat_name}")
            except Exception as e:
                failed += 1
                log.append(f"❌ {chat_name}: {str(e)[:40]}")

        return {"ok": True, "sent": sent, "failed": failed, "total": total,
                "account": used_label, "log": log}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}
    finally:
        try: await client.disconnect()
        except Exception: pass

# ═══════════════════════════════════════════════════════
#  SCRAPING ENGINE (SQLite-based member scraping)
# ═══════════════════════════════════════════════════════

def _extract_user(user):
    """User object se data nikaalo (access_hash ke saath)."""
    is_deleted = getattr(user, "deleted", False)
    last_seen  = None
    is_active  = False
    st2 = getattr(user, "status", None)
    if isinstance(st2, UserStatusOnline):
        is_active = True
    elif isinstance(st2, UserStatusOffline) and getattr(st2, "was_online", None):
        try:
            last_seen = st2.was_online.isoformat()
        except Exception:
            pass
    return {
        "telegram_id":  str(user.id),
        "access_hash":  str(getattr(user, "access_hash", 0) or 0),
        "username":     getattr(user, "username", None),
        "first_name":   getattr(user, "first_name", None),
        "last_name":    getattr(user, "last_name", None),
        "is_active":    1 if is_active else 0,
        "is_deleted":   1 if is_deleted else 0,
        "last_seen":    last_seen,
    }

def _is_inactive_30d(user_dict):
    """
    Return True agar member 1 mahine se zyada purana ho (skip karo).
    Rules:
      - Online hai       → ACTIVE (rakh lo)
      - last_seen within 30 days → ACTIVE (rakh lo)
      - last_seen > 30 days ago  → INACTIVE (skip karo)
      - last_seen unknown (privacy) → ACTIVE (rakh lo — safe side)
      - deleted account           → SKIP
    """
    if user_dict.get("is_deleted"):
        return True
    if user_dict.get("is_active"):
        return False
    ls = user_dict.get("last_seen")
    if not ls:
        return False  # Privacy hidden — assume active
    try:
        last = datetime.fromisoformat(ls.replace("Z", "+00:00"))
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - last).days > 30
    except Exception:
        return False

def _db_save_members(conn, scrape_id, members_data):
    """Batch insert members into DB — ek baar mein sab save karo."""
    rows = [
        (scrape_id, m["telegram_id"], m["access_hash"],
         m["username"], m["first_name"], m["last_name"],
         m["is_active"], m["is_deleted"], m["last_seen"])
        for m in members_data
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO members "
        "(scrape_id,telegram_id,access_hash,username,first_name,"
        "last_name,is_active,is_deleted,last_seen) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()

async def scrape_group_members(phone, api_id, api_hash, group_target, scrape_id,
                               progress_cb=None):
    """
    Group ke ALL members scrape karo — teeno sources se:
      1. Member List   — group mein jo members dikhe
      2. Active Chat   — jo message kiya (active chatters)
      3. Poll Voters   — polls/quiz/anonymous polls mein jo vote kiya
    Sab combine + dedupe karke SQLite mein save.
    Limit: 10000. Returns: (total, stats_dict, error_msg)
    """
    client = get_client(phone, api_id, api_hash)
    LIMIT  = 10000

    def _cb(msg):
        if progress_cb:
            try: progress_cb(msg)
            except Exception: pass

    try:
        await client.connect()
        if not await client.is_user_authorized():
            return 0, {}, "Account authorized nahi!"

        entity   = await client.get_entity(group_target)
        seen_ids = set()
        all_members = []

        count_list   = 0
        count_chat   = 0
        count_poll   = 0

        skipped_inactive = 0

        # ════════════════════════════════════════════════════════
        # SOURCE 1 — Group Member List (iter_participants)
        # ════════════════════════════════════════════════════════
        _cb("👥 Source 1/3: Member list scan ho raha hai...")
        try:
            async for user in client.iter_participants(entity, aggressive=True):
                if len(all_members) >= LIMIT:
                    break
                if getattr(user, "bot", False):
                    continue
                uid = str(user.id)
                if uid in seen_ids:
                    continue
                seen_ids.add(uid)
                udata = _extract_user(user)
                if _is_inactive_30d(udata):
                    skipped_inactive += 1
                    continue
                all_members.append(udata)
                count_list += 1
                await asyncio.sleep(0)
        except Exception:
            pass
        _cb(f"✅ Member list: {count_list} active mila")

        # ════════════════════════════════════════════════════════
        # SOURCE 2 — Active Chat Members (message history)
        # ════════════════════════════════════════════════════════
        _cb(f"💬 Source 2/3: Active chatters scan ho rahe hain...")
        try:
            async for message in client.iter_messages(entity, limit=10000):
                if len(all_members) >= LIMIT:
                    break
                try:
                    sender = await message.get_sender()
                except Exception:
                    continue
                if not sender or not hasattr(sender, "id"):
                    continue
                uid2 = str(sender.id)
                if uid2 in seen_ids or getattr(sender, "bot", False):
                    continue
                seen_ids.add(uid2)
                udata2 = _extract_user(sender)
                # Message bheja hai → always active, skip 30-day check
                all_members.append(udata2)
                count_chat += 1
                await asyncio.sleep(0)
        except Exception:
            pass
        _cb(f"✅ Active chatters: {count_chat} naye mile")

        # ════════════════════════════════════════════════════════
        # SOURCE 3 — Poll / Quiz Voters (public polls only)
        # ════════════════════════════════════════════════════════
        _cb("📊 Source 3/3: Polls/Quiz scan ho rahe hain...")
        polls_found = 0
        try:
            async for message in client.iter_messages(
                entity,
                filter=InputMessagesFilterPoll(),
                limit=200,
            ):
                if not message.media or not isinstance(message.media, MessageMediaPoll):
                    continue
                polls_found += 1
                poll_obj = message.media.poll
                # Anonymous polls mein voters nahi milte — skip
                if not getattr(poll_obj, "public_voters", False):
                    continue

                for option in poll_obj.answers:
                    if len(all_members) >= LIMIT:
                        break
                    offset = ""
                    while True:
                        try:
                            vresult = await client(GetPollVotersRequest(
                                peer=entity, id=message.id,
                                option=option.option, offset=offset, limit=100,
                            ))
                            users_list = getattr(vresult, "users", None) or []
                            if not users_list:
                                break
                            for u in users_list:
                                uid3 = str(u.id)
                                if uid3 in seen_ids or getattr(u, "bot", False):
                                    continue
                                seen_ids.add(uid3)
                                # Poll voter → recently active, skip 30d check
                                all_members.append(_extract_user(u))
                                count_poll += 1
                            next_off = getattr(vresult, "next_offset", None)
                            if not next_off:
                                break
                            offset = next_off
                            await asyncio.sleep(0.3)
                        except Exception:
                            break
        except Exception:
            pass
        _cb(f"✅ Poll voters: {count_poll} naye mile ({polls_found} polls mile)")

        # ════════════════════════════════════════════════════════
        # SAVE TO DB
        # ════════════════════════════════════════════════════════
        if not all_members:
            conn = get_db()
            try:
                conn.execute(
                    "UPDATE scrape_jobs SET status='failed',error_msg=? WHERE id=?",
                    ("Koi member nahi mila. Group private/restricted ho sakta hai.", scrape_id)
                )
                conn.commit()
            finally:
                conn.close()
            return 0, {}, "Koi member nahi mila. Group private/restricted ho sakta hai."

        _cb(f"💾 {len(all_members)} members save ho rahe hain...")
        conn = get_db()
        try:
            _db_save_members(conn, scrape_id, all_members)
            total = len(all_members)
            conn.execute(
                "UPDATE scrape_jobs SET status='done',total_scraped=? WHERE id=?",
                (total, scrape_id)
            )
            conn.commit()
        finally:
            conn.close()

        stats = {
            "member_list":      count_list,
            "active_chat":      count_chat,
            "poll_voters":      count_poll,
            "polls_found":      polls_found,
            "skipped_inactive": skipped_inactive,
            "total":            total,
        }
        return total, stats, None

    except Exception as e:
        try:
            conn = get_db()
            conn.execute(
                "UPDATE scrape_jobs SET status='failed',error_msg=? WHERE id=?",
                (str(e)[:200], scrape_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        return 0, {}, str(e)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

# ═══════════════════════════════════════════════════════
#  POLL / QUIZ VOTERS SCRAPER ENGINE
# ═══════════════════════════════════════════════════════

async def find_polls_in_chat(phone, api_id, api_hash, group_target):
    """
    Group ki POORI history mein se sirf poll/quiz messages fetch karo.
    InputMessagesFilterPoll use karta hai — Telegram directly sirf polls bhejta hai,
    bina baaki messages scan kiye. Poori chat history cover hoti hai.
    Returns: (list of dicts, error_msg)
    """
    client = get_client(phone, api_id, api_hash)
    polls  = []
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return polls, "Account authorized nahi!"

        entity = await client.get_entity(group_target)

        # InputMessagesFilterPoll — directly Telegram server se sirf poll messages
        # limit=None matlab poori history, koi cap nahi
        async for message in client.iter_messages(
            entity,
            filter=InputMessagesFilterPoll(),
            limit=None,                    # poori history
        ):
            try:
                if not message.media or not isinstance(message.media, MessageMediaPoll):
                    continue
                poll      = message.media.poll
                results   = message.media.results
                total_v   = getattr(results, "total_voters", 0) or 0
                poll_type = "🧩 Quiz" if getattr(poll, "quiz", False) else "📊 Poll"

                # question string nikaalo (bytes ya str dono handle)
                q = poll.question
                if isinstance(q, bytes):
                    q = q.decode("utf-8", errors="ignore")
                q = str(q)[:80]

                polls.append({
                    "msg_id":       message.id,
                    "question":     q,
                    "type":         poll_type,
                    "total_voters": total_v,
                    "date":         message.date.strftime("%d %b %Y") if message.date else "",
                })
            except Exception:
                continue   # koi ek message fail hua — baaki continue karo

        if not polls:
            return polls, "Is group mein koi poll/quiz nahi mili."
        return polls, None

    except Exception as e:
        return polls, str(e)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def scrape_poll_voters(phone, api_id, api_hash, group_target, message_id, scrape_id):
    """
    Ek poll/quiz ke saare voters (sabhi options) scrape karo.
    access_hash bhi save karta hai taaki baad mein AddContact kaam kare.
    Returns: (total_scraped, error_msg)
    """
    client = get_client(phone, api_id, api_hash)
    conn   = get_db()
    total  = 0
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return 0, "Account authorized nahi!"

        entity = await client.get_entity(group_target)

        # Poll message fetch karo
        msg = await client.get_messages(entity, ids=message_id)
        if not msg or not isinstance(getattr(msg, "media", None), MessageMediaPoll):
            return 0, "Yeh message poll/quiz nahi hai!"

        poll         = msg.media.poll
        members_data = []
        seen         = set()

        # Har option ke voters fetch karo
        for option in poll.answers:
            offset = ""
            while True:
                try:
                    result = await client(GetPollVotesRequest(
                        peer    = entity,
                        id      = message_id,
                        option  = option.option,
                        offset  = offset,
                        limit   = 100,
                    ))
                    if not result.users:
                        break

                    for user in result.users:
                        uid = str(user.id)
                        if uid in seen or getattr(user, "bot", False):
                            continue
                        seen.add(uid)

                        is_deleted = getattr(user, "deleted", False)
                        members_data.append({
                            "telegram_id":  uid,
                            "access_hash":  str(getattr(user, "access_hash", 0) or 0),
                            "username":     getattr(user, "username", None),
                            "first_name":   getattr(user, "first_name", None),
                            "last_name":    getattr(user, "last_name", None),
                            "is_active":    0,
                            "is_deleted":   1 if is_deleted else 0,
                            "last_seen":    None,
                        })

                    if len(result.users) < 100:
                        break
                    # Next page
                    next_off = getattr(result, "next_offset", None)
                    if not next_off:
                        break
                    offset = next_off
                    await asyncio.sleep(0.5)

                except FloodWaitError as e:
                    await asyncio.sleep(min(e.seconds, 30))
                except Exception:
                    break  # Yeh option skip karo, agle pe jao

        if not members_data:
            return 0, "Koi voter nahi mila. Poll public nahi ho ya abhi tak vote nahi hua."

        # DB mein save karo
        for m in members_data:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO members "
                    "(scrape_id,telegram_id,access_hash,username,first_name,"
                    "last_name,is_active,is_deleted,last_seen) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (scrape_id, m["telegram_id"], m["access_hash"],
                     m["username"], m["first_name"], m["last_name"],
                     m["is_active"], m["is_deleted"], m["last_seen"]),
                )
            except Exception:
                pass

        total = len(members_data)
        conn.execute(
            "UPDATE scrape_jobs SET status='done',total_scraped=? WHERE id=?",
            (total, scrape_id)
        )
        conn.commit()
        return total, None

    except Exception as e:
        conn.execute(
            "UPDATE scrape_jobs SET status='failed',error_msg=? WHERE id=?",
            (str(e)[:200], scrape_id)
        )
        conn.commit()
        return 0, str(e)
    finally:
        safe_disconnect(client, asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop())
        conn.close()

# ═══════════════════════════════════════════════════════
#  TARGETED DM BROADCAST (scraped members ko DM)
# ═══════════════════════════════════════════════════════

async def do_targeted_broadcast(chat_id_bot, data_bc, bot_instance):
    """
    Scraped members ko DM karo — chunk-based, no duplicate, spam account skip.
    • Acc0 → members 1..N  |  Acc1 → members N+1..2N  (no cycling, no overlap)
    • Spam hit → acc mark karo, same members next acc se try karo
    • Sent/permanently-failed members DB se TURANT delete karo (auto-remove)
    • Processed members next campaign run mein nahi aayenge
    • User Master: max 5 members per account enforce hoga
    """
    cfg  = load_cfg()
    # User Master ke liye sirf unke own accounts use karo
    owner_uid = data_bc.get("owner_uid")
    if owner_uid and not is_main_master(owner_uid):
        # User Master → sirf unke accounts
        accs = get_user_accounts(owner_uid)
        # User Master limit enforce karo
        max_per_acc = min(data_bc.get("members_per_account", 5), 5)
    else:
        accs        = active_accounts(cfg)
        max_per_acc = data_bc.get("members_per_account", 5)

    if not accs:
        bot_instance.send_message(chat_id_bot, "❌ Koi active account nahi!")
        return

    scrape_id           = data_bc["scrape_id"]
    message             = data_bc["message"]
    media_type          = data_bc.get("media_type")
    file_id             = data_bc.get("file_id")
    members_per_account = max_per_acc

    conn = get_db()
    cur  = conn.execute(
        "INSERT INTO broadcast_jobs (scrape_id,message,media_type,members_per_account,status) "
        "VALUES (?,?,?,?,?)",
        (scrape_id, message, media_type, members_per_account, "running"),
    )
    broadcast_id = cur.lastrowid
    conn.commit()

    members = conn.execute(
        "SELECT * FROM members WHERE scrape_id=? AND is_deleted=0 ORDER BY id",
        (scrape_id,),
    ).fetchall()
    conn.close()

    # 30-day inactive skip + eligible list
    eligible         = []
    skipped_inactive = 0
    for m in members:
        if is_long_inactive(m["last_seen"]):
            skipped_inactive += 1
        else:
            eligible.append(m)

    total_targeted = len(eligible)
    bot_instance.send_message(
        chat_id_bot,
        f"📢 <b>Targeted Broadcast Shuru!</b>\n\n"
        f"👥 Eligible members: <b>{total_targeted}</b>\n"
        f"⏭ Inactive (skip): <b>{skipped_inactive}</b>\n"
        f"📱 Accounts: <b>{len(accs)}</b>\n"
        f"🔢 Per account: <b>{members_per_account}</b>\n\n"
        "ℹ️ Har member ek baar, ek hi account se message milega."
    )

    total_sent    = 0
    total_failed  = 0
    total_skipped = 0
    spammy_phones = set()    # PeerFlood pe blacklist
    deleted_ids   = []       # turant delete ho chuke IDs

    # ── helper: delete member from DB right away ──────────────────────────────
    def _del_member(mid):
        try:
            c = get_db()
            c.execute("DELETE FROM members WHERE id=?", (mid,))
            c.commit()
            c.close()
        except Exception:
            pass

    # ── helper: send one DM (text or media) ──────────────────────────────────
    async def _send_one(client, target, bc_id, mid_val, ext="jpg"):
        if file_id and media_type in ("photo", "video"):
            cfg2     = load_cfg()
            file_info = bot_instance.get_file(file_id)
            file_url  = (
                f"https://api.telegram.org/file/bot{cfg2['bot_token']}/{file_info.file_path}"
            )
            import urllib.request
            tmp_path = os.path.join(MEDIA_DIR, f"tmp_{bc_id}_{mid_val}.{ext}")
            urllib.request.urlretrieve(file_url, tmp_path)
            await client.send_file(target, tmp_path, caption=message)
            try: os.remove(tmp_path)
            except Exception: pass
        else:
            await client.send_message(target, message, link_preview=False)

    # ── chunk loop — each member processed by exactly one account ─────────────
    i       = 0
    acc_idx = 0

    while i < len(eligible):
        # Skip spammy accounts
        while acc_idx < len(accs) and accs[acc_idx]["phone"] in spammy_phones:
            acc_idx += 1

        if acc_idx >= len(accs):
            remaining = len(eligible) - i
            bot_instance.send_message(chat_id_bot,
                f"⚠️ Saare accounts spam/expire ho gaye!\n"
                f"Baki <b>{remaining}</b> members skip ho gaye.")
            total_skipped += remaining
            break

        acc         = accs[acc_idx]
        chunk       = eligible[i : i + members_per_account]
        chunk_start = i

        bot_instance.send_message(chat_id_bot,
            f"📱 <code>{acc['phone']}</code> → "
            f"members {i+1}–{min(i+members_per_account, total_targeted)}/{total_targeted}")

        acc_sent = 0
        spam_hit = False
        members_done_in_chunk = 0  # kitne members is chunk mein process hue spam se pehle

        ext = "mp4" if media_type == "video" else "jpg"

        client = get_client(acc["phone"], cfg["api_id"], cfg["api_hash"])
        try:
            await client.connect()
            if not await client.is_user_authorized():
                bot_instance.send_message(chat_id_bot,
                    f"⚠️ <code>{acc['phone']}</code> session expire — next account!")
                # Don't advance i — same members try with next account\n                acc_idx += 1\n                continue\n\n            for j, member in enumerate(chunk):\n                uid_m    = int(member["telegram_id"])\n                acc_hash = int(member["access_hash"] or 0)\n                uname    = (member["username"] or "").strip()\n\n                # Resolve target\n                try:\n                    if acc_hash:\n                        target = InputUser(user_id=uid_m, access_hash=acc_hash)\n                    elif uname:\n                        target = await client.get_input_entity(f"@{uname}")\n                    else:\n                        target = uid_m\n                except Exception:\n                    target = uid_m\n\n                try:\n                    await _send_one(client, target, broadcast_id, member["id"], ext)\n                    acc_sent   += 1\n                    total_sent += 1\n                    members_done_in_chunk = j + 1\n                    _del_member(member["id"])\n                    deleted_ids.append(member["id"])\n                    await asyncio.sleep(DELAY_DM)\n\n                except (UserPrivacyRestrictedError, UserIsBlockedError,\n                        InputUserDeactivatedError):\n                    total_skipped += 1\n                    members_done_in_chunk = j + 1\n                    _del_member(member["id"])\n                    deleted_ids.append(member["id"])\n\n                except PeerFloodError:\n                    spammy_phones.add(acc["phone"])\n                    spam_hit = True\n                    bot_instance.send_message(chat_id_bot,\n                        f"🚫 <code>{acc['phone']}</code> SPAM! "\n                        f"Is account se {j} members done. Baki next account se...")\n                    # i will be reset to chunk_start + j so next acc re-handles from here\n                    members_done_in_chunk = j\n                    break\n\n                except FloodWaitError as e:\n                    wait = min(e.seconds, 90)\n                    bot_instance.send_message(chat_id_bot,\n                        f"⏳ FloodWait {e.seconds}s — {wait}s ruk raha hoon...")\n                    await asyncio.sleep(wait)\n                    try:\n                        await _send_one(client, target, broadcast_id, member["id"], ext)\n                        acc_sent   += 1\n                        total_sent += 1\n                        members_done_in_chunk = j + 1\n                        _del_member(member["id"])\n                        deleted_ids.append(member["id"])\n                    except Exception:\n                        total_failed += 1\n                        members_done_in_chunk = j + 1\n\n                except Exception:\n                    total_failed += 1\n                    members_done_in_chunk = j + 1\n\n            # Account summary\n            if acc_sent:\n                bot_instance.send_message(chat_id_bot,\n                    f"✅ <code>{acc['phone']}</code>: <b>{acc_sent}</b> messages sent."\n                    + (f"\n🚫 Spam hit — next account lete hain." if spam_hit else ""))\n\n        except Exception as e:\n            bot_instance.send_message(chat_id_bot,\n                f"❌ <code>{acc['phone']}</code> error: {e}")\n            members_done_in_chunk = len(chunk)\n        finally:\n            try: await client.disconnect()\n            except Exception: pass\n\n        # Advance i only by members actually processed\n        i = chunk_start + members_done_in_chunk\n        # Always move to next account (spammy ones will be skipped at top of loop)\n        acc_idx += 1\n        await asyncio.sleep(2)\n\n    # ── Update DB stats ───────────────────────────────────────────────────────\n    conn = get_db()\n    conn.execute(\n        "UPDATE broadcast_jobs SET status='done',total_sent=?,total_failed=?,total_skipped=? WHERE id=?",\n        (total_sent, total_failed, total_skipped + skipped_inactive, broadcast_id),\n    )\n    conn.commit()\n    conn.close()\n\n    bot_instance.send_message(\n        chat_id_bot,\n        f"🎉 <b>Broadcast Complete!</b>\n\n"\n        f"✅ Sent: <b>{total_sent}</b>\n"\n        f"❌ Failed: <b>{total_failed}</b>\n"\n        f"⏭ Skipped (privacy/inactive): <b>{total_skipped + skipped_inactive}</b>\n"\n        f"🗑️ DB se remove: <b>{len(deleted_ids)}</b>\n"\n        f"━━━━━━━━━━\n"\n        f"📊 Total targeted: <b>{total_targeted}</b>"\n    )\n\n# ═══════════════════════════════════════════════════════\n#  GROUP ADD CAMPAIGN ENGINE  (v2 — no phone number leak)\n#  Flow:\n#    Phase 1 — Direct InviteToChannelRequest (no AddContact)\n#      For each member: try adding to target group directly\n#        ✅ Success     → delete from members DB (no duplicate)\n#        🔒 Privacy     → privacy_queue (phase 2)\n#        ⚠️ Flood/Spam  → switch account\n#\n#    Phase 2 — Send invite link to privacy-blocked members\n#      Try DM with invite link\n#        ✅ Sent  → delete from members DB\n#        🔒 Privacy again → skip\n# ═══════════════════════════════════════════════════════\n\nasync def do_group_add_campaign(chat_id_bot, scrape_id, target_group, invite_link,\n                                 max_per_acc, bot_instance):\n    """\n    Phase 1: InviteToChannelRequest se directly group mein add karo (no AddContact).\n    Phase 2: Privacy-blocked members ko invite link DM karo.\n    • Har member SIRF EK account se process hoga (no duplicate)\n    • Spam account → blacklist, same members next account se try\n    • Processed/failed members DB se TURANT delete hote hain\n    """\n    d    = load()\n    cfg  = d["config"]\n    accs = active_accounts(d)\n\n    if not accs:\n        bot_instance.send_message(chat_id_bot, "❌ Koi active account nahi! Pehle /add karo.")\n        return\n\n    conn    = get_db()\n    members = conn.execute(\n        "SELECT * FROM members WHERE scrape_id=? AND is_deleted=0 ORDER BY id",\n        (scrape_id,)\n    ).fetchall()\n    cur = conn.execute(\n        "INSERT INTO contact_add_jobs (scrape_id,invite_link,broadcast_msg,max_per_acc) VALUES (?,?,?,?)",\n        (scrape_id, invite_link, "", max_per_acc)\n    )\n    job_id = cur.lastrowid\n    conn.commit()\n    conn.close()\n\n    total         = len(members)\n    member_list   = list(members)\n    grand_added   = 0\n    grand_link    = 0\n    grand_failed  = 0\n    grand_deleted = 0\n    privacy_queue = []   # Phase 2 ke liye\n    spammy_phones = set()  # Phase 1 spam accounts — Phase 2 mein bhi skip honge\n\n    # ── helper: delete member from DB immediately ─────────────────────────────\n    def _del(mid):\n        nonlocal grand_deleted\n        try:\n            c = get_db()\n            c.execute("DELETE FROM members WHERE id=?", (mid,))\n            c.commit()\n            c.close()\n            grand_deleted += 1\n        except Exception:\n            pass\n\n    # ── helper: resolve InputUser ─────────────────────────────────────────────\n    async def resolve_user(client, member):\n        uid_m    = int(member["telegram_id"])\n        acc_hash = int(member["access_hash"] or 0)\n        uname    = (member["username"] or "").strip()\n        if acc_hash:\n            return InputUser(user_id=uid_m, access_hash=acc_hash)\n        if uname:\n            try:\n                return await client.get_input_entity(f"@{uname}")\n            except Exception:\n                pass\n        try:\n            return await client.get_input_entity(uid_m)\n        except Exception:\n            return None\n\n    bot_instance.send_message(\n        chat_id_bot,\n        f"🚀 <b>Group Add Campaign Shuru!</b>\n\n"\n        f"🎯 Target: <code>{target_group}</code>\n"\n        f"👥 Total members: <b>{total}</b>\n"\n        f"📱 Accounts: <b>{len(accs)}</b>\n"\n        f"🔢 Per account: <b>{max_per_acc}</b>\n\n"\n        "ℹ️ Har member ek baar, ek hi account se try hoga."\n    )\n\n    # ── Normalize target group ────────────────────────────────────────────────\n    tg = target_group.strip()\n    if tg.startswith("https://t.me/"):\n        slug = tg.split("https://t.me/")[1].split("/")[0]\n        tg   = ("https://t.me/" + slug) if slug.startswith("+") else ("@" + slug)\n    elif not tg.startswith("@") and not tg.startswith("-") and not tg.lstrip("-").isdigit():\n        tg = "@" + tg\n\n    # ═══════════════════════════════════════════════════════════\n    #  PHASE 1: Direct InviteToChannelRequest\n    # ═══════════════════════════════════════════════════════════\n    i       = 0\n    acc_idx = 0\n\n    while i < len(member_list):\n        # Skip spammy accounts\n        while acc_idx < len(accs) and accs[acc_idx]["phone"] in spammy_phones:\n            acc_idx += 1\n\n        if acc_idx >= len(accs):\n            bot_instance.send_message(chat_id_bot,\n                f"⚠️ Saare accounts spam/khatam!\n"\n                f"Baki {len(member_list)-i} members → Phase 2 invite link mein.")\n            privacy_queue.extend(member_list[i:])\n            break\n\n        acc         = accs[acc_idx]\n        chunk       = member_list[i : i + max_per_acc]\n        chunk_start = i\n\n        bot_instance.send_message(chat_id_bot,\n            f"📱 <code>{acc['phone']}</code> — "\n            f"members {i+1}–{min(i+max_per_acc, total)}/{total}")\n\n        acc_added = 0\n        acc_priv  = 0\n        spam_hit  = False\n        done_in_chunk = 0   # kitne process hue spam se pehle\n\n        client = get_client(acc["phone"], cfg["api_id"], cfg["api_hash"])\n        try:\n            await client.connect()\n            if not await client.is_user_authorized():\n                bot_instance.send_message(chat_id_bot,\n                    f"⚠️ <code>{acc['phone']}</code> session expire — next account!")\n                # Don't advance i — same members next account se
                acc_idx += 1
                continue

            try:
                group_entity = await client.get_entity(tg)
            except Exception as e:
                bot_instance.send_message(chat_id_bot,
                    f"❌ Group resolve fail ({acc['phone']}): {e}\n"
                    "Sab members Phase 2 mein.")
                privacy_queue.extend(chunk)
                done_in_chunk = len(chunk)
                acc_idx += 1
                i = chunk_start + done_in_chunk
                continue

            for j, member in enumerate(chunk):
                input_user = await resolve_user(client, member)

                if input_user is None:
                    privacy_queue.append(member)
                    acc_priv += 1
                    done_in_chunk = j + 1
                    continue

                try:
                    await client(InviteToChannelRequest(
                        channel=group_entity, users=[input_user]
                    ))
                    acc_added   += 1
                    grand_added += 1
                    done_in_chunk = j + 1
                    _del(member["id"])          # turant delete
                    await asyncio.sleep(1.5)

                except (UserPrivacyRestrictedError, UserNotMutualContactError,
                        UserChannelsTooMuchError):
                    privacy_queue.append(member)
                    acc_priv += 1
                    done_in_chunk = j + 1

                except (UserBannedInChannelError, InputUserDeactivatedError,
                        UserIsBlockedError):
                    grand_failed += 1
                    done_in_chunk = j + 1
                    _del(member["id"])          # permanently gone

                except PeerFloodError:
                    spammy_phones.add(acc["phone"])
                    spam_hit = True
                    done_in_chunk = j           # j mein spam hua — j nahi process hua
                    privacy_queue.append(member)
                    privacy_queue.extend(chunk[j+1:])  # baki bhi queue
                    bot_instance.send_message(chat_id_bot,
                        f"🚫 <code>{acc['phone']}</code> SPAM (Phase 1)! "
                        f"{j} add done. Baki next account se...")
                    break

                except FloodWaitError as e:
                    wait = min(e.seconds, 90)
                    await asyncio.sleep(wait)
                    try:
                        await client(InviteToChannelRequest(
                            channel=group_entity, users=[input_user]
                        ))
                        acc_added   += 1
                        grand_added += 1
                        done_in_chunk = j + 1
                        _del(member["id"])
                    except Exception:
                        privacy_queue.append(member)
                        acc_priv += 1
                        done_in_chunk = j + 1

                except Exception:
                    privacy_queue.append(member)
                    grand_failed += 1
                    done_in_chunk = j + 1

            bot_instance.send_message(chat_id_bot,
                f"✅ <code>{acc['phone']}</code>:\n"
                f"  ✅ Added: <b>{acc_added}</b>  🔒 Queue: <b>{acc_priv}</b>"
                + (f"\n  🚫 Spam hit — blacklisted" if spam_hit else ""))

        except Exception as e:
            bot_instance.send_message(chat_id_bot,
                f"❌ <code>{acc['phone']}</code> error: {e}")
            privacy_queue.extend(chunk)
            done_in_chunk = len(chunk)
        finally:
            try: await client.disconnect()
            except Exception: pass

        i       = chunk_start + done_in_chunk
        acc_idx += 1
        await asyncio.sleep(2)

    # ═══════════════════════════════════════════════════════════
    #  PHASE 2: Invite Link DM (privacy-blocked members)
    # ═══════════════════════════════════════════════════════════
    grand_dm_fail = 0

    if privacy_queue and invite_link:
        bot_instance.send_message(
            chat_id_bot,
            f"\n📨 <b>Phase 2: Invite Link DM</b>\n"
            f"🔒 Members: <b>{len(privacy_queue)}</b>\n"
            f"🚫 Spam-blacklisted accounts skip honge: {len(spammy_phones)}"
        )

        dm_list    = list(privacy_queue)
        j          = 0
        dm_acc_idx = 0

        while j < len(dm_list):
            # Skip spammy accounts in Phase 2 as well
            while dm_acc_idx < len(accs) and accs[dm_acc_idx]["phone"] in spammy_phones:
                dm_acc_idx += 1

            if dm_acc_idx >= len(accs):
                bot_instance.send_message(chat_id_bot,
                    f"⚠️ Phase 2 mein saare accounts spam/khatam! "
                    f"{len(dm_list)-j} links nahi bheje ja sake.")
                break

            acc           = accs[dm_acc_idx]
            dm_chunk      = dm_list[j : j + max_per_acc]
            chunk_start_2 = j
            acc_sent      = 0
            spam2_hit     = False
            done_dm       = 0

            client = get_client(acc["phone"], cfg["api_id"], cfg["api_hash"])
            try:
                await client.connect()
                if not await client.is_user_authorized():
                    dm_acc_idx += 1
                    continue      # same j, next account

                for k, member in enumerate(dm_chunk):
                    fname     = member["first_name"] or "User"
                    dm_target = await resolve_user(client, member)

                    if dm_target is None:
                        grand_dm_fail += 1
                        done_dm = k + 1
                        _del(member["id"])
                        continue

                    link_msg = (
                        f"👋 Namaste {fname}!\n\n"
                        f"Hamare group mein join karein:\n"
                        f"🔗 {invite_link}"
                    )
                    try:
                        await client.send_message(dm_target, link_msg, link_preview=False)
                        acc_sent   += 1
                        grand_link += 1
                        done_dm    = k + 1
                        _del(member["id"])
                        await asyncio.sleep(DELAY_DM)

                    except (UserPrivacyRestrictedError, UserIsBlockedError,
                            InputUserDeactivatedError):
                        grand_dm_fail += 1
                        done_dm = k + 1
                        _del(member["id"])

                    except PeerFloodError:
                        spammy_phones.add(acc["phone"])
                        spam2_hit = True
                        done_dm   = k    # k nahi gaya
                        bot_instance.send_message(chat_id_bot,
                            f"🚫 <code>{acc['phone']}</code> SPAM (Phase 2)! "
                            f"Next account...")
                        break

                    except FloodWaitError as e:
                        await asyncio.sleep(min(e.seconds, 60))
                        try:
                            await client.send_message(dm_target, link_msg, link_preview=False)
                            acc_sent   += 1
                            grand_link += 1
                            done_dm    = k + 1
                            _del(member["id"])
                        except Exception:
                            grand_dm_fail += 1
                            done_dm = k + 1

                    except Exception:
                        grand_dm_fail += 1
                        done_dm = k + 1

                if acc_sent:
                    bot_instance.send_message(chat_id_bot,
                        f"✅ Link DM <code>{acc['phone']}</code>: <b>{acc_sent}</b> sent."
                        + (f"\n🚫 Spam hit!" if spam2_hit else ""))

            except Exception as e:
                bot_instance.send_message(chat_id_bot,
                    f"❌ DM {acc['phone']} error: {e}")
                done_dm = len(dm_chunk)
            finally:
                try: await client.disconnect()
                except Exception: pass

            j = chunk_start_2 + done_dm
            dm_acc_idx += 1
            await asyncio.sleep(2)

    elif privacy_queue and not invite_link:
        bot_instance.send_message(chat_id_bot,
            f"ℹ️ Invite link nahi diya tha — "
            f"{len(privacy_queue)} privacy-blocked members skip ho gaye.")

    # ── Save final stats ──────────────────────────────────────────────────────
    conn = get_db()
    conn.execute(
        "UPDATE contact_add_jobs SET status='done',"
        "total_contact_added=?,total_link_sent=?,total_dm_sent=?,"
        "total_privacy_skip=?,total_failed=? WHERE id=?",
        (grand_added, grand_link, 0, grand_dm_fail, grand_failed, job_id)
    )
    conn.commit()
    conn.close()

    # ── Final summary ─────────────────────────────────────────────────────────
    remaining = total - grand_deleted
    bot_instance.send_message(
        chat_id_bot,
        f"🎉 <b>Group Add Campaign Complete!</b>\n\n"
        f"🎯 Group: <code>{target_group}</code>\n"
        f"👥 Total: <b>{total}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>Phase 1 — Direct Add:</b>  <b>{grand_added}</b>\n"
        f"🔗 <b>Phase 2 — Link DM:</b>     <b>{grand_link}</b>\n"
        f"❌ <b>Unreachable/Failed:</b>    <b>{grand_dm_fail + grand_failed}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🗑️ DB se remove: <b>{grand_deleted}</b> members\n"
        f"📂 Remaining in DB: <b>{remaining}</b> (next campaign ke liye)"
    )

# ═══════════════════════════════════════════════════════
#  BOT SETUP
# ═══════════════════════════════════════════════════════

def _init_bot_token():
    """Load config from ENV vars (Heroku) or prompt on first CLI run."""
    d = load()
    cfg = d["config"]
    changed = False

    # ── Heroku / environment variable support ────────────────────────────────
    env_token    = os.environ.get("BOT_TOKEN", "").strip()
    env_api_id   = os.environ.get("API_ID", "").strip()
    env_api_hash = os.environ.get("API_HASH", "").strip()
    env_admin_id = os.environ.get("ADMIN_ID", "").strip()

    if env_token and not cfg.get("bot_token"):
        cfg["bot_token"] = env_token; changed = True
    if env_api_id and not cfg.get("api_id"):
        try: cfg["api_id"] = int(env_api_id); changed = True
        except ValueError: pass
    if env_api_hash and not cfg.get("api_hash"):
        cfg["api_hash"] = env_api_hash; changed = True
    if env_admin_id and not cfg.get("admin_ids"):
        try: cfg["admin_ids"].append(int(env_admin_id)); changed = True
        except ValueError: pass
    if changed:
        save(d); return

    # ── CLI fallback (local run) ──────────────────────────────────────────────
    if not cfg.get("bot_token"):
        print("\n╔══════════════════════════════════════════════╗")
        print("║   Pehli baar setup — Bot Token daalo        ║")
        print("╚══════════════════════════════════════════════╝\n")
        tok = input("  Bot Token paste karo: ").strip()
        if not tok:
            print("Token zaruri hai!")
            sys.exit(1)
        cfg["bot_token"] = tok
        save(d)
    if not cfg.get("api_id"):
        print("\n  Telegram API credentials (https://my.telegram.org/apps):")
        api_id_s = input("  API ID (number): ").strip()
        api_hash = input("  API Hash: ").strip()
        try:
            cfg["api_id"]   = int(api_id_s)
            cfg["api_hash"] = api_hash
        except ValueError:
            print("Galat API ID!")
            sys.exit(1)
        save(d)
    if not cfg.get("admin_ids"):
        print("\n  Apna Telegram User ID daalo.")
        admin_id_s = input("  Apna Telegram User ID: ").strip()
        if admin_id_s.isdigit():
            cfg["admin_ids"].append(int(admin_id_s))
        save(d)

_init_bot_token()
_cfg = load()
bot  = TeleBot(_cfg["config"]["bot_token"], parse_mode="HTML")

# ── Admin check ───────────────────────────────────────────────────────────────
def is_admin(uid_or_msg):
    if hasattr(uid_or_msg, "from_user"):
        uid = uid_or_msg.from_user.id
    else:
        try:
            uid = int(uid_or_msg)
        except Exception:
            return False
    d    = load()
    ids  = d["config"].get("admin_ids", [])
    if uid in ids or str(uid) in [str(x) for x in ids]:
        return True
    try:
        conn = get_db()
        row  = conn.execute("SELECT id FROM admins WHERE telegram_user_id=?", (str(uid),)).fetchone()
        conn.close()
        return row is not None
    except Exception:
        return False

def admin_only(fn):
    def wrapper(msg):
        if not is_admin(msg.from_user.id):
            bot.reply_to(msg, "❌ Aapko permission nahi hai.")
            return
        return fn(msg)
    return wrapper

def admin_only_cb(fn):
    def wrapper(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "❌ Permission nahi hai")
            return
        return fn(call)
    return wrapper

def user_access_cb(fn):
    """User Master + Main Master + Admin callbacks ke liye — check_user_access use karta hai."""
    def wrapper(call):
        if not check_user_access(call.from_user.id):
            bot.answer_callback_query(call.id, "❌ Access nahi hai")
            return
        return fn(call)
    return wrapper

# ═══════════════════════════════════════════════════════
#  TWO-TIER MASTER SYSTEM
# ═══════════════════════════════════════════════════════

def get_main_master_id():
    """Main Master ID fetch karo — config se, fallback admin_ids[0]"""
    d    = load()
    mmid = d["config"].get("main_master_id", 0)
    if not mmid:
        ids = d["config"].get("admin_ids", [])
        if ids:
            mmid = int(ids[0])
    return mmid

def is_main_master(uid):
    """Kya yeh user Main Master hai? (Full access)"""
    try:
        mmid = get_main_master_id()
        return mmid and (int(uid) == int(mmid))
    except Exception:
        return False

def is_user_master(uid):
    """Kya yeh user User Master hai? (Limited access — sirf apne accounts)"""
    d   = load()
    ums = [str(x) for x in d["config"].get("user_masters", [])]
    return str(uid) in ums

def get_user_accounts(uid):
    """
    User ke liye accessible accounts return karo:
    • Main Master → sab active accounts
    • User Master → sirf woh accounts jo unhone add kiye
    """
    if is_main_master(uid):
        return active_accounts()
    d      = load()
    owners = d.get("account_owners", {})
    owned_phones = {phone for phone, owner in owners.items() if str(owner) == str(uid)}
    return [a for a in active_accounts() if a["phone"] in owned_phones]

def get_user_scrape_jobs(uid, limit=20):
    """
    User ke liye visible scrape jobs:
    • Main Master → saari done jobs
    • User Master → sirf unki apni jobs
    """
    conn = get_db()
    if is_main_master(uid):
        jobs = conn.execute(
            "SELECT * FROM scrape_jobs WHERE status='done' ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    else:
        jobs = conn.execute(
            "SELECT * FROM scrape_jobs WHERE status='done' AND owner_id=? ORDER BY id DESC LIMIT ?",
            (str(uid), limit)
        ).fetchall()
    conn.close()
    return jobs

def is_blacklisted(group_str):
    """Kya yeh group blacklist mein hai?"""
    d         = load()
    blacklist = d["config"].get("blacklist_groups", [])
    s         = str(group_str).strip().lower().lstrip("@")
    for b in blacklist:
        if s == str(b).strip().lower().lstrip("@"):
            return True
        if s == str(b).strip().lower():
            return True
    return False

def check_user_access(uid):
    """User ka access level return karo"""
    if is_main_master(uid):
        return "main_master"
    if is_user_master(uid):
        return "user_master"
    if is_admin(uid):
        return "admin"
    return None

# ═══════════════════════════════════════════════════════
#  FORCE JOIN ENGINE (Bot Start pe 3 Groups Join)
# ═══════════════════════════════════════════════════════

async def force_join_groups_for_account(phone, api_id, api_hash, groups, progress_cb=None):
    """Ek account se sabhi force-join groups join karo"""
    from telethon.tl.functions.channels import JoinChannelRequest
    client = get_client(phone, api_id, api_hash)
    results = []
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return results
        for group in groups:
            if is_blacklisted(group):
                results.append({"group": group, "status": "blacklisted"})
                continue
            try:
                entity = await client.get_entity(group)
                await client(JoinChannelRequest(entity))
                results.append({"group": group, "status": "joined"})
                if progress_cb:
                    progress_cb(phone, group, "joined")
                await asyncio.sleep(1)
            except Exception as e:
                results.append({"group": group, "status": f"failed: {str(e)[:50]}"})
    except Exception:
        pass
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
    return results

def run_force_join_all(chat_id_report=None):
    """Sab active accounts se force join groups join karo — background thread mein"""
    d      = load()
    cfg    = d["config"]
    groups = cfg.get("force_join_groups", [])
    if not groups:
        return
    accs   = active_accounts()
    if not accs:
        return

    def _thread():
        log = []
        for acc in accs:
            phone  = acc["phone"]
            label  = acc.get("label") or phone
            loop   = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(
                    force_join_groups_for_account(
                        phone, cfg["api_id"], cfg["api_hash"], groups
                    )
                )
                for r in results:
                    icon = "✅" if r["status"] == "joined" else "⚠️"
                    log.append(f"{icon} [{label}] {r['group']} — {r['status']}")
            except Exception as e:
                log.append(f"❌ [{label}] Error: {str(e)[:60]}")
            finally:
                loop.close()
            time.sleep(2)

        if chat_id_report and log:
            try:
                msg_text = "🔗 <b>Force Join Complete!</b>\n\n" + "\n".join(log[:30])
                bot.send_message(chat_id_report, msg_text)
            except Exception:
                pass

    threading.Thread(target=_thread, daemon=True, name="force-join").start()

# ═══════════════════════════════════════════════════════
#  MUSIC BOT JOIN ENGINE (Scrape se pehle bots add karo)
# ═══════════════════════════════════════════════════════

async def add_music_bots_to_group(phone, api_id, api_hash, target_group):
    """
    Scrape se pehle music bots ko target group mein join karwao.
    Bot usernames config mein stored hain.
    """
    from telethon.tl.functions.channels import InviteToChannelRequest as InvChan
    d              = load()
    bot_usernames  = d["config"].get("music_bot_usernames", [])
    if not bot_usernames:
        return []
    client = get_client(phone, api_id, api_hash)
    results = []
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return results
        entity = await client.get_entity(target_group)
        for bot_uname in bot_usernames:
            try:
                bot_entity = await client.get_entity(bot_uname)
                await client(InvChan(entity, [bot_entity]))
                results.append({"bot": bot_uname, "status": "added"})
                await asyncio.sleep(1)
            except Exception as e:
                # Already member ya error — ignore
                results.append({"bot": bot_uname, "status": f"skip: {str(e)[:40]}"})
    except Exception as e:
        results.append({"error": str(e)[:80]})
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
    return results

# ── Keyboards ─────────────────────────────────────────────────────────────────
def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📢 Broadcast"), KeyboardButton("🎯 Targeted DM"))
    kb.row(KeyboardButton("🔍 Scrape"),    KeyboardButton("👥 Members"))
    kb.row(KeyboardButton("📊 Stats"),     KeyboardButton("📱 Accounts"))
    kb.row(KeyboardButton("📤 Export CSV"),KeyboardButton("🔎 Check Limit"))
    kb.row(KeyboardButton("📋 History"),   KeyboardButton("❓ Help"))
    return kb

def main_inline_kb(uid=None):
    """Inline keyboard with main commands — use this for menu messages.

    Master/admin-only settings (Force Join, Music Bots, MongoDB URI, Sessions)
    are only shown when the caller is the Main Master. Regular users and
    User Masters only see the buttons that are actually usable by them.
    """
    is_main = bool(uid is not None and is_main_master(uid))

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📢 Broadcast",    callback_data="menu_broadcast"),
        InlineKeyboardButton("🎯 Targeted DM",  callback_data="menu_targeted"),
    )
    kb.add(
        InlineKeyboardButton("🔍 Scrape",       callback_data="menu_scrape"),
        InlineKeyboardButton("👥 Members",      callback_data="menu_members"),
    )
    kb.add(
        InlineKeyboardButton("⚔️ Reply Raid",   callback_data="menu_replyraid"),
        InlineKeyboardButton("🛑 Stop Raid",    callback_data="menu_stopraid"),
    )
    kb.add(
        InlineKeyboardButton("🏷 Tag All",      callback_data="menu_tagall"),
        InlineKeyboardButton("📣 Promo",        callback_data="menu_promo"),
    )
    kb.add(
        InlineKeyboardButton("🤖 Auto-Reply",   callback_data="menu_autoreply"),
        InlineKeyboardButton("👤 Clone Profile",callback_data="menu_cloneprofile"),
    )
    kb.add(
        InlineKeyboardButton("🧹 Auto Clean",   callback_data="menu_autoclean"),
        InlineKeyboardButton("📊 Stats",        callback_data="menu_stats"),
    )
    kb.add(
        InlineKeyboardButton("📱 Accounts",     callback_data="menu_accounts"),
        InlineKeyboardButton("➕ Add Account",  callback_data="add_account"),
    )
    kb.add(
        InlineKeyboardButton("📤 Export CSV",   callback_data="menu_exportcsv"),
        InlineKeyboardButton("🔎 Check Limit",  callback_data="menu_checklimit"),
    )
    kb.add(
        InlineKeyboardButton("📋 History",      callback_data="menu_history"),
        InlineKeyboardButton("❓ Help",         callback_data="menu_help"),
    )

    # ── Main Master only settings ──────────────────────────────────────────
    if is_main:
        kb.add(
            InlineKeyboardButton("🔗 Force Join",   callback_data="menu_forcejoin"),
            InlineKeyboardButton("🎵 Music Bots",   callback_data="menu_musicbots"),
        )
        kb.add(
            InlineKeyboardButton("🍃 MongoDB URI",  callback_data="menu_setmongouri"),
            InlineKeyboardButton("🔑 Sessions",     callback_data="menu_sessions"),
        )
    return kb

def cancel_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("❌ Cancel"))
    return kb

def make_inline(rows):
    kb = InlineKeyboardMarkup()
    for row in rows:
        kb.add(*[InlineKeyboardButton(t, callback_data=cd) for t, cd in row])
    return kb

# ── Session state dicts ───────────────────────────────────────────────────────
user_state         = {}   # uid → {step, data}  (for: add_phone/otp/2fa, scrape, targeted bc, admin)
broadcast_sessions = {}   # uid → {step, text, media...}  (dialog broadcast wizard)
tagall_sessions    = {}   # uid → {step, groups, selected, mode}
promo_sessions     = {}   # uid → {step, text, link}
clone_sessions     = {}   # uid → True (waiting for target user id)

def get_state(uid):
    return user_state.get(uid, {})

def set_state(uid, step, data=None):
    user_state[uid] = {"step": step, "data": data or {}}

def clear_state(uid):
    user_state.pop(uid, None)

# ═══════════════════════════════════════════════════════
#  BOT COMMANDS
# ═══════════════════════════════════════════════════════

# ── /start ────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid  = msg.from_user.id
    clear_state(uid)
    name = msg.from_user.first_name or "User"

    # Access level check — naya user hai toh auto User Master bana do
    access = check_user_access(uid)
    if not access:
        d2  = load()
        ums = d2["config"].setdefault("user_masters", [])
        if uid not in ums:
            ums.append(uid)
            save(d2)
            try:
                mm = get_main_master_id()
                if mm and mm != uid:
                    bot.send_message(mm,
                        f"\U0001f514 <b>Naya User join kiya!</b>\n"
                        f"\U0001f464 Name: <b>{name}</b>\n"
                        f"\U0001f194 ID: <code>{uid}</code>\n\n"
                        f"Hatane ke liye: <code>/removeusermaster {uid}</code>",
                        parse_mode="HTML")
            except Exception:
                pass
        access = "user_master"

    d   = load()
    cfg = d["config"]

    # ── MAIN MASTER: Full admin panel ────────────────────────────────────────
    if access == "main_master":
        bot.send_message(
            msg.chat.id,
            f"\U0001f44b <b>Welcome back, {name}!</b>\n"
            "\U0001f451 <b>Main Master</b> \u2014 Full Access\n\n"
            "\U0001f916 <b>Telegram Master Bot</b>\n\n"
            "Niche buttons se koi bhi feature choose karo:",
            reply_markup=main_inline_kb(uid),
        )
        if cfg.get("force_join_groups"):
            run_force_join_all(chat_id_report=None)
        return

    # ── USER MASTER: Beautiful Hindi+English Welcome ─────────────────────────
    photo_id   = cfg.get("welcome_photo_id", "")
    custom_cap = cfg.get("welcome_caption", "")

    if custom_cap:
        welcome_text = custom_cap.replace("{name}", name)
    else:
        welcome_text = (
            f"\U0001f389 <b>Swagat hai, {name}!</b> | <b>Welcome, {name}!</b>\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "\U0001f916 <b>Telegram Master Bot</b>\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f4cc <b>Aap kya kar sakte ho | What You Can Do:</b>\n\n"
            "\U0001f50d <b>Scrape</b> \u2014 Kisi bhi group ke members nikalo\n"
            "    <i>Extract members from any group</i>\n\n"
            "\U0001f4e2 <b>Broadcast</b> \u2014 Members ko message bhejo\n"
            "    <i>Send messages to scraped members</i>\n\n"
            "\U0001f465 <b>Group Add</b> \u2014 Members ko apne group mein add karo\n"
            "    <i>Add members directly to your group</i>\n\n"
            "\u2694\ufe0f <b>Reply Raid</b> \u2014 Kisi message pe reply spam\n"
            "    <i>Raid any message with replies</i>\n\n"
            "\U0001f3f7 <b>Tag All</b> \u2014 Group mein sabko tag karo\n"
            "    <i>Tag all members in a group</i>\n\n"
            "\U0001f3b5 <b>Music Bots</b> \u2014 Group mein music bots add karo\n"
            "    <i>Auto-add music bots to your group</i>\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "\u25b6\ufe0f <b>Shuru karne ke liye pehle account add karo!\n"
            "    To start, first add your Telegram account!</b>\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
        )

    # Force join URL buttons banao
    groups    = cfg.get("force_join_groups", [])
    join_kb   = InlineKeyboardMarkup(row_width=1)
    has_joins = False
    for g in groups:
        if g.startswith("@"):
            url = f"https://t.me/{g.lstrip('@')}"
        elif g.startswith("https://t.me/"):
            url = g
        else:
            continue
        join_kb.add(InlineKeyboardButton(f"\U0001f4e2 Join Group: {g}", url=url))
        has_joins = True
    if has_joins:
        join_kb.add(InlineKeyboardButton(
            "\u2705 Join kar liya \u2014 Start karo!", callback_data="after_join_start"))

    # ── Pehle Force Join prompt (agar groups set hain) ───────────────────────
    if has_joins:
        join_prompt = (
            "\U0001f517 <b>Pehle ye groups join karo!</b>\n"
            "<i>Please join these groups first:</i>\n\n"
            + "\n".join(f"\u2022 {g}" for g in groups)
            + "\n\nJoin karne ke baad \u2705 button dabao."
        )
        bot.send_message(msg.chat.id, join_prompt, reply_markup=join_kb, parse_mode="HTML")
        return

    # ── Koi force join nahi — seedha Welcome + Feature menu dikhao ───────────
    try:
        if photo_id:
            bot.send_photo(msg.chat.id, photo_id, caption=welcome_text, parse_mode="HTML")
        else:
            bot.send_message(msg.chat.id, welcome_text, parse_mode="HTML")
    except Exception:
        try:
            bot.send_message(msg.chat.id, welcome_text, parse_mode="HTML")
        except Exception:
            pass

    bot.send_message(msg.chat.id,
        "\U0001f3af <b>Feature choose karo | Choose a feature:</b>",
        reply_markup=main_inline_kb(uid), parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data == "after_join_start")
def cb_after_join_start(call):
    bot.answer_callback_query(call.id, "✅ Shukriya! Welcome aboard!")
    uid  = call.from_user.id
    name = call.from_user.first_name or "User"

    d          = load()
    cfg        = d["config"]
    photo_id   = cfg.get("welcome_photo_id", "")
    custom_cap = cfg.get("welcome_caption", "")

    if custom_cap:
        welcome_text = custom_cap.replace("{name}", name)
    else:
        welcome_text = (
            f"\U0001f389 <b>Swagat hai, {name}!</b> | <b>Welcome, {name}!</b>\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "\U0001f916 <b>Telegram Master Bot</b>\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            "\U0001f4cc <b>Aap kya kar sakte ho | What You Can Do:</b>\n\n"
            "\U0001f50d <b>Scrape</b> \u2014 Kisi bhi group ke members nikalo\n"
            "    <i>Extract members from any group</i>\n\n"
            "\U0001f4e2 <b>Broadcast</b> \u2014 Members ko message bhejo\n"
            "    <i>Send messages to scraped members</i>\n\n"
            "\U0001f465 <b>Group Add</b> \u2014 Members ko apne group mein add karo\n"
            "    <i>Add members directly to your group</i>\n\n"
            "\u2694\ufe0f <b>Reply Raid</b> \u2014 Kisi message pe reply spam\n"
            "    <i>Raid any message with replies</i>\n\n"
            "\U0001f3f7 <b>Tag All</b> \u2014 Group mein sabko tag karo\n"
            "    <i>Tag all members in a group</i>\n\n"
            "\U0001f3b5 <b>Music Bots</b> \u2014 Group mein music bots add karo\n"
            "    <i>Auto-add music bots to your group</i>\n\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "\u25b6\ufe0f <b>Shuru karne ke liye pehle account add karo!\n"
            "    To start, first add your Telegram account!</b>\n"
            "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
        )

    try:
        if photo_id:
            bot.send_photo(call.message.chat.id, photo_id, caption=welcome_text, parse_mode="HTML")
        else:
            bot.send_message(call.message.chat.id, welcome_text, parse_mode="HTML")
    except Exception:
        try:
            bot.send_message(call.message.chat.id, welcome_text, parse_mode="HTML")
        except Exception:
            pass

    bot.send_message(
        call.message.chat.id,
        "\U0001f3af <b>Feature choose karo | Choose a feature:</b>",
        reply_markup=main_inline_kb(uid),
        parse_mode="HTML"
    )

# ── /help ─────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["help"])
@bot.message_handler(func=lambda m: m.text == "❓ Help")
def cmd_help(msg):
    uid    = msg.from_user.id
    access = check_user_access(uid)

    # Common commands (everyone with access)
    common = (
        "📖 <b>Commands List</b>\n\n"
        "<b>📢 Broadcast:</b>\n"
        "/broadcast — dialog broadcast wizard\n"
        "/quicksend &lt;text&gt; — jaldi text bhejo\n\n"
        "<b>🎯 Scrape + Targeted:</b>\n"
        "/scrape — group members scrape karo\n"
        "/members — scraped members dekho (group-wise)\n"
        "/targeted — scraped members ko DM bhejo\n"
        "/groupadd — contact add → invite → DM fallback\n"
        "/pollscrape — poll/quiz voters scrape karo\n\n"
        "<b>🏷 Tag All:</b>\n"
        "/tagall — ek group ke sab members tag karo\n"
        "/tagallgroups — sabhi groups mein auto tag\n\n"
        "<b>📣 Promo:</b>\n"
        "/setpromo — promo text+link set karo\n"
        "/promo — sabhi groups mein promote karo\n\n"
        "<b>🤖 Auto-Reply:</b>\n"
        "/autoreply — AI auto-reply ON/OFF\n\n"
        "<b>⚔️ Reply Raid:</b>\n"
        "/replyraid — user pe reply raid chalu karo\n"
        "/stopraid  — raid band karo\n"
        "/raidlist  — active raids list\n\n"
        "<b>👤 Misc:</b>\n"
        "/cloneprofile — profile clone\n"
        "/autoclean — inactive groups chhodo\n\n"
        "<b>📱 Accounts:</b>\n"
        "/add — account add karo (OTP login)\n"
        "/accounts — accounts list\n\n"
        "<b>📊 Info:</b>\n"
        "/stats — statistics\n"
        "/status — system status\n"
        "/history — broadcast history\n"
        "/myid — apna Telegram ID\n"
    )

    main_master_cmds = (
        "\n<b>👑 Main Master Commands:</b>\n"
        "/addusermaster &lt;ID&gt; — User Master add karo\n"
        "/removeusermaster &lt;ID&gt; — User Master remove karo\n"
        "/listusermaster — User Masters dekho\n"
        "/setmainmaster &lt;ID&gt; — Main Master change karo\n\n"
        "<b>🔗 Force Join:</b>\n"
        "/setforcejoin @g1,@g2,@g3 — 3 groups set karo (bot start pe auto-join)\n"
        "/forcejoin — abhi force join karwao\n"
        "/viewforcejoin — current groups dekho\n\n"
        "<b>🎵 Music Bots:</b>\n"
        "/setmusicbots @bot1,@bot2 — scrape se pehle add hone wale bots\n\n"
        "<b>🚫 Blacklist:</b>\n"
        "/blacklist @group — group blacklist karo\n"
        "/unblacklist @group — blacklist se hatao\n"
        "/listblacklist — blacklist dekho\n\n"
        "<b>🔑 Admin:</b>\n"
        "/addadmin &lt;ID&gt; — admin add\n"
        "/removeadmin &lt;ID&gt; — admin remove\n"
        "/listadmins — admins list\n"
    )

    text = common
    if access == "main_master":
        text += main_master_cmds
    elif access == "user_master":
        text += "\n<b>🔑 Aapka Role: User Master</b>\n<i>Sirf apne accounts use kar sakte ho (max 5 DM/account)</i>"

    bot.send_message(msg.chat.id, text, reply_markup=main_kb())

# ── /myid ─────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["myid"])
def cmd_myid(msg):
    bot.reply_to(
        msg,
        f"👤 <b>User ID:</b> <code>{msg.from_user.id}</code>\n"
        f"Name: {msg.from_user.first_name or ''}\n"
        f"Username: @{msg.from_user.username or 'N/A'}\n\n"
        f"💬 <b>Chat ID:</b> <code>{msg.chat.id}</code>\n\n"
        f"<i>Admin add: /addadmin {msg.from_user.id}</i>",
    )

# ── /stats ────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["stats"])
@bot.message_handler(func=lambda m: m.text == "📊 Stats")
def cmd_stats(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Permission nahi hai."); return
    d    = load()
    hist = d["history"]
    ts1  = sum(x["totalSent"]   for x in hist)
    tf1  = sum(x["totalFailed"] for x in hist)
    tt1  = ts1 + tf1
    rate = round(ts1 / tt1 * 100) if tt1 else 0
    recent_txt = ""
    for r in hist[:3]:
        dt  = r["sentAt"][:16].replace("T", " ")
        mp  = r["message"][:25] + ("..." if len(r["message"]) > 25 else "")
        recent_txt += f"\n• {dt} ✅{r['totalSent']} ❌{r['totalFailed']}\n  <i>{mp}</i>"

    try:
        conn       = get_db()
        total_m    = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        not_bc     = conn.execute("SELECT COUNT(*) FROM members WHERE broadcast_count=0").fetchone()[0]
        total_sc   = conn.execute("SELECT COUNT(*) FROM scrape_jobs").fetchone()[0]
        total_bc   = conn.execute("SELECT COUNT(*) FROM broadcast_jobs").fetchone()[0]
        total_sent2= conn.execute("SELECT COALESCE(SUM(total_sent),0) FROM broadcast_jobs").fetchone()[0]
        conn.close()
        db_stats = (f"\n\n<b>🎯 Targeted DM Stats:</b>\n"
                    f"Scrape Jobs: <b>{total_sc}</b>\n"
                    f"Members: <b>{total_m}</b>  Not DM'd: <b>{not_bc}</b>\n"
                    f"DM Campaigns: <b>{total_bc}</b>  Total Sent: <b>{total_sent2}</b>")
    except Exception:
        db_stats = ""

    bot.send_message(
        msg.chat.id,
        f"📊 <b>Statistics</b>\n\n"
        f"<b>📢 Dialog Broadcasts:</b>\n"
        f"Total: <b>{len(hist)}</b>\n"
        f"Sent: <b>{ts1}</b>  Failed: <b>{tf1}</b>\n"
        f"Success Rate: <b>{rate}%</b>\n"
        f"<b>Recent:</b>{recent_txt if recent_txt else ' —'}"
        f"{db_stats}",
        reply_markup=main_kb(),
    )

# ── /status ───────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["status"])
def cmd_status(msg):
    uid    = msg.from_user.id
    access = check_user_access(uid)
    if not access:
        bot.reply_to(msg, "❌ Access denied!"); return

    d      = load()
    accs   = get_user_accounts(uid)
    active = sum(1 for a in accs if a.get("active") and a.get("verified"))

    # ── MAIN MASTER: Full system status ──────────────────────────────────────
    if access == "main_master":
        api_ok = "✅" if d["config"].get("api_id") and d["config"].get("api_hash") else "❌"
        bot_ok = "✅" if d["config"].get("bot_token") else "❌"
        bot.reply_to(
            msg,
            f"📊 <b>System Status</b>\n\n"
            f"Bot Token: {bot_ok}\n"
            f"API Credentials: {api_ok}\n"
            f"💾 MongoDB: {'✅ Connected' if _get_mongo_db() is not None else '⚠️ Not connected (MONGODB_URI set karo)'}\n\n"
            f"👤 Accounts: {len(accs)} (Active: {active})\n\n"
            f"📈 Dialog Broadcasts: {len(d['history'])}\n\n"
            f"🎯 Broadcast Modes:\n"
            f"  📢 All — Groups + DMs dono\n"
            f"  👥 Groups — Sirf groups/channels\n"
            f"  💬 DMs — Sirf personal chats",
        )
        return

    # ── USER MASTER / USER: Sirf apne account ka status ──────────────────────
    bot.reply_to(
        msg,
        f"📊 <b>Aapka Account Status</b>\n\n"
        f"👤 Aapke Accounts: {len(accs)} (Active: {active})\n\n"
        f"🎯 Broadcast Modes:\n"
        f"  📢 All — Groups + DMs dono\n"
        f"  👥 Groups — Sirf groups/channels\n"
        f"  💬 DMs — Sirf personal chats",
    )

# ── /setmongouri ──────────────────────────────────────────────────────────────
@bot.message_handler(commands=["setmongouri"])
def cmd_setmongouri(msg):
    """Admin MongoDB URI bot se set kar sake — Heroku dashboard pe jaane ki zaroorat nahi."""
    uid = msg.from_user.id
    if not is_admin(uid):
        bot.reply_to(msg, "❌ Sirf admin yeh command use kar sakta hai!"); return
    parts = msg.text.strip().split(None, 1)
    if len(parts) < 2 or not parts[1].strip().startswith("mongodb"):
        bot.reply_to(
            msg,
            "❌ <b>Usage:</b>\n"
            "<code>/setmongouri mongodb+srv://USER:PASS@cluster0.xxxx.mongodb.net/?retryWrites=true&amp;w=majority</code>\n\n"
            "📌 Free cluster banao: mongodb.com/atlas",
            parse_mode="HTML"
        ); return
    uri  = parts[1].strip()
    wait = bot.reply_to(msg, "⏳ MongoDB se connect ho raha hoon...")
    ok   = _mongo_set_uri(uri)
    if ok:
        # Existing accounts bhi MongoDB mein push karo
        def _bg():
            d = load()
            owners = d.get("account_owners", {})
            saved = 0
            for acc in d.get("accounts", []):
                acc_copy = dict(acc)
                acc_copy["owner_id"] = owners.get(acc_copy.get("phone",""), "")
                _mongo_save_account(acc_copy, owner_id=acc_copy["owner_id"])
                saved += 1
            if saved:
                _notify_admin(f"✅ {saved} existing accounts bhi MongoDB mein save ho gaye!")
        threading.Thread(target=_bg, daemon=True).start()
        bot.edit_message_text(
            "✅ <b>MongoDB Connected!</b>\n\n"
            "🔒 URI Heroku Config Vars mein permanently save ho gayi.\n"
            "🔄 Ab accounts bot restart ke baad bhi rahenge — dobara /add nahi karna!",
            msg.chat.id, wait.message_id, parse_mode="HTML"
        )
    else:
        bot.edit_message_text(
            "❌ <b>MongoDB Connection Failed!</b>\n\n"
            "Connection string check karo:\n"
            "• Username/password sahi hai?\n"
            "• Network Access mein 0.0.0.0/0 allow hai?\n"
            "• mongodb.com/atlas → Network Access → Add IP Address",
            msg.chat.id, wait.message_id, parse_mode="HTML"
        )

# ── /sessions — StringSession viewer (Sirf Main Master) ───────────────────────
@bot.message_handler(commands=["sessions"])
def cmd_sessions(msg):
    """
    /sessions        → sabhi accounts ki numbered list (bina session string)
    /sessions 2      → account #2 ki StringSession dikhao
    Sirf Main Master use kar sakta hai.
    """
    uid = msg.from_user.id
    if not is_main_master(uid):
        bot.reply_to(msg, "🔒 Yeh command sirf <b>Main Master</b> use kar sakta hai!", parse_mode="HTML")
        return
    d    = load()
    accs = d.get("accounts", [])
    if not accs:
        bot.reply_to(msg, "❌ Koi account add nahi hai.")
        return
    # Delete original command message for privacy
    try: bot.delete_message(msg.chat.id, msg.message_id)
    except Exception: pass
    # Check agar number diya gaya hai
    parts = msg.text.strip().split()
    if len(parts) >= 2 and parts[1].isdigit():
        # ── Specific account ki session string dikhao ──
        num = int(parts[1])
        if num < 1 or num > len(accs):
            bot.send_message(msg.chat.id,
                f"❌ Account #{num} nahi hai. Total accounts: {len(accs)}\n",
                f"Sahi number ke liye /sessions likhkar list dekho.")
            return
        acc      = accs[num - 1]
        phone    = acc.get("phone", "Unknown")
        name     = acc.get("name", "") or acc.get("first_name", "")
        verified = "✅" if acc.get("verified") else "❌"
        active   = "🟢" if acc.get("active") else "🔴"
        sess_str = acc.get("session_string", "")
        if not sess_str:
            bot.send_message(msg.chat.id,
                f"⚠️ Account #{num} ({phone}) ki session string nahi hai.\n"
                f"Dobara /add se login karo.")
            return
        mongo_ok = "💾 MongoDB saved" if _get_mongo_db() is not None else "⚠️ MongoDB nahi"
        header   = (
            f"🔑 <b>Account #{num} — StringSession</b>\n"
            f"📱 {phone}" + (f" — {name}" if name else "") + "\n"
            f"Verified: {verified} | Active: {active} | {mongo_ok}\n\n"
            f"Session String:"
        )
        bot.send_message(msg.chat.id, header, parse_mode="HTML")
        # Session string chunks mein bhejo (4000 chars max per message)
        chunk_size = 4000
        for i in range(0, len(sess_str), chunk_size):
            bot.send_message(msg.chat.id,
                f"<code>{sess_str[i:i+chunk_size]}</code>",
                parse_mode="HTML")
        bot.send_message(msg.chat.id,
            "⚠️ <b>Yeh message delete kar dena!</b> Session string private hai.",
            parse_mode="HTML")
    else:
        # ── Saare accounts ki numbered list dikhao (bina session string) ──
        lines = ["📋 <b>Session Accounts — Owner Telegram ID ke saath:</b>\n"]
        for i, acc in enumerate(accs, 1):
            phone    = acc.get("phone", "Unknown")
            name     = acc.get("name", "") or acc.get("first_name", "") or acc.get("label", "")
            verified = "✅" if acc.get("verified") else "❌"
            active   = "🟢" if acc.get("active") else "🔴"
            has_sess = "🔑" if acc.get("session_string") else "❌"
            oid      = owners.get(phone, "") or acc.get("owner_id", "") or "Unknown"
            oname    = acc.get("owner_name", "")
            added_at = acc.get("added_at", "")
            owner_disp = str(oid) + (f" ({oname})" if oname else "")
            line = (
                f"{i}. {has_sess} <code>{phone}</code>"
                + (f" — {name}" if name else "")
                + f"\n    👤 Added by: <code>{owner_disp}</code> {verified}{active}"
                + (f"\n    🕐 {added_at}" if added_at else "")
            )
            lines.append(line)
        lines.append(
            "\n💡 <b>Usage:</b>"
            "\n• <code>/sessions 2</code> — account #2 ki string"
            "\n• <code>/sessions 987654321</code> — is Telegram ID ke saare accounts"
        )
        bot.send_message(msg.chat.id, "\n".join(lines), parse_mode="HTML")

# ── /accounts ─────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["accounts"])
@bot.message_handler(func=lambda m: m.text == "📱 Accounts")
def cmd_accounts(msg):
    uid    = msg.from_user.id
    access = check_user_access(uid)
    if not access:
        bot.reply_to(msg, "❌ Access denied!"); return
    d       = load()
    changed = sync_account_status(d)
    if changed:
        save(d)

    # Main Master → sab accounts; User Master → sirf apne
    if access == "main_master":
        accs = d["accounts"]
        header = "👑 <b>All Accounts (Main Master View)</b>"
    else:
        # User Master ke owned accounts
        owners       = d.get("account_owners", {})
        owned_phones = {p for p, owner in owners.items() if str(owner) == str(uid)}
        accs         = [a for a in d["accounts"] if a["phone"] in owned_phones]
        header       = "🔑 <b>Aapke Accounts (User Master)</b>"

    if not accs:
        bot.send_message(msg.chat.id,
            "📱 Koi account nahi hai.\n/add se account add karo.", reply_markup=main_kb())
        return

    active_count = sum(1 for a in accs if a.get("active") and a.get("verified"))
    lines = [f"{header}\n({active_count} active / {len(accs)} total)\n"]
    for i, a in enumerate(accs, 1):
        ok_s   = a.get("active") and a.get("verified")
        icon   = "🟢" if ok_s else "🔴"
        status = "Active" if ok_s else "No session"
        name   = a.get("label") or a.get("name") or a["phone"]
        lines.append(f"{icon} {i}. <b>{name}</b>  <i>[{status}]</i>\n    <code>{a['phone']}</code>")
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("➕ Add Account", callback_data="add_account"))
    if access == "main_master":
        mk.add(InlineKeyboardButton("🗑 Delete Account", callback_data="del_account_list"))
    bot.send_message(msg.chat.id, "\n".join(lines), reply_markup=mk)

@bot.message_handler(commands=["add"])
def cmd_add(msg):
    uid    = msg.from_user.id
    access = check_user_access(uid)
    if not access:
        bot.reply_to(msg, "❌ Access denied!"); return
    set_state(uid, "add_phone")
    bot.send_message(
        msg.chat.id,
        "📱 <b>Account Add karo</b>\n\n"
        "Phone number bhejo (international format):\n"
        "<code>+919876543210</code>",
        reply_markup=cancel_kb(),
    )

@bot.callback_query_handler(func=lambda c: c.data == "add_account")
@user_access_cb
def cb_add_account(call):
    bot.answer_callback_query(call.id)
    set_state(call.from_user.id, "add_phone")
    bot.send_message(
        call.message.chat.id,
        "📱 <b>Account Add karo</b>\n\n"
        "Phone number bhejo (international format):\n<code>+919876543210</code>",
        reply_markup=cancel_kb(),
    )

@bot.callback_query_handler(func=lambda c: c.data == "del_account_list")
@admin_only_cb
def cb_del_acc_list(call):
    bot.answer_callback_query(call.id)
    d = load()
    if not d["accounts"]:
        bot.send_message(call.message.chat.id, "Koi account nahi hai.")
        return
    mk = InlineKeyboardMarkup()
    for i, a in enumerate(d["accounts"]):
        label = a.get("label") or a["phone"]
        mk.add(InlineKeyboardButton(f"🗑 {a['phone']} — {label}", callback_data=f"del_acc_{i}"))
    mk.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_cb"))
    bot.send_message(call.message.chat.id, "Kaun sa account delete karna hai?", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_acc_"))
@admin_only_cb
def cb_del_acc(call):
    bot.answer_callback_query(call.id)
    idx = int(call.data.split("_")[-1])
    d   = load()
    if idx >= len(d["accounts"]):
        bot.send_message(call.message.chat.id, "Account nahi mila.")
        return
    acc  = d["accounts"].pop(idx)
    safe = acc["phone"].replace("+", "").replace(" ", "")
    for ext in [".session", ".session-journal"]:
        f = os.path.join(SESSION_DIR, safe + ext)
        if os.path.exists(f):
            os.remove(f)
    save(d)
    bot.send_message(call.message.chat.id,
        f"✅ Account delete ho gaya: <code>{acc['phone']}</code>", reply_markup=main_kb())

# ── /targets ──────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["targets"])
def cmd_targets(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    d    = load()
    tgts = d["targets"]
    if not tgts:
        bot.reply_to(msg, "❌ Koi target nahi!\nUse: /addtarget &lt;id&gt; [label]"); return
    lines = ["🎯 <b>Targets:</b>\n"]
    for t in tgts:
        icon = "👥" if t["type"] == "group" else "💬"
        lines.append(f"{icon} <b>{t.get('label') or t['value']}</b>\n    ID: <code>{t['value']}</code>")
    bot.reply_to(msg, "\n".join(lines))

@bot.message_handler(commands=["addtarget"])
def cmd_addtarget(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    parts = msg.text.split(maxsplit=2)
    if len(parts) < 2:
        bot.reply_to(msg, "Usage: /addtarget &lt;chat_id&gt; [label]"); return
    chat_id = parts[1].strip()
    label   = parts[2].strip() if len(parts) > 2 else chat_id
    d       = load()
    for t in d["targets"]:
        if t["value"] == chat_id:
            bot.reply_to(msg, f"⚠️ Pehle se hai: {t.get('label') or chat_id}"); return
    t_type = "group" if chat_id.startswith("-") else "dm"
    d["targets"].append({"id": gen_id(), "type": t_type, "value": chat_id,
                          "label": label, "addedAt": datetime.now().isoformat()})
    save(d)
    icon = "👥" if t_type == "group" else "💬"
    bot.reply_to(msg, f"✅ Target add!\n{icon} <b>{label}</b>\n<code>{chat_id}</code>")

@bot.message_handler(commands=["deltarget"])
def cmd_deltarget(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(msg, "Usage: /deltarget &lt;id&gt;"); return
    tid = parts[1].strip()
    d   = load()
    before = len(d["targets"])
    d["targets"] = [t for t in d["targets"] if t["id"] != tid and t["value"] != tid]
    if len(d["targets"]) < before:
        save(d); bot.reply_to(msg, "✅ Target delete ho gaya!")
    else:
        bot.reply_to(msg, f"❌ Nahi mila: {tid}")

# ── /scrape ───────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["scrape"])
@bot.message_handler(func=lambda m: m.text == "🔍 Scrape")
def cmd_scrape(msg):
    uid    = msg.from_user.id
    access = check_user_access(uid)
    if not access:
        bot.reply_to(msg, "❌ Access denied!"); return
    # User ke available accounts
    accs = get_user_accounts(uid)
    if not accs:
        bot.send_message(msg.chat.id,
            "❌ Koi active account nahi! Pehle /add se account add karo.", reply_markup=main_kb())
        return
    mk = InlineKeyboardMarkup()
    for a in accs:
        label = a.get("label") or a["phone"]
        mk.add(InlineKeyboardButton(f"📱 {a['phone']} — {label}",
                                    callback_data=f"scrape_acc_{a['phone']}"))
    mk.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_cb"))
    bot.send_message(msg.chat.id, "🔍 <b>Scrape ke liye account choose karo:</b>", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("scrape_acc_"))
@user_access_cb
def cb_scrape_acc(call):
    bot.answer_callback_query(call.id)
    phone = call.data.replace("scrape_acc_", "")
    set_state(call.from_user.id, "scrape_group", {"phone": phone})
    bot.send_message(
        call.message.chat.id,
        f"📱 Account: <code>{phone}</code>\n\n"
        "🔍 Group link ya username bhejo:\n"
        "<code>@groupname</code>\n"
        "<code>https://t.me/groupname</code>\n"
        "<code>-1001234567890</code> (group ID)",
        reply_markup=cancel_kb(),
    )

# ── /pollscrape (Poll/Quiz voters scrape) ────────────────────────────────────
@bot.message_handler(commands=["pollscrape"])
@bot.message_handler(func=lambda m: m.text == "📊 Poll Scrape")
def cmd_pollscrape(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    accs = active_accounts()
    if not accs:
        bot.send_message(msg.chat.id,
            "❌ Koi active account nahi! Pehle /add karo.", reply_markup=main_kb())
        return
    mk = InlineKeyboardMarkup()
    for a in accs:
        label = a.get("label") or a["phone"]
        mk.add(InlineKeyboardButton(
            f"📱 {a['phone']} — {label}",
            callback_data=f"ps_acc_{a['phone']}"
        ))
    mk.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_cb"))
    bot.send_message(
        msg.chat.id,
        "📊 <b>Poll / Quiz Voters Scrape</b>\n\n"
        "Kaise kaam karta hai:\n"
        "1️⃣ Account choose karo\n"
        "2️⃣ Group/Channel link bhejo\n"
        "3️⃣ Bot poori history mein se <b>saari polls/quizzes</b> dhundh ke list dikhayega\n"
        "4️⃣ Ek poll choose karo\n"
        "5️⃣ Usके saare voters scrape ho jayenge\n\n"
        "📱 <b>Account choose karo:</b>",
        reply_markup=mk,
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("ps_acc_"))
@admin_only_cb
def cb_ps_acc(call):
    bot.answer_callback_query(call.id)
    phone = call.data.replace("ps_acc_", "")
    set_state(call.from_user.id, "ps_group", {"phone": phone})
    bot.send_message(
        call.message.chat.id,
        f"📱 Account: <code>{phone}</code>\n\n"
        "🔗 <b>Group/Channel link ya username bhejo:</b>\n"
        "<code>@groupname</code>\n"
        "<code>https://t.me/groupname</code>\n"
        "<code>-1001234567890</code> (group ID)",
        reply_markup=cancel_kb(),
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("ps_poll_"))
@admin_only_cb
def cb_ps_poll(call):
    bot.answer_callback_query(call.id)
    uid  = call.from_user.id
    st   = get_state(uid)
    if not st:
        bot.send_message(call.message.chat.id, "❌ Session expire. /pollscrape dobara karo.")
        return
    # data: ps_poll_MSGID
    parts  = call.data.split("_")
    msg_id = int(parts[-1])
    data   = st["data"]
    data["message_id"] = msg_id

    phone  = data["phone"]
    group  = data["group"]
    # polls_map se sahi label lo (msg_id → question)
    label  = data.get("polls_map", {}).get(str(msg_id), f"Poll #{msg_id}")

    clear_state(uid)
    chat_id = call.message.chat.id
    bot.send_message(
        chat_id,
        f"📊 Poll selected: <b>{label}</b>\n\n"
        "⏳ Voters scrape ho raha hai (sabhi options)...\n"
        "Thoda wait karo, result aayega.",
        reply_markup=main_kb(),
    )

    def run_poll_scrape():
        d2   = load()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        conn = get_db()
        # scrape_jobs mein entry daalo
        job_label = f"[POLL] {group} — {label[:40]}"
        cur  = conn.execute(
            "INSERT INTO scrape_jobs (group_target,account_phone,status) VALUES (?,?,?)",
            (job_label, phone, "running"),
        )
        scrape_id = cur.lastrowid
        conn.commit()
        conn.close()

        total, err = loop.run_until_complete(
            scrape_poll_voters(
                phone, d2["config"]["api_id"], d2["config"]["api_hash"],
                group, msg_id, scrape_id
            )
        )
        loop.close()

        if err:
            bot.send_message(chat_id,
                f"❌ Poll scrape fail!\n<code>{err}</code>", reply_markup=main_kb())
        else:
            bot.send_message(chat_id,
                f"✅ <b>Poll Voters Scrape Complete!</b>\n\n"
                f"📊 Poll: <b>{label}</b>\n"
                f"🔗 Group: <code>{group}</code>\n"
                f"👥 Voters scraped: <b>{total}</b>\n"
                f"🆔 Scrape ID: <b>{scrape_id}</b>\n\n"
                "Ab /targeted se DM bhej sakte ho!\n"
                "Ya /groupadd se contact add + invite link campaign karo!",
                reply_markup=main_kb())

    threading.Thread(target=run_poll_scrape, daemon=True).start()

# ── /members ──────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["members"])
@bot.message_handler(func=lambda m: m.text == "👥 Members")
def cmd_members(msg):
    uid    = msg.from_user.id
    access = check_user_access(uid)
    if not access:
        bot.reply_to(msg, "❌ Access denied!"); return
    jobs = get_user_scrape_jobs(uid, limit=15)
    if not jobs:
        bot.send_message(msg.chat.id, "❌ Koi scrape nahi hua abhi tak. Pehle /scrape karo.",
                         reply_markup=main_kb())
        return
    mk = InlineKeyboardMarkup()
    for j in jobs:
        owner_note = f" [UID:{j['owner_id']}]" if is_main_master(uid) and j["owner_id"] else ""
        mk.add(InlineKeyboardButton(
            f"[{j['id']}] {j['group_target']} — {j['total_scraped']} members{owner_note}",
            callback_data=f"members_job_{j['id']}"
        ))
    bot.send_message(msg.chat.id, "👥 <b>Kaun sa scrape job dekhen?</b>", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("members_job_"))
@user_access_cb
def cb_members_job(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id
    jid = int(call.data.split("_")[-1])
    conn = get_db()
    # Ownership validation: User Master sirf apni scrape job dekh sakta hai
    job_row = conn.execute("SELECT owner_id FROM scrape_jobs WHERE id=?", (jid,)).fetchone()
    if job_row and job_row["owner_id"] and not is_main_master(uid):
        if str(job_row["owner_id"]) != str(uid):
            conn.close()
            bot.send_message(call.message.chat.id, "❌ Ye scrape job aapki nahi hai!")
            return
    total  = conn.execute("SELECT COUNT(*) FROM members WHERE scrape_id=?", (jid,)).fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM members WHERE scrape_id=? AND is_active=1", (jid,)).fetchone()[0]
    deleted= conn.execute("SELECT COUNT(*) FROM members WHERE scrape_id=? AND is_deleted=1", (jid,)).fetchone()[0]
    not_bc = conn.execute("SELECT COUNT(*) FROM members WHERE scrape_id=? AND broadcast_count=0", (jid,)).fetchone()[0]
    rows   = conn.execute("SELECT * FROM members WHERE scrape_id=? ORDER BY id LIMIT 20", (jid,)).fetchall()
    conn.close()
    text = (f"👥 <b>Members (Scrape ID: {jid})</b>\n\n"
            f"Total: <b>{total}</b>\n"
            f"Active: <b>{active}</b>  Deleted: <b>{deleted}</b>\n"
            f"Not broadcast yet: <b>{not_bc}</b>\n\n"
            "<b>Sample (top 20):</b>\n")
    for m in rows:
        uname = ("@" + m["username"]) if m["username"] else (m["first_name"] or m["telegram_id"])
        flags = "🟢" if m["is_active"] else ("🔴" if m["is_deleted"] else "⚫")
        text += f"{flags} {uname}\n"
    bot.send_message(call.message.chat.id, text, reply_markup=main_kb())

# ── /targeted (scraped members ko DM) ────────────────────────────────────────
@bot.message_handler(commands=["targeted"])
@bot.message_handler(func=lambda m: m.text == "🎯 Targeted DM")
def cmd_targeted(msg):
    uid    = msg.from_user.id
    access = check_user_access(uid)
    if not access:
        bot.reply_to(msg, "❌ Access denied!"); return
    jobs = get_user_scrape_jobs(uid, limit=15)
    if not jobs:
        bot.send_message(msg.chat.id,
            "❌ Koi scrape nahi hua! Pehle /scrape karo.", reply_markup=main_kb())
        return
    accs = get_user_accounts(uid)
    if not accs:
        bot.send_message(msg.chat.id,
            "❌ Koi active account nahi! Pehle /add karo.", reply_markup=main_kb())
        return
    mk = InlineKeyboardMarkup()
    for j in jobs:
        mk.add(InlineKeyboardButton(
            f"[{j['id']}] {j['group_target']} ({j['total_scraped']} members)",
            callback_data=f"bc_job_{j['id']}"
        ))
    mk.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_cb"))
    limit_note = "\n<i>⚠️ User Master: max 5 DM per account</i>" if access == "user_master" else ""
    bot.send_message(msg.chat.id,
        f"🎯 <b>Targeted DM ke liye scrape job choose karo:</b>{limit_note}", reply_markup=mk)

# ── /exportcsv ────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["exportcsv"])
@bot.message_handler(func=lambda m: m.text == "📤 Export CSV")
def cmd_exportcsv(msg):
    uid = msg.from_user.id
    if not check_user_access(uid):
        bot.reply_to(msg, "❌ Access denied!"); return
    jobs = get_user_scrape_jobs(uid, limit=15)
    if not jobs:
        bot.send_message(msg.chat.id,
            "❌ Koi scrape job nahi mili! Pehle /scrape karo.", reply_markup=main_kb())
        return
    mk = InlineKeyboardMarkup()
    for j in jobs:
        mk.add(InlineKeyboardButton(
            f"[{j['id']}] {j['group_target']}  ·  {j['total_scraped'] or 0} members",
            callback_data=f"csv_job_{j['id']}"
        ))
    mk.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_cb"))
    bot.send_message(msg.chat.id,
        "📤 <b>CSV Export</b>\n\nKaun si scrape job export karni hai?",
        reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("csv_job_"))
@user_access_cb
def cb_csv_job(call):
    import csv, io, os, tempfile
    bot.answer_callback_query(call.id, "⏳ CSV bana raha hoon...")
    uid = call.from_user.id
    jid = int(call.data.split("_")[-1])

    conn = get_db()
    job  = conn.execute("SELECT * FROM scrape_jobs WHERE id=?", (jid,)).fetchone()
    if job and job["owner_id"] and not is_main_master(uid):
        if str(job["owner_id"]) != str(uid):
            conn.close()
            bot.send_message(call.message.chat.id, "❌ Ye scrape job aapki nahi hai!")
            return
    rows = conn.execute(
        """SELECT telegram_id, username, first_name, last_name,
                  is_active, last_seen
           FROM members WHERE scrape_id=? ORDER BY id""",
        (jid,)
    ).fetchall()
    conn.close()

    if not rows:
        bot.send_message(call.message.chat.id,
            "❌ Is job mein koi member nahi mila.", reply_markup=main_kb())
        return

    # CSV banao in-memory
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["#", "telegram_id", "username", "first_name", "last_name",
                     "is_active", "last_seen"])
    for i, r in enumerate(rows, 1):
        writer.writerow([
            i,
            r["telegram_id"],
            r["username"] or "",
            r["first_name"] or "",
            r["last_name"] or "",
            "Yes" if r["is_active"] else "No",
            r["last_seen"] or "Unknown",
        ])

    csv_bytes = buf.getvalue().encode("utf-8")
    group_slug = (job["group_target"] if job else f"job{jid}") \
                 .lstrip("@").replace("/", "_").replace(" ", "_")
    filename = f"scraped_{group_slug}_{jid}.csv"

    # Tempfile mein save karke send karo
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb")
    tmp.write(csv_bytes)
    tmp.flush()
    tmp.close()

    caption = (
        f"📤 <b>Export Ready!</b>\n\n"
        f"🔗 Group: <code>{job['group_target'] if job else jid}</code>\n"
        f"👥 Total members: <b>{len(rows)}</b>\n"
        f"🆔 Scrape ID: <b>{jid}</b>"
    )
    try:
        with open(tmp.name, "rb") as f:
            bot.send_document(call.message.chat.id, f,
                              caption=caption, visible_file_name=filename)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ CSV send nahi hua: {e}")
    finally:
        try: os.remove(tmp.name)
        except Exception: pass

# ── /checkaccount (Spam/Flood limit checker + SpamBot appeal) ─────────────────
@bot.message_handler(commands=["checkaccount"])
@bot.message_handler(func=lambda m: m.text == "🔎 Check Limit")
def cmd_checkaccount(msg):
    uid = msg.from_user.id
    if not check_user_access(uid):
        bot.reply_to(msg, "❌ Access denied!"); return
    accs = get_user_accounts(uid)
    if not accs:
        bot.send_message(msg.chat.id,
            "❌ Koi active account nahi! Pehle /add karo.", reply_markup=main_kb())
        return
    mk = InlineKeyboardMarkup()
    for a in accs:
        label = a.get("label") or a["phone"]
        mk.add(InlineKeyboardButton(
            f"📱 {a['phone']} — {label}",
            callback_data=f"chkac_{a['phone']}"
        ))
    mk.add(InlineKeyboardButton("🔍 Saare Accounts Check Karo", callback_data="chkac_ALL"))
    mk.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_cb"))
    bot.send_message(
        msg.chat.id,
        "🔎 <b>Account Limit Checker</b>\n\n"
        "Kaunsa account check karna hai?\n\n"
        "Bot <b>@SpamBot</b> se check karega:\n"
        "✅ Limit nahi hai\n"
        "⚠️ Spam limit lagi hai + kitne time ke liye\n"
        "🆘 Agar limit hai to <b>Auto Appeal</b> bhi kar sakta hai",
        reply_markup=mk,
    )

async def _check_one_account_spambot(phone, api_id, api_hash):
    """
    @SpamBot se account ka spam/limit status check karo.
    Returns: dict {status, message, can_appeal, raw}
    """
    import re
    result = {"phone": phone, "status": "unknown", "message": "", "can_appeal": False, "raw": ""}
    client = get_client(phone, api_id, api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            result["status"]  = "unauthorized"
            result["message"] = "Session expire ho gaya — dobara /add karo"
            return result

        # @SpamBot ko /start bhejo
        await client.send_message("@SpamBot", "/start")
        await asyncio.sleep(3)

        # Last message @SpamBot ka lo
        msgs = await client.get_messages("@SpamBot", limit=3)
        spambot_reply = ""
        for m in msgs:
            txt = getattr(m, "message", "") or ""
            if txt:
                spambot_reply = txt
                break

        result["raw"] = spambot_reply[:500]

        low = spambot_reply.lower()
        if not spambot_reply:
            result["status"]  = "no_response"
            result["message"] = "SpamBot ne jawab nahi diya"
        elif any(w in low for w in ["good news", "no limits", "not limited", "nahi", "free"]):
            result["status"]  = "clean"
            result["message"] = "✅ Koi limit nahi hai — Account bilkul theek hai!"
        elif any(w in low for w in ["unfortunately", "limit", "spam", "restricted", "banned", "block"]):
            result["status"]  = "limited"
            # Time extract karo agar ho
            time_match = re.search(
                r'(\d+)\s*(hour|day|week|minute|hr|din|ghanta)', low, re.IGNORECASE
            )
            if time_match:
                result["message"] = (
                    f"⚠️ SPAM LIMIT LAGI HAI!\n"
                    f"⏳ Duration: <b>{time_match.group(1)} {time_match.group(2)}</b>"
                )
            else:
                # "until" ya date dhundho
                until_match = re.search(r'until\s+([^\n\.]+)', spambot_reply, re.IGNORECASE)
                if until_match:
                    result["message"] = (
                        f"⚠️ SPAM LIMIT LAGI HAI!\n"
                        f"⏳ Until: <b>{until_match.group(1).strip()}</b>"
                    )
                else:
                    result["message"] = "⚠️ SPAM LIMIT LAGI HAI! (duration unknown)"
            result["can_appeal"] = True
        else:
            result["status"]  = "clean"
            result["message"] = "✅ Account theek lagta hai"

    except Exception as e:
        result["status"]  = "error"
        result["message"] = f"❌ Error: {str(e)[:120]}"
    finally:
        try: await client.disconnect()
        except Exception: pass

    return result

@bot.callback_query_handler(func=lambda c: c.data.startswith("chkac_"))
@user_access_cb
def cb_chkac(call):
    bot.answer_callback_query(call.id, "⏳ Check ho raha hai...")
    uid = call.from_user.id
    target = call.data.replace("chkac_", "")
    chat_id = call.message.chat.id

    d2   = load()
    accs = get_user_accounts(uid)
    if target == "ALL":
        check_list = accs
        bot.send_message(chat_id,
            f"🔍 Saare <b>{len(check_list)}</b> accounts check ho rahe hain...\n"
            "⏳ Thoda wait karo (SpamBot se reply aane mein 3-5 sec lagta hai har account ke liye)...")
    else:
        check_list = [a for a in accs if a["phone"] == target]
        if not check_list:
            bot.send_message(chat_id, "❌ Account nahi mila.", reply_markup=main_kb())
            return
        bot.send_message(chat_id,
            f"🔍 <code>{target}</code> check ho raha hai...\n⏳ @SpamBot se reply ka wait...")

    def run_check():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        cfg  = d2["config"]
        results = loop.run_until_complete(asyncio.gather(*[
            _check_one_account_spambot(a["phone"], cfg["api_id"], cfg["api_hash"])
            for a in check_list
        ]))
        loop.close()

        lines = ["🔎 <b>Account Limit Check Results</b>\n"]
        limited_phones = []
        for r in results:
            icon = {"clean": "✅", "limited": "⚠️", "unauthorized": "🔒",
                    "error": "❌", "no_response": "❓"}.get(r["status"], "❓")
            lines.append(f"{icon} <code>{r['phone']}</code>")
            lines.append(f"   {r['message']}")
            if r.get("raw"):
                lines.append(f"   📋 SpamBot: <i>{r['raw'][:120]}</i>")
            lines.append("")
            if r["status"] == "limited":
                limited_phones.append(r["phone"])

        text = "\n".join(lines)

        mk = InlineKeyboardMarkup()
        if limited_phones:
            for ph in limited_phones:
                mk.add(InlineKeyboardButton(
                    f"🆘 {ph} — Auto Appeal Bhejo",
                    callback_data=f"appeal_{ph}"
                ))
        mk.add(InlineKeyboardButton("🔄 Dobara Check Karo",
            callback_data=f"chkac_{'ALL' if target == 'ALL' else target}"))
        mk.add(InlineKeyboardButton("❌ Close", callback_data="cancel_cb"))

        bot.send_message(chat_id, text, reply_markup=mk)

    threading.Thread(target=run_check, daemon=True).start()

@bot.callback_query_handler(func=lambda c: c.data.startswith("appeal_"))
@admin_only_cb
def cb_appeal(call):
    bot.answer_callback_query(call.id, "🆘 Appeal bhej raha hoon...")
    phone   = call.data.replace("appeal_", "")
    chat_id = call.message.chat.id
    d2      = load()
    cfg     = d2["config"]

    bot.send_message(chat_id,
        f"🆘 <code>{phone}</code> ke liye @SpamBot mein <b>appeal</b> bhej raha hoon...\n"
        "⏳ Ek minute...")

    async def do_appeal():
        result = {"phone": phone, "done": False, "reply": "", "error": ""}
        client = get_client(phone, cfg["api_id"], cfg["api_hash"])
        try:
            await client.connect()
            if not await client.is_user_authorized():
                result["error"] = "Session expire — /add se dobara login karo"
                return result

            # SpamBot ko /start bhejo — usually shows appeal button
            await client.send_message("@SpamBot", "/start")
            await asyncio.sleep(2)

            # Messages + buttons check karo
            msgs = await client.get_messages("@SpamBot", limit=5)
            appeal_btn_clicked = False

            for m in msgs:
                # Inline button "Appeal" dhundho
                if hasattr(m, "reply_markup") and m.reply_markup:
                    rows = getattr(m.reply_markup, "rows", [])
                    for row in rows:
                        for btn in getattr(row, "buttons", []):
                            btn_text = getattr(btn, "text", "").lower()
                            if "appeal" in btn_text or "unban" in btn_text or "lift" in btn_text:
                                try:
                                    await m.click(btn_text)
                                    appeal_btn_clicked = True
                                    result["done"] = True
                                except Exception:
                                    pass

            # Agar button nahi mila — manual appeal message bhejo
            if not appeal_btn_clicked:
                await client.send_message(
                    "@SpamBot",
                    "I believe my account was limited by mistake. "
                    "I have not been sending spam. Please review my account and remove the restriction."
                )
                await asyncio.sleep(2)
                reply_msgs = await client.get_messages("@SpamBot", limit=2)
                if reply_msgs:
                    result["reply"] = getattr(reply_msgs[0], "message", "")[:300]
                result["done"] = True

        except Exception as e:
            result["error"] = str(e)[:200]
        finally:
            try: await client.disconnect()
            except Exception: pass
        return result

    def run_appeal():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        r    = loop.run_until_complete(do_appeal())
        loop.close()

        if r.get("error"):
            bot.send_message(chat_id, f"❌ Appeal fail: {r['error']}", reply_markup=main_kb())
        else:
            reply_txt = f"\n\n📋 SpamBot reply:\n<i>{r['reply']}</i>" if r.get("reply") else ""
            bot.send_message(chat_id,
                f"✅ <b>Appeal bhej diya!</b>\n\n"
                f"📱 Account: <code>{phone}</code>\n"
                f"📨 @SpamBot ko appeal message send ho gaya{reply_txt}\n\n"
                "⏳ Telegram 24-48 ghante mein review karta hai.\n"
                "Baad mein /checkaccount se status check karo.",
                reply_markup=main_kb(),
            )

    threading.Thread(target=run_appeal, daemon=True).start()

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc_job_"))
@user_access_cb
def cb_bc_job(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id
    jid = int(call.data.split("_")[-1])
    # Ownership validation
    conn    = get_db()
    job_row = conn.execute("SELECT owner_id FROM scrape_jobs WHERE id=?", (jid,)).fetchone()
    conn.close()
    if job_row and job_row["owner_id"] and not is_main_master(uid):
        if str(job_row["owner_id"]) != str(uid):
            bot.send_message(call.message.chat.id, "❌ Ye scrape job aapki nahi hai!")
            return
    set_state(uid, "bc_message", {"scrape_id": jid})
    bot.send_message(
        call.message.chat.id,
        f"✅ Scrape ID: <b>{jid}</b> select ho gaya.\n\n"
        "✍ <b>Broadcast message bhejo:</b>\n"
        "(Text, photo, ya video bhej sakte ho)\n\n"
        "📌 Sirf text ke liye message type karo.\n"
        "📸 Photo ke liye photo attach karo.",
        reply_markup=cancel_kb(),
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc_perAcc_"))
@user_access_cb
def cb_bc_per_acc(call):
    bot.answer_callback_query(call.id)
    n   = int(call.data.split("_")[-1])
    uid = call.from_user.id
    st  = get_state(uid)
    st["data"]["members_per_account"] = n
    conn     = get_db()
    jid      = st["data"]["scrape_id"]
    conn_row = conn.execute("SELECT * FROM scrape_jobs WHERE id=?", (jid,)).fetchone()
    conn.close()
    # User ke accounts use karo (not all)
    accs          = get_user_accounts(uid)
    effective_n   = min(n, 5) if not is_main_master(uid) else n
    text = (f"📋 <b>Targeted DM Summary:</b>\n\n"
            f"Group: <b>{conn_row['group_target'] if conn_row else jid}</b>\n"
            f"Media: <b>{st['data'].get('media_type') or 'Sirf text'}</b>\n"
            f"Accounts: <b>{len(accs)}</b>\n"
            f"Members per account: <b>{effective_n}</b>"
            + (" <i>(User Master limit)</i>" if effective_n < n else "") + "\n\n"
            f"Message preview:\n<i>{st['data']['message'][:200]}</i>\n\n"
            "Targeted DM shuru karein?")
    st["data"]["members_per_account"] = effective_n
    mk = InlineKeyboardMarkup()
    mk.add(
        InlineKeyboardButton("✅ Haan, Shuru Karo!", callback_data="bc_confirm"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_cb"),
    )
    bot.send_message(call.message.chat.id, text, reply_markup=mk)
    set_state(uid, "bc_confirm", st["data"])

@bot.callback_query_handler(func=lambda c: c.data == "bc_confirm")
@user_access_cb
def cb_bc_confirm(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id
    st  = get_state(uid)
    if not st or st.get("step") != "bc_confirm":
        bot.send_message(call.message.chat.id, "❌ Session expire ho gaya. /targeted se dobara karo.")
        return
    clear_state(uid)
    data_bc              = st["data"]
    data_bc["owner_uid"] = uid   # Owner track karo for account filtering
    chat_id              = call.message.chat.id
    bot.send_message(chat_id, "🚀 Targeted DM shuru ho gaya! Progress yahan aayega...",
                     reply_markup=main_kb())

    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(do_targeted_broadcast(chat_id, data_bc, bot))
        loop.close()

    threading.Thread(target=run_in_thread, daemon=True).start()

# ── /groupadd (Add as Contact → Invite Link → DM fallback) ───────────────────
@bot.message_handler(commands=["groupadd"])
@bot.message_handler(func=lambda m: m.text == "👥 Group Add")
def cmd_groupadd(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    conn = get_db()
    jobs = conn.execute(
        "SELECT * FROM scrape_jobs WHERE status='done' ORDER BY id DESC LIMIT 10"
    ).fetchall()
    conn.close()
    if not jobs:
        bot.send_message(msg.chat.id,
            "❌ Koi scrape nahi hua! Pehle /scrape karo.", reply_markup=main_kb())
        return
    accs = active_accounts(load())
    if not accs:
        bot.send_message(msg.chat.id,
            "❌ Koi active account nahi! Pehle /add karo.", reply_markup=main_kb())
        return
    mk = InlineKeyboardMarkup()
    for j in jobs:
        mk.add(InlineKeyboardButton(
            f"[{j['id']}] {j['group_target']} ({j['total_scraped']} members)",
            callback_data=f"ga_job_{j['id']}"
        ))
    mk.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_cb"))
    bot.send_message(
        msg.chat.id,
        "👥 <b>Group Add Campaign</b>\n\n"
        "Flow:\n"
        "1️⃣ <b>Phase 1</b> — Members ko <b>Add as Contact</b> karo\n"
        "   → Jo add ho gaye unhe <b>Group Invite Link</b> bhejo\n"
        "   → Jo privacy ki wajah se add nahi hue → list mein\n"
        "2️⃣ <b>Phase 2</b> — Privacy-blocked members ko <b>Broadcast DM</b>\n\n"
        "📌 Pehle <b>Scrape Job</b> choose karo:",
        reply_markup=mk,
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("ga_job_"))
@admin_only_cb
def cb_ga_job(call):
    bot.answer_callback_query(call.id)
    jid = int(call.data.split("_")[-1])
    set_state(call.from_user.id, "ga_group", {"scrape_id": jid})
    conn = get_db()
    job  = conn.execute("SELECT * FROM scrape_jobs WHERE id=?", (jid,)).fetchone()
    conn.close()
    bot.send_message(
        call.message.chat.id,
        f"✅ Scrape Job <b>#{jid}</b> select hua "
        f"({job['group_target'] if job else ''}, {job['total_scraped'] if job else '?'} members)\n\n"
        "🎯 <b>Target Group ka link/username bhejo</b>\n"
        "<i>(Jisme members add karne hain)</i>\n\n"
        "<code>@groupname</code>\n"
        "<code>https://t.me/groupname</code>\n"
        "<code>-1001234567890</code>",
        reply_markup=cancel_kb(),
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("ga_perAcc_"))
@admin_only_cb
def cb_ga_per_acc(call):
    bot.answer_callback_query(call.id)
    n   = int(call.data.split("_")[-1])
    uid = call.from_user.id
    st  = get_state(uid)
    if not st:
        bot.send_message(call.message.chat.id, "❌ Session expire. /groupadd dobara karo.")
        return
    data = st["data"]
    data["max_per_acc"] = n
    set_state(uid, "ga_confirm", data)

    conn     = get_db()
    job      = conn.execute("SELECT * FROM scrape_jobs WHERE id=?",
                             (data["scrape_id"],)).fetchone()
    conn.close()
    accs = active_accounts(load())

    mk = InlineKeyboardMarkup()
    mk.add(
        InlineKeyboardButton("✅ Haan, Shuru Karo!", callback_data="ga_confirm"),
        InlineKeyboardButton("❌ Cancel",            callback_data="cancel_cb"),
    )
    bot.send_message(
        call.message.chat.id,
        f"📋 <b>Group Add Campaign — Summary</b>\n\n"
        f"📂 Scrape Job: <b>#{data['scrape_id']}</b> ({job['group_target'] if job else '?'})\n"
        f"🎯 Target Group: <code>{data.get('target_group','?')}</code>\n"
        f"👥 Members: <b>{job['total_scraped'] if job else '?'}</b>\n"
        f"📱 Accounts: <b>{len(accs)}</b>\n"
        f"🔢 Per account: <b>{n}</b>\n"
        f"🔗 Invite Link (fallback): <code>{data.get('invite_link','')[:50]}</code>\n\n"
        "Flow:\n"
        "1️⃣ <b>Phase 1</b> — Direct group add (no phone number sharing)\n"
        "2️⃣ <b>Phase 2</b> — Privacy wale → invite link DM\n"
        "✅ Done members DB se delete ho jayenge\n\n"
        "Campaign shuru karein?",
        reply_markup=mk,
    )

@bot.callback_query_handler(func=lambda c: c.data == "ga_confirm")
@admin_only_cb
def cb_ga_confirm(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id
    st  = get_state(uid)
    if not st or st.get("step") != "ga_confirm":
        bot.send_message(call.message.chat.id,
            "❌ Session expire ho gaya. /groupadd se dobara karo.")
        return
    clear_state(uid)
    data    = st["data"]
    chat_id = call.message.chat.id
    bot.send_message(
        chat_id,
        "🚀 <b>Group Add Campaign shuru ho gaya!</b>\n"
        "Progress neeche aata rahega...",
        reply_markup=main_kb(),
    )

    def run_ga():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(do_group_add_campaign(
            chat_id_bot  = chat_id,
            scrape_id    = data["scrape_id"],
            target_group = data.get("target_group", ""),
            invite_link  = data.get("invite_link", ""),
            max_per_acc  = data.get("max_per_acc", 5),
            bot_instance = bot,
        ))
        loop.close()

    threading.Thread(target=run_ga, daemon=True).start()

# ── /history ──────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["history"])
@bot.message_handler(func=lambda m: m.text == "📋 History")
def cmd_history(msg):
    uid    = msg.from_user.id
    access = check_user_access(uid)
    if not access:
        bot.reply_to(msg, "❌ Access denied!"); return

    is_mm = (access == "main_master")
    text  = "📋 <b>Broadcast History</b>\n\n"

    # Dialog broadcast history (JSON) — sirf Main Master ko dikhta hai (global, per-user tag nahi hai)
    if is_mm:
        d    = load()
        hist = d["history"][:5]
        if hist:
            text += "<b>📢 Dialog Broadcasts (last 5):</b>\n"
            for r in hist:
                dt  = r["sentAt"][:16].replace("T", " ")
                mp  = r["message"][:20] + ("..." if len(r["message"]) > 20 else "")
                text += f"• {dt} ✅{r['totalSent']} ❌{r['totalFailed']}\n  <i>{mp}</i>\n"
        else:
            text += "<b>📢 Dialog Broadcasts:</b> Koi nahi abhi tak.\n"
        text += "\n"

    # Targeted DM history (SQLite) — apni jobs (Main Master ko sab)
    try:
        conn  = get_db()
        if is_mm:
            bc_jobs = conn.execute("SELECT * FROM broadcast_jobs ORDER BY id DESC LIMIT 5").fetchall()
        else:
            bc_jobs = conn.execute(
                "SELECT bj.* FROM broadcast_jobs bj "
                "JOIN scrape_jobs sj ON sj.id = bj.scrape_id "
                "WHERE sj.owner_id=? ORDER BY bj.id DESC LIMIT 5",
                (str(uid),)
            ).fetchall()
        conn.close()
        if bc_jobs:
            text += "<b>🎯 Targeted DM Jobs (last 5):</b>\n"
            for j in bc_jobs:
                date  = (j["created_at"] or "")[:16]
                text += (f"• ID:{j['id']} | {date}\n"
                         f"  ✅ {j['total_sent']} sent | ❌ {j['total_failed']} fail\n")
        else:
            text += "<b>🎯 Targeted DM Jobs:</b> Koi nahi abhi tak.\n"
    except Exception:
        pass

    bot.send_message(msg.chat.id, text, reply_markup=main_kb())

# ── /broadcast (dialog broadcast wizard) ─────────────────────────────────────
@bot.message_handler(commands=["broadcast"])
@bot.message_handler(func=lambda m: m.text == "📢 Broadcast")
def cmd_broadcast(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    uid    = msg.from_user.id
    d      = load()
    active = sum(1 for a in d["accounts"] if a.get("active") and a.get("verified"))
    if not active:
        bot.reply_to(msg, "❌ Koi active account nahi! /add se account add karo."); return

    broadcast_sessions[uid] = {
        "step": "media", "text": "", "media_file_id": None,
        "media_type": None, "buttons": [], "target_mode": "all",
    }
    kb = make_inline([
        [("📷 Photo", "media_photo"), ("🎥 Video", "media_video")],
        [("📄 Document", "media_doc"), ("⏭ Skip (sirf text)", "media_skip")],
    ])
    bot.reply_to(
        msg,
        "📢 <b>Broadcast Wizard</b>\n\n"
        "<b>Step 1/4</b> — Media chuno\n\n"
        "📷 Photo, 🎥 Video, ya 📄 Document bhejoge?\n"
        "Ya skip karke sirf text bhejo.",
        reply_markup=kb,
    )

# ── /quicksend ────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["quicksend"])
def cmd_quicksend(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(msg, "Usage: /quicksend &lt;message&gt;"); return
    text   = parts[1].strip()
    d      = load()
    active = sum(1 for a in d["accounts"] if a.get("active") and a.get("verified"))
    if not active:
        bot.reply_to(msg, "❌ Koi active account nahi!"); return
    st = bot.reply_to(
        msg,
        f"⏳ <b>Quick Broadcast shuru...</b>\n\n"
        f"👤 Accounts: {active}\n"
        f"🎯 Mode: All (Groups + DMs)\n"
        f"<i>Dialogs auto-fetch ho rahe hain...</i>",
    )
    payload = {"text": text, "media_path": None, "buttons": [], "target_mode": "all", "parse_mode": "html"}

    def do():
        r = run_async(run_broadcast(payload))
        if r["ok"]:
            txt = f"✅ <b>Done!</b>\n\n✅ Sent: {r['sent']}\n❌ Failed: {r['failed']}"
        else:
            txt = f"❌ {r['error']}"
        bot.edit_message_text(txt, msg.chat.id, st.message_id)

    threading.Thread(target=do, daemon=True).start()

# ── /tagall ───────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["tagall"])
def cmd_tagall(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    uid    = msg.from_user.id
    d      = load()
    active = sum(1 for a in d["accounts"] if a.get("active") and a.get("verified"))
    if not active:
        bot.reply_to(msg, "❌ Koi active account nahi! /add se account add karo"); return

    st2 = bot.reply_to(
        msg,
        "🏷 <b>Tag All Members</b>\n\n"
        "⏳ Account ke groups fetch ho rahe hain...\n<i>Thoda wait karo</i>",
    )

    def fetch_and_show():
        groups = run_async(fetch_group_list_for_tagall())
        if not groups:
            bot.edit_message_text(
                "❌ Koi group nahi mila!\nAccount ko groups mein add karo pehle.",
                msg.chat.id, st2.message_id
            )
            return
        tagall_sessions[uid] = {"step": "select_group", "groups": groups, "selected": None, "mode": "greeting"}
        lines = ["🏷 <b>Tag All Members — Group Chuno</b>\n\n<b>Groups list:</b>"]
        for i, g in enumerate(groups[:50], 1):
            lines.append(f"  <b>{i}.</b> {g['label']}")
        if len(groups) > 50:
            lines.append(f"  <i>...aur {len(groups)-50} aur (sirf pehle 50 dikha rahe hain)</i>")
        lines.append("\n<b>Number type karo jis group mein tag karna hai:</b>")
        bot.edit_message_text("\n".join(lines), msg.chat.id, st2.message_id)

    threading.Thread(target=fetch_and_show, daemon=True).start()

# ── /tagallgroups ─────────────────────────────────────────────────────────────
@bot.message_handler(commands=["tagallgroups"])
def cmd_tagallgroups(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    d      = load()
    active = sum(1 for a in d["accounts"] if a.get("active") and a.get("verified"))
    if not active:
        bot.reply_to(msg, "❌ Koi active account nahi! /add se account add karo"); return
    kb = make_inline([
        [("🌅 Greeting (Good Morning/Night)", "tagallgrp_greeting")],
        [("📜 Shayri (AI shayri bhejo)",      "tagallgrp_shayri")],
        [("❌ Cancel",                          "tagallgrp_cancel")],
    ])
    bot.reply_to(
        msg,
        "🏷 <b>Tag All Groups — Auto Mode</b>\n\n"
        "✅ Sabhi groups mein sab members automatically tag honge!\n"
        "Koi group select karne ki zaroorat nahi.\n\n"
        "<b>Kaunsa message bhejoge?</b>",
        reply_markup=kb,
    )

# ── /autoclean ────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["autoclean"])
def cmd_autoclean(msg):
    if not check_user_access(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    kb = make_inline([
        [("🧹 Haan, Clean Karo!", "autoclean_confirm")],
        [("❌ Cancel",             "autoclean_cancel")],
    ])
    bot.reply_to(
        msg,
        "🧹 <b>Auto Clean — Inactive Groups</b>\n\n"
        "Yeh feature un sabhi groups ko <b>leave + delete</b> kar dega\n"
        "jahan message nahi bhej sakte.\n\n"
        "<i>⚠️ Yeh action reversible nahi hai!</i>\n\n"
        "Aage badhoge?",
        reply_markup=kb,
    )

# ── /setwelcomephoto ──────────────────────────────────────────────────────────
@bot.message_handler(commands=["setwelcomephoto"])
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/setwelcomephoto"))
def cmd_setwelcomephoto(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf Main Master kar sakta hai!"); return
    bot.send_message(msg.chat.id,
        "📸 <b>Welcome Photo Set karo</b>\n\n"
        "Ab koi bhi photo bhejo — woh sab user masters ko /start pe dikhegi.\n\n"
        "Ya phir photo ki <b>file_id</b> text mein bhejo:\n"
        "<code>/setwelcomephoto FILE_ID_HERE</code>\n\n"
        "Photo hatane ke liye: <code>/setwelcomephoto remove</code>",
        parse_mode="HTML")
    parts = msg.text.split(None, 1)
    if len(parts) > 1:
        val = parts[1].strip()
        if val.lower() == "remove":
            d = load(); d["config"]["welcome_photo_id"] = ""; save(d)
            bot.send_message(msg.chat.id, "🗑️ Welcome photo remove ho gaya.")
        else:
            d = load(); d["config"]["welcome_photo_id"] = val; save(d)
            bot.send_message(msg.chat.id, f"✅ Welcome photo set! File ID: <code>{val}</code>", parse_mode="HTML")
        return
    bot.send_message(msg.chat.id, "📸 Photo bhejo (next message mein):")
    set_state(msg.from_user.id, "setwelcomephoto", {})

@bot.message_handler(content_types=["photo"])
def handle_photo_upload(msg):
    uid  = msg.from_user.id
    step = get_state(uid)[0] if get_state(uid) else None
    if step == "setwelcomephoto" and is_main_master(uid):
        file_id = msg.photo[-1].file_id
        d = load(); d["config"]["welcome_photo_id"] = file_id; save(d)
        clear_state(uid)
        bot.send_message(msg.chat.id,
            f"✅ <b>Welcome photo save ho gaya!</b>\n"
            f"File ID: <code>{file_id}</code>\n\n"
            "Ab /start karne par sabko yeh photo dikhegi.",
            parse_mode="HTML")
        try:
            bot.send_photo(msg.chat.id, file_id, caption="Preview ↑")
        except Exception:
            pass

# ── /setwelcomecaption ────────────────────────────────────────────────────────
@bot.message_handler(commands=["setwelcomecaption"])
def cmd_setwelcomecaption(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf Main Master kar sakta hai!"); return
    parts = msg.text.split(None, 1)
    if len(parts) < 2:
        bot.send_message(msg.chat.id,
            "📝 <b>Welcome Caption Set karo</b>\n\n"
            "Usage: <code>/setwelcomecaption Aapka text yahan...</code>\n\n"
            "Tip: <code>{name}</code> likhoge toh wahan user ka naam ayega.\n\n"
            "Default caption wapas lane ke liye: <code>/setwelcomecaption remove</code>",
            parse_mode="HTML"); return
    val = parts[1].strip()
    if val.lower() == "remove":
        d = load(); d["config"]["welcome_caption"] = ""; save(d)
        bot.send_message(msg.chat.id, "🗑️ Custom caption remove — default use hoga.")
    else:
        d = load(); d["config"]["welcome_caption"] = val; save(d)
        bot.send_message(msg.chat.id,
            f"✅ <b>Welcome caption save ho gaya!</b>\n\nPreview:\n{val.replace('{name}', 'User')}",
            parse_mode="HTML")

# ── /setpromo ─────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["setpromo"])
def cmd_setpromo(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    uid = msg.from_user.id
    promo_sessions[uid] = {"step": "text"}
    bot.reply_to(
        msg,
        "📣 <b>Group Promo Setup</b>\n\n"
        "<b>Step 1/2</b> — Promo text likho\n\n"
        "Example:\n<i>Hamare group mein join karo! Gaming, fun aur prizes! 🎮🔥</i>\n\n"
        "Ab promo text type karo 👇",
    )

# ── /promo ────────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["promo"])
def cmd_promo(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    d  = load()
    pt = d["config"].get("promo_text", "")
    pl = d["config"].get("promo_link", "")
    if not pt or not pl:
        bot.reply_to(msg, "❌ Promo set nahi hai!\nPehle /setpromo se setup karo."); return
    kb = make_inline([
        [("✅ Haan, Promo Bhejo!", "promo_confirm")],
        [("❌ Cancel",             "promo_cancel")],
    ])
    bot.reply_to(
        msg,
        f"📣 <b>Group Promo Confirm</b>\n\n"
        f"<b>Text:</b> {pt[:80]}{'...' if len(pt)>80 else ''}\n"
        f"<b>Link:</b> {pl}\n\n"
        f"Yeh message <b>sabhi groups</b> mein bheja jayega. Confirm?",
        reply_markup=kb,
    )

# ── /autoreply ────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["autoreply"])
def cmd_autoreply(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    d        = load()
    cfg      = d["config"]
    api_id   = cfg.get("api_id", 0)
    api_hash = cfg.get("api_hash", "")
    active   = [a for a in d["accounts"] if a.get("active") and a.get("verified")]
    if not active:
        bot.reply_to(msg, "❌ Koi active account nahi!"); return
    lines = ["🤖 <b>AI Auto-Reply Status</b>\n"]
    for acc in active:
        phone     = acc["phone"]
        acc_label = acc.get("label") or acc.get("name") or phone
        on        = _autoreply_active.get(phone, False)
        status    = "🟢 ON" if on else "🔴 OFF"
        lines.append(f"  {status} — {acc_label}")
    any_on  = any(_autoreply_active.get(a["phone"], False) for a in active)
    any_off = any(not _autoreply_active.get(a["phone"], False) for a in active)
    btns = []
    if any_off:
        btns.append(("✅ Sabhi ON Karo",  "autoreply_all_on"))
    if any_on:
        btns.append(("❌ Sabhi OFF Karo", "autoreply_all_off"))
    kb = make_inline([btns] if btns else [])
    bot.reply_to(msg, "\n".join(lines), reply_markup=kb if btns else None)


# ── /replyraid ────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["replyraid"])
def cmd_replyraid(msg):
    uid = msg.from_user.id
    # Main Master, Admin, ya User Master — sabko permission
    access = check_user_access(uid)
    if not access:
        bot.reply_to(msg, "❌ Access denied!"); return

    target_id = None; target_name = None
    if msg.reply_to_message and msg.reply_to_message.from_user:
        ru = msg.reply_to_message.from_user
        target_id = ru.id; target_name = ru.first_name or str(ru.id)
    else:
        parts = msg.text.split(maxsplit=1)
        if len(parts) >= 2 and parts[1].strip().lstrip("-").isdigit():
            target_id = int(parts[1].strip()); target_name = str(target_id)
        else:
            scope_line = (
                "🌐 <b>Scope: SARE USERS KE SABHI ACCOUNTS</b>" if is_main_master(uid)
                else "👤 <b>Scope: Sirf aapke accounts</b>"
            )
            bot.reply_to(msg,
                f"⚔️ <b>Reply Raid</b>\n\n"
                f"{scope_line}\n\n"
                "Use: kisi ke message pe reply karke <code>/replyraid</code> likho\n"
                "Ya: <code>/replyraid &lt;user_id&gt;</code>\n\n"
                "Band karne: <code>/stopraid</code> (reply) ya <code>/stopraid all</code>\n"
                "List: <code>/raidlist</code>  |  Status: <code>/raidstatus</code>",
                parse_mode="HTML"); return

    # User ke hisab se accounts lo
    accs = get_user_accounts(uid)
    if not accs:
        bot.reply_to(msg,
            "❌ <b>Aapke paas koi active account nahi!</b>\n\n"
            "ReplyRaid ke liye Telethon accounts zaruri hain.\n"
            "/add se account add karo phir try karo.",
            parse_mode="HTML"); return

    sess_ok = [a for a in accs if session_exists(a["phone"])]
    no_sess = [a for a in accs if not session_exists(a["phone"])]

    if not sess_ok:
        lines = ["❌ <b>Kisi bhi account ki session nahi mili!</b>\n"]
        for a in no_sess:
            lines.append(f"  ❌ <code>{a['phone']}</code> — session missing")
        lines.append("\n<b>Solution:</b> /add se sabhi accounts dobara login karo.")
        bot.reply_to(msg, "\n".join(lines), parse_mode="HTML"); return

    _replyraid_users.add(target_id)
    # uid pass karo — main_master = sab accounts, baaki = apne
    started, bad_sess, already = _ensure_replyraid_running(uid, msg.chat.id)

    scope_txt = "🌐 SABHI users ke accounts" if is_main_master(uid) else "👤 Aapke accounts"
    lines = ["⚔️ <b>Reply Raid CHALU!</b>\n"]
    lines.append(f"🎯 Target: <b>{target_name}</b> (<code>{target_id}</code>)")
    lines.append(f"📡 Scope: {scope_txt}")
    lines.append(f"📱 Accounts: {len(accs)} total")
    lines.append(f"  ✅ Session OK  : {len(sess_ok)}")
    if no_sess:
        lines.append(f"  ❌ No session  : {len(no_sess)} (dobara /add se login karo)")
    lines.append(f"  🚀 Naye threads : {started}")
    lines.append(f"  ♻️ Already on   : {already}")
    lines.append(f"\n😈 Target ka har message dekh ke <b>SABHI {len(sess_ok)} accounts</b> ek saath reply karenge!")
    lines.append(f"\n⚠️ <b>Note:</b> Accounts us group mein hone chahiye jahan target message kare.")
    lines.append(f"Band karne: <code>/stopraid</code> (reply) ya <code>/stopraid all</code>")
    bot.reply_to(msg, "\n".join(lines), parse_mode="HTML")


# ── /stopraid ─────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["stopraid"])
def cmd_stopraid(msg):
    uid = msg.from_user.id
    if not check_user_access(uid):
        bot.reply_to(msg, "❌ Access denied!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) >= 2 and parts[1].strip().lower() == "all":
        count = len(_replyraid_users)
        _replyraid_users.clear(); _stop_all_replyraid()
        bot.reply_to(msg,
            f"✅ <b>Sabhi Reply Raids Band!</b>\n❌ {count} target(s) hataye gaye.",
            parse_mode="HTML"); return
    target_id = None; target_name = None
    if msg.reply_to_message and msg.reply_to_message.from_user:
        ru = msg.reply_to_message.from_user
        target_id = ru.id; target_name = ru.first_name or str(ru.id)
    elif len(parts) >= 2 and parts[1].strip().lstrip("-").isdigit():
        target_id = int(parts[1].strip()); target_name = str(target_id)
    else:
        bot.reply_to(msg,
            "Use: kisi ke message pe reply karke <code>/stopraid</code>\n"
            "Ya: <code>/stopraid &lt;user_id&gt;</code>\n"
            "Sab band: <code>/stopraid all</code>", parse_mode="HTML"); return
    if target_id in _replyraid_users:
        _replyraid_users.discard(target_id)
        if not _replyraid_users: _stop_all_replyraid()
        bot.reply_to(msg,
            f"✅ <b>Raid Band!</b>\n"
            f"🎯 <b>{target_name}</b> (<code>{target_id}</code>) ko ab reply nahi jayega.",
            parse_mode="HTML")
    else:
        bot.reply_to(msg, f"⚠️ <code>{target_id}</code> raid list mein nahi tha.", parse_mode="HTML")


# ── /raidstatus ──────────────────────────────────────────────────────────────
@bot.message_handler(commands=["raidstatus"])
def cmd_raidstatus(msg):
    uid = msg.from_user.id
    if not check_user_access(uid):
        bot.reply_to(msg, "❌ Access denied!"); return
    # Caller ke hisab se accounts dikhao
    accs = get_user_accounts(uid)
    scope_txt = "🌐 Sabhi accounts (Main Master)" if is_main_master(uid) else "👤 Aapke accounts"
    lines = ["⚔️ <b>Reply Raid Status</b>\n"]
    lines.append(f"📡 Scope: {scope_txt}")
    lines.append(f"🎯 Raided targets: <b>{len(_replyraid_users)}</b>")
    if _replyraid_users:
        for uid_r in _replyraid_users:
            lines.append(f"  • <code>{uid_r}</code>")
    lines.append("")
    running = sum(1 for a in accs if _replyraid_active.get(a["phone"]))
    lines.append(f"📱 <b>Accounts ({len(accs)} total | 🟢 {running} running):</b>")
    for acc in accs:
        ph   = acc["phone"]
        sess = "✅ sess" if session_exists(ph) else "❌ no-sess"
        thrd = "🟢 ON"   if _replyraid_active.get(ph) else "🔴 OFF"
        lines.append(f"  <code>{ph}</code> — {sess} | {thrd}")
    if not accs:
        lines.append("  Koi account nahi. /add se add karo.")
    lines.append("")
    lines.append("💡 <b>Raid nahi chal raha?</b>")
    lines.append("  1. Session missing → /add se login karo")
    lines.append("  2. Thread OFF → /replyraid &lt;id&gt; dobara chalaao")
    lines.append("  3. Account us group mein hona chahiye jahan target hai")
    bot.reply_to(msg, "\n".join(lines), parse_mode="HTML")


# ── /raidlist ─────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["raidlist"])
def cmd_raidlist(msg):
    uid = msg.from_user.id
    if not check_user_access(uid):
        bot.reply_to(msg, "❌ Access denied!"); return
    if not _replyraid_users:
        bot.reply_to(msg,
            "⚔️ <b>Reply Raid List</b>\n\nKoi user raid mein nahi hai.\n"
            "Shuru karne ke liye: <code>/replyraid</code>", parse_mode="HTML"); return
    lines = [f"⚔️ <b>Active Reply Raids ({len(_replyraid_users)}):</b>\n"]
    for uid_r in _replyraid_users: lines.append(f"  🎯 <code>{uid_r}</code>")
    lines.append("\nBand karne ke liye: <code>/stopraid all</code>")
    bot.reply_to(msg, "\n".join(lines), parse_mode="HTML")


# ── /cloneprofile ─────────────────────────────────────────────────────────────
@bot.message_handler(commands=["cloneprofile"])
def cmd_cloneprofile(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) >= 2 and parts[1].strip():
        target_id = parts[1].strip()
        _run_clone(msg, target_id)
    else:
        clone_sessions[msg.from_user.id] = True
        bot.reply_to(
            msg,
            "👤 <b>Profile Clone</b>\n\n"
            "Jis user ki profile copy karni hai uska <b>Telegram User ID</b> bhejo.\n\n"
            "Example: <code>123456789</code>",
        )

# ── /listadmins ───────────────────────────────────────────────────────────────
@bot.message_handler(commands=["listadmins"])
def cmd_listadmins(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    d    = load()
    ids  = d["config"].get("admin_ids", [])
    lines = ["👑 <b>Admin List:</b>\n"]
    for i, aid in enumerate(ids, 1):
        lines.append(f"  {i}. <code>{aid}</code>")
    try:
        conn   = get_db()
        admins = conn.execute("SELECT * FROM admins ORDER BY id").fetchall()
        conn.close()
        if admins:
            lines.append("\n<b>Extra Admins (DB):</b>")
            for a in admins:
                lines.append(f"  • <code>{a['telegram_user_id']}</code> — {a['label']}")
    except Exception:
        pass
    lines.append(f"\n<i>Total: {len(ids)} super admin(s)</i>")
    bot.reply_to(msg, "\n".join(lines))

@bot.message_handler(commands=["addadmin"])
def cmd_addadmin(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(msg,
            "Usage: /addadmin &lt;ID&gt;\nExample: <code>/addadmin 123456789</code>"); return
    new_id = parts[1].strip()
    if not new_id.lstrip("-").isdigit():
        bot.reply_to(msg, "❌ ID sirf number hona chahiye!"); return
    d   = load()
    ids = [str(x) for x in d["config"].get("admin_ids", [])]
    if new_id in ids:
        bot.reply_to(msg, f"⚠️ <code>{new_id}</code> pehle se admin hai!"); return
    ids.append(new_id)
    d["config"]["admin_ids"] = [int(x) if x.isdigit() else x for x in ids]
    save(d)
    bot.reply_to(
        msg,
        f"✅ <b>Admin add ho gaya!</b>\n\n"
        f"👑 ID: <code>{new_id}</code>\n"
        f"Total admins: <b>{len(ids)}</b>",
    )

@bot.message_handler(commands=["removeadmin"])
def cmd_removeadmin(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(msg, "Usage: /removeadmin &lt;ID&gt;"); return
    rem_id = parts[1].strip()
    if str(msg.from_user.id) == rem_id:
        bot.reply_to(msg, "❌ Aap khud ko remove nahi kar sakte!"); return
    d   = load()
    ids = [str(x) for x in d["config"].get("admin_ids", [])]
    if rem_id not in ids:
        bot.reply_to(msg, f"❌ <code>{rem_id}</code> admin list mein nahi hai!"); return
    ids.remove(rem_id)
    d["config"]["admin_ids"] = [int(x) if x.isdigit() else x for x in ids]
    save(d)
    bot.reply_to(
        msg,
        f"✅ <b>Admin remove ho gaya!</b>\n\n"
        f"🗑 ID: <code>{rem_id}</code>\n"
        f"Remaining admins: <b>{len(ids)}</b>",
    )

# ── /admins (DB admins management) ───────────────────────────────────────────
@bot.message_handler(commands=["admins"])
def cmd_admins(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    try:
        conn   = get_db()
        admins = conn.execute("SELECT * FROM admins ORDER BY id").fetchall()
        conn.close()
    except Exception:
        admins = []
    d    = load()
    text = "👑 <b>Admins List:</b>\n\n"
    text += "<b>Super Admins (config):</b>\n"
    for aid in d["config"].get("admin_ids", []):
        text += f"• <code>{aid}</code>\n"
    if admins:
        text += "\n<b>Extra Admins (DB):</b>\n"
        for a in admins:
            text += f"• <code>{a['telegram_user_id']}</code> — {a['label']}\n"
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("➕ Admin Add Karo", callback_data="admin_add"))
    mk.add(InlineKeyboardButton("🗑 Admin Remove Karo", callback_data="admin_del_list"))
    bot.send_message(msg.chat.id, text, reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data == "admin_add")
@admin_only_cb
def cb_admin_add(call):
    bot.answer_callback_query(call.id)
    set_state(call.from_user.id, "admin_add_id")
    bot.send_message(call.message.chat.id,
        "👑 Naye admin ka <b>Telegram User ID</b> bhejo:",
        reply_markup=cancel_kb())

@bot.callback_query_handler(func=lambda c: c.data == "admin_del_list")
@admin_only_cb
def cb_admin_del_list(call):
    bot.answer_callback_query(call.id)
    conn   = get_db()
    admins = conn.execute("SELECT * FROM admins").fetchall()
    conn.close()
    if not admins:
        bot.send_message(call.message.chat.id, "Koi extra admin nahi hai.")
        return
    mk = InlineKeyboardMarkup()
    for a in admins:
        mk.add(InlineKeyboardButton(
            f"🗑 {a['telegram_user_id']} — {a['label']}",
            callback_data=f"admin_del_{a['id']}"
        ))
    mk.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_cb"))
    bot.send_message(call.message.chat.id, "Kaun sa admin remove karna hai?", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_del_"))
@admin_only_cb
def cb_admin_del(call):
    bot.answer_callback_query(call.id)
    aid  = int(call.data.split("_")[-1])
    conn = get_db()
    conn.execute("DELETE FROM admins WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    bot.send_message(call.message.chat.id, "✅ Admin remove ho gaya!", reply_markup=main_kb())

# ═══════════════════════════════════════════════════════
#  USER MASTER MANAGEMENT (Main Master only)
# ═══════════════════════════════════════════════════════

@bot.message_handler(commands=["addusermaster"])
def cmd_addusermaster(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf Main Master ye kar sakta hai!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        bot.reply_to(msg, "Usage: /addusermaster &lt;TelegramID&gt;\nExample: <code>/addusermaster 123456789</code>"); return
    new_uid = int(parts[1].strip())
    d = load()
    ums = d["config"].setdefault("user_masters", [])
    if new_uid in ums:
        bot.reply_to(msg, f"⚠️ <code>{new_uid}</code> pehle se User Master hai!"); return
    ums.append(new_uid)
    save(d)
    bot.reply_to(msg, f"✅ <b>User Master add ho gaya!</b>\n🔑 ID: <code>{new_uid}</code>\n\n"
                      "Ye user /add se apne accounts add kar sakta hai aur sirf unhe use kar sakta hai.")

@bot.message_handler(commands=["removeusermaster"])
def cmd_removeusermaster(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf Main Master ye kar sakta hai!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(msg, "Usage: /removeusermaster &lt;TelegramID&gt;"); return
    rem_uid = int(parts[1].strip())
    d   = load()
    ums = d["config"].get("user_masters", [])
    if rem_uid not in ums:
        bot.reply_to(msg, f"❌ <code>{rem_uid}</code> User Master nahi hai!"); return
    ums.remove(rem_uid)
    save(d)
    bot.reply_to(msg, f"✅ User Master remove ho gaya: <code>{rem_uid}</code>")

@bot.message_handler(commands=["listusermaster", "usermasterslist"])
def cmd_listusermaster(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf Main Master ye dekh sakta hai!"); return
    d   = load()
    ums = d["config"].get("user_masters", [])
    if not ums:
        bot.reply_to(msg, "🔑 Koi User Master nahi hai abhi.\n/addusermaster se add karo."); return
    lines = ["🔑 <b>User Masters List:</b>\n"]
    owners = d.get("account_owners", {})
    for uid_m in ums:
        owned = [p for p, o in owners.items() if str(o) == str(uid_m)]
        lines.append(f"• <code>{uid_m}</code> — <b>{len(owned)}</b> account(s)")
    bot.reply_to(msg, "\n".join(lines))

@bot.message_handler(commands=["setmainmaster"])
def cmd_setmainmaster(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf current Main Master ye change kar sakta hai!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        bot.reply_to(msg, "Usage: /setmainmaster &lt;TelegramID&gt;\n⚠️ Ye aapka access remove kar dega!"); return
    new_mid = int(parts[1].strip())
    d = load()
    d["config"]["main_master_id"] = new_mid
    save(d)
    bot.reply_to(msg, f"✅ <b>Main Master change ho gaya!</b>\n👑 New Main Master: <code>{new_mid}</code>")

# ═══════════════════════════════════════════════════════
#  FORCE JOIN COMMANDS (Main Master only)
# ═══════════════════════════════════════════════════════

@bot.message_handler(commands=["setforcejoin"])
def cmd_setforcejoin(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf Main Master ye set kar sakta hai!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        d = load()
        curr = d["config"].get("force_join_groups", [])
        bot.reply_to(msg,
            "📌 <b>Force Join Groups</b>\n\n"
            f"Current: {', '.join(curr) if curr else 'Koi nahi'}\n\n"
            "Set karne ke liye:\n"
            "<code>/setforcejoin @group1, @group2, @group3</code>\n\n"
            "Bot start hote hi saare active accounts ye groups join karenge.")
        return
    raw_groups = [g.strip() for g in parts[1].split(",") if g.strip()]
    groups = []
    for g in raw_groups[:3]:  # Max 3
        if g.startswith("https://t.me/"):
            sl = g.split("https://t.me/")[1].split("/")[0]
            g  = ("https://t.me/" + sl) if sl.startswith("+") else ("@" + sl)
        elif not g.startswith("@") and not g.startswith("-") and not g.lstrip("-").isdigit():
            g = "@" + g
        groups.append(g)
    d = load()
    d["config"]["force_join_groups"] = groups
    save(d)
    bot.reply_to(msg,
        f"✅ <b>Force Join Groups set ho gaye!</b>\n\n"
        + "\n".join(f"• <code>{g}</code>" for g in groups)
        + "\n\n/forcejoin se abhi join karwao ya bot restart pe auto-join hoga.")

@bot.message_handler(commands=["forcejoin"])
def cmd_forcejoin(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf Main Master ye kar sakta hai!"); return
    d      = load()
    groups = d["config"].get("force_join_groups", [])
    if not groups:
        bot.reply_to(msg, "❌ Koi force join group set nahi hai!\n/setforcejoin se pehle set karo."); return
    accs = active_accounts()
    if not accs:
        bot.reply_to(msg, "❌ Koi active account nahi!"); return
    bot.reply_to(msg,
        f"🔗 <b>Force Join shuru ho raha hai...</b>\n\n"
        f"Groups: {', '.join(groups)}\n"
        f"Accounts: {len(accs)}\n\n"
        "⏳ Background mein chal raha hai, result aayega...")
    run_force_join_all(chat_id_report=msg.chat.id)

@bot.message_handler(commands=["viewforcejoin"])
def cmd_viewforcejoin(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    d = load()
    groups = d["config"].get("force_join_groups", [])
    if not groups:
        bot.reply_to(msg, "📌 Koi force join group set nahi hai.\n/setforcejoin se set karo.")
    else:
        bot.reply_to(msg, "📌 <b>Force Join Groups:</b>\n" + "\n".join(f"• <code>{g}</code>" for g in groups))

# ═══════════════════════════════════════════════════════
#  MUSIC BOT COMMANDS (Main Master only)
# ═══════════════════════════════════════════════════════

@bot.message_handler(commands=["setmusicbots"])
def cmd_setmusicbots(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf Main Master ye set kar sakta hai!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        d = load()
        curr = d["config"].get("music_bot_usernames", [])
        bot.reply_to(msg,
            "🎵 <b>Music Bot Usernames</b>\n\n"
            f"Current: {', '.join(curr) if curr else 'Koi nahi'}\n\n"
            "Scrape se pehle ye bots target group mein add kiye jayenge.\n\n"
            "Set karne ke liye:\n"
            "<code>/setmusicbots @musicbot1, @musicbot2</code>")
        return
    bots = [b.strip() for b in parts[1].split(",") if b.strip()]
    bots = [("@" + b.lstrip("@")) for b in bots]
    d    = load()
    d["config"]["music_bot_usernames"] = bots
    save(d)
    bot.reply_to(msg,
        f"✅ <b>Music Bots set ho gaye!</b>\n\n"
        + "\n".join(f"• <code>{b}</code>" for b in bots)
        + "\n\nAb /scrape karte waqt ye bots target group mein automatically add honge.")

# ═══════════════════════════════════════════════════════
#  BLACKLIST GROUP COMMANDS (Main Master only)
# ═══════════════════════════════════════════════════════

@bot.message_handler(commands=["blacklist"])
def cmd_blacklist(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf Main Master blacklist manage kar sakta hai!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(msg,
            "🚫 <b>Blacklist Group</b>\n\n"
            "Usage: <code>/blacklist @groupname</code>\n"
            "Ya: <code>/blacklist -1001234567890</code>\n\n"
            "Blacklisted groups mein na scrape hoga na join.\n"
            "/listblacklist se list dekho."); return
    group = parts[1].strip()
    if group.startswith("https://t.me/"):
        sl    = group.split("https://t.me/")[1].split("/")[0]
        group = ("https://t.me/" + sl) if sl.startswith("+") else ("@" + sl)
    elif not group.startswith("@") and not group.startswith("-") and not group.lstrip("-").isdigit():
        group = "@" + group
    d  = load()
    bl = d["config"].setdefault("blacklist_groups", [])
    if group in bl or group.lstrip("@") in [b.lstrip("@") for b in bl]:
        bot.reply_to(msg, f"⚠️ <code>{group}</code> pehle se blacklisted hai!"); return
    bl.append(group)
    save(d)
    bot.reply_to(msg, f"🚫 <b>Blacklist ho gaya!</b>\n<code>{group}</code>\n\nAb is group mein na scrape hoga na join.")

@bot.message_handler(commands=["unblacklist"])
def cmd_unblacklist(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Sirf Main Master blacklist manage kar sakta hai!"); return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(msg, "Usage: <code>/unblacklist @groupname</code>"); return
    group = parts[1].strip().lstrip("@")
    d     = load()
    bl    = d["config"].get("blacklist_groups", [])
    before = len(bl)
    d["config"]["blacklist_groups"] = [b for b in bl if b.lstrip("@") != group]
    if len(d["config"]["blacklist_groups"]) < before:
        save(d)
        bot.reply_to(msg, f"✅ Blacklist se remove ho gaya: <code>@{group}</code>")
    else:
        bot.reply_to(msg, f"❌ <code>@{group}</code> blacklist mein nahi tha!")

@bot.message_handler(commands=["listblacklist"])
def cmd_listblacklist(msg):
    if not is_main_master(msg.from_user.id):
        bot.reply_to(msg, "❌ Access denied!"); return
    d  = load()
    bl = d["config"].get("blacklist_groups", [])
    if not bl:
        bot.reply_to(msg, "🚫 Koi blacklisted group nahi hai."); return
    lines = ["🚫 <b>Blacklisted Groups:</b>\n"]
    for b in bl:
        lines.append(f"• <code>{b}</code>")
    lines.append(f"\n<i>Total: {len(bl)} groups</i>")
    lines.append("\n/unblacklist @group se remove karo")
    bot.reply_to(msg, "\n".join(lines))

# ── Cancel callback ───────────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "cancel_cb")
def cb_cancel(call):
    bot.answer_callback_query(call.id)
    clear_state(call.from_user.id)
    bot.send_message(call.message.chat.id, "❌ Cancel ho gaya.", reply_markup=main_kb())

# ═══════════════════════════════════════════════════════
#  MAIN MENU INLINE BUTTON CALLBACKS
# ═══════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data.startswith("menu_"))
def cb_main_menu(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id
    if not check_user_access(uid):
        bot.answer_callback_query(call.id, "❌ Access denied!")
        return
    action = call.data  # e.g. "menu_broadcast"
    # Create a fake message object pointing to the same chat
    class FakeMsg:
        def __init__(self, orig_call):
            self.chat    = orig_call.message.chat
            self.from_user = orig_call.from_user
            self.text    = ""
            self.message_id = orig_call.message.message_id
    fake = FakeMsg(call)
    if action == "menu_broadcast":
        cmd_broadcast(fake)
    elif action == "menu_targeted":
        cmd_targeted(fake)
    elif action == "menu_scrape":
        cmd_scrape(fake)
    elif action == "menu_members":
        cmd_members(fake)
    elif action == "menu_replyraid":
        cmd_replyraid(fake)
    elif action == "menu_stopraid":
        cmd_stopraid(fake)
    elif action == "menu_tagall":
        cmd_tagall(fake)
    elif action == "menu_promo":
        cmd_promo(fake)
    elif action == "menu_autoreply":
        cmd_autoreply(fake)
    elif action == "menu_cloneprofile":
        cmd_cloneprofile(fake)
    elif action == "menu_autoclean":
        cmd_autoclean(fake)
    elif action == "menu_stats":
        cmd_stats(fake)
    elif action == "menu_accounts":
        cmd_accounts(fake)
    elif action == "menu_exportcsv":
        cmd_exportcsv(fake)
    elif action == "menu_checklimit":
        cmd_checkaccount(fake)
    elif action == "menu_history":
        cmd_history(fake)
    elif action == "menu_help":
        cmd_help(fake)
    elif action == "menu_sessions":
        uid = call.from_user.id
        if not is_main_master(uid):
            bot.answer_callback_query(call.id, "🔒 Sirf Main Master dekh sakta hai!", show_alert=True)
        else:
            fake2 = type('FM', (), {
                'chat': call.message.chat,
                'from_user': call.from_user,
                'text': '/sessions',
                'message_id': call.message.message_id
            })()
            cmd_sessions(fake2)
    elif action == "menu_forcejoin":
        if not is_main_master(call.from_user.id):
            bot.answer_callback_query(call.id, "🔒 Sirf Main Master!", show_alert=True); return
        d = load()
        groups = d["config"].get("force_join_groups", [])
        accs   = active_accounts()
        curr_txt = "\n".join(f"• <code>{g}</code>" for g in groups) if groups else "❌ Koi group set nahi"
        kb2 = InlineKeyboardMarkup()
        if groups and accs:
            kb2.add(InlineKeyboardButton("▶️ Abhi Force Join Karo", callback_data="do_forcejoin"))
        kb2.add(InlineKeyboardButton("✏️ Groups Set Karo", callback_data="set_forcejoin_prompt"))
        bot.send_message(
            call.message.chat.id,
            f"🔗 <b>Force Join Settings</b>\n\n"
            f"<b>Current Groups:</b>\n{curr_txt}\n\n"
            f"Active Accounts: {len(accs)}\n\n"
            f"<b>Group set karne ke liye:</b>\n"
            f"<code>/setforcejoin @group1, @group2</code>",
            parse_mode="HTML", reply_markup=kb2
        )
    elif action == "do_forcejoin":
        if not is_main_master(call.from_user.id): return
        d = load()
        groups = d["config"].get("force_join_groups", [])
        accs   = active_accounts()
        if not groups:
            bot.answer_callback_query(call.id, "❌ Pehle /setforcejoin se groups set karo!", show_alert=True); return
        if not accs:
            bot.answer_callback_query(call.id, "❌ Koi active account nahi!", show_alert=True); return
        bot.answer_callback_query(call.id, "⏳ Force Join shuru ho gaya...")
        bot.send_message(call.message.chat.id,
            f"🔗 Force Join chal raha hai...\n"
            f"Groups: {', '.join(groups)}\n"
            f"Accounts: {len(accs)}\n\n"
            "⏳ Result thodi der mein aayega...")
        run_force_join_all(chat_id_report=call.message.chat.id)
    elif action == "set_forcejoin_prompt":
        if not is_main_master(call.from_user.id): return
        bot.send_message(call.message.chat.id,
            "✏️ <b>Force Join Groups Set Karo:</b>\n\n"
            "<code>/setforcejoin @group1, @group2, @group3</code>\n\n"
            "Max 3 groups. Bot start hote hi saare accounts join karenge.",
            parse_mode="HTML")
    elif action == "menu_musicbots":
        if not is_main_master(call.from_user.id):
            bot.answer_callback_query(call.id, "🔒 Sirf Main Master!", show_alert=True); return
        d    = load()
        bots = d["config"].get("music_bot_usernames", [])
        curr_txt = "\n".join(f"• <code>{b}</code>" for b in bots) if bots else "❌ Koi music bot set nahi"
        bot.send_message(
            call.message.chat.id,
            f"🎵 <b>Music Bot Settings</b>\n\n"
            f"<b>Current Bots:</b>\n{curr_txt}\n\n"
            f"Yeh bots scrape se pehle target group mein automatically add kiye jaate hain.\n\n"
            f"<b>Set karne ke liye:</b>\n"
            f"<code>/setmusicbots @musicbot1, @musicbot2</code>",
            parse_mode="HTML"
        )
    elif action == "menu_setmongouri":
        bot.send_message(
            call.message.chat.id,
            "🍃 <b>MongoDB URI Set Karo</b>\n\n"
            "Neeche diye format mein URI bhejo:\n"
            "<code>/setmongouri mongodb+srv://USER:PASS@cluster0.xxxx.mongodb.net/?retryWrites=true&amp;w=majority</code>\n\n"
            "🆓 Free cluster: mongodb.com/atlas\n"
            f"📡 Current Status: {'✅ Connected' if _get_mongo_db() is not None else '❌ Not connected'}",
            parse_mode="HTML"
        )

# ═══════════════════════════════════════════════════════
#  UNIFIED CALLBACK HANDLER (broadcast wizard + tagall + misc)
# ═══════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid     = call.from_user.id
    data_cb = call.data

    if not check_user_access(uid):
        bot.answer_callback_query(call.id, "❌ Access denied!")
        return

    no_sess_needed = {
        "tagall_confirm", "tagall_cancel",
        "tagall_mode_greeting", "tagall_mode_shayri",
        "tagallgrp_greeting", "tagallgrp_shayri", "tagallgrp_cancel",
        "autoclean_confirm", "autoclean_cancel",
        "promo_confirm", "promo_cancel",
        "autoreply_all_on", "autoreply_all_off",
    }
    if data_cb in no_sess_needed:
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id)

    sess = broadcast_sessions.get(uid)

    # ── Dialog Broadcast Wizard: Step 1 media ────────────────────────────────
    if data_cb in ("media_photo", "media_video", "media_doc", "media_skip"):
        if not sess:
            return
        if data_cb == "media_skip":
            sess["media_type"] = None
            sess["step"] = "text"
            bot.edit_message_text(
                "✅ Media skip\n\n"
                "<b>Step 2/4</b> — Message text likho\n\n"
                "HTML formatting use kar sakte ho:\n"
                "<code>&lt;b&gt;Bold&lt;/b&gt;</code>  <code>&lt;i&gt;Italic&lt;/i&gt;</code>\n\n"
                "Ab message type karke bhejo 👇",
                call.message.chat.id, call.message.message_id,
            )
        else:
            type_map = {"media_photo": "photo", "media_video": "video", "media_doc": "document"}
            sess["media_type"] = type_map[data_cb]
            sess["step"] = "media_upload"
            icons = {"photo": "📷", "video": "🎥", "document": "📄"}
            bot.edit_message_text(
                f"<b>Step 1/4</b> — {icons[sess['media_type']]} {sess['media_type'].title()} bhejo\n\n"
                "Ab media file bhejo 👇",
                call.message.chat.id, call.message.message_id,
            )

    # ── Dialog Broadcast Wizard: Step 3 buttons ──────────────────────────────
    elif data_cb == "btn_add":
        if not sess: return
        sess["step"] = "btn_input"
        bot.edit_message_text(
            "<b>Step 3/4</b> — Button add karo\n\n"
            "Format: <code>Button Text | https://link.com</code>\n\n"
            "Example:\n<code>Join Channel | https://t.me/mychannel</code>\n\n"
            "Ek line mein ek button. Ab likho 👇",
            call.message.chat.id, call.message.message_id,
        )

    elif data_cb == "btn_done":
        if not sess: return
        _ask_target_type(call.message, uid)

    elif data_cb == "btn_clear":
        if not sess: return
        sess["buttons"] = []
        _ask_buttons(call.message, uid)

    # ── Dialog Broadcast Wizard: Step 4 target type ──────────────────────────
    elif data_cb in ("tgt_all", "tgt_groups", "tgt_dms"):
        if not sess: return
        mode_map = {"tgt_all": "all", "tgt_groups": "group", "tgt_dms": "dm"}
        sess["target_mode"] = mode_map[data_cb]
        _show_preview(call.message, uid)

    elif data_cb == "confirm_send":
        if not sess: return
        _do_wizard_broadcast(call.message, uid)

    elif data_cb == "confirm_cancel":
        broadcast_sessions.pop(uid, None)
        bot.edit_message_text("❌ Broadcast cancel ho gaya.", call.message.chat.id, call.message.message_id)

    # ── TagAll: mode selection ────────────────────────────────────────────────
    elif data_cb in ("tagall_mode_greeting", "tagall_mode_shayri"):
        tsess = tagall_sessions.get(uid)
        if not tsess or not tsess.get("selected"):
            bot.edit_message_text("❌ Session expire ho gaya. /tagall dobara",
                                  call.message.chat.id, call.message.message_id); return
        mode      = "shayri" if data_cb == "tagall_mode_shayri" else "greeting"
        tsess["mode"] = mode
        tsess["step"] = "confirm"
        sel       = tsess["selected"]
        mode_icon = "📜 Shayri" if mode == "shayri" else "🌅 Greeting"
        kb = make_inline([
            [("✅ Haan, Tag Shuru Karo!", "tagall_confirm")],
            [("❌ Cancel", "tagall_cancel")],
        ])
        bot.edit_message_text(
            f"🏷 <b>Confirm Tag All</b>\n\n"
            f"👥 Group: <b>{sel['label']}</b>\n"
            f"📨 Mode: <b>{mode_icon}</b>\n\n"
            f"Is group ke <b>sab members</b> ko tag karein?",
            call.message.chat.id, call.message.message_id, reply_markup=kb,
        )

    elif data_cb == "tagall_confirm":
        tsess = tagall_sessions.get(uid)
        if not tsess or not tsess.get("selected"):
            bot.edit_message_text("❌ Session expire ho gaya. /tagall dobara",
                                  call.message.chat.id, call.message.message_id); return
        sel  = tsess["selected"]
        mode = tsess.get("mode", "greeting")
        tagall_sessions.pop(uid, None)
        mode_icon = "📜 Shayri" if mode == "shayri" else "🌅 Greeting"
        st2 = bot.edit_message_text(
            f"⏳ <b>Tagging shuru...</b>\n\n"
            f"👥 Group: <b>{sel['label']}</b>\n"
            f"📨 Mode: <b>{mode_icon}</b>\n<i>Members fetch ho rahe hain...</i>",
            call.message.chat.id, call.message.message_id,
        )
        _last_tag_edit = [time.time()]
        _sel_cap  = sel
        _mode_cap = mode
        _st2_cap  = st2

        def on_tag_progress(status, sent, failed, total):
            now = time.time()
            if now - _last_tag_edit[0] < 3.0: return
            _last_tag_edit[0] = now
            pct = f"{round(sent/total*100)}%" if total else "..."
            try:
                bot.edit_message_text(
                    f"⏳ <b>Tagging Live...</b>\n\n"
                    f"👥 <b>{_sel_cap['label']}</b>\n"
                    f"✅ Tagged: {sent}  ❌ Failed: {failed}  ({pct} of {total})\n"
                    f"<i>{status}</i>",
                    call.message.chat.id, _st2_cap.message_id,
                )
            except Exception: pass

        def do_tag():
            result = run_async(run_tagall(
                {"group_id": _sel_cap["id"], "group_name": _sel_cap["label"], "mode": _mode_cap},
                progress_cb=on_tag_progress
            ))
            if not result["ok"]:
                bot.edit_message_text(f"❌ <b>Tag fail!</b>\n{result['error']}",
                                      call.message.chat.id, _st2_cap.message_id); return
            emoji = "✅" if result["failed"] == 0 else "⚠️"
            bot.edit_message_text(
                f"{emoji} <b>Tagging Complete!</b>\n\n"
                f"👥 Group: <b>{result['group']}</b>\n"
                f"📨 Mode: <b>{'📜 Shayri' if _mode_cap == 'shayri' else '🌅 Greeting'}</b>\n\n"
                f"✅ Tagged: <b>{result['sent']}</b>\n"
                f"❌ Failed: <b>{result['failed']}</b>\n"
                f"👥 Total Members: <b>{result['total']}</b>",
                call.message.chat.id, _st2_cap.message_id,
            )

        threading.Thread(target=do_tag, daemon=True).start()

    elif data_cb == "tagall_cancel":
        tagall_sessions.pop(uid, None)
        bot.edit_message_text("❌ Tag all cancel ho gaya.", call.message.chat.id, call.message.message_id)

    # ── Tag All Groups (auto) ─────────────────────────────────────────────────
    elif data_cb in ("tagallgrp_greeting", "tagallgrp_shayri"):
        mode      = "shayri" if data_cb == "tagallgrp_shayri" else "greeting"
        mode_icon = "📜 Shayri" if mode == "shayri" else "🌅 Greeting"
        st2 = bot.edit_message_text(
            f"⏳ <b>Tag All Groups shuru...</b>\n\n"
            f"📨 Mode: <b>{mode_icon}</b>\n"
            f"<i>Groups fetch ho rahe hain...</i>",
            call.message.chat.id, call.message.message_id,
        )
        _last_grp_edit = [time.time()]
        _mode_grp = mode
        _st2_grp  = st2

        def on_grp_progress(status, total_sent, total_failed, groups_done, total_groups):
            now = time.time()
            if now - _last_grp_edit[0] < 3.5: return
            _last_grp_edit[0] = now
            try:
                bot.edit_message_text(
                    f"⏳ <b>Tag All Groups Live...</b>\n\n"
                    f"📨 Mode: <b>{'📜 Shayri' if _mode_grp == 'shayri' else '🌅 Greeting'}</b>\n"
                    f"📁 Groups: {groups_done}/{total_groups}\n"
                    f"✅ Tagged: {total_sent}  ❌ Failed: {total_failed}\n\n"
                    f"<i>{status}</i>",
                    call.message.chat.id, _st2_grp.message_id,
                )
            except Exception: pass

        def do_grp_tag():
            result = run_async(run_tagall_all_groups({"mode": _mode_grp}, progress_cb=on_grp_progress))
            if not result["ok"]:
                bot.edit_message_text(f"❌ <b>Tag All Groups fail!</b>\n{result['error']}",
                                      call.message.chat.id, _st2_grp.message_id); return
            emoji = "✅" if result["total_failed"] == 0 else "⚠️"
            bot.edit_message_text(
                f"{emoji} <b>Tag All Groups Complete!</b>\n\n"
                f"📨 Mode: <b>{'📜 Shayri' if _mode_grp == 'shayri' else '🌅 Greeting'}</b>\n"
                f"👤 Account: {result.get('account','—')}\n\n"
                f"📁 Groups Tagged: <b>{result['groups_done']}</b> / {result['total_groups']}\n"
                f"✅ Total Tagged: <b>{result['total_sent']}</b>\n"
                f"❌ Total Failed: <b>{result['total_failed']}</b>",
                call.message.chat.id, _st2_grp.message_id,
            )

        threading.Thread(target=do_grp_tag, daemon=True).start()

    elif data_cb == "tagallgrp_cancel":
        bot.edit_message_text("❌ Tag All Groups cancel ho gaya.",
                              call.message.chat.id, call.message.message_id)

    # ── Auto Clean ────────────────────────────────────────────────────────────
    elif data_cb == "autoclean_confirm":
        st2 = bot.edit_message_text(
            "🧹 <b>Auto Clean chal raha hai...</b>\n\n"
            "<i>Groups scan ho rahe hain...</i>",
            call.message.chat.id, call.message.message_id,
        )
        _last_cl_edit = [time.time()]
        _st2_cl = st2

        def on_clean_progress(acc_label, left, errors, status):
            now = time.time()
            if now - _last_cl_edit[0] < 3.0: return
            _last_cl_edit[0] = now
            try:
                bot.edit_message_text(
                    f"🧹 <b>Clean Live...</b>\n\n"
                    f"👤 Account: <b>{acc_label}</b>\n"
                    f"🚪 Left: {left}  ❌ Errors: {errors}\n<i>{status}</i>",
                    call.message.chat.id, _st2_cl.message_id,
                )
            except Exception: pass

        def do_clean():
            result = run_async(run_auto_leave_inactive(progress_cb=on_clean_progress, owner_uid=uid))
            if not result["ok"]:
                bot.edit_message_text(f"❌ <b>Clean fail!</b>\n{result['error']}",
                                      call.message.chat.id, _st2_cl.message_id); return
            emoji = "✅" if result["errors"] == 0 else "⚠️"
            bot.edit_message_text(
                f"{emoji} <b>Auto Clean Complete!</b>\n\n"
                f"🚪 Groups Left: <b>{result['left']}</b>\n"
                f"❌ Errors: <b>{result['errors']}</b>\n\n"
                f"<i>Account limit free ho gayi! ✨</i>",
                call.message.chat.id, _st2_cl.message_id,
            )

        threading.Thread(target=do_clean, daemon=True).start()

    elif data_cb == "autoclean_cancel":
        bot.edit_message_text("❌ Auto Clean cancel ho gaya.", call.message.chat.id, call.message.message_id)

    # ── Promo callbacks ───────────────────────────────────────────────────────
    elif data_cb == "promo_confirm":
        st2 = bot.edit_message_text(
            "📣 <b>Group Promo chal raha hai...</b>\n\n"
            "<i>Sabhi groups ko promo bheja ja raha hai...</i>",
            call.message.chat.id, call.message.message_id,
        )
        _last_promo_edit = [time.time()]
        _st2_promo = st2

        def on_promo_progress(status, sent, failed, total):
            now = time.time()
            if now - _last_promo_edit[0] < 3.0: return
            _last_promo_edit[0] = now
            try:
                bot.edit_message_text(
                    f"📣 <b>Group Promo Live...</b>\n\n"
                    f"✅ Sent: {sent}  ❌ Failed: {failed}\n<i>{status}</i>",
                    call.message.chat.id, _st2_promo.message_id,
                )
            except Exception: pass

        def do_promo():
            result = run_async(run_group_promo(progress_cb=on_promo_progress))
            if not result["ok"]:
                bot.edit_message_text(f"❌ <b>Promo fail!</b>\n{result['error']}",
                                      call.message.chat.id, _st2_promo.message_id); return
            emoji = "✅" if result["failed"] == 0 else "⚠️"
            bot.edit_message_text(
                f"{emoji} <b>Group Promo Complete!</b>\n\n"
                f"👤 Account: {result.get('account','—')}\n"
                f"📁 Total Groups: <b>{result['total']}</b>\n"
                f"✅ Sent: <b>{result['sent']}</b>\n"
                f"❌ Failed: <b>{result['failed']}</b>",
                call.message.chat.id, _st2_promo.message_id,
            )

        threading.Thread(target=do_promo, daemon=True).start()

    elif data_cb == "promo_cancel":
        bot.edit_message_text("❌ Promo cancel ho gaya.", call.message.chat.id, call.message.message_id)

    # ── Autoreply callbacks ───────────────────────────────────────────────────
    elif data_cb in ("autoreply_all_on", "autoreply_all_off"):
        d        = load()
        cfg      = d["config"]
        api_id   = cfg.get("api_id", 0)
        api_hash = cfg.get("api_hash", "")
        active   = [a for a in d["accounts"] if a.get("active") and a.get("verified")]
        turn_on  = (data_cb == "autoreply_all_on")
        if turn_on:
            for acc in active:
                phone = acc["phone"]
                if not _autoreply_active.get(phone):
                    _autoreply_active[phone] = True
                    _start_autoreply_thread(acc, api_id, api_hash)
            bot.edit_message_text(
                "🤖 <b>AI Auto-Reply — Sabhi Accounts ON!</b>\n\n"
                "✅ Ab jab koi aapko tag/mention karega,\n"
                "account automatically smart reply karega! 💬",
                call.message.chat.id, call.message.message_id,
            )
        else:
            for acc in active:
                phone = acc["phone"]
                _autoreply_active[phone] = False
                stop_autoreply(phone)
            bot.edit_message_text(
                "🤖 <b>AI Auto-Reply — Sabhi Accounts OFF!</b>\n\n"
                "❌ Auto-reply band ho gaya.",
                call.message.chat.id, call.message.message_id,
            )

# ═══════════════════════════════════════════════════════
#  WIZARD HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════

def _ask_buttons(ref_msg, uid):
    sess = broadcast_sessions.get(uid)
    if not sess:
        return
    btns      = sess.get("buttons", [])
    btns_text = ""
    if btns:
        btns_text = "\n\n<b>Current buttons:</b>\n" + "\n".join(
            f"🔘 {b['text']} → {b['url']}" for b in btns
        )
    kb = make_inline([
        [("➕ Button add karo", "btn_add")],
        [("✅ Done (aage bado)", "btn_done"), ("🗑 Clear all", "btn_clear")],
    ])
    try:
        bot.send_message(
            ref_msg.chat.id,
            f"<b>Step 3/4</b> — Inline Buttons{btns_text}\n\n"
            f"{'Aur buttons add karo ya Done karo.' if btns else 'URL buttons add karo (optional)'}",
            reply_markup=kb,
        )
    except Exception:
        pass

def _ask_target_type(ref_msg, uid):
    kb = make_inline([
        [("📢 All — Groups + DMs dono", "tgt_all")],
        [("👥 Sirf Groups / Channels",   "tgt_groups")],
        [("💬 Sirf DMs (personal chat)", "tgt_dms")],
    ])
    try:
        bot.send_message(
            ref_msg.chat.id,
            "<b>Step 4/4</b> — Kahan bhejoge?\n\n"
            "📢 <b>All</b> — Account jitne groups/DMs mein hai sab mein\n"
            "👥 <b>Groups</b> — Sirf groups aur channels\n"
            "💬 <b>DMs</b> — Sirf woh log jisse pehle baat ho chuki hai\n\n"
            "<i>Targets account ke dialogs se auto-detect hoga ✨</i>",
            reply_markup=kb,
        )
    except Exception:
        pass

def _show_preview(ref_msg, uid):
    sess   = broadcast_sessions.get(uid)
    d      = load()
    active = sum(1 for a in d["accounts"] if a.get("active") and a.get("verified"))
    mode   = sess.get("target_mode", "all")
    mode_label = {
        "all":   "📢 All — Groups + DMs dono",
        "group": "👥 Sirf Groups / Channels",
        "dm":    "💬 Sirf DMs (personal chat)",
    }.get(mode, mode)
    btn_preview   = ""
    if sess["buttons"]:
        btn_preview = "\n\n<b>Buttons:</b>\n" + "\n".join(
            f"🔘 {b['text']} → {b['url']}" for b in sess["buttons"]
        )
    media_preview = f"\n📎 Media: {sess['media_type'].title()}" if sess.get("media_type") else ""
    kb = make_inline([
        [("🚀 SEND KAR DO!", "confirm_send")],
        [("❌ Cancel", "confirm_cancel")],
    ])
    try:
        bot.send_message(
            ref_msg.chat.id,
            f"📋 <b>Broadcast Preview</b>\n\n"
            f"<b>Message:</b>\n<i>{sess['text'][:300]}{'...' if len(sess['text']) > 300 else ''}</i>"
            f"{media_preview}{btn_preview}\n\n"
            f"<b>Target Mode:</b> {mode_label}\n"
            f"<b>Active Accounts:</b> {active}\n\n"
            f"<i>Targets account ke dialogs se auto-fetch honge</i>",
            reply_markup=kb,
        )
    except Exception as e:
        bot.send_message(ref_msg.chat.id, f"Preview error: {e}\n\n/broadcast se restart karo.")

def _do_wizard_broadcast(ref_msg, uid):
    sess = broadcast_sessions.pop(uid, None)
    if not sess:
        bot.send_message(ref_msg.chat.id, "❌ Session nahi mila!"); return

    d      = load()
    active = sum(1 for a in d["accounts"] if a.get("active") and a.get("verified"))
    mode   = sess.get("target_mode", "all")
    mode_label = {"all": "All (Groups+DMs)", "group": "Sirf Groups", "dm": "Sirf DMs"}.get(mode, mode)

    st = bot.send_message(
        ref_msg.chat.id,
        f"⏳ <b>Broadcast chal raha hai...</b>\n\n"
        f"👤 Accounts: {active}\n"
        f"🎯 Mode: {mode_label}\n"
        f"📎 Media: {'Haan' if sess.get('media_type') else 'Nahi'}\n"
        f"🔘 Buttons: {len(sess['buttons'])}\n\n"
        f"<i>Dialogs fetch ho rahe hain...</i>",
    )

    media_local = None
    if sess.get("media_file_id"):
        try:
            file_info  = bot.get_file(sess["media_file_id"])
            file_url   = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
            ext        = os.path.splitext(file_info.file_path)[1] or ".bin"
            local_path = os.path.join(MEDIA_DIR, f"media_{gen_id()}{ext}")
            resp = requests.get(file_url, stream=True, timeout=60)
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            media_local = local_path
        except Exception as e:
            bot.send_message(ref_msg.chat.id, f"⚠️ Media download fail: {e}\nSirf text jayega.")

    payload = {
        "text":        sess["text"],
        "media_path":  media_local,
        "buttons":     sess["buttons"],
        "target_mode": mode,
        "parse_mode":  "html",
    }

    _last_edit = [0.0]
    _st_ref    = st
    _ref_msg_c = ref_msg

    def on_progress(acc_label, acc_sent, acc_failed, acc_total,
                    total_sent, total_failed, status_line):
        now = time.time()
        if now - _last_edit[0] < 3.0: return
        _last_edit[0] = now
        pct = f"{round(acc_sent/acc_total*100)}%" if acc_total else "..."
        try:
            bot.edit_message_text(
                f"⏳ <b>Broadcast Live...</b>\n\n"
                f"👤 <b>{acc_label}</b>\n"
                f"  ✅ Sent: {acc_sent}  ❌ Failed: {acc_failed}  ({pct} of {acc_total})\n\n"
                f"📊 <b>Total:</b> ✅{total_sent}  ❌{total_failed}\n"
                f"<i>{status_line}</i>",
                _ref_msg_c.chat.id, _st_ref.message_id,
            )
        except Exception:
            pass

    def do():
        result = run_async(run_broadcast(payload, progress_cb=on_progress))
        if media_local and os.path.exists(media_local):
            try: os.remove(media_local)
            except Exception: pass

        if not result["ok"]:
            bot.edit_message_text(
                f"❌ <b>Broadcast fail!</b>\n{result['error']}",
                _ref_msg_c.chat.id, _st_ref.message_id,
            )
            return

        acc_lines = []
        for s in result.get("acc_stats", []):
            if s.get("error") and s.get("sent", 0) == 0:
                acc_lines.append(f"⚠️ <b>{s['label']}</b> — {s['error']}")
            else:
                new_t = s.get("total", 0) - s.get("skipped", 0)
                pct   = round(s["sent"] / new_t * 100) if new_t else 0
                skip_txt = f"  ⏭ skip:{s['skipped']}" if s.get("skipped") else ""
                acc_lines.append(
                    f"👤 <b>{s['label']}</b>\n"
                    f"   ✅ {s['sent']}  ❌ {s['failed']}{skip_txt}  / {new_t} naye  ({pct}%)"
                )
        acc_report = "\n".join(acc_lines) if acc_lines else "—"
        emoji      = "✅" if result["failed"] == 0 else "⚠️"
        skip_line  = (f"⏭ Duplicate Skip: <b>{result['skipped']}</b>\n") if result.get("skipped") else ""
        summary    = (
            f"{emoji} <b>Broadcast Complete!</b>\n\n"
            f"🎯 Unique Targets: <b>{result.get('unique_targets', result['sent'])}</b>\n"
            f"✅ Total Sent: <b>{result['sent']}</b>\n"
            f"❌ Total Failed: <b>{result['failed']}</b>\n"
            f"{skip_line}"
        )
        final = summary + f"\n<b>Account-wise:</b>\n{acc_report}"

        if len(final) <= 4000:
            bot.edit_message_text(final, _ref_msg_c.chat.id, _st_ref.message_id)
        else:
            bot.edit_message_text(summary, _ref_msg_c.chat.id, _st_ref.message_id)
            chunk, chunks = [], []
            for line in acc_lines:
                chunk.append(line)
                if len("\n".join(chunk)) > 3500:
                    chunks.append("\n".join(chunk[:-1]))
                    chunk = [line]
            if chunk:
                chunks.append("\n".join(chunk))
            for i, ch in enumerate(chunks):
                bot.send_message(
                    _ref_msg_c.chat.id,
                    f"<b>Account Report ({i+1}/{len(chunks)}):</b>\n\n{ch}",
                )

    threading.Thread(target=do, daemon=True).start()

def _run_clone(ref_msg, target_id):
    st = bot.reply_to(
        ref_msg,
        f"⏳ <b>Profile Clone shuru...</b>\n\n"
        f"🔍 User ID <code>{target_id}</code> ki profile fetch ho rahi hai...",
    )
    _last_cl2_edit = [time.time()]
    _st_ref        = st
    _ref_msg_c     = ref_msg

    def on_clone_progress(status, idx, total):
        now = time.time()
        if now - _last_cl2_edit[0] < 2.5: return
        _last_cl2_edit[0] = now
        try:
            bot.edit_message_text(
                f"⏳ <b>Clone Live...</b>\n\n"
                f"📋 {idx}/{total} accounts done\n<i>{status}</i>",
                _ref_msg_c.chat.id, _st_ref.message_id,
            )
        except Exception: pass

    def do_clone():
        result = run_async(run_clone_profile(target_id, progress_cb=on_clone_progress))
        if not result["ok"]:
            bot.edit_message_text(f"❌ <b>Clone fail!</b>\n{result['error']}",
                                  _ref_msg_c.chat.id, _st_ref.message_id); return
        photo_txt = "✅ Photo copy ho gayi!" if result["had_photo"] else "⚠️ Photo nahi mili"
        bio_val   = result.get("about", "")
        bio_short = (bio_val[:60] + "...") if len(bio_val) > 60 else bio_val
        bio_txt   = f"✅ Bio: <i>{bio_short}</i>" if bio_val else "⚠️ Bio nahi mili"
        emoji     = "✅" if result["failed"] == 0 else "⚠️"
        log_txt   = "\n".join(result["log"][-12:])
        bot.edit_message_text(
            f"{emoji} <b>Profile Clone Complete!</b>\n\n"
            f"👤 Naam: <b>{result['first_name']} {result['last_name']}</b>\n"
            f"📝 {bio_txt}\n"
            f"🖼 {photo_txt}\n\n"
            f"✅ Done: <b>{result['done']}</b>  ❌ Failed: <b>{result['failed']}</b>\n\n"
            f"<b>Log:</b>\n{log_txt}",
            _ref_msg_c.chat.id, _st_ref.message_id,
        )

    threading.Thread(target=do_clone, daemon=True).start()

# ═══════════════════════════════════════════════════════
#  UNIFIED MESSAGE HANDLER (state machine)
# ═══════════════════════════════════════════════════════

@bot.message_handler(content_types=["text", "photo", "video", "document"])
def handle_message(msg):
    uid  = msg.from_user.id
    text = msg.text or msg.caption or ""

    # ── ReplyRaid: bot-level detection ────────────────────────────────────────
    # Agar message sender raid list mein hai, toh SABHI active accounts reply
    # karenge (Telethon watchers ke alawa — bot jo bhi group/DM mein dekh sake)
    if (msg.from_user
            and not msg.from_user.is_bot
            and msg.from_user.id in _replyraid_users
            and _replyraid_active):   # koi thread running hai tabhi
        try:
            _cid  = msg.chat.id
            _rmid = msg.message_id
            threading.Thread(
                target=_fire_all_raid_replies,
                args=(_cid, _rmid),
                daemon=True
            ).start()
        except Exception:
            pass
    # ── End ReplyRaid bot-level detection ────────────────────────────────────

    # Cancel shortcut
    if text == "❌ Cancel":
        clear_state(uid)
        broadcast_sessions.pop(uid, None)
        tagall_sessions.pop(uid, None)
        promo_sessions.pop(uid, None)
        clone_sessions.pop(uid, None)
        bot.send_message(msg.chat.id, "❌ Cancel ho gaya.", reply_markup=main_kb())
        return

    # ── TagAll: group number selection ────────────────────────────────────────
    tsess = tagall_sessions.get(uid)
    if tsess and tsess["step"] == "select_group" and msg.text:
        try:
            idx    = int(msg.text.strip()) - 1
            groups = tsess["groups"]
            if 0 <= idx < len(groups):
                sel           = groups[idx]
                tsess["selected"] = sel
                tsess["step"]     = "select_mode"
                kb = make_inline([
                    [("🌅 Greeting (Good Morning/Night)", "tagall_mode_greeting")],
                    [("📜 Shayri (AI shayri bhejo)",      "tagall_mode_shayri")],
                    [("❌ Cancel",                          "tagall_cancel")],
                ])
                bot.reply_to(msg,
                    f"🏷 <b>Tag All — Mode Chuno</b>\n\n"
                    f"👥 Group: <b>{sel['label']}</b>\n\n"
                    f"Har member ko kaunsa message bhejoge?",
                    reply_markup=kb,
                )
            else:
                bot.reply_to(msg, f"❌ 1 se {len(groups)} ke beech number dalo")
        except ValueError:
            bot.reply_to(msg, "❌ Sirf number type karo (jaise: 3)")
        return

    # ── Promo setup wizard ────────────────────────────────────────────────────
    psess = promo_sessions.get(uid)
    if psess and msg.text:
        step = psess["step"]
        if step == "text":
            psess["text"] = msg.text.strip()
            psess["step"] = "link"
            bot.reply_to(msg,
                "📣 <b>Group Promo Setup</b>\n\n"
                "<b>Step 2/2</b> — Apne group ka invite link bhejo\n\n"
                "Example: <code>https://t.me/+abcXYZ123</code>\n\n"
                "Ab link type karo 👇",
            )
            return
        elif step == "link":
            link = msg.text.strip()
            if not link.startswith("http"):
                bot.reply_to(msg, "❌ Link https:// se shuru hona chahiye!"); return
            psess["link"] = link
            promo_sessions.pop(uid, None)
            d = load()
            d["config"]["promo_text"] = psess["text"]
            d["config"]["promo_link"] = link
            save(d)
            bot.reply_to(msg,
                "✅ <b>Promo Save Ho Gaya!</b>\n\n"
                f"📝 Text: {psess['text'][:60]}{'...' if len(psess['text'])>60 else ''}\n"
                f"🔗 Link: {link}\n\n"
                "Ab /promo se sabhi groups mein promote karo! 📣",
            )
            return

    # ── Profile clone: waiting for user ID ───────────────────────────────────
    if clone_sessions.get(uid) and msg.text:
        tid = msg.text.strip()
        clone_sessions.pop(uid, None)
        _run_clone(msg, tid)
        return

    # ── Dialog Broadcast Wizard steps ────────────────────────────────────────
    sess = broadcast_sessions.get(uid)
    if sess:
        step = sess.get("step")

        if step == "media_upload":
            mt      = sess["media_type"]
            file_id = None
            if mt == "photo" and msg.photo:
                file_id = msg.photo[-1].file_id
            elif mt == "video" and msg.video:
                file_id = msg.video.file_id
            elif mt == "document" and msg.document:
                file_id = msg.document.file_id
            if not file_id:
                bot.reply_to(msg, f"❌ {mt.title()} bhejo ya /broadcast se restart karo"); return
            sess["media_file_id"] = file_id
            sess["step"]          = "text"
            bot.reply_to(msg,
                "✅ Media save!\n\n"
                "<b>Step 2/4</b> — Message text likho\n\n"
                "HTML formatting:\n"
                "<code>&lt;b&gt;Bold&lt;/b&gt;</code>  <code>&lt;i&gt;Italic&lt;/i&gt;</code>\n\n"
                "Text type karo 👇",
            )
            return

        elif step == "text":
            if not msg.text:
                bot.reply_to(msg, "❌ Text likhna hai!"); return
            sess["text"] = msg.text
            sess["step"] = "buttons"
            _ask_buttons(msg, uid)
            return

        elif step == "btn_input":
            if not msg.text:
                bot.reply_to(msg, "❌ Text mein button likho!"); return
            lines  = [l.strip() for l in msg.text.strip().splitlines() if "|" in l]
            added  = 0
            for line in lines:
                parts    = line.split("|", 1)
                btn_text = parts[0].strip()
                btn_url  = parts[1].strip() if len(parts) > 1 else ""
                if btn_text and btn_url and btn_url.startswith("http"):
                    sess["buttons"].append({"text": btn_text, "url": btn_url})
                    added += 1
            if added:
                sess["step"] = "buttons"
                _ask_buttons(msg, uid)
            else:
                bot.reply_to(msg,
                    "❌ Format galat!\n\n"
                    "Sahi format:\n<code>Button Text | https://link.com</code>",
                )
            return

    # ── user_state: add account, scrape, targeted bc, admin ──────────────────
    st   = get_state(uid)
    if not st:
        return
    step = st.get("step")
    data = st.get("data", {})

    # ADD ACCOUNT: phone
    if step == "add_phone":
        phone = text.strip()
        if not phone.startswith("+"):
            bot.send_message(msg.chat.id,
                "❌ Phone number + se shuru hona chahiye.\nJaise: <code>+919876543210</code>")
            return
        set_state(uid, "add_otp", {"phone": phone})
        bot.send_message(msg.chat.id, f"📱 <code>{phone}</code>\n\nOTP bhej raha hoon...")

        def send_otp():
            d2   = load()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client = get_client(phone, d2["config"]["api_id"], d2["config"]["api_hash"])
            try:
                loop.run_until_complete(client.connect())
                result = loop.run_until_complete(client.send_code_request(phone))
                st2 = get_state(uid)
                if st2:
                    st2["data"]["phone_code_hash"] = result.phone_code_hash
                bot.send_message(msg.chat.id,
                    "✅ OTP bheja gaya!\n\nTelegram pe aaya OTP code bhejo:")
            except Exception as e:
                bot.send_message(msg.chat.id, f"❌ OTP send fail: {e}")
                clear_state(uid)
            finally:
                safe_disconnect(client, loop)
                loop.close()

        threading.Thread(target=send_otp, daemon=True).start()

    # ADD ACCOUNT: OTP
    elif step == "add_otp":
        otp             = text.strip()
        phone           = data["phone"]
        phone_code_hash = data.get("phone_code_hash", "")
        bot.send_message(msg.chat.id, "🔐 Verify kar raha hoon...")

        def verify_otp():
            d2   = load()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client = get_client(phone, d2["config"]["api_id"], d2["config"]["api_hash"])
            try:
                loop.run_until_complete(client.connect())
                loop.run_until_complete(
                    client.sign_in(phone, otp, phone_code_hash=phone_code_hash)
                )
                me   = loop.run_until_complete(client.get_me())
                name = f"{getattr(me,'first_name','') or ''} {getattr(me,'last_name','') or ''}".strip()
                # StringSession save karo — Heroku restart ke baad bhi kaam karega
                sess_str = client.session.save()
                adder_name = ""
                try:
                    adder = bot.get_chat(uid)
                    adder_name = adder.first_name or adder.username or ""
                except Exception:
                    pass
                entry = {"phone": phone, "label": name or phone, "verified": True, "active": True,
                         "session_string": sess_str,
                         "owner_id": str(uid),
                         "owner_name": adder_name,
                         "added_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
                d2["accounts"] = [a for a in d2["accounts"] if a["phone"] != phone]
                d2["accounts"].append(entry)
                # Account owner record karo
                d2.setdefault("account_owners", {})[phone] = str(uid)
                save(d2)
                # ── Automatic Userbot: naya account turant watcher thread shuru kare ──
                threading.Thread(
                    target=_auto_start_userbot,
                    args=(entry, msg.chat.id),
                    daemon=True
                ).start()
                bot.send_message(msg.chat.id,
                    f"✅ <b>Account add ho gaya!</b>\n\n"
                    f"📱 Phone: <code>{phone}</code>\n"
                    f"👤 Name: <b>{name}</b>\n"
                    f"🤖 Userbot: <b>AUTO-START ho raha hai...</b>\n"
                    f"🔑 Owner: <code>{uid}</code>\n\n"
                    f"✅ Session saved — bot restart ke baad bhi dobara login nahi karna!",
                    reply_markup=main_kb(), parse_mode="HTML")
                clear_state(uid)
            except SessionPasswordNeededError:
                set_state(uid, "add_2fa", {"phone": phone})
                bot.send_message(msg.chat.id,
                    "🔒 <b>2FA ON hai</b>\n\n2FA password bhejo:")
            except (PhoneCodeInvalidError, PhoneCodeExpiredError) as e:
                bot.send_message(msg.chat.id,
                    f"❌ OTP galat ya expire: {type(e).__name__}\n/add se dobara try karo.")
                clear_state(uid)
            except Exception as e:
                bot.send_message(msg.chat.id, f"❌ Error: {e}")
                clear_state(uid)
            finally:
                safe_disconnect(client, loop)
                loop.close()

        threading.Thread(target=verify_otp, daemon=True).start()

    # ADD ACCOUNT: 2FA
    elif step == "add_2fa":
        password = text.strip()
        phone    = data["phone"]
        bot.send_message(msg.chat.id, "🔐 2FA verify kar raha hoon...")

        def verify_2fa():
            d2   = load()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client = get_client(phone, d2["config"]["api_id"], d2["config"]["api_hash"])
            try:
                loop.run_until_complete(client.connect())
                loop.run_until_complete(client.sign_in(password=password))
                me   = loop.run_until_complete(client.get_me())
                name = f"{getattr(me,'first_name','') or ''} {getattr(me,'last_name','') or ''}".strip()
                # StringSession save karo
                sess_str = client.session.save()
                adder_name = ""
                try:
                    adder = bot.get_chat(uid)
                    adder_name = adder.first_name or adder.username or ""
                except Exception:
                    pass
                entry = {"phone": phone, "label": name or phone, "verified": True, "active": True,
                         "session_string": sess_str,
                         "owner_id": str(uid),
                         "owner_name": adder_name,
                         "added_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
                d2["accounts"] = [a for a in d2["accounts"] if a["phone"] != phone]
                d2["accounts"].append(entry)
                # Account owner record karo
                d2.setdefault("account_owners", {})[phone] = str(uid)
                save(d2)
                # ── Automatic Userbot: naya account turant watcher thread shuru kare ──
                threading.Thread(
                    target=_auto_start_userbot,
                    args=(entry, msg.chat.id),
                    daemon=True
                ).start()
                bot.send_message(msg.chat.id,
                    f"✅ <b>Account add ho gaya! (2FA)</b>\n\n"
                    f"📱 Phone: <code>{phone}</code>\n"
                    f"👤 Name: <b>{name}</b>\n"
                    f"🤖 Userbot: <b>AUTO-START ho raha hai...</b>\n"
                    f"🔑 Owner: <code>{uid}</code>\n\n"
                    f"✅ Session saved — bot restart ke baad bhi dobara login nahi karna!",
                    reply_markup=main_kb(), parse_mode="HTML")
                clear_state(uid)
            except Exception as e:
                bot.send_message(msg.chat.id, f"❌ 2FA Error: {e}")
                clear_state(uid)
            finally:
                safe_disconnect(client, loop)
                loop.close()

        threading.Thread(target=verify_2fa, daemon=True).start()

    # SCRAPE: group
    elif step == "scrape_group":
        group = text.strip()
        if group.startswith("https://t.me/"):
            grp   = group.split("https://t.me/")[1].split("/")[0]
            group = "@" + grp if not grp.startswith("+") else "https://t.me/" + grp
        elif not group.startswith("@") and not group.startswith("-") and not group.lstrip("-").isdigit():
            group = "@" + group

        # ── BLACKLIST CHECK ──────────────────────────────────────────────
        if is_blacklisted(group):
            bot.send_message(msg.chat.id,
                f"🚫 <b>Group Blacklisted!</b>\n\n"
                f"<code>{group}</code> ko scrape nahi kar sakte.\n"
                "Is group ko blacklist se hatao: /unblacklist",
                reply_markup=main_kb())
            clear_state(uid)
            return

        phone     = data["phone"]
        chat_id_s = msg.chat.id
        clear_state(uid)

        st_msg = bot.send_message(
            chat_id_s,
            f"🔍 <b>Scraping shuru ho gaya!</b>\n\n"
            f"🔗 Group: <code>{group}</code>\n"
            f"📱 Account: <code>{phone}</code>\n\n"
            "🎵 Step 0: Music bots join kar rahe hain...\n"
            "━━━━━━━━━━━━━━━━━\n"
            "👥 Source 1/3: Member list...\n"
            "💬 Source 2/3: Active chat...\n"
            "📊 Source 3/3: Polls/Quiz...\n"
            "━━━━━━━━━━━━━━━━━\n"
            "⏳ <i>Processing...</i>",
        )

        _owner_uid = uid  # Capture scope

        def run_scrape():
            d2   = load()
            cfg2 = d2["config"]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # ── STEP 0: Music bots ko target group mein add karo ────────
            music_bots = cfg2.get("music_bot_usernames", [])
            if music_bots:
                try:
                    bot_results = loop.run_until_complete(
                        add_music_bots_to_group(
                            phone, cfg2["api_id"], cfg2["api_hash"], group
                        )
                    )
                    music_log = " | ".join(
                        f"{r.get('bot','?')}: {r.get('status','?')}"
                        for r in bot_results
                    )
                    try:
                        bot.edit_message_text(
                            f"🔍 <b>Scraping chal raha hai...</b>\n\n"
                            f"🔗 <code>{group}</code>\n\n"
                            f"🎵 Music bots: {music_log}\n"
                            "⏳ <i>Member list fetch ho raha hai...</i>",
                            chat_id_s, st_msg.message_id,
                        )
                    except Exception:
                        pass
                except Exception:
                    pass

            conn  = get_db()
            cur2  = conn.execute(
                "INSERT INTO scrape_jobs (group_target,account_phone,owner_id,status) VALUES (?,?,?,?)",
                (group, phone, str(_owner_uid), "running"),
            )
            scrape_id = cur2.lastrowid
            conn.commit()
            conn.close()

            log_lines = []

            def on_progress(line):
                log_lines.append(line)
                try:
                    preview = "\n".join(log_lines[-6:])
                    bot.edit_message_text(
                        f"🔍 <b>Scraping chal raha hai...</b>\n\n"
                        f"🔗 <code>{group}</code>\n\n"
                        f"{preview}\n\n"
                        "⏳ <i>Kuch minute lag sakte hain...</i>",
                        chat_id_s, st_msg.message_id,
                    )
                except Exception:
                    pass

            total, stats, err = loop.run_until_complete(
                scrape_group_members(
                    phone, d2["config"]["api_id"], d2["config"]["api_hash"],
                    group, scrape_id, progress_cb=on_progress,
                )
            )
            loop.close()

            if err:
                try:
                    bot.edit_message_text(
                        f"❌ <b>Scrape fail!</b>\n\n<code>{err}</code>",
                        chat_id_s, st_msg.message_id,
                    )
                except Exception:
                    bot.send_message(chat_id_s, f"❌ Scrape fail: {err}",
                                     reply_markup=main_kb())
            else:
                s = stats
                try:
                    bot.edit_message_text(
                        f"✅ <b>Scraping Complete!</b>\n\n"
                        f"🔗 Group: <code>{group}</code>\n"
                        f"━━━━━━━━━━━━━━━━━\n"
                        f"👥 Member list se:   <b>{s.get('member_list', 0)}</b>\n"
                        f"💬 Active chatters:  <b>{s.get('active_chat', 0)}</b>\n"
                        f"📊 Poll/Quiz voters: <b>{s.get('poll_voters', 0)}</b>"
                        + (f" ({s.get('polls_found',0)} polls)" if s.get('polls_found') else "") + "\n"
                        f"🚫 Inactive skip:    <b>{s.get('skipped_inactive', 0)}</b>\n"
                        f"━━━━━━━━━━━━━━━━━\n"
                        f"✅ <b>Total Active: {total}</b>\n"
                        f"🆔 Scrape ID: <b>{scrape_id}</b>\n\n"
                        "Ab /targeted se DM bhej sakte ho!\n"
                        "Ya /groupadd se contact add + invite karo!",
                        chat_id_s, st_msg.message_id,
                    )
                except Exception:
                    bot.send_message(
                        chat_id_s,
                        f"✅ <b>Scraping Complete!</b>\n"
                        f"👥 Total Active: <b>{total}</b>\n"
                        f"🆔 Scrape ID: <b>{scrape_id}</b>",
                        reply_markup=main_kb(),
                    )

        threading.Thread(target=run_scrape, daemon=True).start()

    # POLL SCRAPE: group link
    elif step == "ps_group":
        group = text.strip() if text else ""
        if not group:
            bot.send_message(msg.chat.id, "❌ Group link ya username bhejo.", reply_markup=cancel_kb())
            return
        if group.startswith("https://t.me/"):
            grp   = group.split("https://t.me/")[1].split("/")[0]
            group = "@" + grp if not grp.startswith("+") else "https://t.me/" + grp
        elif not group.startswith("@") and not group.startswith("-") and not group.lstrip("-").isdigit():
            group = "@" + group

        phone = data["phone"]
        data["group"] = group
        set_state(uid, "ps_finding", data)

        bot.send_message(msg.chat.id,
            f"🔍 <b>Polls dhundh raha hoon...</b>\n"
            f"Group: <code>{group}</code>\n\n"
            "⏳ Poori history scan ho rahi hai (InputMessagesFilterPoll)...\n"
            "Thoda ruko...")

        def find_polls_thread():
            d2   = load()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            polls, err = loop.run_until_complete(
                find_polls_in_chat(
                    phone, d2["config"]["api_id"], d2["config"]["api_hash"], group
                )
            )
            loop.close()

            if err:
                bot.send_message(msg.chat.id,
                    f"❌ Error: <code>{err}</code>", reply_markup=main_kb())
                clear_state(uid)
                return
            if not polls:
                bot.send_message(msg.chat.id,
                    "❌ Is group mein koi poll/quiz nahi mili.", reply_markup=main_kb())
                clear_state(uid)
                return

            # Polls list dikhao — inline buttons
            mk2 = InlineKeyboardMarkup()
            for p in polls[:20]:   # max 20 show karo
                label = f"{p['type']} | {p['total_voters']} votes | {p['date']}\n{p['question']}"
                mk2.add(InlineKeyboardButton(
                    f"{p['type']} [{p['total_voters']} votes] {p['date']} — {p['question'][:40]}",
                    callback_data=f"ps_poll_{p['msg_id']}"
                ))
                # poll label state mein store karo (latest state)
                data["poll_label"] = p["question"]   # last one, overwritten; handled per-click below
            mk2.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel_cb"))

            # State update: store polls map for label lookup
            data["polls_map"] = {str(p["msg_id"]): p["question"] for p in polls}
            set_state(uid, "ps_select", data)

            shown = len(polls[:20])
            total_found = len(polls)
            bot.send_message(msg.chat.id,
                f"📋 <b>{total_found} Poll/Quiz mili</b> group mein!\n"
                f"{'(Pehli 20 dikhai ja rahi hain)' if total_found > 20 else ''}\n\n"
                "👇 Kaunsi poll ke voters scrape karne hain?",
                reply_markup=mk2)

        threading.Thread(target=find_polls_thread, daemon=True).start()

    # TARGETED DM: message/media input
    elif step == "bc_message":
        media_type = None
        file_id    = None
        if msg.content_type == "photo":
            media_type = "photo"
            file_id    = msg.photo[-1].file_id
        elif msg.content_type == "video":
            media_type = "video"
            file_id    = msg.video.file_id

        data["message"]    = text or ""
        data["media_type"] = media_type
        data["file_id"]    = file_id
        set_state(uid, "bc_per_acc", data)

        mk = InlineKeyboardMarkup()
        mk.row(
            InlineKeyboardButton("3",  callback_data="bc_perAcc_3"),
            InlineKeyboardButton("5",  callback_data="bc_perAcc_5"),
            InlineKeyboardButton("10", callback_data="bc_perAcc_10"),
        )
        mk.row(
            InlineKeyboardButton("15", callback_data="bc_perAcc_15"),
            InlineKeyboardButton("20", callback_data="bc_perAcc_20"),
        )
        media_line = f"📎 Media: {media_type}\n" if media_type else ""
        bot.send_message(
            msg.chat.id,
            f"✅ Message/Media receive hua!\n{media_line}\n"
            "Har account se <b>kitne members</b> ko DM karna hai?",
            reply_markup=mk,
        )

    # GROUP ADD CAMPAIGN: step 1 — target group (jisme add karna hai)
    elif step == "ga_group":
        grp = text.strip() if text else ""
        if not grp:
            bot.send_message(msg.chat.id,
                "❌ Group link/username bhejo!", reply_markup=cancel_kb())
            return
        if grp.startswith("https://t.me/"):
            slug = grp.split("https://t.me/")[1].split("/")[0]
            grp  = ("https://t.me/" + slug) if slug.startswith("+") else ("@" + slug)
        elif not grp.startswith("@") and not grp.startswith("-") and not grp.lstrip("-").isdigit():
            grp = "@" + grp
        data["target_group"] = grp
        set_state(uid, "ga_link", data)
        bot.send_message(
            msg.chat.id,
            f"✅ Target group: <code>{grp}</code>\n\n"
            "🔗 <b>Invite link bhejo</b> (privacy wale members ko DM hogi):\n"
            "<i>Example: https://t.me/+AbcXyzInvite</i>\n\n"
            "📌 Skip karna ho to <code>/skip</code> bhejo",
            reply_markup=cancel_kb(),
        )

    # GROUP ADD CAMPAIGN: step 2 — invite link (fallback for privacy members)
    elif step == "ga_link":
        link = (text.strip() if text else "")
        if link.lower() in ["/skip", "skip"]:
            data["invite_link"] = ""
        elif link and not link.startswith("https://t.me/"):
            bot.send_message(msg.chat.id,
                "❌ Valid Telegram invite link bhejo ya /skip karo!\n"
                "<i>Example: https://t.me/+AbcXyzInvite</i>",
                reply_markup=cancel_kb())
            return
        else:
            data["invite_link"] = link
        set_state(uid, "ga_per_acc", data)
        mk = InlineKeyboardMarkup()
        mk.row(
            InlineKeyboardButton("3",  callback_data="ga_perAcc_3"),
            InlineKeyboardButton("5",  callback_data="ga_perAcc_5"),
            InlineKeyboardButton("10", callback_data="ga_perAcc_10"),
        )
        mk.row(
            InlineKeyboardButton("15", callback_data="ga_perAcc_15"),
            InlineKeyboardButton("20", callback_data="ga_perAcc_20"),
        )
        link_note = (
            f"🔗 Invite Link: <code>{data['invite_link'][:60]}</code>"
            if data.get("invite_link")
            else "🔗 Invite link: <b>Skip (privacy wale members ko link nahi jayegi)</b>"
        )
        bot.send_message(
            msg.chat.id,
            f"✅ {link_note}\n\n"
            "🔢 <b>Har account se kitne members add karein?</b>",
            reply_markup=mk,
        )

    # ADMIN ADD: ID
    elif step == "admin_add_id":
        tid = text.strip()
        if not tid.isdigit():
            bot.send_message(msg.chat.id, "❌ Sirf number bhejo (Telegram User ID).")
            return
        set_state(uid, "admin_add_label", {"tid": tid})
        bot.send_message(msg.chat.id, "✍ Admin ka naam/label bhejo:")

    elif step == "admin_add_label":
        label = text.strip()
        tid   = data["tid"]
        conn  = get_db()
        try:
            conn.execute("INSERT INTO admins (telegram_user_id,label) VALUES (?,?)", (tid, label))
            conn.commit()
            bot.send_message(msg.chat.id,
                f"✅ Admin add ho gaya!\nID: <code>{tid}</code>\nLabel: {label}",
                reply_markup=main_kb())
        except sqlite3.IntegrityError:
            bot.send_message(msg.chat.id, "❌ Yeh ID pehle se admin hai!", reply_markup=main_kb())
        conn.close()
        clear_state(uid)

# ═══════════════════════════════════════════════════════
#  CLI — ACCOUNT OTP LOGIN
# ═══════════════════════════════════════════════════════

async def add_account_otp():
    hdr("Account Add — OTP Login")
    data     = load()
    cfg      = data["config"]
    api_id   = cfg.get("api_id", 0)
    api_hash = cfg.get("api_hash", "")
    if not api_id or not api_hash:
        err("API_ID / API_HASH set nahi hai!"); info("Setup → API Credentials"); pause(); return

    phone = input(f"  {W}Phone:{NC} {DIM}(+919876543210){NC}: ").strip()
    if not phone: err("Phone khali!"); pause(); return
    for a in data["accounts"]:
        if a["phone"] == phone: warn("Pehle se add hai!"); pause(); return

    label = input(f"  {W}Label:{NC} {DIM}(optional){NC}: ").strip()
    print(f"\n  {Y}OTP bhej raha hai...{NC}")

    client = get_client(phone, api_id, api_hash)
    try:
        await client.connect()
        await client.send_code_request(phone)
        ok("OTP bhej diya! Telegram app dekho.")
        otp = input(f"  {W}OTP:{NC} ").strip()
        if not otp: err("OTP khali!"); await client.disconnect(); pause(); return
        try:
            await client.sign_in(phone, otp)
        except SessionPasswordNeededError:
            print(f"\n  {Y}2FA required!{NC}")
            tfa = input(f"  {W}2FA Password:{NC} ").strip()
            await client.sign_in(password=tfa)
        me   = await client.get_me()
        name = f"{me.first_name or ''} {me.last_name or ''}".strip()
        sess_str = client.session.save()
        data["accounts"].append({
            "id": gen_id(), "phone": phone, "label": label or name or phone,
            "name": name, "active": True, "verified": True,
            "addedAt": datetime.now().isoformat(),
            "session_string": sess_str,
        })
        save(data)
        ok(f"Account add! Name: {name}  Phone: {phone}")
    except PhoneCodeInvalidError: err("OTP galat!")
    except PhoneCodeExpiredError: err("OTP expire ho gaya!")
    except Exception as e: err(f"Error: {e}")
    finally:
        try: await client.disconnect()
        except Exception: pass
    pause()

# ═══════════════════════════════════════════════════════
#  CLI MENUS
# ═══════════════════════════════════════════════════════

def setup_menu():
    while True:
        hdr("Setup")
        data = load(); cfg = data["config"]
        api_ok = f"{G}Set ✓{NC}" if cfg.get("api_id") and cfg.get("api_hash") else f"{R}Not Set ✗{NC}"
        tok_ok = f"{G}Set ✓{NC}" if cfg.get("bot_token") else f"{R}Not Set ✗{NC}"
        adm_ok = f"{G}{len(cfg.get('admin_ids',[]))} admin(s){NC}" if cfg.get("admin_ids") else f"{R}Not Set ✗{NC}"
        print(f"  API Credentials: {api_ok}")
        print(f"  Bot Token:       {tok_ok}")
        print(f"  Admin IDs:       {adm_ok}")
        sep()
        print(f"  {W}1.{NC} API ID + Hash   {DIM}(my.telegram.org){NC}")
        print(f"  {W}2.{NC} Bot Token       {DIM}(@BotFather){NC}")
        print(f"  {W}3.{NC} Admin IDs       {DIM}(apna Telegram ID){NC}")
        print(f"\n  {W}0.{NC} Back")
        c = input(f"\n  {W}Chuno:{NC} ").strip()
        if c == "0": break
        elif c == "1":
            hdr("API Credentials")
            info("https://my.telegram.org → Login → API development tools → Create App")
            ai = input(f"\n  {W}API ID:{NC} ").strip()
            ah = input(f"  {W}API Hash:{NC} ").strip()
            if ai and ah:
                try:
                    cfg["api_id"] = int(ai); cfg["api_hash"] = ah
                    save(data); ok("Save ho gaya!")
                except ValueError: err("API ID number hona chahiye!")
            else: warn("Khali, skip.")
            pause()
        elif c == "2":
            hdr("Bot Token")
            info("Telegram → @BotFather → /newbot → Token copy karo")
            tok = input(f"\n  {W}Token:{NC} ").strip()
            if tok:
                print(f"  {Y}Verify ho raha hai...{NC}")
                try:
                    r = requests.get(f"https://api.telegram.org/bot{tok}/getMe", timeout=10).json()
                    if r.get("ok"):
                        cfg["bot_token"] = tok; save(data)
                        ok(f"Bot: {r['result']['first_name']} (@{r['result']['username']})")
                    else: err(f"Invalid: {r.get('description')}")
                except Exception as e: err(f"Error: {e}")
            else: warn("Khali, skip.")
            pause()
        elif c == "3":
            hdr("Admin IDs")
            info("Bot ko /myid bhejo → ID milega")
            existing = cfg.get("admin_ids", [])
            if existing: info(f"Current: {existing}")
            raw = input(f"\n  {W}IDs:{NC} ").strip()
            if raw:
                cfg["admin_ids"] = [int(x.strip()) if x.strip().isdigit() else x.strip()
                                    for x in raw.split(",") if x.strip()]
                save(data); ok(f"Save: {cfg['admin_ids']}")
            else: warn("Khali, skip.")
            pause()

def accounts_menu():
    while True:
        data = load(); accs = data["accounts"]
        if sync_account_status(data):
            save(data)
        active = sum(1 for a in accs if a.get("active") and a.get("verified"))
        hdr(f"Accounts  ({active} active / {len(accs)} total)")
        print(f"  {W}1.{NC} Add Account  {DIM}(OTP login){NC}")
        print(f"  {W}2.{NC} List")
        print(f"  {W}3.{NC} Activate / Deactivate")
        print(f"  {W}4.{NC} Delete")
        print(f"\n  {W}0.{NC} Back")
        c = input(f"\n  {W}Chuno:{NC} ").strip()
        if c == "0": break
        elif c == "1": asyncio.run(add_account_otp())
        elif c == "2":
            hdr("Accounts List")
            if not accs: warn("Koi account nahi."); pause(); continue
            for i, a in enumerate(accs, 1):
                has_s = session_exists(a["phone"])
                if a.get("active") and a.get("verified") and has_s:
                    st_txt = f"{G}🟢 Active ✓{NC}"
                elif not has_s:
                    st_txt = f"{R}🔴 No Session{NC}"
                else:
                    st_txt = f"{Y}🟡 Inactive{NC}"
                name = a.get("label") or a.get("name") or a["phone"]
                print(f"  {W}{i}.{NC} {name}  {st_txt}")
                print(f"     {DIM}{a['phone']}{NC}")
                sep()
            pause()
        elif c == "3":
            hdr("Toggle Active/Inactive")
            if not accs: warn("Koi account nahi."); pause(); continue
            for i, a in enumerate(accs, 1):
                has_s = session_exists(a["phone"])
                if not has_s: st = f"{R}No Session{NC}"
                elif a.get("active"): st = f"{G}ON ✓{NC}"
                else: st = f"{Y}OFF{NC}"
                name = a.get("label") or a.get("name") or a["phone"]
                print(f"  {W}{i}.{NC} {name}  [{st}]")
            print(f"\n  {W}0.{NC} Back")
            ch = input(f"\n  {W}Number:{NC} ").strip()
            if ch == "0": continue
            try:
                idx = int(ch) - 1
                if 0 <= idx < len(accs):
                    a     = accs[idx]
                    has_s = session_exists(a["phone"])
                    if not has_s:
                        err("Session file nahi hai — pehle account re-add karo"); pause(); continue
                    accs[idx]["active"] = not accs[idx].get("active", True)
                    save(data)
                    ok(f"{'🟢 Active' if accs[idx]['active'] else '🟡 Inactive'}")
                else: err("Invalid!")
            except ValueError: err("Number!")
            pause()
        elif c == "4":
            hdr("Delete Account")
            if not accs: warn("Koi account nahi."); pause(); continue
            for i, a in enumerate(accs, 1):
                name  = a.get("label") or a.get("name") or a["phone"]
                has_s = "✓" if session_exists(a["phone"]) else "✗"
                print(f"  {W}{i}.{NC} {name}  {DIM}[session:{has_s}]{NC}")
            print(f"\n  {W}0.{NC} Back")
            ch = input(f"\n  {W}Number:{NC} ").strip()
            if ch == "0": continue
            try:
                idx = int(ch) - 1
                if 0 <= idx < len(accs):
                    a    = accs[idx]
                    name = a.get("label") or a.get("name") or a["phone"]
                    cf   = input(f"  {R}'{name}' delete? [y/N]:{NC} ").strip()
                    if cf.lower() == "y":
                        safe = a["phone"].replace("+", "").replace(" ", "")
                        for ext in [".session", ".session-journal"]:
                            p = os.path.join(SESSION_DIR, safe + ext)
                            if os.path.exists(p):
                                os.remove(p)
                        accs.pop(idx); save(data); ok("Delete ho gaya!")
                    else: warn("Cancel.")
                else: err("Invalid!")
            except ValueError: err("Number!")
            pause()

def targets_menu():
    while True:
        data = load(); tgts = data["targets"]
        g  = sum(1 for t in tgts if t["type"] == "group")
        d2 = sum(1 for t in tgts if t["type"] == "dm")
        hdr(f"Targets  ({g} groups / {d2} DMs)")
        print(f"  {W}1.{NC} Add Target")
        print(f"  {W}2.{NC} List")
        print(f"  {W}3.{NC} Delete")
        print(f"\n  {W}0.{NC} Back")
        c = input(f"\n  {W}Chuno:{NC} ").strip()
        if c == "0": break
        elif c == "1":
            hdr("Add Target")
            print(f"  {W}1.{NC} Group / Channel\n  {W}2.{NC} User DM\n  {W}0.{NC} Back")
            t = input(f"\n  {W}Type:{NC} ").strip()
            if t == "0": continue
            t_type = "group" if t == "1" else "dm" if t == "2" else None
            if not t_type: err("Galat!"); pause(); continue
            val = input(f"  {W}Chat ID:{NC} ").strip()
            if not val: err("ID khali!"); pause(); continue
            lbl = input(f"  {W}Label:{NC} {DIM}(optional){NC}: ").strip()
            for tg in data["targets"]:
                if tg["value"] == val: warn("Pehle se hai!"); pause(); break
            else:
                data["targets"].append({"id": gen_id(), "type": t_type, "value": val,
                                        "label": lbl or val, "addedAt": datetime.now().isoformat()})
                save(data); ok(f"Add: {lbl or val}")
                pause()
        elif c == "2":
            hdr("Targets List")
            if not tgts: warn("Koi target nahi."); pause(); continue
            for tg in tgts:
                icon = "👥" if tg["type"] == "group" else "💬"
                print(f"  {icon} {tg.get('label') or tg['value']}  {DIM}[{tg['value']}]{NC}")
            pause()
        elif c == "3":
            hdr("Delete Target")
            if not tgts: warn("Koi target nahi."); pause(); continue
            for i, tg in enumerate(tgts, 1):
                print(f"  {W}{i}.{NC} {tg.get('label') or tg['value']}")
            print(f"\n  {W}0.{NC} Back")
            ch = input(f"\n  {W}Number:{NC} ").strip()
            if ch == "0": continue
            try:
                idx = int(ch) - 1
                if 0 <= idx < len(tgts):
                    cf = input(f"  {R}Delete? [y/N]:{NC} ").strip()
                    if cf.lower() == "y": tgts.pop(idx); save(data); ok("Delete!")
                    else: warn("Cancel.")
                else: err("Invalid!")
            except ValueError: err("Number!")
            pause()

# ═══════════════════════════════════════════════════════
#  FIRST-RUN WIZARD (CLI)
# ═══════════════════════════════════════════════════════

def first_run_wizard():
    clr()
    print(f"\n{C}  ╔══════════════════════════════════════════════════════╗")
    print(f"  ║   {W}Welcome to Telegram Master Bot!{C}                  ║")
    print(f"  ║   {DIM}Pehli baar setup karte hain — 3 steps{C}           ║")
    print(f"  ╚══════════════════════════════════════════════════════╝{NC}\n")

    data = load()
    cfg  = data["config"]

    if not cfg.get("bot_token"):
        print(f"  {W}━━━ Step 1/3 — Bot Token ━━━{NC}")
        print(f"  {DIM}@BotFather → /newbot → naam aur username do → Token copy karo{NC}\n")
        while True:
            token = input(f"  {W}Bot Token paste karo:{NC} ").strip()
            if not token: warn("Token khali nahi ho sakta!"); continue
            print(f"  {Y}Verify ho raha hai...{NC}")
            try:
                r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10).json()
                if r.get("ok"):
                    cfg["bot_token"] = token
                    ok(f"Bot: {W}{r['result']['first_name']}{NC} (@{r['result']['username']})")
                    break
                else:
                    err(f"Invalid token: {r.get('description')}")
            except Exception as e:
                err(f"Internet error: {e}"); warn("Dobara try karo.")

    if not cfg.get("api_id"):
        print(f"\n  {W}━━━ Step 2/3 — API Credentials ━━━{NC}")
        print(f"  {DIM}my.telegram.org → Login → API development tools → Create App{NC}\n")
        while True:
            ai = input(f"  {W}API ID{NC} {DIM}(number){NC}: ").strip()
            ah = input(f"  {W}API Hash{NC} {DIM}(string){NC}: ").strip()
            if not ai or not ah: err("Khali nahi chhod sakte!"); continue
            try:
                cfg["api_id"] = int(ai); cfg["api_hash"] = ah
                ok("API credentials save ho gaye!"); break
            except ValueError: err("API ID sirf number hona chahiye!")

    if not cfg.get("admin_ids"):
        print(f"\n  {W}━━━ Step 3/3 — Apna Admin ID ━━━{NC}")
        print(f"  {DIM}Bot ko /myid bhejo → apna Telegram ID milega{NC}\n")
        while True:
            raw = input(f"  {W}Admin ID(s){NC} {DIM}(comma se alag karo: 123,456){NC}: ").strip()
            if not raw: err("Admin ID zaruri hai!"); continue
            ids = [int(x.strip()) if x.strip().isdigit() else x.strip()
                   for x in raw.split(",") if x.strip()]
            if ids: cfg["admin_ids"] = ids; ok(f"Admin IDs save: {ids}"); break
            else: err("Sahi ID likho!")

    save(data)
    print(f"\n  {G}{'━'*52}{NC}")
    ok("Setup complete! Ab bot start karo ya accounts add karo.")
    print(f"  {G}{'━'*52}{NC}")
    pause()

# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def _start_bot_polling():
    """Seedha bot polling shuru karo — Heroku/server mode ke liye."""
    d       = load()
    token   = d["config"].get("bot_token", "")
    adm_ids = [str(x) for x in d["config"].get("admin_ids", [])]
    accs    = d["accounts"]
    active  = sum(1 for a in accs if a.get("active") and a.get("verified"))
    print(f"\n✅ Telegram Master Bot chal raha hai!")
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10).json()
        if r.get("ok"):
            binfo = r["result"]
            print(f"   Bot : {binfo['first_name']} (@{binfo.get('username','?')})")
    except Exception:
        pass
    print(f"   Admin IDs : {adm_ids}")
    print(f"   Accounts  : {active}/{len(accs)} active")
    print(f"   Mode      : {'Heroku/Server' if not sys.stdin.isatty() else 'Local'}\n")
    # ── Sabhi existing accounts ko userbot ki tarah auto-start karo ──────────
    _startup_all_userbots()
    _check_mongodb_on_startup()
    bot.infinity_polling(timeout=20, long_polling_timeout=10)


def main():
    data = load()
    cfg  = data["config"]

    # ── Non-interactive mode (Heroku, Railway, VPS) ──────────────────────────
    # DYNO env var = Heroku; ya stdin TTY nahi = server/pipe mode
    is_heroku = bool(os.environ.get("DYNO"))
    is_server = not sys.stdin.isatty()

    if is_heroku or is_server:
        # Config ENV vars se aa jaati hai (_init_bot_token already run ho chuka)
        if not cfg.get("bot_token"):
            print("❌ BOT_TOKEN env var set nahi hai! Heroku Config Vars check karo.")
            sys.exit(1)
        if not cfg.get("api_id"):
            print("❌ API_ID env var set nahi hai! Heroku Config Vars check karo.")
            sys.exit(1)
        if not cfg.get("admin_ids"):
            print("❌ ADMIN_ID env var set nahi hai! Heroku Config Vars check karo.")
            sys.exit(1)
        _start_bot_polling()
        return

    # ── Interactive CLI menu (local run) ─────────────────────────────────────
    if not cfg.get("bot_token") or not cfg.get("api_id") or not cfg.get("admin_ids"):
        first_run_wizard()

    while True:
        clr()
        data   = load(); cfg = data["config"]
        accs   = data["accounts"]; tgts = data["targets"]
        active = sum(1 for a in accs if a.get("active") and a.get("verified"))
        ready  = cfg.get("bot_token") and cfg.get("api_id") and cfg.get("admin_ids")

        print(f"\n{C}  ╔══════════════════════════════════════════════════════╗")
        print(f"  ║   {W}Telegram Master Bot — All-in-One Edition{C}         ║")
        print(f"  ║   {DIM}Broadcast + Scrape + TagAll + Promo + AutoReply{C}  ║")
        print(f"  ╚══════════════════════════════════════════════════════╝{NC}\n")
        print(f"  {DIM}Accounts: {active}/{len(accs)} active   Targets: {len(tgts)}   Bot: {'✅' if cfg.get('bot_token') else '❌ Not set'}{NC}\n")
        print(f"  {W}1.{NC} {Y}Setup{NC}        (API, Bot Token, Admin ID)")
        print(f"  {W}2.{NC} {C}Accounts{NC}     (OTP login)")
        print(f"  {W}3.{NC} {C}Targets{NC}      (dialog groups & DMs)")
        print(f"  {W}4.{NC} {G}Start Bot{NC}    (all features via Telegram commands)")
        sep()
        if not ready: print(f"\n  {Y}⚠  Pehle Setup karo (Option 1){NC}\n")
        print(f"  {W}0.{NC} Exit")

        try:
            c = input(f"\n  {W}Chuno:{NC} ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if c == "0":
            clr(); print(f"\n  {G}Bye! 👋{NC}\n"); break
        elif c == "1": setup_menu()
        elif c == "2": accounts_menu()
        elif c == "3": targets_menu()
        elif c == "4":
            if not ready: err("Pehle Setup karo!"); pause()
            else:
                clr()
                _start_bot_polling()
        else: err("Galat choice!"); time.sleep(0.4)


if __name__ == "__main__":
    init_db()
    print("\n╔══════════════════════════════════════════════════╗")
    print("║   🤖 Telegram Master Bot — All-in-One Edition   ║")
    print("╚══════════════════════════════════════════════════╝\n")

    # --server flag = Heroku/Railway/VPS mode — menu skip, seedha bot chalu
    SERVER_MODE = (
        "--server" in sys.argv
        or bool(os.environ.get("DYNO"))          # Heroku
        or bool(os.environ.get("RAILWAY_ENV"))   # Railway
        or not sys.stdin.isatty()                # any non-interactive shell
    )

    if SERVER_MODE:
        d   = load()
        cfg = d["config"]
        missing = []
        if not cfg.get("bot_token"):  missing.append("BOT_TOKEN")
        if not cfg.get("api_id"):     missing.append("API_ID")
        if not cfg.get("admin_ids"):  missing.append("ADMIN_ID")
        if missing:
            print(f"❌ Yeh Config Vars set nahi hain: {', '.join(missing)}")
            print("   Heroku Dashboard → Settings → Config Vars mein add karo.")
            sys.exit(1)
        try:
            _start_bot_polling()
        except KeyboardInterrupt:
            print("\nBot band kiya.")
    else:
        try:
            main()
        except KeyboardInterrupt:
            print(f"\n\n  {Y}Bye!{NC}\n")
