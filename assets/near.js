/* Closest-first search: geocodes the visitor's address in the browser, then sorts
   programs by distance from it. Nothing is saved. Data: /assets/near.json */
(function () {
  var form = document.getElementById('nearform'); if (!form) return;
  var out = document.getElementById('nearout'), D = null;
  var NEED = window.NEAR_NEEDS || {};
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function load(cb) { if (D) return cb(); fetch('/assets/near.json').then(function (r) { return r.json(); }).then(function (j) { D = j; cb(); }).catch(function () { msg('Sorry, the directory did not load. Please try again.'); }); }
  function msg(h) { out.innerHTML = '<p class="muted">' + h + '</p>'; }
  function mi(a, b, c, d) { var R = 3958.8, r = Math.PI / 180, x = (c - a) * r, y = (d - b) * r; var h = Math.sin(x / 2) * Math.sin(x / 2) + Math.cos(a * r) * Math.cos(c * r) * Math.sin(y / 2) * Math.sin(y / 2); return 2 * R * Math.asin(Math.sqrt(h)); }
  function zipOf(s) { var m = String(s).match(/\b(3[56]\d{3})\b/); return m ? m[1] : null; }
  function nearestZip(lat, lon) { var best = null, bd = 1e9; for (var z in D.z) { var p = D.z[z], d = mi(lat, lon, p[0], p[1]); if (d < bd) { bd = d; best = z; } } return best; }
  function countyFromName(n) { if (!n) return null; n = n.replace(/ County$/i, '').toLowerCase(); for (var i = 0; i < D.c.length; i++) if (D.c[i][1].toLowerCase() === n) return i; return null; }

  function geocode(q, cb) {
    var zip = zipOf(q), justZip = /^\s*3[56]\d{3}\s*$/.test(q);
    function byZip() { if (zip && D.z[zip]) { var p = D.z[zip]; cb({ lat: p[0], lon: p[1], county: p[2], label: 'ZIP ' + zip, rough: true }); } else cb(null); }
    if (justZip) return byZip();
    var qq = /\b(al|alabama)\b/i.test(q) ? q : q + ', Alabama';
    fetch('https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=1&countrycodes=us&q=' + encodeURIComponent(qq), { headers: { 'Accept-Language': 'en' } })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j.length || (j[0].address && j[0].address.state && j[0].address.state !== 'Alabama')) return byZip();
        var a = j[0].address || {}, lat = +j[0].lat, lon = +j[0].lon;
        var c = countyFromName(a.county); if (c == null) { var nz = nearestZip(lat, lon); c = nz ? D.z[nz][2] : null; }
        var label = [a.house_number && a.road ? a.house_number + ' ' + a.road : a.road, a.city || a.town || a.village || a.hamlet || a.suburb].filter(Boolean).join(', ');
        cb({ lat: lat, lon: lon, county: c, label: label || q, rough: !a.road });
      })
      .catch(byZip);
  }

  function run(q, need, here) {
    msg('Finding the closest help…');
    load(function () {
      var go = function (loc) {
        if (!loc) return msg('We couldn\'t find that address. Try adding the city, or enter a 5-digit ZIP code.');
        render(loc, need);
      };
      if (here) {
        navigator.geolocation.getCurrentPosition(function (p) {
          var lat = p.coords.latitude, lon = p.coords.longitude, nz = nearestZip(lat, lon);
          go({ lat: lat, lon: lon, county: nz ? D.z[nz][2] : null, label: 'your current location' });
        }, function () { msg('Location is turned off. Type your address instead.'); }, { timeout: 10000 });
      } else geocode(q, go);
    });
  }

  function card(r, d, warn) {
    var nk = r[5].split(',').filter(function (k) { return NEED[k]; });
    return '<article class="res near"><div class="dist">' + (d < 0.1 ? '<0.1' : d.toFixed(1)) + '<small>mi</small></div><div>' +
      '<h3><a href="' + esc(r[8]) + '">' + esc(r[0]) + '</a></h3>' +
      '<div>' + nk.slice(0, 4).map(function (k) { return '<span class="badge">' + esc(NEED[k][1]) + '</span>'; }).join('') + (r[7] === 'z' ? '<span class="badge" title="Distance measured from the program\'s ZIP code">approx.</span>' : '') + '</div>' +
      (r[1] ? '<a class="phone" href="tel:' + esc(r[1].replace(/\D/g, '').slice(0, 10)) + '">' + esc(r[1]) + '</a>' : '') +
      '<p style="margin:6px 0 0"><a href="https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(r[2]) + '" target="_blank" rel="nofollow noopener">' + esc(r[2]) + '</a></p>' +
      (warn ? '<p class="muted" style="font-size:15px;margin:6px 0 0">Based in a neighboring county. Call to ask if they serve your address.</p>' : '') +
      '<p style="margin:6px 0 0"><a href="' + esc(r[8]) + '">Who qualifies and what to bring →</a></p></div></article>';
  }

  function render(loc, need) {
    var rows = [];
    for (var i = 0; i < D.r.length; i++) {
      var r = D.r[i];
      if (need && (',' + r[5] + ',').indexOf(',' + need + ',') < 0) continue;
      var d = mi(loc.lat, loc.lon, r[3], r[4]);
      var serves = loc.county == null || r[6].indexOf(loc.county) > -1;
      if (d > 60) continue;
      rows.push([d, r, serves]);
    }
    rows.sort(function (a, b) { return a[0] - b[0]; });
    var mine = rows.filter(function (x) { return x[2]; }).slice(0, 40);
    var other = rows.filter(function (x) { return !x[2] && x[0] < 20; }).slice(0, 8);
    var cn = loc.county != null ? D.c[loc.county] : null;
    var h = '<p class="found">Closest help to <b>' + esc(loc.label) + '</b>' + (cn ? ' in ' + esc(cn[1]) + ' County' : '') +
      (need ? ' for <b>' + esc(NEED[need][1]) + '</b>' : '') + ', nearest first.' + (loc.rough ? ' (Measured from the center of your town or ZIP. Add your street address for closer results.)' : '') + '</p>';
    if (!mine.length && !other.length) h += '<p>No programs with an office within 60 miles matched. Countywide and statewide programs below still cover you.</p>';
    h += mine.map(function (x) { return card(x[1], x[0], false); }).join('');
    if (other.length) h += '<h2>Just across the county line</h2>' + other.map(function (x) { return card(x[1], x[0], true); }).join('');
    if (cn) {
      h += '<div class="box" style="margin-top:20px"><h3>Programs that cover all of ' + esc(cn[1]) + ' County</h3><p style="margin:0 0 10px">Many programs have no walk-in office near you but still serve your address, like LIHEAP, Medicaid and statewide hotlines.</p>' +
        (need ? '<a class="btn btn-sm" href="/alabama/' + cn[0] + '/' + NEED[need][0] + '/">See all ' + esc(NEED[need][1].toLowerCase()) + ' in ' + esc(cn[1]) + ' County</a>' :
          '<a class="btn btn-sm" href="/alabama/' + cn[0] + '/">See everything in ' + esc(cn[1]) + ' County</a>') + '</div>';
    }
    out.innerHTML = h;
    out.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault(); var q = form.a.value.trim(), n = form.n.value;
    if (!q) return msg('Type an address, city or ZIP code.');
    history.replaceState(null, '', '?a=' + encodeURIComponent(q) + (n ? '&n=' + n : ''));
    run(q, n, false);
  });
  var me = document.getElementById('nearme');
  if (me) me.addEventListener('click', function () { if (!navigator.geolocation) return msg('Your browser can\'t share location. Type your address instead.'); run('', form.n.value, true); });
  var p = new URLSearchParams(location.search);
  if (p.get('n')) form.n.value = p.get('n');
  if (p.get('a')) { form.a.value = p.get('a'); run(p.get('a'), form.n.value, false); }
  else if (p.get('me') && navigator.geolocation) run('', form.n.value, true);
})();
