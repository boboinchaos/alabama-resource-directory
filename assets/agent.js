/* "Got a quick question? Click here" — chat + voice helper for Alabama Resource Directory.
   Runs entirely in the browser from /assets/agent-data.json. No account, no API key, nothing sent anywhere. */
(function(){
'use strict';
const NEED_WORDS={power:/\b(power|electric|light bill|lights (are |were |got )?(off|cut)|alabama power)/i,water:/\bwater\b/i,gas:/\b(gas bill|gas|heat|heating|propane|spire)\b/i,plumbing:/\b(plumb|pipe|leak|sewer|toilet|no running water)/i,roof:/\b(roof|shingles?|ceiling (is )?leak|leaking ceiling|home repairs?|house repairs?|repair (my|the|her|his) (house|home)|tarp)\b/i,
 food:/\b(food|hungry|groceries|grocery|pantry|eat|meals?|snap|food stamps)\b/i,rent:/\b(rent|evict|eviction|landlord|mortgage|behind on (the )?house|housing)\b/i,shelter:/\b(homeless|shelter|place to (stay|sleep|live)|nowhere to (stay|live|sleep|go)|living in (my|a|the|her|his) car|sleeping (outside|in (my|a|the|her|his) car)|on the streets?|kicked out|couch ?surfing|unhoused)\b/i,
 clothing:/\b(cloth|clothes|clothing|coat|coats|shoes|jacket)\b/i,furniture:/\b(furniture|bed|beds|mattress|couch|sofa|table|chairs?)\b/i,transport:/\b(ride|rides|transport|transportation|bus|car broke|no car|get to (the )?(doctor|appointments?|work))\b/i,
 equipment:/\b(wheelchair|walker|scooter|hospital bed|ramp|shower chair|lift|equipment|cane|oxygen|prosthe\w*|artificial (leg|arm|limb)|amputee|amputation|limb loss|brace|orthotic\w*|power chair)\b/i,respite:/\b(respite|caregiver|care giver|a break|break from|sitter|adult day|take care of (my|her|his))\b/i,
 benefits:/\b(social security|ssi|ssdi|disability check|medicaid|medicare|benefits)\b/i,health:/\b(doctor|clinic|medical|medicine|prescriptions?|dental|dentist|teeth|tooth|sick|health care|no insurance|uninsured)\b/i,foster:/\b(foster|kinship|grand(kids?|child|children|sons?|daughters?)|raising (my|her|his|their) (niece|nephew|sister|brother)|aging out|aged out|adopt\w*|custody|placed (with|in)|placement|casa)\b/i,job:/\b(job|work|unemploy|laid off|lost (my|her|his) (job|hours)|income)\b/i};
var D=null, ctx={county:null,need:null}, speakOn=false, rec=null, listening=false;
var $=function(s,r){return (r||document).querySelector(s)};
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function load(cb){ if(D) return cb(); fetch('/assets/agent-data.json').then(function(r){return r.json()}).then(function(j){D=j;cb()}).catch(function(){say('Sorry, I couldn\'t load the directory. Try the county menu at the top of the page.')}); }

/* ---------- UI ---------- */
var css='.ask-strip{background:#13233a;border-bottom:1px solid #2a4468}.ask-strip-in{display:flex;align-items:center;justify-content:center;gap:14px;min-height:54px;flex-wrap:wrap;padding-top:6px;padding-bottom:6px}.ask-hint{color:#a9bdd4;font-size:15px}@media(max-width:720px){.ask-hint{display:none}}.ask-bar{display:flex;gap:8px;align-items:center}.ask-btn{background:#4cc9f0;color:#0b1626;border:0;border-radius:999px;font:800 15px var(--display,system-ui);padding:9px 16px;cursor:pointer;display:inline-flex;gap:8px;align-items:center}.ask-btn svg{width:18px;height:18px}.ask-mic{background:#ffd23f;width:40px;height:40px;padding:0;justify-content:center}'+
'.ask-panel{position:fixed;right:16px;bottom:16px;width:min(420px,calc(100vw - 32px));height:min(620px,calc(100vh - 32px));background:#13233a;border:1px solid #2a4468;border-radius:18px;box-shadow:0 20px 60px rgba(0,0,0,.55);display:flex;flex-direction:column;z-index:50;color:#eef4fb;font:16px/1.5 var(--body,system-ui)}'+
'.ask-panel[hidden]{display:none}.ask-head{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid #2a4468}.ask-head b{font:800 17px var(--display,system-ui);flex:1}.ask-x{background:none;border:0;color:#a9bdd4;font-size:26px;cursor:pointer;line-height:1}'+
'.ask-log{flex:1;overflow:auto;padding:14px 16px;display:flex;flex-direction:column;gap:10px}.ask-m{max-width:92%;padding:10px 13px;border-radius:14px}.ask-m.bot{background:#1a2f4c;align-self:flex-start}.ask-m.me{background:#ffd23f;color:#0b1626;align-self:flex-end;font-weight:600}'+
'.ask-m a{color:#4cc9f0}.ask-m .ph{color:#ffd23f;font-weight:800;text-decoration:none}.ask-m ul{margin:6px 0 0;padding-left:18px}.ask-m li{margin:0 0 6px}.ask-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.ask-chip{background:#0b1626;border:1px solid #2a4468;color:#eef4fb;border-radius:999px;padding:5px 11px;font-size:14px;cursor:pointer}'+
'.ask-form{display:flex;gap:8px;padding:12px;border-top:1px solid #2a4468}.ask-form input{flex:1;min-width:0;font:inherit;padding:11px 12px;border-radius:12px;border:2px solid #2a4468;background:#0b1626;color:#eef4fb}.ask-form button{border:0;border-radius:12px;font-weight:800;cursor:pointer;padding:0 14px}.ask-send{background:#ffd23f;color:#0b1626}.ask-talk{background:#4cc9f0;color:#0b1626;width:48px;display:flex;align-items:center;justify-content:center}.ask-talk.on{background:#ff6b6b;animation:askp 1.2s infinite}@keyframes askp{50%{opacity:.6}}'+
'.ask-opts{display:flex;justify-content:space-between;align-items:center;padding:0 16px 10px;font-size:13px;color:#a9bdd4}.ask-opts label{display:flex;gap:6px;align-items:center;cursor:pointer}'+
'@media(max-width:720px){.ask-btn .lbl-long{display:none}.ask-panel{right:8px;left:8px;bottom:8px;width:auto;height:calc(100vh - 16px)}}';
var micSvg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>';
var chatSvg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4z"/></svg>';
function build(){
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
  var bar=document.createElement('div'); bar.className='ask-bar';
  bar.innerHTML='<button type="button" class="ask-btn" id="askOpen" aria-haspopup="dialog">'+chatSvg+'<span>Got a quick question? Click here</span></button><button type="button" class="ask-btn ask-mic" id="askVoice" aria-label="Ask by voice">'+micSvg+'</button>';
  var strip=document.createElement('div'); strip.className='ask-strip'; var w=document.createElement('div'); w.className='wrap ask-strip-in';
  w.innerHTML='<span class="ask-hint">Need help fast? Type or talk. Answers come from our directory.</span>'; w.appendChild(bar); strip.appendChild(w);
  var hdr=$('header.top'); if(hdr) hdr.parentNode.insertBefore(strip,hdr); else document.body.prepend(strip);
  var p=document.createElement('div'); p.className='ask-panel'; p.hidden=true; p.setAttribute('role','dialog'); p.setAttribute('aria-label','Ask a quick question');
  p.innerHTML='<div class="ask-head"><b>Ask a quick question</b><button class="ask-x" id="askClose" aria-label="Close">×</button></div>'+
   '<div class="ask-log" id="askLog" aria-live="polite"></div>'+
   '<div class="ask-opts"><label><input type="checkbox" id="askSpeak"> Read answers out loud</label><span>Free · nothing is saved</span></div>'+
   '<form class="ask-form" id="askForm"><input id="askIn" autocomplete="off" placeholder="e.g. help with my power bill in Shelby County" aria-label="Your question"><button type="button" class="ask-talk" id="askTalk" aria-label="Talk instead of typing">'+micSvg+'</button><button class="ask-send" type="submit">Ask</button></form>';
  document.body.appendChild(p);
  $('#askOpen').onclick=function(){open(false)}; $('#askVoice').onclick=function(){open(true)};
  $('#askClose').onclick=function(){p.hidden=true;voiceMode=false;stopTalk();if(window.speechSynthesis)speechSynthesis.cancel();$('#askOpen').focus()};
  $('#askForm').onsubmit=function(e){e.preventDefault();if(!listening)voiceMode=false;var v=$('#askIn').value.trim();if(!v)return;$('#askIn').value='';ask(v)};
  $('#askTalk').onclick=function(){ if(listening){voiceMode=false;stopTalk();} else { voiceMode=true; $('#askSpeak').checked=speakOn=true; talk(); } };
  $('#askSpeak').onchange=function(){speakOn=this.checked;if(!speakOn&&window.speechSynthesis)speechSynthesis.cancel()};
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!p.hidden)$('#askClose').click()});
  document.addEventListener('click',function(e){var c=e.target.closest('.ask-chip');if(c)ask(c.dataset.q)});
}
function open(voice){
  var p=$('.ask-panel'); p.hidden=false;
  if(!$('#askLog').children.length){
    var here=pageContext(); if(here.county) ctx.county=here.county; if(here.need) ctx.need=here.need;
    bot('Hi! Tell me what you need help with and your county or city. For example: <i>"Can\'t pay my light bill in Tuscaloosa"</i> or <i>"food pantry near Dothan."</i>'+chips(['Power bill help','Food pantry','Rent help','Shelter tonight']));
  }
  if(voice){ $('#askSpeak').checked=speakOn=true; voiceMode=true; talk(); } else { voiceMode=false; $('#askIn').focus(); }
}
function pageContext(){ var m=location.pathname.match(/^\/alabama\/([^\/]+)\/(?:([^\/]+)\/)?/), o={};
  if(m){o.county=m[1]; if(m[2]) o.needSlug=m[2];}
  var n=location.pathname.match(/^\/help\/([^\/]+)\//); if(n) o.needSlug=n[1];
  return o; }
function chips(a){return '<div class="ask-chips">'+a.map(function(q){return '<button type="button" class="ask-chip" data-q="'+esc(q)+'">'+esc(q)+'</button>'}).join('')+'</div>'}
function add(html,who){var d=document.createElement('div');d.className='ask-m '+who;d.innerHTML=html;$('#askLog').appendChild(d);$('#askLog').scrollTop=1e9;return d}
function me(t){add(esc(t),'me')}
function bot(html,spoken){add(html,'bot'); if(speakOn) speak(spoken||html.replace(/<[^>]+>/g,' ').replace(/\s+/g,' '))}
function say(t){bot(esc(t),t)}

/* ---------- voice ---------- */
var VOICE=null; function pickVoice(){ if(!window.speechSynthesis) return null; var v=speechSynthesis.getVoices().filter(function(x){return /^en(-|_)US/i.test(x.lang)}); var pref=[/Natural/i,/Google US English/i,/Samantha/i,/Aria|Jenny|Ava|Allison/i,/Zira/i]; for(var i=0;i<pref.length;i++){ var f=v.find(function(x){return pref[i].test(x.name)}); if(f) return f; } return v[0]||null; }
if(window.speechSynthesis){ speechSynthesis.onvoiceschanged=function(){VOICE=pickVoice()}; VOICE=pickVoice(); }
var voiceMode=false;
function speak(t){ if(!window.speechSynthesis) return; speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance(t.replace(/↗/g,'').replace(/\(local\)/g,'').slice(0,700)); u.rate=0.95; u.pitch=1; u.lang='en-US'; if(VOICE||(VOICE=pickVoice())) u.voice=VOICE;
  u.onend=function(){ if(voiceMode&&!$('.ask-panel').hidden&&!listening) setTimeout(talk,350); }; speechSynthesis.speak(u); }
function talk(){
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){ say('Voice isn\'t available in this browser. Chrome, Edge and Safari support it, or you can type your question.'); return; }
  if(window.speechSynthesis) speechSynthesis.cancel();
  rec=new SR(); rec.lang='en-US'; rec.interimResults=true; rec.maxAlternatives=1;
  var final='';
  rec.onresult=function(e){var t='';for(var i=e.resultIndex;i<e.results.length;i++){t+=e.results[i][0].transcript; if(e.results[i].isFinal) final+=e.results[i][0].transcript;} $('#askIn').value=final||t;};
  rec.onerror=function(e){ if(e.error==='no-speech'){ voiceMode=false; } stopTalk(); if(e.error==='not-allowed'||e.error==='service-not-allowed') say('I need permission to use your microphone. Allow it in your browser, or type your question.'); };
  rec.onend=function(){ var v=($('#askIn').value||'').trim(); stopTalk(); if(v){ $('#askIn').value=''; ask(v); } };
  try{ rec.start(); listening=true; $('#askTalk').classList.add('on'); $('#askIn').placeholder='Listening… speak now'; }catch(_){ stopTalk(); }
}
function stopTalk(){ listening=false; var b=$('#askTalk'); if(b) b.classList.remove('on'); var i=$('#askIn'); if(i) i.placeholder='e.g. help with my power bill in Shelby County'; if(rec){ try{rec.stop()}catch(_){ } rec=null; } }

/* ---------- understanding ---------- */
function findCounty(q){
  var t=' '+q.toLowerCase().replace(/[^a-z0-9 .]/g,' ').replace(/\s+/g,' ')+' ';
  var best=null;
  Object.keys(D.counties).forEach(function(slug){ var n=D.counties[slug].toLowerCase(); if(t.indexOf(' '+n+' county')>-1||t.indexOf(' '+n+' co ')>-1) best=slug; });
  if(best) return best;
  var z=q.match(/\b3[56]\d{3}\b/); if(z&&D.zips[z[0]]) return D.zips[z[0]];
  var cities=Object.keys(D.cities).sort(function(a,b){return b.length-a.length});
  var amb=/^(mobile|center|union|lee|clay|pike|dallas|marion|macon|perry|jackson|monroe|clarke|henry|hale|greene|russell)$/;
  for(var i=0;i<cities.length;i++){ var cn=cities[i]; if(amb.test(cn)){ if(new RegExp('\\b(in|near|around|from|at) '+cn+'\\b').test(t)||t.indexOf(' '+cn+' al ')>-1||t.indexOf(' '+cn+' alabama ')>-1) return D.cities[cn]; continue; } if(t.indexOf(' '+cn+' ')>-1) return D.cities[cn]; }
  Object.keys(D.counties).forEach(function(slug){ var n=D.counties[slug].toLowerCase(); if(best||n.length<4) return; if(n==='mobile'){ if(/\b(in|near|around|from) mobile\b/.test(t)) best=slug; return; } if(t.indexOf(' '+n+' ')>-1) best=slug; });
  return best;
}
var EXTRA={power:/\b(electricity|power company|light company|utility bill|utilities|lights? (off|cut|shut))\b/i,food:/\b(starving|feed my|meal|lunch|dinner|breakfast|pantries)\b/i,rent:/\b(apartment|lease|behind on rent|section 8|public housing)\b/i,shelter:/\b(sleep tonight|stay tonight|motel|warming (station|center))\b/i,health:/\b(hospital|prescription|medicine|glasses|eye doctor|mental health|counseling)\b/i,transport:/\b(get to my appointment|medical ride|bus pass|gas money|car repair)\b/i,job:/\b(employment|hiring|career|resume|training)\b/i,furniture:/\b(crib|dresser|appliance|stove|refrigerator|fridge)\b/i,equipment:/\b(handicap|ramps?|grab ?bars?|hand ?rails?|railings?|home modifications?|stair ?lift|hearing aid|cpap|prosthe\w*|amputee)\b/i,benefits:/\b(snap|ebt|disability benefits|food stamps|wic)\b/i,water:/\b(water bill|water company|water (is |got )?(off|cut|shut))\b/i};
function findNeeds(q){ var hits=[]; Object.keys(NEED_WORDS).forEach(function(k){ if(!D.needs[k]) return; var m=q.match(NEED_WORDS[k])||(EXTRA[k]&&q.match(EXTRA[k])); if(m) hits.push([m.index,k]); });
  // "water" inside "water bill" also matches plumbing etc.: earliest mention wins, bills beat repairs on ties
  hits.sort(function(a,b){return a[0]-b[0]}); return hits.map(function(h){return h[1]}); }

function ask(q){
  me(q); ctx.lastQ=q;
  load(function(){
    if(!ctx.county&&pageContext().county) ctx.county=pageContext().county;
    if(/\b(suicid|kill myself|end my life|want to die|hurt myself)\b/i.test(q)){ bot('Please call or text <a class="ph" href="tel:988">988</a> right now, the Suicide and Crisis Lifeline. It\'s free and open 24/7. If you\'re in danger, call <a class="ph" href="tel:911">911</a>.','Please call or text 9 8 8 right now. It is free and open all day and night. If you are in danger, call 9 1 1.'); return; }
    if(/\b(emergency|overdose|not breathing|chest pain|being attacked|fire)\b/i.test(q)){ bot('If this is an emergency, call <a class="ph" href="tel:911">911</a> now.','If this is an emergency, call 9 1 1 now.'); return; }
    if(/\b(abuse|domestic violence|he hits|she hits|afraid of (my|him|her))\b/i.test(q)){ bot('The Alabama domestic violence hotline is free and confidential, 24/7: <a class="ph" href="tel:18006506522">1-800-650-6522</a>. National hotline: <a class="ph" href="tel:18007997233">1-800-799-7233</a>. In danger right now? Call <a class="ph" href="tel:911">911</a>.'); }
    var c=findCounty(q), n=findNeeds(q);
    if(c) ctx.county=c;
    var followUp=/\b(what (do|should) i (bring|need)|documents?|paperwork|proof|more|another|other (one|ones|options)|next|what else|anything else)\b/i.test(q);
    if(n.length) ctx.need=n[0];
    else if(!followUp) ctx.need=null;
    if(!ctx.need&&!n.length&&pageContext().needSlug&&!c&&!followUp&&ctx.firstAsk!==false){ var ps=pageContext().needSlug; Object.keys(D.needs).forEach(function(k){ if(D.needs[k].s===ps) ctx.need=k; }); }
    if(/\b(what (do|should) i (bring|need)|documents?|paperwork|proof)\b/i.test(q)){ bring(); return; }
    if(/\b(advertis|sponsor|promote my business)\b/i.test(q)){ bot('You can advertise to families by county or category. See <a href="/advertise/">Advertise with us</a>.'); return; }
    if(/\b(case ?manager|agency|intake|my clients|pro version|for (my )?organization)\b/i.test(q)){ bot('For agencies and advocates, the Pro version adds client intake, a Help Action Plan and PDF email. See <a href="/for-organizations/">Pro features</a>.'); return; }
    if(/^\s*(hi|hello|hey|thanks|thank you|ok|okay)\b/i.test(q)&&!c&&!n.length){ say(/thank/i.test(q)?'You\'re welcome. Anything else I can look up?':'Hi! What do you need help with, and what county or city are you in?'); return; }
    if(!ctx.county&&!ctx.need){ var hits=searchIdx(q); if(hits) return; bot('I can help with bills, food, rent, shelter, repairs, rides, medical care and more. What do you need, and what county or city are you in?'+chips(['Power bill help','Food pantry','Rent help','Shelter tonight'])); return; }
    ctx.firstAsk=false;
    if(!ctx.county){ bot('What county or city are you in? (For example: Jefferson County, Huntsville, or a ZIP code.)'); return; }
    if(!ctx.need){ countyMenu(); return; }
    answer();
  });
}
function searchIdx(q){ return false; }
function countyMenu(){
  var name=D.counties[ctx.county], cnt=D.counts[ctx.county]||{};
  var opts=Object.keys(D.needs).filter(function(k){return cnt[k]}).slice(0,17);
  bot('Got it, <b>'+esc(name)+' County</b>. What kind of help do you need?'+chips(opts.slice(0,8).map(function(k){return D.needs[k].t}))+'<p style="margin:8px 0 0"><a href="/alabama/'+ctx.county+'/">See everything in '+esc(name)+' County</a></p>',
      'Got it, '+name+' County. What kind of help do you need? For example power bills, food, rent, or shelter.');
}
function answer(){
  var cslug=ctx.county, nid=ctx.need, name=D.counties[cslug], meta=D.needs[nid];
  var T=D.top[cslug]||{}, list=T[nid]||[], total=(D.counts[cslug]||{})[nid]||0, url='/alabama/'+cslug+'/'+meta.s+'/';
  if(nid==='equipment'){ var sub=null; if(/\b(ramps?|hand ?rails?|railings?|grab ?bars?|home modif\w*|widen\w* (the )?doors?|walk-in shower|stair ?lift)\b/i.test(ctx.lastQ||'')&&T._ramp&&T._ramp.length){ list=T._ramp; sub='Ramps, Handrails and Home Accessibility'; } else if(/prosthe|artificial|amput|limb|blade/i.test(ctx.lastQ||'')&&T._prosth&&T._prosth.length) list=T._prosth; else if(/wheelchair|power chair|scooter|walker|cane|crutch|hospital bed|shower chair|lift chair|commode/i.test(ctx.lastQ||'')&&T._wheel&&T._wheel.length) list=T._wheel; }
  if(!list.length){ bot('I don\'t have '+esc(meta.t.toLowerCase())+' listed for '+esc(name)+' County yet. Call <a class="ph" href="tel:211">2-1-1</a>, Alabama\'s free help line, or <a href="/alabama/'+cslug+'/">see everything in '+esc(name)+' County</a>.'); return; }
  var title=(typeof sub!=='undefined'&&sub)||meta.t;
  var html='<b>'+esc(title)+' in '+esc(name)+' County</b>, start with these:<ul>'+list.map(function(r){
    return '<li><b>'+esc(r[0])+'</b>'+(r[3]?' <span style="color:#5bd1a0">(local)</span>':'')+'<br>'+(r[2]?'<a class="ph" href="tel:'+esc(r[2])+'">'+esc(r[1])+'</a>':(r[5]?'<a href="'+esc(r[5])+'" target="_blank" rel="noopener nofollow">No phone listed · Website ↗</a>':esc(r[1])))+(r[4]?'<br><span style="color:#a9bdd4">'+esc(r[4])+'</span>':'')+'</li>'}).join('')+'</ul>'+
    '<a href="'+url+'">See all '+total+' programs, with who qualifies and what to bring</a>'+chips(['What should I bring?','Other help in '+name+' County']);
  var spoken=title+' in '+name+' County. '+list.slice(0,2).map(function(r,i){return (i+1)+'. '+r[0]+'. '+(r[2]?'Phone '+sayPhone(r[2]):'')}).join('. ')+'. There are '+total+' programs in all, and the full list is on screen. What else can I help with?';
  bot(html,spoken);
}
function sayPhone(t){t=String(t).replace(/\D/g,'');if(t.length===11&&t[0]==='1')t=t.slice(1);return t.length===10?[t.slice(0,3),t.slice(3,6),t.slice(6)].map(function(g){return g.split('').join(' ')}).join(', '):t.split('').join(' ');}
function bring(){
  var k=ctx.need==='job'?'job':(['power','water','gas','rent'].indexOf(ctx.need)>-1?'bill':'any');
  var L=D.bring[k];
  bot('Most programs ask for:<ul>'+L.map(function(x){return '<li>'+esc(x)+'</li>'}).join('')+'</ul>Call first to confirm. Each program can ask for something different.','Most programs ask for: '+L.join('. ')+'. Call first to confirm.');
}
/* "Other help in X County" chip */
document.addEventListener('click',function(e){var c=e.target.closest('.ask-chip'); if(c&&/^Other help in /.test(c.dataset.q)){ ctx.need=null; }},true);

if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',build); else build();
})();
