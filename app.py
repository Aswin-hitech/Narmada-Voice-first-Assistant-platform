import os, json, math, uuid
import psycopg2, psycopg2.extras
from flask import Flask, request, jsonify, render_template
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
ai = OpenAI()
CHAT = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
EMB = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
LANGS = {"en-IN":"English","hi-IN":"Hindi","ta-IN":"Tamil","te-IN":"Telugu","kn-IN":"Kannada","ml-IN":"Malayalam","mr-IN":"Marathi","bn-IN":"Bengali"}

def run(sql, args=(), fetch=None):
    c = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        with c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, args)
            return cur.fetchone() if fetch == "one" else cur.fetchall() if fetch == "all" else None
    finally:
        c.close()

def embed(texts):
    return [d.embedding for d in ai.embeddings.create(model=EMB, input=texts).data]

def init():
    run("""CREATE TABLE IF NOT EXISTS kb(code text PRIMARY KEY, kind text, title text, sector text, level int, body text, emb jsonb);
           CREATE TABLE IF NOT EXISTS sessions(id text PRIMARY KEY, lang text, history jsonb DEFAULT '[]', profile jsonb DEFAULT '{}', rec jsonb, created timestamptz DEFAULT now());""")
    if run("SELECT count(*) n FROM kb", fetch="one")["n"] == 0:
        docs = json.load(open(os.path.join(os.path.dirname(__file__), "kb.json")))
        for d, e in zip(docs, embed([f"{d['title']}. {d['text']}" for d in docs])):
            run("INSERT INTO kb VALUES(%s,%s,%s,%s,%s,%s,%s)", (d["code"], d["kind"], d["title"], d["sector"], d["level"], d["text"], json.dumps(e)))

def cos(a, b):
    return sum(x*y for x, y in zip(a, b)) / (math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b)) + 1e-9)

def llm(system, messages):
    r = ai.chat.completions.create(model=CHAT, response_format={"type": "json_object"}, temperature=0.3,
                                   messages=[{"role": "system", "content": system}] + messages)
    return json.loads(r.choices[0].message.content)

@app.route("/")
def home():
    return render_template("index.html", langs=LANGS)

@app.post("/api/start")
def start():
    lang = request.json.get("lang", "en-IN")
    sid = uuid.uuid4().hex
    run("INSERT INTO sessions(id,lang) VALUES(%s,%s)", (sid, lang))
    opener = llm(f"Reply ONLY as JSON {{\"reply\":str}}. Write one warm, simple greeting in {LANGS.get(lang,'English')} asking the person to describe a normal day of their work. Max 2 short sentences.", [{"role": "user", "content": "start"}])["reply"]
    run("UPDATE sessions SET history=%s WHERE id=%s", (json.dumps([{"role": "assistant", "content": opener}]), sid))
    return jsonify(sid=sid, reply=opener)

@app.post("/api/chat")
def chat():
    d = request.json
    s = run("SELECT * FROM sessions WHERE id=%s", (d["sid"],), "one")
    hist = s["history"] + [{"role": "user", "content": d["message"]}]
    out = llm(f"""You are Agent 1 of a voice assistant that maps a person's existing livelihood to skilling programs. Speak {LANGS.get(s['lang'],'English')}, simple words, ONE short follow-up question per turn.
Current profile: {json.dumps(s['profile'])}
Return JSON: {{"reply":str,"profile":{{"activities":[str],"tools":[str],"frequency":str,"experience":str,"communication":str}},"enough":bool}}.
Merge new facts into the profile (English values). communication = brief note on how clearly they explain their work. enough=true after you know activities, tools and experience.""", hist)
    hist.append({"role": "assistant", "content": out["reply"]})
    run("UPDATE sessions SET history=%s, profile=%s WHERE id=%s", (json.dumps(hist), json.dumps(out["profile"]), d["sid"]))
    return jsonify(reply=out["reply"], profile=out["profile"], enough=out["enough"])

@app.post("/api/recommend")
def recommend():
    s = run("SELECT * FROM sessions WHERE id=%s", (request.json["sid"],), "one")
    qv = embed([json.dumps(s["profile"])])[0]
    rows = run("SELECT * FROM kb", fetch="all")
    for r in rows: r["score"] = cos(qv, r["emb"])
    qps = sorted([r for r in rows if r["kind"] == "qp"], key=lambda r: -r["score"])[:4]
    rules = [r for r in rows if r["kind"] == "rule"]
    ctx = "\n".join(f"[{r['code']}] {r['title']} (NSQF level {r['level']}, {r['sector']}): {r['body']}" for r in qps + rules)
    out = llm(f"""You are Agent 2. Recommend ONE best-fit training path using ONLY these documents; cite the code. Write text fields in {LANGS.get(s['lang'],'English')}.
Documents:\n{ctx}
Return JSON: {{"code":str,"title":str,"level":int,"why":str,"eligibility":str,"next_step":str,"alternatives":[{{"code":str,"title":str}}],"spoken":str}}. spoken = 2-3 simple sentences to read aloud.""",
              [{"role": "user", "content": json.dumps(s["profile"])}])
    run("UPDATE sessions SET rec=%s WHERE id=%s", (json.dumps(out), s["id"]))
    return jsonify(out)

@app.get("/api/stats")
def stats():
    return jsonify(run("SELECT count(*) sessions, count(rec) recommendations FROM sessions", fetch="one"))

if __name__ == "__main__":
    init()
    app.run(debug=True, port=5000)
