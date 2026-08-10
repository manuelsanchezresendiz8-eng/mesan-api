// script.js -- MESAN Omega Landing v2.0 (datos reales)
document.addEventListener("DOMContentLoaded", function() {

  // FETCH REAL DATA FROM API
  async function loadRealKPIs() {
    try {
      var r = await fetch(window.location.origin + "/commercial/mission-control");
      var d = await r.json();
      var leads = d.leads || {};
      var guardian = d.guardian || {};
      var pipeline = d.pipeline || {};
      var system = d.system || {};

      setKPI("kpi-leads", leads.total || 0);
      setKPI("kpi-nuevos", leads.nuevos || 0);
      setKPI("kpi-mrr", "$" + (pipeline.mrr || 0).toLocaleString());
      setKPI("kpi-health", guardian.health || 0);
      setKPI("kpi-alerts", guardian.alerts || 0);
      setKPI("kpi-conversion", (pipeline.conversion || 0) + "%");
      setKPI("kpi-uptime", Math.round(system.uptime || 0));

      var gauge = document.querySelector(".gauge-fill");
      if (gauge) gauge.style.width = (guardian.health || 0) + "%";
      var gaugeVal = document.getElementById("gauge-value");
      if (gaugeVal) gaugeVal.textContent = guardian.health || 0;

      var survival = document.getElementById("kpi-survival");
      if (survival) survival.textContent = guardian.health || 0;
    } catch(e) {
      console.log("KPI fetch error:", e);
    }
  }

  function setKPI(id, value) {
    var el = document.getElementById(id);
    if (el) {
      if (typeof value === "number" && value > 0) {
        animateCounter(el, value);
      } else {
        el.textContent = value;
      }
    }
  }

  // ANIMATED COUNTERS
  function animateCounter(element, target, duration) {
    duration = duration || 2000;
    var start = 0;
    var increment = target / (duration / 16);
    function update() {
      start += increment;
      if (start < target) {
        element.textContent = Math.floor(start);
        requestAnimationFrame(update);
      } else {
        element.textContent = target;
      }
    }
    update();
  }

  // INTERSECTION OBSERVER FOR ANIMATIONS
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: "0px 0px -50px 0px" });

  document.querySelectorAll(".fade-in, section").forEach(function(el) {
    observer.observe(el);
  });

  // LAZY LOADING IMAGES
  var images = document.querySelectorAll("img[data-src]");
  var imgObs = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        var img = entry.target;
        img.src = img.dataset.src;
        img.classList.add("loaded");
        imgObs.unobserve(img);
      }
    });
  });
  images.forEach(function(img) { imgObs.observe(img); });

  // SMOOTH SCROLL
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener("click", function(e) {
      e.preventDefault();
      var target = document.querySelector(this.getAttribute("href"));
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  // LOAD REAL DATA
  loadRealKPIs();
  setInterval(loadRealKPIs, 30000);
});