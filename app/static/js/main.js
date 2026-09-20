(function () {
  var bz = document.getElementById("batch-zone");
  var binput = document.getElementById("batch-input");
  var bform = document.getElementById("batch-form");
  var bstart = document.getElementById("batch-start");
  var bcount = document.getElementById("batch-count");
  var bprog = document.getElementById("batch-progress");
  var bfill = document.getElementById("progress-fill");
  var btext = document.getElementById("progress-text");
  var bdone = document.getElementById("batch-done");

  if (!bz || !bform) return;

  bindZone(bz, binput, updateCount);
  binput.addEventListener("change", updateCount);

  function bindZone(zone, fileInput, onPick) {
    zone.addEventListener("click", function () { fileInput.click(); });
    zone.addEventListener("dragover", function (e) {
      e.preventDefault();
      zone.classList.add("drag");
    });
    zone.addEventListener("dragleave", function () { zone.classList.remove("drag"); });
    zone.addEventListener("drop", function (e) {
      e.preventDefault();
      zone.classList.remove("drag");
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        onPick();
      }
    });
  }

  function updateCount() {
    var n = binput.files ? binput.files.length : 0;
    bstart.disabled = !n;
    bcount.textContent = n ? "عدد الصور المختارة: " + n : "";
  }

  bform.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!binput.files.length) return;
    bstart.disabled = true;
    bcount.textContent = "";
    bdone.classList.add("hidden");
    bdone.innerHTML = "";
    bprog.classList.remove("hidden");
    bfill.style.width = "0%";
    btext.textContent = "جارٍ رفع الصور...";

    var fd = new FormData();
    Array.prototype.forEach.call(binput.files, function (f) { fd.append("images", f); });

    fetch(bform.getAttribute("action") || "/batch/start", { method: "POST", body: fd })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.error) { showDone("خطأ: " + res.error); return; }
        poll(res.job_id);
      })
      .catch(function (err) { showDone("خطأ في الرفع: " + err); });
  });

  function poll(jobId) {
    fetch("/batch/" + jobId + "/progress")
      .then(function (r) { return r.json(); })
      .then(function (p) {
        if (p.status === "missing") { showDone("الدفعة غير موجودة."); return; }
        var pct = p.total ? Math.round(100 * p.current / p.total) : 0;
        bfill.style.width = pct + "%";
        btext.textContent = "جارٍ المعالجة... " + p.current + " / " + p.total +
          " (نجاح: " + p.success + "، فشل: " + p.failed + ")";
        if (p.status === "done") {
          showDone("اكتملت المعالجة! إجمالي: " + p.total +
            " — نجحت: " + p.success + "، فشلت: " + p.failed);
          var a = document.createElement("a");
          a.className = "btn btn-dl";
          a.href = p.zip_url;
          a.textContent = "تنزيل ZIP";
          bdone.appendChild(a);
        } else if (p.status === "error") {
          showDone("خطأ أثناء المعالجة: " + p.message);
        } else {
          setTimeout(function () { poll(jobId); }, 1000);
        }
      })
      .catch(function (err) { showDone("خطأ في الاستعلام: " + err); });
  }

  function showDone(text) {
    bprog.classList.add("hidden");
    bdone.classList.remove("hidden");
    bdone.innerHTML = "";
    var p = document.createElement("p");
    p.className = "done-text";
    p.textContent = text;
    bdone.appendChild(p);
    bstart.disabled = true;
  }
})();