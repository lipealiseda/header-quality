// Rankings explorer: search, position filter, sortable columns, 95% ranges, rank
// ranges and a two player comparison, all over window.DUELS
(function () {
  var rows = window.DUELS || [];
  var groups = {
    def: ["Centre back", "Full back"],
    fwd: ["Striker", "Winger", "Attacking mid"],
    mid: ["Defensive mid", "Central mid", "Wide mid"],
    all: null
  };
  var groupName = { def: "defenders", fwd: "forwards", mid: "midfielders", all: "players" };
  var state = { key: "above", dir: -1, showAll: false };
  var tbody = document.querySelector("#duels tbody");
  var q = document.getElementById("q");
  var pos = document.getElementById("pos");
  var count = document.getElementById("count");
  var more = document.getElementById("more");
  var rrHead = document.getElementById("rr-head");
  var LIMIT = 25, SPAN = 25; // the range bar covers -25 to +25 per 100

  function norm(s) {
    return (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function pct(v) { return Math.max(0, Math.min(100, 50 + (v / SPAN) * 50)); }
  function signed(v) { return (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(1); }

  // normal cdf via the Abramowitz and Stegun erf approximation (error below 1.5e-7)
  function phi(z) {
    var t = 1 / (1 + 0.3275911 * Math.abs(z) / Math.SQRT2);
    var y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) *
      t * Math.exp(-z * z / 2);
    return z >= 0 ? (1 + y) / 2 : (1 - y) / 2;
  }

  function render() {
    var term = norm(q.value.trim());
    var g = pos.value, allowed = groups[g];
    var list = rows.filter(function (r) {
      if (allowed && allowed.indexOf(r.pos) < 0) return false;
      return !term || norm(r.name).indexOf(term) >= 0 || norm(r.club).indexOf(term) >= 0;
    });
    var byAbove = list.slice().sort(function (a, b) { return b.above - a.above; });
    var rank = new Map(byAbove.map(function (r, i) { return [r, i + 1]; }));
    // when searching, show the rank within the whole group, not within the matches
    if (term) {
      var whole = rows.filter(function (r) { return !allowed || allowed.indexOf(r.pos) >= 0; })
        .sort(function (a, b) { return b.above - a.above; });
      rank = new Map(whole.map(function (r, i) { return [r, i + 1]; }));
    }
    list.sort(function (a, b) {
      var x = a[state.key], y = b[state.key];
      if (state.key === "rank") { x = rank.get(a); y = rank.get(b); }
      if (typeof x === "string") return state.dir * x.localeCompare(y);
      return state.dir * (x - y);
    });
    var shown = (state.showAll || term) ? list : list.slice(0, LIMIT);
    rrHead.textContent = "95% rank range among " + groupName[g];
    tbody.innerHTML = shown.map(function (r) {
      var cls = r.above >= 0 ? "pos" : "neg";
      var lo = pct(r.lo), hi = pct(r.hi), mid = pct(r.above);
      var rr = r.rr[g] ? r.rr[g][0] + " to " + r.rr[g][1] : "";
      return "<tr>" +
        '<td class="num">' + rank.get(r) + "</td>" +
        "<td>" + esc(r.name) + "</td>" +
        '<td class="club" title="' + esc(r.club) + '">' + esc(r.club) + "</td>" +
        "<td>" + esc(r.pos) + "</td>" +
        '<td class="num">' + r.h + "</td>" +
        '<td class="num">' + r.n + "</td>" +
        '<td class="num">' + r.won + ' <span class="of">of</span> ' + r.exp.toFixed(1) + "</td>" +
        '<td class="num above ' + cls + '-t">' + signed(r.above) + "</td>" +
        '<td class="bar-cell"><div class="range ' + cls + '" role="img" aria-label="95% range ' +
          signed(r.lo) + " to " + signed(r.hi) + '">' +
          '<span class="axis"></span>' +
          '<span class="span" style="left:' + lo + "%;width:" + Math.max(hi - lo, 1) + '%"></span>' +
          '<span class="dot" style="left:' + mid + '%"></span></div>' +
          '<span class="range-txt">' + signed(r.lo) + " to " + signed(r.hi) + "</span></td>" +
        '<td class="num">' + rr + "</td>" +
        "</tr>";
    }).join("");
    count.textContent = shown.length < list.length
      ? "Showing " + shown.length + " of " + list.length + " " + groupName[g]
      : list.length + " " + (list.length === 1 ? "player" : groupName[g]);
    more.hidden = state.showAll || !!term || list.length <= LIMIT;
    document.querySelectorAll("#duels th").forEach(function (th) {
      var b = th.querySelector("button");
      if (!b) return;
      if (b.dataset.k === state.key) th.setAttribute("aria-sort", state.dir < 0 ? "descending" : "ascending");
      else th.removeAttribute("aria-sort");
    });
  }

  document.querySelectorAll("#duels th button").forEach(function (b) {
    b.addEventListener("click", function () {
      var k = b.dataset.k;
      if (state.key === k) state.dir = -state.dir;
      else { state.key = k; state.dir = (k === "name" || k === "club" || k === "pos" || k === "rank") ? 1 : -1; }
      render();
    });
  });
  q.addEventListener("input", render);
  pos.addEventListener("change", function () { state.showAll = false; render(); });
  more.addEventListener("click", function () { state.showAll = true; render(); });

  // ---------------- compare two players
  var a = document.getElementById("cmp-a"), b = document.getElementById("cmp-b");
  var out = document.getElementById("cmp-out");
  var list = document.getElementById("players");
  var byName = {};
  rows.slice().sort(function (x, y) { return x.name.localeCompare(y.name); }).forEach(function (r) {
    var key = r.name + " (" + r.club + ")";
    byName[norm(key)] = r;
    byName[norm(r.name)] = byName[norm(r.name)] || r;
    var o = document.createElement("option");
    o.value = key;
    list.appendChild(o);
  });
  function find(v) { return byName[norm(v.trim())]; }
  function compare() {
    var A = find(a.value), B = find(b.value);
    if (!a.value.trim() || !b.value.trim()) {
      out.innerHTML = "Pick two players from the list to see how sure we can be that one is better in the air.";
      return;
    }
    if (!A || !B) { out.innerHTML = "Choose names from the suggestions, for example Manolas (AS Roma)."; return; }
    if (A === B) { out.innerHTML = "Those are the same player. Pick two different players."; return; }
    var p = phi((A.mu - B.mu) / Math.sqrt(A.sd * A.sd + B.sd * B.sd));
    var first = p >= 0.5 ? A : B, second = p >= 0.5 ? B : A, pp = Math.max(p, 1 - p);
    var verdict = pp >= 0.95 ? "The data separates them clearly."
      : pp >= 0.8 ? "A lean, but not a clear separation."
      : "The data cannot really separate these two.";
    var shownP = pp > 0.99 ? "Over 99%" : Math.round(pp * 100) + "%";
    out.innerHTML = "<strong>" + shownP + "</strong> chance that " + esc(first.name) +
      " (" + signed(first.above) + ") is truly better than " + esc(second.name) + " (" + signed(second.above) +
      ") at winning aerial duels above expectation. " + verdict;
  }
  a.addEventListener("input", compare);
  b.addEventListener("input", compare);
  render();
  compare();
})();
