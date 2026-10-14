// Rankings explorer: search, position filter and sortable columns over window.DUELS
(function () {
  var rows = window.DUELS || [];
  var groups = {
    def: ["Centre back", "Full back"],
    fwd: ["Striker", "Winger", "Attacking mid"],
    mid: ["Defensive mid", "Central mid", "Wide mid"],
    all: null
  };
  var state = { key: "above", dir: -1, showAll: false };
  var tbody = document.querySelector("#duels tbody");
  var q = document.getElementById("q");
  var pos = document.getElementById("pos");
  var count = document.getElementById("count");
  var more = document.getElementById("more");
  var LIMIT = 25, SPAN = 22; // the range bar covers -22 to +22 per 100

  function norm(s) {
    return (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function pct(v) { return Math.max(0, Math.min(100, 50 + (v / SPAN) * 50)); }
  function signed(v) { return (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(1); }

  function render() {
    var term = norm(q.value.trim());
    var allowed = groups[pos.value];
    var list = rows.filter(function (r) {
      if (allowed && allowed.indexOf(r.pos) < 0) return false;
      return !term || norm(r.name).indexOf(term) >= 0 || norm(r.club).indexOf(term) >= 0;
    });
    // rank by the main metric within the current filter, before any re-sorting
    var byAbove = list.slice().sort(function (a, b) { return b.above - a.above; });
    var rank = new Map(byAbove.map(function (r, i) { return [r, i + 1]; }));
    list.sort(function (a, b) {
      var x = a[state.key], y = b[state.key];
      if (typeof x === "string") return state.dir * x.localeCompare(y);
      return state.dir * (x - y);
    });
    var shown = (state.showAll || term) ? list : list.slice(0, LIMIT);
    tbody.innerHTML = shown.map(function (r) {
      var cls = r.above >= 0 ? "pos" : "neg";
      var lo = pct(r.lo), hi = pct(r.hi), mid = pct(r.above);
      return "<tr>" +
        '<td class="num">' + rank.get(r) + "</td>" +
        "<td>" + esc(r.name) + "</td>" +
        '<td class="club" title="' + esc(r.club) + '">' + esc(r.club) + "</td>" +
        "<td>" + esc(r.pos) + "</td>" +
        '<td class="num">' + r.h + "</td>" +
        '<td class="num">' + r.n + "</td>" +
        '<td class="num">' + r.won + "</td>" +
        '<td class="num">' + r.exp.toFixed(1) + "</td>" +
        '<td class="num above ' + cls + '-t">' + signed(r.above) + "</td>" +
        '<td class="bar-cell"><div class="range ' + cls + '" role="img" aria-label="likely range ' +
          signed(r.lo) + " to " + signed(r.hi) + '">' +
          '<span class="axis"></span>' +
          '<span class="span" style="left:' + lo + "%;width:" + Math.max(hi - lo, 1) + '%"></span>' +
          '<span class="dot" style="left:' + mid + '%"></span></div></td>' +
        "</tr>";
    }).join("");
    count.textContent = shown.length < list.length
      ? "Showing " + shown.length + " of " + list.length + " players"
      : list.length + (list.length === 1 ? " player" : " players");
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
      else { state.key = k; state.dir = (k === "name" || k === "club" || k === "pos") ? 1 : -1; }
      render();
    });
  });
  q.addEventListener("input", render);
  pos.addEventListener("change", function () { state.showAll = false; render(); });
  more.addEventListener("click", function () { state.showAll = true; render(); });
  render();
})();
