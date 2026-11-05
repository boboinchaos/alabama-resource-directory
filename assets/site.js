document.addEventListener('submit',function(ev){var f=ev.target;if(!f.classList.contains('finder'))return;ev.preventDefault();
 var c=f.querySelector('[name=c]').value,n=f.querySelector('[name=n]').value;
 if(!c&&!n)return; location.href=c?('/alabama/'+c+'/'+(n?n+'/':'')):('/help/'+n+'/');});
(function(){var box=document.getElementById('q');if(!box)return;var out=document.getElementById('results'),idx=null;
 function load(cb){if(idx)return cb();fetch('/assets/search-index.json').then(function(r){return r.json()}).then(function(j){idx=j;cb()})}
 function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
 function run(){var q=box.value.trim().toLowerCase();if(q.length<2){out.innerHTML='';return}
  load(function(){var w=q.split(/\s+/),hits=[];for(var i=0;i<idx.length&&hits.length<60;i++){var t=idx[i].t;if(w.every(function(x){return t.indexOf(x)>-1}))hits.push(idx[i])}
   out.innerHTML=hits.length?hits.map(function(h){return '<div class="res"><h3><a href="'+h.u+'">'+esc(h.n)+'</a></h3><div class="muted">'+esc(h.s)+(h.p?' · '+esc(h.p):'')+'</div></div>'}).join(''):'<p class="muted">No matches. Try a county name or a word like "rent".</p>'})}
 box.addEventListener('input',run);var p=new URLSearchParams(location.search).get('q');if(p){box.value=p;run()}})();