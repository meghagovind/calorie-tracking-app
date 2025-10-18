// inside your renderResult(data) function, add Save button and "Save" flow
function renderResult(data) {
  if (data.error) {
    result.innerText = "Error: " + data.error;
    return;
  }

  let html = `<h3>Estimated total calories: ${data.total_estimated_calories || 0} kcal</h3>`;
  html += "<ul>";
  for (const it of data.items || []) {
    html += `<li>${escapeHtml(it.label)} — ${it.calories !== null ? it.calories + " kcal" : "unknown"} (source: ${it.source})</li>`;
  }
  html += "</ul>";

  // Save button & note input
  html += `<div style="margin-top:8px;">
    <input id="mealNote" placeholder="optional note (e.g., lunch)" style="padding:6px;border-radius:4px;border:1px solid #ddd" />
    <button id="saveMealBtn" style="margin-left:8px;padding:6px 10px">Save meal</button>
    <span id="saveStatus" style="margin-left:10px;color:green"></span>
  </div>`;

  result.innerHTML = html;

  document.getElementById("saveMealBtn").addEventListener("click", async () => {
    const note = document.getElementById("mealNote").value || null;
    document.getElementById("saveStatus").innerText = "Saving...";
    try {
      const payload = {
        items: data.items,
        total_estimated_calories: data.total_estimated_calories,
        note: note
      };
      const res = await fetch("/save_meal", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      const j = await res.json();
      if (j.saved) {
        document.getElementById("saveStatus").innerText = "Saved ✓";
        // optionally refresh daily summary display
        fetchDailySummary(); 
      } else {
        document.getElementById("saveStatus").innerText = "Save failed";
      }
    } catch (err) {
      console.error(err);
      document.getElementById("saveStatus").innerText = "Error saving";
    }
  });
}

// add a function to show daily summary at top or bottom
async function fetchDailySummary(dateStr) {
  try {
    const today = dateStr || new Date().toISOString().slice(0,10);
    const res = await fetch(`/summary?date=${today}`);
    const data = await res.json();
    // render a small summary
    const summaryEl = document.getElementById("dailySummary") || (() => {
      const el = document.createElement("div");
      el.id = "dailySummary";
      el.style.marginTop = "14px";
      document.body.insertBefore(el, document.getElementById("result"));
      return el;
    })();
    let html = `<h3>Daily summary (${data.date}) — ${Math.round(data.total_cal)} kcal across ${data.meals_count} meals</h3>`;
    html += "<ol>";
    for (const m of data.meals) {
      const time = new Date(m.timestamp).toLocaleTimeString();
      html += `<li><b>${time}</b>: ${Math.round(m.total_cal)} kcal — ${m.items.map(it => escapeHtml(it.label)).join(", ")}</li>`;
    }
    html += "</ol>";
    summaryEl.innerHTML = html;
  } catch (err) {
    console.error("summary fetch error", err);
  }
}

// call fetchDailySummary on initial page load
fetchDailySummary();
