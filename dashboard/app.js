(function () {
  var data = window.TENDER_DATA;
  if (!data) return;

  var COLORS = { bid: "#1d9e75", catatan: "#e8a13a", nobid: "#d64545" };

  function recClass(rec) {
    if (rec === "BID") return "bid";
    if (rec === "NO-BID") return "nobid";
    return "catatan";
  }

  function rp(value) {
    if (!value) return "-";
    return "Rp " + String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  document.getElementById("meta").textContent =
    "Tanggal analisis: " + data.tanggal_analisis + " · Profil perusahaan: " + data.profil;

  var cardsEl = document.getElementById("cards");
  var chartEl = document.getElementById("score-chart");
  var tabsEl = document.getElementById("tabs");
  var detailEl = document.getElementById("detail");
  var active = 0;

  data.tender.forEach(function (t, idx) {
    var cls = recClass(t.rekomendasi);
    var card = document.createElement("article");
    card.className = "card" + (idx === 0 ? " active" : "");
    card.innerHTML =
      "<h3>" + t.nama_paket + "</h3>" +
      '<p class="instansi">' + t.instansi + "</p>" +
      '<span class="badge ' + cls + '">' + t.rekomendasi + "</span> " +
      '<span class="badge risk">Risiko ' + t.risiko.level + " " + t.risiko.skor + "/100</span>" +
      '<div class="gauge"><div style="width:' + t.skor + "%;background:" + COLORS[cls] + '"></div></div>' +
      '<div class="score-row"><span>HPS ' + rp(t.nilai_hps_rp) + " · " + t.jangka_waktu_hari + ' hari</span>' +
      '<span class="score">' + t.skor + "</span></div>";
    card.addEventListener("click", function () { select(idx); });
    cardsEl.appendChild(card);

    var row = document.createElement("div");
    row.className = "row";
    row.innerHTML =
      "<span>" + t.nama_paket + "</span>" +
      '<div class="track"><div class="fill" style="width:' + t.skor + "%;background:" + COLORS[cls] + '"></div>' +
      '<div class="threshold" style="left:60%"></div><div class="threshold" style="left:85%"></div></div>' +
      "<span>" + t.skor + "/100</span>";
    chartEl.appendChild(row);

    var tab = document.createElement("button");
    tab.textContent = t.nama_paket;
    if (idx === 0) tab.className = "active";
    tab.addEventListener("click", function () { select(idx); });
    tabsEl.appendChild(tab);
  });

  function select(idx) {
    active = idx;
    Array.prototype.forEach.call(cardsEl.children, function (c, i) {
      c.classList.toggle("active", i === idx);
    });
    Array.prototype.forEach.call(tabsEl.children, function (b, i) {
      b.classList.toggle("active", i === idx);
    });
    renderDetail(data.tender[idx]);
  }

  function renderDetail(t) {
    var rows = t.checklist.map(function (i) {
      return "<tr><td>" + i.item + '</td><td class="status ' + i.status + '">' + i.status +
        "</td><td>" + i.bobot + "</td><td>" + i.skor + "</td><td>" + i.detail + "</td></tr>";
    }).join("");
    var steps = t.jadwal.map(function (j) {
      return '<div class="step"><b>' + j.tahap + "</b>" + j.tanggal + "</div>";
    }).join("");
    var questions = t.pertanyaan.map(function (q) { return "<li>" + q + "</li>"; }).join("");
    detailEl.innerHTML =
      "<h3 style='margin:0 0 4px;color:var(--navy)'>" + t.nama_paket + "</h3>" +
      "<p style='margin:0 0 6px;color:var(--muted);font-size:13px'>Skor kesiapan " + t.skor +
      "/100 · Rekomendasi " + t.rekomendasi + " · Risiko " + t.risiko.level + " (" + t.risiko.skor + "/100)</p>" +
      '<div class="timeline">' + steps + "</div>" +
      "<table><thead><tr><th>Item</th><th>Status</th><th>Bobot</th><th>Skor</th><th>Keterangan</th></tr></thead><tbody>" +
      rows + "</tbody></table>" +
      "<h4 style='margin:16px 0 4px;color:var(--navy)'>Draf pertanyaan aanwijzing (" + t.pertanyaan.length + ")</h4>" +
      '<ol class="questions">' + questions + "</ol>";
  }

  renderDetail(data.tender[0]);
})();
