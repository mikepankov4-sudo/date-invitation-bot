import os, json, sqlite3, asyncio
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

BOT_TOKEN=os.getenv("BOT_TOKEN","")
ADMIN_ID=int(os.getenv("ADMIN_ID","0") or 0)
WEBAPP_URL=os.getenv("WEBAPP_URL","")
app=FastAPI()
bot=Bot(BOT_TOKEN) if BOT_TOKEN else None
dp=Dispatcher()
DB="invitations.sqlite3"

def init_db():
    c=sqlite3.connect(DB); c.execute("""CREATE TABLE IF NOT EXISTS invitations(
    id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, date TEXT, time TEXT,
    place TEXT, format TEXT, user_id TEXT, username TEXT)"""); c.commit(); c.close()
init_db()

@dp.message(CommandStart())
async def start(message: types.Message):
    if not WEBAPP_URL:
        await message.answer("WEBAPP_URL пока не настроен.")
        return
    kb=types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="💌 Открыть приглашение",web_app=types.WebAppInfo(url=WEBAPP_URL))
    ]])
    await message.answer("У тебя новое приглашение.\n\nЕсть одно небольшое предложение.",reply_markup=kb)

@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id!=ADMIN_ID:return
    c=sqlite3.connect(DB); rows=c.execute("SELECT date,time,place,format,username FROM invitations ORDER BY id DESC LIMIT 20").fetchall();c.close()
    if not rows: await message.answer("Пока приглашений нет.");return
    await message.answer("\n\n".join(f"📅 {r[0]} · {r[1]}\n📍 {r[2]}\n✨ {r[3]}\n@{r[4] or '—'}" for r in rows))

@app.get("/",response_class=HTMLResponse)
async def home(): return HTML

@app.post("/api/invitation")
async def save(request:Request):
    d=await request.json();u=d.get("user") or {}
    c=sqlite3.connect(DB);c.execute("INSERT INTO invitations(created_at,date,time,place,format,user_id,username) VALUES(?,?,?,?,?,?,?)",
    (datetime.now().isoformat(),d.get("date",""),d.get("time",""),d.get("place",""),d.get("format",""),str(u.get("id","")),u.get("username","")));c.commit();c.close()
    if bot and ADMIN_ID:
        try: await bot.send_message(ADMIN_ID,f"❤️ Новое подтверждение!\n📅 {d.get('date')} · {d.get('time')}\n📍 {d.get('place')}\n✨ {d.get('format')}")
        except: pass
    return JSONResponse({"ok":True})

async def run_bot():
    if bot: await dp.start_polling(bot)

if __name__=="__main__":
    import uvicorn
    async def runner():
        asyncio.create_task(run_bot())
        config=uvicorn.Config(app,host="0.0.0.0",port=int(os.getenv("PORT","10000")))
        server=uvicorn.Server(config);await server.serve()
    asyncio.run(runner())

HTML='<!doctype html>\n<html lang="ru"><head>\n<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<title>AN INVITATION</title>\n<script src="https://telegram.org/js/telegram-web-app.js"></script>\n<style>\n*{box-sizing:border-box}body{margin:0;background:#10100f;color:#f1eee7;font-family:Arial,sans-serif;min-height:100vh}\nmain{max-width:520px;margin:auto;padding:42px 22px 35px;min-height:100vh;display:flex;flex-direction:column;justify-content:center}\n.ey{font-size:11px;letter-spacing:4px;opacity:.55;margin-bottom:22px}.title{font-family:Georgia,serif;font-size:42px;line-height:1.05;margin:0 0 18px}.sub{color:#bdb8ad;line-height:1.6;font-size:16px;margin-bottom:32px}\n.step{font-size:11px;letter-spacing:2px;color:#9d967f;margin-bottom:16px}.choices{display:grid;gap:10px}\n.choice{padding:18px;border:1px solid #36342e;border-radius:15px;background:#171714;text-align:left;color:#eee;transition:.2s;font-size:15px}\n.choice small{display:block;color:#969188;margin-top:7px;line-height:1.4}.btn{margin-top:24px;width:100%;border:0;border-radius:15px;padding:17px;background:#d7c59a;color:#171512;font-weight:700;font-size:15px}\n.muted{opacity:.55;font-size:13px}.hide{display:none}.success{text-align:center}.heart{font-size:48px;margin-bottom:20px}\n</style></head><body><main>\n<section id="intro"><div class="ey">AN INVITATION</div><h1 class="title">У тебя новое<br>приглашение.</h1><p class="sub">Есть одно небольшое предложение.<br>Давай сделаем этот вечер особенным.</p><button class="btn" onclick="next()">Открыть</button></section>\n<section id="form" class="hide"><div id="content"></div></section>\n<section id="success" class="hide success"><div class="heart">♥</div><div class="ey">AN INVITATION</div><h1 class="title">Договорились.</h1><p class="sub">Тогда до встречи.<br>Остальное я беру на себя.</p></section>\n</main>\n<script>\nconst TG=window.Telegram?.WebApp;if(TG){TG.ready();TG.expand();}\nconst qs=[\n{t:"Когда?",o:["Пятница, 02 октября","Суббота, 03 октября","Воскресенье, 04 октября"]},\n{t:"Во сколько?",o:["18:00","19:00","20:00","21:00"]},\n{t:"Какой вариант вечера?",o:[\n["🍷 Красивый ресторан","Спокойный вечер, хороший ужин и возможность нормально поговорить."],\n["🍸 Коктейли","Немного красивее, немного веселее."],\n["🌆 Прогулка + ужин","Сначала немного города. Потом найдём место по настроению."],\n["🎲 Я всё придумал","Ты просто приходи. Остальное — моя забота."]]},\n{t:"И последний вопрос.",o:["🥂 Нарядно","👟 Расслабленно","🕶 Без дресс-кода","🎲 Сюрприз"]}];\nlet i=-1,ans=[];\nfunction next(){intro.classList.add("hide");form.classList.remove("hide");show()}\nfunction show(){i++;if(i>=qs.length){send();return}let q=qs[i];content.innerHTML=`<div class="step">${i+1} / ${qs.length}</div><h1 class="title">${q.t}</h1><div class="choices">${q.o.map((x,n)=>`<button class="choice" onclick="pick(${n})">${Array.isArray(x)?x[0]:x}${Array.isArray(x)?`<small>${x[1]}</small>`:""}</button>`).join("")}</div><div class="muted" style="margin-top:18px">Выбери один вариант</div>`}\nfunction pick(n){ans[i]=Array.isArray(qs[i].o[n])?qs[i].o[n][0]:qs[i].o[n];show()}\nasync function send(){let d={date:ans[0],time:ans[1],place:ans[2],format:ans[3],user:TG?.initDataUnsafe?.user||{}};try{await fetch("/api/invitation",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)})}catch(e){}form.classList.add("hide");success.classList.remove("hide")}\n</script></body></html>'
