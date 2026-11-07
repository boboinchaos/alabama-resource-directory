/* "Got a quick question? Click here" opens the GoHighLevel AI assistant (chat + voice).
   Widget: GoHighLevel "Widget Demo" sub-account, widget id 6aecd79f6e7a665a17c7adda (Riley). */
(function(){
'use strict';
var WIDGET_ID='6aecd79f6e7a665a17c7adda';
var css='.ask-strip{background:#13233a;border-bottom:1px solid #2a4468}.ask-strip-in{display:flex;align-items:center;justify-content:center;gap:14px;min-height:54px;flex-wrap:wrap;padding-top:6px;padding-bottom:6px}'+
 '.ask-hint{color:#a9bdd4;font-size:15px}@media(max-width:720px){.ask-hint{display:none}}'+
 '.ask-bar{display:flex;gap:8px}.ask-btn{display:inline-flex;align-items:center;gap:8px;border:0;border-radius:999px;background:#4cc9f0;color:#0b1626;font:800 16px var(--display,system-ui);padding:9px 16px;cursor:pointer}'+
 '.ask-btn svg{width:20px;height:20px}.ask-mic{background:#ffd23f;padding:9px 11px}';
var micSvg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>';
var chatSvg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4z"/></svg>';
function build(){
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);
  var strip=document.createElement('div'); strip.className='ask-strip';
  strip.innerHTML='<div class="wrap ask-strip-in"><span class="ask-hint">Need help fast? Chat or talk with our assistant.</span><div class="ask-bar">'+
    '<button type="button" class="ask-btn" id="askOpen">'+chatSvg+'<span>Got a quick question? Click here</span></button>'+
    '<button type="button" class="ask-btn ask-mic" id="askVoice" aria-label="Talk to the assistant">'+micSvg+'</button></div></div>';
  var hdr=document.querySelector('header.top'); if(hdr) hdr.parentNode.insertBefore(strip,hdr); else document.body.prepend(strip);
  var s=document.createElement('script'); s.src='https://widgets.leadconnectorhq.com/loader.js';
  s.setAttribute('data-resources-url','https://widgets.leadconnectorhq.com/chat-widget/loader.js'); s.setAttribute('data-widget-id',WIDGET_ID);
  document.body.appendChild(s);
  // hide the widget's own corner bubble; our button opens it
  var tries=0, t=setInterval(function(){
    var cw=document.querySelector('chat-widget'), sr=cw&&cw.shadowRoot;
    if(sr&&!sr.getElementById('hide-bubble')){ var h=document.createElement('style'); h.id='hide-bubble';
      h.textContent='.lc_text-widget--bubble,.lc_text-widget_prompt,[class*="widget_prompt"]{display:none!important}'; sr.appendChild(h); }
    if((sr&&sr.getElementById('hide-bubble'))||++tries>80) clearInterval(t);
  },500);
  function openW(){
    var lc=window.leadConnector&&window.leadConnector.chatWidget;
    if(lc&&lc.openWidget){ lc.openWidget(); return; }
    var cw=document.querySelector('chat-widget'), b=cw&&cw.shadowRoot&&cw.shadowRoot.querySelector('.lc_text-widget--bubble');
    if(b) b.click(); else setTimeout(openW,400);
  }
  document.getElementById('askOpen').onclick=openW; document.getElementById('askVoice').onclick=openW;
}
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',build); else build();
})();
