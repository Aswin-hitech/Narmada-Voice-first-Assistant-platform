import os
import json
import math
import uuid
import re
import hashlib
from datetime import datetime, timezone
import sqlite3
import tempfile

from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# ----------------- NVIDIA NIM & AI Foundation Separate Client Initialization -----------------
# Global fallback key
NVIDIA_API_KEY = (os.getenv("NVIDIA_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
DEFAULT_NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# 1. Reasoning & Generation (Nemotron 3-Super 120B)
NEMOTRON_API_KEY = (os.getenv("NEMOTRON_API_KEY") or NVIDIA_API_KEY).strip()
NEMOTRON_BASE_URL = (os.getenv("NEMOTRON_BASE_URL") or os.getenv("NVIDIA_BASE_URL") or DEFAULT_NVIDIA_BASE_URL).strip()
NEMOTRON_MODEL = (os.getenv("NEMOTRON_MODEL") or "nvidia/nemotron-3-super-120b-a12b").strip()

# 2. Text Translation (Riva-Translate-4B-Instruct-v2)
RIVA_TRANSLATE_API_KEY = (os.getenv("RIVA_TRANSLATE_API_KEY") or os.getenv("NMT_API_KEY") or NVIDIA_API_KEY).strip()
RIVA_TRANSLATE_BASE_URL = (os.getenv("RIVA_TRANSLATE_BASE_URL") or os.getenv("NVIDIA_BASE_URL") or DEFAULT_NVIDIA_BASE_URL).strip()
RIVA_TRANSLATE_MODEL = (os.getenv("RIVA_TRANSLATE_MODEL") or "nvidia/riva-translate-4b-instruct-v2").strip()

# 3. Speech-to-Text (Parakeet ASR)
PARAKEET_API_KEY = (os.getenv("PARAKEET_API_KEY") or os.getenv("ASR_API_KEY") or NVIDIA_API_KEY).strip()
PARAKEET_ASR_MODEL = (os.getenv("PARAKEET_ASR_MODEL") or "nvidia/parakeet-tdt-0.6b-v2").strip()
PARAKEET_ASR_SERVER = (os.getenv("PARAKEET_ASR_SERVER") or os.getenv("RIVA_ASR_SERVER") or "grpc.nvcf.nvidia.com:443").strip()
PARAKEET_FUNCTION_ID = (os.getenv("PARAKEET_FUNCTION_ID") or "").strip()

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()

# Initialize Nemotron Reasoning Client
NEMOTRON_CLIENT = None
if NEMOTRON_API_KEY and not NEMOTRON_API_KEY.startswith("sk-placeholder") and NEMOTRON_API_KEY != "sk-...":
    try:
        from openai import OpenAI
        NEMOTRON_CLIENT = OpenAI(
            base_url=NEMOTRON_BASE_URL,
            api_key=NEMOTRON_API_KEY
        )
        print(f"[Nemotron Client] Initialized successfully with model: {NEMOTRON_MODEL}")
    except Exception as e:
        print(f"[Warning] Nemotron client init failed: {e}")

# Initialize Riva Translation Client
RIVA_TRANSLATE_CLIENT = None
if RIVA_TRANSLATE_API_KEY and not RIVA_TRANSLATE_API_KEY.startswith("sk-placeholder") and RIVA_TRANSLATE_API_KEY != "sk-...":
    try:
        from openai import OpenAI
        RIVA_TRANSLATE_CLIENT = OpenAI(
            base_url=RIVA_TRANSLATE_BASE_URL,
            api_key=RIVA_TRANSLATE_API_KEY
        )
        print(f"[Riva Translate Client] Initialized successfully with model: {RIVA_TRANSLATE_MODEL}")
    except Exception as e:
        print(f"[Warning] Riva Translate client init failed: {e}")

# Initialize Parakeet Riva ASR Service
RIVA_ASR_SERVICE = None
try:
    import riva.client
    if PARAKEET_API_KEY:
        try:
            metadata = [["authorization", f"Bearer {PARAKEET_API_KEY}"]]
            if PARAKEET_FUNCTION_ID:
                metadata.append(["function-id", PARAKEET_FUNCTION_ID])
            auth = riva.client.Auth(
                uri=PARAKEET_ASR_SERVER,
                use_ssl=True,
                metadata_args=metadata
            )
            RIVA_ASR_SERVICE = riva.client.ASRService(auth)
            print("[Parakeet ASR Service] Initialized successfully via Riva gRPC.")
        except Exception as e:
            print(f"[Notice] Parakeet Riva ASR auth optional: {e}")
except Exception as e:
    print(f"[Notice] riva.client not available: {e}")

# Supported Indian Languages
LANGS = {
    "en-IN": {"name": "English (India)", "native": "English", "code": "en-IN", "iso": "en"},
    "hi-IN": {"name": "Hindi", "native": "हिन्दी", "code": "hi-IN", "iso": "hi"},
    "ta-IN": {"name": "Tamil", "native": "தமிழ்", "code": "ta-IN", "iso": "ta"},
    "te-IN": {"name": "Telugu", "native": "తెలుగు", "code": "te-IN", "iso": "te"},
    "kn-IN": {"name": "Kannada", "native": "ಕನ್ನಡ", "code": "kn-IN", "iso": "kn"},
    "ml-IN": {"name": "Malayalam", "native": "മലയാളം", "code": "ml-IN", "iso": "ml"},
    "mr-IN": {"name": "Marathi", "native": "मराठी", "code": "mr-IN", "iso": "mr"},
    "bn-IN": {"name": "Bengali", "native": "বাংলা", "code": "bn-IN", "iso": "bn"},
    "gu-IN": {"name": "Gujarati", "native": "ગુજરાતી", "code": "gu-IN", "iso": "gu"},
    "or-IN": {"name": "Odia", "native": "ଓଡ଼ିଆ", "code": "or-IN", "iso": "or"},
    "pa-IN": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "code": "pa-IN", "iso": "pa"}
}

# Pre-defined localized greetings & fallback templates
LOCALIZED_GREETINGS = {
    "en-IN": "Namaste! Welcome to NARMADA. Please tell me about the work you do every day, the tools you use, and how many years you have been doing it.",
    "hi-IN": "नमस्ते! नर्मदा सहायक में आपका स्वागत है। कृपया अपने दैनिक काम, इस्तेमाल होने वाले औजारों और अपने अनुभव के बारे में बताएं।",
    "ta-IN": "வணக்கம்! நர்மதா திட்டத்திற்கு உங்களை வரவேற்கிறோம். நீங்கள் தினமும் செய்யும் வேலை, பயன்படுத்தும் கருவிகள் மற்றும் உங்கள் அனுபவத்தைப் பற்றி சொல்லுங்கள்.",
    "te-IN": "నమస్కారం! నర్మదా ప్లాట్‌ఫామ్‌కు స్వాగతం. మీరు ప్రతిరోజూ చేసే పని, ఉపయోగించే పరికరాలు మరియు మీ అనుభవం గురించి చెప్పండి.",
    "kn-IN": "ನಮಸ್ಕಾರ! ನರ್ಮದಾ ಯೋಜನೆಗೆ ಸುಸ್ವಾಗತ. ನೀವು ಪ್ರತಿದಿನ ಮಾಡುವ ಕೆಲಸ, ಬಳಸುವ ಉಪಕರಣಗಳು ಮತ್ತು ನಿಮ್ಮ ಅನುಭವದ ಬಗ್ಗೆ ತಿಳಿಸಿ.",
    "ml-IN": "നമസ്കാരം! നർമ്മദ പ്ലാറ്റ്‌ഫോമിലേക്ക് സ്വാഗതം. നിങ്ങളുടെ ദൈനംദിന ജോലി, ഉപയോഗിക്കുന്ന ഉപകരണങ്ങൾ, തൊഴിൽ പരിചയം എന്നിവയെക്കുറിച്ച് പറയുക.",
    "mr-IN": "नमस्ते! नर्मदा सहाय्यकामध्ये आपले स्वागत आहे. आपण रोज करत असलेले काम, वापरत असलेली साधने आणि आपल्या अनुभवाबद्दल सांगा.",
    "bn-IN": "নমস্কার! নর্মদা সহায়কে আপনাকে স্বাগতম। আপনি প্রতিদিন কী কাজ করেন, কী কী যন্ত্রপাতি ব্যবহার করেন এবং আপনার অভিজ্ঞতা জানান।",
    "gu-IN": "નમસ્તે! નર્મદા સહાયકમાં આપનું સ્વાગત છે. તમારા રોજના काम, સાધનો અને અનુભવ વિશે જણાવો.",
    "or-IN": "ନମସ୍କାର! ନର୍ମଦା ସହାୟକକୁ ଆପଣଙ୍କୁ ସ୍ୱାଗତ। ଆପଣଙ୍କ ଦୈନନ୍ଦିନ କାର୍ଯ୍ୟ, ବ୍ୟବହୃତ ଉପକରଣ ଓ ଅଭିଜ୍ଞତା ବିଷୟରେ କୁହନ୍ତୁ।",
    "pa-IN": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਨਰਮਦਾ ਸਹਾਇਕ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਰੋਜ਼ਾਨਾ ਦੇ ਕੰਮ, ਵਰਤੇ ਜਾਂਦੇ ਔਜ਼ਾਰਾਂ ਅਤੇ ਤਜ਼ਰਬੇ ਬਾਰੇ ਦੱਸੋ।"
}

LOCALIZED_PROMPTS = {
    "en-IN": {
        "need_tools": "That sounds great! Could you also mention which tools, machines, or materials you use?",
        "need_exp": "Understood! How many months or years have you been doing this work?",
        "complete": "Thank you! I have gathered your work profile. Ready to generate your NSQF skilling recommendation."
    },
    "hi-IN": {
        "need_tools": "बहुत बढ़िया! क्या आप बता सकते हैं कि इस काम में आप कौन से औजार, मशीन या सामान का उपयोग करते हैं?",
        "need_exp": "समझ गया! आप यह काम कितने सालों या महीनों से कर रहे हैं?",
        "complete": "धन्यवाद! मैंने आपकी कार्य प्रोफ़ाइल तैयार कर ली है। आपके लिए NSQF प्रशिक्षण खोजने के लिए तैयार हैं।"
    },
    "ta-IN": {
        "need_tools": "மிக நன்று! இந்த வேலையில் நீங்கள் என்ன கருவிகள் அல்லது இயந்திரங்களை பயன்படுத்துகிறீர்கள்?",
        "need_exp": "புரிந்தது! இந்த தொழிலை நீங்கள் எத்தனை வருடங்களாக அல்லது மாதங்களாக செய்து வருகிறீர்கள்?",
        "complete": "நன்றி! உங்கள் பணி விவரங்களை பதிவு செய்துவிட்டேன். உங்களுக்கான NSQF பயிற்சி பரிந்துரையை பெறலாம்."
    },
    "te-IN": {
        "need_tools": "చాలా మంచిది! ఈ పనిలో మీరు ఏ పరికరాలు లేదా యంత్రాలను ఉపయోగిస్తున్నారు?",
        "need_exp": "అర్థమైంది! మీరు ఈ పనిని ఎన్ని సంవత్సరాలు లేదా నెలల నుండి చేస్తున్నారు?",
        "complete": "ధన్యవాదాలు! మీ పని వివరాలు నమోదయ్యాయి. మీకు సరిపోయే NSQF శిక్షణ సిఫార్సు సిద్ధంగా ఉంది."
    },
    "kn-IN": {
        "need_tools": "ಉತ್ತಮ! ಈ ಕೆಲಸದಲ್ಲಿ ನೀವು ಯಾವ ಉಪಕರಣಗಳು ಅಥವಾ ಯಂತ್ರಗಳನ್ನು ಬಳಸುತ್ತೀರಿ?",
        "need_exp": "ತಿಳಿಯಿತು! ನೀವು ಈ ಕೆಲಸವನ್ನು ಎಷ್ಟು ವರ್ಷಗಳಿಂದ ಮಾಡುತ್ತಿದ್ದೀರಿ?",
        "complete": "ಧನ್ಯವಾದಗಳು! ನಿಮ್ಮ ಕೆಲಸದ ವಿವರ ದಾಖಲಾಗಿದೆ. ನಿಮಗಾಗಿ NSQF ತರಬೇತಿ ಶಿಫಾರಸು ಪಡೆಯಬಹುದು."
    },
    "ml-IN": {
        "need_tools": "വളരെ നല്ലത്! ഈ ജോലിയിൽ നിങ്ങൾ എന്തെല്ലാം ഉപകരണങ്ങളാണ് ഉപയോഗിക്കുന്നത്?",
        "need_exp": "മനസ്സിലായി! ഈ ജോലി നിങ്ങൾ എത്ര വർഷമായി ചെയ്യുന്നു?",
        "complete": "നന്ദി! നിങ്ങളുടെ തൊഴിൽ വിവരങ്ങൾ രേഖപ്പെടുത്തി. നിങ്ങൾക്കുള്ള NSQF പരിശീലന ശുപാർശ തയ്യാറാണ്."
    },
    "mr-IN": {
        "need_tools": "छान! आपण या कामासाठी कोणती साधने किंवा यंत्रे वापरता?",
        "need_exp": "समजले! आपण हे काम किती वर्षांपासून करत आहात?",
        "complete": "धन्यवाद! आपली कामाची माहिती नोंदवली आहे. आपल्यासाठी NSQF प्रशिक्षण शिफारस तयार आहे."
    },
    "bn-IN": {
        "need_tools": "খুব ভালো! এই কাজে আপনি কী কী সরঞ্জাম বা যন্ত্রপাতি ব্যবহার করেন?",
        "need_exp": "বুঝতে পেরেছি! আপনি কত বছর বা মাস ধরে এই কাজ করছেন?",
        "complete": "ধন্যবাদ! আপনার কাজের বিবরণ প্রস্তুত। আপনার জন্য NSQF প্রশিক্ষণ সুপারিশ তৈরি করতে পারেন।"
    },
    "gu-IN": {
        "need_tools": "સરસ! આ કામમાં તમે કયા સાધનો અથવા મશીનનો ઉપયોગ કરો છો?",
        "need_exp": "સમજાયું! તમે કેટલા સમયથી આ કામ કરી રહ્યા છો?",
        "complete": "આભાર! તમારી કાર્ય પ્રોફાઇલ તૈયાર છે. તમારા માટે NSQF તાલીમ ભલામણ મેળવી શકાય છે."
    },
    "or-IN": {
        "need_tools": "ଉତ୍ତମ! ଏହି କାମରେ ଆପଣ କେଉଁ ଉପକରଣ ବା ଯନ୍ତ୍ରପାତି ବ୍ୟବହାର କରନ୍ତି?",
        "need_exp": "ବୁଝିପାରିଲି! ଆପଣ କେତେ ବର୍ଷ ହେଲା ଏହି କାମ କରୁଛନ୍ତି?",
        "complete": "ଧନ୍ୟବାଦ! ଆପଣଙ୍କ କାର୍ଯ୍ୟ ବିବରଣୀ ପ୍ରସ୍ତୁତ। ଆପଣଙ୍କ ପାଇଁ NSQF ପ୍ରଶିକ୍ଷଣ ସୁପାରିଶ ପାଇପାରିବେ।"
    },
    "pa-IN": {
        "need_tools": "ਬਹੁਤ ਵਧੀਆ! ਕੀ ਤੁਸੀਂ ਦੱਸ ਸਕਦੇ ਹੋ ਕਿ ਇਸ ਕੰਮ ਵਿੱਚ ਤੁਸੀਂ ਕਿਹੜੇ ਔਜ਼ਾਰ ਜਾਂ ਮਸ਼ੀਨਾਂ ਵਰਤਦੇ ਹੋ?",
        "need_exp": "ਸਮਝ ਗਿਆ! ਤੁਸੀਂ ਕਿੰਨੇ ਸਾਲਾਂ ਜਾਂ ਮਹੀਨਿਆਂ ਤੋਂ ਇਹ ਕੰਮ ਕਰ ਰਹੇ ਹੋ?",
        "complete": "ਧੰਨਵਾਦ! ਤੁਹਾਡੀ ਪ੍ਰੋਫਾਈਲ ਤਿਆਰ ਹੈ। ਹੁਣ ਤੁਸੀਂ NSQF ਸਿਖਲਾਈ ਸਿਫਾਰਸ਼ ਪ੍ਰਾਪਤ ਕਰ ਸਕਦੇ ਹੋ।"
    }
}

# ----------------- Translation Layer (Riva-Translate-4B-Instruct-v2) -----------------
def translate_with_riva(text, src_lang="en-IN", target_lang="hi-IN"):
    """
    Translates text using nvidia/riva-translate-4b-instruct-v2.
    """
    client = RIVA_TRANSLATE_CLIENT or NEMOTRON_CLIENT
    if not text or not client:
        return text

    src_iso = LANGS.get(src_lang, {}).get("iso", "en") if "-" in src_lang else src_lang
    tgt_iso = LANGS.get(target_lang, {}).get("iso", "en") if "-" in target_lang else target_lang

    if src_iso == tgt_iso:
        return text

    try:
        pair = f"{src_iso}-{tgt_iso}"
        res = client.chat.completions.create(
            model=RIVA_TRANSLATE_MODEL,
            messages=[
                {"role": "system", "content": pair},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=1024
        )
        content = res.choices[0].message.content
        if content and content.strip():
            return content.strip()
    except Exception as e:
        # Fallback to instruction prompt format if pair format differs
        try:
            target_name = LANGS.get(target_lang, {}).get("name", target_lang)
            res = client.chat.completions.create(
                model=RIVA_TRANSLATE_MODEL,
                messages=[
                    {"role": "user", "content": f"Translate the following text accurately into {target_name}:\n{text}"}
                ],
                temperature=0.1,
                max_tokens=1024
            )
            content = res.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception as e2:
            print(f"[Riva Translate Error] ({src_iso}->{tgt_iso}): {e2}")

    return text

# ----------------- Speech-to-Text Layer (Parakeet ASR) -----------------
def transcribe_with_parakeet(audio_bytes, lang_code="en-IN"):
    """
    Transcribes voice audio using NVIDIA Parakeet ASR model.
    """
    if RIVA_ASR_SERVICE and audio_bytes:
        try:
            config = riva.client.RecognitionConfig(
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                sample_rate_hertz=16000,
                language_code=lang_code,
                max_alternatives=1,
                enable_automatic_punctuation=True
            )
            response = RIVA_ASR_SERVICE.offline_recognize(audio_bytes, config)
            if response.results and response.results[0].alternatives:
                transcript = response.results[0].alternatives[0].transcript
                return transcript
        except Exception as e:
            print(f"[Parakeet Riva ASR Notice] {e}")

    return None

# ----------------- Robust JSON Output Cleaner -----------------
def clean_json_response(raw_text):
    if not raw_text:
        return {}
    # Extract json block if inside markdown ```json ... ```
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
    if match:
        raw_text = match.group(1)
    else:
        # Look for the outer { ... }
        s = raw_text.find('{')
        e = raw_text.rfind('}')
        if s != -1 and e != -1 and e > s:
            raw_text = raw_text[s:e+1]
    try:
        return json.loads(raw_text)
    except Exception as err:
        print(f"[JSON Parse Notice] Error parsing: {err}")
        return {}

# ----------------- Database Abstraction Layer -----------------
DB_FILE = os.path.join(os.path.dirname(__file__), "narmada.db")
USE_POSTGRES = False

def get_db():
    global USE_POSTGRES
    if DATABASE_URL and ("postgresql://" in DATABASE_URL or "postgres://" in DATABASE_URL) and "ep-xxxx" not in DATABASE_URL and "user:password@" not in DATABASE_URL:
        try:
            import psycopg2
            import psycopg2.extras
            conn = psycopg2.connect(DATABASE_URL)
            USE_POSTGRES = True
            return conn
        except Exception as e:
            print(f"[Warning] PostgreSQL connection failed ({e}), falling back to SQLite.")
            USE_POSTGRES = False

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(sql, args=(), fetch=None):
    conn = get_db()
    try:
        if USE_POSTGRES:
            import psycopg2.extras
            with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, args)
                if fetch == "one":
                    return cur.fetchone()
                elif fetch == "all":
                    return cur.fetchall()
                return None
        else:
            # SQLite conversion
            sqlite_sql = sql.replace("%s", "?")
            sqlite_sql = sqlite_sql.replace("jsonb", "text").replace("timestamptz", "text").replace("now()", "datetime('now')")
            with conn:
                cur = conn.cursor()
                cur.execute(sqlite_sql, args)
                if fetch == "one":
                    row = cur.fetchone()
                    return dict(row) if row else None
                elif fetch == "all":
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
                return None
    finally:
        conn.close()

# ----------------- Hybrid Semantic Vector & RAG Engine -----------------
def simple_tokenize(text):
    if not text:
        return []
    cleaned = re.sub(r'[^\w\s]', ' ', text.lower(), flags=re.UNICODE)
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
    return tokens

def compute_term_freqs(texts):
    vocab = {}
    doc_freqs = []
    for doc in texts:
        tokens = simple_tokenize(doc)
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        doc_freqs.append(tf)
        for t in tf:
            vocab[t] = vocab.get(t, 0) + 1
    return vocab, doc_freqs

def tfidf_vector(tokens, vocab, N, doc_freq_counts):
    vec = {}
    tf_counts = {}
    for t in tokens:
        tf_counts[t] = tf_counts.get(t, 0) + 1
    
    total_tokens = len(tokens) or 1
    for t, count in tf_counts.items():
        if t in vocab:
            tf = count / total_tokens
            df = doc_freq_counts.get(t, 1)
            idf = math.log((N + 1) / (df + 0.5)) + 1
            vec[t] = tf * idf
    return vec

def sparse_cosine(vec_a, vec_b):
    common = set(vec_a.keys()) & set(vec_b.keys())
    if not common:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in common)
    mag_a = math.sqrt(sum(v*v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v*v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

def dense_cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x*y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x*x for x in a))
    mag_b = math.sqrt(sum(y*y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)

# ----------------- Database Initialization -----------------
def init_db():
    if USE_POSTGRES:
        execute_query("""
            CREATE TABLE IF NOT EXISTS kb (
                code text PRIMARY KEY,
                kind text,
                title text,
                sector text,
                level int,
                min_education text,
                body text,
                modules jsonb DEFAULT '[]',
                career_path text,
                wage_potential text,
                pm_ajay_grant text,
                emb jsonb
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id text PRIMARY KEY,
                lang text,
                history jsonb DEFAULT '[]',
                profile jsonb DEFAULT '{}',
                rec jsonb,
                mentor_history jsonb DEFAULT '[]',
                status text DEFAULT 'active',
                officer_notes text DEFAULT '',
                dpdp_consent jsonb DEFAULT '{"consented": true, "timestamp": "2026-09-30T10:00:00Z", "purpose": "PM-AJAY Skilling Livelihood Mapping"}',
                audit_hash text,
                created timestamptz DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS dpdp_logs (
                id text PRIMARY KEY,
                session_id text,
                action text,
                timestamp timestamptz DEFAULT now(),
                details jsonb
            );
        """)
    else:
        execute_query("""
            CREATE TABLE IF NOT EXISTS kb (
                code text PRIMARY KEY,
                kind text,
                title text,
                sector text,
                level integer,
                min_education text,
                body text,
                modules text DEFAULT '[]',
                career_path text,
                wage_potential text,
                pm_ajay_grant text,
                emb text
            );
        """)
        execute_query("""
            CREATE TABLE IF NOT EXISTS sessions (
                id text PRIMARY KEY,
                lang text,
                history text DEFAULT '[]',
                profile text DEFAULT '{}',
                rec text,
                mentor_history text DEFAULT '[]',
                status text DEFAULT 'active',
                officer_notes text DEFAULT '',
                dpdp_consent text DEFAULT '{"consented": true, "timestamp": "2026-09-30T10:00:00Z", "purpose": "PM-AJAY Skilling Livelihood Mapping"}',
                audit_hash text,
                created text DEFAULT (datetime('now'))
            );
        """)
        execute_query("""
            CREATE TABLE IF NOT EXISTS dpdp_logs (
                id text PRIMARY KEY,
                session_id text,
                action text,
                timestamp text DEFAULT (datetime('now')),
                details text
            );
        """)

    # Seed and sync Knowledge Base (NSQF Qualification Packs & PM-AJAY Scheme Guidelines)
    kb_path = os.path.join(os.path.dirname(__file__), "kb.json")
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        
        for d in docs:
            modules_json = json.dumps(d.get("modules", []))
            if USE_POSTGRES:
                execute_query("""
                    INSERT INTO kb (code, kind, title, sector, level, min_education, body, modules, career_path, wage_potential, pm_ajay_grant, emb)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (code) DO UPDATE SET
                        kind = EXCLUDED.kind,
                        title = EXCLUDED.title,
                        sector = EXCLUDED.sector,
                        level = EXCLUDED.level,
                        min_education = EXCLUDED.min_education,
                        body = EXCLUDED.body,
                        modules = EXCLUDED.modules,
                        career_path = EXCLUDED.career_path,
                        wage_potential = EXCLUDED.wage_potential,
                        pm_ajay_grant = EXCLUDED.pm_ajay_grant
                """, (
                    d["code"],
                    d["kind"],
                    d["title"],
                    d.get("sector", ""),
                    d.get("level", 0),
                    d.get("min_education", ""),
                    d["text"],
                    modules_json,
                    d.get("career_path", ""),
                    d.get("wage_potential", ""),
                    d.get("pm_ajay_grant", ""),
                    None
                ))
            else:
                execute_query("""
                    INSERT OR REPLACE INTO kb (code, kind, title, sector, level, min_education, body, modules, career_path, wage_potential, pm_ajay_grant, emb)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    d["code"],
                    d["kind"],
                    d["title"],
                    d.get("sector", ""),
                    d.get("level", 0),
                    d.get("min_education", ""),
                    d["text"],
                    modules_json,
                    d.get("career_path", ""),
                    d.get("wage_potential", ""),
                    d.get("pm_ajay_grant", ""),
                    None
                ))
        print(f"[NARMADA RAG] Synced {len(docs)} NSQF Qualification Packs & PM-AJAY Scheme Rules into Knowledge Base.")

# ----------------- Domain Taxonomy for Resilient Multi-lingual Extraction -----------------
DOMAIN_KEYWORD_MAP = {
    "Dairy & Animal Husbandry": {
        "keywords": ["cow", "cows", "buffalo", "buffaloes", "milk", "milking", "dairy", "cattle", "ghee", "curd", "paneer", "dung", "பால்", "எருமை", "மாடு", "गाय", "भैंस", "दूध", "डेयरी", "గొర్రెలు", "ఆవు", "గేదె", "పాలు", "ಹಸು", "ಹಾಲು", "പശു", "പാൽ", "দুধ", "গরু"],
        "qp_code": "AGR/Q8101",
        "tools": ["Milk Cans", "Milking Pail", "Lactometer", "Fodder Cutter"]
    },
    "Organic Farming & Agriculture": {
        "keywords": ["farm", "farming", "crop", "crops", "vegetables", "organic", "soil", "harvest", "field", "fertilizer", "compost", "jeevamrut", "விவசாயம்", "பயிர்", "காய்கறி", "தோட்டம்", "खेती", "फसल", "सब्जी", "खाद", "వ్యవసాయం", "పంట", "తోట", "ಕೃಷಿ", "ಬೆಳೆ", "കൃഷി", "চাষ", "ফসল"],
        "qp_code": "AGR/Q1201",
        "tools": ["Spade", "Hoe", "Compost Sprayer", "Weeder", "Soil Testing Kit"]
    },
    "Micro Irrigation & Farm Water": {
        "keywords": ["drip", "sprinkler", "irrigation", "borewell", "pump", "pvc", "pipes", "valve", "water pump", "சொட்டு நீர்", "பாசனம்", "कुआं", "ड्रिप", "सिंचाई", "పైపులు", "బోరుబావి", "ಹನಿ ನೀರಾವರಿ"],
        "qp_code": "AGR/Q1002",
        "tools": ["Pipe Wrench", "Solvent Cement", "Pressure Gauge", "Dripper Punch"]
    },
    "Poultry & Bird Rearing": {
        "keywords": ["chicken", "chickens", "hen", "poultry", "eggs", "broiler", "rooster", "birds", "கோழி", "முட்டை", "मुर्गी", "पोल्ट्री", "अंडा", "కోళ్లు", "గుడ్లు", "ಕೋಳಿ", "কোয়েল", "মুরগি"],
        "qp_code": "AGR/Q4301",
        "tools": ["Egg Trays", "Feeder", "Drinker", "Brooder Lamp"]
    },
    "Goat & Sheep Farming": {
        "keywords": ["goat", "goats", "sheep", "lamb", "mutton", "grazing", "ஆடு", "மேய்த்தல்", "बकरी", "भेड़", "మేకలు", "గొర్రెలు", "ಆಡು", "ছাগল"],
        "qp_code": "AGR/Q4401",
        "tools": ["Deworming Gun", "Hoof Trimmer", "Fodder Trough"]
    },
    "Tailoring & Garment Stitching": {
        "keywords": ["tailor", "tailoring", "stitch", "stitching", "sew", "sewing", "cloth", "clothes", "fabric", "blouse", "dress", "garment", "needle", "thread", "scissors", "தையல்", "துணி", "சட்டை", "தையல் இயந்திரம்", "सिलाई", "दर्जी", "कपड़ा", "ब्लाउज", "धागा", "కుట్టు", "బట్టలు", "సిల్వర్", "தையற்கலை", "সিলਾਈ", "দর্জি"],
        "qp_code": "AMH/Q0301",
        "tools": ["Sewing Machine", "Measuring Tape", "Fabric Scissors", "Tailoring Chalk", "Bobbin"]
    },
    "Custom Boutique & Designer Apparel": {
        "keywords": ["boutique", "designer", "embroidery", "aari", "zari", "salwar", "master tailor", "custom fit", "ஆரி", "ஜரிகை", "बुटीक", "कढ़ाई", "जरी", "జాకెట్", "জরির কাজ"],
        "qp_code": "AMH/Q1947",
        "tools": ["Adda Frame", "Aari Needle", "Master Cutting Table", "Pattern Scales"]
    },
    "Domestic Electrical & Appliance Repair": {
        "keywords": ["electric", "electrical", "electrician", "wire", "wiring", "switch", "fan", "motor", "repair", "tester", "plug", "fuse", "மின்னியல்", "மின்சாரம்", "வயரிங்", "பேன்", "बिजली", "वायरिंग", "स्विच", "पंखा", "इलेक्ट्रीशियन", "కరెంట్", "వైరింగ్", "ఫ్యాన్", "ವಿದ್ಯುತ್", "বৈদ্যুতিক"],
        "qp_code": "ELE/Q6001",
        "tools": ["Digital Multimeter", "Insulated Plier", "Screw Driver Set", "Voltage Tester", "Wire Stripper"]
    },
    "Solar PV & Surya Mitra": {
        "keywords": ["solar", "panel", "solar rooftop", "inverter", "battery", "surya mitra", "சூரிய மின்சக்தி", "சோலார்", "सोलर", "सौर ऊर्जा", "ಸೌರ", "সৌর"],
        "qp_code": "ELE/Q5901",
        "tools": ["Solar Angle Finder", "Crimping Tool", "MC4 Connector Tool", "Multimeter"]
    },
    "Mobile Phone Repair": {
        "keywords": ["mobile", "phone", "smartphone", "screen", "display", "mic", "speaker", "soldering", "charger", "மொபைல்", "செல்போன்", "मोबाइल", "स्क्रीन", "మొబైల్", "ಮೊಬೈಲ್", "মোবাইল"],
        "qp_code": "ELE/Q8104",
        "tools": ["SMD Rework Station", "Soldering Iron", "Magnifying Lens", "Display Separator"]
    },
    "Food Processing & Preservation": {
        "keywords": ["pickle", "pickles", "jam", "snacks", "papad", "chips", "food", "cook", "cooking", "sweets", "spices", "ஊறுகாய்", "அப்பளம்", "உணவு", "अचार", "पापड़", "नमकीन", "खाना", "মিষ্টি", "পাপড়", "ಉಪ್ಪಿನಕಾಯಿ", "పచ్చళ్ళు"],
        "qp_code": "FIC/Q0103",
        "tools": ["Sealing Machine", "Digital Weighing Scale", "Stainless Steel Vessels", "Sterilizer Jar"]
    },
    "Bakery & Confectionery": {
        "keywords": ["bakery", "bake", "baking", "bread", "cake", "pav", "biscuit", "oven", "dough", "ரொட்டி", "கேக்", "பேக்கரி", "बेकरी", "केक", "पाव", "बिस्कुट", "ওভেন", "কেক"],
        "qp_code": "FIC/Q5003",
        "tools": ["Deck Oven", "Dough Mixer", "Baking Trays", "Cake Spatula"]
    },
    "Two-Wheeler Mechanic & Garage": {
        "keywords": ["bike", "motorcycle", "scooter", "garage", "mechanic", "engine", "oil change", "brake", "clutch", "பைக்கர்", "மெக்கானிக்", "பைக்", "बाइक", "स्कूटर", "गैरेज", "इंजन", "మెకానిక్", "బైక్"],
        "qp_code": "ASC/Q1411",
        "tools": ["Socket Wrench Set", "Spanners", "Spark Plug Gauge", "Oil Drain Pan", "Air Compressor"]
    },
    "Auto Electrician & EV": {
        "keywords": ["auto electric", "e-rickshaw", "ev", "auto battery", "dynamo", "starter", "ஆட்டோ எலக்ட்ரிக்", "ई-रिक्शा", "ऑटो बैटरी", "బ్యాటరీ రిపేర్"],
        "qp_code": "ASC/Q1408",
        "tools": ["Battery Load Tester", "Wire Crimper", "Multimeter", "Battery Charger"]
    },
    "Plumbing & Sanitation": {
        "keywords": ["plumber", "plumbing", "pipe", "tap", "drain", "water tank", "leak", "sink", "bathroom", "குழாய்", "தண்ணீர் குழாய்", "ப்ளம்பர்", "नल", "प्लंबर", "पाइप", "लीकेज", "నీళ్ల పైపులు", "ಪ್ಲಂಬರ್", "প্লাম্বার"],
        "qp_code": "PSC/Q0104",
        "tools": ["Pipe Wrench", "Hacksaw", "Thread Seal Tape", "Pipe Cutter", "Plunger"]
    },
    "Masonry & Construction": {
        "keywords": ["mason", "brick", "cement", "mortar", "plaster", "wall", "building", "construction", "house", "கொத்தனார்", "கட்டுமானம்", "செங்கல்", "राजमिस्त्री", "ईंट", "सीमेंट", "प्लास्टर", "మేస్త్రీ", "ఇటుకలు", "ಕಟ್ಟಡ", "রাজমিস্ত্রি"],
        "qp_code": "CON/Q0102",
        "tools": ["Trowel", "Spirit Level", "Plumb Bob", "Mortar Pan", "Right Angle Square"]
    },
    "Healthcare & Patient Care (GDA)": {
        "keywords": ["hospital", "patient", "nurse", "nursing", "medicine", "first aid", "vital signs", "clinic", "மருத்துவமனை", "நோயாளி", "அரவணைப்பு", "अस्पताल", "मरीज", "दवा", "నర్సింగ్", "వైద్యశాల", "হাসপাতাল"],
        "qp_code": "HSS/Q5101",
        "tools": ["BP Monitor", "Pulse Oximeter", "Digital Thermometer", "First Aid Kit"]
    },
    "Retail & Kirana Store": {
        "keywords": ["shop", "store", "retail", "kirana", "sales", "billing", "customer", "pos", "goods", "கடை", "சில்லறை விற்பனை", "பில்", "दुकान", "किराना", "बिक्री", "ग्राहक", "షాప్", "దుకాణం", "দোকান"],
        "qp_code": "RAS/Q0104",
        "tools": ["POS Machine", "Barcode Scanner", "UPI QR Stand", "Inventory Register"]
    },
    "Bamboo & Handicrafts": {
        "keywords": ["bamboo", "cane", "basket", "craft", "artisan", "handicraft", "weaving", "மூங்கில்", "கூடை", "கைவினை", "बांस", "टोकरी", "हस्तशिल्प", "వెదురు", "ಬುಟ್ಟಿ", "বাঁশ"],
        "qp_code": "HCS/Q8702",
        "tools": ["Bamboo Slicing Knife", "Shaving Tool", "Weaving Awl", "Measuring Scale"]
    }
}

def extract_experience_from_text(text):
    exp_match = re.search(r'(\d+)\s*(?:years?|yrs?|saal|sal|varusham|varushangal|samvatsaralu|varsha|varshangal|bochhor|mahine|months?|masam)', text, re.IGNORECASE)
    if exp_match:
        return f"{exp_match.group(1)} years"
    
    if any(w in text.lower() for w in ["traditional", "childhood", "many years", "parambariyam", "bachpan", "bahut saal"]):
        return "5+ years (Traditional / Family livelihood)"
    elif any(w in text.lower() for w in ["recently", "new", "pudhusa", "naya"]):
        return "1 year"
    return ""

def calculate_communication_signal(history):
    user_msgs = [m["content"] for m in history if m.get("role") == "user" and m.get("content")]
    if not user_msgs:
        return {"score": 75, "clarity": "Moderate", "details": "Initial greeting response."}
    
    total_words = sum(len(m.split()) for m in user_msgs)
    avg_len = total_words / max(len(user_msgs), 1)
    
    has_specifics = any(re.search(r'\d+', m) for m in user_msgs) or any(len(m.split()) > 6 for m in user_msgs)
    
    if avg_len >= 12 and has_specifics:
        score = min(96, 85 + int(avg_len))
        clarity = "High Clarity & Detailed Articulation"
    elif avg_len >= 6:
        score = 80 + int(avg_len * 1.2)
        clarity = "Good Expressiveness & Action-Oriented"
    else:
        score = 70 + int(avg_len * 2)
        clarity = "Concise Vernacular Expression"
        
    return {
        "score": score,
        "clarity": clarity,
        "articulation_detail": f"Expresses daily workflow with {total_words} words across {len(user_msgs)} voice turns."
    }

def analyze_profile_heuristic(history, lang):
    user_texts = " ".join([m["content"] for m in history if m.get("role") == "user"])
    text_lower = user_texts.lower()
    
    matched_domains = []
    extracted_tools = []
    extracted_activities = []
    suggested_qp = "AGR/Q8101"
    
    for domain, meta in DOMAIN_KEYWORD_MAP.items():
        count = sum(1 for kw in meta["keywords"] if kw in text_lower)
        if count > 0:
            matched_domains.append((domain, count, meta))
            
    if matched_domains:
        matched_domains.sort(key=lambda x: -x[1])
        top_domain, _, meta = matched_domains[0]
        suggested_qp = meta["qp_code"]
        extracted_tools = meta["tools"]
        extracted_activities = [f"Daily operational work in {top_domain}"]
    else:
        top_domain = "General Rural Livelihood"
        extracted_tools = ["Standard Manual Tools"]
        extracted_activities = ["Daily vocational activity"]
        
    exp = extract_experience_from_text(user_texts) or "2-3 years"
    freq = "Daily (Full-time / Active)" if any(w in text_lower for w in ["daily", "every day", "dinamum", "roz", "prati roju", "protidin"]) else "Regular"
    
    comm = calculate_communication_signal(history)
    
    has_activity = bool(matched_domains) or len(user_texts.split()) > 5
    has_tools = bool(extracted_tools) or any(w in text_lower for w in ["machine", "tool", "gear", "pan", "needle", "wire", "can"])
    has_exp = bool(exp and exp != "2-3 years") or len(history) >= 4
    
    enough = has_activity and (has_tools or has_exp or len(history) >= 4)
    
    profile = {
        "domain": top_domain,
        "activities": extracted_activities,
        "tools": extracted_tools,
        "frequency": freq,
        "experience": exp,
        "suggested_qp": suggested_qp,
        "communication": f"{comm['clarity']} (Signal Score: {comm['score']}%)"
    }
    
    lang_key = lang if lang in LOCALIZED_PROMPTS else "en-IN"
    if enough:
        reply = LOCALIZED_PROMPTS[lang_key]["complete"]
    elif not has_tools:
        reply = LOCALIZED_PROMPTS[lang_key]["need_tools"]
    elif not has_exp:
        reply = LOCALIZED_PROMPTS[lang_key]["need_exp"]
    else:
        reply = LOCALIZED_PROMPTS[lang_key]["complete"]
        enough = True
        
    return {"reply": reply, "profile": profile, "enough": enough}

# ----------------- NVIDIA Nemotron-3 Reasoning & Discovery Agent (Agent 1) -----------------
def call_discovery_agent(history, lang, current_profile):
    """
    Executes Agent 1 (Discovery) using NVIDIA Nemotron-3 Super 120B (MoE) reasoning.
    """
    lang_info = LANGS.get(lang, {"name": "English", "native": "English"})
    lang_name = lang_info["name"]

    if NEMOTRON_CLIENT:
        try:
            system_prompt = f"""You are Agent 1 (Discovery Agent) of NARMADA, powered by NVIDIA Nemotron-3 Super 120B reasoning, mapping rural and informal livelihoods to NSQF skilling programs under PM-AJAY.

Your Responsibilities:
1. Speak in {lang_name} warmly, simply, and empathetically for low-literacy citizens.
2. Ask only ONE short follow-up question per turn if vital info is missing (e.g. tools used or years of experience).
3. Reason over the user's vernacular voice message and extract structured work profile facts in English: domain, activities, tools, frequency, experience, communication signal.
4. Set enough=true once you have identified their primary activity, tools/materials, and experience.

Current Profile: {json.dumps(current_profile)}

Return STRICT JSON ONLY:
{{
  "reply": "Warm 1-2 sentence response/question in {lang_name}",
  "profile": {{
    "domain": "e.g. Dairy / Tailoring / Electronics / Food Processing / Solar PV",
    "activities": ["list of concrete tasks"],
    "tools": ["list of tools/equipment"],
    "frequency": "Daily / Seasonal / Part-time",
    "experience": "e.g. 4 years",
    "communication": "Brief note on citizen confidence and articulation clarity"
  }},
  "enough": true/false
}}"""
            res = NEMOTRON_CLIENT.chat.completions.create(
                model=NEMOTRON_MODEL,
                temperature=0.2,
                max_tokens=2048,
                messages=[{"role": "system", "content": system_prompt}] + history
            )
            raw_content = res.choices[0].message.content
            parsed = clean_json_response(raw_content)
            
            if parsed and "reply" in parsed and "profile" in parsed:
                # Localize reply with Riva Translate if language is not English and reply was in English
                reply_text = parsed["reply"]
                if lang != "en-IN" and not any(ord(c) > 127 for c in reply_text):
                    reply_text = translate_with_riva(reply_text, src_lang="en-IN", target_lang=lang)
                    parsed["reply"] = reply_text
                return parsed
        except Exception as e:
            print(f"[Warning] Nemotron Discovery Agent error: {e}. Utilizing built-in Indic NLP agent.")

    return analyze_profile_heuristic(history, lang)

# ----------------- NVIDIA Nemotron-3 Grounded Guidance Agent (Agent 2) -----------------
def call_guidance_agent(profile, lang, qp_matches, rules):
    """
    Executes Agent 2 (Guidance & Mentoring) using NVIDIA Nemotron-3 Super 120B reasoning and Riva Translate.
    """
    lang_info = LANGS.get(lang, {"name": "English", "native": "English"})
    lang_name = lang_info["name"]
    
    if NEMOTRON_CLIENT:
        try:
            ctx = "### MATCHED NSQF QUALIFICATION PACKS:\n"
            for qp in qp_matches:
                ctx += f"Code: [{qp['code']}] | Title: {qp['title']} | Sector: {qp['sector']} | NSQF Level: {qp['level']}\n"
                ctx += f"Description: {qp['body']}\n"
                ctx += f"Modules: {qp.get('modules', '[]')}\n"
                ctx += f"Career Path: {qp.get('career_path', '')}\n"
                ctx += f"Wage Potential: {qp.get('wage_potential', '')}\n"
                ctx += f"PM-AJAY Support: {qp.get('pm_ajay_grant', '')}\n\n"
            
            ctx += "### PM-AJAY GIA SCHEME RULES:\n"
            for r in rules:
                ctx += f"[{r['code']}] {r['title']}: {r['body']}\n"
                
            system_prompt = f"""You are Agent 2 (Guidance & Mentoring Agent) of NARMADA, powered by NVIDIA Nemotron-3 Super 120B.
Recommend the single best-fit NSQF Qualification Pack from the provided documents that recognizes what this citizen already knows and elevates their livelihood under PM-AJAY GIA.
Every recommendation MUST cite the exact QP Code and explain the deterministic PM-AJAY eligibility.
Provide the why, eligibility, next step, and spoken explanation in {lang_name}.

Context Documents:
{ctx}

Return STRICT JSON ONLY:
{{
  "code": "Exact QP Code from context",
  "title": "Exact Title",
  "sector": "Sector name",
  "level": 4,
  "why": "Detailed 2-3 sentence rationale linking citizen's extracted tools/tasks to this certified qualification (in {lang_name})",
  "eligibility": "Deterministic PM-AJAY GIA entitlement breakdown: 100% free training, ₹15,000 tool-kit subsidy, SC quota eligibility (in {lang_name})",
  "training_modules": ["3-4 key training curriculum modules"],
  "career_path": "Career progression string",
  "wage_potential": "Expected earning potential string",
  "pm_ajay_benefit": "Grant & stipend support details",
  "nearest_center": "Pradhan Mantri Kaushal Kendra (PMKK) & District SC Development Office",
  "next_step": "Clear next action for the citizen (e.g. visit nearest center with Aadhaar card) (in {lang_name})",
  "alternatives": [{{"code": "string", "title": "string", "sector": "string"}}],
  "spoken": "3-4 crystal clear, comforting, empowering sentences in {lang_name} to be read aloud via voice synthesis."
}}"""
            res = NEMOTRON_CLIENT.chat.completions.create(
                model=NEMOTRON_MODEL,
                temperature=0.2,
                max_tokens=3000,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": json.dumps(profile)}]
            )
            raw_content = res.choices[0].message.content
            parsed = clean_json_response(raw_content)
            if parsed and "code" in parsed and "spoken" in parsed:
                return parsed
        except Exception as e:
            print(f"[Warning] Nemotron Guidance Agent error: {e}. Utilizing built-in deterministic guidance engine.")

    # High-fidelity Deterministic Guidance Engine Fallback
    top_qp = qp_matches[0] if qp_matches else None
    if not top_qp:
        top_qp = {
            "code": "AGR/Q8101",
            "title": "Dairy Farmer / Entrepreneur",
            "sector": "Agriculture & Allied",
            "level": 4,
            "body": "Rearing cattle, clean milk production, value addition.",
            "modules": '["Scientific Cattle Rearing", "Clean Milk Production", "Dairy Value Addition (Ghee, Curd)"]',
            "career_path": "Dairy Worker -> Commercial Dairy Farmer -> Dairy Cooperative Entrepreneur",
            "wage_potential": "₹18,000 - ₹35,000 / month",
            "pm_ajay_grant": "100% free NSQF skilling + ₹15,000 tool kit subsidy under PM-AJAY GIA"
        }

    modules = top_qp.get("modules")
    if isinstance(modules, str):
        try:
            modules = json.loads(modules)
        except Exception:
            modules = ["Core Competency Training", "Safety & Hygiene Standards", "PM-AJAY Enterprise Setup"]

    alternatives = []
    for alt in qp_matches[1:3]:
        alternatives.append({
            "code": alt.get("code", ""),
            "title": alt.get("title", ""),
            "sector": alt.get("sector", "")
        })

    spoken_map = {
        "en-IN": f"Based on your daily experience in {profile.get('domain', 'your work')}, we have matched you to {top_qp['title']} at NSQF Level {top_qp['level']}. Under the PM-AJAY scheme, your entire training is 100% free and you are eligible for tool kit support up to ₹15,000. Please bring your Aadhaar card to the nearest Kaushal Kendra to register.",
        "hi-IN": f"आपके {profile.get('domain', 'दैनिक कार्य')} के अनुभव के आधार पर, आपको NSQF स्तर {top_qp['level']} के अंतर्गत '{top_qp['title']}' से जोड़ा गया है। PM-AJAY योजना के तहत आपका पूरा प्रशिक्षण बिल्कुल मुफ्त है और आपको ₹15,000 तक की टूलकिट सहायता मिलेगी। कृपया अपने आधार कार्ड के साथ नजदीकी कौशल केंद्र पर जाएं।",
        "ta-IN": f"உங்கள் {profile.get('domain', 'பணி')} அனுபவத்தின் அடிப்படையில், நீங்கள் NSQF நிலை {top_qp['level']} சான்றிதழான '{top_qp['title']}' பயிற்சிக்கு தகுதி பெற்றுள்ளீர்கள். PM-AJAY திட்டத்தின் கீழ் உங்கள் முழு பயிற்சியும் 100% இலவசம் மற்றும் ₹15,000 வரை கருவித்தொகுப்பு உதவித்தொகை வழங்கப்படும். உடனடியாக உங்கள் ஆதார் அட்டையுடன் அருகில் உள்ள திறன் மையத்தை அணுகவும்.",
        "te-IN": f"మీ {profile.get('domain', 'పని')} అనుభవం ఆధారంగా, మీరు NSQF స్థాయి {top_qp['level']} యొక్క '{top_qp['title']}' శిక్షణకు సరిపోలారు. PM-AJAY పథకం కింద మీ శిక్షణ పూర్తిగా ఉచితం మరియు ₹15,000 వరకు టూల్‌కిట్ గ్రాంట్ లభిస్తుంది. దయచేసి మీ ఆధార్ కార్డుతో సమీప కౌశల్ కేంద్రాన్ని సంప్రదించండి.",
        "kn-IN": f"ನಿಮ್ಮ {profile.get('domain', 'ಕೆಲಸದ')} ಅನುಭವದ ಆಧಾರದ ಮೇಲೆ, ನೀವು NSQF ಹಂತ {top_qp['level']} ರ '{top_qp['title']}' ತರಬೇತಿಗೆ ಆಯ್ಕೆಯಾಗಿದ್ದೀರಿ. PM-AJAY ಯೋಜನೆಯಡಿ ನಿಮ್ಮ ಸಂಪೂರ್ಣ ತರಬೇತಿ ಉಚಿತವಾಗಿದ್ದು, ₹15,000 ವರೆಗೆ ಉಪಕರಣ ಸಹಾಯಧನ ಸಿಗಲಿದೆ.",
        "ml-IN": f"നിങ്ങളുടെ തൊഴിൽ പരിചയത്തിന്റെ അടിസ്ഥാനത്തിൽ, നിങ്ങൾ NSQF ലെവൽ {top_qp['level']} കോഴ്‌സായ '{top_qp['title']}' ലേക്ക് തിരഞ്ഞെടുക്കപ്പെട്ടു. PM-AJAY പദ്ധതി പ്രകാരം സൗജന്യ പരിശീലനവും ₹15,000 ടൂൾകിറ്റ് സഹായവും ലഭിക്കും.",
        "mr-IN": f"आपल्या अनुभवाच्या आधारे, आपल्याला NSQF स्तर {top_qp['level']} अंतर्गत '{top_qp['title']}' साठी निवडले आहे. PM-AJAY योजनेअंतर्गत आपले प्रशिक्षण मोफत असून ₹15,000 टूलकिट अनुदान मिळेल.",
        "bn-IN": f"আপনার কাজের অভিজ্ঞতার ভিত্তিতে, আপনাকে NSQF স্তর {top_qp['level']} এর '{top_qp['title']}' কোর্সে যুক্ত করা হয়েছে। PM-AJAY প্রকল্পে আপনার প্রশিক্ষণ ১০০% বিনামূল্যে হবে এবং ₹১৫,০০০ পর্যন্ত টুলকিট অনুদান পাবেন।"
    }

    why_map = {
        "en-IN": f"Your practical experience with {', '.join(profile.get('tools', ['specialized tools']))} directly fulfills the competencies for {top_qp['title']} (NSQF Level {top_qp['level']}). This certification converts your informal livelihood into a nationally recognized qualification.",
        "hi-IN": f"आपके द्वारा उपयोग किए जाने वाले औजारों ({', '.join(profile.get('tools', ['संबंधित औजार']))}) और कार्यशैली के आधार पर {top_qp['title']} (NSQF स्तर {top_qp['level']}) आपके लिए सर्वोत्तम प्रमाणन है।",
        "ta-IN": f"நீங்கள் பயன்படுத்தும் கருவிகள் ({', '.join(profile.get('tools', ['சிறப்பு கருவிகள்']))}) மற்றும் நடைமுறை அனுபவம் நேரடியாக {top_qp['title']} (NSQF நிலை {top_qp['level']}) தகுதித் தொகுப்புடன் பொருந்துகிறது."
    }

    spoken_text = spoken_map.get(lang, spoken_map["en-IN"])
    why_text = why_map.get(lang, why_map["en-IN"])

    return {
        "code": top_qp["code"],
        "title": top_qp["title"],
        "sector": top_qp.get("sector", "Vocational Skilling"),
        "level": top_qp.get("level", 4),
        "why": why_text,
        "eligibility": "100% Central Government Grant under PM-AJAY GIA Component for Scheduled Caste (SC) Beneficiaries. Includes zero course fee, travel stipend & ₹15,000 tool kit subsidy.",
        "training_modules": modules,
        "career_path": top_qp.get("career_path", "Vocational Practitioner -> Certified Specialist -> Enterprise Lead"),
        "wage_potential": top_qp.get("wage_potential", "₹18,000 - ₹35,000 / month"),
        "pm_ajay_benefit": top_qp.get("pm_ajay_grant", "Full scholarship + Tool kit grant up to ₹15,000"),
        "nearest_center": "District Pradhan Mantri Kaushal Kendra (PMKK) & State SC Development Corporation",
        "next_step": "Visit your nearest PMKK center or District Welfare Office with your Aadhaar card and Bank Passbook to confirm your PM-AJAY batch enrollment.",
        "alternatives": alternatives,
        "spoken": spoken_text
    }

# ----------------- Flask Routes & REST Endpoints -----------------

@app.route("/")
def home():
    return render_template("index.html", langs=LANGS)

@app.get("/api/models")
def get_model_info():
    """
    Returns active AI model configuration and status for all three separate models.
    """
    return jsonify({
        "provider": "NVIDIA AI Foundation Models (NIM / Riva)",
        "models": {
            "speech_to_text": {
                "name": "NVIDIA Parakeet ASR",
                "model_id": PARAKEET_ASR_MODEL,
                "server": PARAKEET_ASR_SERVER,
                "connected": bool(RIVA_ASR_SERVICE) or bool(PARAKEET_API_KEY),
                "key_configured": bool(PARAKEET_API_KEY)
            },
            "reasoning_generation": {
                "name": "NVIDIA Nemotron-3 Super 120B",
                "model_id": NEMOTRON_MODEL,
                "endpoint": NEMOTRON_BASE_URL,
                "connected": bool(NEMOTRON_CLIENT),
                "key_configured": bool(NEMOTRON_API_KEY)
            },
            "text_translation": {
                "name": "NVIDIA Riva-Translate-4B-Instruct-v2",
                "model_id": RIVA_TRANSLATE_MODEL,
                "endpoint": RIVA_TRANSLATE_BASE_URL,
                "connected": bool(RIVA_TRANSLATE_CLIENT),
                "key_configured": bool(RIVA_TRANSLATE_API_KEY)
            }
        },
        "all_connected": bool(NEMOTRON_CLIENT and (RIVA_TRANSLATE_CLIENT or NEMOTRON_CLIENT))
    })

@app.post("/api/transcribe")
def transcribe():
    """
    Endpoint for speech-to-text transcription using NVIDIA Parakeet ASR.
    Accepts multipart audio file or raw audio with optional language code.
    """
    lang = request.form.get("lang") or request.args.get("lang") or "en-IN"
    
    audio_file = request.files.get("audio") or request.files.get("file")
    transcript = None
    
    if audio_file:
        audio_bytes = audio_file.read()
        transcript = transcribe_with_parakeet(audio_bytes, lang_code=lang)
    
    if not transcript:
        # If no audio or audio parsing returned empty, return fallback/text echo
        fallback_text = request.form.get("text") or request.args.get("text") or ""
        transcript = fallback_text

    # Optionally provide English translation via Riva Translate if Indic
    translated = transcript
    if transcript and lang != "en-IN":
        translated = translate_with_riva(transcript, src_lang=lang, target_lang="en-IN")

    return jsonify({
        "transcript": transcript,
        "translated": translated,
        "model": PARAKEET_ASR_MODEL,
        "lang": lang
    })

@app.post("/api/translate")
def translate_endpoint():
    """
    Endpoint for text translation using NVIDIA Riva-Translate-4B-Instruct-v2.
    """
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "")
    src_lang = data.get("src_lang", "en-IN")
    target_lang = data.get("target_lang", "hi-IN")
    
    translated_text = translate_with_riva(text, src_lang=src_lang, target_lang=target_lang)
    return jsonify({
        "original": text,
        "translated": translated_text,
        "src_lang": src_lang,
        "target_lang": target_lang,
        "model": RIVA_TRANSLATE_MODEL
    })

@app.post("/api/start")
def start():
    data = request.get_json(force=True, silent=True) or {}
    lang = data.get("lang", "en-IN")
    if lang not in LANGS:
        lang = "en-IN"
        
    sid = uuid.uuid4().hex
    
    consent_meta = {
        "consented": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "purpose": "PM-AJAY Livelihood Skill Mapping & Continuous Voice Mentoring",
        "retention_policy": "Minimal Session Retention with Cryptographic Hashing"
    }
    
    greeting = LOCALIZED_GREETINGS.get(lang, LOCALIZED_GREETINGS["en-IN"])
    
    initial_history = [{"role": "assistant", "content": greeting}]
    initial_profile = {
        "domain": "",
        "activities": [],
        "tools": [],
        "frequency": "",
        "experience": "",
        "communication": "Session initiated"
    }
    
    execute_query("""
        INSERT INTO sessions (id, lang, history, profile, status, dpdp_consent, created)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        sid,
        lang,
        json.dumps(initial_history),
        json.dumps(initial_profile),
        "active",
        json.dumps(consent_meta),
        datetime.now(timezone.utc).isoformat()
    ))
    
    execute_query("""
        INSERT INTO dpdp_logs (id, session_id, action, timestamp, details)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        uuid.uuid4().hex,
        sid,
        "CONSENT_GRANTED_AND_SESSION_START",
        datetime.now(timezone.utc).isoformat(),
        json.dumps({"lang": lang, "purpose": consent_meta["purpose"], "ai_models": {"stt": PARAKEET_ASR_MODEL, "llm": NEMOTRON_MODEL, "nmt": RIVA_TRANSLATE_MODEL}})
    ))
    
    return jsonify({
        "sid": sid,
        "reply": greeting,
        "lang": lang,
        "profile": initial_profile,
        "models": {
            "stt": PARAKEET_ASR_MODEL,
            "llm": NEMOTRON_MODEL,
            "nmt": RIVA_TRANSLATE_MODEL
        }
    })

@app.post("/api/chat")
def chat():
    data = request.get_json(force=True, silent=True) or {}
    sid = data.get("sid")
    message = (data.get("message") or "").strip()
    
    if not sid:
        return jsonify({"error": "Missing session ID"}), 400
        
    session = execute_query("SELECT * FROM sessions WHERE id=%s", (sid,), fetch="one")
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    history = json.loads(session["history"]) if isinstance(session["history"], str) else (session["history"] or [])
    current_profile = json.loads(session["profile"]) if isinstance(session["profile"], str) else (session["profile"] or {})
    lang = session["lang"]
    
    if message:
        history.append({"role": "user", "content": message})
        
    # Execute Agent 1 (Discovery Agent via NVIDIA Nemotron-3-Super-120B)
    discovery_out = call_discovery_agent(history, lang, current_profile)
    
    assistant_reply = discovery_out.get("reply", "Please tell me more about your work.")
    updated_profile = discovery_out.get("profile", current_profile)
    is_enough = discovery_out.get("enough", False)
    
    history.append({"role": "assistant", "content": assistant_reply})
    
    execute_query("""
        UPDATE sessions SET history=%s, profile=%s WHERE id=%s
    """, (json.dumps(history), json.dumps(updated_profile), sid))
    
    return jsonify({
        "reply": assistant_reply,
        "profile": updated_profile,
        "enough": is_enough,
        "history_count": len(history),
        "model": NEMOTRON_MODEL
    })

@app.post("/api/recommend")
def recommend():
    data = request.get_json(force=True, silent=True) or {}
    sid = data.get("sid")
    if not sid:
        return jsonify({"error": "Missing session ID"}), 400
        
    session = execute_query("SELECT * FROM sessions WHERE id=%s", (sid,), fetch="one")
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    profile = json.loads(session["profile"]) if isinstance(session["profile"], str) else (session["profile"] or {})
    history = json.loads(session["history"]) if isinstance(session["history"], str) else (session["history"] or [])
    lang = session["lang"]
    
    # Query Knowledge Base (Hybrid RAG)
    all_kb_rows = execute_query("SELECT * FROM kb", fetch="all") or []
    qp_rows = [r for r in all_kb_rows if r["kind"] == "qp"]
    rule_rows = [r for r in all_kb_rows if r["kind"] == "rule"]
    
    user_texts = " ".join([m['content'] for m in history if m.get('role') == 'user'])
    # If user message is in Indic language, translate to English for RAG matching
    if lang != "en-IN" and user_texts:
        translated_user_text = translate_with_riva(user_texts, src_lang=lang, target_lang="en-IN")
    else:
        translated_user_text = user_texts

    query_text = f"{profile.get('domain', '')} {' '.join(profile.get('activities', []))} {' '.join(profile.get('tools', []))} {translated_user_text}"
    
    # High-accuracy Token Weighted similarity
    all_texts = [f"{q['title']} {q['sector']} {q['body']}" for q in qp_rows]
    vocab, doc_freqs = compute_term_freqs(all_texts)
    N = len(qp_rows)
    
    query_tokens = simple_tokenize(query_text)
    query_vec = tfidf_vector(query_tokens, vocab, N, vocab)
    
    scored_qps = []
    for idx, qp in enumerate(qp_rows):
        doc_tokens = simple_tokenize(f"{qp['title']} {qp['sector']} {qp['body']}")
        doc_vec = tfidf_vector(doc_tokens, vocab, N, vocab)
        score = sparse_cosine(query_vec, doc_vec)
        
        # Boost score if suggested_qp matches
        if profile.get("suggested_qp") and qp["code"] == profile.get("suggested_qp"):
            score += 0.4
            
        scored_qps.append((score, qp))
        
    scored_qps.sort(key=lambda x: -x[0])
    top_matches = [item[1] for item in scored_qps[:4]]
    
    # Execute Agent 2 (Guidance & Mentorship Agent via NVIDIA Nemotron-3-Super-120B)
    rec_result = call_guidance_agent(profile, lang, top_matches, rule_rows)
    
    # Cryptographic Audit Hash for DPDP & Administrative Integrity
    audit_payload = f"{sid}:{rec_result['code']}:{datetime.now(timezone.utc).isoformat()}:{json.dumps(profile)}"
    audit_hash = hashlib.sha256(audit_payload.encode('utf-8')).hexdigest()
    rec_result["audit_hash"] = audit_hash
    rec_result["generated_at"] = datetime.now(timezone.utc).strftime("%d %B %Y, %I:%M %p UTC")
    rec_result["beneficiary_id"] = f"PMAJAY-SC-{sid[:8].upper()}"
    rec_result["model"] = NEMOTRON_MODEL
    rec_result["nmt_model"] = RIVA_TRANSLATE_MODEL
    
    execute_query("""
        UPDATE sessions SET rec=%s, audit_hash=%s WHERE id=%s
    """, (json.dumps(rec_result), audit_hash, sid))
    
    execute_query("""
        INSERT INTO dpdp_logs (id, session_id, action, timestamp, details)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        uuid.uuid4().hex,
        sid,
        "RECOMMENDATION_GENERATED_AND_HASHED",
        datetime.now(timezone.utc).isoformat(),
        json.dumps({"qp_code": rec_result["code"], "audit_hash": audit_hash, "model": NEMOTRON_MODEL})
    ))
    
    return jsonify(rec_result)

@app.post("/api/mentor")
def mentor_checkin():
    data = request.get_json(force=True, silent=True) or {}
    sid = data.get("sid")
    week = int(data.get("week", 1))
    user_status = data.get("status", "progressing")
    user_feedback = data.get("feedback", "")
    
    if not sid:
        return jsonify({"error": "Missing session ID"}), 400
        
    session = execute_query("SELECT * FROM sessions WHERE id=%s", (sid,), fetch="one")
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    rec = json.loads(session["rec"]) if isinstance(session["rec"], str) else (session["rec"] or {})
    lang = session["lang"]
    course_title = rec.get("title", "NSQF Skilling Program")
    
    # Localized weekly mentor responses
    mentor_responses = {
        1: {
            "en-IN": f"Week 1 Check-in: Great job starting your journey in {course_title}! Have you collected your training handbook and tool kit from the training center? Keep practicing daily.",
            "hi-IN": f"सप्ताह 1 समीक्षा: {course_title} में अपनी यात्रा शुरू करने के लिए बधाई! क्या आपने प्रशिक्षण केंद्र से अपनी हैंडबुक और टूलकिट प्राप्त कर ली है? नियमित रूप से अभ्यास जारी रखें।",
            "ta-IN": f"வாரம் 1 வழிகாட்டல்: {course_title} பயிற்சியில் உங்கள் பயணத்தை தொடங்கியதற்கு வாழ்த்துகள்! பயிற்சி மையத்தில் உங்கள் கையேடு மற்றும் கருவித்தொகுப்பை பெற்றுவிட்டீர்களா? தினமும் பயிற்சியை தொடருங்கள்.",
            "te-IN": f"వారం 1 మార్గదర్శనం: {course_title} లో మీ ప్రయాణాన్ని ప్రారంభించినందుకు అభినందనలు! శిక్షణా కేంద్రం నుండి టూల్‌కిట్ అందుకున్నారా? రోజూ సాధన చేయండి."
        },
        2: {
            "en-IN": f"Week 2 Check-in: You are now at the practical skill module for {course_title}. Your PM-AJAY conveyance stipend is being processed directly to your Aadhaar-linked bank account.",
            "hi-IN": f"सप्ताह 2 समीक्षा: आप {course_title} के व्यावहारिक कौशल चरण में हैं। आपका PM-AJAY यात्रा भत्ता सीधे आपके आधार से जुड़े बैंक खाते में भेजा जा रहा है।",
            "ta-IN": f"வாரம் 2 வழிகாட்டல்: {course_title} பயிற்சியின் செய்முறை பகுதிக்கு வந்துள்ளீர்கள். உங்கள் PM-AJAY உதவித்தொகை உங்கள் ஆதார் இணைக்கப்பட்ட வங்கிக் கணக்கிற்கு நேரடியாக அனுப்பப்படுகிறது.",
            "te-IN": f"వారం 2 మార్గదర్శనం: మీరు ఇప్పుడు ప్రాక్టికల్ శిక్షణలో ఉన్నారు. మీ PM-AJAY స్టైపెండ్ మీ ఆధార్ లింక్ చేయబడిన బ్యాంక్ ఖాతాలో జమ చేయబడుతోంది."
        },
        3: {
            "en-IN": f"Week 3 & Beyond: Certification milestone! Prepare for your NCVET skill assessment test. Post-certification, our guidance agent will connect you to PM-AJAY Income Generation Project micro-loans up to ₹50,000.",
            "hi-IN": f"सप्ताह 3 व आगे: प्रमाणन चरण! अपने NCVET कौशल मूल्यांकन की तैयारी करें। प्रमाणन के बाद, आपको ₹50,000 तक के PM-AJAY आय सृजन माइक्रो-ऋण से जोड़ा जाएगा।",
            "ta-IN": f"வாரம் 3 மற்றும் சான்றிதழ்: NCVET திறன் மதிப்பீட்டுத் தேர்வுக்கு தயாராகுங்கள். சான்றிதழ் பெற்றவுடன், ₹50,000 வரையிலான PM-AJAY சுயதொழில் கடன் உதவிக்கு இணைப்பு ஏற்படுத்தப்படும்.",
            "te-IN": f"వారం 3 & ధృవీకరణ: NCVET అసెస్‌మెంట్ కోసం సిద్ధం అవ్వండి. సర్టిఫికేషన్ తర్వాత ₹50,000 వరకు PM-AJAY మైక్రో-లోన్ లింకేజ్ అందించబడుతుంది."
        }
    }
    
    week_key = week if week in [1, 2, 3] else 1
    spoken_text = mentor_responses[week_key].get(lang)
    if not spoken_text:
        base_en = mentor_responses[week_key]["en-IN"]
        spoken_text = translate_with_riva(base_en, src_lang="en-IN", target_lang=lang)
    
    mentor_log = {
        "week": week,
        "status": user_status,
        "feedback": user_feedback,
        "mentor_reply": spoken_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": NEMOTRON_MODEL
    }
    
    existing_mentor_hist = json.loads(session["mentor_history"]) if isinstance(session["mentor_history"], str) else (session["mentor_history"] or [])
    existing_mentor_hist.append(mentor_log)
    
    execute_query("""
        UPDATE sessions SET mentor_history=%s WHERE id=%s
    """, (json.dumps(existing_mentor_hist), sid))
    
    return jsonify({
        "week": week,
        "mentor_reply": spoken_text,
        "next_milestone": "NCVET Practical Assessment & Tool Kit Handover",
        "mentor_history": existing_mentor_hist,
        "model": NEMOTRON_MODEL
    })

# ----------------- State Skilling Officer (Admin / Verification) Endpoints -----------------

@app.get("/api/officer/beneficiaries")
def officer_beneficiaries():
    rows = execute_query("SELECT * FROM sessions ORDER BY created DESC LIMIT 50", fetch="all") or []
    results = []
    for r in rows:
        prof = json.loads(r["profile"]) if isinstance(r["profile"], str) else (r.get("profile") or {})
        rec = json.loads(r["rec"]) if isinstance(r["rec"], str) else (r.get("rec") or {})
        results.append({
            "id": r["id"],
            "beneficiary_id": f"PMAJAY-SC-{r['id'][:8].upper()}",
            "lang": LANGS.get(r["lang"], {}).get("name", r["lang"]),
            "domain": prof.get("domain", "Pending Mapping"),
            "experience": prof.get("experience", "-"),
            "tools": prof.get("tools", []),
            "communication": prof.get("communication", "Standard"),
            "recommended_qp": rec.get("title", "Under Assessment"),
            "qp_code": rec.get("code", "-"),
            "nsqf_level": rec.get("level", "-"),
            "status": r.get("status", "active"),
            "officer_notes": r.get("officer_notes", ""),
            "audit_hash": r.get("audit_hash", "-"),
            "created": r.get("created", "")
        })
    return jsonify({"beneficiaries": results, "total": len(results)})

@app.post("/api/officer/action")
def officer_action():
    data = request.get_json(force=True, silent=True) or {}
    sid = data.get("sid")
    action = data.get("action", "approved")
    notes = data.get("notes", "")
    
    if not sid:
        return jsonify({"error": "Missing session ID"}), 400
        
    execute_query("""
        UPDATE sessions SET status=%s, officer_notes=%s WHERE id=%s
    """, (action, notes, sid))
    
    execute_query("""
        INSERT INTO dpdp_logs (id, session_id, action, timestamp, details)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        uuid.uuid4().hex,
        sid,
        f"OFFICER_REVIEW_{action.upper()}",
        datetime.now(timezone.utc).isoformat(),
        json.dumps({"action": action, "notes": notes})
    ))
    
    return jsonify({"success": True, "status": action, "notes": notes})

@app.get("/api/stats")
def stats():
    sess_row = execute_query("SELECT count(*) as total_sessions FROM sessions", fetch="one") or {"total_sessions": 0}
    rec_row = execute_query("SELECT count(*) as total_recs FROM sessions WHERE rec IS NOT NULL", fetch="one") or {"total_recs": 0}
    appr_row = execute_query("SELECT count(*) as approved FROM sessions WHERE status='approved'", fetch="one") or {"approved": 0}
    dpdp_row = execute_query("SELECT count(*) as dpdp_logs FROM dpdp_logs", fetch="one") or {"dpdp_logs": 0}
    
    return jsonify({
        "active_beneficiaries_mapped": sess_row.get("total_sessions", 0),
        "nsqf_recommendations_issued": rec_row.get("total_recs", 0),
        "officer_approved_grants": appr_row.get("approved", 0),
        "dpdp_trust_verifications": dpdp_row.get("dpdp_logs", 0),
        "models": {
            "speech_to_text": PARAKEET_ASR_MODEL,
            "reasoning_generating": NEMOTRON_MODEL,
            "text_translation": RIVA_TRANSLATE_MODEL
        },
        "national_benchmarks": {
            "pm_ajay_sc_beneficiaries_fy23_24": 70934,
            "skill_projects_approved_gia": 913,
            "sc_entered_nsqf_training": 30660,
            "sc_population_target": "201.38 Million (16.63%)",
            "income_generation_beneficiaries": "1.94 Lakhs"
        }
    })

@app.get("/api/kb")
def get_knowledge_base():
    rows = execute_query("SELECT code, kind, title, sector, level, min_education, body, modules, career_path, wage_potential, pm_ajay_grant FROM kb", fetch="all") or []
    for r in rows:
        if isinstance(r.get("modules"), str):
            try:
                r["modules"] = json.loads(r["modules"])
            except Exception:
                pass
    return jsonify({"knowledge_base": rows, "count": len(rows)})

# Initialize Database upon server launch
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
