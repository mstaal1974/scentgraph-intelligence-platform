const stages = ["supplier_import", "match_candidate", "profile_draft", "enrichment_review",
  "catalogue_promotion", "scent_vector", "recommendation", "maison_api_ready"];
const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g,
  (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[char]);
let pending;

async function get(path) { const response = await fetch(path); if (!response.ok) throw Error(await response.text()); return response.json(); }
function itemMarkup(item) { return `<article class="item"><strong>${escapeHtml(item.title)}</strong>
  <div class="flag">${escapeHtml(item.stage)} · ${escapeHtml(item.status)}</div>
  <p>${escapeHtml(item.blocking_reason || item.provenance_summary)}</p></article>`; }
async function refresh() {
  const filter = $("#stage").value;
  const [summary, queue, blocked, readiness] = await Promise.all([
    get("/admin/review/summary"), get(`/admin/review/queue${filter ? `/${filter}` : ""}`),
    get("/admin/review/blocked"), get("/admin/review/readiness")]);
  $("#summary").innerHTML = [["Total",summary.total],["Human review",summary.requiring_human_review],
    ["Ready",summary.ready_for_approval],["Blocked",summary.blocked]].map(([label,value]) =>
      `<div class="card"><span>${label}</span><strong>${value}</strong></div>`).join("");
  $("#queue").innerHTML = `<table><thead><tr><th>Record</th><th>Status & confidence</th><th>Provenance / blocker</th><th>Actions</th></tr></thead><tbody>${queue.map((item) =>
    `<tr><td><strong>${escapeHtml(item.title)}</strong><br><span class="muted">${escapeHtml(item.stage)} · ${escapeHtml(item.source_record_id)}</span></td>
    <td>${escapeHtml(item.status)}<br>${Math.round(item.confidence_score*100)}% · source ${Math.round(item.source_confidence*100)}%</td>
    <td>${item.blocking_reason ? `<span class="danger">${escapeHtml(item.blocking_reason)}</span>` : escapeHtml(item.provenance_summary)}</td>
    <td>${["approve","reject","request-more-sources"].map((action) => `<button data-stage="${item.stage}" data-id="${item.source_record_id}" data-action="${action}">${action.replaceAll("-"," ")}</button>`).join(" ")}</td></tr>`).join("")}</tbody></table>`;
  $("#blocked").innerHTML = blocked.length ? blocked.map(itemMarkup).join("") : '<p class="muted">No blocked records.</p>';
  $("#readiness").innerHTML = `<div class="card"><strong>${readiness.maison_api_ready_count}</strong><span>Maison API-ready</span><p>${readiness.ready_count} ready; ${readiness.not_ready_count} not ready.</p></div>`;
}
$("#stage").innerHTML += stages.map((stage) => `<option>${stage}</option>`).join("");
$("#stage").addEventListener("change", refresh);
$("#queue").addEventListener("click", (event) => { const button = event.target.closest("button"); if (!button) return;
  pending = button.dataset; $("#decision-title").textContent = button.textContent; $("#reason").required = pending.action === "reject";
  $("#decision-error").textContent = ""; $("#decision").showModal(); });
$("#submit").addEventListener("click", async (event) => { event.preventDefault();
  const reviewer = $("#reviewer").value.trim(), reason = $("#reason").value.trim();
  if (!reviewer || (pending.action === "reject" && !reason)) { $("#decision-error").textContent = "Reviewer and rejection reason are required."; return; }
  const response = await fetch(`/admin/review/${pending.stage}/${pending.id}/${pending.action}`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({reviewer,reason:reason||null})});
  if (!response.ok) { $("#decision-error").textContent = (await response.json()).detail || "Decision failed"; return; }
  $("#decision").close(); await refresh(); });
refresh().catch((error) => { $("#queue").textContent = `Unable to load review data: ${error.message}`; });
