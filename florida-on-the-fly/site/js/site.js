/* Florida's On The Fly Charters — site script */

/* ============================================================
   CONFIG: paste the client's real links here.
   BOOKING_URL   – the online booking page (FishySites / Vally / FareHarbor etc.).
                   While empty, "Book" buttons send people to the contact form
                   with their trip and date filled in, plus a call option.
   FORM_ENDPOINT – where the contact and group-quote forms POST (Formspree,
                   Basin, Netlify Forms, etc.). While empty, forms open the
                   visitor's email app addressed to Capt. Tanner instead.
   ============================================================ */
var SITE_CONFIG = {
  BOOKING_URL: "",
  FORM_ENDPOINT: "",
  EMAIL: "captaintannermartin@gmail.com",
  PHONE: "(352) 577-4084",
  TEL: "tel:+13525774084"
};

(function () {
  "use strict";
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };

  /* ---------- Trips (used by the booking widget) ---------- */
  var TRIPS = [
    { key: "inshore", name: "Inshore Charter", from: "From $600", url: "/charters/inshore-fishing/",
      lengths: ["4 hours • $600", "7 hours • $700"], times: ["7:00 AM"], note: "Groups of 3 or 4 add $100." },
    { key: "fly", name: "Backcountry Fly & Light Tackle", from: "From $600", url: "/charters/fly-fishing/",
      lengths: ["4 hours • $600", "7 hours • $700"], times: ["7:00 AM"], note: "1 or 2 anglers." },
    { key: "tarpon", name: "Homosassa Tarpon", from: "$900", url: "/charters/homosassa-tarpon/",
      lengths: ["8 hours • $900"], times: ["6:00 AM"], note: "Up to 2 anglers. Leaves MacRae's of Homosassa." },
    { key: "scalloping", name: "Scalloping", from: "From $600", url: "/charters/scalloping/",
      lengths: ["Up to 2 • $600", "Up to 4 • $700", "Up to 6 • $800"], times: ["8:00 AM"], note: "July 1 to September 24." },
    { key: "duck", name: "Duck Hunt", from: "$500", url: "/charters/duck-hunting/",
      lengths: ["2 hunters • $500", "3 hunters • $750"], times: ["Morning", "Evening"], note: "Mid-November to January." },
    { key: "mud", name: "Mud Boat Trip", from: "From $500", url: "/charters/mud-boat-fishing/",
      lengths: ["1 or 2 • $500", "3 anglers • $600"], times: ["Tide dependent"], note: "November to February, 4 to 6 hours." }
  ];
  var tripByKey = {};
  TRIPS.forEach(function (t) { tripByKey[t.key] = t; });

  var body = document.body;
  function lock(on) { body.classList.toggle("lock", !!on); }

  /* ---------- Mega menu ---------- */
  var megaBtn = $("#mega-btn"), mega = $("#mega"), scrim = $("#mega-scrim");
  function setMega(open) {
    if (!megaBtn) return;
    megaBtn.setAttribute("aria-expanded", open ? "true" : "false");
    mega.classList.toggle("open", open);
    scrim.classList.toggle("open", open);
  }
  if (megaBtn) {
    var hoverOpenedAt = 0;
    megaBtn.addEventListener("click", function () {
      if (Date.now() - hoverOpenedAt < 600) return; // hover already opened it; don't let the click close it
      setMega(megaBtn.getAttribute("aria-expanded") !== "true");
    });
    scrim.addEventListener("click", function () { setMega(false); });
    var hoverTimer;
    var hdr = $(".site-header");
    megaBtn.addEventListener("mouseenter", function () { if (window.matchMedia("(hover:hover)").matches) { clearTimeout(hoverTimer); if (megaBtn.getAttribute("aria-expanded") !== "true") hoverOpenedAt = Date.now(); setMega(true); } });
    hdr.addEventListener("mouseleave", function () { hoverTimer = setTimeout(function () { setMega(false); }, 200); });
    hdr.addEventListener("mouseenter", function () { clearTimeout(hoverTimer); });
  }

  /* ---------- Mobile menu ---------- */
  var mm = $("#mobile-menu"), toggle = $(".menu-toggle");
  function setMenu(open) {
    if (!mm) return;
    mm.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    lock(open);
  }
  if (toggle) toggle.addEventListener("click", function () { setMenu(true); });
  $$(".menu-close").forEach(function (b) { b.addEventListener("click", function () { setMenu(false); }); });

  /* ---------- Sheets (booking popup, trip picker) ---------- */
  var lastFocus;
  function openSheet(name, trip) {
    var sh = $("#sheet-" + name);
    if (!sh) return;
    setMenu(false); setMega(false);
    lastFocus = document.activeElement;
    if (name === "booking" && trip) {
      var w = $("[data-widget]", sh); if (w && w._select) w._select(trip);
    }
    sh.classList.add("open"); lock(true);
    var c = $(".close", sh); if (c) c.focus();
  }
  function closeSheets() {
    $$(".sheet.open").forEach(function (s) { s.classList.remove("open"); });
    if (!(mm && mm.classList.contains("open"))) lock(false);
    if (lastFocus) lastFocus.focus();
  }
  document.addEventListener("click", function (e) {
    var o = e.target.closest("[data-open]");
    if (o) { e.preventDefault(); openSheet(o.getAttribute("data-open"), o.getAttribute("data-trip")); return; }
    if (e.target.closest("[data-close]")) closeSheets();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    closeSheets(); setMega(false); setMenu(false); closeLightbox();
  });

  /* ---------- Booking widget ---------- */
  var MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  var DAYS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function iso(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }

  function Widget(el) {
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var view = new Date(today.getFullYear(), today.getMonth(), 1);
    var state = { trip: el.getAttribute("data-trip") || "inshore", date: null, length: 0, time: 0 };
    if (!tripByKey[state.trip]) state.trip = "inshore";
    var only = el.getAttribute("data-only") === "true";

    el.innerHTML =
      '<h3>Trip Availability</h3>' +
      '<div class="rate"><span class="stars" aria-hidden="true">★★★★★</span><span>5.0 on Tripadvisor</span></div>' +
      '<div class="cal-head"><button type="button" class="prev" aria-label="Previous month">‹</button><span aria-live="polite"></span><button type="button" class="next" aria-label="Next month">›</button></div>' +
      '<div class="cal" role="grid"></div>' +
      '<p class="w-date">Pick a date to see your trip</p>' +
      '<div class="w-trips"></div>' +
      '<a class="btn btn-blue w-book" href="#">Book this trip</a>' +
      '<a class="btn btn-line" href="' + SITE_CONFIG.TEL + '">Call ' + SITE_CONFIG.PHONE + '</a>' +
      '<p class="w-note"></p>';

    var cal = $(".cal", el), label = $(".cal-head span", el), prev = $(".prev", el), next = $(".next", el);
    var wDate = $(".w-date", el), wTrips = $(".w-trips", el), book = $(".w-book", el), note = $(".w-note", el);

    function drawCal() {
      label.textContent = MONTHS[view.getMonth()] + " " + view.getFullYear();
      prev.disabled = view <= new Date(today.getFullYear(), today.getMonth(), 1);
      var html = "";
      ["S","M","T","W","T","F","S"].forEach(function (d) { html += '<span class="dow" aria-hidden="true">' + d + "</span>"; });
      var first = view.getDay(), days = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
      for (var i = 0; i < first; i++) html += "<span></span>";
      for (var d = 1; d <= days; d++) {
        var dt = new Date(view.getFullYear(), view.getMonth(), d);
        var past = dt < today;
        var sel = state.date && iso(state.date) === iso(dt);
        html += '<button type="button" data-d="' + d + '"' + (past ? " disabled" : "") + ' aria-pressed="' + (sel ? "true" : "false") + '" aria-label="' + DAYS[dt.getDay()] + " " + MONTHS[dt.getMonth()] + " " + d + '">' + d + "</button>";
      }
      cal.innerHTML = html;
    }
    function drawTrips() {
      var list = only ? [tripByKey[state.trip]] : TRIPS;
      wTrips.innerHTML = list.map(function (t) {
        var open = t.key === state.trip;
        var opts = "";
        if (open) {
          opts = '<div class="w-opts"><div class="pills" role="group" aria-label="Trip length">' +
            t.lengths.map(function (l, i) { return '<button type="button" class="pill len" data-i="' + i + '" aria-pressed="' + (i === state.length) + '">' + l + "</button>"; }).join("") +
            '</div><div class="pills" role="group" aria-label="Start time">' +
            t.times.map(function (l, i) { return '<button type="button" class="pill time" data-i="' + i + '" aria-pressed="' + (i === state.time) + '">' + l + "</button>"; }).join("") +
            '<a class="pill note" href="' + SITE_CONFIG.TEL + '">Call for other times</a></div></div>';
        }
        return '<div class="w-trip' + (open ? " open" : "") + '"><button type="button" data-k="' + t.key + '" aria-expanded="' + open + '"><span>' + t.name + "</span><span>" + t.from + "</span></button>" + opts + "</div>";
      }).join("");
      updateBook();
    }
    function updateBook() {
      var t = tripByKey[state.trip];
      var params = "trip=" + encodeURIComponent(t.name) + "&length=" + encodeURIComponent(t.lengths[state.length] || "") + (state.date ? "&date=" + iso(state.date) : "");
      if (SITE_CONFIG.BOOKING_URL) {
        book.href = SITE_CONFIG.BOOKING_URL; book.target = "_blank"; book.rel = "noopener";
        book.textContent = "Book this trip";
        note.textContent = "$100 deposit holds your date. Balance due after the trip.";
      } else {
        book.href = "/contact/?" + params; book.removeAttribute("target");
        book.textContent = state.date ? "Request this date" : "Request a date";
        note.textContent = "$100 deposit holds your date. Capt. Tanner confirms every request by phone or text.";
      }
    }
    cal.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-d]"); if (!b || b.disabled) return;
      state.date = new Date(view.getFullYear(), view.getMonth(), +b.getAttribute("data-d"));
      var d = state.date;
      wDate.textContent = "Your date: " + DAYS[d.getDay()] + ", " + MONTHS[d.getMonth()].slice(0, 3) + " " + d.getDate();
      drawCal(); updateBook();
    });
    prev.addEventListener("click", function () { view.setMonth(view.getMonth() - 1); drawCal(); });
    next.addEventListener("click", function () { view.setMonth(view.getMonth() + 1); drawCal(); });
    wTrips.addEventListener("click", function (e) {
      var k = e.target.closest("button[data-k]");
      if (k) { select(k.getAttribute("data-k")); return; }
      var p = e.target.closest("button.pill");
      if (p) { state[p.classList.contains("len") ? "length" : "time"] = +p.getAttribute("data-i"); drawTrips(); }
    });
    function select(key) {
      if (!tripByKey[key] || key === state.trip) return;
      state.trip = key; state.length = 0; state.time = 0; drawTrips();
    }
    el._select = select;
    drawCal(); drawTrips();
  }
  $$("[data-widget]").forEach(Widget);

  /* Charters page: the sticky widget follows the trip section on screen */
  var follow = $("[data-widget][data-follow]");
  if (follow && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting && follow._select) follow._select(en.target.getAttribute("data-trip-section")); });
    }, { rootMargin: "-40% 0px -55% 0px" });
    $$("[data-trip-section]").forEach(function (s) { io.observe(s); });
  }

  /* ---------- YouTube: load the player only when clicked ---------- */
  $$(".video[data-yt]").forEach(function (v) {
    v.addEventListener("click", function (e) {
      e.preventDefault();
      var id = v.getAttribute("data-yt");
      v.insertAdjacentHTML("beforeend", '<iframe src="https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0" title="' + (v.getAttribute("aria-label") || "Video") + '" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>');
    }, { once: true });
  });

  /* ---------- Lightbox for galleries ---------- */
  var lb = $("#lightbox"), lbImg = null, group = [], idx = 0;
  if (lb) { lbImg = document.createElement("img"); lbImg.alt = ""; lb.insertBefore(lbImg, $(".lb-next", lb)); }
  function showLb() { if (!lbImg) return; lbImg.src = group[idx].getAttribute("href"); lbImg.alt = ($("img", group[idx]) || {}).alt || ""; }
  function closeLightbox() { if (lb && lb.classList.contains("open")) { lb.classList.remove("open"); lock(false); } }
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a[data-gallery]");
    if (!a || !lb) return;
    e.preventDefault();
    group = $$('a[data-gallery="' + a.getAttribute("data-gallery") + '"]');
    idx = group.indexOf(a); showLb(); lb.classList.add("open"); lock(true);
  });
  if (lb) {
    $(".lb-close", lb).addEventListener("click", closeLightbox);
    $(".lb-prev", lb).addEventListener("click", function () { idx = (idx - 1 + group.length) % group.length; showLb(); });
    $(".lb-next", lb).addEventListener("click", function () { idx = (idx + 1) % group.length; showLb(); });
    lb.addEventListener("click", function (e) { if (e.target === lb) closeLightbox(); });
  }

  /* ---------- FAQ accordions (native <details>), nothing needed ---------- */

  /* ---------- Forms ---------- */
  $$("form[data-form]").forEach(function (form) {
    // Prefill from the booking widget (?trip=&date=&length=)
    var q = new URLSearchParams(location.search);
    ["trip", "date", "length"].forEach(function (k) {
      var f = form.querySelector('[name="' + (k === "length" ? "date" : k) + '"]'); if (k === "length") return; if (f && q.get(k)) {
        if (f.tagName === "SELECT") { $$("option", f).forEach(function (o) { if (q.get(k).toLowerCase().indexOf(o.value.toLowerCase().split(" ")[0]) === 0 || o.value === q.get(k)) f.value = o.value; }); }
        else f.value = q.get(k) + (k === "date" && q.get("length") ? " (" + q.get("length") + ")" : "");
      }
    });
    var status = $(".form-status", form);
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var data = new FormData(form);
      if (SITE_CONFIG.FORM_ENDPOINT) {
        var btn = $("button[type=submit]", form); if (btn) btn.disabled = true;
        fetch(SITE_CONFIG.FORM_ENDPOINT, { method: "POST", body: data, headers: { Accept: "application/json" } })
          .then(function (r) { if (!r.ok) throw new Error(); location.href = "/thank-you/"; })
          .catch(function () { if (btn) btn.disabled = false; if (status) status.textContent = "Sorry, that didn't send. Please call or text " + SITE_CONFIG.PHONE + "."; });
      } else {
        var lines = [];
        data.forEach(function (v, k) { if (v && k !== "_gotcha") lines.push(k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, " ") + ": " + v); });
        var subject = form.getAttribute("data-subject") || "Trip request from the website";
        location.href = "mailto:" + SITE_CONFIG.EMAIL + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(lines.join("\n"));
        if (status) status.textContent = "Your email app should open with your message ready to send. Prefer to talk? Call or text " + SITE_CONFIG.PHONE + ".";
      }
    });
  });

  /* Year in footer stays current */
  $$("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
