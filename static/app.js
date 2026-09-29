const $=id=>document.getElementById(id);let sid=null,size=16;
function fs(d){size=d?size+d:16;document.documentElement.style.fontSize=size+"px"}
const say=(t,lang)=>{if(!window.speechSynthesis)return;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t);u.lang=lang;speechSynthesis.speak(u)};
const add=(t,c)=>{const d=document.createElement("div");d.className="b "+c;d.textContent=t;$("log").append(d);$("log").scrollTop=1e9};
const post=(u,b)=>fetch(u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)}).then(r=>{if(!r.ok)throw Error(r.status);return r.json()});
const list=a=>(a&&a.length?a.join(", "):"-");
function showProf(p){$("prof").innerHTML=`<dt>Activities</dt><dd>${list(p.activities)}</dd><dt>Tools</dt><dd>${list(p.tools)}</dd><dt>Experience</dt><dd>${p.experience||"-"}</dd>`}
$("begin").onclick=async()=>{try{const r=await post("/api/start",{lang:$("lang").value});sid=r.sid;add(r.reply,"a");say(r.reply,$("lang").value);["msg","send","mic","rec"].forEach(i=>$(i).disabled=false);$("begin").disabled=true}catch(e){add("Could not start. Check server settings and try again.","a")}};
async function send(){const m=$("msg").value.trim();if(!m)return;$("msg").value="";add(m,"u");try{const r=await post("/api/chat",{sid,message:m});add(r.reply,"a");say(r.reply,$("lang").value);showProf(r.profile);if(r.enough)$("rec").focus()}catch(e){add("Something went wrong. Please send your answer again.","a")}}
$("send").onclick=send;$("msg").onkeydown=e=>{if(e.key==="Enter")send()};
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
$("mic").onclick=()=>{if(!SR){alert("Voice input needs Chrome or Edge. You can type instead.");return}const r=new SR();r.lang=$("lang").value;$("mic").classList.add("on");r.onresult=e=>{$("msg").value=e.results[0][0].transcript;send()};r.onend=()=>$("mic").classList.remove("on");r.start()};
$("rec").onclick=async()=>{$("rec").disabled=true;try{const r=await post("/api/recommend",{sid});$("result").hidden=false;$("rbody").innerHTML=`<p><span class="badge">${r.code}</span> NSQF Level ${r.level}</p><h4>${r.title}</h4><p>${r.why}</p><p><b>Eligibility:</b> ${r.eligibility}</p><p><b>Next step:</b> ${r.next_step}</p><p><small>Other options: ${(r.alternatives||[]).map(a=>a.title).join("; ")||"-"}</small></p>`;say(r.spoken,$("lang").value)}catch(e){add("Could not create the recommendation. Please try again.","a")}$("rec").disabled=false};
fetch("/api/stats").then(r=>r.json()).then(s=>$("st").textContent=`Citizens guided: ${s.recommendations}`).catch(()=>{});
