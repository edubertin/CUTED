from __future__ import annotations

import json
from pathlib import Path


def project_home_css() -> str:
    return """
body[data-project-home]{overflow-x:hidden}body[data-project-home] header{display:none}.project-home{width:min(1080px,calc(100vw - 36px));max-width:none;min-height:100vh;padding:30px 0 34px;align-content:start;gap:12px}.home-brand-stage{display:grid;place-items:center;min-height:164px;padding:4px 0 0}.home-logo-orbit{position:relative;display:grid;place-items:center;width:min(620px,84vw);isolation:isolate}.home-logo-orbit:before{position:absolute;inset:18% 12%;z-index:-1;border-radius:999px;background:radial-gradient(circle at 26% 50%,rgba(17,162,207,.28),transparent 34%),radial-gradient(circle at 74% 50%,rgba(175,207,42,.24),transparent 34%);filter:blur(24px);content:"";animation:home-logo-aura 5.2s ease-in-out infinite}.home-brand-logo{display:block;width:min(520px,80vw);height:104px;object-fit:contain;filter:drop-shadow(0 0 12px rgba(17,162,207,.18)) drop-shadow(0 0 12px rgba(175,207,42,.12));animation:home-logo-breathe 5.8s ease-in-out infinite}.project-library{display:grid;align-content:start;gap:0;border:1px solid var(--glass-border);border-radius:8px;background:linear-gradient(180deg,rgba(255,255,255,.052),rgba(255,255,255,.016)),rgba(7,7,7,.76);box-shadow:0 18px 46px rgba(0,0,0,.42),inset 0 1px 0 var(--glass-edge);backdrop-filter:blur(22px) saturate(1.22);overflow:hidden}.project-section-head{display:flex;justify-content:space-between;gap:12px;align-items:center;min-height:52px;padding:9px 16px;border-bottom:1px solid rgba(231,231,232,.1)}.project-section-head strong{font-size:17px;letter-spacing:0}.project-toolbar{display:flex;gap:8px;align-items:center;justify-content:flex-end;flex-wrap:wrap}.project-toolbar button,.project-row-actions button,.project-row-actions a{min-height:32px;padding:6px 11px}.project-icon-button{display:inline-grid!important;place-items:center;width:36px;min-width:36px;padding:0!important;font-size:17px;font-weight:900}.project-primary{border-color:rgba(175,207,42,.58)!important;background:linear-gradient(180deg,rgba(175,207,42,.26),rgba(17,162,207,.1)),rgba(23,32,14,.78)!important;color:var(--color-text)!important}.project-table{display:grid;max-height:min(456px,calc(100vh - 304px));overflow:auto;scrollbar-width:thin;scrollbar-color:rgba(175,207,42,.55) rgba(255,255,255,.055)}.project-table::-webkit-scrollbar{width:10px}.project-table::-webkit-scrollbar-track{background:rgba(255,255,255,.04);border-left:1px solid rgba(231,231,232,.06)}.project-table::-webkit-scrollbar-thumb{border:2px solid rgba(7,7,7,.76);border-radius:999px;background:linear-gradient(180deg,rgba(17,162,207,.72),rgba(175,207,42,.72));box-shadow:0 0 12px rgba(17,162,207,.22)}.project-table::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,var(--color-brand-blue),var(--color-brand-green))}.project-table-head,.project-row{display:grid;grid-template-columns:minmax(230px,1fr) minmax(245px,.82fr) 100px minmax(214px,.58fr);gap:14px;align-items:center}.project-table-head{position:sticky;top:0;z-index:2;min-height:34px;padding:0 16px;border-bottom:1px solid rgba(231,231,232,.08);background:rgba(11,11,11,.92);color:var(--color-text-muted);font-size:11px;text-transform:uppercase;backdrop-filter:blur(12px)}.project-row{min-height:76px;padding:12px 16px;border-bottom:1px solid rgba(231,231,232,.075);animation:home-row-in .42s ease both}.project-row:last-child{border-bottom:0}.project-row:nth-child(2){animation-delay:.03s}.project-row:nth-child(3){animation-delay:.08s}.project-row:nth-child(4){animation-delay:.13s}.project-row:nth-child(5){animation-delay:.18s}.project-row:hover{background:linear-gradient(90deg,rgba(17,162,207,.085),rgba(175,207,42,.045),transparent)}.project-name-cell{display:grid;gap:3px;min-width:0}.project-name-cell strong{font-size:15px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.project-name-cell p{margin:0;color:rgba(175,207,42,.82);font-size:12px}.project-name-cell small{display:block;color:#777;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.project-meta-cell{display:flex;gap:10px;margin:0}.project-meta-cell div{display:grid;gap:2px;min-width:62px}.project-meta-cell dt{color:var(--color-text-muted);font-size:11px}.project-meta-cell dd{margin:0;color:var(--color-text);font-weight:800}.project-updated-cell{color:var(--color-text-muted);font-size:12px}.project-row-actions{display:flex;gap:7px;justify-content:flex-end;flex-wrap:wrap}.project-row-actions a{display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--glass-border);border-radius:999px;background:var(--color-brand-white);color:var(--color-brand-black);text-decoration:none}.project-row-actions button[data-delete-project]{color:var(--color-danger)}.project-row-actions button:disabled{opacity:.38;cursor:not-allowed}.project-import{margin-top:12px}.project-import[hidden],.project-library[hidden]{display:none}.project-import .import-panel{animation:home-row-in .28s ease both}.new-project-panel{gap:14px;border-color:var(--glass-border);background:linear-gradient(180deg,rgba(255,255,255,.052),rgba(255,255,255,.016)),rgba(7,7,7,.76);box-shadow:0 18px 46px rgba(0,0,0,.42),inset 0 1px 0 var(--glass-edge);backdrop-filter:blur(22px) saturate(1.22)}.new-project-head,.new-project-footer,.ai-context-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.new-project-head{min-height:38px;padding-bottom:10px;border-bottom:1px solid rgba(231,231,232,.1)}.new-project-head strong{font-size:17px}.source-toggle{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.source-toggle label,.duration-size-toggle label{position:relative;display:grid}.source-toggle input,.duration-size-toggle input{position:absolute;opacity:0;pointer-events:none}.source-toggle span,.duration-size-toggle span{display:grid;place-items:center;min-height:48px;padding:8px 12px;border:1px solid var(--glass-border);border-radius:8px;background:rgba(231,231,232,.055);box-shadow:inset 0 1px rgba(255,255,255,.14);color:var(--color-text-soft);font-weight:800}.source-toggle input:checked+span,.duration-size-toggle input:checked+span{border-color:rgba(175,207,42,.72);background:linear-gradient(180deg,rgba(175,207,42,.2),rgba(17,162,207,.08)),rgba(13,18,12,.84);color:var(--color-text);box-shadow:inset 0 1px rgba(255,255,255,.18),0 0 22px rgba(175,207,42,.12)}.source-panel{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px}.source-panel[hidden]{display:none}.new-project-grid{display:grid;grid-template-columns:minmax(140px,.32fr) minmax(0,1fr);gap:12px;align-items:end}.suggestion-field{display:grid;gap:6px;color:var(--color-text-muted);font-size:12px}.duration-size-toggle{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:0;padding:0;border:0}.duration-size-toggle legend{grid-column:1/-1;color:var(--color-text-muted);font-size:12px}.duration-size-toggle span{min-height:58px}.duration-size-toggle strong{font-size:22px;line-height:1}.duration-size-toggle small{color:var(--color-text-muted);font-size:11px}.ai-context-box{display:grid;gap:8px;padding:12px;border:1px solid rgba(17,162,207,.28);border-radius:8px;background:linear-gradient(135deg,rgba(17,162,207,.09),rgba(175,207,42,.035)),rgba(0,0,0,.18)}.ai-context-box textarea{min-height:126px;border-color:rgba(17,162,207,.28);background:rgba(0,0,0,.44)}.new-project-footer{padding-top:4px}.new-project-footer span{color:var(--color-text-muted);font-size:12px}@keyframes home-logo-aura{0%,100%{opacity:.56;transform:scale(.98)}50%{opacity:.84;transform:scale(1.03)}}@keyframes home-logo-breathe{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-1px) scale(1.006)}}@keyframes home-row-in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}@media(max-width:900px){.project-home{width:min(100vw - 20px,760px);padding-top:26px}.home-brand-stage{min-height:138px}.home-brand-logo{height:78px}.project-section-head{align-items:flex-start;flex-direction:column}.project-toolbar{justify-content:flex-start}.project-table{max-height:none}.project-table-head{display:none}.project-row,.new-project-grid,.source-panel{grid-template-columns:1fr;gap:10px}.project-meta-cell{justify-content:space-between}.project-row-actions{justify-content:flex-start}.project-updated-cell{display:none}}
.project-empty-state{display:grid;justify-items:center;gap:6px;min-height:116px;padding:30px 18px;border-top:1px solid rgba(231,231,232,.075);color:rgba(231,231,232,.64);text-align:center;animation:home-row-in .3s ease both}.project-empty-state strong{color:var(--color-text);font-size:15px}.project-empty-state p{margin:0;color:var(--color-text-muted);font-size:12px}
"""


def project_home_compact_import_css() -> str:
    return """
.sr-only{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
.home-settings-button{position:fixed;top:18px;right:22px;z-index:20;border-color:var(--glass-border);background:rgba(231,231,232,.055);color:var(--color-text-soft);box-shadow:inset 0 1px rgba(255,255,255,.14)}
.home-settings-button:hover{border-color:rgba(17,162,207,.5);color:var(--color-text);background:rgba(17,162,207,.1)}
.home-settings-button svg{display:block;width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.new-project-config-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;align-items:start}
.new-project-config-block{display:grid;gap:8px;justify-self:stretch;width:100%;min-height:170px;padding:10px;border:1px solid rgba(231,231,232,.08);border-radius:8px;background:rgba(255,255,255,.018)}
.new-project-block-title{display:flex;align-items:baseline;justify-content:space-between;gap:10px;min-height:18px}
.new-project-block-title strong{color:var(--color-text);font-size:12px;text-transform:uppercase}
.new-project-block-title span,.tuning-copy{color:var(--color-text-muted);font-size:11px}
.icon-source-toggle{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;width:100%}
.icon-source-toggle span,.duration-size-toggle label span,.icon-action-button,.field-icon{display:grid;place-items:center;border:1px solid var(--glass-border);border-radius:8px;background:rgba(231,231,232,.055);box-shadow:inset 0 1px rgba(255,255,255,.14);color:var(--color-text-soft)}
.icon-source-toggle span{grid-template-rows:auto auto;gap:4px;min-height:68px;padding:9px 8px}
.icon-source-toggle span strong{font-size:11px;letter-spacing:0;text-transform:uppercase}
.icon-source-toggle input:checked+span,.duration-size-toggle input:checked+span{border-color:rgba(175,207,42,.72);background:rgba(25,33,18,.9);color:var(--color-text);box-shadow:inset 0 1px rgba(255,255,255,.18),0 0 18px rgba(175,207,42,.13)}
.icon-source-toggle svg,.duration-size-toggle svg,.icon-action-button svg,.field-icon svg{display:block;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.icon-source-toggle svg{width:30px;height:30px}
.source-panel{grid-template-columns:minmax(0,1fr) 52px;gap:8px;width:100%}
.source-panel[data-source-panel=youtube]{grid-template-columns:minmax(0,1fr)}
.source-panel input,.suggestion-field select{min-height:44px}
.icon-action-button{width:52px;min-width:52px;min-height:44px;padding:0!important}
.icon-action-button svg,.field-icon svg{width:19px;height:19px}
.icon-action-button:hover{border-color:rgba(17,162,207,.52);color:var(--color-text);background:rgba(17,162,207,.1)}
.cuts-control-grid{display:grid;grid-template-columns:minmax(128px,.42fr) minmax(0,.58fr);gap:10px;align-items:stretch}
.cut-count-field{display:grid!important;grid-template-rows:auto 1fr;gap:8px;min-width:0;color:inherit;font-size:inherit}
.cut-count-field .tuning-copy{align-self:end;font-weight:800;text-transform:uppercase}
.cut-count-field select{width:100%;min-height:96px;padding:0 14px;border:1px solid var(--glass-border);border-radius:8px;background:#202020;color:var(--color-text);font-weight:900;text-align:center}
.cut-count-field select option{background:#111;color:var(--color-text)}
.duration-size-toggle{display:grid;grid-template-columns:minmax(0,1fr) repeat(3,62px);gap:8px;align-items:center;margin:0;padding:0;border:0}
.duration-size-toggle legend.sr-only{position:absolute;grid-column:auto;color:inherit;font-size:inherit}
.duration-size-toggle>.tuning-copy{display:flex!important;align-items:center;min-height:auto!important;padding:0!important;border:0!important;background:transparent!important;box-shadow:none!important;color:var(--color-text-muted)!important;font-weight:600}
.duration-size-toggle label span{gap:2px;min-width:62px;min-height:44px;padding:6px 8px}
.duration-size-toggle label small{color:var(--color-text-muted);font-size:10px;line-height:1}
.duration-tile-grid{grid-template-columns:repeat(2,minmax(0,1fr));grid-template-rows:repeat(2,minmax(0,1fr));align-items:stretch}
.duration-tile-grid label span{width:100%;min-width:0;min-height:44px}
.duration-option-long{grid-column:1/-1}
.duration-size-toggle svg{width:14px;height:14px;opacity:.72}
.duration-size-toggle strong{font-size:17px;line-height:1}
.ai-context-title{display:grid;gap:2px}.ai-context-title small{color:var(--color-text-muted);font-size:11px;line-height:1.25}.ai-context-device-row{display:grid;grid-template-columns:minmax(160px,240px) minmax(120px,1fr);gap:8px;align-items:center}.ai-context-device-row select{min-height:32px;padding:5px 8px;border-color:rgba(231,231,232,.12);font-size:12px}.ai-context-level{height:8px;overflow:hidden;border:1px solid rgba(231,231,232,.12);border-radius:999px;background:rgba(0,0,0,.32)}.ai-context-level span{display:block;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--color-brand-blue),var(--color-brand-green));transition:width .16s ease}.ai-context-status{min-height:18px;color:rgba(231,231,232,.68);font-size:12px}.ai-context-box[data-audio-state=recording]{border-color:rgba(17,162,207,.72);box-shadow:0 0 0 1px rgba(17,162,207,.22),0 0 28px rgba(17,162,207,.12)}.ai-context-box[data-audio-state=recording] .context-audio-button{border-color:rgba(17,162,207,.8);background:rgba(17,162,207,.18);color:var(--color-text);animation:context-mic-pulse 1.1s ease-in-out infinite}.ai-context-box[data-audio-state=transcribing] .context-audio-button{border-color:rgba(175,207,42,.7);background:rgba(175,207,42,.14);color:var(--color-text)}.ai-context-box[data-audio-state=applied]{border-color:rgba(175,207,42,.52)}.ai-context-box[data-audio-state=error]{border-color:rgba(255,111,111,.52)}
.context-audio-button{border-radius:999px}
@keyframes context-mic-pulse{0%,100%{box-shadow:0 0 0 0 rgba(17,162,207,.18)}50%{box-shadow:0 0 0 7px rgba(17,162,207,.08)}}
.import-submit-button{min-width:116px;min-height:42px!important;border-color:var(--color-brand-white)!important;background:var(--color-brand-white)!important;color:var(--color-brand-black)!important;font-weight:900;box-shadow:0 10px 24px rgba(0,0,0,.32)}
.import-submit-button:hover{transform:translateY(-1px);border-color:var(--color-brand-green)!important;background:var(--color-brand-green)!important;color:var(--color-brand-black)!important;box-shadow:0 12px 26px rgba(0,0,0,.36),0 0 16px rgba(175,207,42,.16)}
.home-import-loading{position:fixed;inset:0;z-index:60;display:grid;place-items:center;background:radial-gradient(circle at 50% 42%,rgba(17,162,207,.12),transparent 30%),radial-gradient(circle at 56% 52%,rgba(175,207,42,.09),transparent 34%),rgba(5,5,5,.88);backdrop-filter:blur(18px) saturate(1.25)}
.home-import-loading[hidden]{display:none}
.home-import-loading-inner{display:grid;justify-items:center;gap:14px;width:min(520px,calc(100vw - 44px));animation:home-row-in .28s ease both}
.home-import-loading img{display:block;width:min(360px,76vw);height:96px;object-fit:contain;filter:drop-shadow(0 0 14px rgba(17,162,207,.16)) drop-shadow(0 0 12px rgba(175,207,42,.12))}
.home-import-progress{position:relative;width:100%;height:42px;border:1px solid var(--glass-border);border-radius:999px;background:rgba(231,231,232,.055);box-shadow:inset 0 1px rgba(255,255,255,.14),0 18px 44px rgba(0,0,0,.34);overflow:hidden}
.home-import-progress span{position:absolute;inset:0 auto 0 0;width:8%;border-radius:999px;background:linear-gradient(90deg,var(--color-brand-blue),var(--color-brand-green));transition:width .5s ease}
.home-import-progress strong{position:relative;z-index:1;display:grid;place-items:center;height:100%;padding:0 18px;color:var(--color-text);font-size:13px;text-align:center;text-shadow:0 1px 8px rgba(0,0,0,.6)}
.home-import-loading small{color:var(--color-text-muted);font-size:12px;text-transform:uppercase}
.home-import-detail{min-height:18px;margin:-4px 0 0;color:rgba(231,231,232,.7);font-size:12px;text-align:center}
.home-import-steps{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:6px;width:100%;margin:2px 0 0;padding:0;list-style:none}
.home-import-steps li{display:grid;justify-items:center;gap:6px;min-width:0;color:rgba(231,231,232,.48);font-size:10px;font-weight:800;text-transform:uppercase}
.home-import-steps li span{display:block;width:10px;height:10px;border:1px solid rgba(231,231,232,.18);border-radius:999px;background:rgba(231,231,232,.08);box-shadow:inset 0 1px rgba(255,255,255,.12)}
.home-import-steps li[data-state=done]{color:rgba(175,207,42,.86)}.home-import-steps li[data-state=done] span{border-color:rgba(175,207,42,.62);background:var(--color-brand-green);box-shadow:0 0 14px rgba(175,207,42,.3)}
.home-import-steps li[data-state=active]{color:var(--color-text)}.home-import-steps li[data-state=active] span{border-color:rgba(17,162,207,.72);background:var(--color-brand-blue);box-shadow:0 0 16px rgba(17,162,207,.38);animation:home-import-step-pulse 1.2s ease-in-out infinite}
.home-import-loading[data-state=failed] .home-import-progress span{background:linear-gradient(90deg,#7f1d1d,var(--color-danger))}
.home-import-loading[data-state=failed] .home-import-steps li[data-state=active] span{border-color:rgba(255,111,111,.68);background:var(--color-danger);box-shadow:0 0 16px rgba(255,111,111,.32);animation:none}
.home-import-loading button{min-height:38px;padding:8px 14px;border-color:var(--glass-border);background:var(--color-brand-white);color:var(--color-brand-black)}
body[data-importing=true] .project-home{opacity:0;pointer-events:none;transition:opacity .24s ease}
@keyframes home-import-step-pulse{0%,100%{transform:scale(1);opacity:.72}50%{transform:scale(1.2);opacity:1}}
@media(max-width:680px){.home-import-steps{grid-template-columns:repeat(4,minmax(0,1fr))}.home-import-steps li{font-size:9px}}
@media(max-width:900px){.new-project-config-grid{grid-template-columns:1fr}.new-project-config-block{width:100%}.source-panel,.source-panel[data-source-panel=youtube]{grid-template-columns:minmax(0,1fr) 52px}.source-panel[data-source-panel=youtube]{grid-template-columns:minmax(0,1fr)}.cuts-control-grid{grid-template-columns:1fr}.cut-count-field select{min-height:54px}.duration-tile-grid{grid-template-columns:repeat(2,minmax(54px,1fr))}.duration-size-toggle span{min-width:0}}
"""


def project_home_js(workspace: Path) -> str:
    script = r"""
const workspacePath = __WORKSPACE_PATH__;
const homeImport = document.querySelector("[data-home-import]");
const projectLibrary = document.querySelector("[data-project-library]");
const projectList = document.querySelector("[data-project-list]");
function escapeHtml(value){
  return String(value || "").replace(/[&<>"']/g, char => {
    if (char === "&") return "&amp;";
    if (char === "<") return "&lt;";
    if (char === ">") return "&gt;";
    if (char === '"') return "&quot;";
    return "&#39;";
  });
}
function escapeAttr(value){ return escapeHtml(value); }
function projectPayload(form){
  const data = new FormData(form);
  const sourceMode = String(data.get("source_mode") || form.dataset.sourceMode || "local");
  return {
    source_path: sourceMode === "local" ? String(data.get("source_path") || "").trim() : "",
    source_url: sourceMode === "youtube" ? String(data.get("source_url") || "").trim() : "",
    output_path: String(data.get("output_path") || "").trim(),
    preview_count: Number(data.get("preview_count") || 10),
    language: String(data.get("language") || "pt"),
    preset: String(data.get("preset") || "tiktok"),
    duration_profile: String(data.get("duration_profile") || "medium"),
    context_prompt: String(data.get("context_prompt") || ""),
    render_previews: true
  };
}
function setStatus(text){
  const status = document.querySelector("[data-import-status]");
  if (status) status.textContent = text;
}
function setResult(html){
  const result = document.querySelector("[data-import-result]");
  if (result) result.innerHTML = html;
}
async function postJson(url, payload){
  const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload || {}) });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || !data.ok) throw new Error(data.error || "Local operation failed.");
  return data;
}
let importOpenaiState = { provider: "local", keyConfigured: true };
function importNeedsOpenaiKey(){
  return importOpenaiState.provider === "openai" && !importOpenaiState.keyConfigured;
}
const importStageOrder = ["prepare", "media", "audio", "analysis", "suggestions", "previews", "publish", "editor"];
function setImportLoading(message, label = "Import", percent = 8, progress = {}){
  const loading = document.querySelector("[data-import-loading]");
  if (!loading) return;
  const value = Math.max(0, Math.min(100, Number(percent || 0)));
  const stage = String(progress.stage || "prepare");
  loading.hidden = false;
  loading.dataset.state = "running";
  document.body.dataset.importing = "true";
  loading.querySelector("[data-import-loading-message]").textContent = message || "Processing...";
  loading.querySelector("[data-import-loading-label]").textContent = label || "Import";
  loading.querySelector("[data-import-loading-detail]").textContent = importProgressDetail(progress);
  loading.querySelector("[data-import-loading-bar]").style.width = `${value}%`;
  loading.querySelector("[role=progressbar]").setAttribute("aria-valuenow", String(value));
  loading.querySelector("[data-import-loading-back]").hidden = true;
  updateImportSteps(stage);
}
function importProgressDetail(progress){
  if (progress.detail) return String(progress.detail);
  const step = Number(progress.step || 0);
  const steps = Number(progress.steps || 0);
  if (step && steps) return `${step} of ${steps}`;
  if (progress.stage === "media") return "Preparing the video source.";
  if (progress.stage === "audio") return "Converting and transcribing audio.";
  if (progress.stage === "analysis") return "Finding strong hooks and complete thoughts.";
  if (progress.stage === "previews") return "Generating samples for editor review.";
  return "Follow the steps while the project is created.";
}
function updateImportSteps(stage){
  const currentIndex = importStageOrder.includes(stage) ? importStageOrder.indexOf(stage) : 0;
  document.querySelectorAll("[data-import-step]").forEach(item => {
    const index = importStageOrder.indexOf(item.dataset.importStep || "");
    item.dataset.state = index < currentIndex ? "done" : index === currentIndex ? "active" : "";
  });
}
function updateImportLoading(job){
  const progress = job.progress || {};
  setImportLoading(progress.message || job.message || "Processing import...", progress.label || job.status || "Import", progress.percent || 35, progress);
}
function failImportLoading(message){
  const loading = document.querySelector("[data-import-loading]");
  if (!loading) return;
  loading.hidden = false;
  loading.dataset.state = "failed";
  loading.querySelector("[data-import-loading-message]").textContent = message || "Could not import this project.";
  loading.querySelector("[data-import-loading-label]").textContent = "Import stopped";
  loading.querySelector("[data-import-loading-detail]").textContent = "Check the message below and try again.";
  loading.querySelector("[data-import-loading-bar]").style.width = "100%";
  loading.querySelector("[role=progressbar]").setAttribute("aria-valuenow", "100");
  loading.querySelector("[data-import-loading-back]").hidden = false;
}
function hideImportLoading(){
  const loading = document.querySelector("[data-import-loading]");
  if (loading) loading.hidden = true;
  delete document.body.dataset.importing;
}
const activeImportJobStorageKey = "cuted-active-import-job";
let activeImportPollJobId = "";
function importJobStorage(){
  try {
    return window.sessionStorage;
  } catch (error) {
    console.warn("Could not access sessionStorage for import recovery.", error);
    return null;
  }
}
function saveActiveImportJob(job){
  if (!job?.id) return;
  const storage = importJobStorage();
  if (!storage) return;
  storage.setItem(activeImportJobStorageKey, JSON.stringify({
    id: job.id,
    output_url: job.output_url || "",
    updated_at: Date.now()
  }));
}
function storedActiveImportJob(){
  const storage = importJobStorage();
  if (!storage) return null;
  try {
    const data = JSON.parse(storage.getItem(activeImportJobStorageKey) || "null");
    return data && data.id ? data : null;
  } catch (error) {
    storage.removeItem(activeImportJobStorageKey);
    return null;
  }
}
function clearActiveImportJob(jobId){
  const storage = importJobStorage();
  if (!storage) return;
  const active = storedActiveImportJob();
  if (!jobId || !active || active.id === jobId) storage.removeItem(activeImportJobStorageKey);
}
async function completeImportJob(job, button, options = {}){
  activeImportPollJobId = "";
  clearActiveImportJob(job.id || options.jobId);
  if (button) button.disabled = false;
  setImportLoading("Project ready. Opening editor...", "Done", 100, { stage: "editor", detail: "Updating recent projects." });
  if (job.output_url) setResult(`<a href="${escapeAttr(job.output_url)}">Open imported project</a>`);
  await refreshProjects().catch(error => console.warn("Could not refresh projects after import.", error));
  if (job.output_url && options.open !== false) {
    window.setTimeout(() => window.location.assign(job.output_url), 450);
  }
}
async function importOutputIsReady(outputUrl){
  if (!outputUrl) return false;
  try {
    const response = await fetch(outputUrl, { cache: "no-store" });
    return response.ok;
  } catch (error) {
    return false;
  }
}
function recoverActiveImportJob(options = {}){
  const active = storedActiveImportJob();
  if (!active?.id || activeImportPollJobId === active.id) return;
  setImportLoading("Resuming import...", "Tracking", 35, { stage: "analysis", detail: "Reconnecting to the active job." });
  pollImport(active.id, document.querySelector("[data-import-form] button[type=submit]"), options);
}
function setupImportRecovery(){
  refreshProjects().catch(error => console.warn("Could not refresh projects on Home load.", error));
  recoverActiveImportJob();
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible") return;
    refreshProjects().catch(error => console.warn("Could not refresh projects when the tab returned.", error));
    recoverActiveImportJob();
  });
  window.addEventListener("focus", () => {
    refreshProjects().catch(error => console.warn("Could not refresh projects on focus.", error));
    recoverActiveImportJob();
  });
}
async function startImport(form){
  const button = form.querySelector("button[type=submit]");
  const payload = projectPayload(form);
  if (!payload.source_path && !payload.source_url) {
    setStatus(form.dataset.sourceMode === "youtube" ? "Paste a YouTube link." : "Select a local video.");
    form.querySelector(form.dataset.sourceMode === "youtube" ? "[name=source_url]" : "[name=source_path]")?.focus();
    return;
  }
  if (importNeedsOpenaiKey()) {
    setStatus("Add your OpenAI key in Settings to import with AI.");
    openSettingsPanel();
    return;
  }
  setResult("");
  setImportLoading("Preparing project...", "Preparing", 8, { stage: "prepare", detail: "Organizing local files." });
  setStatus("Creating import job...");
  if (button) button.disabled = true;
  try {
    const data = await postJson("/api/import-jobs", payload);
    setStatus(data.job?.message || "Import started.");
    updateImportLoading(data.job || {});
    saveActiveImportJob(data.job || {});
    pollImport(data.job.id, button);
  } catch (error) {
    if (button) button.disabled = false;
    failImportLoading(error.message || "Could not start the import.");
    setStatus("Could not start the import.");
    setResult(`<code>${escapeHtml(error.message || String(error))}</code>`);
  }
}
async function pollImport(jobId, button, options = {}){
  if (!jobId) return;
  activeImportPollJobId = jobId;
  try {
    const response = await fetch(`/api/import-jobs/${encodeURIComponent(jobId)}`);
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "Job not found.");
    const job = data.job || {};
    setStatus(`${job.message || "Processing..."} (${job.status || "running"})`);
    updateImportLoading(job);
    if (job.status === "ready") {
      await completeImportJob(job, button, { jobId, open: options.open !== false });
      return;
    }
    if (job.status === "failed" || job.status === "cancelled") {
      activeImportPollJobId = "";
      clearActiveImportJob(jobId);
      if (button) button.disabled = false;
      failImportLoading(job.stderr || job.message || "Import ended.");
      setResult(`<code>${escapeHtml(job.stderr || job.message || "Import ended.")}</code>`);
      return;
    }
    window.setTimeout(() => pollImport(jobId, button), 1200);
  } catch (error) {
    activeImportPollJobId = "";
    const active = storedActiveImportJob();
    if (active?.id === jobId && await importOutputIsReady(active.output_url)) {
      await completeImportJob({ id: jobId, output_url: active.output_url }, button, { jobId, open: options.open !== false });
      return;
    }
    if (button) button.disabled = false;
    setImportLoading("Reconnecting import...", "Tracking", 35, { stage: "analysis", detail: "The tab lost the job stream; retrying." });
    setStatus("Could not track the import. I will retry when the tab comes back.");
    setResult(`<code>${escapeHtml(error.message || String(error))}</code>`);
    refreshProjects().catch(() => {});
  }
}
let contextAudio = { recorder: null, stream: null, chunks: [], startedAt: 0, audioContext: null, analyser: null, levelTimer: 0, maxLevel: 0, deviceLabel: "" };
function setContextAudioState(form, state, message){
  const box = form.querySelector("[data-ai-context-box]");
  const status = form.querySelector("[data-context-audio-status]");
  const button = form.querySelector("[data-context-audio]");
  if (box) box.dataset.audioState = state || "ready";
  if (status) status.textContent = message || "";
  if (button) button.disabled = state === "transcribing";
  if (button) button.title = state === "recording" ? "Stop recording" : "Record voice briefing";
}
function contextAudioMimeType(){
  if (!window.MediaRecorder) return "";
  const types = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
  return types.find(type => MediaRecorder.isTypeSupported(type)) || "";
}
function selectedContextAudioDeviceId(form){
  return String(form.querySelector("[data-context-audio-device]")?.value || "");
}
function contextAudioConstraints(form){
  const deviceId = selectedContextAudioDeviceId(form);
  const audio = { echoCancellation: false, noiseSuppression: false, autoGainControl: true };
  if (deviceId) audio.deviceId = { exact: deviceId };
  return { audio };
}
async function refreshContextAudioDevices(form){
  const select = form.querySelector("[data-context-audio-device]");
  if (!select || !navigator.mediaDevices?.enumerateDevices) return;
  const current = select.value;
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const audioInputs = devices.filter(device => device.kind === "audioinput");
    select.innerHTML = '<option value="">Default microphone</option>';
    audioInputs.forEach((device, index) => {
      const option = document.createElement("option");
      option.value = device.deviceId;
      option.textContent = device.label || `Microphone ${index + 1}`;
      select.appendChild(option);
    });
    if (current && Array.from(select.options).some(option => option.value === current)) select.value = current;
  } catch (error) {
    console.warn("Could not list microphones:", error);
  }
}
async function toggleContextAudio(form){
  if (contextAudio.recorder?.state === "recording") {
    contextAudio.recorder.requestData?.();
    contextAudio.recorder.stop();
    return;
  }
  await startContextAudio(form);
}
async function startContextAudio(form){
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    throw new Error("Microphone recording is not available in this browser.");
  }
  const stream = await navigator.mediaDevices.getUserMedia(contextAudioConstraints(form));
  await refreshContextAudioDevices(form);
  const mimeType = contextAudioMimeType();
  const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
  const track = stream.getAudioTracks()[0];
  contextAudio = { recorder, stream, chunks: [], startedAt: Date.now(), audioContext: null, analyser: null, levelTimer: 0, maxLevel: 0, deviceLabel: track?.label || "microphone" };
  const activeDeviceId = track?.getSettings?.().deviceId || "";
  const deviceSelect = form.querySelector("[data-context-audio-device]");
  if (activeDeviceId && deviceSelect && !deviceSelect.value) deviceSelect.value = activeDeviceId;
  recorder.addEventListener("dataavailable", event => {
    if (event.data?.size) contextAudio.chunks.push(event.data);
  });
  recorder.addEventListener("stop", () => finishContextAudio(form, mimeType));
  recorder.start(250);
  startContextAudioLevelMonitor(form, stream);
  setContextAudioState(form, "recording", `Recording from ${contextAudio.deviceLabel} - input 0%... click the mic again to stop.`);
}
async function finishContextAudio(form, mimeType){
  const maxLevel = contextAudio.maxLevel || 0;
  const deviceLabel = contextAudio.deviceLabel || "microphone";
  stopContextAudioLevelMonitor(form);
  contextAudio.stream?.getTracks().forEach(track => track.stop());
  const seconds = Math.max(0, (Date.now() - contextAudio.startedAt) / 1000);
  const blob = new Blob(contextAudio.chunks, { type: mimeType || "audio/webm" });
  contextAudio = { recorder: null, stream: null, chunks: [], startedAt: 0, audioContext: null, analyser: null, levelTimer: 0, maxLevel: 0, deviceLabel: "" };
  if (!blob.size || seconds < .35) {
    setContextAudioState(form, "ready", "No briefing was recorded.");
    return;
  }
  if (seconds >= 2 && maxLevel < .006) {
    setContextAudioState(form, "error", `Microphone input stayed very low from ${deviceLabel}. Pick another microphone or check Windows input settings.`);
    return;
  }
  await transcribeContextAudio(form, blob, seconds, maxLevel);
}
function startContextAudioLevelMonitor(form, stream){
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return;
  const meter = form.querySelector("[data-context-audio-level]");
  try {
    const audioContext = new AudioContextClass();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 1024;
    const source = audioContext.createMediaStreamSource(stream);
    const data = new Uint8Array(analyser.fftSize);
    source.connect(analyser);
    contextAudio.audioContext = audioContext;
    contextAudio.analyser = analyser;
    const tick = () => {
      analyser.getByteTimeDomainData(data);
      const level = contextAudioInputLevel(data);
      contextAudio.maxLevel = Math.max(contextAudio.maxLevel || 0, level);
      const percent = contextAudioLevelPercent(level);
      if (meter) meter.style.width = `${percent}%`;
      setContextAudioState(form, "recording", `Recording from ${contextAudio.deviceLabel || "microphone"} - input ${percent}%... click the mic again to stop.`);
    };
    contextAudio.levelTimer = window.setInterval(tick, 250);
    tick();
  } catch (error) {
    console.warn("Could not monitor microphone level:", error);
  }
}
function stopContextAudioLevelMonitor(form){
  if (contextAudio.levelTimer) window.clearInterval(contextAudio.levelTimer);
  contextAudio.audioContext?.close?.().catch?.(() => {});
  const meter = form.querySelector("[data-context-audio-level]");
  if (meter) meter.style.width = "0%";
}
function contextAudioInputLevel(data){
  let sum = 0;
  for (const value of data) {
    const centered = (value - 128) / 128;
    sum += centered * centered;
  }
  return Math.sqrt(sum / Math.max(1, data.length));
}
function contextAudioLevelPercent(level){
  return Math.max(0, Math.min(100, Math.round(Number(level || 0) * 420)));
}
async function transcribeContextAudio(form, blob, seconds, maxLevel){
  const sizeKb = Math.max(1, Math.round(blob.size / 1024));
  setContextAudioState(form, "transcribing", `Transcribing ${seconds.toFixed(1)}s / ${sizeKb} KB, peak input ${contextAudioLevelPercent(maxLevel)}%...`);
  try {
    const language = "pt";
    const response = await fetch(`/api/ai-context/audio?language=${encodeURIComponent(language)}`, {
      method: "POST",
      headers: { "Content-Type": blob.type || "audio/webm" },
      body: blob
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.ok) throw new Error(data.error || "Transcription failed.");
    const transcript = String(data.context?.text || "").trim();
    if (isWeakContextTranscript(transcript, seconds)) {
      throw new Error(weakContextTranscriptMessage(transcript, seconds, sizeKb, maxLevel));
    }
    applyContextTranscript(form, transcript);
    setContextAudioState(form, "applied", `Voice briefing applied (${seconds.toFixed(1)}s / ${sizeKb} KB). Review it before importing.`);
  } catch (error) {
    setContextAudioState(form, "error", error.message || "Could not transcribe the briefing.");
  }
}
function isWeakContextTranscript(text, seconds){
  const clean = String(text || "").trim().toLowerCase();
  if (!clean) return true;
  if (seconds < 1.2) return clean.length <= 3;
  return clean.length <= 4 || ["you", "you.", "yeah", "ok", "okay"].includes(clean);
}
function weakContextTranscriptMessage(text, seconds, sizeKb, maxLevel){
  const detected = String(text || "").trim() || "no speech";
  return `Only "${detected}" was detected from ${seconds.toFixed(1)}s / ${sizeKb} KB, peak input ${contextAudioLevelPercent(maxLevel)}%. Pick another microphone or record closer to the input.`;
}
function applyContextTranscript(form, text){
  const textarea = form.querySelector("[name=context_prompt]");
  const transcript = String(text || "").trim();
  if (!textarea || !transcript) return;
  const current = textarea.value.trim();
  textarea.value = current ? `${current}\n\n${transcript}` : transcript;
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
}
function bindImportForm(){
  const form = document.querySelector("[data-import-form]");
  if (!form) return;
  bindSourceMode(form);
  form.addEventListener("submit", event => {
    event.preventDefault();
    startImport(form);
  });
  form.querySelector("[data-select-video-file]")?.addEventListener("click", () => selectPath("/api/select-video-file", "[name=source_path]", "Local video selected."));
  form.querySelector("[data-context-audio]")?.addEventListener("click", () => {
    toggleContextAudio(form).catch(error => setContextAudioState(form, "error", error.message || "Microphone unavailable."));
  });
  document.querySelector("[data-import-loading-back]")?.addEventListener("click", () => hideImportLoading());
}
function bindSourceMode(form){
  const inputs = form.querySelectorAll("[name=source_mode]");
  const sync = () => {
    const mode = String(new FormData(form).get("source_mode") || "local");
    form.dataset.sourceMode = mode;
    form.querySelectorAll("[data-source-panel]").forEach(panel => {
      panel.hidden = panel.dataset.sourcePanel !== mode;
    });
  };
  inputs.forEach(input => input.addEventListener("change", sync));
  sync();
}
async function selectPath(url, selector, message){
  setStatus("Opening local picker...");
  try {
    const data = await postJson(url);
    const input = document.querySelector(selector);
    if (input) input.value = data.path || input.value;
    setStatus(message);
  } catch (error) {
    setStatus(error.message || "Local picker unavailable.");
  }
}
let settingsLastFocus = null;
function setupHomeSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  const form = document.querySelector("[data-settings-form]");
  const open = document.getElementById("open-settings");
  const close = document.querySelector("[data-settings-close]");
  const test = document.querySelector("[data-settings-test]");
  if (!modal || !form || !open) return;
  open.addEventListener("click", () => openSettingsPanel());
  close?.addEventListener("click", () => closeSettingsPanel());
  modal.addEventListener("click", event => { if (event.target === modal) closeSettingsPanel(); });
  document.addEventListener("keydown", event => {
    if (modal.hidden) return;
    if (event.key === "Escape") closeSettingsPanel();
    if (event.key === "Tab") trapSettingsFocus(event);
  });
  form.addEventListener("submit", event => {
    event.preventDefault();
    saveSettingsForm(form);
  });
  test?.addEventListener("click", () => testSettingsConnection(form));
  loadOpenaiSettings();
}
function openSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal) return;
  settingsLastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  modal.hidden = false;
  modal.classList.remove("is-closing");
  requestAnimationFrame(() => modal.classList.add("is-open"));
  loadOpenaiSettings();
  modal.querySelector("[data-settings-panel]")?.focus();
}
function closeSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal || modal.hidden) return;
  modal.classList.remove("is-open");
  modal.classList.add("is-closing");
  window.setTimeout(() => {
    modal.hidden = true;
    modal.classList.remove("is-closing");
    settingsLastFocus?.focus?.();
    settingsLastFocus = null;
  }, 190);
}
function settingsFocusableElements(modal){
  return Array.from(modal.querySelectorAll("button,input,select,textarea,a[href],[tabindex]:not([tabindex='-1'])"))
    .filter(element => !element.disabled && !element.hidden && element.offsetParent !== null);
}
function trapSettingsFocus(event){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal || modal.hidden) return;
  const focusable = settingsFocusableElements(modal);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
async function loadOpenaiSettings(){
  const form = document.querySelector("[data-settings-form]");
  const status = document.querySelector("[data-settings-status]");
  if (!form) return;
  try {
    const response = await fetch("/api/settings/openai");
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Could not load settings.");
    applySettingsPayload(form, payload.settings || {}, payload.usage || {});
  } catch (error) {
    if (status) status.textContent = error.message || "Could not load settings.";
  }
}
function applySettingsPayload(form, settings, usage){
  form.elements.ai_provider.value = settings.ai_provider || "local";
  form.elements.openai_model.value = settings.openai_model || "gpt-5-mini";
  form.elements.transcribe_model.value = settings.transcribe_model || "whisper-1";
  form.elements.api_key.value = "";
  importOpenaiState = {
    provider: String(settings.ai_provider || "local"),
    keyConfigured: Boolean(settings.key_configured)
  };
  const status = document.querySelector("[data-settings-status]");
  if (status) {
    const key = settings.key_configured ? "Token configured" : "Token not configured";
    status.textContent = `${key} - ${settings.openai_model || "gpt-5-mini"} / ${settings.transcribe_model || "whisper-1"}`;
  }
  renderSettingsUsage(usage);
  refreshImportKeyBannerFromState();
}
function settingsPayloadFromForm(form){
  const data = new FormData(form);
  const payload = {
    ai_provider: String(data.get("ai_provider") || "local"),
    openai_model: String(data.get("openai_model") || "gpt-5-mini"),
    transcribe_model: String(data.get("transcribe_model") || "whisper-1")
  };
  const apiKey = String(data.get("api_key") || "").trim();
  if (apiKey) payload.api_key = apiKey;
  return payload;
}
async function saveSettingsForm(form){
  const status = document.querySelector("[data-settings-status]");
  if (status) status.textContent = "Saving...";
  try {
    const response = await fetch("/api/settings/openai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settingsPayloadFromForm(form))
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Could not save settings.");
    applySettingsPayload(form, payload.settings || {}, payload.usage || {});
    if (status) status.textContent = `Saved. ${status.textContent}`;
  } catch (error) {
    if (status) status.textContent = error.message || "Could not save.";
  }
}
async function testSettingsConnection(form){
  const status = document.querySelector("[data-settings-status]");
  const button = document.querySelector("[data-settings-test]");
  if (status) status.textContent = "Testing connection...";
  if (button) button.disabled = true;
  try {
    const response = await fetch("/api/settings/openai/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settingsPayloadFromForm(form))
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "Could not test connection.");
    if (status) status.textContent = data.message || "OpenAI connection validated.";
  } catch (error) {
    if (status) status.textContent = error.message || "Could not validate the connection.";
  } finally {
    if (button) button.disabled = false;
  }
}
function renderSettingsUsage(usage){
  const target = document.querySelector("[data-settings-usage]");
  if (!target) return;
  const total = Number(usage?.estimated_total_usd || 0);
  const count = Number(usage?.event_count || 0);
  const last = usage?.last_event || {};
  const lastText = last.operation
    ? `Last: ${escapeHtml(last.operation)} on ${escapeHtml(last.model || "-")} - ${formatUsd(last.estimated_usd || 0)}`
    : "Last: no record.";
  target.innerHTML = `<strong>Estimated local total: ${formatUsd(total)}</strong><span>${count} event(s) recorded.</span><span>${lastText}</span>`;
}
function formatUsd(value){
  return `$${Number(value || 0).toFixed(4)}`;
}
async function refreshImportKeyBanner(){
  const banner = document.querySelector("[data-import-key-banner]");
  if (!banner) return;
  try {
    const response = await fetch("/api/settings/openai");
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Could not load settings.");
    const settings = payload.settings || {};
    importOpenaiState = {
      provider: String(settings.ai_provider || "local"),
      keyConfigured: Boolean(settings.key_configured)
    };
  } catch (error) {
    console.warn("Could not check the OpenAI key:", error);
    importOpenaiState = { provider: "local", keyConfigured: true };
  }
  refreshImportKeyBannerFromState();
}
function refreshImportKeyBannerFromState(){
  const banner = document.querySelector("[data-import-key-banner]");
  if (banner) banner.hidden = !importNeedsOpenaiKey();
}
function setupImportKeyBanner(){
  const banner = document.querySelector("[data-import-key-banner]");
  if (!banner) return;
  banner.querySelector("[data-import-key-open]")?.addEventListener("click", () => openSettingsPanel());
  refreshImportKeyBanner();
}
function projectCard(project){
  const open = project.url ? `<a href="${escapeAttr(project.url)}">Open</a>` : `<button type="button" disabled>Open</button>`;
  const size = sizeLabel(project.size_bytes || 0);
  return `<article class="project-row" data-project-id="${escapeAttr(project.id)}" data-project-title="${escapeAttr(project.title || "Untitled project")}" data-project-path="${escapeAttr(project.path || "")}" data-project-size="${escapeAttr(size)}">
    <div class="project-name-cell"><strong>${escapeHtml(project.title || "Untitled project")}</strong><p>${escapeHtml(project.source_label || "")}</p><small>${escapeHtml(project.path || "")}</small></div>
    <dl class="project-meta-cell"><div><dt>Clips</dt><dd>${Number(project.clip_count || 0)}</dd></div><div><dt>Renders</dt><dd>${Number(project.render_count || 0)}</dd></div><div><dt>Size</dt><dd>${escapeHtml(size)}</dd></div></dl>
    <time class="project-updated-cell">${escapeHtml(project.last_opened_at || "")}</time>
    <div class="project-row-actions">${open}<button type="button" data-forget-project>Remove recent</button><button type="button" data-delete-project>Delete project</button></div>
  </article>`;
}
function emptyProjectState(){
  return `<article class="project-empty-state" data-project-empty-state><strong>No recent projects</strong><p>Create a new project to start.</p></article>`;
}
function sizeLabel(bytes){
  let value = Number(bytes || 0);
  for (const unit of ["B", "KB", "MB", "GB"]) {
    if (value < 1024 || unit === "GB") return unit === "B" ? `${Math.round(value)} B` : `${value.toFixed(1)} ${unit}`;
    value /= 1024;
  }
  return "0 MB";
}
async function refreshProjects(){
  if (!projectList) return;
  const response = await fetch("/api/projects");
  const data = await response.json();
  if (!response.ok || !data.ok) throw new Error(data.error || "Could not load projects.");
  const projects = Array.isArray(data.projects) ? data.projects : [];
  const content = projects.length ? projects.map(projectCard).join("") : emptyProjectState();
  projectList.innerHTML = `<div class="project-table-head" aria-hidden="true"><span>Project</span><span>Status</span><span>Updated</span><span>Actions</span></div>${content}`;
}
async function deleteProject(card, deleteFiles){
  const projectId = card?.dataset.projectId || "";
  const title = card?.dataset.projectTitle || "Untitled project";
  const path = card?.dataset.projectPath || "";
  const size = card?.dataset.projectSize || "unknown size";
  const message = projectDeleteMessage(title, path, size, deleteFiles);
  if (!projectId || !window.confirm(message)) return;
  const result = await postJson(`/api/projects/${encodeURIComponent(projectId)}/delete`, { delete_files: deleteFiles });
  await refreshProjects();
  if (deleteFiles) {
    const method = result.delete_method === "recycle-bin" ? "Project moved to the Recycle Bin." : "Project deleted locally.";
    setStatus(method);
  } else {
    setStatus("Project removed from recents. Files remain on disk.");
  }
}
function projectDeleteMessage(title, path, size, deleteFiles){
  if (!deleteFiles) {
    return `Remove "${title}" from recents?\n\nFiles remain on disk:\n${path}`;
  }
  return [
    `Delete project "${title}"?`,
    "",
    `Approximate size: ${size}`,
    `Folder: ${path}`,
    "",
    "The project folder will be moved to the Recycle Bin when available.",
    "If the Recycle Bin is unavailable, local files will be removed.",
    "Final renders outside the project folder are not deleted by this action."
  ].join("\n");
}
document.querySelectorAll("[data-new-project]").forEach(button => {
  button.addEventListener("click", () => {
    if (projectLibrary) projectLibrary.hidden = true;
    if (homeImport) homeImport.hidden = false;
    document.querySelector("[data-import-form]")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});
document.querySelector("[data-show-projects]")?.addEventListener("click", () => {
  if (homeImport) homeImport.hidden = true;
  if (projectLibrary) projectLibrary.hidden = false;
});
document.querySelectorAll("[data-open-workspace]").forEach(button => {
  button.addEventListener("click", () => postJson("/api/open-folder", { path: workspacePath }).catch(error => setStatus(error.message || "Could not open the folder.")));
});
document.querySelector("[data-refresh-projects]")?.addEventListener("click", () => refreshProjects().catch(error => setStatus(error.message || "Could not refresh projects.")));
projectList?.addEventListener("click", event => {
  const card = event.target.closest("[data-project-id]");
  if (event.target.closest("[data-forget-project]")) deleteProject(card, false);
  if (event.target.closest("[data-delete-project]")) deleteProject(card, true);
});
setupHomeSettingsPanel();
setupImportKeyBanner();
bindImportForm();
setupImportRecovery();
"""
    return script.replace("__WORKSPACE_PATH__", json.dumps(str(workspace)))


def css() -> str:
    return base_css() + liquid_ui_css()


def base_css() -> str:
    return """
*{box-sizing:border-box}:root{--color-brand-blue:#11A2CF;--color-brand-green:#AFCF2A;--color-brand-white:#E7E7E8;--color-brand-black:#050505;--color-metal-gray:#68686A;--color-surface:#0D0D0D;--color-surface-raised:#111;--color-surface-muted:#151515;--color-surface-control:#191919;--color-border:#272727;--color-border-strong:#333;--color-text:#f4f4f4;--color-text-soft:#ddd;--color-text-muted:#9a9a9a;--color-focus:#11A2CF;--color-danger:#ffb3b3;--shadow-panel:0 14px 42px rgba(0,0,0,.5)}body{margin:0;background:var(--color-brand-black);color:var(--color-text);font:14px/1.45 Arial,sans-serif}
header{position:sticky;top:0;z-index:5;display:grid;grid-template-columns:minmax(90px,1fr) auto minmax(90px,1fr);gap:16px;align-items:center;padding:10px 22px 12px;background:var(--color-brand-black);border-bottom:1px solid var(--color-border)}.header-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.icon-button{display:inline-grid;place-items:center;width:38px;min-width:38px;padding:0}.icon-button svg{display:block;width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.brand-lockup{display:grid;justify-items:center;gap:8px;min-width:0}.brand-logo{display:block;width:min(540px,54vw);height:78px;object-fit:contain;object-position:center;border:0;border-radius:0;filter:none}.brand-lockup p{margin:2px 0 0;color:var(--color-text-muted);font-size:11px;line-height:1.1;text-align:center;max-width:min(520px,56vw);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.tabs{position:sticky;top:119px;z-index:4;display:flex;gap:8px;padding:10px 22px;background:#060606;border-bottom:1px solid #1f1f1f}.tabs button{background:var(--color-surface-control);color:var(--color-text-soft);border:1px solid #303030;padding:8px 12px}.tabs button.active{background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white)}
main{display:grid;gap:12px;max-width:1440px;margin:0 auto;padding:16px 18px 28px}.card{border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface);overflow:hidden}.card[open]{border-color:var(--color-metal-gray);background:var(--color-surface-raised)}.card.liked{border-color:var(--color-brand-green)}.card.discarded{opacity:.46}.clip-summary{display:grid;grid-template-columns:auto minmax(0,1fr) minmax(180px,.55fr) auto;gap:12px;align-items:center;min-height:62px;padding:12px 14px;cursor:pointer;list-style:none}.clip-summary::-webkit-details-marker{display:none}.clip-rank{color:var(--color-metal-gray);font-weight:700}.clip-title{display:grid;gap:2px;min-width:0}.clip-title strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:15px}.clip-title small{color:var(--color-text-muted)}.clip-row-timeline{position:relative;display:block;min-width:160px;height:30px;border:1px solid rgba(17,162,207,.22);border-radius:4px;background:linear-gradient(180deg,rgba(17,162,207,.08),rgba(255,255,255,.02)),rgba(5,5,5,.28);overflow:hidden}.clip-row-timeline-track{position:absolute;left:8px;right:8px;top:50%;height:3px;border-radius:999px;background:rgba(231,231,232,.12);transform:translateY(-50%)}.clip-row-timeline-window{position:absolute;top:7px;bottom:7px;border:1px solid rgba(175,207,42,.5);border-radius:3px;background:rgba(175,207,42,.08)}.clip-row-timeline-marker{position:absolute;top:6px;width:7px;height:18px;border:1px solid rgba(17,162,207,.8);border-radius:3px;background:rgba(17,162,207,.22);transform:translateX(-50%)}.clip-row-timeline-playhead{position:absolute;top:5px;width:2px;height:20px;border-radius:999px;background:var(--color-brand-white);transform:translateX(-50%);opacity:.72}.clip-status{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.clip-status span,.format-previews span{display:inline-flex;align-items:center;min-height:26px;padding:4px 8px;border-radius:999px;background:#242424;color:var(--color-text-soft);font-size:12px}
.app-notice{position:sticky;top:0;z-index:30;margin:0;padding:10px 14px;background:#2b1717;color:#ffd7d7;border-bottom:1px solid #6d2b2b;font-size:13px;text-align:center}.app-notice[hidden]{display:none}
.import-stage{display:none;max-width:1080px;margin:18px auto;padding:0 18px}.import-panel{display:grid;gap:14px;padding:18px;border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface-raised)}.import-panel p{margin:4px 0 0;color:var(--color-text-muted)}.import-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.import-panel label{display:grid;gap:6px;color:var(--color-text-muted);font-size:12px}.import-panel input,.import-panel select,.import-panel textarea{width:100%;border:1px solid var(--color-border-strong);border-radius:6px;background:var(--color-brand-black);color:var(--color-text);padding:9px 10px;font:inherit}.import-panel textarea{resize:vertical;min-height:112px}.import-panel small{color:var(--color-text-muted);line-height:1.35}.import-path-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px}.import-key-banner{display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;padding:10px 12px;border:1px solid rgba(17,162,207,.4);border-radius:8px;background:rgba(17,162,207,.1);color:var(--color-text)}.import-key-banner[hidden]{display:none}.import-key-banner button{min-height:34px}.import-path-row button{min-height:38px;background:var(--color-surface-control);color:var(--color-text-soft);border:1px solid var(--color-border-strong)}.duration-profile{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:0;padding:0;border:0}.duration-profile legend{grid-column:1/-1;color:var(--color-text-muted);font-size:12px}.duration-profile label{position:relative;display:grid!important}.duration-profile input{position:absolute;opacity:0;pointer-events:none}.duration-profile span{display:grid;gap:2px;min-height:54px;padding:10px 12px;border:1px solid var(--color-border-strong);border-radius:8px;background:var(--color-surface-muted);color:var(--color-text-soft)}.duration-profile input:checked+span{border-color:var(--color-brand-green);background:#182011;color:var(--color-text)}.duration-profile small{color:var(--color-text-muted)}.import-context{display:grid}.import-status{min-height:20px;color:var(--color-text-muted)}.import-result{display:flex;gap:8px;flex-wrap:wrap}.import-result a{display:inline-flex;align-items:center;justify-content:center;min-height:38px;padding:9px 12px;border-radius:6px;background:var(--color-brand-white);color:var(--color-brand-black);text-decoration:none}.import-result code{display:block;width:100%;padding:10px;border:1px solid #3a2525;border-radius:6px;background:#180d0d;color:#ffcccc;white-space:pre-wrap}
.layer-strip{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;width:100%;min-height:0}.layer-strip:empty{display:none}.bumper-sequence{display:flex;gap:6px;align-items:center;justify-content:center;flex-wrap:wrap;min-height:24px;color:var(--color-text-muted);font-size:12px}.bumper-sequence:empty{display:none}.bumper-sequence span{max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bumper-sequence b{color:var(--color-brand-green);font-weight:800}.layer-chip{display:inline-flex;gap:6px;align-items:center;max-width:100%;min-height:30px;padding:4px 5px 4px 9px;border:1px solid #303030;border-radius:999px;background:var(--color-surface-muted);color:var(--color-text-soft);font-size:12px}.layer-chip.is-selected{border-color:var(--color-focus);background:#182011;color:var(--color-text)}.layer-chip span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.layer-chip button{display:inline-grid;place-items:center;width:22px;height:22px;min-width:22px;padding:0;border:1px solid #3a3a3a;border-radius:999px;background:#242424;color:var(--color-text-soft);font-size:14px;line-height:1}
.cuted-control-surface-slot{display:none;position:relative;z-index:90;margin:-34px 14px 8px;justify-content:center}.cuted-control-surface-slot:empty{display:none}.card[open]>.cuted-control-surface-slot:not(:empty){display:flex}.cuted-control-surface-slot .cuted-control-bar{width:min(66%,930px);min-width:min(100%,820px);min-height:98px;padding:9px 16px;border-radius:18px}.cuted-control-surface-slot .cuted-render-zone{justify-content:flex-end;overflow:visible;min-height:74px}.cuted-control-surface-slot .cuted-tool-group{flex:0 0 408px;min-height:74px}.cuted-control-surface-slot .cuted-tile-button{flex:0 0 68px;width:68px;height:62px;font-size:30px}.cuted-control-surface-slot .cuted-insert-button span{font-size:20px}.cuted-control-surface-slot .cuted-format-trigger{flex:0 0 118px;width:118px;height:62px;grid-template-columns:auto 1fr auto;gap:8px;padding:7px 9px}.cuted-control-surface-slot .cuted-format-copy small{display:none}.cuted-control-surface-slot .cuted-format-copy strong{font-size:20px}.cuted-control-surface-slot .cuted-ratio-icon{border-width:2px;border-radius:3px}.cuted-control-surface-slot .cuted-ratio-vertical{width:16px;height:34px}.cuted-control-surface-slot .cuted-ratio-feed{width:22px;height:28px}.cuted-control-surface-slot .cuted-ratio-wide{width:32px;height:17px}.cuted-control-surface-slot .cuted-divider{flex:0 0 1px;height:48px;margin:0 8px}.cuted-control-surface-slot .cuted-audio-group{flex:0 0 58px;min-width:58px}.cuted-control-surface-slot .cuted-ready-region{flex:0 0 132px;width:132px;min-height:62px;margin-left:auto}.cuted-control-surface-slot .cuted-approve-button{width:60px;height:60px}.cuted-control-surface-slot .cuted-approve-button svg{width:36px;height:36px}.cuted-control-surface-slot .cuted-discard-button{width:46px;height:46px}.cuted-control-surface-slot .cuted-discard-button svg{width:25px;height:25px}
.editor-shell{display:grid;grid-template-columns:minmax(280px,520px) minmax(360px,1fr);gap:14px;padding:0 14px 14px}.editor-preview{display:grid;align-content:start;justify-items:center;gap:10px}.preview-frame{display:grid;gap:10px;width:100%;max-width:520px}.media{position:relative;container-type:inline-size;aspect-ratio:16/9;background:#000;max-height:72vh;overflow:hidden;border-radius:6px}.media video,.media img{width:100%;height:100%;object-fit:cover;display:block;background:#000;pointer-events:none}.placeholder{display:grid;place-items:center;height:100%;color:#777}.preview-bar{display:grid;grid-template-columns:1fr;gap:8px;justify-items:center;width:100%;padding:8px;border:1px solid #252525;border-radius:8px;background:#0a0a0a}.preview-controls,.preview-volume-group{display:flex;gap:6px;align-items:center}.preview-controls{justify-content:center;padding:4px;border:1px solid #202020;border-radius:999px;background:var(--color-surface-raised)}.preview-volume-group{padding-left:4px;border-left:1px solid #2d2d2d}.preview-icon,.preview-step{display:inline-grid;place-items:center;width:32px;height:32px;min-width:32px;padding:0;border:1px solid var(--color-border-strong);border-radius:999px;background:var(--color-surface-control);color:var(--color-text-soft)}.preview-play{background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white)}.preview-icon svg{width:16px;height:16px;display:block;stroke:currentColor}.preview-step{width:26px;height:26px;min-width:26px;font-weight:700}.preview-volume-group output{min-width:32px;color:#d8d8d8;font-size:12px;text-align:center}.card[data-preview-format=tiktok] .preview-frame,.card[data-preview-format=shorts] .preview-frame,.card[data-preview-format=instagram] .preview-frame{max-width:min(100%,calc(72vh * 9 / 16))}.card[data-preview-format=facebook] .preview-frame{max-width:min(100%,calc(72vh * 4 / 5))}.card[data-preview-format=youtube] .preview-frame{max-width:min(100%,520px)}.card[data-preview-format=tiktok] .media,.card[data-preview-format=shorts] .media,.card[data-preview-format=instagram] .media{aspect-ratio:9/16}.card[data-preview-format=facebook] .media{aspect-ratio:4/5}.card[data-preview-format=youtube] .media{aspect-ratio:16/9}.preview-strip{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;overflow:visible;padding-bottom:1px}.preview-strip button{background:var(--color-surface-control);color:var(--color-text-soft);border:1px solid #303030;padding:8px 10px;min-height:34px;border-radius:999px;white-space:nowrap}.preview-strip button.active{background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white)}
.preview-camera-timeline--live{position:relative;display:block!important;width:100%;min-height:152px;padding:0!important;border-color:rgba(17,162,207,.34)!important;overflow:hidden}.preview-camera-timeline--live .timeline-shell{min-height:150px;border:0;border-radius:4px;background:linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px) 0 0/28px 100%,linear-gradient(180deg,rgba(17,162,207,.08),transparent 34%),#070707}.preview-camera-timeline--live .volume-popover[data-disabled=true]{display:none!important}.preview-live-timeline-loading{display:grid;place-items:center;min-height:86px;color:var(--color-text-muted);font-size:12px}.overlay-timeline{position:absolute;left:76px;right:76px;bottom:44px;z-index:18;height:34px;pointer-events:none}.overlay-timeline[hidden]{display:none}.overlay-timeline-item{position:absolute;left:var(--overlay-time-left);top:0;display:grid;place-items:center;width:clamp(16px,var(--overlay-time-width),24px);height:26px;min-width:16px;min-height:26px;padding:0;border:2px solid rgba(175,207,42,.86);border-radius:7px;background:linear-gradient(180deg,rgba(175,207,42,.16),rgba(5,5,5,.9));color:transparent;box-shadow:0 0 0 2px rgba(175,207,42,.12),0 0 18px rgba(175,207,42,.22);font-size:0;line-height:1;cursor:grab;overflow:visible;pointer-events:auto;transform:translateY(0);transition:border-color .14s ease,box-shadow .14s ease,background .14s ease}.overlay-timeline-item:before{content:"";position:absolute;left:50%;top:-9px;width:5px;height:5px;border-radius:999px;background:var(--color-brand-green);box-shadow:0 0 10px rgba(175,207,42,.7);transform:translateX(-50%)}.overlay-timeline-item:after{content:"";position:absolute;inset:5px 4px;border:1px solid rgba(175,207,42,.38);border-radius:3px;background:rgba(0,0,0,.42)}.overlay-timeline-item span{position:absolute;inset:0;overflow:hidden;opacity:0;pointer-events:none}.overlay-timeline-item i{position:absolute;right:-3px;top:4px;bottom:4px;z-index:2;display:block;width:7px;border:0;border-radius:999px;background:rgba(231,231,232,.2);cursor:ew-resize}.overlay-timeline-item[data-overlay-kind=speech]{border-color:rgba(231,231,232,.88);background:linear-gradient(180deg,rgba(175,207,42,.28),rgba(5,5,5,.9));box-shadow:0 0 0 2px rgba(231,231,232,.08),0 0 20px rgba(175,207,42,.28)}.overlay-timeline-item[data-overlay-kind=image]{border-style:dashed}.overlay-timeline-item.is-active,.overlay-timeline-item.is-selected{border-color:rgba(231,231,232,.98);box-shadow:0 0 0 3px rgba(175,207,42,.18),0 0 24px rgba(175,207,42,.36)}
.editor-tools{display:grid;align-content:start;gap:12px}.tool-stack{display:grid;gap:10px}.tool-section{border:1px solid #242424;border-radius:8px;background:#0a0a0a;padding:0;overflow:hidden}.tool-section>summary{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:44px;padding:10px 12px;cursor:pointer;list-style:none;color:var(--color-text);font-weight:800}.tool-section>summary::-webkit-details-marker{display:none}.tool-section>summary:after{content:"";width:8px;height:8px;border-right:1px solid currentColor;border-bottom:1px solid currentColor;transform:rotate(45deg);opacity:.62;transition:transform .16s ease}.tool-section[open]>summary:after{transform:rotate(225deg)}.tool-section>summary small{color:var(--color-text-muted);font-size:12px;font-weight:600;text-align:right}.tool-section[open]>summary{border-bottom:1px solid rgba(231,231,232,.08)}.tool-section>*:not(summary){margin:12px}.timeline-editor{padding:0}.timeline-head,.timeline-timebar,.timeline-values{display:flex;justify-content:space-between;gap:12px;color:var(--color-text-muted);font-size:12px}.timeline-head output,.timeline-timebar output{color:var(--color-text);text-align:right}.timeline-timebar{margin-top:10px}.timeline-timebar span:last-child{color:#777;text-align:right}.timeline-scrub{position:relative;height:42px;margin-top:8px}.timeline-scrub-track{position:absolute;left:0;right:0;top:17px;height:8px;border:1px solid #343434;border-radius:999px;background:linear-gradient(90deg,var(--color-surface-muted),#252525);overflow:hidden}.timeline-selected{position:absolute;top:0;bottom:0;background:rgba(175,207,42,.22);border-left:1px solid var(--color-brand-green);border-right:1px solid var(--color-brand-green)}.timeline-playhead{position:absolute;top:-8px;bottom:-8px;width:2px;background:var(--color-brand-white);box-shadow:0 0 0 1px rgba(0,0,0,.7)}.timeline-playhead:before{content:"";position:absolute;left:50%;top:-4px;width:10px;height:10px;border-radius:50%;background:var(--color-brand-white);transform:translateX(-50%)}.timeline-scrub input{position:absolute;inset:0;width:100%;height:42px;margin:0;background:transparent;opacity:0;cursor:pointer}.timeline{position:relative;height:38px;margin-top:6px}.timeline-track{position:absolute;left:0;right:0;top:16px;height:6px;background:#292929;border-radius:999px;overflow:hidden}.timeline-fill{position:absolute;top:0;bottom:0;background:var(--color-brand-white);border-radius:999px}.timeline input{position:absolute;inset:0;width:100%;height:38px;margin:0;background:transparent;pointer-events:none;-webkit-appearance:none;appearance:none}.timeline input::-webkit-slider-thumb{width:18px;height:18px;border-radius:50%;background:var(--color-brand-white);border:2px solid var(--color-brand-black);pointer-events:auto;-webkit-appearance:none;appearance:none}.timeline input::-webkit-slider-runnable-track{background:transparent}.timeline input::-moz-range-thumb{width:18px;height:18px;border-radius:50%;background:var(--color-brand-white);border:2px solid var(--color-brand-black);pointer-events:auto}.timeline input::-moz-range-track{background:transparent}.timeline-values{margin-top:6px}.actions,.platform-tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.export-dock{display:grid;gap:8px;margin-top:2px;padding:12px;border:1px solid #303030;border-radius:8px;background:#111}.export-dock strong{display:block;font-size:13px}.export-dock span{color:#a8a8a8;font-size:12px}
.platform-tags button,.camera-card-buttons button,.effect-card-buttons button,.overlay-card-buttons button{background:var(--color-surface-control);color:var(--color-text-soft);border:1px solid var(--color-border-strong);text-align:left}.platform-tags button.active,.camera-card-buttons button.active,.effect-card-buttons button.active,.overlay-card-buttons button.active{background:#102018;color:var(--color-text);border-color:var(--color-brand-green)}.camera-card-controls,.effect-card-controls,.overlay-card-controls{display:grid;gap:10px}.effect-split{display:grid;grid-template-columns:minmax(0,1fr) minmax(220px,.75fr);gap:10px}.effect-subpanel{display:grid;gap:10px;padding:10px;border:1px solid #2a2a2a;border-radius:8px;background:#101010}.effect-subpanel strong{font-size:12px}.bumper-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.bumper-upload{display:grid;gap:6px;align-content:start;min-height:64px;padding:9px;border:1px dashed var(--color-border-strong);border-radius:8px;background:var(--color-surface-control);cursor:pointer}.bumper-upload input{font-size:11px}.bumper-strip{display:flex;gap:6px;flex-wrap:wrap;min-height:28px}.bumper-empty{color:var(--color-text-muted);font-size:12px}.camera-card-buttons,.effect-card-buttons,.overlay-card-buttons{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.camera-card-controls label,.effect-card-controls label,.overlay-card-controls label,.caption-settings label{display:grid;gap:6px;color:var(--color-text-muted);font-size:12px}.camera-card-controls input,.effect-card-controls input,.overlay-card-controls input{width:100%;accent-color:var(--color-brand-blue)}.camera-card-controls select,.caption-settings select,.caption-settings input{width:100%;background:var(--color-brand-black);color:var(--color-text);border:1px solid var(--color-border-strong);border-radius:6px;padding:8px}.camera-path-editor,.camera-manual-panel{display:grid;gap:10px;padding:10px;border:1px solid #2a2a2a;border-radius:8px;background:#101010}.camera-path-head,.camera-panel-title{display:flex;justify-content:space-between;gap:10px;align-items:center}.camera-path-head strong,.camera-panel-title strong{font-size:12px}.camera-path-head span,.camera-panel-title span{color:var(--color-text-muted);font-size:12px}.camera-smart-panel{display:grid;gap:9px;padding:10px;border:1px solid rgba(17,162,207,.28);border-radius:8px;background:linear-gradient(135deg,rgba(17,162,207,.12),rgba(175,207,42,.06))}.camera-smart-row,.camera-smart-ai{display:grid;gap:8px}.camera-smart-row{grid-template-columns:repeat(3,minmax(0,1fr))}.camera-smart-ai{grid-template-columns:repeat(5,minmax(0,1fr))}.camera-smart-panel button{display:grid;gap:3px;justify-items:center;background:rgba(17,162,207,.1);color:var(--color-text);border:1px solid rgba(17,162,207,.34);text-align:center}.camera-smart-panel button:hover{border-color:var(--color-brand-blue);box-shadow:0 0 0 3px rgba(17,162,207,.14)}.camera-path-track{position:relative;height:34px}.camera-path-rail{position:absolute;left:0;right:0;top:15px;height:5px;border-radius:999px;background:#292929}.camera-path-marker{position:absolute;top:7px;width:20px;height:20px;min-width:20px;padding:0;border-radius:999px;transform:translateX(-50%);background:var(--color-surface-control);border:1px solid var(--color-border-strong)}.camera-path-marker.active{background:var(--color-brand-blue);border-color:var(--color-brand-blue);box-shadow:0 0 0 4px rgba(17,162,207,.18)}.camera-path-actions{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.camera-keyframe-panel{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;align-items:end}.camera-auto-status{min-height:18px;color:var(--color-text-muted);font-size:12px}.camera-path-delete{color:var(--color-danger)!important}.camera-segments{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.camera-segment{display:grid;gap:8px;padding:10px;border:1px solid #2a2a2a;border-radius:8px;background:#101010}.camera-segment strong{font-size:12px}.caption-settings{display:grid;grid-template-columns:minmax(160px,1fr) 120px 150px;gap:12px;max-width:none}.caption-toggle{align-content:center}.caption-toggle input{justify-self:start;width:auto;min-height:20px;accent-color:var(--color-brand-blue)}
.camera-smart-panel p{margin:0;color:var(--color-text-muted);font-size:12px}.camera-smart-panel button span{color:var(--color-text-muted);font-size:11px}.camera-director-action{min-height:72px;background:linear-gradient(135deg,rgba(17,162,207,.32),rgba(231,231,232,.08))!important;border-color:rgba(17,162,207,.72)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.16),0 16px 34px rgba(17,162,207,.1)}.camera-director-action strong{font-size:15px}.camera-smart-row button{min-height:54px}.camera-smart-ai button{min-height:50px}.camera-advanced{display:grid;gap:10px;padding:10px;border:1px solid rgba(231,231,232,.08);border-radius:8px;background:rgba(255,255,255,.025)}.camera-advanced summary{display:flex;justify-content:space-between;gap:10px;align-items:center;cursor:pointer;color:var(--color-text-soft)}.camera-advanced summary small{color:var(--color-text-muted);font-size:12px}.camera-advanced[open] summary{padding-bottom:8px;border-bottom:1px solid rgba(231,231,232,.08)}.camera-advanced .camera-manual-panel{padding:0;border:0;background:transparent}.camera-surface video{position:relative;z-index:1;object-position:var(--camera-x,50%) 50%;transform:scale(var(--camera-scale,1));transform-origin:var(--camera-x,50%) 50%;transition:object-position var(--camera-transition-ms,700ms) cubic-bezier(.22,.61,.36,1),transform var(--camera-transition-ms,700ms) cubic-bezier(.22,.61,.36,1)}.camera-surface[data-camera-cut=hard] video:not(.camera-fit-bg){transition:none}.camera-surface .camera-fit-bg{position:absolute!important;inset:-7%;z-index:0!important;width:114%!important;height:114%!important;display:none!important;object-fit:cover!important;object-position:center!important;transform:none!important;filter:blur(22px) saturate(.88) brightness(.62)!important;pointer-events:none}.camera-surface .camera-fit-logo{position:absolute;top:11%;left:50%;z-index:1;width:38%!important;max-width:240px;height:auto!important;display:none!important;object-fit:contain!important;object-position:center;background:transparent!important;transform:translateX(-50%);opacity:.9;pointer-events:none}.camera-surface[data-camera-fit=contain]{background:#050505}.camera-surface[data-camera-fit=contain] .camera-fit-bg{display:block!important}.camera-surface[data-camera-fit=contain] .camera-fit-logo{display:block!important}.camera-surface[data-camera-fit=contain] video:not(.camera-fit-bg){z-index:2;object-fit:contain;transform:none;transform-origin:center;background:transparent}.camera-reticle{position:absolute;inset:14% 22%;z-index:3;border:1px solid rgba(36,209,126,.58);border-radius:8px;box-shadow:0 0 0 999px rgba(0,0,0,.1);pointer-events:none}.preview-caption-layer{position:absolute;left:7.4%;right:7.4%;bottom:16.25%;z-index:4;display:grid;justify-items:center;pointer-events:none;opacity:0;transform:translateY(8px);transition:opacity 120ms ease,transform 120ms ease}.preview-caption-layer[data-visible=true]{opacity:1;transform:translateY(0)}.preview-caption-layer span{display:block;max-width:100%;color:#fff;font-family:Arial,sans-serif;font-size:clamp(18px,6.67cqw,36px);font-weight:900;line-height:1.08;text-align:center;text-shadow:0 2px 0 #000,0 -2px 0 #000,2px 0 0 #000,-2px 0 0 #000,0 0 12px rgba(0,0,0,.9),0 8px 22px rgba(0,0,0,.66);-webkit-text-stroke:clamp(1.2px,.44cqw,2.4px) rgba(0,0,0,.88);paint-order:stroke fill;text-transform:none;white-space:normal}.card[data-preview-format=facebook] .preview-caption-layer{bottom:8.8%}.card[data-preview-format=facebook] .preview-caption-layer span{font-size:clamp(18px,5cqw,34px);-webkit-text-stroke:clamp(1.1px,.38cqw,2px) rgba(0,0,0,.88)}.card[data-preview-format=youtube] .preview-caption-layer{bottom:11%}.card[data-preview-format=youtube] .preview-caption-layer span{font-size:clamp(18px,2.82cqw,32px);-webkit-text-stroke:clamp(1px,.26cqw,1.8px) rgba(0,0,0,.88)}
.card[data-effect=light-grain] .media video,.card[data-effect=light-grain] .media img{filter:contrast(1.08) brightness(1.02)}.card[data-effect=old-film] .media video,.card[data-effect=old-film] .media img{filter:sepia(.48) contrast(1.2) saturate(.62) brightness(.92)}.card[data-effect=vhs] .media video,.card[data-effect=vhs] .media img{filter:saturate(.62) contrast(1.22) brightness(.9) hue-rotate(-7deg)}.card[data-effect=bw-old] .media video,.card[data-effect=bw-old] .media img{filter:grayscale(1) contrast(1.22) brightness(.9)}.card[data-effect=light-grain] .media:after,.card[data-effect=old-film] .media:after,.card[data-effect=vhs] .media:after,.card[data-effect=bw-old] .media:after{content:"";position:absolute;inset:0;pointer-events:none;opacity:var(--effect-opacity,.24);background-image:radial-gradient(circle at 20% 30%,rgba(255,255,255,.95) 0 1px,transparent 1.6px),radial-gradient(circle at 70% 65%,rgba(0,0,0,.95) 0 1px,transparent 1.8px);background-size:4px 4px,6px 6px;mix-blend-mode:overlay}.card[data-effect=old-film] .media:before,.card[data-effect=bw-old] .media:before{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;background:radial-gradient(circle at center,transparent 44%,rgba(0,0,0,.46) 100%)}.card[data-effect=vhs] .media:before{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;background:repeating-linear-gradient(0deg,rgba(255,255,255,.08) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
.camera-surface[data-camera-fit=contain] video:not(.camera-fit-bg){object-position:center}
.preview-caption-layer span{padding:var(--preview-caption-padding,0);border-radius:.16em;background:var(--preview-caption-bg,transparent);color:var(--preview-caption-color,#fff);font-size:var(--preview-caption-size,clamp(18px,6.67cqw,36px));box-decoration-break:clone;-webkit-box-decoration-break:clone}
.overlay-tools{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:end}.overlay-box{position:absolute;z-index:3;left:calc(var(--overlay-x)*100%);top:calc(var(--overlay-y)*100%);width:calc(var(--overlay-width)*100%);min-width:120px;padding:10px 14px 11px 18px;border-left:6px solid var(--overlay-accent,var(--color-brand-green));border-radius:8px;background:rgba(0,0,0,var(--overlay-opacity,.92));box-shadow:0 10px 30px rgba(0,0,0,.35);cursor:move;touch-action:none;user-select:none;pointer-events:auto;opacity:1;transform:translateY(0);transition:opacity 170ms ease,transform 170ms ease,outline-color .14s ease}.overlay-box[data-overlay-visible=false]{opacity:0;transform:translateY(5px);pointer-events:none}.overlay-box[data-overlay-key=none]{display:none}.overlay-box strong{font-size:clamp(13px,4vw,20px);line-height:1.05}.overlay-box em{display:block;margin-top:3px;color:rgba(255,255,255,.75);font-style:normal;font-size:clamp(10px,2.4vw,13px);line-height:1.2}.overlay-text-box{display:grid;align-items:center;min-width:96px;min-height:34px;padding:8px 12px;border-left:0;background:rgba(var(--overlay-bg-rgb,0,0,0),var(--overlay-bg-opacity,.7));box-shadow:none;color:var(--overlay-color,#fff);font-weight:700;font-size:clamp(13px,var(--overlay-font-size,20px),36px);line-height:1.05;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.overlay-text-box[data-overlay-bg=off]{background:transparent;box-shadow:none}.overlay-text-box span{opacity:var(--overlay-opacity,1);overflow:hidden;text-overflow:ellipsis}.overlay-speech-box{display:grid;align-items:center;min-width:112px;min-height:42px;padding:10px 15px;border:0;border-radius:18px;background:rgba(var(--overlay-bg-rgb,255,255,255),var(--overlay-bg-opacity,.94));box-shadow:0 10px 24px rgba(0,0,0,.22);color:var(--overlay-color,#050505);font-weight:900;font-size:clamp(14px,var(--overlay-font-size,22px),30px);line-height:1.08;white-space:normal;overflow:visible}.overlay-speech-box:after{position:absolute;left:18%;bottom:-12px;width:24px;height:20px;border-radius:0 0 22px 0;background:inherit;content:"";transform:skewX(-18deg);box-shadow:8px 9px 16px rgba(0,0,0,.12)}.overlay-speech-box span{position:relative;z-index:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;opacity:var(--overlay-opacity,1);overflow:hidden;text-overflow:ellipsis;overflow-wrap:anywhere}.overlay-box.is-selected{outline:2px solid var(--color-focus);outline-offset:2px}.overlay-image-box{display:grid;place-items:center;min-width:72px;min-height:72px;padding:6px;border:1px dashed rgba(255,255,255,.42);background:rgba(0,0,0,.12);box-shadow:0 8px 24px rgba(0,0,0,.22)}.overlay-image-box img{display:block;width:100%;height:auto;max-height:100%;object-fit:contain;opacity:var(--overlay-opacity,1);pointer-events:none;background:transparent}.overlay-resize{position:absolute;right:3px;bottom:3px;z-index:4;width:22px;height:22px;padding:0;border:1px solid rgba(255,255,255,.52);border-radius:5px;background:rgba(255,255,255,.2);cursor:nwse-resize;touch-action:none;pointer-events:auto}.overlay-menu{position:absolute;z-index:6;display:grid;gap:8px;width:min(360px,94%);max-height:min(420px,calc(100vh - 24px));overflow:auto;padding:8px;border:1px solid var(--color-border-strong);border-radius:8px;background:#101010;box-shadow:var(--shadow-panel);touch-action:none;scrollbar-width:thin;scrollbar-color:rgba(175,207,42,.5) rgba(255,255,255,.06)}.overlay-menu[hidden]{display:none}.overlay-menu-head{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:2px 2px 4px;cursor:move}.overlay-menu-head strong{font-size:13px}.overlay-menu-head button{padding:6px 9px}.overlay-menu-actions{display:grid;grid-template-columns:repeat(2,minmax(120px,1fr));gap:6px}.overlay-menu button{background:#242424;color:var(--color-text-soft);border:1px solid var(--color-border-strong)}.overlay-inspector{display:grid;gap:8px}.overlay-inspector label{display:grid;gap:5px;color:var(--color-text-muted);font-size:12px}.overlay-inspector input[type=text],.overlay-inspector input[type=number]{width:100%;background:var(--color-brand-black);color:var(--color-text);border:1px solid var(--color-border-strong);border-radius:6px;padding:8px}.overlay-inspector input[type=color]{width:42px;height:32px;padding:2px;border:1px solid var(--color-border-strong);border-radius:6px;background:var(--color-brand-black)}.overlay-inspector input[type=range]{width:100%;accent-color:var(--color-brand-green)}.overlay-inspector-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.overlay-inspector-row>*{flex:1 1 96px}.overlay-inspector-check{display:flex!important;grid-template-columns:none!important;align-items:center;gap:8px}.overlay-inspector-check input{width:auto}.overlay-inspector-section{display:grid;gap:8px;padding:8px;border:1px solid rgba(231,231,232,.1);border-radius:8px;background:rgba(231,231,232,.035)}.overlay-inspector-section summary{cursor:pointer;color:var(--color-text-soft);font-size:12px;font-weight:800;list-style:none}.overlay-inspector-section summary::-webkit-details-marker{display:none}.overlay-inspector-section[open] summary{padding-bottom:6px;border-bottom:1px solid rgba(231,231,232,.08)}.overlay-image-source{display:grid;grid-template-columns:44px 1fr;gap:8px;align-items:center}.overlay-image-source img,.overlay-image-source span{display:block;width:44px;height:44px;border:1px solid rgba(231,231,232,.14);border-radius:6px;background:#050505;object-fit:contain}.overlay-inspector-actions{display:flex;gap:8px;flex-wrap:wrap}.overlay-inspector-actions button{flex:1 1 120px}.overlay-danger{color:var(--color-danger)!important;border-color:#5b2626!important;background:#251111!important}.image-upload{padding:10px;border:1px dashed var(--color-border-strong);border-radius:8px;background:#0f0f0f}.overlay-layer-list{display:grid;gap:6px}.overlay-layer-row{display:flex;justify-content:space-between;gap:8px;align-items:center;padding:8px;border:1px solid #242424;border-radius:6px;background:#101010}.overlay-layer-row span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.overlay-layer-row button{padding:6px 9px;background:#242424;color:var(--color-text-soft);border:1px solid var(--color-border-strong)}.overlay-empty{padding:10px;border:1px dashed var(--color-border-strong);border-radius:8px;color:var(--color-text-muted)}
p{color:#bebebe}.peak{color:#fff;font-size:16px;line-height:1.35}dl{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;color:#aaa}dt{color:#707070}dd{margin:0}.transcript-copy{max-height:220px;overflow:auto;margin-top:10px;padding:10px;border:1px solid rgba(231,231,232,.08);border-radius:8px;background:rgba(0,0,0,.18)}.transcript-copy p{margin:0;line-height:1.45}
body[data-tab=import] main,body[data-tab=import] .final-stage{display:none}body[data-tab=import] .import-stage{display:block}body[data-tab=final] main,body[data-tab=final] .import-stage{display:none}body[data-tab=final] .final-stage{display:block}.final-stage{display:none;margin:18px auto;max-width:1240px;padding:18px;border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface-raised)}.stage-head{display:flex;justify-content:space-between;gap:16px;align-items:center}.render-status{margin-top:12px;color:var(--color-text-muted)}.render-results{display:grid;gap:12px;margin-top:14px}.result-item{border:1px solid #303030;border-radius:8px;background:#090909;overflow:hidden}.result-item[open]{border-color:var(--color-metal-gray)}.result-item summary{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:12px 14px;border:0;color:var(--color-text)}.result-item summary strong{font-size:14px}.result-item summary span{color:var(--color-text-muted);font-size:12px}.result-body{display:grid;grid-template-columns:minmax(260px,420px) minmax(240px,1fr);gap:14px;padding:0 14px 14px}.result-body video{width:100%;max-height:70vh;background:#000;border-radius:6px;object-fit:contain}.result-meta{display:grid;align-content:start;gap:10px}.result-meta dl{margin:0}.result-path{display:block;max-width:100%;padding:8px 10px;border:1px solid rgba(17,162,207,.28);border-radius:6px;background:rgba(17,162,207,.08);color:var(--color-text);font-size:12px;line-height:1.35;overflow-wrap:anywhere}.result-actions{display:flex;gap:8px;flex-wrap:wrap}.result-actions a,.result-actions button{display:inline-flex;align-items:center;justify-content:center;min-height:38px;padding:9px 12px;border-radius:6px;background:var(--color-brand-white);color:var(--color-brand-black);text-decoration:none}.result-actions a.secondary,.result-actions button.secondary{background:#242424;color:var(--color-text-soft);border:1px solid var(--color-border-strong)}
.empty-project-stage{display:none;max-width:720px;margin:18px auto;padding:0 18px}.empty-project-panel{display:grid;gap:10px;padding:18px;border:1px solid var(--glass-border);border-radius:var(--radius-panel);background:var(--glass-bg-strong);box-shadow:var(--glass-shadow),inset 0 1px 0 var(--glass-edge);backdrop-filter:blur(24px) saturate(1.45);text-align:center}.empty-project-panel p{margin:0;color:var(--color-text-muted)}.empty-project-panel button{justify-self:center}body[data-project-empty=true][data-tab=edit] main{display:none}body[data-project-empty=true][data-tab=edit] .empty-project-stage{display:block}
.settings-backdrop{position:fixed;inset:0;z-index:50;display:grid;place-items:center;padding:18px;background:rgba(0,0,0,.58)}.settings-backdrop[hidden]{display:none}.settings-panel{width:min(560px,100%);border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface-raised);box-shadow:var(--shadow-panel);padding:16px}.settings-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.settings-head p{margin:3px 0 0;color:var(--color-text-muted)}.settings-form{display:grid;gap:12px;margin-top:14px}.settings-form label{display:grid;gap:6px;color:var(--color-text-muted);font-size:12px}.settings-form input,.settings-form select{width:100%;border:1px solid var(--color-border-strong);border-radius:6px;background:var(--color-brand-black);color:var(--color-text);padding:9px 10px;font:inherit}.settings-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.settings-status,.settings-usage{padding:10px;border:1px solid var(--color-border);border-radius:8px;background:#0b0b0b;color:var(--color-text-soft)}.settings-usage{display:grid;gap:3px;color:var(--color-text-muted)}.settings-actions{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}.settings-form small{color:var(--color-text-muted)}
button{background:var(--color-brand-white);color:var(--color-brand-black);border:0;border-radius:6px;padding:9px 12px;cursor:pointer}#reset-ui,button[data-action=discard]{background:#242424;color:var(--color-text-soft)}
@media(max-width:860px){header{position:relative;grid-template-columns:1fr;justify-items:center}.header-actions{justify-content:center}.brand-logo{width:min(390px,88vw);height:64px}.brand-lockup p{max-width:86vw}.tabs{top:0;overflow:auto}.preview-strip button{font-size:12px;padding:7px 9px}main{padding:12px}.clip-summary{grid-template-columns:auto minmax(0,1fr);align-items:start}.clip-row-timeline,.clip-status{grid-column:1/-1}.clip-status{justify-content:flex-start}.editor-shell,.result-body,.camera-segments,.camera-smart-row,.camera-smart-ai,.camera-path-actions,.camera-keyframe-panel,.caption-settings,.preview-bar,.import-grid,.duration-profile,.import-path-row,.settings-grid,.effect-split,.bumper-actions{grid-template-columns:1fr}.preview-frame{max-width:100%}.preview-strip{justify-content:center}.preview-controls{width:max-content;max-width:100%;flex-wrap:wrap}.media{max-height:none}.stage-head{align-items:flex-start;flex-direction:column}.result-item summary{align-items:flex-start;flex-direction:column}.camera-card-buttons,.effect-card-buttons,.overlay-card-buttons,.overlay-menu{grid-template-columns:1fr}}
"""


def liquid_ui_css() -> str:
    return """
:root{--glass-bg:rgba(18,18,18,.54);--glass-bg-strong:rgba(22,22,22,.76);--glass-border:rgba(231,231,232,.18);--glass-edge:rgba(255,255,255,.34);--glass-highlight:rgba(255,255,255,.12);--glass-shadow:0 22px 56px rgba(0,0,0,.46);--control-bg:rgba(28,28,28,.58);--control-hover:rgba(54,54,54,.7);--control-active:rgba(17,162,207,.2);--radius-control:999px;--radius-panel:8px;--focus-ring:0 0 0 2px rgba(17,162,207,.55)}
html{min-height:100%;background:var(--color-brand-black)}
body{min-height:100vh;background:linear-gradient(145deg,rgba(17,162,207,.16) 0%,rgba(5,5,5,.04) 24%,rgba(5,5,5,0) 52%,rgba(175,207,42,.12) 100%),linear-gradient(180deg,#050505 0%,#080808 42%,#050505 100%);background-repeat:no-repeat;background-size:100vw 100vh,100vw 100vh;background-attachment:fixed;font-family:Inter,Arial,sans-serif;letter-spacing:0}
button,.import-result a,.result-actions a{position:relative;min-height:36px;border:1px solid var(--glass-border);border-radius:var(--radius-control);background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025) 38%,rgba(0,0,0,.08)),var(--control-bg);color:var(--color-text-soft);box-shadow:inset 0 1px 0 var(--glass-edge),inset 0 -10px 18px rgba(0,0,0,.16),0 8px 22px rgba(0,0,0,.22);transition:background .16s ease,border-color .16s ease,color .16s ease,transform .16s ease,box-shadow .16s ease}
button:hover,.import-result a:hover,.result-actions a:hover{background:linear-gradient(180deg,rgba(255,255,255,.14),rgba(255,255,255,.035) 42%,rgba(0,0,0,.08)),var(--control-hover);border-color:rgba(231,231,232,.3);box-shadow:inset 0 1px 0 rgba(255,255,255,.42),inset 0 -10px 18px rgba(0,0,0,.14),0 10px 26px rgba(0,0,0,.26)}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:0;box-shadow:var(--focus-ring)}
button:active{transform:translateY(1px)}
button:disabled{opacity:.48;cursor:not-allowed;transform:none}
header{background:linear-gradient(180deg,rgba(5,5,5,.92),rgba(5,5,5,.68));backdrop-filter:blur(22px) saturate(1.35);border-bottom:1px solid var(--glass-border)}
.brand-logo{width:min(500px,48vw);height:70px}.brand-lockup p{margin-top:0;color:rgba(231,231,232,.56)}
.header-actions button,#reset-ui{background:linear-gradient(180deg,rgba(255,255,255,.12),rgba(255,255,255,.03)),rgba(231,231,232,.08);color:var(--color-text-soft);border-color:var(--glass-border)}
.tabs{justify-content:center;background:rgba(5,5,5,.58);backdrop-filter:blur(22px) saturate(1.35);border-bottom:1px solid var(--glass-border)}
.tabs button{min-width:98px;background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025)),rgba(231,231,232,.055);border-color:var(--glass-border);color:rgba(231,231,232,.78);font-weight:700}
.tabs button.active{background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white)}
.card,.import-panel,.final-stage{border-color:var(--glass-border);background:linear-gradient(180deg,rgba(17,17,17,.92),rgba(10,10,10,.94));box-shadow:0 10px 34px rgba(0,0,0,.22)}
.card[open]{border-color:rgba(231,231,232,.22);background:linear-gradient(180deg,rgba(20,20,20,.96),rgba(12,12,12,.96))}
.card.liked,.card.liked[open]{border-color:rgba(175,207,42,.68)}.card.liked [data-status-pill]{background:rgba(175,207,42,.16);border-color:rgba(175,207,42,.58);color:var(--color-brand-green)}
.clip-summary{min-height:58px}.clip-status span,.format-previews span{background:rgba(231,231,232,.07);border:1px solid var(--glass-border);color:rgba(231,231,232,.72)}
.preview-bar{gap:10px;padding:10px;width:100%;border:1px solid var(--glass-border);border-radius:var(--radius-panel);background:linear-gradient(160deg,rgba(255,255,255,.12),rgba(255,255,255,.035) 34%,rgba(0,0,0,.1) 100%),var(--glass-bg);box-shadow:var(--glass-shadow),inset 0 1px 0 var(--glass-edge),inset 0 -18px 30px rgba(0,0,0,.18);backdrop-filter:blur(26px) saturate(1.55)}
.preview-strip{width:100%;justify-content:center}.preview-strip button,.platform-tags button,.camera-card-buttons button,.effect-card-buttons button,.overlay-card-buttons button{border-color:var(--glass-border);background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025)),rgba(231,231,232,.055);color:rgba(231,231,232,.82);font-weight:700;text-align:center}
.preview-strip button.active,.platform-tags button.active,.camera-card-buttons button.active,.effect-card-buttons button.active,.overlay-card-buttons button.active{background:var(--control-active);color:var(--color-brand-blue);border-color:rgba(17,162,207,.72)}
.preview-controls{gap:8px;padding:5px 8px;border-color:var(--glass-border);background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025)),rgba(5,5,5,.26);box-shadow:inset 0 1px 0 var(--glass-edge),0 8px 22px rgba(0,0,0,.24);backdrop-filter:blur(18px) saturate(1.45)}
.preview-icon,.preview-step{border-color:var(--glass-border);background:linear-gradient(180deg,rgba(255,255,255,.14),rgba(255,255,255,.035)),rgba(231,231,232,.08);color:var(--color-text);box-shadow:inset 0 1px 0 rgba(255,255,255,.36),inset 0 -8px 14px rgba(0,0,0,.14)}
.preview-play{width:38px;height:38px;min-width:38px;background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white)}
.preview-volume-group{border-left:1px solid rgba(231,231,232,.12)}.preview-volume-group output{color:rgba(231,231,232,.72);font-variant-numeric:tabular-nums}
.preview-bar,.preview-controls,.preview-camera-timeline,.preview-volume-group{overflow:visible}.preview-bar{position:relative;z-index:20}.preview-topbar{display:flex;align-items:center;justify-content:space-between;gap:8px;width:100%;min-width:0}.preview-topbar .preview-strip{flex:1 1 auto;width:auto;min-width:0;justify-content:flex-start;flex-wrap:nowrap;overflow-x:auto;overflow-y:hidden;padding-bottom:0;scrollbar-width:none}.preview-topbar .preview-strip::-webkit-scrollbar{display:none}.preview-topbar .preview-strip button{flex:0 0 auto;min-height:32px;padding:7px 9px;font-size:12px}.preview-controls{display:block;width:100%;max-width:100%;padding:0;border:0;background:transparent;box-shadow:none;backdrop-filter:none}.preview-transport-group{flex:0 0 auto;display:flex;align-items:center;gap:6px;padding:5px 6px;border:1px solid var(--glass-border);border-radius:999px;background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025)),rgba(5,5,5,.26);box-shadow:inset 0 1px 0 var(--glass-edge),0 8px 22px rgba(0,0,0,.18);backdrop-filter:blur(18px) saturate(1.45)}.preview-volume-group{position:relative;padding-left:0;border-left:0}.preview-camera-timeline{position:relative;width:100%;min-width:0;display:grid;align-items:center;min-height:42px;padding:6px 12px;border:1px solid rgba(17,162,207,.42);border-radius:4px;background:linear-gradient(180deg,rgba(17,162,207,.11),rgba(255,255,255,.025)),rgba(5,5,5,.24);box-shadow:inset 0 1px 0 var(--glass-edge),0 8px 22px rgba(0,0,0,.18);backdrop-filter:blur(18px) saturate(1.45)}.preview-camera-rail{position:relative;width:100%;height:24px;cursor:pointer;touch-action:none}.preview-audio-waveform{position:absolute;inset:1px 0;z-index:0;display:flex;align-items:center;gap:1px;opacity:.78;pointer-events:none}.preview-audio-waveform[hidden]{display:none}.preview-audio-waveform span{flex:1;min-width:1px;max-height:21px;background:rgba(175,207,42,.42);border-radius:1px}.preview-camera-track{position:absolute;left:0;right:0;top:50%;z-index:1;height:3px;border-radius:0;background:linear-gradient(90deg,rgba(17,162,207,.5),rgba(231,231,232,.12));box-shadow:inset 0 0 0 1px rgba(255,255,255,.04);transform:translateY(-50%)}.preview-camera-playhead{position:absolute;top:50%;z-index:4;width:2px;height:20px;border-radius:999px;background:var(--color-brand-white);box-shadow:0 0 0 1px rgba(0,0,0,.7);transform:translate(-50%,-50%);pointer-events:none}.preview-camera-marker{position:absolute;top:50%;z-index:3;width:9px;height:22px;min-width:9px;padding:0;border:1px solid rgba(17,162,207,.84);border-radius:3px;background:rgba(17,162,207,.16);box-shadow:inset 0 1px 0 rgba(255,255,255,.2),0 0 0 2px rgba(17,162,207,.06);transform:translate(-50%,-50%);cursor:pointer}.preview-camera-marker:active{transform:translate(-50%,-50%)}.preview-camera-marker.active{background:var(--color-brand-blue);box-shadow:0 0 0 3px rgba(17,162,207,.18),0 0 14px rgba(17,162,207,.32)}.preview-camera-popover,.preview-volume-popover{position:absolute;z-index:1000;display:grid;gap:8px;padding:10px;border:1px solid var(--glass-border);border-radius:8px;background:#101010;box-shadow:var(--shadow-panel)}.preview-camera-popover{top:calc(100% + 8px);left:50%;width:min(260px,92vw);transform:translateX(-50%)}.preview-camera-popover[hidden],.preview-volume-popover[hidden]{display:none}.preview-camera-popover label{display:grid;gap:5px;color:var(--color-text-muted);font-size:12px}.preview-camera-popover select{width:100%;background:var(--color-brand-black);color:var(--color-text);border:1px solid var(--color-border-strong);border-radius:6px;padding:8px}.preview-camera-popover input{width:100%;accent-color:var(--color-brand-blue)}.preview-camera-popover button{min-height:32px;background:#242424;color:var(--color-text-soft);border:1px solid var(--color-border-strong)}.preview-volume-popover{right:50%;bottom:calc(100% + 8px);width:auto;height:128px;padding:12px 8px;place-items:center;transform:translateX(50%)}.preview-volume-slider{display:block;width:110px;accent-color:var(--color-brand-blue);writing-mode:vertical-rl;direction:rtl}
.preview-topbar{justify-content:flex-start;position:relative;z-index:80}.preview-format-menu{position:relative;z-index:1400;min-width:134px}.preview-format-trigger{display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;min-height:38px;padding:8px 12px;border:1px solid var(--glass-border);border-radius:999px;background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025)),rgba(5,5,5,.26);color:var(--color-text-soft);font-weight:800}.preview-format-trigger:after{content:"";width:7px;height:7px;border-right:1px solid currentColor;border-bottom:1px solid currentColor;transform:rotate(45deg) translateY(-2px);opacity:.72}.preview-format-trigger[aria-expanded=true]{border-color:rgba(17,162,207,.72);color:var(--color-brand-blue)}.preview-format-options{position:absolute;top:calc(100% + 7px);left:0;z-index:1500;display:grid;gap:4px;width:max(100%,160px);padding:7px;border:1px solid var(--glass-border);border-radius:8px;background:#101010;box-shadow:var(--shadow-panel)}.preview-format-options[hidden]{display:none}.preview-format-options button{display:flex;justify-content:flex-start;min-height:32px;padding:7px 9px;border:1px solid transparent;border-radius:6px;background:transparent;color:var(--color-text-soft);font-weight:700;text-align:left}.preview-format-options button.active{border-color:rgba(17,162,207,.52);background:rgba(17,162,207,.14);color:var(--color-brand-blue)}
.preview-motion-control{display:flex;align-items:center;gap:7px;min-height:38px;padding:7px 10px;border:1px solid var(--glass-border);border-radius:999px;background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(255,255,255,.02)),rgba(5,5,5,.22);color:var(--color-text-muted);font-size:11px;font-weight:800;white-space:nowrap}.preview-motion-control input{width:82px;accent-color:var(--color-brand-blue)}
.clip-summary{grid-template-columns:auto minmax(0,1fr) auto;align-items:start;gap:10px 12px;cursor:pointer}.clip-status{grid-column:3;grid-row:1;align-self:start}.clip-row-timeline{grid-column:2/4;width:100%;min-width:0;height:36px;min-height:36px;padding:0;cursor:default}.clip-row-timeline.preview-camera-timeline{display:block;align-items:initial}.card[open]{overflow:visible}.card[open] .clip-summary{position:relative;overflow:visible;padding:14px 18px 16px;grid-template-columns:auto minmax(0,1fr) auto}.card[open] .clip-row-timeline{grid-column:1/-1;height:auto;min-height:226px}.card[open] .clip-row-timeline.preview-camera-timeline--live{width:calc(100% + 36px);min-height:226px;margin:4px -18px 0;border:0!important;background:transparent!important;box-shadow:none!important;overflow:visible!important;backdrop-filter:none}.card[open] .clip-row-timeline.preview-camera-timeline--live .timeline-shell{min-height:224px;overflow:visible!important;border:0!important;border-radius:0!important;background:linear-gradient(90deg,rgba(255,255,255,.028) 1px,transparent 1px) 0 0/28px 100%,linear-gradient(180deg,rgba(17,162,207,.055),transparent 38%)!important;box-shadow:none!important}.card[open] .clip-row-timeline.preview-camera-timeline--live .timeline-canvas{overflow:visible}.card[open] .clip-row-timeline.preview-camera-timeline--live .playhead-control{z-index:12}.card[open] .clip-row-timeline.preview-camera-timeline--live .trim-handle,.card[open] .clip-row-timeline.preview-camera-timeline--live .trim-handle:hover,.card[open] .clip-row-timeline.preview-camera-timeline--live .trim-handle:focus-visible,.card[open] .clip-row-timeline.preview-camera-timeline--live .trim-handle.is-dragging{z-index:10!important;padding:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;transform:none!important}.card:not([open]) .clip-row-timeline.preview-camera-timeline{overflow:hidden}.card:not([open]) .clip-row-timeline .preview-camera-popover,.card:not([open]) .clip-row-timeline .volume-popover{display:none!important}
.media{border:1px solid rgba(255,255,255,.08);border-radius:var(--radius-panel);background:#000;box-shadow:0 14px 44px rgba(0,0,0,.32)}
.tool-section,.export-dock,.overlay-menu,.settings-panel{border-color:var(--glass-border);border-radius:var(--radius-panel);background:linear-gradient(160deg,rgba(255,255,255,.08),rgba(255,255,255,.025) 36%,rgba(0,0,0,.08) 100%),var(--glass-bg-strong);box-shadow:var(--glass-shadow),inset 0 1px 0 var(--glass-edge),inset 0 -18px 28px rgba(0,0,0,.14);backdrop-filter:blur(24px) saturate(1.45)}
.tool-section>summary{color:rgba(231,231,232,.9)}.export-dock{padding:14px}.export-dock span{color:rgba(231,231,232,.6)}
.timeline-scrub-track,.timeline-track{border-color:rgba(231,231,232,.12);background:linear-gradient(90deg,rgba(17,162,207,.18),rgba(231,231,232,.08))}
.timeline-selected{background:rgba(17,162,207,.2)}.timeline-playhead,.timeline-playhead:before,.timeline-fill{background:var(--color-brand-white)}
button[data-action=like],.import-panel button[type=submit],#finalize-videos,.import-result a,.result-actions a,.result-actions button{background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white);font-weight:800}
button[data-action=discard],.result-actions a.secondary,.result-actions button.secondary{background:rgba(231,231,232,.07);color:rgba(231,231,232,.76);border-color:var(--glass-border)}
.import-panel input,.import-panel select,.import-panel textarea,.camera-card-controls select,.caption-settings select,.caption-settings input,.overlay-inspector input[type=text],.overlay-inspector input[type=number],.settings-form input,.settings-form select{border-color:var(--glass-border);border-radius:var(--radius-panel);background:rgba(5,5,5,.72);color:var(--color-text)}
.duration-profile span,.camera-path-editor,.camera-segment,.layer-chip,.overlay-layer-row,.image-upload{border-color:var(--glass-border);background:rgba(231,231,232,.05)}
.duration-profile input:checked+span,.layer-chip.is-selected{border-color:rgba(17,162,207,.72);background:var(--control-active);color:var(--color-text)}
.camera-path-rail{background:linear-gradient(90deg,rgba(17,162,207,.28),rgba(231,231,232,.1),rgba(175,207,42,.18))}.camera-path-marker{border-color:var(--glass-border);background:linear-gradient(180deg,rgba(255,255,255,.14),rgba(255,255,255,.035)),rgba(231,231,232,.12);box-shadow:inset 0 1px 0 rgba(255,255,255,.32),0 6px 14px rgba(0,0,0,.26)}.camera-path-marker.active{background:var(--color-brand-blue);border-color:rgba(17,162,207,.88);box-shadow:0 0 0 4px rgba(17,162,207,.16),0 0 24px rgba(17,162,207,.26)}
.preview-camera-marker span,.camera-path-marker span{position:absolute;left:50%;bottom:calc(100% + 4px);max-width:72px;padding:2px 5px;border:1px solid rgba(231,231,232,.2);border-radius:999px;background:rgba(5,5,5,.82);color:var(--color-text-soft);font-size:10px;line-height:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transform:translateX(-50%);pointer-events:none}.camera-path-marker{overflow:visible}.preview-camera-marker{overflow:visible}.camera-path-marker span{bottom:calc(100% + 5px)}.preview-camera-marker.active span,.camera-path-marker.active span{border-color:rgba(17,162,207,.7);color:#fff}
.preview-camera-popover{overflow:hidden}.preview-camera-popover--live{gap:7px;padding:11px;border-color:rgba(17,162,207,.42);border-radius:12px;background:radial-gradient(circle at 26% 0,rgba(17,162,207,.26),transparent 36%),linear-gradient(135deg,rgba(231,231,232,.16),transparent 32%),rgba(7,7,7,.86);box-shadow:inset 0 1px rgba(255,255,255,.22),inset 0 -1px rgba(0,0,0,.62),0 22px 58px rgba(0,0,0,.58),0 0 36px rgba(17,162,207,.24);backdrop-filter:blur(24px) saturate(1.28);animation:preview-camera-popover-in 220ms cubic-bezier(.2,.9,.2,1)}.preview-camera-popover-aura,.preview-camera-popover-lens,.preview-camera-popover-beam{position:absolute;pointer-events:none}.preview-camera-popover-aura{inset:-34px;background:conic-gradient(from 140deg,transparent,rgba(17,162,207,.24),transparent 42%),radial-gradient(circle at 76% 18%,rgba(175,207,42,.16),transparent 20%);opacity:.48;animation:preview-camera-popover-orbit 5.2s linear infinite}.preview-camera-popover-lens{right:10px;top:12px;width:50px;height:50px;border:1px solid rgba(231,231,232,.12);border-radius:50%;background:radial-gradient(circle at 36% 30%,rgba(255,255,255,.24),transparent 28%),radial-gradient(circle,rgba(17,162,207,.16),transparent 68%);opacity:.64}.preview-camera-popover-beam{left:50%;bottom:-34px;width:2px;height:34px;background:linear-gradient(180deg,rgba(17,162,207,.9),transparent);box-shadow:0 0 18px rgba(17,162,207,.54)}.preview-camera-popover-head,.preview-camera-popover label,.preview-camera-popover small,.preview-camera-popover-actions,.preview-camera-popover-meter,.preview-camera-popover-primary{position:relative;z-index:1}.preview-camera-popover-head{display:grid;grid-template-columns:1fr auto auto;gap:7px;align-items:center}.preview-camera-popover-head strong{font-size:12px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-shadow:0 0 16px rgba(17,162,207,.36)}.preview-camera-popover-head span,.preview-camera-popover small{color:rgba(231,231,232,.64);font-size:11px}.preview-camera-popover-close{display:inline-grid!important;place-items:center;width:22px!important;height:22px!important;min-width:22px!important;min-height:22px!important;padding:0!important;border-radius:999px!important;background:rgba(231,231,232,.08)!important}.preview-camera-popover label{gap:4px;font-size:11px;text-transform:none}.preview-camera-popover select{min-height:31px;padding:6px 8px;border-color:rgba(17,162,207,.34);background:rgba(0,0,0,.56)}.preview-camera-popover input{height:18px}.preview-camera-popover-meter{overflow:hidden;height:6px;margin:1px 0 2px;border-radius:999px;background:rgba(0,0,0,.28);box-shadow:inset 0 0 10px rgba(0,0,0,.58)}.preview-camera-popover-meter i{position:relative;display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,var(--color-brand-blue),rgba(231,231,232,.9));box-shadow:0 0 16px rgba(17,162,207,.52);animation:preview-camera-meter-breathe 1.8s ease-in-out infinite}.preview-camera-popover-meter i::after{position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.52),transparent);content:"";transform:translateX(-110%);animation:preview-camera-meter-scan 2.4s ease-in-out infinite}.preview-camera-popover-actions{display:grid;grid-template-columns:1fr auto;gap:7px;align-items:center}.preview-camera-popover button{min-height:31px}.preview-camera-popover-primary{border-color:rgba(17,162,207,.56)!important;background:linear-gradient(180deg,rgba(17,162,207,.34),rgba(17,162,207,.12))!important;color:var(--color-text)!important;font-weight:900}.preview-camera-popover-danger{min-width:70px;color:#ff8f8f!important;border-color:rgba(255,111,111,.32)!important;background:linear-gradient(180deg,rgba(255,111,111,.12),rgba(255,111,111,.04))!important}.preview-camera-popover-danger:disabled{opacity:.42}.preview-camera-popover--portal{position:fixed!important;z-index:3200!important;width:min(236px,calc(100vw - 16px))!important;max-width:calc(100vw - 16px);transform:none!important}@keyframes preview-camera-popover-in{from{opacity:0;transform:translateY(12px) scale(.94);filter:blur(6px)}to{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}}@keyframes preview-camera-popover-orbit{to{transform:rotate(360deg)}}@keyframes preview-camera-meter-breathe{0%,100%{filter:brightness(.94)}50%{filter:brightness(1.18)}}@keyframes preview-camera-meter-scan{0%,18%{transform:translateX(-110%)}58%,100%{transform:translateX(130%)}}
.preview-volume-group{z-index:2300}.preview-volume-popover{z-index:2600!important;width:44px!important;min-width:44px!important;height:120px!important;padding:10px 6px!important;overflow:visible}.preview-volume-slider{width:92px!important;max-width:92px}.preview-ai-button{display:inline-grid;place-items:center;min-width:42px;height:32px;padding:0 12px;border:1px solid rgba(17,162,207,.72);border-radius:999px;background:linear-gradient(180deg,rgba(17,162,207,.28),rgba(17,162,207,.1));color:var(--color-text);font-weight:900;letter-spacing:0}.preview-ai-button:disabled{opacity:.62;cursor:progress}.preview-ai-status{min-height:16px;width:100%;color:rgba(231,231,232,.62);font-size:12px;line-height:1.25;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.overlay-menu button,.overlay-layer-row button{background:rgba(231,231,232,.08);color:rgba(231,231,232,.8);border-color:var(--glass-border)}
.overlay-danger{background:rgba(80,20,20,.72)!important;border-color:rgba(255,120,120,.46)!important;color:#ffd2d2!important}
.settings-status,.settings-usage{border-color:var(--glass-border);background:rgba(231,231,232,.05)}.settings-backdrop{backdrop-filter:blur(14px)}
.result-item{border-color:var(--glass-border);background:rgba(9,9,9,.82)}.result-item[open]{border-color:rgba(231,231,232,.25)}
.result-body video{border:1px solid rgba(255,255,255,.08);border-radius:var(--radius-panel)}
.tabs{display:none!important}header{grid-template-columns:minmax(120px,1fr) auto minmax(240px,1fr);padding:14px 26px 16px}.brand-logo{width:min(560px,52vw);height:84px}.header-actions{align-items:center}.header-actions #finalize-videos{padding-inline:18px}.clip-summary{grid-template-columns:auto minmax(220px,1fr) minmax(560px,760px);align-items:center;gap:10px 14px;min-height:104px;padding:12px 18px;overflow:visible}.clip-rank{align-self:center;font-size:13px;letter-spacing:.08em}.clip-title strong{font-size:16px;letter-spacing:0}.clip-title small{font-size:12px}.clip-control-surface{grid-column:3;grid-row:1;display:flex!important;justify-content:flex-end;width:100%;min-width:0;margin:0!important}.clip-control-surface:empty{display:none!important}.clip-control-surface .cuted-control-bar{width:min(100%,760px);min-width:0;min-height:82px;padding:7px 12px;border-radius:16px}.clip-control-surface .cuted-render-zone{min-height:64px;justify-content:flex-end;overflow:visible}.clip-control-surface .cuted-tool-group{flex:0 1 354px;min-height:64px}.clip-control-surface .cuted-tile-button{flex:0 0 58px;width:58px;height:54px;font-size:26px}.clip-control-surface .cuted-insert-button span{font-size:18px}.clip-control-surface .cuted-format-trigger{flex:0 0 104px;width:104px;height:54px;gap:7px;padding:6px 8px}.clip-control-surface .cuted-format-copy small{display:none}.clip-control-surface .cuted-format-copy strong{font-size:18px}.clip-control-surface .cuted-ratio-vertical{width:14px;height:30px}.clip-control-surface .cuted-ratio-feed{width:20px;height:26px}.clip-control-surface .cuted-ratio-wide{width:29px;height:16px}.clip-control-surface .cuted-divider{height:42px;margin:0 6px}.clip-control-surface .cuted-audio-group{flex:0 0 52px;min-width:52px}.clip-control-surface .cuted-ready-region{flex:0 0 116px;width:116px;min-height:54px;margin-left:auto}.clip-control-surface .cuted-approve-button{width:52px;height:52px}.clip-control-surface .cuted-approve-button svg{width:31px;height:31px}.clip-control-surface .cuted-discard-button{width:40px;height:40px}.clip-row-timeline{grid-column:1/-1;grid-row:2;width:100%;min-width:0;height:34px;min-height:34px;margin-top:2px}.card[open] .clip-summary{grid-template-columns:auto minmax(220px,1fr) minmax(560px,760px);align-items:center;padding:14px 18px 16px}.card[open] .clip-row-timeline{grid-column:1/-1;grid-row:2}.card[open] .clip-row-timeline.preview-camera-timeline--live{width:calc(100% + 36px);margin:6px -18px 0}.editor-shell{display:grid;grid-template-columns:1fr;padding:0 18px 22px}.editor-preview{justify-items:center}.preview-frame{width:100%;justify-items:center;max-width:100%}.card[data-preview-format=tiktok] .preview-frame,.card[data-preview-format=shorts] .preview-frame,.card[data-preview-format=instagram] .preview-frame{max-width:100%}.card[data-preview-format=facebook] .preview-frame,.card[data-preview-format=youtube] .preview-frame{max-width:100%}.media{width:min(100%,calc(72vh * 9 / 16));max-width:520px;max-height:72vh}.card[data-preview-format=facebook] .media{width:min(100%,calc(72vh * 4 / 5));max-width:560px}.card[data-preview-format=youtube] .media{width:min(100%,920px);max-width:920px}.edit-hidden-hooks{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.preview-bar,.editor-tools,.tool-stack,.tool-section,.export-dock,.clip-status{display:none!important}@media(max-width:1120px){.clip-summary,.card[open] .clip-summary{grid-template-columns:auto minmax(0,1fr);align-items:start}.clip-control-surface{grid-column:1/-1;grid-row:2;justify-content:center}.clip-row-timeline{grid-row:3}.clip-control-surface .cuted-control-bar{width:min(100%,760px)}}@media(max-width:860px){header{grid-template-columns:1fr;padding:12px}.brand-logo{width:min(420px,90vw);height:70px}.clip-summary,.card[open] .clip-summary{grid-template-columns:auto minmax(0,1fr);padding:12px}.clip-control-surface{grid-column:1/-1;grid-row:2}.clip-row-timeline{grid-column:1/-1;grid-row:3}.clip-control-surface .cuted-control-bar{width:100%;min-height:80px;padding:7px 9px}.editor-shell{padding:0 12px 16px}.media{max-height:none;width:100%;max-width:min(100%,520px)}}
@supports not (backdrop-filter:blur(1px)){.preview-bar,.preview-controls,.tool-section,.export-dock,.overlay-menu,header,.tabs{background:#111}}
@media(max-width:860px){.brand-logo{width:min(360px,86vw);height:58px}.tabs{justify-content:flex-start}.tabs button{min-width:auto}.preview-bar{padding:8px}.preview-controls{grid-template-columns:1fr;max-width:100%;justify-content:stretch}.preview-transport-group{justify-self:center}.preview-camera-timeline{width:100%}.preview-volume-group{flex-wrap:nowrap}}
@media(max-width:860px){body{overflow-x:hidden}.brand-logo{width:min(420px,90vw);height:70px}.card[open] .clip-row-timeline{grid-row:3}.card[open] .clip-row-timeline.preview-camera-timeline--live{width:100%;margin:6px 0 0}.clip-control-surface .cuted-format-menu{left:auto;right:0;width:min(300px,calc(100vw - 48px))}.clip-control-surface .cuted-format-option{width:100%}}
body{position:relative;background:linear-gradient(180deg,#050505 0%,#070907 58%,#050505 100%);background-attachment:fixed}body::before{position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(circle at 16% 8%,rgba(17,162,207,.22),transparent 30%),radial-gradient(circle at 88% 38%,rgba(175,207,42,.19),transparent 34%);content:"";opacity:.72;animation:cuted-edit-bg-breathe 22s ease-in-out infinite}header,main,.empty-project-stage,.settings-backdrop,.app-notice{position:relative;z-index:1}@keyframes cuted-edit-bg-breathe{0%,100%{opacity:.5}50%{opacity:.82}}header{padding:18px 26px 2px!important;background:transparent!important;border-bottom:0!important;box-shadow:none!important}.brand-lockup{gap:1px}.brand-logo{width:min(672px,62vw);height:101px;transform:translateY(4px)}.brand-lockup p{display:none!important}.tabs{border-bottom:0!important}main{padding-top:0}.card,.card[open]{border:0!important;background:transparent!important;box-shadow:none!important;overflow:visible}.clip-summary,.card[open] .clip-summary{grid-template-columns:1fr;align-items:stretch;gap:0;min-height:0;padding:0;overflow:visible}.clip-control-surface{grid-column:1/-1;grid-row:1;display:block!important;width:100%;min-width:0;margin:0!important}.clip-control-surface:empty{display:none!important}.clip-control-surface .cuted-control-bar{width:100%;max-width:none;min-width:0;min-height:88px;margin:0;padding:7px 12px 7px 18px;border-radius:16px}.clip-control-surface .cuted-clip-info{flex:0 1 30%;max-width:30%;min-width:0;padding-right:10px}.clip-control-surface .cuted-clip-copy,.clip-control-surface .cuted-clip-copy strong,.clip-control-surface .cuted-clip-copy small{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.clip-control-surface .cuted-render-zone{flex:1 1 auto;min-width:0;min-height:64px;justify-content:flex-end;overflow:visible}.clip-control-surface .cuted-tool-group{flex:0 1 354px;min-height:64px}.clip-control-surface .cuted-tile-button{flex:0 0 58px;width:58px;height:54px;font-size:26px}.clip-control-surface .cuted-format-trigger{flex:0 0 104px;width:104px;height:54px}.clip-control-surface .cuted-audio-group{flex:0 0 52px;min-width:52px}.clip-control-surface .cuted-divider{height:42px;margin:0 6px}.clip-row-timeline,.clip-row-timeline.preview-camera-timeline{display:none!important}.card[open] .clip-row-timeline,.card[open] .clip-row-timeline.preview-camera-timeline{display:block!important;grid-column:1/-1;grid-row:2;margin-top:0}.card[open] .clip-row-timeline.preview-camera-timeline--live{width:100%;margin:-12px 0 0}.editor-shell{display:grid;grid-template-columns:1fr;padding:0 0 16px;margin-top:-18px}.editor-preview{gap:0}.preview-frame{gap:0}@media(max-width:1120px){.clip-control-surface .cuted-control-bar{flex-wrap:wrap;gap:10px}.clip-control-surface .cuted-clip-info{flex:0 1 100%;max-width:100%}.clip-control-surface .cuted-render-zone{flex:1 1 auto}.card[open] .clip-row-timeline{grid-row:2}}@media(max-width:860px){.clip-control-surface .cuted-control-bar{min-height:80px;padding:10px}.card[open] .clip-row-timeline.preview-camera-timeline--live{width:100%;margin:-12px 0 0}}
.brand-logo{transform:translateY(-16px)}.clip-control-surface .cuted-render-zone{justify-content:flex-end;padding-left:clamp(96px,12vw,190px);gap:14px}.clip-control-surface .cuted-ready-region{flex:0 0 116px;width:116px;min-height:54px;margin-left:14px}.clip-control-surface .cuted-tool-group{flex:0 0 354px}.clip-control-surface .cuted-tool-buttons{justify-content:flex-end}.clip-control-surface .cuted-format-trigger{flex:0 0 132px;width:132px;height:58px;gap:8px;padding:6px 10px}.clip-control-surface .cuted-format-copy small{display:block;font-size:10px;line-height:1.05}.clip-control-surface .cuted-format-copy strong{font-size:18px}.clip-control-surface .cuted-ratio-vertical{width:14px;height:30px}.clip-control-surface .cuted-ratio-feed{width:20px;height:26px}.clip-control-surface .cuted-ratio-wide{width:29px;height:16px}
.clip-control-surface{position:relative;z-index:2600}.clip-control-surface .cuted-control-bar{position:relative;z-index:2600;overflow:visible}.clip-control-surface .cuted-effect-menu,.clip-control-surface .cuted-insert-menu,.clip-control-surface .cuted-caption-menu,.clip-control-surface .cuted-format-menu,.clip-control-surface .cuted-volume-popover{z-index:3200}.card[open] .clip-row-timeline.preview-camera-timeline--live{position:relative;z-index:1}
.header-actions{gap:10px;align-items:center}.header-actions .header-icon-button,#reset-ui.header-icon-button,#finalize-videos.header-icon-button,#open-settings.header-icon-button{position:relative;display:inline-grid;place-items:center;width:52px;height:52px;min-width:52px;padding:0!important;border:1px solid rgba(231,231,232,.18)!important;border-radius:16px;background:linear-gradient(180deg,rgba(255,255,255,.11),rgba(255,255,255,.025)),rgba(8,9,10,.52)!important;color:rgba(231,231,232,.8)!important;box-shadow:inset 0 1px rgba(255,255,255,.15),0 14px 34px rgba(0,0,0,.3);backdrop-filter:blur(18px) saturate(1.2);overflow:hidden}.header-actions .header-icon-button:before{position:absolute;inset:7px;border-radius:12px;background:radial-gradient(circle at 50% 22%,rgba(17,162,207,.16),transparent 62%);opacity:.64;content:"";transition:opacity .18s ease,transform .18s ease}.header-actions .header-icon-button svg{position:relative;z-index:1;width:28px;height:28px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}.header-actions .header-icon-button:hover,.header-actions .header-icon-button:focus-visible{border-color:rgba(17,162,207,.58)!important;color:var(--color-text)!important;box-shadow:inset 0 1px rgba(255,255,255,.2),0 0 24px rgba(17,162,207,.22),0 16px 38px rgba(0,0,0,.34)}.header-actions .header-icon-button:hover:before,.header-actions .header-icon-button:focus-visible:before{opacity:1;transform:scale(1.08)}.header-actions .header-render-button,#finalize-videos.header-render-button{width:58px;height:58px;min-width:58px;border-color:rgba(175,207,42,.48)!important;color:var(--color-brand-green)!important;background:linear-gradient(180deg,rgba(175,207,42,.18),rgba(17,162,207,.065)),rgba(12,14,9,.7)!important;box-shadow:inset 0 1px rgba(255,255,255,.2),0 0 24px rgba(175,207,42,.22),0 16px 38px rgba(0,0,0,.36)}.header-actions .header-render-button:before{background:radial-gradient(circle at 58% 25%,rgba(175,207,42,.28),transparent 60%),radial-gradient(circle at 32% 70%,rgba(17,162,207,.12),transparent 56%)}.header-actions .header-render-button svg{width:32px;height:32px;stroke-width:1.85}.header-actions .header-render-button.is-rendering,#finalize-videos.header-render-button.is-rendering{border-color:rgba(175,207,42,.78)!important;color:var(--color-brand-green)!important;box-shadow:inset 0 1px rgba(255,255,255,.24),0 0 28px rgba(175,207,42,.34),0 0 42px rgba(17,162,207,.14),0 16px 38px rgba(0,0,0,.36);animation:cuted-render-button-pulse 1.65s ease-in-out infinite}.header-actions .header-render-button.is-rendering:before,#finalize-videos.header-render-button.is-rendering:before{opacity:1;transform:scale(1.12);animation:cuted-render-button-scan 1.4s ease-in-out infinite}.header-actions .header-render-button.is-rendering svg,#finalize-videos.header-render-button.is-rendering svg{animation:cuted-render-icon-drift 1.9s ease-in-out infinite;filter:drop-shadow(0 0 9px rgba(175,207,42,.42))}.header-actions .header-settings-button svg{width:26px;height:26px}.header-actions .header-new-project svg{width:29px;height:29px}#open-settings.header-settings-button.is-openai-ready{border-color:rgba(175,207,42,.62)!important;color:var(--color-brand-green)!important;background:linear-gradient(180deg,rgba(175,207,42,.2),rgba(17,162,207,.055)),rgba(10,14,8,.7)!important;box-shadow:inset 0 1px rgba(255,255,255,.2),0 0 24px rgba(175,207,42,.26),0 16px 38px rgba(0,0,0,.36)}#open-settings.header-settings-button.is-openai-ready:before{background:radial-gradient(circle at 50% 34%,rgba(175,207,42,.32),transparent 62%)}#open-settings.header-settings-button.is-openai-ready svg{animation:cuted-openai-gear-spin 5.8s linear infinite;filter:drop-shadow(0 0 8px rgba(175,207,42,.34))}@keyframes cuted-openai-gear-spin{to{transform:rotate(360deg)}}@keyframes cuted-render-button-pulse{0%,100%{filter:brightness(1)}50%{filter:brightness(1.2)}}@keyframes cuted-render-button-scan{0%,100%{opacity:.72;transform:scale(1.04) rotate(0deg)}50%{opacity:1;transform:scale(1.16) rotate(3deg)}}@keyframes cuted-render-icon-drift{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-1px) rotate(9deg)}}
.settings-backdrop{position:fixed!important;inset:0!important;z-index:5000!important;display:grid!important;place-items:center!important;padding:32px;background:radial-gradient(circle at 50% 42%,rgba(17,162,207,.18),transparent 30%),radial-gradient(circle at 64% 58%,rgba(175,207,42,.12),transparent 26%),rgba(0,0,0,.68)!important;backdrop-filter:blur(18px) saturate(1.18)!important;opacity:0;pointer-events:none;transition:opacity 180ms ease}.settings-backdrop[hidden]{display:none!important}.settings-backdrop.is-open{opacity:1;pointer-events:auto}.settings-backdrop.is-closing{opacity:0;pointer-events:none}.settings-panel{position:relative!important;isolation:isolate;width:min(640px,calc(100vw - 48px))!important;max-height:min(760px,calc(100vh - 56px));overflow:hidden auto;padding:20px!important;border:1px solid rgba(17,162,207,.34)!important;border-radius:22px!important;background:linear-gradient(145deg,rgba(231,231,232,.11),rgba(5,5,5,.8) 46%,rgba(11,15,10,.88)),rgba(5,5,5,.92)!important;box-shadow:0 0 0 1px rgba(255,255,255,.055),0 0 42px rgba(17,162,207,.2),0 0 58px rgba(175,207,42,.12),0 32px 86px rgba(0,0,0,.72)!important;transform:translateY(18px) scale(.965);opacity:0;outline:none;transition:transform 210ms cubic-bezier(.2,.9,.2,1),opacity 180ms ease}.settings-backdrop.is-open .settings-panel{transform:translateY(0) scale(1);opacity:1}.settings-backdrop.is-closing .settings-panel{transform:translateY(12px) scale(.975);opacity:0}.settings-aura{position:absolute;inset:-46px;z-index:-1;background:conic-gradient(from 130deg,transparent,rgba(17,162,207,.22),transparent 32%,rgba(175,207,42,.18),transparent 62%);opacity:.54;filter:blur(12px);animation:settings-aura-drift 8s linear infinite}.settings-head{position:relative;display:flex!important;align-items:flex-start!important;justify-content:space-between!important;gap:18px;padding:0 0 16px;border-bottom:1px solid rgba(231,231,232,.1)}.settings-title-row{display:flex;align-items:center;gap:14px;min-width:0}.settings-orb{display:grid;place-items:center;width:52px;height:52px;min-width:52px;border:1px solid rgba(175,207,42,.44);border-radius:16px;background:radial-gradient(circle at 50% 32%,rgba(175,207,42,.22),transparent 62%),rgba(8,11,8,.78);color:var(--color-brand-green);box-shadow:inset 0 1px rgba(255,255,255,.16),0 0 26px rgba(175,207,42,.18)}.settings-orb svg{width:27px;height:27px;fill:none;stroke:currentColor;stroke-width:1.9;animation:cuted-openai-gear-spin 7.2s linear infinite}.settings-head strong{display:block;color:var(--color-text);font-size:22px;line-height:1.05}.settings-head p{margin:5px 0 0!important;color:rgba(231,231,232,.62)!important;font-size:13px;line-height:1.25}.settings-close-button{display:grid!important;place-items:center;width:40px!important;height:40px!important;min-width:40px!important;padding:0!important;border:1px solid rgba(231,231,232,.16)!important;border-radius:14px!important;background:rgba(231,231,232,.06)!important;color:rgba(231,231,232,.75)!important;font-weight:900!important}.settings-close-button:hover,.settings-close-button:focus-visible{border-color:rgba(255,111,111,.42)!important;color:#ff9d9d!important;box-shadow:0 0 22px rgba(255,111,111,.18)}.settings-form{display:grid!important;gap:14px!important;margin-top:16px!important}.settings-status{padding:12px 14px!important;border:1px solid rgba(17,162,207,.26)!important;border-radius:14px!important;background:linear-gradient(90deg,rgba(17,162,207,.12),rgba(175,207,42,.065)),rgba(0,0,0,.3)!important;color:rgba(231,231,232,.82)!important;font-size:13px}.settings-field{display:grid!important;gap:7px!important;color:rgba(231,231,232,.68)!important;font-size:12px!important;font-weight:800;letter-spacing:.01em}.settings-form input,.settings-form select{min-height:44px!important;border:1px solid rgba(231,231,232,.14)!important;border-radius:14px!important;background:rgba(0,0,0,.52)!important;color:var(--color-text)!important;padding:10px 12px!important;box-shadow:inset 0 1px rgba(255,255,255,.05)!important}.settings-form input:focus,.settings-form select:focus{border-color:rgba(17,162,207,.62)!important;outline:none;box-shadow:0 0 0 3px rgba(17,162,207,.16),inset 0 1px rgba(255,255,255,.07)!important}.settings-grid{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:10px!important}.settings-usage{display:grid!important;gap:5px!important;padding:12px 14px!important;border:1px solid rgba(231,231,232,.12)!important;border-radius:14px!important;background:rgba(231,231,232,.045)!important;color:rgba(231,231,232,.6)!important;font-size:12px!important}.settings-usage strong{color:rgba(231,231,232,.86)}.settings-actions{display:flex!important;justify-content:flex-end!important;gap:10px!important;flex-wrap:wrap!important;padding-top:2px}.settings-actions button{min-height:42px!important;border-radius:999px!important;padding:0 18px!important}.settings-actions button[type=submit]{border-color:rgba(175,207,42,.56)!important;background:linear-gradient(90deg,rgba(175,207,42,.95),rgba(17,162,207,.88))!important;color:#050505!important;font-weight:900!important}.settings-actions [data-settings-test]{border-color:rgba(17,162,207,.36)!important;background:rgba(17,162,207,.08)!important;color:var(--color-text)!important}.settings-form small{color:rgba(231,231,232,.5)!important;font-size:11px!important}@keyframes settings-aura-drift{to{transform:rotate(360deg)}}@media(max-width:760px){.settings-backdrop{padding:18px}.settings-panel{width:calc(100vw - 28px)!important;padding:16px!important}.settings-grid{grid-template-columns:1fr!important}.settings-head strong{font-size:20px}}
.settings-panel{scrollbar-width:none}.settings-panel::-webkit-scrollbar{width:0;height:0}
.render-queue-backdrop{position:fixed!important;inset:0!important;z-index:4900!important;display:grid!important;place-items:center!important;padding:32px;background:radial-gradient(circle at 46% 38%,rgba(17,162,207,.18),transparent 30%),radial-gradient(circle at 63% 62%,rgba(175,207,42,.12),transparent 28%),rgba(0,0,0,.7)!important;backdrop-filter:blur(18px) saturate(1.18)!important;opacity:0;pointer-events:none;transition:opacity 180ms ease}.render-queue-backdrop[hidden]{display:none!important}.render-queue-backdrop.is-open{opacity:1;pointer-events:auto}.render-queue-backdrop.is-closing{opacity:0;pointer-events:none}.render-queue-panel{position:relative;isolation:isolate;width:min(760px,calc(100vw - 56px));max-height:min(780px,calc(100vh - 56px));overflow:hidden;padding:20px;border:1px solid rgba(17,162,207,.34);border-radius:22px;background:linear-gradient(145deg,rgba(231,231,232,.11),rgba(5,5,5,.82) 46%,rgba(11,15,10,.9)),rgba(5,5,5,.94);box-shadow:0 0 0 1px rgba(255,255,255,.055),0 0 42px rgba(17,162,207,.2),0 0 58px rgba(175,207,42,.12),0 32px 86px rgba(0,0,0,.72);transform:translateY(18px) scale(.965);opacity:0;outline:none;transition:transform 210ms cubic-bezier(.2,.9,.2,1),opacity 180ms ease}.render-queue-backdrop.is-open .render-queue-panel{transform:translateY(0) scale(1);opacity:1}.render-queue-aura{position:absolute;inset:-46px;z-index:-1;background:conic-gradient(from 120deg,transparent,rgba(17,162,207,.2),transparent 34%,rgba(175,207,42,.18),transparent 64%);opacity:.48;filter:blur(12px);animation:settings-aura-drift 8.5s linear infinite}.render-queue-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;padding-bottom:16px;border-bottom:1px solid rgba(231,231,232,.1)}.render-queue-head strong{display:block;font-size:22px;line-height:1.05}.render-queue-head p{margin:5px 0 0;color:rgba(231,231,232,.62);font-size:13px}.render-queue-close{display:grid;place-items:center;width:40px;height:40px;min-width:40px;padding:0;border:1px solid rgba(231,231,232,.16);border-radius:14px;background:rgba(231,231,232,.06);color:rgba(231,231,232,.75);font-weight:900}.render-resource-switch{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:16px 0}.render-resource-switch button{min-height:42px;border:1px solid rgba(231,231,232,.16);border-radius:14px;background:rgba(231,231,232,.055);color:rgba(231,231,232,.74);font-weight:900}.render-resource-switch button.active{border-color:rgba(175,207,42,.58);background:linear-gradient(90deg,rgba(175,207,42,.2),rgba(17,162,207,.08));color:var(--color-text);box-shadow:0 0 22px rgba(175,207,42,.14)}.render-queue-status{min-height:42px;padding:12px 14px;border:1px solid rgba(17,162,207,.26);border-radius:14px;background:linear-gradient(90deg,rgba(17,162,207,.12),rgba(175,207,42,.065)),rgba(0,0,0,.3);color:rgba(231,231,232,.82);font-size:13px}.render-queue-list{display:grid;gap:10px;max-height:min(486px,calc(100vh - 288px));margin-top:12px;overflow:auto;padding-right:4px;scrollbar-width:thin;scrollbar-color:rgba(175,207,42,.55) rgba(255,255,255,.055)}.render-queue-list::-webkit-scrollbar{width:8px}.render-queue-list::-webkit-scrollbar-thumb{border-radius:999px;background:linear-gradient(180deg,rgba(17,162,207,.72),rgba(175,207,42,.72))}.render-job-card{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center;padding:13px 14px;border:1px solid rgba(231,231,232,.12);border-radius:16px;background:linear-gradient(180deg,rgba(231,231,232,.07),rgba(231,231,232,.025)),rgba(0,0,0,.34)}.render-job-card[data-status=ready]{border-color:rgba(175,207,42,.38)}.render-job-card[data-status=failed],.render-job-card[data-status=cancelled]{border-color:rgba(255,111,111,.36)}.render-job-main{display:grid;gap:7px;min-width:0}.render-job-title{display:flex;gap:8px;align-items:center;min-width:0}.render-job-title strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.render-job-pill{display:inline-flex;align-items:center;min-height:22px;padding:3px 8px;border-radius:999px;background:rgba(17,162,207,.12);color:rgba(36,220,255,.9);font-size:11px;font-weight:900;text-transform:uppercase}.render-job-card[data-status=cancelled] .render-job-pill,.render-job-card[data-status=failed] .render-job-pill{background:rgba(255,111,111,.12);color:#ff9d9d}.render-job-meta{color:rgba(231,231,232,.58);font-size:12px}.render-job-progress{position:relative;height:5px;overflow:hidden;border-radius:999px;background:rgba(231,231,232,.1)}.render-job-progress span{position:absolute;inset:0 auto 0 0;width:var(--progress);border-radius:inherit;background:linear-gradient(90deg,var(--color-brand-blue),var(--color-brand-green));box-shadow:0 0 14px rgba(17,162,207,.34)}.render-job-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end}.render-job-actions button{min-height:34px;padding:7px 11px;border:1px solid rgba(231,231,232,.16);border-radius:999px;background:rgba(231,231,232,.07);color:rgba(231,231,232,.82);font-weight:800}.render-job-actions button.primary{border-color:rgba(175,207,42,.52);background:rgba(175,207,42,.14);color:var(--color-brand-green)}.render-job-actions [data-render-cancel],.render-job-actions [data-render-remove]{border-color:rgba(255,111,111,.34);background:rgba(255,111,111,.08);color:#ffb3b3}.render-empty{padding:18px;border:1px dashed rgba(231,231,232,.16);border-radius:16px;color:rgba(231,231,232,.58);text-align:center}
.render-cover-frame-toggle{display:flex;gap:10px;align-items:center;margin:-4px 0 14px;padding:10px 12px;border:1px solid rgba(231,231,232,.13);border-radius:14px;background:rgba(231,231,232,.045);color:rgba(231,231,232,.82);cursor:pointer}.render-cover-frame-toggle input{width:18px;height:18px;accent-color:var(--color-brand-green)}.render-cover-frame-toggle span{display:grid;gap:2px}.render-cover-frame-toggle strong{font-size:13px}.render-cover-frame-toggle small{color:rgba(231,231,232,.54);font-size:11px;line-height:1.25}
.workspace-exit-backdrop{position:fixed!important;inset:0!important;z-index:4950!important;display:grid!important;place-items:center!important;padding:32px;background:radial-gradient(circle at 45% 38%,rgba(17,162,207,.18),transparent 30%),radial-gradient(circle at 62% 62%,rgba(175,207,42,.12),transparent 28%),rgba(0,0,0,.72)!important;backdrop-filter:blur(18px) saturate(1.18)!important;opacity:0;pointer-events:none;transition:opacity 180ms ease}.workspace-exit-backdrop[hidden]{display:none!important}.workspace-exit-backdrop.is-open{opacity:1;pointer-events:auto}.workspace-exit-backdrop.is-closing{opacity:0;pointer-events:none}.workspace-exit-panel{position:relative;isolation:isolate;width:min(620px,calc(100vw - 48px));overflow:hidden;padding:20px;border:1px solid rgba(17,162,207,.34);border-radius:22px;background:linear-gradient(145deg,rgba(231,231,232,.11),rgba(5,5,5,.83) 46%,rgba(11,15,10,.9)),rgba(5,5,5,.94);box-shadow:0 0 0 1px rgba(255,255,255,.055),0 0 42px rgba(17,162,207,.2),0 0 58px rgba(175,207,42,.12),0 32px 86px rgba(0,0,0,.72);transform:translateY(18px) scale(.965);opacity:0;outline:none;transition:transform 210ms cubic-bezier(.2,.9,.2,1),opacity 180ms ease}.workspace-exit-backdrop.is-open .workspace-exit-panel{transform:translateY(0) scale(1);opacity:1}.workspace-exit-aura{position:absolute;inset:-46px;z-index:-1;background:conic-gradient(from 120deg,transparent,rgba(17,162,207,.2),transparent 34%,rgba(175,207,42,.18),transparent 64%);opacity:.48;filter:blur(12px);animation:settings-aura-drift 8.5s linear infinite}.workspace-exit-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;padding-bottom:16px;border-bottom:1px solid rgba(231,231,232,.1)}.workspace-exit-head strong{display:block;font-size:22px;line-height:1.05}.workspace-exit-head p,.workspace-exit-body p{margin:5px 0 0;color:rgba(231,231,232,.62);font-size:13px;line-height:1.35}.workspace-exit-body{display:grid;gap:8px;padding:16px 0}.workspace-exit-close{display:grid;place-items:center;width:40px;height:40px;min-width:40px;padding:0;border:1px solid rgba(231,231,232,.16);border-radius:14px;background:rgba(231,231,232,.06);color:rgba(231,231,232,.75);font-weight:900}.workspace-exit-actions{display:flex;justify-content:flex-end;gap:10px;flex-wrap:wrap}.workspace-exit-actions button{min-height:42px;border-radius:999px;padding:0 18px;border:1px solid rgba(231,231,232,.16);background:rgba(231,231,232,.07);color:rgba(231,231,232,.82);font-weight:900}.workspace-exit-actions button.primary{border-color:rgba(175,207,42,.56);background:var(--color-brand-white);color:var(--color-brand-black)}
.header-actions{position:absolute;right:26px;top:50%;display:flex;justify-content:flex-end;align-items:center;gap:10px;width:auto;margin:0;transform:translateY(-50%)}header{grid-template-columns:1fr!important;justify-items:center;padding:18px 26px 2px!important}.header-actions .header-icon-button,#reset-ui.header-icon-button,#finalize-videos.header-icon-button,#open-settings.header-icon-button{width:56px!important;height:56px!important;min-width:56px!important;border-color:rgba(17,162,207,.42)!important;background:linear-gradient(145deg,rgba(17,162,207,.16),rgba(175,207,42,.08) 48%,rgba(5,5,5,.84)),rgba(5,5,5,.88)!important;color:var(--color-text)!important;box-shadow:inset 0 1px rgba(255,255,255,.12),0 0 18px rgba(17,162,207,.12),0 14px 34px rgba(0,0,0,.36)!important;transition:transform 170ms ease,border-color 170ms ease,box-shadow 170ms ease,color 170ms ease!important}.header-actions .header-icon-button:before,#finalize-videos.header-render-button:before,#open-settings.header-settings-button.is-openai-ready:before{background:radial-gradient(circle at 45% 22%,rgba(17,162,207,.24),transparent 58%),radial-gradient(circle at 70% 72%,rgba(175,207,42,.18),transparent 62%)!important;opacity:.66!important;transition:opacity 170ms ease,transform 170ms ease!important}.header-actions .header-icon-button:hover,.header-actions .header-icon-button:focus-visible{border-color:rgba(175,207,42,.7)!important;color:var(--color-text)!important;box-shadow:inset 0 1px rgba(255,255,255,.16),0 0 24px rgba(17,162,207,.24),0 0 26px rgba(175,207,42,.16),0 18px 40px rgba(0,0,0,.42)!important;transform:translateY(-2px) scale(1.035)}.header-actions .header-icon-button:hover:before,.header-actions .header-icon-button:focus-visible:before{opacity:1!important;transform:scale(1.12) rotate(2deg)!important}.header-actions .header-render-button,#finalize-videos.header-render-button{width:56px!important;height:56px!important;min-width:56px!important;animation:none!important}.header-actions .header-render-button svg,#finalize-videos.header-render-button svg{width:30px;height:30px;stroke-width:1.85;animation:none!important;filter:none!important}#open-settings.header-settings-button.is-openai-ready{border-color:rgba(17,162,207,.42)!important;background:linear-gradient(145deg,rgba(17,162,207,.16),rgba(175,207,42,.08) 48%,rgba(5,5,5,.84)),rgba(5,5,5,.88)!important;color:var(--color-text)!important;box-shadow:inset 0 1px rgba(255,255,255,.12),0 0 18px rgba(17,162,207,.12),0 14px 34px rgba(0,0,0,.36)!important}#open-settings.header-settings-button.is-openai-ready svg{animation:cuted-openai-gear-spin 5.8s linear infinite;filter:drop-shadow(0 0 8px rgba(175,207,42,.24))}.header-actions .header-render-button.is-rendering,#finalize-videos.header-render-button.is-rendering{border-color:rgba(175,207,42,.78)!important;background:linear-gradient(180deg,rgba(175,207,42,.2),rgba(17,162,207,.065)),rgba(12,14,9,.72)!important;color:var(--color-brand-green)!important;box-shadow:inset 0 1px rgba(255,255,255,.24),0 0 28px rgba(175,207,42,.34),0 0 42px rgba(17,162,207,.14),0 16px 38px rgba(0,0,0,.36)!important;animation:cuted-render-button-pulse 1.65s ease-in-out infinite!important}.header-actions .header-render-button.is-rendering:before,#finalize-videos.header-render-button.is-rendering:before{background:radial-gradient(circle at 58% 25%,rgba(175,207,42,.28),transparent 60%),radial-gradient(circle at 32% 70%,rgba(17,162,207,.12),transparent 56%)!important;opacity:1!important;transform:scale(1.12);animation:cuted-render-button-scan 1.4s ease-in-out infinite}.header-actions .header-render-button.is-rendering svg,#finalize-videos.header-render-button.is-rendering svg{animation:cuted-render-icon-drift 1.9s ease-in-out infinite!important;filter:drop-shadow(0 0 9px rgba(175,207,42,.42))!important}@media(max-width:1080px){.header-actions{position:static;justify-content:center;width:100%;margin:0;transform:none}.brand-logo{width:min(520px,88vw)}header{grid-template-columns:1fr!important;gap:8px;padding:12px!important}}@media(max-width:860px){.header-actions{justify-content:center;width:100%;margin:0;transform:none}header{grid-template-columns:1fr!important;padding:12px!important}}
.clip-control-surface .cuted-render-zone.is-ready .cuted-ready-region{flex:0 0 46px;width:46px;min-width:46px}.clip-control-surface .cuted-render-zone.is-ready .cuted-ready-pill{width:46px}
.card[open] .editor-shell{grid-template-columns:minmax(210px,260px) minmax(340px,1fr) minmax(260px,330px);gap:14px;align-items:start;padding:0 18px 18px;margin-top:-10px}.card[open] .editor-preview{grid-column:2}.publish-panel{display:grid;gap:10px;align-content:start;min-width:0;max-height:72vh;overflow:auto;padding:12px;border:1px solid rgba(231,231,232,.12);border-radius:12px;background:linear-gradient(180deg,rgba(231,231,232,.075),rgba(231,231,232,.025)),rgba(5,5,5,.52);box-shadow:inset 0 1px rgba(255,255,255,.08),0 12px 34px rgba(0,0,0,.24);backdrop-filter:blur(16px) saturate(1.1)}.publish-panel strong{color:rgba(231,231,232,.72);font-size:11px;letter-spacing:.08em;text-transform:uppercase}.publish-panel h2{margin:0;color:var(--color-text);font-size:17px;line-height:1.18;letter-spacing:0}.publish-panel p{margin:0;color:rgba(231,231,232,.72);font-size:12px;line-height:1.38}.publish-panel small{color:rgba(231,231,232,.5);font-size:11px;line-height:1.34}.publish-cover-frame{position:relative;overflow:hidden;aspect-ratio:9/16;border:1px solid rgba(231,231,232,.1);border-radius:8px;background:#050505}.publish-cover-frame img{display:block;width:100%;height:100%;object-fit:cover}.publish-cover-frame span{display:block;width:100%;height:100%;background:linear-gradient(135deg,rgba(17,162,207,.18),rgba(175,207,42,.08))}.publish-cover-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.publish-cover-options button{min-height:58px;padding:2px;border:1px solid rgba(231,231,232,.14);border-radius:8px;background:rgba(0,0,0,.38);overflow:hidden}.publish-cover-options button.active{border-color:rgba(175,207,42,.82);box-shadow:0 0 0 2px rgba(175,207,42,.16)}.publish-cover-options img{display:block;width:100%;aspect-ratio:9/16;object-fit:cover;border-radius:5px}.publish-hook{padding:9px 10px;border-left:3px solid rgba(175,207,42,.78);border-radius:8px;background:rgba(175,207,42,.075);color:var(--color-text)!important;font-weight:800}.publish-tags{display:flex;gap:6px;flex-wrap:wrap}.publish-tags span{display:inline-flex;align-items:center;min-height:24px;max-width:100%;padding:4px 7px;border:1px solid rgba(17,162,207,.24);border-radius:999px;background:rgba(17,162,207,.09);color:rgba(231,231,232,.84);font-size:11px;line-height:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}@media(max-width:1180px){.card[open] .editor-shell{grid-template-columns:minmax(0,1fr);margin-top:0}.card[open] .editor-preview{grid-column:1}.publish-panel{max-height:none}.publish-cover-panel{grid-row:2}.publish-copy-panel{grid-row:3}.publish-cover-frame{max-width:180px}}@media(max-width:860px){.card[open] .editor-shell{padding:0 12px 16px}.publish-panel{border-radius:10px}.publish-cover-frame{max-width:150px}}
.card[open] .editor-shell{grid-template-columns:minmax(205px,252px) minmax(340px,calc(72vh * 9 / 16)) minmax(260px,330px);gap:8px;align-items:center;justify-content:center}.card[data-preview-format=facebook][open] .editor-shell{grid-template-columns:minmax(205px,252px) minmax(390px,calc(72vh * 4 / 5)) minmax(260px,330px)}.card[data-preview-format=youtube][open] .editor-shell{grid-template-columns:minmax(205px,252px) minmax(520px,720px) minmax(260px,330px)}.publish-panel{gap:9px;align-content:center;align-self:center;padding:11px}.publish-cover-panel{justify-self:end}.publish-copy-panel{justify-self:start}.publish-panel-head{display:flex;justify-content:space-between;gap:10px;align-items:center}.publish-panel-head button{min-height:26px;padding:4px 8px;border-radius:999px;font-size:11px}.publish-field{display:grid;gap:5px;color:rgba(231,231,232,.62);font-size:11px;font-weight:800;letter-spacing:0}.publish-field input,.publish-field textarea{width:100%;min-height:34px;padding:7px 9px;border:1px solid rgba(231,231,232,.14);border-radius:8px;background:rgba(0,0,0,.42);color:var(--color-text);font:inherit;font-size:12px;line-height:1.28;letter-spacing:0}.publish-field textarea{resize:vertical;min-height:72px}.publish-field input:focus,.publish-field textarea:focus{border-color:rgba(17,162,207,.58);outline:0;box-shadow:0 0 0 2px rgba(17,162,207,.16)}@media(max-width:1180px){.card[open] .editor-shell{grid-template-columns:minmax(0,1fr)}.publish-panel{align-content:start}.publish-cover-panel{justify-self:center}.publish-copy-panel{justify-self:stretch}}
.publish-cover-stage{position:relative}.publish-cover-frame{touch-action:none}.publish-cover-frame[data-publish-cover-can-drag="1"]{cursor:grab}.publish-cover-frame[data-publish-cover-dragging="1"]{cursor:grabbing}.publish-cover-frame>img{user-select:none;-webkit-user-drag:none;transform:scale(var(--publish-cover-zoom,1));transform-origin:var(--publish-cover-x,50%) var(--publish-cover-y,50%);transition:transform 120ms ease;will-change:transform}.publish-cover-frame[data-publish-cover-dragging="1"]>img{transition:none}.publish-cover-layer-list{position:absolute;inset:0;z-index:2;pointer-events:none}.publish-cover-layer{position:absolute;display:grid;align-items:center;min-height:24px;padding:5px 7px;border-radius:6px;color:var(--cover-layer-color,#fff);font-weight:800;line-height:1.05;overflow:hidden;text-overflow:ellipsis;cursor:move;pointer-events:auto;touch-action:none}.publish-cover-layer.is-selected{outline:2px solid var(--color-focus);outline-offset:2px}.publish-cover-layer span{overflow:hidden;text-overflow:ellipsis}.publish-cover-layer[data-cover-layer-kind=text]{background:rgba(var(--cover-layer-bg,0,0,0),var(--cover-layer-bg-opacity,.7))}.publish-cover-layer[data-cover-layer-kind=speech]{border-radius:11px;background:rgba(var(--cover-layer-bg,255,255,255),var(--cover-layer-bg-opacity,.94));box-shadow:0 8px 18px rgba(0,0,0,.22);color:var(--cover-layer-color,#050505);font-weight:900;overflow:visible}.publish-cover-layer[data-cover-layer-kind=speech]:after{position:absolute;left:18%;bottom:-8px;width:15px;height:12px;border-radius:0 0 14px 0;background:inherit;content:"";transform:skewX(-18deg)}.publish-cover-layer[data-cover-layer-kind=image]{padding:0;background:transparent}.publish-cover-layer[data-cover-layer-kind=image] img{display:block;width:100%;height:auto;object-fit:contain;transform:none;transform-origin:center;opacity:var(--cover-layer-opacity,1);pointer-events:none}.publish-cover-resize{position:absolute;right:2px;bottom:2px;width:18px;height:18px;padding:0;border:1px solid rgba(255,255,255,.56);border-radius:5px;background:rgba(0,0,0,.34);cursor:nwse-resize}.publish-cover-adjust{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center}.publish-cover-adjust label{display:grid;grid-template-columns:auto 1fr auto;gap:7px;align-items:center;color:rgba(231,231,232,.62);font-size:11px;font-weight:800;letter-spacing:0}.publish-cover-adjust output{min-width:38px;color:rgba(231,231,232,.84);font-size:11px;text-align:right}.publish-cover-adjust input{width:100%;accent-color:var(--color-brand-green)}.publish-cover-adjust button{min-height:28px;padding:4px 8px;border-radius:999px;font-size:11px}.publish-cover-menu{z-index:7;width:min(320px,96%);max-height:min(380px,calc(100vh - 24px))}
.preview-caption-layer{bottom:var(--preview-caption-bottom,16.25%)}.card[data-preview-format=facebook] .preview-caption-layer{bottom:var(--preview-caption-bottom,8.8%)}.card[data-preview-format=youtube] .preview-caption-layer{bottom:var(--preview-caption-bottom,11%)}.preview-caption-layer[data-mode=animated] .preview-caption-window{display:inline-grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:.54em;width:min(94%,18em);padding:0;border-radius:0;background:transparent;color:var(--preview-caption-color,#fff);font-size:calc(var(--preview-caption-size,28px) * .76);line-height:1;text-shadow:0 2px 8px rgba(0,0,0,.75);-webkit-text-stroke:0;white-space:nowrap;box-decoration-break:slice;-webkit-box-decoration-break:slice;animation:cuted-caption-window-step 190ms cubic-bezier(.2,.9,.2,1)}.preview-caption-layer[data-mode=animated] .preview-caption-word{display:inline-grid;place-items:center;min-width:.56em;max-width:100%;padding:.1em .32em;border-radius:.22em;background:var(--preview-caption-bg,transparent);color:var(--preview-caption-color,#fff);font-size:1em;overflow:hidden;text-overflow:ellipsis;box-decoration-break:slice;-webkit-box-decoration-break:slice}.preview-caption-layer[data-mode=animated] .preview-caption-side{opacity:.72;font-size:.76em;transform:translateY(.1em)}.preview-caption-layer[data-mode=animated] .preview-caption-side:empty{min-width:0;padding:0;background:transparent}.preview-caption-layer[data-mode=animated] .preview-caption-prev{justify-self:end}.preview-caption-layer[data-mode=animated] .preview-caption-next{justify-self:start}.preview-caption-layer[data-mode=animated] .preview-caption-active{justify-self:center;max-width:7.4em;padding:.15em .44em;border-radius:.25em;background:var(--preview-caption-highlight-bg,var(--preview-caption-bg,rgba(0,0,0,.82)));color:var(--preview-caption-color,#fff);font-size:1em;box-shadow:0 8px 22px rgba(0,0,0,.34),0 0 0 1px rgba(255,255,255,.12);animation:cuted-caption-pop 220ms cubic-bezier(.2,.9,.2,1)}@keyframes cuted-caption-pop{0%{opacity:.72;transform:translateY(7px) scale(.88)}64%{opacity:1;transform:translateY(-5px) scale(1.12)}100%{opacity:1;transform:translateY(0) scale(1)}}@keyframes cuted-caption-window-step{0%{transform:translateX(.18em);filter:blur(.8px)}100%{transform:translateX(0);filter:blur(0)}}
.overlay-menu[data-overlay-menu-mode=add]{display:block;width:max-content;min-width:0;max-width:calc(100vw - 28px);max-height:none;overflow:visible;padding:6px;border-radius:999px;background:linear-gradient(135deg,rgba(17,162,207,.16),rgba(175,207,42,.08)),rgba(5,5,5,.9);box-shadow:0 12px 30px rgba(0,0,0,.42),0 0 18px rgba(17,162,207,.18);backdrop-filter:blur(18px) saturate(1.16)}.overlay-menu[data-overlay-menu-mode=add] .overlay-icon-actions{display:flex;gap:6px;align-items:center}.overlay-icon-action{display:grid!important;place-items:center;width:38px;height:38px;min-width:38px;min-height:38px;padding:0!important;border-radius:12px!important;background:rgba(231,231,232,.075)!important;color:rgba(231,231,232,.9)!important;font-size:11px!important;font-weight:950!important;letter-spacing:0!important;line-height:1!important}.overlay-icon-action:hover,.overlay-icon-action:focus-visible{border-color:rgba(175,207,42,.68)!important;color:var(--color-brand-green)!important;box-shadow:0 0 16px rgba(175,207,42,.2)}.overlay-icon-close{width:30px!important;height:30px!important;min-width:30px!important;min-height:30px!important;border-radius:999px!important;color:rgba(231,231,232,.68)!important;font-size:14px!important}.overlay-icon-close:hover,.overlay-icon-close:focus-visible{border-color:rgba(255,111,111,.5)!important;color:#ffb2b2!important;box-shadow:0 0 16px rgba(255,111,111,.16)!important}.overlay-menu[hidden],.publish-cover-menu[hidden]{display:none!important}.publish-cover-menu[data-overlay-menu-mode=add]{width:max-content;max-height:none}.clip-control-surface .cuted-control-bar{min-height:82px}.clip-control-surface .cuted-render-zone{min-height:58px}.clip-control-surface .cuted-tool-group{flex-basis:330px;min-height:58px}.clip-control-surface .cuted-tile-button{flex-basis:54px;width:54px;height:50px;font-size:24px}.card[open] .clip-row-timeline.preview-camera-timeline--live .timeline-shell{min-height:214px}.card[open] .clip-row-timeline.preview-camera-timeline--live{min-height:216px;margin:-10px 0 0}
"""


def js() -> str:
    return """
function galleryStorageKey(name){
  return `${name}:${currentGalleryPath() || window.location.pathname || "root"}`;
}
const editorStateStorageKey = galleryStorageKey("cutted-state");
const editorTabStorageKey = galleryStorageKey("cutted-tab");
if (new URLSearchParams(location.search).has("reset")) {
  localStorage.removeItem(editorStateStorageKey);
  localStorage.removeItem(editorTabStorageKey);
  localStorage.removeItem("cutted-state");
  localStorage.removeItem("cutted-tab");
  localStorage.removeItem("cutted-empty-gallery");
  history.replaceState(null, "", location.pathname);
}
const state = JSON.parse(localStorage.getItem(editorStateStorageKey) || "{}");
const emptyGalleryStorageKey = "cutted-empty-gallery";
const maxOverlayImageBytes = 1800000;
const maxOverlayImageSourceBytes = 6000000;
const maxOverlayImagePixels = 1600;
const coverLayerVerticalLift = .30;
const maxBumperVideoBytes = 48000000;
const cameraAnalysisFetchTimeoutMs = 180000;
const cameraReadinessPollMs = 3500;
function save(){
  try {
    localStorage.setItem(editorStateStorageKey, JSON.stringify(state));
    clearAppNotice();
    return true;
  } catch (error) {
    showAppNotice("A imagem ficou pesada demais para salvar nesta tela. Remova ou use uma versao menor antes de continuar.");
    console.warn("CUTED state was not saved", error);
    return false;
  }
}
function showAppNotice(message){
  let notice = document.querySelector("[data-app-notice]");
  if (!notice) {
    notice = document.createElement("div");
    notice.dataset.appNotice = "";
    notice.className = "app-notice";
    document.body.prepend(notice);
  }
  notice.textContent = message;
  notice.hidden = false;
}
function clearAppNotice(){
  const notice = document.querySelector("[data-app-notice]");
  if (notice) notice.hidden = true;
}
function cardState(rank){
  const raw = state[rank];
  if (typeof raw === "string") return { status: raw, trimStart: 0, trimEnd: 0, platforms: [], camera: defaultCamera(), camera_path: [], director_plan: null, cameraMotionMs: defaultCameraMotionMs, effect: defaultEffect(), overlay: defaultOverlay(), overlays: [], bumpers: defaultBumpers(), platformEdits: {}, publish: {} };
  const next = Object.assign({ status: null, trimStart: 0, trimEnd: 0, platforms: [], camera: defaultCamera(), camera_path: [], director_plan: null, cameraMotionMs: defaultCameraMotionMs, effect: defaultEffect(), overlay: defaultOverlay(), overlays: [], bumpers: defaultBumpers(), platformEdits: {}, publish: {} }, raw || {});
  next.platforms = next.status === "discarded" ? [] : uniquePlatforms(next.platforms);
  next.camera = normalizeCamera(next.camera);
  next.director_plan = normalizeDirectorPlan(next.director_plan);
  next.effect = normalizeEffect(next.effect);
  next.overlay = normalizeOverlay(next.overlay);
  next.overlays = normalizeOverlayLayers(next.overlays, next.overlay);
  next.bumpers = normalizeBumpers(next.bumpers);
  next.cameraMotionMs = normalizeCameraMotionMs(next.cameraMotionMs);
  next.platformEdits = normalizePlatformEdits(next.platformEdits, next);
  next.publish = normalizePublishEdit(next.publish);
  return next;
}
function setCardState(rank, patch){ state[rank] = Object.assign(cardState(rank), patch); save(); }
function normalizeCameraMotionMs(value){
  const raw = Number(value || defaultCameraMotionMs);
  return Math.round(Math.max(350, Math.min(raw, 1400)) / 50) * 50;
}
function fixed(value){ return `${Number(value || 0).toFixed(1)}s`; }
const platformMeta = {
  tiktok: { label: "TikTok", width: 1080, height: 1920, resolution_preset: "vertical_9_16" },
  shorts: { label: "Shorts", width: 1080, height: 1920, resolution_preset: "vertical_9_16" },
  instagram: { label: "Instagram", width: 1080, height: 1920, resolution_preset: "vertical_9_16" },
  facebook: { label: "Facebook", width: 1080, height: 1350, resolution_preset: "vertical_4_5" },
  youtube: { label: "YouTube", width: 1920, height: 1080, resolution_preset: "horizontal_16_9" }
};
const resolutionPresets = {
  vertical_9_16: { label: "Vertical 9:16", width: 1080, height: 1920, platform: "tiktok", destinations: ["tiktok", "shorts", "instagram"] },
  vertical_4_5: { label: "Vertical 4:5", width: 1080, height: 1350, platform: "facebook", destinations: ["facebook"] },
  horizontal_16_9: { label: "Horizontal 16:9", width: 1920, height: 1080, platform: "youtube", destinations: ["youtube"] }
};
const defaultPreviewVolume = 0.2;
const defaultCameraMotionMs = 700;
const effectMeta = {
  none: { label: "Sem efeito", note: "Preview limpo" },
  "light-grain": { label: "Chuvisco Leve", note: "Granulado sutil" },
  "old-film": { label: "Filme Antigo", note: "Vintage com vinheta" },
  vhs: { label: "VHS / TV Antiga", note: "Ruido analogico" },
  "bw-old": { label: "Preto e Branco Antigo", note: "P&B com grao" }
};
const cameraMeta = {
  center: { label: "Centro manual", note: "Crop limpo no centro", x: 50, scale: 1 },
  "face-center": { label: "Centro + zoom manual", note: "Zoom leve no centro", x: 50, scale: 1.1 },
  "face-left": { label: "Esquerda manual", note: "Prioriza o lado esquerdo", x: 22, scale: 1 },
  "face-right": { label: "Direita manual", note: "Prioriza o lado direito", x: 78, scale: 1 },
  alternate: { label: "Alternar manual", note: "Pan suave entre lados", x: 50, scale: 1 },
  "jump-cut": { label: "Corte manual", note: "Troca seca entre lados", x: 50, scale: 1 },
  "fit-blur": { label: "Fit com blur", note: "Quadro inteiro com fundo desfocado", x: 50, scale: 1 },
  "soft-zoom": { label: "Zoom sutil", note: "Aproxima sem trocar o foco", x: 50, scale: 1.12 },
  "punch-in": { label: "Punch-in", note: "Mais fechado e energetico", x: 50, scale: 1.22 }
};
const manualAlternateHoldSeconds = 3.5;
const manualAlternateMoveSeconds = 1.2;
const smartCameraModes = {
  "auto-director": { label: "Auto Director", note: "Escolhe o enquadramento usando rosto principal e contexto multi-rosto", featured: true },
  "ai-director": { label: "IA", note: "Direcao automatica por IA com mapa visual local", featured: true },
  "ai-director-group": { label: "AI Grupo", note: "Preserva duas ou mais pessoas antes de fechar em close" },
  "ai-director-speaker": { label: "AI Fala", note: "Prioriza quem parece conduzir o trecho sem cortar contexto" },
  "ai-director-reactions": { label: "AI Reacoes", note: "Alterna foco entre pessoas visiveis com pausas editoriais" },
  "ai-director-cuts": { label: "AI Cortes", note: "Troca enquadramentos em cortes secos com pausas editoriais" },
  "follow-face": { label: "Seguir rosto", note: "Acompanha o rosto principal detectado" },
  "stable-face": { label: "Mais estavel", note: "Trava no enquadramento medio do rosto" },
  "face-zoom": { label: "Mais close", note: "Aproxima usando deteccao real" }
};
const cameraParts = [
  { key: "start", label: "Inicio" },
  { key: "middle", label: "Meio" },
  { key: "end", label: "Fim" }
];
const overlayMeta = {
  none: { label: "Sem chamada", title: "", subtitle: "", accent: "#000000" },
  subscribe: { label: "Inscreva-se", title: "Inscreva-se", subtitle: "Novos cortes toda semana", accent: "#ff3b30" },
  follow: { label: "Siga-nos", title: "Siga-nos", subtitle: "Mais cortes no perfil", accent: "#AFCF2A" },
  description: { label: "Veja a descricao", title: "Veja a descricao", subtitle: "Link e contexto completo", accent: "#4da3ff" },
  "like-share": { label: "Curta e compartilhe", title: "Curta e compartilhe", subtitle: "Mostre para alguem", accent: "#ffd166" },
  "pinned-comment": { label: "Comentario fixado", title: "Comentario fixado", subtitle: "Detalhes no primeiro comentario", accent: "#b388ff" },
  watermark: { label: "Marca d'agua", title: "CUTED", subtitle: "clip selecionado", accent: "#E7E7E8" }
};
function applyTab(tab){
  const next = ["import", "edit", "final"].includes(tab) ? tab : "edit";
  document.body.dataset.tab = next;
  localStorage.setItem(editorTabStorageKey, next);
  document.querySelectorAll(".tabs [data-tab]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === next);
  });
  renderFinalStage();
  if (next === "final") restoreFinalizeResults();
}
function platformLabel(key){
  return resolutionPresetLabel(resolutionPresetForPlatform(key));
}
function validPlatform(format){
  return Object.prototype.hasOwnProperty.call(platformMeta, format) ? format : "tiktok";
}
function resolutionPresetForPlatform(platform){
  const key = platformMeta[validPlatform(platform)]?.resolution_preset || "vertical_9_16";
  return resolutionPresets[key] ? key : "vertical_9_16";
}
function resolutionPresetLabel(key){
  return (resolutionPresets[key] || resolutionPresets.vertical_9_16).label;
}
function platformForResolutionPreset(key){
  return validPlatform((resolutionPresets[key] || resolutionPresets.vertical_9_16).platform);
}
function representativePlatform(platform){
  return platformForResolutionPreset(resolutionPresetForPlatform(platform));
}
function destinationResolutionMap(){
  return Object.fromEntries(Object.keys(platformMeta).map(platform => [platform, resolutionPresetForPlatform(platform)]));
}
function activePlatformForRank(rank){
  const card = cardForRank(rank);
  return validPlatform(card?.dataset.previewFormat || document.body.dataset.format || "tiktok");
}
function normalizePlatformEdit(edit, fallback){
  const source = edit && typeof edit === "object" ? edit : {};
  const base = fallback && typeof fallback === "object" ? fallback : {};
  const overlayFallback = source.overlay || base.overlay || defaultOverlay();
  const overlays = normalizeOverlayLayers(source.overlays, overlayFallback);
  const pathSource = Object.prototype.hasOwnProperty.call(source, "camera_path") ? source.camera_path : base.camera_path;
  const captionSource = Object.prototype.hasOwnProperty.call(source, "captions") ? source.captions : null;
  const captionBase = Object.prototype.hasOwnProperty.call(base, "captions") ? base.captions : null;
  const captionLanguageSource = Object.prototype.hasOwnProperty.call(source, "captionLanguage") ? source.captionLanguage : source.caption_language;
  const captionLanguageBase = Object.prototype.hasOwnProperty.call(base, "captionLanguage") ? base.captionLanguage : base.caption_language;
  return {
    camera: normalizeCamera(source.camera || base.camera || defaultCamera()),
    camera_path: normalizeCameraPath(pathSource),
    captions: normalizeCaptionSettings(captionSource, captionBase),
    captionLanguage: normalizeCaptionLanguage(captionLanguageSource || captionLanguageBase || defaultCaptionLanguage()),
    director_plan: normalizeDirectorPlan(source.director_plan || base.director_plan),
    effect: normalizeEffect(source.effect || base.effect || defaultEffect()),
    overlay: overlays.find(layer => layer.kind !== "image") || defaultOverlay(),
    overlays,
    bumpers: normalizeBumpers(source.bumpers || base.bumpers || defaultBumpers())
  };
}
function normalizePlatformEdits(edits, fallback){
  if (!edits || typeof edits !== "object") return {};
  return Object.fromEntries(Object.entries(edits)
    .filter(([key]) => platformMeta[key])
    .map(([key, edit]) => [key, normalizePlatformEdit(edit, fallback)]));
}
function platformEditForRank(rank, platform = activePlatformForRank(rank)){
  const current = cardState(String(rank));
  return normalizePlatformEdit(current.platformEdits[validPlatform(platform)], current);
}
function setPlatformEditForRank(rank, platform, patch){
  const key = validPlatform(platform);
  const current = cardState(String(rank));
  const edit = normalizePlatformEdit(Object.assign({}, platformEditForRank(rank, key), patch), current);
  setCardState(String(rank), {
    platformEdits: Object.assign({}, current.platformEdits, { [key]: edit })
  });
}
function defaultCaptionSettings(){
  return { enabled: captionEnabled(), style: captionStyle() };
}
function defaultCaptionLanguage(){
  return "pt-BR";
}
function normalizeCaptionLanguage(value){
  const text = String(value || "").trim().toLowerCase().replace("_", "-");
  if (["en", "eng", "english", "ingles"].includes(text)) return "en";
  return "pt-BR";
}
function normalizeCaptionTracks(value, fallbackSegments = []){
  const source = value && typeof value === "object" ? value : {};
  const tracks = {};
  ["pt-BR", "en"].forEach(language => {
    const aliases = language === "pt-BR" ? ["pt-BR", "pt", "pt_br", "pt-BR".toLowerCase()] : ["en", "eng", "english"];
    const raw = aliases.map(key => source[key]).find(item => item && typeof item === "object");
    if (raw) {
      tracks[language] = Object.assign({}, raw, {
        language,
        label: raw.label || (language === "pt-BR" ? "PT-BR" : "EN"),
        status: raw.status || (Array.isArray(raw.segments) && raw.segments.length ? "ready" : "unavailable"),
        segments: Array.isArray(raw.segments) ? raw.segments : []
      });
    }
  });
  if (!tracks["pt-BR"]) {
    tracks["pt-BR"] = {
      language: "pt-BR",
      label: "PT-BR",
      status: "ready",
      source: "legacy_caption_segments",
      segments: Array.isArray(fallbackSegments) ? fallbackSegments : []
    };
  }
  if (!tracks.en) {
    tracks.en = { language: "en", label: "EN", status: "unavailable", source: "not_generated", segments: [] };
  }
  return tracks;
}
function captionTrackForMoment(moment, language){
  const tracks = normalizeCaptionTracks(moment?.caption_tracks, moment?.caption_segments || []);
  return tracks[normalizeCaptionLanguage(language)] || tracks["pt-BR"];
}
function captionTrackAvailable(moment, language){
  const track = captionTrackForMoment(moment, language);
  return Boolean(track && track.status === "ready" && Array.isArray(track.segments) && track.segments.length);
}
function captionSegmentsForMoment(moment, language){
  const track = captionTrackForMoment(moment, language);
  if (track?.status === "ready" && Array.isArray(track.segments)) return track.segments;
  return Array.isArray(moment?.caption_segments) ? moment.caption_segments : [];
}
function captionLanguageOptionsForMoment(moment){
  return { "pt-BR": true, en: captionTrackAvailable(moment, "en") };
}
function normalizeCaptionSettings(value, fallback = null){
  const source = value && typeof value === "object" ? value : {};
  const base = fallback && typeof fallback === "object" ? fallback : defaultCaptionSettings();
  const style = normalizeCaptionStyleObject(Object.assign({}, base.style || {}, source.style || {}));
  const enabled = Object.prototype.hasOwnProperty.call(source, "enabled")
    ? Boolean(source.enabled)
    : Object.prototype.hasOwnProperty.call(base, "enabled")
      ? Boolean(base.enabled)
      : captionEnabled();
  return {
    enabled: style.mode === "off" ? false : enabled,
    style: Object.assign(style, { mode: enabled ? style.mode === "off" ? "on" : style.mode : "off" })
  };
}
function normalizeCaptionStyleObject(value){
  const source = value && typeof value === "object" ? value : {};
  const backgroundColor = normalizeCaptionBackground(source.backgroundColor || source.background_color);
  return {
    size: clampNumber(Number(source.size || defaultCaptionSize()), 24, 140),
    width: clampNumber(Number(source.width || 28), 12, 56),
    bottom: clampNumber(Number(source.bottom || source.height || defaultCaptionBottom()), 6, 32),
    mode: normalizeCaptionMode(source.mode || source.captionMode),
    textColor: normalizeCaptionColor(source.textColor || source.text_color, "#ffffff"),
    backgroundColor,
    highlightBackgroundColor: normalizeCaptionHighlightBackground(
      source.highlightBackgroundColor || source.highlight_background_color || source.activeBackgroundColor || source.active_background_color || backgroundColor
    )
  };
}
function normalizeCaptionMode(value){
  const mode = String(value || "").trim().toLowerCase();
  if (mode === "animated" || mode === "animada") return "animated";
  if (mode === "on" || mode === "static") return "on";
  if (mode === "off" || mode === "false" || mode === "0") return "off";
  return "on";
}
function defaultCamera(){ return cameraSequence(cameraParts.map(part => defaultCameraSegment(part.key))); }
function defaultCameraSegment(part){ return { part, part_label: cameraPartLabel(part), key: "center", label: cameraMeta.center.label, strength: 60 }; }
function cameraPartLabel(part){ return (cameraParts.find(item => item.key === part) || { label: part }).label; }
function cameraSequence(segments){ return { key: "sequence", label: "Linha de camera", strength: 60, segments }; }
function normalizeCamera(camera){
  if (camera?.key === "sequence" || Array.isArray(camera?.segments)) {
    const source = Array.isArray(camera?.segments) ? camera.segments : [];
    return cameraSequence(cameraParts.map(part => normalizeCameraSegment(source.find(item => item?.part === part.key), part.key)));
  }
  const base = normalizeSingleCamera(camera);
  return cameraSequence(cameraParts.map(part => Object.assign({ part: part.key, part_label: part.label }, base)));
}
function cameraLabel(camera){
  const current = normalizeCamera(camera);
  const active = current.segments.filter(segment => segment.key !== "center");
  if (!active.length) return cameraMeta.center.label;
  return active.map(segment => `${segment.part_label}: ${segment.label}`).join(" | ");
}
function cameraEditLabel(edit, duration){
  const path = normalizeCameraPath(edit?.camera_path);
  const shots = normalizeDirectorPlan(edit?.director_plan).shots;
  if (path.length && shots.length) return `Director plan: ${shots.length} cenas`;
  if (path.length) return `Camera path: ${path.length} pontos`;
  return cameraLabel(edit?.camera || defaultCamera());
}
function cameraForRank(rank, platform = activePlatformForRank(rank)){ return platformEditForRank(rank, platform).camera; }
function updateCardCameraSummary(card, camera, edit = null){
  const summary = card?.querySelector("[data-camera-current]");
  if (summary) {
    const context = card ? cameraContextForCard(card) : { duration: 0 };
    summary.textContent = edit ? cameraEditLabel(edit, context.duration) : cameraLabel(camera);
  }
}
function setCameraSegmentForRank(rank, part, patch, platform = activePlatformForRank(rank)){
  const targetPlatform = validPlatform(platform);
  const camera = cameraForRank(rank, targetPlatform);
  const segments = camera.segments.map(segment => {
    if (segment.part !== part) return segment;
    return normalizeCameraSegment(Object.assign({}, segment, patch), part);
  });
  setPlatformEditForRank(rank, targetPlatform, { camera: cameraSequence(segments), camera_path: [], director_plan: null });
  const card = cardForRank(rank);
  if (card) {
    const nextCamera = cameraForRank(rank, activePlatformForRank(rank));
    updateCardCameraSummary(card, nextCamera);
    updateCameraSurfaceForCard(card);
  }
  renderFinalStage();
}
function cameraPathHasMovement(path){
  return normalizeCameraPath(path).some(frame => Math.abs(Number(frame.x || 50) - 50) > .2 || Math.abs(Number(frame.zoom || 1) - 1) > .002 || frame.key && frame.key !== "center");
}
function cameraEditHasMovement(edit){
  const path = normalizeCameraPath(edit?.camera_path);
  return path.length ? cameraPathHasMovement(path) : cameraHasMovement(edit?.camera || defaultCamera());
}
function normalizeSingleCamera(camera){
  const key = cameraMeta[camera?.key] ? camera.key : "center";
  const strength = Math.max(0, Math.min(Number(camera?.strength ?? 60), 100));
  return { key, label: cameraMeta[key].label, strength };
}
function normalizeCameraSegment(segment, part){
  const current = normalizeSingleCamera(segment);
  return Object.assign({ part, part_label: cameraPartLabel(part) }, current);
}
function normalizeCameraPath(path){
  const source = Array.isArray(path) ? path : Array.isArray(path?.keyframes) ? path.keyframes : [];
  return source.map(frame => normalizeCameraPathFrame(frame)).filter(Boolean).sort((a, b) => a.time - b.time);
}
function normalizeCameraPathFrame(frame){
  if (!frame || typeof frame !== "object") return null;
  const time = Math.max(0, Number(frame.time ?? frame.t ?? 0));
  const key = cameraMeta[frame.key] ? frame.key : cameraMeta[frame.camera_key] ? frame.camera_key : null;
  const strength = Math.max(0, Math.min(Number(frame.strength ?? 60), 100));
  const base = key ? normalizeSingleCamera({ key, strength }) : null;
  const x = Math.max(0, Math.min(Number(frame.x ?? (base ? cameraCropPercent(base, time) : 50)), 100));
  const y = Math.max(0, Math.min(Number(frame.y ?? 50), 100));
  const zoom = Math.max(1, Math.min(Number(frame.zoom ?? (base ? cameraScaleValue(base) : 1)), 2));
  return {
    time: Number(time.toFixed(3)),
    x: Number(x.toFixed(2)),
    y: Number(y.toFixed(2)),
    zoom: Number(zoom.toFixed(3)),
    fit: String(frame.fit || "").toLowerCase() === "contain" || String(frame.source || "").includes("group-fit") ? "contain" : undefined,
    source: String(frame.source || (key ? "manual-segment" : "manual-path")),
    confidence: Math.max(0, Math.min(Number(frame.confidence ?? 1), 1)),
    intent: frame.intent ? String(frame.intent) : undefined,
    reason: frame.reason ? String(frame.reason) : undefined,
    transition: frame.transition ? String(frame.transition) : undefined,
    part: frame.part ? String(frame.part) : undefined,
    key: key || undefined,
    label: frame.label ? String(frame.label) : key ? cameraMeta[key].label : undefined,
    strength: key ? strength : undefined
  };
}
function normalizeDirectorPlan(plan){
  if (!plan || typeof plan !== "object") return { version: 1, source: "none", resolution_preset: "vertical_9_16", shots: [] };
  const shots = Array.isArray(plan.shots) ? plan.shots.map(normalizeDirectorShot).filter(Boolean) : [];
  return {
    version: Number(plan.version || 1),
    source: String(plan.source || "director-plan"),
    mode: String(plan.mode || ""),
    resolution_preset: resolutionPresets[plan.resolution_preset] ? plan.resolution_preset : "vertical_9_16",
    style: String(plan.style || "normal"),
    energy: String(plan.energy || "normal"),
    shots
  };
}
function normalizeDirectorShot(shot){
  if (!shot || typeof shot !== "object") return null;
  const start = Math.max(0, Number(shot.start || 0));
  const end = Math.max(start, Number(shot.end || start));
  const label = String(shot.label || directorIntentLabel(shot.intent || "speaker_hold"));
  return {
    id: String(shot.id || `shot-${Math.round(start * 1000)}`),
    start: Number(start.toFixed(3)),
    end: Number(end.toFixed(3)),
    intent: String(shot.intent || "speaker_hold"),
    label,
    subject: String(shot.subject || "primary"),
    transition: String(shot.transition || "hold"),
    reason: String(shot.reason || "")
  };
}
function directorPlanFromCameraPath(path, duration, platform, source = "manual"){
  const frames = normalizeCameraPath(path);
  const safeDuration = Math.max(Number(duration) || 0, .3);
  const shots = (frames.length ? frames : [normalizeCameraPathFrame({ time: 0, x: 50, y: 50, zoom: 1 })])
    .map((frame, index, sourceFrames) => directorShotFromFrame(frame, index, sourceFrames, safeDuration));
  return { version: 1, source, mode: "", resolution_preset: resolutionPresetForPlatform(platform), style: "normal", energy: "normal", shots };
}
function directorShotFromFrame(frame, index, frames, duration){
  const start = clampNumber(Number(frame.time || 0), 0, duration);
  const next = frames[index + 1];
  const end = next ? clampNumber(Number(next.time || duration), start, duration) : duration;
  const intent = frame.intent || directorIntentFromFrame(frame);
  return { id: `shot-${String(index + 1).padStart(3, "0")}`, start, end, intent, label: directorIntentLabel(intent), subject: directorSubject(intent), transition: directorTransition(frame, intent), reason: frame.reason || directorReason(intent) };
}
function directorIntentFromFrame(frame){
  const source = String(frame?.source || "");
  if (cameraFrameUsesGroupFit(frame) || source.includes("group")) return "group_open";
  if (source.includes("reaction")) return "reaction_focus";
  if (source.includes("cuts")) return "cut_focus";
  return Number(frame?.zoom || 1) >= 1.18 ? "speaker_close" : "speaker_hold";
}
function directorIntentLabel(intent){
  return {
    group_open: "Group",
    reaction_focus: "Reaction",
    cut_focus: "Cut",
    center_hold: "Center",
    speaker_close: "Zoom",
    speaker_hold: "Speaker"
  }[intent] || "Camera";
}
function directorSubject(intent){
  if (intent === "group_open") return "group";
  if (intent === "reaction_focus") return "secondary";
  if (intent === "center_hold") return "center";
  return "primary";
}
function directorTransition(frame, intent){
  if (intent === "cut_focus" || cameraFrameUsesHardCut(frame)) return "cut";
  return ["group_open", "speaker_hold", "center_hold"].includes(intent) ? "hold" : "smooth";
}
function directorReason(intent){
  return {
    group_open: "Preserva o grupo.",
    reaction_focus: "Realca reacao.",
    cut_focus: "Corte seco para ritmo.",
    center_hold: "Volta para o centro seguro.",
    speaker_close: "Aproxima o foco.",
    speaker_hold: "Segura foco estavel."
  }[intent] || "";
}
function directorIntentOptions(){
  return [
    { intent: "speaker_hold", label: "Speaker" },
    { intent: "group_open", label: "Group" },
    { intent: "reaction_focus", label: "Reaction" },
    { intent: "center_hold", label: "Center" },
    { intent: "speaker_close", label: "Zoom" },
    { intent: "cut_focus", label: "Hard cut" }
  ];
}
function directorIntentOptionsHtml(selectedIntent){
  return directorIntentOptions().map(item => {
    const selected = item.intent === selectedIntent ? " selected" : "";
    return `<option value="${escapeAttr(item.intent)}"${selected}>${escapeHtml(item.label)}</option>`;
  }).join("");
}
function cameraFramePatchForIntent(intent, frame){
  const current = normalizeCameraPathFrame(frame) || normalizeCameraPathFrame({ time: 0, x: 50, y: 50, zoom: 1 });
  const base = { intent, label: directorIntentLabel(intent), reason: directorReason(intent), transition: directorTransition(current, intent), key: undefined, strength: undefined };
  if (intent === "group_open") return Object.assign({}, current, base, { x: 50, y: 50, zoom: 1, fit: "contain", source: "manual-director-group" });
  if (intent === "reaction_focus") {
    const x = Number(current.x || 50) <= 50 ? 72 : 28;
    return Object.assign({}, current, base, { x, y: 50, zoom: 1.14, fit: undefined, source: "manual-director-reaction" });
  }
  if (intent === "cut_focus") return Object.assign({}, current, base, { zoom: Math.max(Number(current.zoom || 1.12), 1.12), fit: undefined, source: "ai-director-cuts-manual" });
  if (intent === "center_hold") return Object.assign({}, current, base, { x: 50, y: 50, zoom: 1, fit: undefined, source: "manual-director-center" });
  if (intent === "speaker_close") return Object.assign({}, current, base, { zoom: Math.max(Number(current.zoom || 1), 1.22), fit: undefined, source: "manual-director-zoom" });
  return Object.assign({}, current, base, { zoom: Math.max(Number(current.zoom || 1), 1.08), fit: undefined, source: "manual-director-speaker" });
}
function directorShotForFrame(plan, frame){
  const shots = normalizeDirectorPlan(plan).shots;
  const time = Number(frame?.time || 0);
  return shots.find(shot => Math.abs(Number(shot.start || 0) - time) < .16) || null;
}
function directorMarkerLabel(plan, frame){
  const shot = directorShotForFrame(plan, frame);
  if (shot?.label) return shot.label;
  if (frame?.label) return frame.label;
  if (frame?.key) return cameraMeta[frame.key]?.label || "Camera";
  return directorIntentLabel(directorIntentFromFrame(frame));
}
function directorMarkerTitle(plan, frame){
  const shot = directorShotForFrame(plan, frame);
  const label = directorMarkerLabel(plan, frame);
  const detail = shot?.reason ? ` - ${shot.reason}` : "";
  return `${fixed(frame?.time || 0)} - ${label}${detail}`;
}
function cameraCropPercent(camera, elapsed = 0){
  const current = normalizeSingleCamera(camera);
  const strength = current.strength;
  if (current.key === "face-left") return clampNumber((0.22 - strength * 0.0012) * 100, 0, 100);
  if (current.key === "face-right") return clampNumber((0.78 + strength * 0.0012) * 100, 0, 100);
  if (current.key === "alternate") {
    const amplitude = 0.12 + (strength / 100) * 0.22;
    return manualAlternateCropPercent(0.5 - amplitude, 0.5 + amplitude, Number(elapsed || 0));
  }
  if (current.key === "jump-cut") {
    const left = 0.22 - strength * 0.0012;
    const right = 0.78 + strength * 0.0012;
    return clampNumber((Number(elapsed || 0) % 6 < 3 ? left : right) * 100, 0, 100);
  }
  return 50;
}
function manualAlternateCropPercent(left, right, elapsed){
  const hold = manualAlternateHoldSeconds;
  const move = manualAlternateMoveSeconds;
  const cycle = (hold + move) * 2;
  const phase = positiveModulo(elapsed, cycle);
  let ratio = left;
  if (phase < hold) ratio = left;
  else if (phase < hold + move) ratio = easedCameraRatio(left, right, (phase - hold) / move);
  else if (phase < hold + move + hold) ratio = right;
  else ratio = easedCameraRatio(right, left, (phase - hold - move - hold) / move);
  return clampNumber(ratio * 100, 0, 100);
}
function easedCameraRatio(start, end, progress){
  const amount = (1 - Math.cos(Math.PI * clampNumber(progress, 0, 1))) / 2;
  return start + (end - start) * amount;
}
function positiveModulo(value, size){
  return ((Number(value || 0) % size) + size) % size;
}
function cameraScaleValue(camera){
  const current = normalizeSingleCamera(camera);
  const strength = current.strength;
  if (current.key === "face-center") return 1.06 + (strength / 100) * 0.08;
  if (current.key === "soft-zoom") return 1.04 + (strength / 100) * 0.10;
  if (current.key === "punch-in") return 1.12 + (strength / 100) * 0.16;
  return 1;
}
function cameraSegmentForTime(camera, position, duration){
  const current = normalizeCamera(camera);
  const safeDuration = Math.max(Number(duration) || 0, .3);
  const segmentDuration = safeDuration / cameraParts.length;
  const safePosition = clampNumber(Number(position) || 0, 0, Math.max(safeDuration - .001, 0));
  const index = Math.min(cameraParts.length - 1, Math.max(0, Math.floor(safePosition / segmentDuration)));
  const part = cameraParts[index] || cameraParts[0];
  const segment = current.segments.find(item => item.part === part.key) || defaultCameraSegment(part.key);
  return { segment, elapsed: Math.max(0, safePosition - segmentDuration * index) };
}
function cameraFrameFromSegment(segment, time, elapsed){
  const current = normalizeCameraSegment(segment, segment.part || "start");
  const frame = {
    time: Number(Math.max(0, Number(time) || 0).toFixed(3)),
    x: Number(cameraCropPercent(current, elapsed).toFixed(2)),
    y: 50,
    zoom: Number(cameraScaleValue(current).toFixed(3)),
    source: "manual-segment",
    confidence: 1,
    part: current.part,
    key: current.key,
    label: current.label,
    strength: current.strength
  };
  if (current.key === "fit-blur") frame.fit = "contain";
  return frame;
}
function cameraPathFromCamera(camera, duration){
  const current = normalizeCamera(camera);
  const safeDuration = Math.max(Number(duration) || 0, .3);
  const segmentDuration = safeDuration / cameraParts.length;
  return cameraParts.map((part, index) => {
    const segment = current.segments.find(item => item.part === part.key) || defaultCameraSegment(part.key);
    return cameraFrameFromSegment(segment, segmentDuration * index, 0);
  });
}
function cameraPathForEdit(edit, duration){
  const path = normalizeCameraPath(edit?.camera_path);
  return path.length ? path : cameraPathFromCamera(edit?.camera || defaultCamera(), duration);
}
function exportCameraPathForEdit(edit, sourceDuration, trimStart, adjustedDuration){
  const safeSourceDuration = Math.max(Number(sourceDuration) || Number(adjustedDuration) || 0, .3);
  const safeTrimStart = clampNumber(Number(trimStart) || 0, 0, Math.max(safeSourceDuration - .001, 0));
  const safeAdjustedDuration = Math.max(Number(adjustedDuration) || (safeSourceDuration - safeTrimStart), .3);
  const sourcePath = cameraPathForEdit(edit, safeSourceDuration);
  const active = cameraFrameForTime(edit?.camera, sourcePath, safeTrimStart, safeSourceDuration);
  const frames = [Object.assign({}, active, { time: 0 })];
  sourcePath.forEach(frame => {
    const time = Number(frame.time || 0);
    if (time <= safeTrimStart + .001) return;
    if (time >= safeTrimStart + safeAdjustedDuration - .001) return;
    frames.push(Object.assign({}, frame, { time: Number((time - safeTrimStart).toFixed(3)) }));
  });
  return normalizeCameraPath(frames);
}
function sourceDurationForMoment(moment){
  return Number(moment?.duration || (Number(moment?.end || 0) - Number(moment?.start || 0)) || moment?.adjusted_duration || 0);
}
function explicitCameraPathForEdit(edit){
  return normalizeCameraPath(edit?.camera_path);
}
function selectedCameraPathIndex(card, path){
  const count = path.length;
  if (!count) return 0;
  const index = Number(card?.dataset.cameraPathIndex ?? 0);
  return Math.min(Math.max(Number.isFinite(index) ? index : 0, 0), count - 1);
}
function setSelectedCameraPathIndex(card, index){
  if (!card) return;
  card.dataset.cameraPathIndex = String(Math.max(0, Number(index) || 0));
}
function cameraPathWithFrame(path, frame, index = null){
  const frames = normalizeCameraPath(path);
  const next = normalizeCameraPathFrame(frame);
  if (!next) return frames;
  const exactIndex = index === null ? frames.findIndex(item => Math.abs(item.time - next.time) < .15) : Number(index);
  if (exactIndex >= 0 && exactIndex < frames.length) {
    frames[exactIndex] = next;
  } else {
    frames.push(next);
  }
  return normalizeCameraPath(frames);
}
function cameraPathFrameWithPreset(frame, key, strength){
  const next = cameraFrameFromSegment({ part: frame.part || "", key, strength }, frame.time, 0);
  next.source = "manual-path";
  return next;
}
function setCameraPathForRank(rank, path, platform = activePlatformForRank(rank), rerender = true){
  const normalized = normalizeCameraPath(path);
  const duration = cardForRank(rank) ? cameraTimelineDurationForCard(cardForRank(rank)) : 0;
  setPlatformEditForRank(rank, platform, { camera_path: normalized, director_plan: directorPlanFromCameraPath(normalized, duration, platform) });
  const card = cardForRank(rank);
  if (card) {
    const edit = platformEditForRank(rank, platform);
    if (rerender) updateCameraUi(card);
    updateCardCameraSummary(card, edit.camera, edit);
    updateCameraSurfaceForCard(card);
    renderPreviewCameraTimeline(card);
  }
  renderFinalStage();
}
function addCameraPathFrameForCard(card){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card);
  const edit = platformEditForRank(rank, platform);
  const sourcePath = cameraPathForEdit(edit, duration);
  const frame = cameraFrameForTime(edit.camera, sourcePath, position, duration);
  const next = Object.assign({}, frame, { time: Number(position.toFixed(3)), source: "manual-path" });
  const path = cameraPathWithFrame(sourcePath, next);
  const index = path.findIndex(item => Math.abs(item.time - next.time) < .01);
  setSelectedCameraPathIndex(card, index >= 0 ? index : path.length - 1);
  setCameraPathForRank(rank, path, platform);
}
function addCenterCameraFrameForCard(card){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card);
  const edit = platformEditForRank(rank, platform);
  const sourcePath = cameraPathForEdit(edit, duration);
  const next = normalizeCameraPathFrame({
    time: Number(position.toFixed(3)),
    key: "center",
    strength: 60,
    source: "manual-path"
  });
  const path = next ? cameraPathWithFrame(sourcePath, next) : sourcePath;
  const index = next ? path.findIndex(item => Math.abs(item.time - next.time) < .01) : path.length - 1;
  setSelectedCameraPathIndex(card, index >= 0 ? index : path.length - 1);
  setCameraPathForRank(rank, path, platform);
}
function updateCameraPathFrameForCard(card, patch, rerender = true){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const edit = platformEditForRank(rank, platform);
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card);
  const path = cameraPathForEdit(edit, duration);
  const index = selectedCameraPathIndex(card, path);
  const current = path[index] || cameraFrameForTime(edit.camera, path, position, duration);
  let frame = Object.assign({}, current, patch);
  if (patch.key || patch.strength !== undefined) {
    frame = cameraPathFrameWithPreset(frame, patch.key || current.key || "center", patch.strength ?? current.strength ?? 60);
  }
  const nextPath = cameraPathWithFrame(path, frame, index);
  setSelectedCameraPathIndex(card, Math.min(index, nextPath.length - 1));
  setCameraPathForRank(rank, nextPath, platform, rerender);
}
function updateCameraPathFrameIntentForCard(card, intent){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const edit = platformEditForRank(rank, platform);
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card);
  const path = cameraPathForEdit(edit, duration);
  const index = selectedCameraPathIndex(card, path);
  const current = path[index] || cameraFrameForTime(edit.camera, path, position, duration);
  const frame = cameraFramePatchForIntent(intent, current);
  const nextPath = cameraPathWithFrame(path, frame, index);
  setSelectedCameraPathIndex(card, Math.min(index, nextPath.length - 1));
  setCameraPathForRank(rank, nextPath, platform);
}
function addCameraIntentFrameForCard(card, intent){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card);
  const edit = platformEditForRank(rank, platform);
  const sourcePath = cameraPathForEdit(edit, duration);
  const base = cameraFrameForTime(edit.camera, sourcePath, position, duration);
  const frame = cameraFramePatchForIntent(intent, Object.assign({}, base, { time: Number(position.toFixed(3)) }));
  const path = cameraPathWithFrame(sourcePath, frame);
  const index = path.findIndex(item => Math.abs(item.time - frame.time) < .01);
  setSelectedCameraPathIndex(card, index >= 0 ? index : path.length - 1);
  setCameraPathForRank(rank, path, platform);
}
function moveCameraPathFrameToPlayhead(card){
  const position = cameraTimelinePositionForCard(card);
  updateCameraPathFrameForCard(card, { time: Number(position.toFixed(3)) });
}
function deleteCameraPathFrameForCard(card){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const edit = platformEditForRank(rank, platform);
  const duration = cameraTimelineDurationForCard(card);
  const path = cameraPathForEdit(edit, duration);
  if (path.length <= 1) return;
  const index = selectedCameraPathIndex(card, path);
  path.splice(index, 1);
  setSelectedCameraPathIndex(card, Math.max(0, index - 1));
  setCameraPathForRank(rank, path, platform);
}
function resetCameraPathForCard(card){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  setSelectedCameraPathIndex(card, 0);
  setCameraPathForRank(rank, [], platform);
}
function cameraAnalysisRequestPayload(card, smartMode, forceRefresh){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const moment = (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === String(rank));
  const values = trimValues(card);
  return {
    gallery_path: currentGalleryPath(),
    rank,
    platform,
    mode: smartMode,
    force_refresh: forceRefresh,
    allow_completed_cache: true,
    clip_file: moment?.clip_file || "",
    title: moment?.title || "",
    transcript: moment?.transcript || moment?.text || "",
    trim_start_seconds: values.trimStart,
    source_start_seconds: Number(moment?.start || 0) + values.trimStart,
    adjusted_duration: Math.max(values.endPos - values.startPos, .3)
  };
}
function cameraStatusUrl(card, smartMode){
  const payload = cameraAnalysisRequestPayload(card, smartMode, false);
  const params = new URLSearchParams();
  Object.entries(payload).forEach(([key, value]) => {
    if (value !== undefined && value !== null) params.set(key, String(value));
  });
  return `/api/camera/status?${params.toString()}`;
}
function scheduleAiReadinessRefresh(card){
  if (card.dataset.aiPollScheduled === "1") return;
  card.dataset.aiPollScheduled = "1";
  window.setTimeout(() => {
    delete card.dataset.aiPollScheduled;
    refreshAiReadinessForCard(card);
  }, cameraReadinessPollMs);
}
async function refreshAiReadinessForCard(card){
  const button = card.querySelector("[data-camera-ai]");
  if (card.dataset.aiApplying === "1") return;
  if (card.dataset.aiStatusLoading === "1") return;
  card.dataset.aiStatusLoading = "1";
  try {
    const response = await fetch(cameraStatusUrl(card, "ai-director"));
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "status indisponivel");
    card.dataset.aiReady = payload.ready ? "1" : "0";
    card.dataset.aiCacheReady = payload.cache_ready ? "1" : "0";
    if (button) {
      button.disabled = !payload.ready;
      button.textContent = payload.ready ? "IA" : "...";
    }
    if (payload.cache_ready) setCameraAutoStatus(card, "IA pronta do cache");
    else if (payload.ready) setCameraAutoStatus(card, "IA pronta");
    else {
      setCameraAutoStatus(card, "Mapeando video...");
      scheduleAiReadinessRefresh(card);
    }
  } catch (_error) {
    card.dataset.aiReady = "0";
    if (button) {
      button.disabled = true;
      button.textContent = "...";
    }
    setCameraAutoStatus(card, "Mapeando video...");
    scheduleAiReadinessRefresh(card);
  } finally {
    delete card.dataset.aiStatusLoading;
    updateControlSurfaceForCard(card);
  }
}
async function analyzeCameraForCard(card, mode = "auto-director"){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const smartMode = smartCameraModes[mode] ? mode : "auto-director";
  const currentEdit = platformEditForRank(rank, platform);
  const hasCachedAiPath = smartMode === "ai-director" && explicitCameraPathForEdit(currentEdit).length > 0;
  const forceRefresh = smartMode === "ai-director" && !hasCachedAiPath;
  const button = card.querySelector(`[data-camera-smart-mode="${smartMode}"]`) || card.querySelector("[data-camera-ai]") || card.querySelector("[data-camera-auto]");
  if (smartMode === "ai-director" && card.dataset.aiReady !== "1") {
    setCameraAutoStatus(card, "Mapeando video...");
    refreshAiReadinessForCard(card);
    return;
  }
  card.dataset.aiApplying = "1";
  setCameraAutoStatus(card, `Aplicando ${smartCameraModes[smartMode].label}...`);
  if (button) {
    button.disabled = true;
    if (smartMode === "ai-director") button.textContent = "...";
  }
  try {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), cameraAnalysisFetchTimeoutMs);
    let response;
    try {
      response = await fetch("/api/camera/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify(cameraAnalysisRequestPayload(card, smartMode, forceRefresh))
      });
    } finally {
      window.clearTimeout(timeoutId);
    }
    const payload = await response.json();
    const diagnosticText = cameraDiagnosticsText(payload.diagnostics);
    if (!response.ok || !payload.ok) {
      const detail = diagnosticText ? ` (${diagnosticText})` : "";
      throw new Error(`${payload.error || "Falha ao analisar camera."}${detail}`);
    }
    const path = normalizeCameraPath(payload.camera_path);
    if (!path.length) throw new Error("A analise nao retornou keyframes.");
    setSelectedCameraPathIndex(card, 0);
    const directorPlan = normalizeDirectorPlan(payload.director_plan);
    setPlatformEditForRank(rank, platform, { camera_path: path, director_plan: directorPlan });
    updateCameraUi(card);
    updateCameraSurfaceForCard(card);
    renderPreviewCameraTimeline(card);
    renderFinalStage();
    const label = payload.mode_label || smartCameraModes[smartMode].label;
    const suffix = diagnosticText ? ` (${diagnosticText})` : "";
    const applied = payload.cache_recovered ? `${label}: mantive ultimo resultado bom` : payload.completed_cache ? `${label} pronto do cache` : payload.cached ? `${label} aplicado do cache` : payload.cache_bypassed ? `${label} recalculado` : `${label} aplicado`;
    setCameraAutoStatus(card, `${applied}.${suffix}`);
  } catch (error) {
    const message = error && error.name === "AbortError"
      ? "IA ainda esta aplicando; tente novamente em alguns segundos para buscar o resultado pronto."
      : (error.message || "Falha na auto camera.");
    setCameraAutoStatus(card, message);
  } finally {
    delete card.dataset.aiApplying;
    const nextButton = card.querySelector(`[data-camera-smart-mode="${smartMode}"]`) || card.querySelector("[data-camera-ai]") || card.querySelector("[data-camera-auto]");
    if (nextButton) {
      nextButton.disabled = false;
      if (smartMode === "ai-director") nextButton.textContent = "IA";
    }
    if (smartMode === "ai-director") refreshAiReadinessForCard(card);
  }
}
function setCameraAutoStatus(card, message){
  const status = card.querySelector("[data-camera-auto-status]");
  if (status) status.textContent = message || "";
  updateControlSurfaceForCard(card);
}
function cameraDiagnosticsText(diagnostics){
  if (!diagnostics || typeof diagnostics !== "object") return "";
  const samples = Number(diagnostics.sample_count || 0);
  const detected = Number(diagnostics.detection_frames || 0);
  const width = Number(diagnostics.video_width || 0);
  const height = Number(diagnostics.video_height || 0);
  const keyframes = Number(diagnostics.camera_keyframes || 0);
  const visualMap = diagnostics.visual_map || {};
  let input = diagnostics.analysis_input === "source" ? "source" : "clip";
  if (visualMap && visualMap.used) input = "mapa visual";
  const multi = Number(diagnostics.multi_face_frames || 0);
  const edge = Number(diagnostics.edge_face_frames || 0);
  const maxGap = Number(diagnostics.camera_max_gap_seconds || 0);
  const risk = Number(diagnostics.camera_risk_frames || 0);
  const protectedFrames = Number(diagnostics.camera_protected_keyframes || 0);
  const size = width && height ? `${width}x${height}` : "video";
  const parts = [input, `${detected}/${samples} frames`, size, `${keyframes} keyframes`];
  if (visualMap && visualMap.segment_samples) parts.splice(1, 0, `${Number(visualMap.segment_samples)} do mapa`);
  const ai = diagnostics.ai_director || {};
  const intent = ai && ai.intent ? `IA ${ai.intent}` : "IA";
  if (diagnostics.ai_cache_recovered && diagnostics.ai_cache_recovered.used) parts.push("cache bom preservado");
  if (ai && ai.status === "visual_map_pending") parts.push("mapa visual preparando");
  else if (ai && ai.status === "timeout") parts.push(`${intent} timeout`);
  else if (ai && ai.status === "quality_rejected") parts.push(`${intent} rejeitada por monotonia`);
  else if (ai && ai.status === "no_key") parts.push("IA sem chave");
  else if (ai && ai.enabled) parts.push(ai.error ? `${intent} fallback local` : `${intent} aplicada`);
  if (ai && !ai.enabled && ai.error && ai.status !== "no_key") parts.push("IA sem chave");
  if (Number(ai.director_plan_shots || 0)) parts.push(`${Number(ai.director_plan_shots)} cenas`);
  if (multi) parts.splice(1, 0, `${multi} multi-face`);
  if (edge) parts.splice(2, 0, `${edge} borda`);
  if (maxGap) parts.push(`gap max ${maxGap.toFixed(1)}s`);
  if (protectedFrames) parts.push(`${protectedFrames} protegidos`);
  if (risk) parts.push(`${risk} riscos`);
  return parts.join(" | ");
}
function cameraFrameForTime(camera, cameraPath, position, duration){
  const path = normalizeCameraPath(cameraPath);
  if (!path.length) {
    const active = cameraSegmentForTime(camera, position, duration);
    return cameraFrameFromSegment(active.segment, position, active.elapsed);
  }
  const safePosition = Math.max(0, Number(position) || 0);
  let previous = path[0];
  let next = path[path.length - 1];
  for (let index = 0; index < path.length; index += 1) {
    if (path[index].time <= safePosition) previous = path[index];
    if (path[index].time >= safePosition) {
      next = path[index];
      break;
    }
  }
  if (previous.key || cameraFrameUsesHardCut(previous) || cameraFrameUsesGroupFit(previous)) {
    return previous.key ? cameraFrameFromSegment(previous, safePosition, Math.max(0, safePosition - previous.time)) : previous;
  }
  if (previous === next || next.time <= previous.time) return previous;
  if (cameraFrameUsesHardCut(next) || cameraFrameUsesGroupFit(next)) return previous;
  const ratio = (safePosition - previous.time) / (next.time - previous.time);
  return {
    time: Number(safePosition.toFixed(3)),
    x: Number((previous.x + (next.x - previous.x) * ratio).toFixed(2)),
    y: Number((previous.y + (next.y - previous.y) * ratio).toFixed(2)),
    zoom: Number((previous.zoom + (next.zoom - previous.zoom) * ratio).toFixed(3)),
    source: previous.source || "manual-path",
    confidence: Math.min(previous.confidence ?? 1, next.confidence ?? 1)
  };
}
function cameraFrameUsesHardCut(frame){
  return String(frame?.source || "").includes("ai-director-cuts");
}
function cameraFrameUsesGroupFit(frame){
  return String(frame?.fit || "").toLowerCase() === "contain" || String(frame?.source || "").includes("group-fit");
}
function cameraPreviewStyle(camera, elapsed = 0){
  const current = normalizeSingleCamera(camera);
  const x = cameraCropPercent(current, elapsed).toFixed(2);
  const scale = cameraScaleValue(current).toFixed(3);
  return `--camera-x:${x}%;--camera-scale:${scale}`;
}
function cameraPreviewStyleFromFrame(frame){
  const current = normalizeCameraPathFrame(frame) || { x: 50, zoom: 1 };
  if (cameraFrameUsesGroupFit(current)) return "--camera-x:50%;--camera-scale:1";
  return `--camera-x:${current.x.toFixed(2)}%;--camera-scale:${current.zoom.toFixed(3)}`;
}
function cameraHasMovement(camera){
  return normalizeCamera(camera).segments.some(segment => segment.key !== "center");
}
function applyCameraSurface(surface, camera, position = 0, duration = 0, cameraPath = []){
  if (!surface) return;
  const frame = cameraFrameForTime(camera, cameraPath, position, duration);
  surface.dataset.cameraKey = frame.key || "path";
  surface.dataset.cameraCut = cameraFrameUsesHardCut(frame) ? "hard" : "smooth";
  surface.dataset.cameraFit = cameraFrameUsesGroupFit(frame) ? "contain" : "cover";
  surface.setAttribute("style", cameraPreviewStyleFromFrame(frame));
  syncCameraFitBackground(surface);
}
function applyCameraMotionSpeed(card){
  const speed = normalizeCameraMotionMs(cardState(card.dataset.rank).cameraMotionMs);
  card.style.setProperty("--camera-transition-ms", `${speed}ms`);
  const input = card.querySelector("[data-camera-motion-speed]");
  if (input) input.value = String(speed);
}
function setCameraMotionSpeed(card, value){
  const speed = normalizeCameraMotionMs(value);
  setCardState(card.dataset.rank, { cameraMotionMs: speed });
  applyCameraMotionSpeed(card);
}
function primaryCameraVideo(scope){
  return scope?.querySelector("video:not(.camera-fit-bg)") || null;
}
function cameraFitBackgroundFor(scope){
  const surface = scope?.classList?.contains("camera-surface") ? scope : scope?.querySelector(".camera-surface");
  if (!surface) return null;
  const existing = surface.querySelector(".camera-fit-bg");
  if (existing) return existing;
  const bg = document.createElement("video");
  bg.className = "camera-fit-bg";
  bg.dataset.cameraFitBg = "1";
  bg.muted = true;
  bg.playsInline = true;
  bg.preload = "none";
  bg.setAttribute("aria-hidden", "true");
  bg.setAttribute("tabindex", "-1");
  const main = primaryCameraVideo(surface);
  if (main) main.insertAdjacentElement("afterend", bg);
  else surface.prepend(bg);
  return bg;
}
function syncCameraFitBackground(scope){
  const surface = scope?.classList?.contains("camera-surface") ? scope : scope?.querySelector(".camera-surface");
  if (!surface) return;
  const main = primaryCameraVideo(surface);
  const bg = cameraFitBackgroundFor(surface);
  if (!main || !bg) return;
  const nextSrc = main.currentSrc || main.getAttribute("src") || main.dataset.src || "";
  if (nextSrc && bg.getAttribute("src") !== nextSrc) {
    bg.setAttribute("src", nextSrc);
    bg.load();
  }
  bg.muted = true;
  bg.playsInline = true;
  if (bg.readyState > 0 && Number.isFinite(main.currentTime) && Math.abs(bg.currentTime - main.currentTime) > .12) {
    bg.currentTime = main.currentTime;
  }
  if (surface.dataset.cameraFit === "contain" && !main.paused && !main.ended) {
    const playback = bg.play();
    if (playback && typeof playback.catch === "function") playback.catch(() => {
      bg.dataset.playbackBlocked = "1";
    });
  } else {
    bg.pause();
  }
}
function unloadCameraFitBackground(scope){
  const bg = cameraFitBackgroundFor(scope?.classList?.contains("camera-surface") ? scope : scope?.querySelector(".camera-surface"));
  if (!bg) return;
  bg.pause();
  bg.removeAttribute("src");
  bg.load();
}
function cameraContextForCard(card, time = null){
  const values = trimValues(card);
  const video = primaryCameraVideo(card);
  const raw = time === null && video && Number.isFinite(video.currentTime) ? video.currentTime : time;
  const current = clampPreviewTime(values, Number(raw ?? values.trimStart));
  return {
    position: Math.max(0, current - values.trimStart),
    duration: Math.max(values.endPos - values.trimStart, .3)
  };
}
function cameraTimelineDurationForCard(card){
  const values = trimValues(card);
  return Math.max(Number(values.duration) || Number(card?.dataset?.duration) || 0, .3);
}
function cameraTimelinePositionForCard(card, time = null){
  const values = trimValues(card);
  const video = primaryCameraVideo(card);
  const raw = time === null && video && Number.isFinite(video.currentTime) ? video.currentTime : time;
  return clampPreviewTime(values, Number(raw ?? values.trimStart));
}
function updateCameraSurfaceForCard(card, time = null){
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card, time);
  const edit = platformEditForRank(card.dataset.rank, activePlatformForRank(card.dataset.rank));
  applyCameraSurface(card.querySelector(".camera-surface"), edit.camera, position, duration, cameraPathForEdit(edit, duration));
}
function startCameraFrameSync(video, update){
  if (!video || typeof requestAnimationFrame !== "function") return;
  const tick = () => {
    if (video.paused || video.ended) {
      delete video.dataset.cameraFrameSync;
      return;
    }
    update();
    video.dataset.cameraFrameSync = String(requestAnimationFrame(tick));
  };
  if (video.dataset.cameraFrameSync) return;
  update();
  video.dataset.cameraFrameSync = String(requestAnimationFrame(tick));
}
function stopCameraFrameSync(video, update){
  if (!video || !video.dataset.cameraFrameSync) {
    if (update) update();
    return;
  }
  cancelAnimationFrame(Number(video.dataset.cameraFrameSync));
  delete video.dataset.cameraFrameSync;
  if (update) update();
}
function cameraStyle(camera){
  return cameraPreviewStyle(camera, 0);
}
function defaultEffect(){ return { key: "none", label: effectMeta.none.label, intensity: 0 }; }
function normalizeEffect(effect){
  const key = effectMeta[effect?.key] ? effect.key : "none";
  const intensity = key === "none" ? 0 : Math.max(0, Math.min(Number(effect?.intensity || 65), 100));
  return { key, label: effectMeta[key].label, intensity };
}
function effectLabel(effect){
  const current = normalizeEffect(effect);
  return current.key === "none" ? current.label : `${current.label} - ${current.intensity}%`;
}
function effectForRank(rank, platform = activePlatformForRank(rank)){ return platformEditForRank(rank, platform).effect; }
function setEffectForRank(rank, patch){
  const platform = activePlatformForRank(rank);
  const current = effectForRank(rank, platform);
  setPlatformEditForRank(rank, platform, { effect: normalizeEffect(Object.assign({}, current, patch)) });
  const card = cardForRank(rank);
  if (card) {
    updateEffectUi(card);
    updateControlSurfaceForCard(card);
  }
  renderFinalStage();
}
function effectOpacity(effect){
  const current = normalizeEffect(effect);
  return current.key === "none" ? 0 : Math.max(.12, current.intensity / 185);
}
function defaultBumpers(){ return {}; }
function normalizeBumperSlot(slot){ return slot === "outro" ? "outro" : "intro"; }
function normalizeBumper(bumper, slot){
  if (!bumper || typeof bumper !== "object") return null;
  const assetFile = String(bumper.asset_file || "");
  const dataUrl = String(bumper.video_data_url || "");
  if (!assetFile && !dataUrl) return null;
  const safeSlot = normalizeBumperSlot(slot || bumper.slot);
  return {
    id: String(bumper.id || `bumper-${safeSlot}-${Date.now().toString(36)}`),
    slot: safeSlot,
    label: String(bumper.label || "vinheta.mp4"),
    asset_file: assetFile,
    video_data_url: dataUrl,
    width: Number(bumper.width || 0),
    height: Number(bumper.height || 0),
    duration: Math.max(Number(bumper.duration || 0), 0)
  };
}
function normalizeBumpers(bumpers){
  if (!bumpers || typeof bumpers !== "object") return defaultBumpers();
  const result = {};
  ["intro", "outro"].forEach(slot => {
    const bumper = normalizeBumper(bumpers[slot], slot);
    if (bumper) result[slot] = bumper;
  });
  return result;
}
function bumpersForRank(rank, platform = activePlatformForRank(rank)){ return platformEditForRank(rank, platform).bumpers; }
function setBumperForRank(rank, slot, bumper, platform = activePlatformForRank(rank)){
  const key = validPlatform(platform);
  const safeSlot = normalizeBumperSlot(slot);
  const current = bumpersForRank(rank, key);
  const next = Object.assign({}, current, { [safeSlot]: normalizeBumper(bumper, safeSlot) });
  if (!next[safeSlot]) delete next[safeSlot];
  setPlatformEditForRank(rank, key, { bumpers: normalizeBumpers(next) });
  const card = cardForRank(rank);
  if (card) {
    updateEffectUi(card);
    updateControlSurfaceForCard(card);
  }
  renderFinalStage();
}
function removeBumperForRank(rank, slot, platform = activePlatformForRank(rank)){
  const key = validPlatform(platform);
  const safeSlot = normalizeBumperSlot(slot);
  const next = Object.assign({}, bumpersForRank(rank, key));
  delete next[safeSlot];
  setPlatformEditForRank(rank, key, { bumpers: normalizeBumpers(next) });
  const card = cardForRank(rank);
  if (card) {
    updateEffectUi(card);
    updateControlSurfaceForCard(card);
  }
  renderFinalStage();
}
function bumperSlotLabel(slot){ return normalizeBumperSlot(slot) === "intro" ? "Entrada" : "Saida"; }
function bumperSummary(bumpers){
  const current = normalizeBumpers(bumpers);
  const labels = [];
  if (current.intro) labels.push("Entrada");
  if (current.outro) labels.push("Saida");
  return labels.length ? labels.join(" + ") : "Sem vinheta";
}
function defaultOverlay(){ return { id: "", kind: "cta", key: "none", label: overlayMeta.none.label, x: .62, y: .78, width: .34, opacity: 95 }; }
function overlayId(){
  return `layer-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}
function defaultTextOverlay(text = "Digite seu texto"){
  return {
    id: overlayId(),
    kind: "text",
    key: "text",
    label: text,
    text,
    x: .36,
    y: .34,
    width: .42,
    opacity: 100,
    font_size: 44,
    font_weight: "700",
    color: "#ffffff",
    background_enabled: true,
    background_color: "#000000",
    background_opacity: 70,
    start_seconds: 0,
    duration_seconds: 3
  };
}
function defaultSpeechOverlay(text = "Fala rapida"){
  return {
    id: overlayId(),
    kind: "speech",
    key: "speech",
    label: text,
    text,
    x: .32,
    y: .24,
    width: .56,
    opacity: 96,
    font_size: 34,
    font_weight: "800",
    color: "#050505",
    background_enabled: true,
    background_color: "#ffffff",
    background_opacity: 94,
    tail: "bottom-left",
    start_seconds: 0,
    duration_seconds: 3
  };
}
function normalizeOverlay(overlay){
  const key = overlayMeta[overlay?.key] ? overlay.key : "none";
  if (key === "none") return defaultOverlay();
  const text = String(overlay?.text || overlayMeta[key].title || overlayMeta[key].label);
  return normalizeTextOverlay(Object.assign({}, overlay, { text, label: text }));
}
function normalizeTextOverlay(layer){
  const text = String(layer?.text || layer?.label || "Digite seu texto").trim() || "Digite seu texto";
  return {
    id: String(layer?.id || overlayId()),
    kind: "text",
    key: "text",
    label: text,
    text,
    x: clampNumber(layer?.x ?? .36, 0, 1),
    y: clampNumber(layer?.y ?? .34, 0, 1),
    width: clampNumber(layer?.width ?? .42, .16, .9),
    opacity: clampNumber(layer?.opacity ?? 100, 10, 100),
    font_size: clampNumber(layer?.font_size ?? 44, 14, 96),
    font_weight: String(layer?.font_weight || "700"),
    color: normalizeHexColor(layer?.color, "#ffffff"),
    background_enabled: layer?.background_enabled !== false,
    background_color: normalizeHexColor(layer?.background_color, "#000000"),
    background_opacity: clampNumber(layer?.background_opacity ?? 70, 0, 100),
    start_seconds: clampNumber(layer?.start_seconds ?? 0, 0, 9999),
    duration_seconds: clampNumber(layer?.duration_seconds ?? 3, .3, 60)
  };
}
function normalizeSpeechOverlay(layer){
  const base = normalizeTextOverlay(Object.assign({}, defaultSpeechOverlay(), layer, {
    background_enabled: true,
    background_color: layer?.background_color || "#ffffff",
    background_opacity: layer?.background_opacity ?? 94,
    color: layer?.color || "#050505",
    font_weight: layer?.font_weight || "800"
  }));
  return Object.assign(base, {
    kind: "speech",
    key: "speech",
    label: base.text,
    tail: String(layer?.tail || "bottom-left"),
    start_seconds: clampNumber(layer?.start_seconds ?? 0, 0, 9999),
    duration_seconds: clampNumber(layer?.duration_seconds ?? 3, .3, 60)
  });
}
function normalizeImageOverlay(layer){
  return {
    id: String(layer?.id || overlayId()),
    kind: "image",
    key: "image",
    label: String(layer?.label || "Imagem"),
    x: clampNumber(layer?.x ?? .58, 0, 1),
    y: clampNumber(layer?.y ?? .68, 0, 1),
    width: clampNumber(layer?.width ?? .28, .08, .9),
    opacity: clampNumber(layer?.opacity ?? 100, 10, 100),
    image_data_url: String(layer?.image_data_url || ""),
    image_file: String(layer?.image_file || ""),
    start_seconds: clampNumber(layer?.start_seconds ?? 0, 0, 9999),
    duration_seconds: clampNumber(layer?.duration_seconds ?? 3, .3, 60)
  };
}
function normalizeOverlayLayer(layer){
  if (layer?.kind === "image" || layer?.key === "image") return normalizeImageOverlay(layer);
  if (layer?.kind === "speech" || layer?.key === "speech") return normalizeSpeechOverlay(layer);
  if (layer?.kind === "text" || layer?.key === "text") return normalizeTextOverlay(layer);
  return normalizeOverlay(layer);
}
function normalizeOverlayLayers(layers, fallback){
  const source = Array.isArray(layers) ? layers : [];
  const normalized = source.map(normalizeOverlayLayer).filter(layer => layer.key !== "none");
  if (normalized.length) return normalized;
  const legacy = normalizeOverlay(fallback);
  return legacy.key === "none" ? [] : [legacy];
}
function overlayLayersForRank(rank, platform = activePlatformForRank(rank)){ return platformEditForRank(rank, platform).overlays; }
function primaryOverlayForRank(rank, platform = activePlatformForRank(rank)){
  const layers = overlayLayersForRank(rank, platform).filter(layer => layer.kind !== "image");
  return layers[0] || defaultOverlay();
}
function overlayPlatformForItem(item){
  return validPlatform(item?.dataset?.platform || item?.dataset?.previewFormat || activePlatformForRank(item?.dataset?.rank));
}
function setOverlayLayersForRank(rank, layers, rerender = true, platform = activePlatformForRank(rank)){
  const normalized = normalizeOverlayLayers(layers, defaultOverlay());
  setPlatformEditForRank(rank, platform, { overlays: normalized, overlay: normalized.find(layer => layer.kind !== "image") || defaultOverlay() });
  const card = cardForRank(rank);
  if (card && rerender) updateOverlayUi(card);
  renderFinalStage();
}
function addOverlayLayerForRank(rank, layer, platform = activePlatformForRank(rank)){
  setOverlayLayersForRank(rank, [...overlayLayersForRank(rank, platform), normalizeOverlayLayer(layer)], true, platform);
}
function patchOverlayLayerForRank(rank, id, patch, rerender = true, platform = activePlatformForRank(rank)){
  const layers = overlayLayersForRank(rank, platform).map(layer => layer.id === id ? normalizeOverlayLayer(Object.assign({}, layer, patch)) : layer);
  setOverlayLayersForRank(rank, layers, rerender, platform);
}
function removeOverlayLayerForRank(rank, id, platform = activePlatformForRank(rank)){
  setOverlayLayersForRank(rank, overlayLayersForRank(rank, platform).filter(layer => layer.id !== id), true, platform);
}
function setOverlayForRank(rank, patch, rerender = true, platform = activePlatformForRank(rank)){
  const layers = overlayLayersForRank(rank, platform);
  const first = layers.find(layer => layer.kind !== "image");
  if (first) {
    patchOverlayLayerForRank(rank, first.id, patch, rerender, platform);
    return;
  }
  setOverlayLayersForRank(rank, [normalizeOverlay(Object.assign({}, defaultOverlay(), patch))], rerender, platform);
}
function overlayLabel(overlay){
  const current = normalizeOverlayLayer(overlay);
  if (current.key === "none") return current.label;
  return `${current.label} - ${Math.round(current.opacity)}%`;
}
function overlayStyle(overlay){
  const current = normalizeOverlayLayer(overlay);
  const meta = overlayMeta[current.key] || overlayMeta.none;
  const textLike = current.kind === "text" || current.kind === "speech";
  const backgroundRgb = textLike ? hexToRgb(current.background_color).join(",") : "0,0,0";
  const color = textLike ? current.color : "#ffffff";
  const fontSize = textLike ? `${current.font_size}px` : "20px";
  const backgroundOpacity = textLike ? current.background_opacity / 100 : .7;
  return `--overlay-x:${current.x};--overlay-y:${current.y};--overlay-width:${current.width};--overlay-opacity:${current.opacity / 100};--overlay-accent:${meta.accent};--overlay-color:${color};--overlay-font-size:${fontSize};--overlay-bg-rgb:${backgroundRgb};--overlay-bg-opacity:${backgroundOpacity}`;
}
function overlayTimingForLayer(layer){
  return {
    start: clampNumber(layer?.start_seconds ?? 0, 0, 9999),
    duration: clampNumber(layer?.duration_seconds ?? 3, .3, 60)
  };
}
function overlayTimingAttrs(layer){
  const timing = overlayTimingForLayer(layer);
  return `data-overlay-start="${timing.start.toFixed(3)}" data-overlay-duration="${timing.duration.toFixed(3)}"`;
}
function overlayTimingForCard(card){
  const context = cameraContextForCard(card);
  const start = clampNumber(context.position, 0, Math.max(context.duration - .3, 0));
  const duration = clampNumber(Math.min(3, Math.max(context.duration - start, .3)), .3, 60);
  return { start_seconds: Number(start.toFixed(3)), duration_seconds: Number(duration.toFixed(3)) };
}
function speechOverlayTimingForCard(card){ return overlayTimingForCard(card); }
function overlayBoxVisibleAtPosition(box, position){
  if (box.dataset.overlayStart === undefined) return true;
  const start = clampNumber(box.dataset.overlayStart ?? 0, 0, 9999);
  const duration = clampNumber(box.dataset.overlayDuration ?? 3, .3, 60);
  return position >= start && position < start + duration;
}
function setOverlayBoxVisibility(box, visible){
  box.hidden = false;
  box.dataset.overlayVisible = visible ? "true" : "false";
  box.setAttribute("aria-hidden", visible ? "false" : "true");
}
function syncTimedOverlayVisibility(item, time = null){
  const boxes = item?.querySelectorAll?.("[data-overlay-drag]");
  if (!boxes?.length) return;
  const video = item.querySelector("video");
  const raw = time ?? (video && Number.isFinite(video.currentTime) ? video.currentTime : 0);
  const position = item.classList.contains("card") ? cameraContextForCard(item, raw).position : Number(raw || 0);
  boxes.forEach(box => setOverlayBoxVisibility(box, overlayBoxVisibleAtPosition(box, position)));
  syncOverlayTimelineActive(item, position);
}
function syncOverlayTimelineActive(item, position){
  item?.querySelectorAll?.("[data-overlay-timeline-layer]").forEach(node => {
    const start = clampNumber(node.dataset.overlayStart ?? 0, 0, 9999);
    const duration = clampNumber(node.dataset.overlayDuration ?? 3, .3, 60);
    node.classList.toggle("is-active", position >= start && position < start + duration);
  });
}
function normalizeHexColor(value, fallback){
  const raw = String(value || "").trim();
  const hex = raw.startsWith("#") ? raw.slice(1) : raw;
  return /^[0-9a-fA-F]{6}$/.test(hex) ? `#${hex.toLowerCase()}` : fallback;
}
function hexToRgb(value){
  const hex = normalizeHexColor(value, "#000000").slice(1);
  return [0, 2, 4].map(index => parseInt(hex.slice(index, index + 2), 16));
}
function clampNumber(value, min, max){
  const next = Number(value);
  if (!Number.isFinite(next)) return min;
  return Math.min(Math.max(next, min), max);
}
function cardForRank(rank){
  return document.querySelector(`.card[data-rank="${CSS.escape(String(rank))}"]`);
}
function statusLabel(status){
  if (status === "liked") return "Aprovado";
  if (status === "discarded") return "Descartado";
  return "Em edicao";
}
function setCardPreviewFormat(card, format){
  const next = validPlatform(format);
  card.dataset.previewFormat = next;
  card.querySelectorAll("[data-card-format-preview]").forEach(button => {
    button.classList.toggle("active", button.dataset.cardFormatPreview === next);
    button.setAttribute("aria-selected", button.dataset.cardFormatPreview === next ? "true" : "false");
  });
  const trigger = card.querySelector("[data-preview-format-trigger]");
  if (trigger) trigger.setAttribute("aria-label", `Formato do preview: ${platformLabel(next)}`);
  const label = card.querySelector("[data-preview-format-current]");
  if (label) label.textContent = platformLabel(next);
  const status = card.querySelector("[data-platform-preset-current]");
  if (status) status.textContent = `Preset: ${platformLabel(next)}`;
  updateControlSurfaceForCard(card);
}
function closePreviewFormatMenus(except = null){
  document.querySelectorAll("[data-preview-format-menu]").forEach(menu => {
    if (menu === except) return;
    menu.querySelector("[data-preview-format-options]")?.setAttribute("hidden", "");
    menu.querySelector("[data-preview-format-trigger]")?.setAttribute("aria-expanded", "false");
  });
}
function togglePreviewFormatMenu(card){
  const menu = card.querySelector("[data-preview-format-menu]");
  const options = card.querySelector("[data-preview-format-options]");
  const trigger = card.querySelector("[data-preview-format-trigger]");
  if (!menu || !options || !trigger) return;
  const willOpen = options.hasAttribute("hidden");
  closePreviewFormatMenus(menu);
  options.toggleAttribute("hidden", !willOpen);
  trigger.setAttribute("aria-expanded", willOpen ? "true" : "false");
}
function bindPreviewFormatDismiss(){
  if (document.body.dataset.previewFormatDismissBound) return;
  document.body.dataset.previewFormatDismissBound = "1";
  document.addEventListener("click", event => {
    if (event.target instanceof Element && event.target.closest("[data-preview-format-menu]")) return;
    closePreviewFormatMenus();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closePreviewFormatMenus();
  });
}
function updateCardTools(card){
  updateCameraUi(card);
  updateEffectUi(card);
  updateOverlayUi(card);
  syncPreviewCaptions(card);
  updateControlSurfaceForCard(card);
}
function updateControlSurfaceForCard(card){
  if (!card) return;
  const slot = card.querySelector("[data-cuted-control-surface]");
  if (!slot || typeof window.createCutedControlBar !== "function") return;
  const next = controlSurfaceStateForCard(card);
  if (card.__cutedControlSurface) {
    card.__cutedControlSurface.update(next);
    return;
  }
  card.__cutedControlSurface = window.createCutedControlBar(slot, Object.assign(next, {
    mockBumpers: false,
    callbacks: controlSurfaceCallbacksForCard(card)
  }));
}
function destroyControlSurfaceForCard(card){
  if (!card || !card.__cutedControlSurface) return;
  card.__cutedControlSurface.destroy();
  delete card.__cutedControlSurface;
}
function controlSurfaceStateForCard(card){
  const rank = card.dataset.rank;
  const current = cardState(rank);
  const platform = activePlatformForRank(rank);
  const edit = platformEditForRank(rank, platform);
  const effect = effectForRank(rank, platform);
  const video = primaryCameraVideo(card);
  const platforms = uniquePlatforms(current.platforms);
  const busy = controlSurfaceBusy(card);
  const trim = trimValues(card);
  const moment = previewMomentForCard(card);
  return {
    aiStatus: busy ? "loading" : controlSurfaceAiStatus(card),
    aspectRatio: controlSurfaceAspectRatio(platform),
    bumpers: bumpersForRank(rank, platform),
    busy,
    captionLanguage: edit.captionLanguage,
    captionLanguageOptions: captionLanguageOptionsForMoment(moment),
    captionMode: edit.captions.style.mode,
    captionsEnabled: edit.captions.enabled,
    captionStyle: edit.captions.style,
    clipInfo: controlSurfaceClipInfo(card),
    effectStyle: controlSurfaceEffectStyle(effect),
    muted: video ? video.muted || video.volume <= 0 : false,
    ready: current.status === "liked" && platforms.includes(platform),
    discarded: current.status === "discarded",
    status: controlSurfaceStatus(card),
    trimApplied: trimRangeActive(trim),
    trimMode: !busy && card.dataset.trimMode === "1",
    volume: video ? Math.round((video.muted ? 0 : video.volume) * 100) : Math.round(defaultPreviewVolume * 100)
  };
}
function controlSurfaceClipInfo(card){
  const rank = String(card.dataset.rank || "").padStart(2, "0");
  const title = card.dataset.clipTitle || card.querySelector(".clip-title strong")?.textContent || "Corte sem titulo";
  const summary = card.querySelector("[data-card-summary]")?.textContent || card.dataset.clipSummary || "";
  return { rank: `#${rank}`, title, summary };
}
function controlSurfaceCallbacksForCard(card){
  return {
    onAiClick: () => analyzeCameraForCard(card, "ai-director"),
    onApproveClick: () => markControlSurfaceReady(card),
    onBumperClick: payload => openControlSurfaceBumperInput(card, payload.slot),
    onBumperRemove: payload => removeBumperForRank(card.dataset.rank, payload.slot),
    onCaptionToggle: payload => setControlSurfaceCaptions(payload.captionsEnabled, payload.captionStyle),
    onCaptionLanguageChange: payload => setControlSurfaceCaptionLanguage(payload.captionLanguage),
    onCaptionStyleChange: payload => setControlSurfaceCaptions(payload.captionsEnabled, payload.captionStyle),
    onDiscardClick: () => discardControlSurfaceCard(card),
    onEffectStyleChange: payload => setEffectForRank(card.dataset.rank, { key: appEffectKeyFromControlSurface(payload.effectStyle) }),
    onFormatChange: payload => setControlSurfaceFormat(card, payload.aspectRatio),
    onReadyCancel: () => cancelControlSurfaceReady(card),
    onSendRender: () => sendCardToRenderQueue(card),
    onTrimToggle: payload => setControlSurfaceTrimMode(card, payload.trimMode),
    onVolumeChange: payload => setPreviewVolume(card, payload.muted ? 0 : payload.volume / 100)
  };
}
function controlSurfaceAiStatus(card){
  const edit = platformEditForRank(card.dataset.rank, activePlatformForRank(card.dataset.rank));
  return explicitCameraPathForEdit(edit).length ? "active" : "idle";
}
function controlSurfaceBusy(card){
  return card.dataset.aiApplying === "1" || controlSurfaceMapping(card);
}
function controlSurfaceMapping(card){
  if (card.dataset.aiApplying === "1") return false;
  if (controlSurfaceAiStatus(card) === "active") return false;
  return card.dataset.aiReady !== "1" && card.dataset.aiCacheReady !== "1";
}
function controlSurfaceStatus(card){
  const current = cardState(card.dataset.rank);
  const platform = activePlatformForRank(card.dataset.rank);
  const platforms = uniquePlatforms(current.platforms);
  if (card.dataset.bumperStatus) return { kind: "error", label: card.dataset.bumperStatus, tone: "red" };
  if (current.status === "discarded") return { kind: "discarded", label: "CUT DISCARDED", persistent: true, tone: "red" };
  if (card.dataset.aiApplying === "1") return { kind: "ai", label: "IA ajustando keyframes...", progress: 58, persistent: true, tone: "blue" };
  if (controlSurfaceMapping(card)) return { kind: "mapping", label: "Projeto sendo mapeado...", progress: 28, persistent: true, tone: "blue" };
  if (current.status === "liked" && platforms.includes(platform)) return { kind: "ready", label: "Ready", persistent: true, tone: "green" };
  return null;
}
function controlSurfaceAspectRatio(platform){
  const preset = resolutionPresetForPlatform(platform);
  if (preset === "vertical_4_5") return "4:5";
  if (preset === "horizontal_16_9") return "16:9";
  return "9:16";
}
function controlSurfacePlatform(aspectRatio){
  if (aspectRatio === "4:5") return "facebook";
  if (aspectRatio === "16:9") return "youtube";
  return "tiktok";
}
function controlSurfaceEffectStyle(effect){
  const key = normalizeEffect(effect).key;
  if (key === "vhs") return "vhs";
  if (key === "old-film") return "film";
  if (key === "light-grain" || key === "bw-old") return "grain";
  return "clean";
}
function appEffectKeyFromControlSurface(style){
  if (style === "vhs") return "vhs";
  if (style === "film") return "old-film";
  if (style === "grain") return "light-grain";
  return "none";
}
function setControlSurfaceFormat(card, aspectRatio){
  card.dataset.previewTouched = "1";
  setPreviewPlayback(card, false);
  setCardPreviewFormat(card, controlSurfacePlatform(aspectRatio));
  updateCardTools(card);
  renderFinalStage();
}
function openControlSurfaceBumperInput(card, slot){
  const safeSlot = normalizeBumperSlot(slot);
  updateEffectUi(card);
  const input = card.querySelector(`[data-bumper-video="${safeSlot}"]`);
  if (input) input.click();
}
function setControlSurfaceCaptions(enabled, style = null){
  document.querySelectorAll(".card[open]").forEach(card => {
    const rank = card.dataset.rank;
    const platform = activePlatformForRank(rank);
    const current = platformEditForRank(rank, platform).captions;
    const nextStyle = normalizeCaptionStyleObject(Object.assign({}, style || current.style));
    const nextEnabled = nextStyle.mode === "off" ? false : Boolean(enabled);
    setPlatformEditForRank(rank, platform, {
      captions: normalizeCaptionSettings({
        enabled: nextEnabled,
        style: nextStyle
      }, current)
    });
  });
  const nextMode = normalizeCaptionMode(style?.mode || (enabled ? "on" : "off"));
  localStorage.setItem("cutted-caption-enabled", nextMode === "off" ? "0" : "1");
  localStorage.setItem("cutted-caption-mode", nextMode);
  storeCaptionStyle(Object.assign({}, style || {}, { mode: nextMode }));
  syncCaptionInputs();
  syncPreviewCaptionsForOpenCards();
  renderCaptionQueue();
  renderFinalStage();
  document.querySelectorAll(".card[open]").forEach(updateControlSurfaceForCard);
}
function setControlSurfaceCaptionLanguage(language){
  const nextLanguage = normalizeCaptionLanguage(language);
  document.querySelectorAll(".card[open]").forEach(card => {
    const rank = card.dataset.rank;
    const platform = activePlatformForRank(rank);
    setPlatformEditForRank(rank, platform, { captionLanguage: nextLanguage });
  });
  syncPreviewCaptionsForOpenCards();
  renderCaptionQueue();
  renderFinalStage();
  document.querySelectorAll(".card[open]").forEach(updateControlSurfaceForCard);
}
function setControlSurfaceTrimMode(card, enabled){
  if (!card) return;
  const active = Boolean(enabled);
  card.dataset.trimMode = active ? "1" : "0";
  card.classList.toggle("is-trim-mode", active);
  const timeline = card.querySelector("[data-preview-camera-timeline]");
  if (timeline) timeline.dataset.trimMode = active ? "1" : "0";
  updateControlSurfaceForCard(card);
  syncLiveTimelinePlaybackState(card);
}
function markControlSurfaceReady(card){
  const current = cardState(card.dataset.rank);
  const platform = activePlatformForRank(card.dataset.rank);
  const platforms = uniquePlatforms([...(current.platforms || []), platform]);
  setCardState(card.dataset.rank, { status: "liked", platforms });
  paint(card);
  updatePlatformUi(card);
  updateControlSurfaceForCard(card);
  renderCaptionQueue();
  renderFinalStage();
}
function cancelControlSurfaceReady(card){
  const current = cardState(card.dataset.rank);
  if (current.status === "discarded") {
    setCardState(card.dataset.rank, { status: null, platforms: [] });
    paint(card);
    updatePlatformUi(card);
    updateControlSurfaceForCard(card);
    renderCaptionQueue();
    renderFinalStage();
    return;
  }
  const platform = activePlatformForRank(card.dataset.rank);
  const platforms = uniquePlatforms(current.platforms).filter(item => item !== platform);
  setCardState(card.dataset.rank, { status: platforms.length ? "liked" : null, platforms });
  paint(card);
  updatePlatformUi(card);
  updateControlSurfaceForCard(card);
  renderCaptionQueue();
  renderFinalStage();
}
function discardControlSurfaceCard(card){
  setCardState(card.dataset.rank, { status: "discarded", platforms: [] });
  paint(card);
  updatePlatformUi(card);
  updateControlSurfaceForCard(card);
  renderCaptionQueue();
  renderFinalStage();
}
function updateCameraUi(card){
  const edit = platformEditForRank(card.dataset.rank, activePlatformForRank(card.dataset.rank));
  const camera = edit.camera;
  const context = cameraContextForCard(card);
  const surface = card.querySelector(".camera-surface");
  if (surface) updateCameraSurfaceForCard(card);
  updateCardCameraSummary(card, camera, edit);
  renderPreviewCameraTimeline(card);
  const container = card.querySelector("[data-card-camera]");
  if (!container) return;
  container.innerHTML = `<div class="camera-card-controls">${cameraPathEditorHtml(card, edit, context.duration, camera)}</div>`;
  bindCardCameraControls(card);
}
function bindCardCameraControls(card){
  const rank = card.dataset.rank;
  card.querySelectorAll("[data-camera-path-marker]").forEach(button => {
    button.addEventListener("click", () => {
      setSelectedCameraPathIndex(card, button.dataset.cameraPathMarker);
      updateCameraUi(card);
      updateCameraSurfaceForCard(card);
    });
  });
  card.querySelector("[data-camera-path-add]")?.addEventListener("click", () => addCameraPathFrameForCard(card));
  card.querySelector("[data-camera-auto]")?.addEventListener("click", () => analyzeCameraForCard(card));
  card.querySelectorAll("[data-camera-smart-mode]").forEach(button => {
    button.addEventListener("click", () => analyzeCameraForCard(card, button.dataset.cameraSmartMode));
  });
  refreshAiReadinessForCard(card);
  card.querySelector("[data-camera-path-reset]")?.addEventListener("click", () => resetCameraPathForCard(card));
  card.querySelector("[data-camera-path-set-time]")?.addEventListener("click", () => moveCameraPathFrameToPlayhead(card));
  card.querySelector("[data-camera-path-delete]")?.addEventListener("click", () => deleteCameraPathFrameForCard(card));
  card.querySelector("[data-camera-path-key]")?.addEventListener("change", event => {
    updateCameraPathFrameForCard(card, { key: event.target.value });
  });
  const keyframeStrength = card.querySelector("[data-camera-path-strength]");
  keyframeStrength?.addEventListener("input", event => {
    updateCameraPathFrameForCard(card, { strength: Number(event.target.value) }, false);
  });
  keyframeStrength?.addEventListener("change", event => {
    updateCameraPathFrameForCard(card, { strength: Number(event.target.value) });
  });
  card.querySelectorAll("[data-preview-camera-segment]").forEach(select => {
    select.addEventListener("change", () => setCameraSegmentForRank(rank, select.dataset.previewCameraSegment, { key: select.value }));
  });
  card.querySelectorAll("[data-preview-camera-strength]").forEach(strength => {
    const update = () => setCameraSegmentForRank(rank, strength.dataset.previewCameraStrength, { strength: Number(strength.value) });
    strength.addEventListener("input", update);
    strength.addEventListener("change", update);
  });
}
function updateEffectUi(card){
  const effect = effectForRank(card.dataset.rank);
  const bumpers = bumpersForRank(card.dataset.rank);
  card.dataset.effect = effect.key;
  card.style.setProperty("--effect-opacity", effectOpacity(effect));
  const summary = card.querySelector("[data-effect-current]");
  if (summary) summary.textContent = `${effectLabel(effect)} | ${bumperSummary(bumpers)}`;
  renderBumperSequence(card, bumpers);
  bindBumperInputs(card);
  const container = card.querySelector("[data-card-effect]");
  if (!container) return;
  container.innerHTML = `<div class="effect-card-controls">
    <div class="effect-split">
      <section class="effect-subpanel">
        <strong>Visual</strong>
        <div class="effect-card-buttons" role="group" aria-label="Efeito do corte ${escapeAttr(card.dataset.rank)}">${effectButtonsHtml(effect)}</div>
        <label>Intensidade
          <input data-preview-effect-intensity type="range" min="0" max="100" step="5" value="${effect.intensity}">
        </label>
      </section>
      <section class="effect-subpanel">
        <strong>Vinhetas</strong>
        <div class="bumper-actions">
          ${bumperUploadHtml("intro", card.dataset.rank)}
          ${bumperUploadHtml("outro", card.dataset.rank)}
        </div>
        <div class="bumper-strip" data-bumper-strip>${bumperChipsHtml(bumpers)}</div>
        <small data-bumper-status style="min-height:16px;color:var(--color-danger);font-size:12px">${escapeHtml(card.dataset.bumperStatus || "")}</small>
        <small data-bumper-current>${escapeHtml(bumperSummary(bumpers))}</small>
      </section>
    </div>
  </div>`;
  bindCardEffectControls(card);
}
function bindBumperInputs(card){
  card.querySelectorAll("[data-bumper-video]").forEach(input => {
    if (input.dataset.bumperBound === "1") return;
    input.dataset.bumperBound = "1";
    input.addEventListener("change", () => addBumperFromInput(card, input));
  });
  card.querySelectorAll("[data-bumper-remove]").forEach(button => {
    if (button.dataset.bumperBound === "1") return;
    button.dataset.bumperBound = "1";
    button.addEventListener("click", () => removeBumperForRank(card.dataset.rank, button.dataset.bumperRemove));
  });
}
function renderBumperSequence(card, bumpers){
  const target = card.querySelector("[data-bumper-sequence]");
  if (!target) return;
  const current = normalizeBumpers(bumpers);
  const parts = [];
  if (current.intro) parts.push(`Entrada: ${current.intro.label}`);
  parts.push("Corte");
  if (current.outro) parts.push(`Saida: ${current.outro.label}`);
  target.innerHTML = parts.length > 1
    ? parts.map(part => `<span>${escapeHtml(part)}</span>`).join('<b>-></b>')
    : "";
}
function bumperUploadHtml(slot, rank){
  const label = bumperSlotLabel(slot);
  const platform = activePlatformForRank(rank);
  const preset = platformMeta[platform] || platformMeta.tiktok;
  const resolution = resolutionPresets[resolutionPresetForPlatform(platform)] || resolutionPresets.vertical_9_16;
  return `<label class="bumper-upload">
    <span>${escapeHtml(label)}</span>
    <small style="color:var(--color-text-muted);font-size:11px">${escapeHtml(resolution.label)}: ${preset.width}x${preset.height}</small>
    <input data-bumper-video="${escapeAttr(slot)}" type="file" accept="video/mp4,video/quicktime,video/webm,video/x-m4v">
  </label>`;
}
function bumperChipsHtml(bumpers){
  const current = normalizeBumpers(bumpers);
  const chips = ["intro", "outro"].map(slot => {
    const bumper = current[slot];
    if (!bumper) return "";
    const meta = [bumper.width && bumper.height ? `${bumper.width}x${bumper.height}` : "", bumper.duration ? fixed(bumper.duration) : ""].filter(Boolean).join(" - ");
    return `<span class="layer-chip bumper-chip" data-bumper-chip="${escapeAttr(slot)}">
      <span>${escapeHtml(bumperSlotLabel(slot))}: ${escapeHtml(bumper.label)}${meta ? ` (${escapeHtml(meta)})` : ""}</span>
      <button data-bumper-remove="${escapeAttr(slot)}" type="button" title="Remover vinheta" aria-label="Remover vinheta">x</button>
    </span>`;
  }).filter(Boolean).join("");
  return chips || '<span class="bumper-empty">Sem vinheta nesta plataforma</span>';
}
function bindCardEffectControls(card){
  const rank = card.dataset.rank;
  card.querySelectorAll("[data-preview-effect]").forEach(button => {
    button.addEventListener("click", () => setEffectForRank(rank, { key: button.dataset.previewEffect }));
  });
  const intensity = card.querySelector("[data-preview-effect-intensity]");
  if (intensity) {
    intensity.addEventListener("input", () => setEffectForRank(rank, { intensity: Number(intensity.value) }));
    intensity.addEventListener("change", () => setEffectForRank(rank, { intensity: Number(intensity.value) }));
  }
  bindBumperInputs(card);
}
function setBumperStatus(card, message = ""){
  card.dataset.bumperStatus = message;
  const status = card.querySelector("[data-bumper-status]");
  if (status) status.textContent = message;
}
async function addBumperFromInput(card, input){
  const file = input.files && input.files[0];
  if (!file) return;
  const rank = card.dataset.rank;
  const slot = normalizeBumperSlot(input.dataset.bumperVideo);
  const platform = activePlatformForRank(rank);
  const preset = platformMeta[platform] || platformMeta.tiktok;
  const resolution = resolutionPresets[resolutionPresetForPlatform(platform)] || resolutionPresets.vertical_9_16;
  try {
    if (file.size > maxBumperVideoBytes) throw new Error("Vinheta muito pesada. Use um video menor para o MVP local.");
    const metadata = await videoMetadataForFile(file);
    if (metadata.width !== preset.width || metadata.height !== preset.height) {
      throw new Error(`Use um video ${preset.width}x${preset.height} para ${resolution.label}.`);
    }
    showAppNotice(`Enviando vinheta de ${bumperSlotLabel(slot).toLowerCase()}...`);
    const dataUrl = await readFileAsDataUrl(file);
    const bumper = await uploadBumperAsset({
      slot,
      platform,
      label: file.name,
      width: metadata.width,
      height: metadata.height,
      duration: metadata.duration,
      data_url: dataUrl,
      gallery_path: currentGalleryPath()
    });
    setBumperForRank(rank, slot, bumper, platform);
    setBumperStatus(card, "");
    clearAppNotice();
  } catch (error) {
    const message = error.message || "Nao foi possivel usar esta vinheta.";
    showAppNotice(message);
    setBumperStatus(card, message);
    console.warn("CUTED bumper was rejected", error);
  } finally {
    input.value = "";
  }
}
function videoMetadataForFile(file){
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      const metadata = {
        width: Number(video.videoWidth || 0),
        height: Number(video.videoHeight || 0),
        duration: Number(video.duration || 0)
      };
      URL.revokeObjectURL(url);
      if (!metadata.width || !metadata.height || !metadata.duration) {
        reject(new Error("Nao consegui ler os metadados da vinheta."));
        return;
      }
      resolve(metadata);
    };
    video.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Video de vinheta invalido ou corrompido."));
    };
    video.src = url;
  });
}
async function uploadBumperAsset(payload){
  const response = await fetch("/api/bumper-assets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || !data.ok || !data.bumper) throw new Error(data.error || "Falha ao salvar a vinheta.");
  return data.bumper;
}
function updateOverlayUi(card){
  const layers = overlayLayersForRank(card.dataset.rank);
  const summary = card.querySelector("[data-overlay-current]");
  if (summary) summary.textContent = layers.length ? `${layers.length} camada(s)` : "Sem chamada";
  renderOverlayLayerBoxes(card, layers);
  renderOverlayTimeline(card);
  bindCardOverlayControls(card);
}
function renderOverlayLayerBoxes(card, layers){
  const list = card.querySelector("[data-overlay-layer-list]");
  if (list) {
    list.innerHTML = layers.map(overlayLayerBoxHtml).join("");
  }
  syncTimedOverlayVisibility(card);
  renderLayerStrip(card, layers);
}
function renderLayerStrip(card, layers){
  const strip = card.querySelector("[data-layer-strip]");
  if (!strip) return;
  const selectedId = card.dataset.selectedOverlayLayer || "";
  strip.innerHTML = layers.map(layer => {
    const selected = layer.id === selectedId ? " is-selected" : "";
    return `<span class="layer-chip${selected}" data-layer-chip="${escapeAttr(layer.id)}">
      <span>${escapeHtml(layerStripLabel(layer))}</span>
      <button data-layer-strip-remove="${escapeAttr(layer.id)}" type="button" title="Remover camada" aria-label="Remover camada">x</button>
    </span>`;
  }).join("");
  bindLayerStripControls(card, strip);
}
function layerStripLabel(layer){
  if (layer.kind === "image") return layer.label || "Imagem";
  if (layer.kind === "speech") return `Fala: ${layer.text || layer.label || ""}`.trim();
  if (layer.kind === "text") return layer.text || layer.label || "Texto";
  return overlayMeta[layer.key]?.label || layer.label || "Camada";
}
function bindLayerStripControls(card, strip){
  if (strip.dataset.layerStripBound) return;
  strip.dataset.layerStripBound = "1";
  strip.addEventListener("click", event => {
    const removeButton = event.target.closest("[data-layer-strip-remove]");
    if (removeButton) {
      event.preventDefault();
      event.stopPropagation();
      removeOverlayLayerForRank(card.dataset.rank, removeButton.dataset.layerStripRemove);
      delete card.dataset.selectedOverlayLayer;
      closeOverlayMenu(card);
      return;
    }
    const chip = event.target.closest("[data-layer-chip]");
    if (!chip) return;
    card.dataset.selectedOverlayLayer = chip.dataset.layerChip;
    showOverlayInspectorForLayer(card, chip.dataset.layerChip);
  });
}
function overlayLayerBoxHtml(layer){
  const selected = document.querySelector(`.card[data-rank="${CSS.escape(String(activeRankForLayer(layer)))}"]`)?.dataset.selectedOverlayLayer === layer.id;
  const selectedClass = selected ? " is-selected" : "";
  if (layer.kind === "image") {
    const src = layer.image_data_url || layer.image_file || "";
    return `<div class="overlay-box overlay-image-box${selectedClass}" data-overlay-drag data-overlay-layer="${escapeAttr(layer.id)}" data-overlay-key="image" ${overlayTimingAttrs(layer)} style="${escapeAttr(overlayStyle(layer))}">
      <img src="${escapeAttr(src)}" alt="${escapeAttr(layer.label)}">
      <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
    </div>`;
  }
  if (layer.kind === "text") {
    return `<div class="overlay-box overlay-text-box${selectedClass}" data-overlay-drag data-overlay-layer="${escapeAttr(layer.id)}" data-overlay-key="text" data-overlay-bg="${layer.background_enabled ? "on" : "off"}" ${overlayTimingAttrs(layer)} style="${escapeAttr(overlayStyle(layer))}">
      <span>${escapeHtml(layer.text)}</span>
      <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
    </div>`;
  }
  if (layer.kind === "speech") {
    return `<div class="overlay-box overlay-speech-box${selectedClass}" data-overlay-drag data-overlay-layer="${escapeAttr(layer.id)}" data-overlay-key="speech" ${overlayTimingAttrs(layer)} style="${escapeAttr(overlayStyle(layer))}">
      <span>${escapeHtml(layer.text)}</span>
      <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
    </div>`;
  }
  const meta = overlayMeta[layer.key] || overlayMeta.none;
  return `<div class="overlay-box${selectedClass}" data-overlay-drag data-overlay-layer="${escapeAttr(layer.id)}" data-overlay-key="${escapeAttr(layer.key)}" style="${escapeAttr(overlayStyle(layer))}">
    <strong>${escapeHtml(meta.title)}</strong>
    <em>${escapeHtml(meta.subtitle)}</em>
    <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
  </div>`;
}
function activeRankForLayer(layer){
  const card = Array.from(document.querySelectorAll(".card")).find(item => overlayLayersForRank(item.dataset.rank).some(current => current.id === layer.id));
  return card?.dataset.rank || "";
}
function overlayPlaceButtonsHtml(){
  return `<div class="overlay-icon-actions" aria-label="Adicionar camada">
      <button class="overlay-icon-action" data-overlay-place-text type="button" aria-label="Texto" title="Texto"><span aria-hidden="true">T</span></button>
      <button class="overlay-icon-action" data-overlay-place-speech type="button" aria-label="Fala" title="Fala"><span aria-hidden="true">F</span></button>
      <button class="overlay-icon-action" data-overlay-place-image type="button" aria-label="Imagem transparente" title="Imagem"><span aria-hidden="true">IMG</span></button>
      <button class="overlay-icon-action" data-overlay-place-camera type="button" aria-label="Camera" title="Camera"><span aria-hidden="true">CAM</span></button>
      <button class="overlay-icon-action overlay-icon-close" data-overlay-close type="button" aria-label="Fechar menu de camadas" title="Fechar"><span aria-hidden="true">x</span></button>
    </div>`;
}
function coverPlaceButtonsHtml(){
  return `<div class="overlay-icon-actions overlay-icon-actions-cover" aria-label="Adicionar na capa">
      <button class="overlay-icon-action" data-publish-cover-add="text" type="button" aria-label="Texto" title="Texto"><span aria-hidden="true">T</span></button>
      <button class="overlay-icon-action" data-publish-cover-add="speech" type="button" aria-label="Fala" title="Fala"><span aria-hidden="true">F</span></button>
      <button class="overlay-icon-action" data-publish-cover-add="image" type="button" aria-label="Imagem transparente" title="Imagem"><span aria-hidden="true">IMG</span></button>
      <button class="overlay-icon-action overlay-icon-close" data-overlay-close type="button" aria-label="Fechar menu da capa" title="Fechar"><span aria-hidden="true">x</span></button>
    </div>`;
}
function overlayInspectorHtml(layer){
  if (!layer) return overlayPlaceButtonsHtml();
  if (layer.kind === "image") {
    return overlayInspectorShell("Imagem", `${overlayImageSourceHtml(layer)}${overlayTimingInspectorHtml(layer)}${overlaySizeControlsHtml(layer, "Largura")}${overlayImageInspectorActionsHtml()}`);
  }
  if (layer.kind === "speech") {
    return overlayInspectorShell("Fala", `${overlayTextFieldHtml(layer)}${overlayTimingInspectorHtml(layer)}${overlayTextSizeControlsHtml(layer)}${overlaySpeechStyleHtml(layer)}${overlayRemoveButtonHtml()}`);
  }
  return overlayInspectorShell("Texto", `${overlayTextFieldHtml(layer)}${overlayTimingInspectorHtml(layer)}${overlayTextSizeControlsHtml(layer)}${overlayTextStyleHtml(layer)}${overlayRemoveButtonHtml()}`);
}
function coverInspectorHtml(layer){
  if (!layer) return "";
  if (layer.kind === "image") {
    return overlayInspectorShell("Imagem da capa", `${overlayImageSourceHtml(layer)}${overlaySizeControlsHtml(layer, "Largura")}${overlayImageInspectorActionsHtml()}`);
  }
  if (layer.kind === "speech") {
    return overlayInspectorShell("Fala da capa", `${overlayTextFieldHtml(layer)}${overlayTextSizeControlsHtml(layer)}${overlaySpeechStyleHtml(layer)}${overlayRemoveButtonHtml()}`);
  }
  return overlayInspectorShell("Texto da capa", `${overlayTextFieldHtml(layer)}${overlayTextSizeControlsHtml(layer)}${overlayTextStyleHtml(layer)}${overlayRemoveButtonHtml()}`);
}
function overlayInspectorShell(title, body){
  return `<div class="overlay-menu-head" data-overlay-menu-drag><strong>${escapeHtml(title)}</strong><button data-overlay-close>Fechar</button></div>
    <div class="overlay-inspector">
      ${body}
    </div>`;
}
function overlayTextFieldHtml(layer){
  return `<label>Conteudo
    <input data-layer-text type="text" value="${escapeAttr(layer.text || layer.label || "")}">
  </label>`;
}
function overlayTimingInspectorHtml(layer){
  const timing = overlayTimingForLayer(layer);
  return `<div class="overlay-inspector-row overlay-time-row">
    <label>Inicio
      <input data-layer-start type="number" min="0" max="9999" step="0.1" value="${timing.start.toFixed(1)}">
    </label>
    <label>Duracao
      <input data-layer-duration type="number" min="0.3" max="60" step="0.1" value="${timing.duration.toFixed(1)}">
    </label>
  </div>`;
}
function overlayTextSizeControlsHtml(layer){
  return `<div class="overlay-inspector-row">
    <label>Tamanho
      <input data-layer-font-size type="number" min="14" max="96" step="1" value="${Math.round(layer.font_size || 44)}">
    </label>
    <label>Largura
      <input data-layer-width type="range" min="16" max="90" step="1" value="${Math.round(layer.width * 100)}">
    </label>
    <label>Opacidade
      <input data-layer-opacity type="range" min="10" max="100" step="5" value="${layer.opacity}">
    </label>
  </div>`;
}
function overlaySizeControlsHtml(layer, widthLabel){
  return `<div class="overlay-inspector-row">
    <label>${escapeHtml(widthLabel)}
      <input data-layer-width type="range" min="8" max="90" step="1" value="${Math.round(layer.width * 100)}">
    </label>
    <label>Opacidade
      <input data-layer-opacity type="range" min="10" max="100" step="5" value="${layer.opacity}">
    </label>
  </div>`;
}
function overlayTextStyleHtml(layer){
  return `<details class="overlay-inspector-section" open>
    <summary>Aparencia</summary>
    <div class="overlay-inspector-row">
      <label>Cor
        <input data-layer-color type="color" value="${escapeAttr(layer.color || "#ffffff")}">
      </label>
      <label class="overlay-inspector-check">
        <input data-layer-background-enabled type="checkbox" ${layer.background_enabled ? "checked" : ""}>
        Fundo
      </label>
    </div>
    <div class="overlay-inspector-row">
      <label>Cor do fundo
        <input data-layer-background-color type="color" value="${escapeAttr(layer.background_color || "#000000")}">
      </label>
      <label>Opacidade fundo
        <input data-layer-background-opacity type="range" min="0" max="100" step="5" value="${layer.background_opacity}">
      </label>
    </div>
  </details>`;
}
function overlaySpeechStyleHtml(layer){
  return `<details class="overlay-inspector-section" open>
    <summary>Aparencia</summary>
    <div class="overlay-inspector-row">
      <label>Texto
        <input data-layer-color type="color" value="${escapeAttr(layer.color || "#050505")}">
      </label>
      <label>Balao
        <input data-layer-background-color type="color" value="${escapeAttr(layer.background_color || "#ffffff")}">
      </label>
    </div>
    <label>Opacidade do balao
      <input data-layer-background-opacity type="range" min="20" max="100" step="5" value="${layer.background_opacity}">
    </label>
  </details>`;
}
function overlayImageSourceHtml(layer){
  const src = layer.image_data_url || layer.image_file || "";
  return `<div class="overlay-image-source">
    ${src ? `<img src="${escapeAttr(src)}" alt="">` : "<span></span>"}
    <button type="button" data-layer-replace-image>Trocar imagem</button>
  </div>`;
}
function overlayImageInspectorActionsHtml(){
  return `<div class="overlay-inspector-actions">${overlayRemoveButtonHtml()}</div>`;
}
function overlayRemoveButtonHtml(){
  return `<button class="overlay-danger" data-layer-remove>Remover camada</button>`;
}
function bindCardOverlayControls(card){
  const imageInput = card.querySelector("[data-overlay-image]");
  if (imageInput && !imageInput.dataset.overlayImageBound) {
    imageInput.dataset.overlayImageBound = "1";
    imageInput.addEventListener("change", () => addImageOverlayFromInput(card, imageInput));
  }
  bindOverlayDrag(card);
  bindOverlayPlacement(card);
}
function addImageOverlayFromInput(card, input){
  const file = input.files && input.files[0];
  if (!file) return;
  const replaceLayerId = String(input.dataset.overlayReplaceLayer || "");
  const platform = overlayPlatformForItem(card);
  const currentLayer = replaceLayerId ? overlayLayersForRank(card.dataset.rank, platform).find(row => row.id === replaceLayerId) : null;
  const x = Number(input.dataset.overlayX || .36);
  const y = Number(input.dataset.overlayY || .34);
  const timing = {
    start_seconds: Number(input.dataset.overlayStart || 0),
    duration_seconds: Number(input.dataset.overlayDuration || 3)
  };
  overlayImageDataUrl(file).then(dataUrl => {
    const layer = normalizeImageOverlay({
      id: overlayId(),
      kind: "image",
      key: "image",
      label: file.name,
      image_data_url: dataUrl,
      x,
      y,
      width: .28,
      opacity: 100,
      ...timing
    });
    if (currentLayer) {
      card.dataset.selectedOverlayLayer = replaceLayerId;
      patchOverlayLayerForRank(card.dataset.rank, replaceLayerId, {
        image_data_url: dataUrl,
        image_file: "",
        label: file.name
      }, true, platform);
    } else {
      card.dataset.selectedOverlayLayer = layer.id;
      addOverlayLayerForRank(card.dataset.rank, layer, platform);
    }
    const surface = card.querySelector("[data-overlay-surface]");
    if (surface) {
      const inspectorLayer = currentLayer || layer;
      showOverlayInspectorForLayer(card, replaceLayerId || layer.id, inspectorLayer.x * surface.clientWidth, inspectorLayer.y * surface.clientHeight);
    }
    clearAppNotice();
  }).catch(error => {
    showAppNotice(error.message || "Nao foi possivel usar esta imagem. Tente uma versao menor.");
    console.warn("CUTED image overlay was rejected", error);
  }).finally(() => {
    input.value = "";
    delete input.dataset.overlayReplaceLayer;
  });
}
function overlayImageDataUrl(file){
  if (!["image/png", "image/webp", "image/jpeg"].includes(file.type)) {
    return Promise.reject(new Error("Use PNG, WebP ou JPG para a camada de imagem."));
  }
  if (file.size > maxOverlayImageSourceBytes) {
    return Promise.reject(new Error("Imagem muito pesada. Use uma versao de ate 6 MB para nao travar o editor."));
  }
  return readFileAsDataUrl(file).then(dataUrl => {
    if (dataUrl.length <= maxOverlayImageBytes) return dataUrl;
    return downscaleImageDataUrl(dataUrl, file.type);
  }).then(dataUrl => {
    if (dataUrl.length > maxOverlayImageBytes) {
      throw new Error("Imagem ainda ficou pesada depois da otimizacao. Use uma versao menor.");
    }
    return dataUrl;
  });
}
function readFileAsDataUrl(file){
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Falha ao ler a imagem."));
    reader.readAsDataURL(file);
  });
}
function downscaleImageDataUrl(dataUrl, sourceType){
  return loadImageForOverlay(dataUrl).then(image => {
    const originalWidth = image.naturalWidth || image.width;
    const originalHeight = image.naturalHeight || image.height;
    const longSide = Math.max(originalWidth, originalHeight, 1);
    const outputType = sourceType === "image/jpeg" ? "image/jpeg" : "image/webp";
    const plans = [
      { pixels: maxOverlayImagePixels, quality: outputType === "image/jpeg" ? .86 : .84 },
      { pixels: 1280, quality: outputType === "image/jpeg" ? .8 : .78 },
      { pixels: 960, quality: outputType === "image/jpeg" ? .74 : .72 },
      { pixels: 720, quality: outputType === "image/jpeg" ? .7 : .68 }
    ];
    let best = "";
    return plans.reduce((chain, plan) => chain.then(done => {
      if (done) return done;
      const scale = Math.min(1, plan.pixels / longSide);
      const width = Math.max(1, Math.round(originalWidth * scale));
      const height = Math.max(1, Math.round(originalHeight * scale));
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Nao foi possivel otimizar a imagem.");
      context.clearRect(0, 0, width, height);
      context.drawImage(image, 0, 0, width, height);
      return canvasToDataUrl(canvas, outputType, plan.quality).catch(() => canvasToDataUrl(canvas, "image/png")).then(candidate => {
        best = candidate.length < (best.length || Infinity) ? candidate : best;
        return candidate.length <= maxOverlayImageBytes ? candidate : "";
      });
    }), Promise.resolve("")).then(done => done || best);
  });
}
function loadImageForOverlay(dataUrl){
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Imagem invalida ou corrompida."));
    image.src = dataUrl;
  });
}
function canvasToDataUrl(canvas, type, quality){
  return new Promise((resolve, reject) => {
    canvas.toBlob(blob => {
      if (!blob) {
        reject(new Error("Nao foi possivel otimizar a imagem."));
        return;
      }
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(new Error("Falha ao preparar a imagem."));
      reader.readAsDataURL(blob);
    }, type, quality);
  });
}
function bindOverlayPlacement(card){
  const surface = card.querySelector("[data-overlay-surface]");
  const menu = card.querySelector("[data-overlay-menu]");
  if (!surface || !menu) return;
  surface.onclick = event => {
    if (card.dataset.overlaySuppressClick) {
      delete card.dataset.overlaySuppressClick;
      return;
    }
    if (event.target.closest("[data-overlay-drag]") || event.target.closest("[data-overlay-menu]") || event.target.closest(".preview-bar")) return;
    const rect = surface.getBoundingClientRect();
    const x = clampNumber((event.clientX - rect.left) / rect.width, 0, 1);
    const y = clampNumber((event.clientY - rect.top) / rect.height, 0, 1);
    card.dataset.overlayMenuX = x;
    card.dataset.overlayMenuY = y;
    showOverlayAddMenu(card, event.clientX - rect.left, event.clientY - rect.top);
  };
  document.addEventListener("pointerdown", event => {
    if (menu.hidden || surface.contains(event.target)) return;
    closeOverlayMenu(card);
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closeOverlayMenu(card);
  });
}
function closeOverlayMenu(card){
  const menu = card.querySelector("[data-overlay-menu]");
  if (!menu) return;
  menu.hidden = true;
  if (menu.dataset.overlayMenuMode === "add") menu.innerHTML = "";
}
function showOverlayAddMenu(card, left, top){
  const surface = card.querySelector("[data-overlay-surface]");
  const menu = card.querySelector("[data-overlay-menu]");
  if (!surface || !menu) return;
  menu.innerHTML = overlayPlaceButtonsHtml();
  menu.dataset.overlayMenuMode = "add";
  bindOverlayMenuBasics(card);
  menu.querySelector("[data-overlay-place-text]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    const layer = defaultTextOverlay();
    Object.assign(layer, overlayTimingForCard(card));
    layer.x = Number(card.dataset.overlayMenuX || .36);
    layer.y = Number(card.dataset.overlayMenuY || .34);
    card.dataset.selectedOverlayLayer = layer.id;
    addOverlayLayerForRank(card.dataset.rank, layer, overlayPlatformForItem(card));
    showOverlayInspectorForLayer(card, layer.id, left, top);
  });
  menu.querySelector("[data-overlay-place-speech]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    const layer = defaultSpeechOverlay();
    Object.assign(layer, overlayTimingForCard(card));
    layer.x = Number(card.dataset.overlayMenuX || .32);
    layer.y = Number(card.dataset.overlayMenuY || .24);
    card.dataset.selectedOverlayLayer = layer.id;
    addOverlayLayerForRank(card.dataset.rank, layer, overlayPlatformForItem(card));
    showOverlayInspectorForLayer(card, layer.id, left, top);
  });
  menu.querySelector("[data-overlay-place-image]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    const input = card.querySelector("[data-overlay-image]");
    if (!input) return;
    const timing = overlayTimingForCard(card);
    input.dataset.overlayX = String(card.dataset.overlayMenuX || .36);
    input.dataset.overlayY = String(card.dataset.overlayMenuY || .34);
    input.dataset.overlayStart = String(timing.start_seconds);
    input.dataset.overlayDuration = String(timing.duration_seconds);
    closeOverlayMenu(card);
    input.click();
  });
  menu.querySelector("[data-overlay-place-camera]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    closeOverlayMenu(card);
    addCenterCameraFrameForCard(card);
    openPreviewCameraPopover(card);
  });
  positionOverlayMenu(surface, menu, left, top);
  menu.hidden = false;
}
function showOverlayInspectorForLayer(card, layerId, left = null, top = null){
  const surface = card.querySelector("[data-overlay-surface]");
  const menu = card.querySelector("[data-overlay-menu]");
  if (!surface || !menu) return;
  const platform = overlayPlatformForItem(card);
  const layer = overlayLayersForRank(card.dataset.rank, platform).find(item => item.id === layerId);
  if (!layer) return;
  card.dataset.selectedOverlayLayer = layer.id;
  menu.innerHTML = overlayInspectorHtml(layer);
  menu.dataset.overlayMenuMode = "inspect";
  bindOverlayMenuBasics(card);
  bindOverlayInspectorControls(card, layer, platform);
  const box = card.querySelector(`[data-overlay-layer="${CSS.escape(layer.id)}"]`);
  menu.hidden = false;
  if (box) {
    positionOverlayInspectorNearLayer(surface, menu, box);
  } else {
    positionOverlayMenu(surface, menu, Number(left ?? 8), Number(top ?? 8));
  }
  renderOverlayLayerBoxes(card, overlayLayersForRank(card.dataset.rank, platform));
  bindOverlayDrag(card);
}
function positionOverlayInspectorNearLayer(surface, menu, box){
  const surfaceRect = surface.getBoundingClientRect();
  const boxRect = box.getBoundingClientRect();
  const menuWidth = menu.offsetWidth || Math.min(360, surfaceRect.width * .94);
  const menuHeight = menu.offsetHeight || 150;
  const boxLeft = boxRect.left - surfaceRect.left;
  const boxTop = boxRect.top - surfaceRect.top;
  const boxRight = boxLeft + boxRect.width;
  const boxBottom = boxTop + boxRect.height;
  const candidates = [
    { left: boxRight + 8, top: boxTop },
    { left: boxLeft - menuWidth - 8, top: boxTop },
    { left: boxLeft, top: boxTop - menuHeight - 8 },
    { left: boxLeft, top: boxBottom + 8 },
    { left: 8, top: 8 }
  ];
  const best = candidates.find(candidate => {
    const left = clampNumber(candidate.left, 8, Math.max(surfaceRect.width - menuWidth - 8, 8));
    const top = clampNumber(candidate.top, 8, Math.max(surfaceRect.height - menuHeight - 8, 8));
    return !rectsOverlap(
      { left, top, right: left + menuWidth, bottom: top + menuHeight },
      { left: boxLeft, top: boxTop, right: boxRight, bottom: boxBottom }
    );
  }) || candidates[candidates.length - 1];
  positionOverlayMenu(surface, menu, best.left, best.top);
}
function rectsOverlap(a, b){
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}
function bindOverlayMenuBasics(card){
  const surface = card.querySelector("[data-overlay-surface]");
  const menu = card.querySelector("[data-overlay-menu]");
  if (!surface || !menu) return;
  menu.querySelector("[data-overlay-close]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    closeOverlayMenu(card);
  });
  bindOverlayMenuDrag(surface, menu);
}
function bindOverlayInspectorControls(card, layer, platform = overlayPlatformForItem(card)){
  const rank = card.dataset.rank;
  const patch = (value, rerender = true) => patchOverlayLayerForRank(rank, layer.id, value, rerender, platform);
  const start = card.querySelector("[data-layer-start]");
  if (start) start.addEventListener("input", () => patch({ start_seconds: Number(start.value) }));
  const duration = card.querySelector("[data-layer-duration]");
  if (duration) duration.addEventListener("input", () => patch({ duration_seconds: Number(duration.value) }));
  const text = card.querySelector("[data-layer-text]");
  if (text) text.addEventListener("input", () => patch({ text: text.value, label: text.value }));
  const fontSize = card.querySelector("[data-layer-font-size]");
  if (fontSize) fontSize.addEventListener("input", () => patch({ font_size: Number(fontSize.value) }));
  const color = card.querySelector("[data-layer-color]");
  if (color) color.addEventListener("input", () => patch({ color: color.value }));
  const opacity = card.querySelector("[data-layer-opacity]");
  if (opacity) opacity.addEventListener("input", () => patch({ opacity: Number(opacity.value) }));
  const width = card.querySelector("[data-layer-width]");
  if (width) width.addEventListener("input", () => patch({ width: Number(width.value) / 100 }));
  card.querySelector("[data-layer-replace-image]")?.addEventListener("click", () => {
    const input = card.querySelector("[data-overlay-image]");
    if (!input) return;
    input.dataset.overlayReplaceLayer = layer.id;
    closeOverlayMenu(card);
    input.click();
  });
  const backgroundEnabled = card.querySelector("[data-layer-background-enabled]");
  if (backgroundEnabled) backgroundEnabled.addEventListener("change", () => patch({ background_enabled: backgroundEnabled.checked }));
  const backgroundColor = card.querySelector("[data-layer-background-color]");
  if (backgroundColor) backgroundColor.addEventListener("input", () => patch({ background_color: backgroundColor.value }));
  const backgroundOpacity = card.querySelector("[data-layer-background-opacity]");
  if (backgroundOpacity) backgroundOpacity.addEventListener("input", () => patch({ background_opacity: Number(backgroundOpacity.value) }));
  card.querySelector("[data-layer-remove]")?.addEventListener("click", () => {
    removeOverlayLayerForRank(rank, layer.id, platform);
    delete card.dataset.selectedOverlayLayer;
    closeOverlayMenu(card);
  });
}
function bindOverlayMenuDrag(surface, menu){
  const handle = menu.querySelector("[data-overlay-menu-drag]");
  if (!handle) return;
  let drag = null;
  const start = event => {
    if (event.type === "mousedown" && drag) return;
    if (event.target.closest("button")) return;
    const surfaceRect = surface.getBoundingClientRect();
    const menuRect = menu.getBoundingClientRect();
    drag = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      startLeft: menuRect.left - surfaceRect.left,
      startTop: menuRect.top - surfaceRect.top
    };
    if (event.pointerId !== undefined && handle.setPointerCapture) handle.setPointerCapture(event.pointerId);
    if (event.type === "mousedown") {
      document.addEventListener("mousemove", move);
      document.addEventListener("mouseup", end, { once: true });
    }
    event.preventDefault();
    event.stopPropagation();
  };
  const move = event => {
    if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
    positionOverlayMenu(surface, menu, drag.startLeft + event.clientX - drag.startX, drag.startTop + event.clientY - drag.startY);
    event.preventDefault();
    event.stopPropagation();
  };
  const end = event => {
    if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
    drag = null;
    document.removeEventListener("mousemove", move);
    event.stopPropagation();
  };
  handle.onpointerdown = start;
  handle.onpointermove = move;
  handle.onpointerup = end;
  handle.onpointercancel = end;
  handle.onmousedown = start;
}
function positionOverlayMenu(surface, menu, left, top){
  const rect = surface.getBoundingClientRect();
  const menuWidth = menu.offsetWidth || Math.min(360, rect.width * .94);
  const menuHeight = menu.offsetHeight || 150;
  menu.style.left = `${clampNumber(left, 8, Math.max(rect.width - menuWidth - 8, 8))}px`;
  menu.style.top = `${clampNumber(top, 8, Math.max(rect.height - menuHeight - 8, 8))}px`;
}
function updatePlatformUi(card){
  const current = cardState(card.dataset.rank);
  const platforms = uniquePlatforms(current.platforms);
  card.querySelectorAll("[data-platform]").forEach(btn => {
    btn.classList.toggle("active", platforms.includes(btn.dataset.platform));
  });
  const fallback = document.body.dataset.format || "tiktok";
  const summary = platforms.length
    ? `Fila: ${platforms.map(platformLabel).join(", ")}`
    : (current.status === "liked" ? `Fila: ${platformLabel(fallback)}` : "Sem destino");
  card.querySelectorAll("[data-platform-summary]").forEach(item => { item.textContent = summary; });
  const status = card.querySelector("[data-status-pill]");
  if (status) status.textContent = statusLabel(current.status);
}
function paint(card){
  const current = cardState(card.dataset.rank);
  card.classList.toggle("liked",current.status==="liked");
  card.classList.toggle("discarded",current.status==="discarded");
  const status = card.querySelector("[data-status-pill]");
  if (status) status.textContent = statusLabel(current.status);
  if (card.dataset.publishBound === "1") syncPublishPanel(card);
}
function syncPublishPanel(card){
  const moment = (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === String(card.dataset.rank));
  if (!moment) return;
  const metadata = publishMetadata(activePlatformForRank(card.dataset.rank), moment);
  const cover = metadata.cover || {};
  setPublishFieldValue(card, "title", metadata.title || "");
  setPublishFieldValue(card, "hook", metadata.hook || "");
  setPublishFieldValue(card, "description", metadata.description || "");
  setPublishFieldValue(card, "hashtags", (metadata.hashtags || []).join(" "));
  syncPublishCoverPanel(card, moment, cover);
  const tags = card.querySelector(".publish-tags");
  if (tags) tags.innerHTML = (metadata.hashtags || []).map(tag => `<span>${escapeHtml(tag)}</span>`).join("");
}
function syncPublishCoverPanel(card, moment, cover){
  const selected = cover.selected_frame || moment.frame_file || "";
  const zoom = normalizePublishCoverZoom(cover.zoom, 1);
  const x = normalizePublishCoverPosition(cover.x, zoom);
  const y = normalizePublishCoverPosition(cover.y, zoom);
  const frame = card.querySelector("[data-publish-cover-preview]");
  const preview = frame?.querySelector("img");
  if (frame) {
    frame.dataset.publishCoverCanDrag = zoom > 1.001 ? "1" : "0";
    frame.dataset.publishCoverX = String(Math.round(x));
    frame.dataset.publishCoverY = String(Math.round(y));
  }
  if (preview && selected) {
    preview.src = cacheBustedPreview(selected, `${moment.rank}-${selected}`);
    preview.style.setProperty("--publish-cover-zoom", String(zoom));
    preview.style.setProperty("--publish-cover-x", `${x}%`);
    preview.style.setProperty("--publish-cover-y", `${y}%`);
  }
  const zoomInput = card.querySelector("[data-publish-cover-zoom]");
  if (zoomInput && document.activeElement !== zoomInput) zoomInput.value = String(Math.round(zoom * 100));
  const zoomValue = card.querySelector("[data-publish-cover-zoom-value]");
  if (zoomValue) zoomValue.textContent = `${Math.round(zoom * 100)}%`;
  card.querySelectorAll("[data-publish-cover-option]").forEach(button => {
    button.classList.toggle("active", button.dataset.publishCoverOption === selected);
  });
  syncPublishCoverLayerPreview(card, cover);
  refreshPublishCoverFloatingMenu(card);
}
function syncPublishCoverLayerPreview(card, cover = null){
  const moment = (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === String(card.dataset.rank));
  const currentCover = cover || (moment ? publishMetadata(activePlatformForRank(card.dataset.rank), moment).cover || {} : {});
  const layers = normalizeCoverOverlayLayers(currentCover.layers);
  const layerList = card.querySelector("[data-publish-cover-layer-list]");
  if (layerList) layerList.innerHTML = layers.map(publishCoverLayerHtml).join("");
  const layerCount = card.querySelector("[data-publish-cover-layer-count]");
  if (layerCount) layerCount.textContent = layers.length === 1 ? "1 camada" : `${layers.length} camadas`;
  bindPublishCoverLayerControls(card);
}
function setPublishFieldValue(card, field, value){
  const input = card.querySelector(`[data-publish-field="${field}"]`);
  if (!input || document.activeElement === input) return;
  input.value = value;
}
function bindPublishCoverDrag(card){
  const frame = card.querySelector("[data-publish-cover-preview]");
  if (!frame) return;
  frame.addEventListener("pointerdown", event => beginPublishCoverDrag(card, event));
}
function bindPublishCoverPlacement(card){
  const frame = card.querySelector("[data-publish-cover-preview]");
  if (!frame || frame.dataset.publishCoverPlacementBound === "1") return;
  frame.dataset.publishCoverPlacementBound = "1";
  frame.addEventListener("click", event => {
    if (card.dataset.publishCoverFrameMoved === "1") return;
    if (event.target.closest("[data-publish-cover-layer]")) return;
    showPublishCoverAddMenu(card, event.clientX, event.clientY);
  });
}
function publishCoverForCard(card){
  const moment = (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === String(card.dataset.rank));
  if (!moment) return null;
  const metadata = publishMetadata(activePlatformForRank(card.dataset.rank), moment);
  return metadata.cover || {};
}
function beginPublishCoverDrag(card, event){
  if (event.button !== undefined && event.button !== 0) return;
  if (event.target.closest("[data-publish-cover-layer]")) return;
  const frame = event.currentTarget;
  const cover = publishCoverForCard(card);
  if (!cover) return;
  const zoom = normalizePublishCoverZoom(cover.zoom, 1);
  if (zoom <= 1.001) return;
  const rect = frame.getBoundingClientRect();
  const drag = {
    rank: card.dataset.rank,
    startClientX: event.clientX,
    startClientY: event.clientY,
    startX: normalizePublishCoverPosition(cover.x, zoom),
    startY: normalizePublishCoverPosition(cover.y, zoom),
    width: Math.max(rect.width, 1),
    height: Math.max(rect.height, 1),
    zoom,
    moved: false
  };
  event.preventDefault();
  frame.dataset.publishCoverDragging = "1";
  frame.setPointerCapture?.(event.pointerId);
  const move = pointerEvent => movePublishCoverDrag(card, drag, pointerEvent);
  const end = () => endPublishCoverDrag(frame, event.pointerId, move, end);
  frame.addEventListener("pointermove", move);
  frame.addEventListener("pointerup", end);
  frame.addEventListener("pointercancel", end);
}
function movePublishCoverDrag(card, drag, event){
  event.preventDefault();
  if (Math.abs(event.clientX - drag.startClientX) > 2 || Math.abs(event.clientY - drag.startClientY) > 2) drag.moved = true;
  if (drag.moved) card.querySelector("[data-publish-cover-preview]")?.setAttribute("data-publish-cover-moved", "1");
  const publish = normalizePublishEdit(cardState(drag.rank).publish);
  publish.coverZoom = drag.zoom;
  publish.coverX = normalizePublishCoverPosition(drag.startX + publishCoverDragDelta(drag.startClientX, event.clientX, drag.width, drag.zoom), drag.zoom);
  publish.coverY = normalizePublishCoverPosition(drag.startY + publishCoverDragDelta(drag.startClientY, event.clientY, drag.height, drag.zoom), drag.zoom);
  setCardState(drag.rank, { publish });
  syncPublishPanel(card);
}
function endPublishCoverDrag(frame, pointerId, move, end){
  const card = frame.closest(".card");
  if (card && frame.dataset.publishCoverMoved === "1") {
    card.dataset.publishCoverFrameMoved = "1";
    window.setTimeout(() => { delete card.dataset.publishCoverFrameMoved; }, 120);
  }
  delete frame.dataset.publishCoverMoved;
  frame.dataset.publishCoverDragging = "0";
  if (frame.hasPointerCapture?.(pointerId)) frame.releasePointerCapture(pointerId);
  frame.removeEventListener("pointermove", move);
  frame.removeEventListener("pointerup", end);
  frame.removeEventListener("pointercancel", end);
  renderCaptionQueue();
}
function publishCoverDragDelta(start, current, size, zoom){
  const zoomGap = Math.max(normalizePublishCoverZoom(zoom, 1) - 1, 0.08);
  return ((start - current) / Math.max(size, 1)) * 100 / zoomGap;
}
function bindPublishCoverImageInput(card){
  const input = card.querySelector("[data-publish-cover-image]");
  if (!input || input.dataset.publishCoverImageBound === "1") return;
  input.dataset.publishCoverImageBound = "1";
  input.addEventListener("change", () => addPublishCoverImageFromInput(card, input));
}
function addPublishCoverLayer(card, kind){
  if (kind === "image") {
    const input = card.querySelector("[data-publish-cover-image]");
    if (input) {
      delete input.dataset.coverReplaceLayer;
      input.dataset.coverX = String(card.dataset.coverMenuX || .28);
      input.dataset.coverY = String(card.dataset.coverMenuY || .28);
      closePublishCoverMenu(card);
      input.click();
    }
    return;
  }
  const layer = kind === "speech" ? defaultSpeechOverlay() : defaultTextOverlay();
  layer.x = clampNumber(Number(card.dataset.coverMenuX || (kind === "speech" ? .18 : .16)), 0, .84);
  layer.y = clampNumber(Number(card.dataset.coverMenuY || (kind === "speech" ? .18 : .12)), 0, .9);
  layer.width = kind === "speech" ? .64 : .68;
  layer.start_seconds = 0;
  layer.duration_seconds = 3;
  card.dataset.selectedCoverLayer = layer.id;
  addCoverLayerForRank(card.dataset.rank, layer);
  showPublishCoverInspector(card, layer.id);
}
function addPublishCoverImageFromInput(card, input){
  const file = input.files && input.files[0];
  if (!file) return;
  const replaceLayerId = String(input.dataset.coverReplaceLayer || "");
  overlayImageDataUrl(file).then(dataUrl => {
    if (replaceLayerId) {
      patchCoverLayerForRank(card.dataset.rank, replaceLayerId, {
        image_data_url: dataUrl,
        image_file: "",
        label: file.name
      });
      card.dataset.selectedCoverLayer = replaceLayerId;
      showPublishCoverInspector(card, replaceLayerId);
    } else {
      const layer = normalizeImageOverlay({
        id: overlayId(),
        kind: "image",
        key: "image",
        label: file.name,
        image_data_url: dataUrl,
        x: clampNumber(Number(input.dataset.coverX || .28), 0, .92),
        y: clampNumber(Number(input.dataset.coverY || .28), 0, .92),
        width: .42,
        opacity: 100,
        start_seconds: 0,
        duration_seconds: 3
      });
      card.dataset.selectedCoverLayer = layer.id;
      addCoverLayerForRank(card.dataset.rank, layer);
      showPublishCoverInspector(card, layer.id);
    }
    clearAppNotice();
  }).catch(error => {
    showAppNotice(error.message || "Nao foi possivel usar esta imagem na capa.");
    console.warn("CUTED cover image overlay was rejected", error);
  }).finally(() => {
    input.value = "";
    delete input.dataset.coverReplaceLayer;
    delete input.dataset.coverX;
    delete input.dataset.coverY;
  });
}
function coverLayersForRank(rank){
  return normalizePublishEdit(cardState(String(rank)).publish).coverLayers;
}
function setCoverLayersForRank(rank, layers, rerender = true){
  const current = cardState(String(rank));
  const publish = normalizePublishEdit(current.publish);
  publish.coverLayers = normalizeCoverOverlayLayers(layers);
  setCardState(String(rank), { publish });
  const card = cardForRank(rank);
  if (rerender && card) syncPublishPanel(card);
  if (rerender) renderCaptionQueue();
}
function addCoverLayerForRank(rank, layer){
  setCoverLayersForRank(rank, [...coverLayersForRank(rank), normalizeOverlayLayer(layer)]);
}
function patchCoverLayerForRank(rank, id, patch, rerender = true){
  const layers = coverLayersForRank(rank).map(layer => {
    if (layer.id !== id) return layer;
    return normalizeOverlayLayer(Object.assign({}, layer, patch));
  });
  setCoverLayersForRank(rank, layers, rerender);
}
function removeCoverLayerForRank(rank, id){
  setCoverLayersForRank(rank, coverLayersForRank(rank).filter(layer => layer.id !== id));
}
function selectedCoverLayerForCard(card){
  const selected = String(card.dataset.selectedCoverLayer || "");
  return coverLayersForRank(card.dataset.rank).find(layer => layer.id === selected) || null;
}
function publishCoverMenuSurface(card){
  return card.querySelector("[data-publish-cover-stage]") || card.querySelector("[data-publish-cover-preview]");
}
function closePublishCoverMenu(card){
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!menu) return;
  menu.hidden = true;
  menu.innerHTML = "";
  delete card.dataset.selectedCoverLayer;
}
function bindPublishCoverMenuBasics(card){
  const surface = publishCoverMenuSurface(card);
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!surface || !menu) return;
  menu.querySelector("[data-overlay-close]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    closePublishCoverMenu(card);
  });
  bindOverlayMenuDrag(surface, menu);
}
function publishCoverMenuPoint(card, clientX, clientY){
  const frame = card.querySelector("[data-publish-cover-preview]");
  const surface = publishCoverMenuSurface(card);
  const frameRect = frame?.getBoundingClientRect();
  const surfaceRect = surface?.getBoundingClientRect();
  if (!frameRect || !surfaceRect) return { x: .28, y: .28, left: 8, top: 8 };
  const x = clampNumber((clientX - frameRect.left) / Math.max(frameRect.width, 1), 0, .92);
  const y = clampNumber((clientY - frameRect.top) / Math.max(frameRect.height, 1), 0, .92);
  return { x, y, left: clientX - surfaceRect.left, top: clientY - surfaceRect.top };
}
function showPublishCoverAddMenu(card, clientX, clientY){
  const surface = publishCoverMenuSurface(card);
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!surface || !menu) return;
  const point = publishCoverMenuPoint(card, clientX, clientY);
  card.dataset.coverMenuX = String(point.x);
  card.dataset.coverMenuY = String(point.y);
  delete card.dataset.selectedCoverLayer;
  menu.innerHTML = coverPlaceButtonsHtml();
  menu.dataset.overlayMenuMode = "add";
  bindPublishCoverMenuBasics(card);
  bindPublishCoverAddButtons(card);
  positionOverlayMenu(surface, menu, point.left, point.top);
  menu.hidden = false;
}
function refreshPublishCoverFloatingMenu(card){
  const layer = selectedCoverLayerForCard(card);
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!menu || menu.hidden || !layer) return;
  showPublishCoverInspector(card, layer.id);
}
function showPublishCoverInspector(card, layerId){
  const surface = publishCoverMenuSurface(card);
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!surface || !menu) return;
  card.dataset.selectedCoverLayer = layerId;
  const layer = selectedCoverLayerForCard(card);
  if (!layer) return;
  menu.innerHTML = coverInspectorHtml(layer);
  menu.dataset.overlayMenuMode = "inspect";
  bindPublishCoverMenuBasics(card);
  bindPublishCoverInspectorControls(card, layer);
  menu.hidden = false;
  const box = card.querySelector(`[data-publish-cover-layer="${CSS.escape(layer.id)}"]`);
  if (box) positionOverlayInspectorNearLayer(surface, menu, box);
  else positionOverlayMenu(surface, menu, 8, 8);
}
function bindPublishCoverInspectorControls(card, layer){
  const rank = card.dataset.rank;
  const patch = value => {
    patchCoverLayerForRank(rank, layer.id, value, false);
    syncPublishCoverLayerPreview(card);
    renderCaptionQueue();
  };
  const menu = card.querySelector("[data-publish-cover-menu]");
  const text = menu?.querySelector("[data-layer-text]");
  if (text) text.addEventListener("input", () => patch({ text: text.value, label: text.value }));
  const fontSize = menu?.querySelector("[data-layer-font-size]");
  if (fontSize) fontSize.addEventListener("input", () => patch({ font_size: Number(fontSize.value) }));
  const color = menu?.querySelector("[data-layer-color]");
  if (color) color.addEventListener("input", () => patch({ color: color.value }));
  const opacity = menu?.querySelector("[data-layer-opacity]");
  if (opacity) opacity.addEventListener("input", () => patch({ opacity: Number(opacity.value) }));
  const width = menu?.querySelector("[data-layer-width]");
  if (width) width.addEventListener("input", () => patch({ width: Number(width.value) / 100 }));
  const backgroundEnabled = menu?.querySelector("[data-layer-background-enabled]");
  if (backgroundEnabled) backgroundEnabled.addEventListener("change", () => patch({ background_enabled: backgroundEnabled.checked }));
  const backgroundColor = menu?.querySelector("[data-layer-background-color]");
  if (backgroundColor) backgroundColor.addEventListener("input", () => patch({ background_color: backgroundColor.value }));
  const backgroundOpacity = menu?.querySelector("[data-layer-background-opacity]");
  if (backgroundOpacity) backgroundOpacity.addEventListener("input", () => patch({ background_opacity: Number(backgroundOpacity.value) }));
  menu?.querySelector("[data-layer-replace-image]")?.addEventListener("click", () => {
    const input = card.querySelector("[data-publish-cover-image]");
    if (!input) return;
    input.dataset.coverReplaceLayer = layer.id;
    closePublishCoverMenu(card);
    input.click();
  });
  menu?.querySelector("[data-layer-remove]")?.addEventListener("click", () => {
    removeCoverLayerForRank(rank, layer.id);
    closePublishCoverMenu(card);
  });
}
function bindPublishCoverAddButtons(card){
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!menu) return;
  menu.querySelectorAll("[data-publish-cover-add]").forEach(button => {
    button.addEventListener("click", () => addPublishCoverLayer(card, button.dataset.publishCoverAdd));
  });
}
function bindPublishCoverLayerControls(card){
  const frame = card.querySelector("[data-publish-cover-preview]");
  if (!frame) return;
  frame.querySelectorAll("[data-publish-cover-layer]").forEach(layerNode => bindPublishCoverLayerDrag(card, frame, layerNode));
}
function bindPublishCoverLayerDrag(card, frame, layerNode){
  let drag = null;
  const start = event => {
    if (event.type === "mousedown" && drag) return;
    const resizing = !!event.target?.closest?.("[data-publish-cover-resize]");
    const frameRect = frame.getBoundingClientRect();
    const layerRect = layerNode.getBoundingClientRect();
    drag = {
      pointerId: event.pointerId,
      type: resizing ? "resize" : "move",
      startX: event.clientX,
      startY: event.clientY,
      startLeft: layerRect.left - frameRect.left,
      startTop: layerRect.top - frameRect.top,
      startWidth: layerRect.width,
      frameWidth: Math.max(frameRect.width, 1),
      frameHeight: Math.max(frameRect.height, 1),
      moved: false
    };
    card.dataset.selectedCoverLayer = layerNode.dataset.publishCoverLayer;
    layerNode.classList.add("is-selected");
    if (event.pointerId !== undefined && layerNode.setPointerCapture) layerNode.setPointerCapture(event.pointerId);
    document.addEventListener("pointermove", move);
    document.addEventListener("pointerup", end, { once: true });
    document.addEventListener("pointercancel", end, { once: true });
    document.addEventListener("mousemove", move);
    document.addEventListener("mouseup", end, { once: true });
    event.preventDefault();
    event.stopPropagation();
  };
  const move = event => {
    if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) drag.moved = true;
    const patch = {};
    if (drag.type === "resize") {
      const minWidth = layerNode.dataset.coverLayerKind === "image" ? .08 : .16;
      patch.width = clampNumber((drag.startWidth + dx) / drag.frameWidth, minWidth, .9);
      layerNode.style.width = `${patch.width * 100}%`;
    } else {
      const layerRect = layerNode.getBoundingClientRect();
      const left = clampNumber(drag.startLeft + dx, 0, Math.max(drag.frameWidth - layerRect.width, 0));
      const top = clampNumber(drag.startTop + dy, 0, Math.max(drag.frameHeight - layerRect.height, 0));
      patch.x = left / drag.frameWidth;
      patch.y = clampNumber(top / drag.frameHeight + coverLayerVerticalLift, 0, 1);
      layerNode.style.left = `${patch.x * 100}%`;
      layerNode.style.top = `${liftedCoverLayerY(patch.y) * 100}%`;
    }
    patchCoverLayerForRank(card.dataset.rank, layerNode.dataset.publishCoverLayer, patch, false);
    event.preventDefault();
    event.stopPropagation();
  };
  const end = event => {
    if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
    const shouldInspect = !drag.moved;
    drag = null;
    document.removeEventListener("pointermove", move);
    document.removeEventListener("mousemove", move);
    document.removeEventListener("pointerup", end);
    document.removeEventListener("pointercancel", end);
    document.removeEventListener("mouseup", end);
    syncPublishPanel(card);
    renderCaptionQueue();
    if (shouldInspect) showPublishCoverInspector(card, layerNode.dataset.publishCoverLayer);
    event.preventDefault();
    event.stopPropagation();
  };
  layerNode.onpointerdown = start;
  layerNode.onmousedown = start;
  layerNode.querySelectorAll("[data-publish-cover-resize]").forEach(handle => {
    handle.onpointerdown = start;
    handle.onmousedown = start;
  });
}
function bindPublishPanel(card){
  if (card.dataset.publishBound === "1") return;
  card.dataset.publishBound = "1";
  syncPublishPanel(card);
  bindPublishCoverDrag(card);
  bindPublishCoverPlacement(card);
  bindPublishCoverImageInput(card);
  card.querySelectorAll("[data-publish-field]").forEach(input => {
    input.addEventListener("input", () => {
      const current = cardState(card.dataset.rank);
      const publish = normalizePublishEdit(current.publish);
      publish[input.dataset.publishField] = input.dataset.publishField === "hashtags"
        ? normalizePublishHashtags(input.value)
        : cleanPublishField(input.value, input.dataset.publishField === "description" ? 360 : 140);
      setCardState(card.dataset.rank, { publish });
      syncPublishPanel(card);
      renderCaptionQueue();
    });
  });
  card.querySelectorAll("[data-publish-cover-option]").forEach(button => {
    button.addEventListener("click", () => {
      const publish = normalizePublishEdit(cardState(card.dataset.rank).publish);
      publish.coverFrame = cleanPublishField(button.dataset.publishCoverOption, 260);
      setCardState(card.dataset.rank, { publish });
      syncPublishPanel(card);
      renderCaptionQueue();
    });
  });
  card.querySelector("[data-publish-cover-zoom]")?.addEventListener("input", event => {
    const publish = normalizePublishEdit(cardState(card.dataset.rank).publish);
    const zoom = normalizePublishCoverZoom(Number(event.target.value) / 100, 1);
    publish.coverZoom = zoom;
    if (zoom <= 1.001) {
      publish.coverX = 50;
      publish.coverY = 50;
    }
    setCardState(card.dataset.rank, { publish });
    syncPublishPanel(card);
    renderCaptionQueue();
  });
  card.querySelector("[data-publish-cover-zoom-reset]")?.addEventListener("click", () => {
    const publish = normalizePublishEdit(cardState(card.dataset.rank).publish);
    publish.coverZoom = 1;
    publish.coverX = 50;
    publish.coverY = 50;
    setCardState(card.dataset.rank, { publish });
    syncPublishPanel(card);
    renderCaptionQueue();
  });
  card.querySelector("[data-publish-reset]")?.addEventListener("click", () => {
    setCardState(card.dataset.rank, { publish: {} });
    syncPublishPanel(card);
    renderCaptionQueue();
  });
}
function trimValues(card){
  const start = Number(card.dataset.start);
  const end = Number(card.dataset.end);
  const duration = Number(card.dataset.duration);
  const current = cardState(card.dataset.rank);
  const trimStart = Math.min(Number(current.trimStart || 0), Math.max(duration - 1, 0));
  const trimEnd = Math.min(Number(current.trimEnd || 0), Math.max(duration - trimStart - 1, 0));
  return { start, end, duration, trimStart, trimEnd, startPos: trimStart, endPos: duration - trimEnd, adjustedStart: start + trimStart, adjustedEnd: end - trimEnd };
}
function updateTrimUi(card){
  const values = trimValues(card);
  const startInput = card.querySelector("[data-trim=start]");
  const endInput = card.querySelector("[data-trim=end]");
  const scrubInput = card.querySelector("[data-trim-scrub]");
  if (startInput) {
    startInput.max = values.duration.toFixed(1);
    startInput.value = values.startPos;
  }
  if (endInput) {
    endInput.max = values.duration.toFixed(1);
    endInput.value = values.endPos;
  }
  if (scrubInput) scrubInput.max = values.duration.toFixed(1);
  const startOutput = card.querySelector("[data-output=start]");
  const endOutput = card.querySelector("[data-output=end]");
  if (startOutput) startOutput.textContent = fixed(values.trimStart);
  if (endOutput) endOutput.textContent = fixed(values.trimEnd);
  const summary = `${fixed(values.adjustedStart)} - ${fixed(values.adjustedEnd)} (${fixed(values.adjustedEnd - values.adjustedStart)})`;
  const trimSummary = card.querySelector("[data-trim-summary]");
  if (trimSummary) trimSummary.textContent = summary;
  const cardSummary = card.querySelector("[data-card-summary]");
  if (cardSummary) cardSummary.textContent = summary;
  const fill = card.querySelector("[data-trim-fill]");
  const duration = Math.max(values.duration, .1);
  if (fill) {
    fill.style.left = `${(values.startPos / duration) * 100}%`;
    fill.style.right = `${100 - ((values.endPos / duration) * 100)}%`;
  }
  const selected = card.querySelector("[data-timeline-selected]");
  if (selected && fill) {
    selected.style.left = fill.style.left;
    selected.style.right = fill.style.right;
  }
  const windowLabel = card.querySelector("[data-timeline-window]");
  if (windowLabel) windowLabel.textContent = `${fixed(values.startPos)} - ${fixed(values.endPos)} no clipe`;
  renderCardRowTimeline(card, values);
  updateTimelinePlayhead(card);
  syncPreviewCaptions(card);
}
function renderCardRowTimeline(card, values = null){
  const container = card.querySelector("[data-card-row-timeline]");
  if (!container) return;
  if (card.open && (card.__liveTimelineController || card.__liveTimelineLoading)) return;
  const current = values || trimValues(card);
  const duration = Math.max(current.duration, .1);
  const endPos = trimEndPosition(current);
  const platform = activePlatformForRank(card.dataset.rank);
  const edit = platformEditForRank(card.dataset.rank, platform);
  const path = cameraPathForEdit(edit, duration).slice(0, 24);
  const left = clampNumber((current.trimStart / duration) * 100, 0, 100);
  const right = clampNumber((endPos / duration) * 100, 0, 100);
  const context = cameraContextForCard(card);
  const playhead = clampNumber((context.position / duration) * 100, 0, 100);
  const markers = path.map(frame => {
    const markerLeft = clampNumber((Number(frame.time || 0) / duration) * 100, 0, 100);
    const label = directorMarkerTitle(edit.director_plan, frame);
    return `<span class="clip-row-timeline-marker" style="left:${markerLeft.toFixed(2)}%" title="${escapeAttr(label)}"></span>`;
  }).join("");
  container.innerHTML = `<span class="clip-row-timeline-track"></span>
    <span class="clip-row-timeline-window" style="left:${left.toFixed(2)}%;right:${(100 - right).toFixed(2)}%"></span>
    ${markers}
    <span class="clip-row-timeline-playhead" style="left:${playhead.toFixed(2)}%"></span>`;
}
function updateTimelinePlayhead(card, time = null){
  const values = trimValues(card);
  const video = primaryCameraVideo(card);
  const raw = time === null && video && Number.isFinite(video.currentTime) ? video.currentTime : time;
  const current = clampPreviewTime(values, Number(raw ?? values.trimStart));
  if (time === null && video && trimRangeActive(values) && Math.abs(Number(video.currentTime || 0) - current) > .05) {
    video.currentTime = current;
  }
  syncPreviewPlaybackFrame(card, current);
}
function syncPreviewPlaybackFrame(card, time = null){
  const values = trimValues(card);
  const video = primaryCameraVideo(card);
  const raw = time === null && video && Number.isFinite(video.currentTime) ? video.currentTime : time;
  const current = clampPreviewTime(values, Number(raw ?? values.trimStart));
  const scrubInput = card.querySelector("[data-trim-scrub]");
  if (scrubInput) scrubInput.value = current.toFixed(1);
  const playhead = card.querySelector("[data-timeline-playhead]");
  if (playhead) playhead.style.left = `${(current / Math.max(values.duration, .1)) * 100}%`;
  const output = card.querySelector("[data-output=current]");
  if (output) output.textContent = fixed(values.start + current);
  updateCameraSurfaceForCard(card, current);
  updatePreviewCameraTimelinePlayhead(card, current);
  syncPreviewCaptions(card, current);
  syncTimedOverlayVisibility(card, current);
}
function previewCameraTimelineContext(card){
  const values = trimValues(card);
  const context = cameraContextForCard(card);
  const duration = cameraTimelineDurationForCard(card);
  const platform = activePlatformForRank(card.dataset.rank);
  const edit = platformEditForRank(card.dataset.rank, platform);
  const path = cameraPathForEdit(edit, duration);
  return { values, context, duration, platform, edit, path };
}
function renderPreviewCameraTimeline(card){
  if (card.open) {
    if (renderLivePreviewCameraTimeline(card)) return;
    renderLegacyPreviewCameraTimeline(card);
    return;
  }
  destroyLivePreviewCameraTimeline(card);
  renderCardRowTimeline(card);
}
function overlayTimelineLayersForCard(card){
  return overlayLayersForRank(card.dataset.rank)
    .filter(layer => ["image", "speech", "text"].includes(layer.kind));
}
function overlayTimelineLabel(layer){
  if (layer.kind === "image") return "Img";
  if (layer.kind === "speech") return "Fala";
  return "Texto";
}
function overlayTimelineItemHtml(layer, duration, index){
  const timing = overlayTimingForLayer(layer);
  const start = clampNumber(timing.start, 0, Math.max(duration - .3, 0));
  const itemDuration = clampNumber(timing.duration, .3, Math.max(duration - start, .3));
  const left = clampNumber((start / Math.max(duration, .3)) * 100, 0, 100);
  const width = clampNumber((itemDuration / Math.max(duration, .3)) * 100, 1, 100 - left);
  const row = index % 3;
  const selected = document.querySelector(`.card[data-rank="${CSS.escape(String(activeRankForLayer(layer)))}"]`)?.dataset.selectedOverlayLayer === layer.id;
  return `<button class="overlay-timeline-item${selected ? " is-selected" : ""}" data-overlay-timeline-layer="${escapeAttr(layer.id)}" data-overlay-kind="${escapeAttr(layer.kind)}" data-overlay-start="${start.toFixed(3)}" data-overlay-duration="${itemDuration.toFixed(3)}" style="--overlay-time-left:${left.toFixed(3)}%;--overlay-time-width:${width.toFixed(3)}%;--overlay-time-row:${row}" type="button" title="${escapeAttr(`${overlayTimelineLabel(layer)} ${fixed(start)} por ${fixed(itemDuration)}`)}"><span>${escapeHtml(overlayTimelineLabel(layer))}</span><i data-overlay-timeline-resize></i></button>`;
}
function renderOverlayTimeline(card){
  const container = card.querySelector("[data-preview-camera-timeline]");
  if (!container) return;
  let track = card.querySelector("[data-overlay-timeline]");
  const layers = overlayTimelineLayersForCard(card);
  if (!track) {
    track = document.createElement("div");
    track.className = "overlay-timeline";
    track.setAttribute("data-overlay-timeline", "");
  }
  if (track.parentElement !== container) {
    container.appendChild(track);
  }
  const duration = cameraTimelineDurationForCard(card);
  track.innerHTML = layers.map((layer, index) => overlayTimelineItemHtml(layer, duration, index)).join("");
  track.hidden = !layers.length;
  bindOverlayTimelineControls(card, track);
  syncTimedOverlayVisibility(card);
}
function bindOverlayTimelineControls(card, track){
  if (track.dataset.overlayTimelineBound) return;
  track.dataset.overlayTimelineBound = "1";
  track.addEventListener("pointerdown", event => startOverlayTimelineDrag(card, track, event));
}
function startOverlayTimelineDrag(card, track, event){
  const item = event.target.closest("[data-overlay-timeline-layer]");
  if (!item) return;
  event.preventDefault();
  event.stopPropagation();
  const platform = overlayPlatformForItem(card);
  const layer = overlayLayersForRank(card.dataset.rank, platform).find(row => row.id === item.dataset.overlayTimelineLayer);
  if (!layer) return;
  const timing = overlayTimingForLayer(layer);
  const state = {
    duration: cameraTimelineDurationForCard(card),
    id: layer.id,
    moved: false,
    resizing: Boolean(event.target.closest("[data-overlay-timeline-resize]")),
    startDuration: timing.duration,
    startSeconds: timing.start,
    startX: event.clientX
  };
  if (item.setPointerCapture && event.pointerId !== undefined) item.setPointerCapture(event.pointerId);
  const move = moveEvent => moveOverlayTimelineDrag(card, track, item, state, moveEvent, platform);
  const end = endEvent => endOverlayTimelineDrag(card, item, state, endEvent, move, platform);
  document.addEventListener("pointermove", move);
  document.addEventListener("pointerup", end, { once: true });
  document.addEventListener("pointercancel", end, { once: true });
}
function overlayTimelinePatchFromDrag(track, state, event){
  const rect = track.getBoundingClientRect();
  const delta = rect.width ? ((event.clientX - state.startX) / rect.width) * state.duration : 0;
  if (state.resizing) {
    const maxDuration = Math.max(state.duration - state.startSeconds, .3);
    return { duration_seconds: Number(clampNumber(state.startDuration + delta, .3, maxDuration).toFixed(3)) };
  }
  const start = clampNumber(state.startSeconds + delta, 0, Math.max(state.duration - state.startDuration, 0));
  return { start_seconds: Number(start.toFixed(3)) };
}
function moveOverlayTimelineDrag(card, track, item, state, event, platform){
  event.preventDefault();
  event.stopPropagation();
  state.moved = state.moved || Math.abs(event.clientX - state.startX) > 2;
  const patch = overlayTimelinePatchFromDrag(track, state, event);
  patchOverlayLayerForRank(card.dataset.rank, state.id, patch, false, platform);
  updateOverlayTimingDom(card, state.id, patch);
  updateOverlayTimelineItem(item, patch, state.duration);
  syncTimedOverlayVisibility(card);
}
function endOverlayTimelineDrag(card, item, state, event, move, platform){
  document.removeEventListener("pointermove", move);
  event.preventDefault();
  event.stopPropagation();
  if (!state.moved) {
    card.dataset.selectedOverlayLayer = state.id;
    showOverlayInspectorForLayer(card, state.id);
  }
  renderOverlayTimeline(card);
}
function updateOverlayTimingDom(card, layerId, patch){
  const box = card.querySelector(`[data-overlay-layer="${CSS.escape(layerId)}"]`);
  if (box && patch.start_seconds !== undefined) box.dataset.overlayStart = Number(patch.start_seconds).toFixed(3);
  if (box && patch.duration_seconds !== undefined) box.dataset.overlayDuration = Number(patch.duration_seconds).toFixed(3);
}
function updateOverlayTimelineItem(item, patch, totalDuration){
  const start = clampNumber(patch.start_seconds ?? item.dataset.overlayStart ?? 0, 0, Math.max(totalDuration - .3, 0));
  const duration = clampNumber(patch.duration_seconds ?? item.dataset.overlayDuration ?? 3, .3, Math.max(totalDuration - start, .3));
  item.dataset.overlayStart = start.toFixed(3);
  item.dataset.overlayDuration = duration.toFixed(3);
  item.style.setProperty("--overlay-time-left", `${((start / Math.max(totalDuration, .3)) * 100).toFixed(3)}%`);
  item.style.setProperty("--overlay-time-width", `${((duration / Math.max(totalDuration, .3)) * 100).toFixed(3)}%`);
}
function renderLivePreviewCameraTimeline(card){
  const container = card.querySelector("[data-preview-camera-timeline]");
  if (!container || container.dataset.liveTimelineFailed === "1") return false;
  const live = window.CuttedLiveTimeline;
  if (!live || typeof live.createLiveTimeline !== "function") return false;
  const options = liveTimelineOptionsForCard(card);
  container.classList.add("preview-camera-timeline--live");
  if (card.__liveTimelineController) {
    ensureLivePreviewCameraPopover(card);
    card.__liveTimelineController.update(options);
    loadLiveTimelineWaveform(card);
    renderOverlayTimeline(card);
    return true;
  }
  if (card.__liveTimelineLoading) return true;
  card.__liveTimelineLoading = true;
  container.innerHTML = '<div class="preview-live-timeline-loading">Carregando timeline...</div>';
  live.createLiveTimeline(container, options).then(controller => {
    card.__liveTimelineController = controller;
    delete card.__liveTimelineLoading;
    controller.update(liveTimelineOptionsForCard(card));
    ensureLivePreviewCameraPopover(card);
    loadLiveTimelineWaveform(card);
    renderOverlayTimeline(card);
  }).catch(error => {
    console.warn("Timeline viva indisponivel; usando timeline compacta.", error);
    delete card.__liveTimelineLoading;
    container.dataset.liveTimelineFailed = "1";
    renderLegacyPreviewCameraTimeline(card);
  });
  return true;
}
function destroyLivePreviewCameraTimeline(card){
  if (card.__liveTimelineController && typeof card.__liveTimelineController.destroy === "function") {
    card.__liveTimelineController.destroy();
  }
  delete card.__liveTimelineController;
  delete card.__liveTimelineLoading;
  const container = card.querySelector("[data-preview-camera-timeline]");
  if (container) {
    container.classList.remove("preview-camera-timeline--live");
    container.removeAttribute("style");
  }
}
function liveTimelineOptionsForCard(card){
  const values = trimValues(card);
  const duration = cameraTimelineDurationForCard(card);
  const platform = activePlatformForRank(card.dataset.rank);
  const edit = platformEditForRank(card.dataset.rank, platform);
  const path = cameraPathForEdit(edit, duration);
  const video = primaryCameraVideo(card);
  const pending = Number(card.dataset.pendingSeek);
  const playhead = Number.isFinite(pending) ? pending : cameraTimelinePositionForCard(card);
  const model = {
    cameraPath: path,
    duration,
    effectKeyframes: liveTimelineEffectKeyframesForCard(card),
    muted: video ? video.muted : false,
    playhead,
    selectedCameraIndex: selectedCameraPathIndex(card, path),
    trimEndPosition: trimEndPosition(values),
    trimStart: values.trimStart,
    volume: video ? video.volume : defaultPreviewVolume,
    waveformPayload: parsePreviewWaveform(card.dataset.previewWaveformPeaks)
  };
  const live = window.CuttedLiveTimeline || {};
  const options = typeof live.createLiveTimelineOptionsFromCuttedModel === "function"
    ? live.createLiveTimelineOptionsFromCuttedModel(model)
    : fallbackLiveTimelineOptions(model);
  return Object.assign(options, {
    callbacks: liveTimelineCallbacksForCard(card),
    logoUrl: "assets/brand/cuted-logo-transparent.png",
    playing: video ? !video.paused && !video.ended : false,
    showInspector: false,
    showVolume: false,
    trimEnabled: card.dataset.trimMode === "1"
  });
}
function fallbackLiveTimelineOptions(model){
  const camera = (model.cameraPath || []).map((frame, index) => ({
    id: `camera-${index}`,
    layer: "camera",
    time: clampNumber(Number(frame.time || 0), 0, Math.max(model.duration, .3)),
    label: frame.label || frame.key || frame.source || `Camera ${index + 1}`,
    editable: true,
    intensity: clampNumber(Number(frame.confidence ?? 0.68), .18, 1)
  }));
  return {
    duration: model.duration,
    keyframes: camera,
    muted: model.muted,
    peaks: model.waveformPayload,
    playhead: model.playhead,
    selectedKeyframeId: camera[model.selectedCameraIndex]?.id || null,
    trimEnd: model.trimEndPosition,
    trimStart: model.trimStart,
    volume: model.volume
  };
}
function liveTimelineEffectKeyframesForCard(card){
  const current = cardState(card.dataset.rank);
  const effectFrames = Array.isArray(current.effect_keyframes) ? current.effect_keyframes : [];
  return effectFrames;
}
function liveTimelineCallbacksForCard(card){
  return {
    onSeek: time => {
      setPreviewPlayback(card, false);
      seekTimeline(card, time, { userInitiated: true, mode: "free" });
    },
    onTrimChange: trim => applyLiveTimelineTrim(card, trim),
    onKeyframeOpen: keyframe => openLiveTimelineKeyframe(card, keyframe),
    onPlayToggle: playing => setPreviewPlayback(card, playing)
  };
}
function applyLiveTimelineTrim(card, trim){
  setPreviewPlayback(card, false);
  const duration = Number(card.dataset.duration) || 0;
  const start = clampNumber(Number(trim.start || 0), 0, Math.max(duration - 1, 0));
  const end = clampNumber(Number(trim.end || duration), start + 1, Math.max(duration, start + 1));
  setCardState(card.dataset.rank, { trimStart: start, trimEnd: Math.max(duration - end, 0) });
  updateTrimUi(card);
  seekTimeline(card, trim.side === "end" ? end : start, { userInitiated: true, mode: "trim" });
  renderCaptionQueue();
}
function openLiveTimelineKeyframe(card, keyframe){
  if (!keyframe || keyframe.layer !== "camera") return;
  setPreviewPlayback(card, false);
  const match = String(keyframe.id || "").match(/camera-(\\d+)/);
  if (match) setSelectedCameraPathIndex(card, Number(match[1]));
  ensureLivePreviewCameraPopover(card);
  updateCameraUi(card);
  openPreviewCameraPopover(card, "edit");
}
function ensureLivePreviewCameraPopover(card){
  const rank = String(card?.dataset?.rank || "");
  if (!rank) return null;
  let popover = livePreviewCameraPopoverForRank(rank);
  if (!popover) {
    popover = document.createElement("div");
    popover.className = "preview-camera-popover preview-camera-popover--live preview-camera-popover--portal";
    popover.dataset.previewCameraPopover = "";
    popover.dataset.previewCameraPopoverRank = rank;
    popover.hidden = true;
    document.body.appendChild(popover);
    bindPreviewCameraPopover(card, popover);
  }
  bindPreviewCameraTimeline(card);
  return popover;
}
function livePreviewCameraPopoverForRank(rank){
  return Array.from(document.querySelectorAll(".preview-camera-popover--portal"))
    .find(popover => String(popover.dataset.previewCameraPopoverRank || "") === String(rank)) || null;
}
function previewCameraPopoverForCard(card){
  return livePreviewCameraPopoverForRank(card?.dataset?.rank) || card.querySelector("[data-preview-camera-popover]");
}
function loadLiveTimelineWaveform(card){
  if (parsePreviewWaveform(card.dataset.previewWaveformPeaks).length) return;
  const src = previewWaveformSource(card);
  if (!src || card.dataset.previewWaveformLoading === src) return;
  card.dataset.previewWaveformLoading = src;
  fetch(cacheBustedPreview(src, `waveform-${card.dataset.rank || ""}`))
    .then(response => response.ok ? response.json() : null)
    .then(payload => {
      const peaks = parsePreviewWaveform(payload?.peaks);
      delete card.dataset.previewWaveformLoading;
      if (!peaks.length) return;
      card.dataset.previewWaveformPeaks = JSON.stringify(peaks);
      renderPreviewCameraTimeline(card);
    })
    .catch(error => {
      console.debug("Nao consegui carregar waveform da timeline viva.", error);
      delete card.dataset.previewWaveformLoading;
    });
}
function renderLegacyPreviewCameraTimeline(card){
  const container = card.querySelector("[data-preview-camera-timeline]");
  if (!container) return;
  container.classList.remove("preview-camera-timeline--live");
  const state = previewCameraTimelineContext(card);
  const selectedIndex = selectedCameraPathIndex(card, state.path);
  const markers = state.path.map((frame, index) => {
    const left = clampNumber((Number(frame.time || 0) / state.duration) * 100, 0, 100);
    const active = index === selectedIndex ? " active" : "";
    const label = directorMarkerLabel(state.edit.director_plan, frame);
    const title = directorMarkerTitle(state.edit.director_plan, frame);
    return `<button class="preview-camera-marker${active}" data-preview-camera-marker="${index}" type="button" style="left:${left.toFixed(2)}%" title="${escapeAttr(title)}" aria-label="${escapeAttr(`Editar camera ${label} em ${fixed(frame.time)}`)}"><span>${escapeHtml(label)}</span></button>`;
  }).join("");
  container.innerHTML = `<div class="preview-camera-rail" data-preview-camera-rail>
    <div class="preview-audio-waveform" data-preview-audio-waveform hidden></div>
    <div class="preview-camera-track"></div>
    ${markers}
    <span class="preview-camera-playhead" data-preview-camera-playhead style="left:0%"></span>
  </div>
  <div class="preview-camera-popover" data-preview-camera-popover hidden></div>`;
  bindPreviewCameraTimeline(card);
  renderPreviewAudioWaveform(card);
  updatePreviewCameraTimelinePlayhead(card);
  renderOverlayTimeline(card);
}
function renderPreviewAudioWaveform(card){
  const layer = card.querySelector("[data-preview-audio-waveform]");
  if (!layer) return;
  const cached = parsePreviewWaveform(card.dataset.previewWaveformPeaks);
  if (cached.length) {
    layer.innerHTML = previewWaveformBarsHtml(cached);
    layer.hidden = false;
    return;
  }
  loadPreviewAudioWaveform(card, layer);
}
function loadPreviewAudioWaveform(card, layer){
  const src = previewWaveformSource(card);
  if (!src) {
    layer.hidden = true;
    return;
  }
  if (card.dataset.previewWaveformLoading === src) return;
  card.dataset.previewWaveformLoading = src;
  fetch(cacheBustedPreview(src, `waveform-${card.dataset.rank || ""}`))
    .then(response => response.ok ? response.json() : null)
    .then(payload => applyPreviewWaveformPayload(card, payload))
    .catch(error => {
      console.debug("Nao consegui carregar waveform do preview.", error);
      layer.hidden = true;
    });
}
function applyPreviewWaveformPayload(card, payload){
  const peaks = parsePreviewWaveform(payload?.peaks);
  const layer = card.querySelector("[data-preview-audio-waveform]");
  delete card.dataset.previewWaveformLoading;
  if (!layer || !peaks.length) {
    if (layer) layer.hidden = true;
    return;
  }
  card.dataset.previewWaveformPeaks = JSON.stringify(peaks);
  layer.innerHTML = previewWaveformBarsHtml(peaks);
  layer.hidden = false;
}
function previewWaveformSource(card){
  const moment = (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === String(card.dataset.rank));
  return moment?.waveform_file || "";
}
function parsePreviewWaveform(value){
  const raw = typeof value === "string" ? safeJsonParse(value) : value;
  if (!Array.isArray(raw)) return [];
  return raw.map(item => clampNumber(Number(item) || 0, 0, 1)).filter(item => item > 0).slice(0, 180);
}
function safeJsonParse(value){
  try { return JSON.parse(value); }
  catch (error) {
    console.debug("Waveform cache invalido.", error);
    return null;
  }
}
function previewWaveformBarsHtml(peaks){
  return peaks.map(item => `<span style="height:${Math.max(8, Math.round(item * 100))}%"></span>`).join("");
}
function updatePreviewCameraTimelinePlayhead(card, time = null){
  const playhead = card.querySelector("[data-preview-camera-playhead]");
  if (!playhead) return;
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card, time);
  const left = clampNumber((position / Math.max(duration, .3)) * 100, 0, 100);
  playhead.style.left = `${left.toFixed(2)}%`;
}
function bindPreviewCameraTimeline(card){
  const container = card.querySelector("[data-preview-camera-timeline]");
  if (!container || container.dataset.previewCameraTimelineBound) return;
  container.dataset.previewCameraTimelineBound = "1";
  container.addEventListener("click", event => {
    const popoverTarget = event.target.closest("[data-preview-camera-popover]");
    if (popoverTarget) return;
    const marker = event.target.closest("[data-preview-camera-marker]");
    if (marker) {
      event.preventDefault();
      event.stopPropagation();
      setSelectedCameraPathIndex(card, marker.dataset.previewCameraMarker);
      renderPreviewCameraTimeline(card);
      openPreviewCameraPopover(card);
      return;
    }
    const rail = event.target.closest("[data-preview-camera-rail]");
    if (!rail) return;
    event.preventDefault();
    event.stopPropagation();
    const position = seekPreviewCameraTimeline(card, event, rail);
    openPreviewCameraPopover(card, "insert", position);
  });
  container.addEventListener("change", event => {
    handlePreviewCameraPopoverChange(card, event);
  });
  container.addEventListener("input", event => {
    handlePreviewCameraPopoverInput(card, event);
  });
  container.addEventListener("click", event => {
    handlePreviewCameraPopoverClick(card, event);
  });
}
function bindPreviewCameraPopover(card, popover){
  if (!popover || popover.dataset.previewCameraPopoverBound) return;
  const rank = String(card?.dataset?.rank || "");
  const currentCard = () => cardForRank(rank) || card;
  popover.dataset.previewCameraPopoverBound = "1";
  popover.addEventListener("change", event => handlePreviewCameraPopoverChange(currentCard(), event));
  popover.addEventListener("input", event => handlePreviewCameraPopoverInput(currentCard(), event));
  popover.addEventListener("click", event => handlePreviewCameraPopoverClick(currentCard(), event));
  popover.addEventListener("contextmenu", event => {
    event.stopPropagation();
  });
}
function handlePreviewCameraPopoverChange(card, event){
  if (event.target.matches("[data-preview-camera-popover-intent]")) {
    event.preventDefault();
    const mode = event.target.closest("[data-preview-camera-popover]")?.dataset.previewCameraPopoverMode || "edit";
    if (mode === "edit") {
      const index = selectedCameraPathIndex(card, previewCameraTimelineContext(card).path);
      updateCameraPathFrameIntentForCard(card, event.target.value);
      setSelectedCameraPathIndex(card, index);
      renderPreviewCameraTimeline(card);
      openPreviewCameraPopover(card, "edit");
    }
    return;
  }
  if (event.target.matches("[data-preview-camera-popover-key]")) {
    event.preventDefault();
    const index = selectedCameraPathIndex(card, previewCameraTimelineContext(card).path);
    updateCameraPathFrameForCard(card, { key: event.target.value });
    setSelectedCameraPathIndex(card, index);
    renderPreviewCameraTimeline(card);
    openPreviewCameraPopover(card);
  }
}
function handlePreviewCameraPopoverInput(card, event){
  if (!event.target.matches("[data-preview-camera-popover-strength]")) return;
  const index = selectedCameraPathIndex(card, previewCameraTimelineContext(card).path);
  updateCameraPathFrameForCard(card, { strength: Number(event.target.value) }, false);
  setSelectedCameraPathIndex(card, index);
  renderPreviewCameraTimeline(card);
  openPreviewCameraPopover(card);
}
function handlePreviewCameraPopoverClick(card, event){
  const close = event.target.closest("[data-preview-camera-popover-close]");
  if (close) {
    event.preventDefault();
    event.stopPropagation();
    closePreviewCameraPopover(card);
    return;
  }
  const add = event.target.closest("[data-preview-camera-popover-add]");
  if (add) {
    event.preventDefault();
    event.stopPropagation();
    const popover = event.target.closest("[data-preview-camera-popover]");
    const intent = popover?.querySelector("[data-preview-camera-popover-intent]")?.value || "speaker_hold";
    addCameraIntentFrameForCard(card, intent);
    renderPreviewCameraTimeline(card);
    openPreviewCameraPopover(card, "edit");
    return;
  }
  const done = event.target.closest("[data-preview-camera-popover-continue]");
  if (done) {
    event.preventDefault();
    event.stopPropagation();
    closePreviewCameraPopover(card);
    return;
  }
  const remove = event.target.closest("[data-preview-camera-popover-delete]");
  if (!remove) return;
  event.preventDefault();
  event.stopPropagation();
  deleteCameraPathFrameForCard(card);
  closePreviewCameraPopover(card);
}
function seekPreviewCameraTimeline(card, event, rail){
  const rect = rail.getBoundingClientRect();
  const ratio = rect.width ? clampNumber((event.clientX - rect.left) / rect.width, 0, 1) : 0;
  const values = trimValues(card);
  const duration = Math.max(values.duration, .3);
  const position = ratio * duration;
  seekTimeline(card, position, { userInitiated: true, mode: "free" });
  return position;
}
function openPreviewCameraPopover(card, mode = "edit", positionOverride = null){
  const popover = previewCameraPopoverForCard(card) || ensureLivePreviewCameraPopover(card);
  if (!popover) return;
  closePreviewVolumePopover(card);
  const state = previewCameraTimelineContext(card);
  const index = selectedCameraPathIndex(card, state.path);
  const frame = state.path[index] || state.path[0] || normalizeCameraPathFrame({ time: 0, key: "center", strength: 60 });
  const position = mode === "insert" ? Number(positionOverride ?? cameraTimelinePositionForCard(card)) : Number(frame.time || 0);
  const left = clampNumber((position / state.duration) * 100, 6, 94);
  const intent = mode === "insert" ? "speaker_hold" : directorIntentFromFrame(frame);
  positionPreviewCameraPopover(card, popover, left);
  popover.dataset.previewCameraPopoverMode = mode;
  popover.innerHTML = mode === "insert" ? previewCameraInsertPopoverHtml(position, intent) : previewCameraEditPopoverHtml(state, frame, intent);
  popover.hidden = false;
}
function positionPreviewCameraPopover(card, popover, leftPercent){
  if (!popover.classList.contains("preview-camera-popover--portal")) {
    popover.style.left = `${leftPercent.toFixed(2)}%`;
    return;
  }
  const container = card.querySelector("[data-preview-camera-timeline]");
  const rect = container?.getBoundingClientRect();
  if (!rect) return;
  const width = Math.min(236, Math.max(window.innerWidth - 16, 0));
  const rawLeft = rect.left + rect.width * (leftPercent / 100) - width / 2;
  const left = clampNumber(rawLeft, 8, Math.max(window.innerWidth - width - 8, 8));
  const below = rect.bottom + 8;
  const height = 236;
  const top = below + height < window.innerHeight - 8 ? below : clampNumber(rect.top - height - 8, 8, Math.max(window.innerHeight - height - 8, 8));
  popover.style.left = `${left.toFixed(1)}px`;
  popover.style.top = `${top.toFixed(1)}px`;
  popover.style.right = "auto";
  popover.style.bottom = "auto";
}
function previewCameraPopoverDecorHtml(strength){
  const amount = clampNumber(Number(strength ?? 60), 0, 100);
  return `<div class="preview-camera-popover-aura" aria-hidden="true"></div>
  <div class="preview-camera-popover-lens" aria-hidden="true"></div>
  <div class="preview-camera-popover-beam" aria-hidden="true"></div>
  <div class="preview-camera-popover-meter" aria-hidden="true"><i style="width:${amount}%"></i></div>`;
}
function previewCameraInsertPopoverHtml(position, intent){
  return `${previewCameraPopoverDecorHtml(62)}
  <div class="preview-camera-popover-head">
    <strong>Novo shot</strong>
    <span>${escapeHtml(fixed(position))}</span>
    <button class="preview-camera-popover-close" data-preview-camera-popover-close type="button" aria-label="Fechar">x</button>
  </div>
  <label>Intencao
    <select data-preview-camera-popover-intent>${directorIntentOptionsHtml(intent)}</select>
  </label>
  <button class="preview-camera-popover-primary" data-preview-camera-popover-add type="button">Continuar</button>`;
}
function previewCameraEditPopoverHtml(state, frame, intent){
  const title = directorMarkerTitle(state.edit.director_plan, frame);
  const key = frame.key || "center";
  const strength = clampNumber(Number(frame.strength ?? 60), 0, 100);
  return `${previewCameraPopoverDecorHtml(strength)}
  <div class="preview-camera-popover-head">
    <strong>${escapeHtml(directorMarkerLabel(state.edit.director_plan, frame))}</strong>
    <span>${escapeHtml(fixed(frame.time))}</span>
    <button class="preview-camera-popover-close" data-preview-camera-popover-close type="button" aria-label="Fechar">x</button>
  </div>
  <small>${escapeHtml(title)}</small>
  <label>Intencao
    <select data-preview-camera-popover-intent>${directorIntentOptionsHtml(intent)}</select>
  </label>
  <label>Camera
    <select data-preview-camera-popover-key>${cameraOptionsHtml(key)}</select>
  </label>
  <label>Forca
    <input data-preview-camera-popover-strength type="range" min="0" max="100" step="5" value="${strength}">
  </label>
  <div class="preview-camera-popover-actions">
    <button class="preview-camera-popover-primary" data-preview-camera-popover-continue type="button">Continuar</button>
    <button class="preview-camera-popover-danger" data-preview-camera-popover-delete type="button"${state.path.length > 1 ? "" : " disabled"}>Excluir</button>
  </div>`;
}
function closePreviewCameraPopover(card){
  const popover = previewCameraPopoverForCard(card);
  if (popover) popover.hidden = true;
}
function applyTimelineSeek(card, video, current){
  if (!video) return false;
  try {
    video.currentTime = current;
    updateTimelinePlayhead(card, current);
    return Math.abs(Number(video.currentTime || 0) - current) < .6;
  } catch (error) {
    return false;
  }
}
function applyPendingTimelineSeek(card, video){
  const pending = card.dataset.pendingSeek;
  if (pending === undefined) return false;
  const duration = Number(card.dataset.duration) || .1;
  const current = clampNumber(Number(pending), 0, Math.max(duration, .1));
  const applied = applyTimelineSeek(card, video, current);
  if (applied) delete card.dataset.pendingSeek;
  return applied;
}
function seekTimeline(card, time, options = {}){
  const video = primaryCameraVideo(card);
  const values = trimValues(card);
  const current = clampPreviewTime(values, Number(time));
  const mode = trimRangeActive(values) && options.mode === "free" ? "trim" : options.mode;
  if (options.userInitiated && !trimRangeActive(values)) card.dataset.timelineSeekIntent = "1";
  if (mode) card.dataset.playbackMode = mode;
  card.dataset.pendingSeek = current.toFixed(3);
  if (video) {
    loadCardVideo(card);
    if (video.readyState > 0) {
      applyPendingTimelineSeek(card, video);
    }
    window.setTimeout(() => applyPendingTimelineSeek(card, video), 120);
    window.setTimeout(() => applyPendingTimelineSeek(card, video), 400);
  }
  updateTimelinePlayhead(card, current);
}
function seekPreview(card){
  const video = primaryCameraVideo(card);
  if (!video) return;
  loadCardVideo(card);
  const values = trimValues(card);
  delete card.dataset.timelineSeekIntent;
  seekTimeline(card, values.trimStart, { mode: "range" });
}
function seekTrimHandle(card, handle){
  const video = primaryCameraVideo(card);
  if (video) video.pause();
  const values = trimValues(card);
  const target = handle === "end" ? values.endPos : values.startPos;
  delete card.dataset.timelineSeekIntent;
  seekTimeline(card, target, { mode: "trim" });
}
function trimEndPosition(values){
  return values.duration - values.trimEnd;
}
function trimRangeActive(values){
  return values.trimStart > .05 || values.trimEnd > .05;
}
function clampPreviewTime(values, time){
  const safeTime = clampNumber(Number(time), 0, Math.max(values.duration, .1));
  if (!trimRangeActive(values)) return safeTime;
  const endPos = trimEndPosition(values);
  return clampNumber(safeTime, values.trimStart, Math.max(values.trimStart, endPos));
}
function trimPlaybackStart(values, currentTime){
  const endPos = trimEndPosition(values);
  if (currentTime < values.trimStart || currentTime >= endPos - .05) return values.trimStart;
  return currentTime;
}
function pauseAtTrimEnd(card, video, values){
  const endPos = trimEndPosition(values);
  if (video.currentTime < endPos) return false;
  video.pause();
  video.currentTime = endPos;
  updateTimelinePlayhead(card, endPos);
  return true;
}
function setPreviewPlayback(card, shouldPlay){
  const video = primaryCameraVideo(card);
  if (!video) return;
  loadCardVideo(card);
  applyPreviewVolume(video);
  if (shouldPlay) {
    if (!video.paused && !video.ended) {
      syncPreviewPlaybackState(card);
      return;
    }
    const playback = video.play();
    if (playback && typeof playback.catch === "function") playback.catch(() => syncPreviewPlaybackState(card));
    return;
  }
  if (!video.paused) video.pause();
  else syncPreviewPlayButton(card);
}
function togglePreviewPlayback(card){
  const video = primaryCameraVideo(card);
  if (!video) return;
  setPreviewPlayback(card, video.paused || video.ended);
}
function syncPreviewPlaybackState(card){
  syncPreviewPlayButton(card);
  syncLiveTimelinePlaybackState(card);
}
function syncLiveTimelinePlaybackState(card){
  if (!card.__liveTimelineController || typeof card.__liveTimelineController.update !== "function") return;
  card.__liveTimelineController.update(liveTimelineOptionsForCard(card));
}
function applyPreviewVolume(video){
  if (!video) return;
  if (!video.dataset.volumeReady) {
    video.volume = defaultPreviewVolume;
    video.dataset.volumeReady = "1";
  }
}
function setPreviewVolume(card, value){
  const video = primaryCameraVideo(card);
  if (!video) return;
  video.dataset.volumeReady = "1";
  video.volume = clampNumber(value, 0, 1);
  video.muted = video.volume <= 0;
  syncPreviewVolumeButton(card);
}
function syncPreviewPlayButton(card){
  const button = card.querySelector("[data-preview-play]");
  const video = primaryCameraVideo(card);
  if (!button) return;
  if (!video) {
    button.hidden = true;
    return;
  }
  button.hidden = false;
  button.innerHTML = previewIcon(video.paused ? "play" : "pause");
  button.setAttribute("aria-label", video.paused ? "Reproduzir" : "Pausar");
  button.title = video.paused ? "Reproduzir" : "Pausar";
}
function syncPreviewVolumeButton(card){
  const button = card.querySelector("[data-preview-volume]");
  const slider = card.querySelector("[data-preview-volume-slider]");
  const video = primaryCameraVideo(card);
  if (!button) return;
  if (!video) {
    button.hidden = true;
    return;
  }
  applyPreviewVolume(video);
  const value = video.muted ? 0 : Math.round(video.volume * 100);
  button.hidden = false;
  button.innerHTML = previewIcon(video.muted || video.volume <= 0 ? "volume-off" : "volume");
  button.setAttribute("aria-label", "Volume");
  button.title = "Volume";
  if (slider) slider.value = String(value);
  updateControlSurfaceForCard(card);
}
function openPreviewVolumePopover(card){
  const popover = card.querySelector("[data-preview-volume-popover]");
  if (!popover) return;
  closePreviewCameraPopover(card);
  syncPreviewVolumeButton(card);
  popover.hidden = false;
}
function closePreviewVolumePopover(card){
  const popover = card.querySelector("[data-preview-volume-popover]");
  if (popover) popover.hidden = true;
}
function togglePreviewVolumePopover(card){
  const popover = card.querySelector("[data-preview-volume-popover]");
  if (!popover) return;
  if (popover.hidden) openPreviewVolumePopover(card);
  else closePreviewVolumePopover(card);
}
function bindPreviewVolumeDismiss(){
  if (document.body.dataset.previewVolumeDismissBound) return;
  document.body.dataset.previewVolumeDismissBound = "1";
  document.addEventListener("click", event => {
    document.querySelectorAll("[data-preview-volume-popover]").forEach(popover => {
      const group = popover.closest(".preview-volume-group");
      if (!group || !group.contains(event.target)) popover.hidden = true;
    });
  });
}
function previewIcon(name){
  const icons = {
    play: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z" fill="currentColor" stroke="none"></path></svg>',
    pause: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h4v14H7zM13 5h4v14h-4z" fill="currentColor" stroke="none"></path></svg>',
    volume: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor" stroke="none"></path><path d="M16 9.5c1.2 1.4 1.2 3.6 0 5M18.5 7c2.4 2.8 2.4 7.2 0 10" fill="none" stroke-width="2" stroke-linecap="round"></path></svg>',
    "volume-off": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor" stroke="none"></path><path d="M16 9l5 5M21 9l-5 5" fill="none" stroke-width="2" stroke-linecap="round"></path></svg>'
  };
  return icons[name] || "";
}
function loadCardVideo(card){
  const video = card.querySelector("video:not(.camera-fit-bg)[data-src]");
  if (!video || video.getAttribute("src")) return;
  video.setAttribute("src", video.dataset.src);
  applyPreviewVolume(video);
  video.load();
  syncCameraFitBackground(card);
  syncPreviewPlayButton(card);
  syncPreviewVolumeButton(card);
}
function unloadCardVideo(card){
  destroyLivePreviewCameraTimeline(card);
  const video = card.querySelector("video:not(.camera-fit-bg)[data-src]");
  if (!video || !video.getAttribute("src")) return;
  video.pause();
  video.removeAttribute("src");
  video.load();
  unloadCameraFitBackground(card);
  syncPreviewPlayButton(card);
  syncPreviewVolumeButton(card);
}
function activateCard(card){
  document.querySelectorAll(".card[open]").forEach(item => {
    if (item === card) return;
    item.open = false;
    unloadCardVideo(item);
  });
  if (card.open) {
    loadCardVideo(card);
    updateCardTools(card);
  } else {
    unloadCardVideo(card);
  }
}
function openNextCard(card){
  const cards = Array.from(document.querySelectorAll(".card"));
  const index = cards.indexOf(card);
  const next = cards[index + 1];
  if (next) {
    next.open = true;
    next.scrollIntoView({ behavior: "smooth", block: "start" });
    activateCard(next);
    return;
  }
  applyTab("final");
}
function adjustedMoment(moment){
  const current = cardState(String(moment.rank));
  const trimStart = Number(current.trimStart || 0);
  const trimEnd = Number(current.trimEnd || 0);
  const platforms = Array.isArray(current.platforms) ? current.platforms : [];
  const adjustedDuration = Number((moment.end - trimEnd - moment.start - trimStart).toFixed(3));
  const edit = platformEditForRank(moment.rank);
  const captionLanguage = normalizeCaptionLanguage(edit.captionLanguage);
  const captionTracks = normalizeCaptionTracks(moment.caption_tracks, moment.caption_segments || []);
  const sourceDuration = sourceDurationForMoment(moment);
  return Object.assign({}, moment, {
    status: current.status || null,
    platforms,
    trim_start_seconds: trimStart,
    trim_end_seconds: trimEnd,
    adjusted_start: Number((moment.start + trimStart).toFixed(3)),
    adjusted_end: Number((moment.end - trimEnd).toFixed(3)),
    adjusted_duration: adjustedDuration,
    camera: edit.camera,
    camera_path: exportCameraPathForEdit(edit, sourceDuration, trimStart, adjustedDuration),
    director_plan: edit.director_plan,
    camera_motion_ms: current.cameraMotionMs,
    caption_language: captionLanguage,
    caption_tracks: captionTracks,
    caption_segments: captionSegmentsForMoment(Object.assign({}, moment, { caption_tracks: captionTracks }), captionLanguage),
    effect: effectForRank(moment.rank),
    overlay: primaryOverlayForRank(moment.rank),
    overlays: overlayLayersForRank(moment.rank),
    bumpers: bumpersForRank(moment.rank),
    platform_edits: current.platformEdits
  });
}
function resolutionEditForPlatform(rank, platform, sourceDuration, trimStart, duration){
  const key = resolutionPresetForPlatform(platform);
  const edit = platformEditForRank(rank, platform);
  return {
    resolution_preset: key,
    resolution_label: resolutionPresetLabel(key),
    source: "platform_edits",
    camera: edit.camera,
    camera_path: exportCameraPathForEdit(edit, sourceDuration, trimStart, duration),
    director_plan: edit.director_plan,
    camera_motion_ms: cardState(String(rank)).cameraMotionMs,
    caption_language: normalizeCaptionLanguage(edit.captionLanguage),
    effect: edit.effect,
    overlay: edit.overlays.find(layer => layer.kind !== "image") || defaultOverlay(),
    overlays: edit.overlays,
    bumpers: edit.bumpers
  };
}
function resolutionEditsForMoment(moment, exportFormat){
  const result = {};
  captionPlatforms(moment, exportFormat).forEach(platform => {
    const key = resolutionPresetForPlatform(platform);
    if (!result[key]) {
      result[key] = Object.assign(resolutionEditForPlatform(moment.rank, platform, sourceDurationForMoment(moment), moment.trim_start_seconds, moment.adjusted_duration), {
        destinations: resolutionPresets[key]?.destinations || [platform],
        shared: true
      });
    }
  });
  return result;
}
function buildExportData(){
  const data = Object.assign({}, window.CUTTED_DATA);
  data.export_format = document.body.dataset.format || "tiktok";
  data.resolution_presets = resolutionPresets;
  data.destination_resolution_map = destinationResolutionMap();
  const adjusted = data.moments.map(adjustedMoment).map(moment => Object.assign({}, moment, {
    resolution_edits: resolutionEditsForMoment(moment, data.export_format)
  }));
  data.moments = adjusted;
  data.selected = adjusted.filter(moment => captionPlatforms(moment, data.export_format).length > 0);
  data.caption_queue = data.selected.flatMap(moment => captionPlatforms(moment, data.export_format).map(platform => {
    const edit = platformEditForRank(moment.rank, platform);
    const overlays = edit.overlays;
    const cameraPath = exportCameraPathForEdit(edit, sourceDurationForMoment(moment), moment.trim_start_seconds, moment.adjusted_duration);
    const resolutionKey = resolutionPresetForPlatform(platform);
    const captions = normalizeCaptionSettings(edit.captions);
    const captionLanguage = normalizeCaptionLanguage(edit.captionLanguage);
    const captionTracks = normalizeCaptionTracks(moment.caption_tracks, moment.caption_segments || []);
    const captionSegments = captionSegmentsForMoment(Object.assign({}, moment, { caption_tracks: captionTracks }), captionLanguage);
    const captionMoment = Object.assign({}, moment, { caption_segments: captionSegments });
    return {
      rank: moment.rank,
      platform,
      platform_label: platformLabel(platform),
      resolution_preset: resolutionKey,
      resolution_label: resolutionPresetLabel(resolutionKey),
      shared_destinations: resolutionPresets[resolutionKey]?.destinations || [platform],
      resolution_edit: moment.resolution_edits[resolutionKey] || null,
      width: platformMeta[platform]?.width || null,
      height: platformMeta[platform]?.height || null,
      publish_metadata: publishMetadata(platform, moment),
      trim_start_seconds: moment.trim_start_seconds,
      trim_end_seconds: moment.trim_end_seconds,
      adjusted_start: moment.adjusted_start,
      adjusted_end: moment.adjusted_end,
      adjusted_duration: moment.adjusted_duration,
      camera: edit.camera,
      camera_path: cameraPath,
      director_plan: edit.director_plan,
      effect: edit.effect,
      overlay: overlays.find(layer => layer.kind !== "image") || defaultOverlay(),
      overlays,
      bumpers: edit.bumpers,
      captions_enabled: captions.enabled,
      caption_language: captionLanguage,
      caption_tracks: captionTracks,
      caption_style: captions.style,
      animated_caption_windows: captions.style.mode === "animated" ? previewAnimatedCaptionTimeline(captionMoment) : [],
      clip_file: moment.clip_file,
      title: moment.title,
      peak_text: moment.peak_text,
      transcript: moment.transcript,
      caption_segments: captionSegments
    };
  }));
  return data;
}
function captionPlatforms(moment, exportFormat){
  if (moment.status === "discarded") return [];
  const platforms = uniquePlatforms(moment.platforms);
  if (platforms.length) return platforms;
  return moment.status === "liked" && platformMeta[exportFormat] ? [exportFormat] : [];
}
function uniquePlatforms(values){
  const seen = new Set();
  return (Array.isArray(values) ? values : []).map(value => representativePlatform(String(value || "").trim().toLowerCase())).filter(platform => {
    const resolution = resolutionPresetForPlatform(platform);
    if (!platformMeta[platform] || seen.has(resolution)) return false;
    seen.add(resolution);
    return true;
  });
}
function publishMetadata(platform, moment){
  const edit = publishEditForRank(moment.rank);
  if (moment.publish_metadata && typeof moment.publish_metadata === "object") {
    const generated = moment.publish_metadata;
    const hashtags = edit.hashtags.length
      ? edit.hashtags
      : Array.isArray(generated.hashtags) && generated.hashtags.length
      ? generated.hashtags
      : suggestHashtags(platform, `${moment.title} ${moment.peak_text} ${moment.transcript}`);
    const result = Object.assign({}, generated, {
      title: edit.title || generated.title,
      hook: edit.hook || generated.hook,
      description: edit.description || generated.description,
      hashtags,
      cover: publishCoverFromEdit(edit, generated, moment),
      caption_hint: publishCaptionHintFromEdit(edit, generated, platform, moment, hashtags),
      strategy: generated.strategy || platformStrategy(platform)
    });
    return result;
  }
  const hashtags = edit.hashtags.length ? edit.hashtags : suggestHashtags(platform, `${moment.title} ${moment.peak_text} ${moment.transcript}`);
  return {
    title: edit.title || moment.title,
    hook: edit.hook || "",
    description: edit.description || "",
    hashtags,
    cover: publishCoverFromEdit(edit, null, moment),
    caption_hint: publishCaptionHintFromEdit(edit, null, platform, moment, hashtags),
    strategy: platformStrategy(platform)
  };
}
function normalizePublishEdit(value){
  const source = value && typeof value === "object" ? value : {};
  return {
    title: cleanPublishField(source.title, 110),
    hook: cleanPublishField(source.hook, 140),
    description: cleanPublishField(source.description, 360),
    coverFrame: cleanPublishField(source.coverFrame, 260),
    coverZoom: normalizePublishCoverZoom(source.coverZoom, null),
    coverX: normalizePublishCoverPosition(source.coverX, source.coverZoom || 1),
    coverY: normalizePublishCoverPosition(source.coverY, source.coverZoom || 1),
    coverLayers: normalizeCoverOverlayLayers(source.coverLayers),
    hashtags: normalizePublishHashtags(source.hashtags)
  };
}
function publishEditForRank(rank){
  return normalizePublishEdit(cardState(String(rank)).publish);
}
function cleanPublishField(value, limit){
  const cleaned = String(value || "").replace(/\\s+/g, " ").trim();
  return cleaned.length > limit ? `${cleaned.slice(0, Math.max(0, limit - 1)).trim()}…` : cleaned;
}
function normalizePublishHashtags(value){
  const raw = Array.isArray(value) ? value.join(" ") : String(value || "");
  const seen = new Set();
  return raw.split(/[\\s,]+/).map(item => item.trim()).filter(Boolean).map(item => {
    const clean = item.replace(/^#+/, "").replace(/[^\\p{L}\\p{N}_]/gu, "");
    return clean ? `#${clean}` : "";
  }).filter(tag => {
    const key = tag.toLowerCase();
    if (!tag || seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, 8);
}
function publishCoverFromEdit(edit, generated, moment){
  const cover = generated?.cover && typeof generated.cover === "object" ? generated.cover : {};
  const editedFrame = cleanPublishField(edit.coverFrame, 260);
  const baseCandidates = publishCoverCandidates(moment, cover);
  const fallback = cover.selected_frame || baseCandidates[0] || moment.frame_file || "";
  const selected = editedFrame || fallback;
  const candidates = uniqueCoverFrames([selected, ...baseCandidates]);
  const zoom = normalizePublishCoverZoom(edit.coverZoom, normalizePublishCoverZoom(cover.zoom, 1));
  return {
    selected_frame: selected,
    candidates,
    zoom,
    x: normalizePublishCoverPosition(edit.coverX ?? cover.x, zoom),
    y: normalizePublishCoverPosition(edit.coverY ?? cover.y, zoom),
    layers: normalizeCoverOverlayLayers(edit.coverLayers.length ? edit.coverLayers : cover.layers),
    reason: cover.reason || "Frame de pico extraido do corte."
  };
}
function normalizeCoverOverlayLayers(layers){
  const source = Array.isArray(layers) ? layers : [];
  return source.map(normalizeOverlayLayer).filter(layer => layer.key !== "none");
}
function liftedCoverLayerY(y){
  return clampNumber(Number(y || 0) - coverLayerVerticalLift, 0, 1);
}
function publishCoverLayerHtml(layer){
  const current = normalizeOverlayLayer(layer);
  const left = clampNumber(current.x * 100, 0, 100);
  const top = clampNumber(liftedCoverLayerY(current.y) * 100, 0, 100);
  const width = clampNumber(current.width * 100, 8, 90);
  const opacity = clampNumber(current.opacity / 100, .1, 1);
  const fontSize = clampNumber((current.font_size || 34) * .42, 10, 24);
  const selected = document.querySelector(`.card[data-rank="${CSS.escape(String(activeRankForCoverLayer(current)))}"]`)?.dataset.selectedCoverLayer === current.id;
  const selectedClass = selected ? " is-selected" : "";
  const resize = '<button class="publish-cover-resize" data-publish-cover-resize type="button" title="Redimensionar"></button>';
  if (current.kind === "image") {
    const src = current.image_data_url || current.image_file || "";
    if (!src) return "";
    return `<div class="publish-cover-layer${selectedClass}" data-publish-cover-layer="${escapeAttr(current.id)}" data-cover-layer-kind="image" style="left:${left}%;top:${top}%;width:${width}%;--cover-layer-opacity:${opacity}"><img src="${escapeAttr(src)}" alt="">${resize}</div>`;
  }
  const bg = hexToRgb(current.background_color || "#000000").join(",");
  const bgOpacity = clampNumber((current.background_opacity ?? 70) / 100, 0, 1);
  const color = normalizeHexColor(current.color, current.kind === "speech" ? "#050505" : "#ffffff");
  const text = escapeHtml(current.text || current.label || "");
  return `<div class="publish-cover-layer${selectedClass}" data-publish-cover-layer="${escapeAttr(current.id)}" data-cover-layer-kind="${escapeAttr(current.kind)}" style="left:${left}%;top:${top}%;width:${width}%;font-size:${fontSize}px;opacity:${opacity};--cover-layer-color:${color};--cover-layer-bg:${bg};--cover-layer-bg-opacity:${bgOpacity}"><span>${text}</span>${resize}</div>`;
}
function activeRankForCoverLayer(layer){
  const card = Array.from(document.querySelectorAll(".card")).find(item => coverLayersForRank(item.dataset.rank).some(current => current.id === layer.id));
  return card?.dataset.rank || "";
}
function normalizePublishCoverZoom(value, fallback = 1){
  if (value === null || value === undefined || value === "") return fallback;
  const next = Number(value);
  if (!Number.isFinite(next)) return fallback;
  return clampNumber(next, 1, 1.8);
}
function normalizePublishCoverPosition(value, zoom){
  if (normalizePublishCoverZoom(zoom, 1) <= 1.001) return 50;
  const next = Number(value);
  if (!Number.isFinite(next)) return 50;
  return clampNumber(next, 0, 100);
}
function publishCoverCandidates(moment, cover){
  const raw = Array.isArray(cover.candidates) && cover.candidates.length
    ? cover.candidates
    : (Array.isArray(moment.cover_candidates) ? moment.cover_candidates : []);
  return uniqueCoverFrames([...raw, cover.selected_frame, moment.frame_file]);
}
function uniqueCoverFrames(values){
  const seen = new Set();
  return values.map(value => String(value || "").trim()).filter(value => {
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  }).slice(0, 4);
}
function publishCaptionHintFromEdit(edit, generated, platform, moment, hashtags){
  const hook = edit.hook || generated?.hook || "";
  const description = edit.description || generated?.description || "";
  const parts = [hook, description, hashtags.join(" ")].filter(Boolean);
  return parts.length ? parts.join("\\n\\n") : (generated?.caption_hint || captionHint(platform, moment, hashtags));
}
function suggestHashtags(platform, text){
  const topicTags = extractTopicTags(text);
  const topicalBoosts = inferTopicalBoosts(text);
  const defaults = {
    tiktok: ["IA", "InteligenciaArtificial", "Podcast"],
    shorts: ["IA", "InteligenciaArtificial", "Shorts"],
    youtube: ["IA", "InteligenciaArtificial", "Tecnologia"],
    instagram: ["IA", "InteligenciaArtificial", "Reels"],
    facebook: ["IA", "Tecnologia"]
  };
  const limits = { tiktok: 6, shorts: 4, youtube: 4, instagram: 5, facebook: 3 };
  const merged = [...topicalBoosts, ...(defaults[platform] || []), ...topicTags];
  return unique(merged).slice(0, limits[platform] || 4).map(tag => `#${tag}`);
}
function extractTopicTags(text){
  const extraStopWords = [
    "acho","ainda","agora","assim","cada","cara","certo","com","daqui","dele","dela","deles","dessa",
    "desse","disso","dizer","esta","estao","falar","mas","meio","nao","nem","nessa","nesse",
    "cortou","negocio","pela","pelo","qual","quando","que","quem","sabe","seguinte","tambem",
    "tem","tipo","uma","volta","vou"
  ];
  const stop = new Set(["para","como","porque","entao","então","sobre","isso","essa","esse","aqui","gente","voce","você","video","clip","coisa","forma","mais","menos","muito","fala","falando"]);
  extraStopWords.forEach(word => stop.add(word));
  const normalized = String(text).normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
  const words = normalized.match(/[a-zA-Z0-9]{3,}/g) || [];
  const counts = new Map();
  words.map(word => word.toLowerCase()).filter(word => !stop.has(word)).forEach(word => {
    counts.set(word, (counts.get(word) || 0) + 1);
  });
  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1] || b[0].length - a[0].length)
    .slice(0, 4)
    .map(([word]) => word.charAt(0).toUpperCase() + word.slice(1));
}
function inferTopicalBoosts(text){
  const normalized = String(text).normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase();
  const boosts = [];
  if (/\\bia\\b|inteligencia artificial|artificial/.test(normalized)) boosts.push("IA", "InteligenciaArtificial");
  if (/podcast|episodio|entrevista|conversa/.test(normalized)) boosts.push("Podcast");
  if (/tecnologia|tech|futuro|ferramenta|automacao/.test(normalized)) boosts.push("Tecnologia");
  if (/criador|conteudo|youtube|tiktok|instagram|reels|shorts/.test(normalized)) boosts.push("Criadores");
  return boosts;
}
function unique(values){
  const seen = new Set();
  return values.filter(value => {
    const clean = String(value).replace(/^#/, "").replace(/[^a-zA-Z0-9]/g, "");
    const key = clean.toLowerCase();
    if (!clean || seen.has(key)) return false;
    seen.add(key);
    return true;
  }).map(value => String(value).replace(/^#/, "").replace(/[^a-zA-Z0-9]/g, ""));
}
function captionHint(platform, moment, hashtags){
  const lead = moment.peak_text || moment.title || "Corte selecionado";
  return `${lead}\\n\\n${hashtags.join(" ")}`;
}
function platformStrategy(platform){
  return {
    tiktok: "Usar poucos hashtags relevantes; validar tendencias no TikTok Creative Center antes de publicar.",
    shorts: "Priorizar 3-4 hashtags relevantes; no YouTube, os primeiros hashtags da descricao sao os mais visiveis.",
    youtube: "Usar hashtags como contexto, sem exagero; evitar excesso de hashtags.",
    instagram: "Usar 3-5 hashtags especificos e relevantes; evitar blocos longos genericos.",
    facebook: "Usar 1-3 hashtags pesquisaveis; legenda clara e nativa do feed importa mais que volume."
  }[platform] || "Usar hashtags relevantes e especificos.";
}
function downloadJson(data, filename){
  const blob = new Blob([JSON.stringify(data, null, 2)], {type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
}
function renderCaptionQueue(){
  renderFinalStage();
}
function renderCameraPreview(){
  const preview = document.querySelector("[data-camera-preview]");
  const summary = document.querySelector("[data-camera-summary]");
  if (!preview) return;
  const queue = buildExportData().caption_queue || [];
  if (!queue.length) {
    if (summary) summary.textContent = "Marque cortes como Gostei ou escolha destinos para liberar a camera.";
    preview.innerHTML = '<div class="camera-empty">Nenhum corte selecionado ainda.</div>';
    return;
  }
  if (summary) summary.textContent = `${queue.length} saidas selecionadas. Escolha um enquadramento em cada uma.`;
  preview.innerHTML = queue.map(cameraPreviewItemHtml).join("");
  bindCameraPreviewControls();
}
function cameraPreviewItemHtml(item){
  const camera = normalizeCamera(item.camera);
  const cameraPath = cameraPathForEdit({ camera, camera_path: item.camera_path }, Number(item.adjusted_duration || 0));
  const previewFrame = cameraFrameForTime(camera, cameraPath, 0, Number(item.adjusted_duration || 0));
  const src = cacheBustedPreview(item.clip_file || "", `camera-${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  const duration = Number(item.adjusted_duration || 0);
  return `<article class="caption-item" data-rank="${escapeAttr(item.rank)}" data-platform="${escapeAttr(item.platform)}" data-camera-duration="${escapeAttr(item.adjusted_duration || 0)}">
    <div class="caption-preview camera-surface" data-camera-key="${escapeAttr(previewFrame.key || "path")}" data-camera-cut="${cameraFrameUsesHardCut(previewFrame) ? "hard" : "smooth"}" data-camera-fit="${cameraFrameUsesGroupFit(previewFrame) ? "contain" : "cover"}" style="${escapeAttr(cameraPreviewStyleFromFrame(previewFrame))}">
      <video controls preload="metadata" src="${escapeAttr(src)}"></video>
      <video class="camera-fit-bg" data-camera-fit-bg playsinline muted preload="metadata" src="${escapeAttr(src)}" aria-hidden="true" tabindex="-1"></video>
      <img class="camera-fit-logo" src="assets/brand/cuted-logo-transparent.png" alt="" aria-hidden="true">
      <div class="camera-reticle"></div>
    </div>
    <div class="caption-item-body">
      <strong>Preview #${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
      <span>${escapeHtml(item.platform_label)}</span><span data-camera-current>${escapeHtml(cameraEditLabel({ camera, camera_path: item.camera_path }, duration))}</span>
      <div class="camera-card-controls">
        ${cameraSegmentsHtml(camera)}
      </div>
    </div>
  </article>`;
}
function cameraPathEditorHtml(card, edit, duration, camera){
  const explicit = explicitCameraPathForEdit(edit);
  const path = cameraPathForEdit(edit, duration);
  const selectedIndex = selectedCameraPathIndex(card, path);
  const selected = path[selectedIndex] || path[0] || normalizeCameraPathFrame({ time: 0, key: "center", strength: 60 });
  const safeDuration = Math.max(Number(duration) || 0, .3);
  const platform = activePlatformForRank(card.dataset.rank);
  const resolutionKey = resolutionPresetForPlatform(platform);
  const resolution = resolutionPresets[resolutionKey] || resolutionPresets.vertical_9_16;
  const shared = resolution.destinations.map(platformLabel).join(", ");
  const markers = path.map((frame, index) => {
    const left = clampNumber((Number(frame.time || 0) / safeDuration) * 100, 0, 100);
    const active = index === selectedIndex ? " active" : "";
    const label = directorMarkerLabel(edit.director_plan, frame);
    const title = directorMarkerTitle(edit.director_plan, frame);
    return `<button class="camera-path-marker${active}" data-camera-path-marker="${index}" type="button" style="left:${left.toFixed(2)}%" title="${escapeAttr(title)}"><span>${escapeHtml(label)}</span></button>`;
  }).join("");
  return `<div class="camera-path-editor" data-camera-path-editor>
    <div class="camera-smart-panel">
      <div class="camera-panel-title">
        <strong>AI Director</strong>
        <span>${escapeHtml(resolution.label)} ${resolution.width}x${resolution.height}</span>
      </div>
      <p>Direcione este formato uma vez e reuse em ${escapeHtml(shared)}. Ajuste pontos na timeline quando quiser corrigir a intencao.</p>
      ${smartCameraButtonsHtml()}
    </div>
    <div class="camera-auto-status" data-camera-auto-status></div>
    <details class="camera-advanced">
      <summary>
        <span>Ajustes avancados</span>
        <small>${explicit.length ? `${path.length} keyframes ativos` : "manual e keyframes"}</small>
      </summary>
      <div class="camera-path-head">
        <strong>Camera path</strong>
        <span>${explicit.length ? `${path.length} keyframes manuais` : "Derivado de Inicio/Meio/Fim"}</span>
      </div>
      <div class="camera-path-track" aria-label="Keyframes de camera">
        <div class="camera-path-rail"></div>
        ${markers}
      </div>
      <div class="camera-path-actions">
        <button data-camera-path-add type="button">+ no playhead</button>
        <button data-camera-path-set-time type="button"${explicit.length ? "" : " disabled"}>Mover para playhead</button>
        <button data-camera-path-reset type="button"${explicit.length ? "" : " disabled"}>Usar simples</button>
      </div>
      <div class="camera-keyframe-panel">
        <label>Keyframe
          <select data-camera-path-key${explicit.length ? "" : " disabled"}>${cameraOptionsHtml(selected?.key || "center")}</select>
        </label>
        <label>Forca
          <input data-camera-path-strength type="range" min="0" max="100" step="5" value="${selected?.strength ?? 60}"${explicit.length ? "" : " disabled"}>
        </label>
        <button class="camera-path-delete" data-camera-path-delete type="button"${path.length > 1 && explicit.length ? "" : " disabled"}>Excluir ponto</button>
      </div>
      ${cameraSegmentsHtml(camera)}
    </details>
  </div>`;
}
function smartCameraButtonsHtml(){
  const quick = ["follow-face", "stable-face", "face-zoom"];
  const ai = ["ai-director-group", "ai-director-speaker", "ai-director-reactions", "ai-director-cuts"];
  const director = cameraSmartButtonHtml("ai-director", smartCameraModes["ai-director"], true);
  const auto = cameraSmartButtonHtml("auto-director", smartCameraModes["auto-director"], false);
  const quickHtml = quick.map(key => cameraSmartButtonHtml(key, smartCameraModes[key], false)).join("");
  const aiHtml = ai.map(key => cameraSmartButtonHtml(key, smartCameraModes[key], false)).join("");
  return `${director}<div class="camera-smart-row">${auto}${quickHtml}</div><div class="camera-smart-ai">${aiHtml}</div>`;
}
function cameraSmartButtonHtml(key, meta, featured){
  const className = featured ? ' class="camera-director-action"' : "";
  return `<button${className} data-camera-smart-mode="${escapeAttr(key)}" type="button" title="${escapeAttr(meta.note)}"><strong>${escapeHtml(meta.label)}</strong><span>${escapeHtml(meta.note)}</span></button>`;
}
function cameraSegmentsHtml(camera){
  return `<div class="camera-manual-panel">
    <div class="camera-panel-title">
      <strong>Manual</strong>
      <span>Inicio / Meio / Fim</span>
    </div>
    <div class="camera-segments">${cameraParts.map(part => {
    const segment = camera.segments.find(item => item.part === part.key) || defaultCameraSegment(part.key);
    return `<div class="camera-segment" data-camera-part="${escapeAttr(part.key)}">
      <strong>${escapeHtml(part.label)}</strong>
      <select data-preview-camera-segment="${escapeAttr(part.key)}">${cameraOptionsHtml(segment.key)}</select>
      <label>Forca
        <input data-preview-camera-strength="${escapeAttr(part.key)}" type="range" min="0" max="100" step="5" value="${segment.strength}">
      </label>
    </div>`;
  }).join("")}</div>
  </div>`;
}
function cameraOptionsHtml(selectedKey){
  return Object.entries(cameraMeta).map(([key, meta]) => {
    const selected = selectedKey === key ? " selected" : "";
    return `<option value="${escapeAttr(key)}"${selected}>${escapeHtml(meta.label)}</option>`;
  }).join("");
}
function bindCameraPreviewControls(){
  document.querySelectorAll("[data-camera-preview] .caption-item").forEach(item => {
    const rank = item.dataset.rank;
    const updatePreviewSurface = () => {
      const video = primaryCameraVideo(item);
      const edit = platformEditForRank(rank, item.dataset.platform);
      const duration = Number(item.dataset.cameraDuration || video?.duration || 0);
      applyCameraSurface(item.querySelector(".camera-surface"), edit.camera, Number(video?.currentTime || 0), duration, cameraPathForEdit(edit, duration));
      const summary = item.querySelector("[data-camera-current]");
      if (summary) summary.textContent = cameraEditLabel(edit, duration);
    };
    updatePreviewSurface();
    const video = primaryCameraVideo(item);
    if (video) {
      ["loadedmetadata", "durationchange", "seeked", "timeupdate"].forEach(eventName => {
        video.addEventListener(eventName, updatePreviewSurface);
      });
      video.addEventListener("play", () => startCameraFrameSync(video, updatePreviewSurface));
      ["pause", "ended"].forEach(eventName => {
        video.addEventListener(eventName, () => stopCameraFrameSync(video, updatePreviewSurface));
      });
    }
    item.querySelectorAll("[data-preview-camera-segment]").forEach(select => {
      select.addEventListener("change", () => {
        setCameraSegmentForRank(rank, select.dataset.previewCameraSegment, { key: select.value }, item.dataset.platform);
        updatePreviewSurface();
      });
    });
    item.querySelectorAll("[data-preview-camera-strength]").forEach(strength => {
      const update = () => {
        setCameraSegmentForRank(rank, strength.dataset.previewCameraStrength, { strength: Number(strength.value) }, item.dataset.platform);
        updatePreviewSurface();
      };
      strength.addEventListener("input", update);
      strength.addEventListener("change", update);
    });
  });
}
function renderEffectPreview(){
  const preview = document.querySelector("[data-effect-preview]");
  const summary = document.querySelector("[data-effect-summary]");
  if (!preview) return;
  const queue = buildExportData().caption_queue || [];
  if (!queue.length) {
    if (summary) summary.textContent = "Marque cortes como Gostei ou escolha destinos para liberar os efeitos.";
    preview.innerHTML = '<div class="effect-empty">Nenhum corte selecionado ainda.</div>';
    return;
  }
  if (summary) summary.textContent = `${queue.length} saidas selecionadas. Escolha um efeito em cada uma.`;
  preview.innerHTML = queue.map(effectPreviewItemHtml).join("");
  bindEffectPreviewControls();
}
function effectPreviewItemHtml(item){
  const effect = normalizeEffect(item.effect);
  const src = cacheBustedPreview(item.clip_file || "", `effect-${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  return `<article class="caption-item" data-rank="${escapeAttr(item.rank)}" data-platform="${escapeAttr(item.platform)}" data-effect="${escapeAttr(effect.key)}" style="--effect-opacity:${effectOpacity(effect)}">
    <div class="caption-preview"><video controls preload="metadata" src="${escapeAttr(src)}"></video></div>
    <div class="caption-item-body">
      <strong>Preview #${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
      <span>${escapeHtml(item.platform_label)}</span><span data-effect-current>${escapeHtml(effectLabel(effect))}</span>
      <div class="effect-card-controls">
        <div class="effect-card-buttons" role="group" aria-label="Efeito do corte ${escapeAttr(item.rank)}">
          ${effectButtonsHtml(effect)}
        </div>
        <label>Intensidade
          <input data-preview-effect-intensity type="range" min="0" max="100" step="5" value="${effect.intensity}">
        </label>
      </div>
    </div>
  </article>`;
}
function effectButtonsHtml(current){
  return Object.entries(effectMeta).map(([key, meta]) => {
    const active = current.key === key ? " active" : "";
    return `<button data-preview-effect="${escapeAttr(key)}" class="${active}">${escapeHtml(meta.label)}</button>`;
  }).join("");
}
function bindEffectPreviewControls(){
  document.querySelectorAll("[data-effect-preview] .caption-item").forEach(item => {
    const rank = item.dataset.rank;
    item.querySelectorAll("[data-preview-effect]").forEach(button => {
      button.addEventListener("click", () => setEffectForRank(rank, { key: button.dataset.previewEffect }));
    });
    const intensity = item.querySelector("[data-preview-effect-intensity]");
    if (intensity) {
      intensity.addEventListener("input", () => setEffectForRank(rank, { intensity: Number(intensity.value) }));
      intensity.addEventListener("change", () => setEffectForRank(rank, { intensity: Number(intensity.value) }));
    }
  });
}
function renderOverlayPreview(){
  const preview = document.querySelector("[data-overlay-preview]");
  const summary = document.querySelector("[data-overlay-summary]");
  if (!preview) return;
  const queue = buildExportData().caption_queue || [];
  if (!queue.length) {
    if (summary) summary.textContent = "Marque cortes como Gostei ou escolha destinos para liberar as chamadas.";
    preview.innerHTML = '<div class="overlay-empty">Nenhum corte selecionado ainda.</div>';
    return;
  }
  if (summary) summary.textContent = `${queue.length} saidas selecionadas. Escolha um card e arraste em cada preview.`;
  preview.innerHTML = queue.map(overlayPreviewItemHtml).join("");
  bindOverlayPreviewControls();
}
function overlayPreviewItemHtml(item){
  const layers = normalizeOverlayLayers(item.overlays, item.overlay);
  const src = cacheBustedPreview(item.clip_file || "", `overlay-${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  return `<article class="caption-item" data-rank="${escapeAttr(item.rank)}" data-platform="${escapeAttr(item.platform)}">
    <div class="caption-preview" data-overlay-surface>
      <video controls preload="metadata" src="${escapeAttr(src)}"></video>
      ${layers.map(overlayLayerBoxHtml).join("")}
    </div>
    <div class="caption-item-body">
      <strong>Preview #${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
      <span>${escapeHtml(item.platform_label)}</span><span data-overlay-current>${layers.length ? `${layers.length} camada(s)` : "Sem camada"}</span>
    </div>
  </article>`;
}
function bindOverlayPreviewControls(){
  document.querySelectorAll("[data-overlay-preview] .caption-item video").forEach(video => {
    video.volume = defaultPreviewVolume;
    ["loadedmetadata", "durationchange", "seeked", "timeupdate"].forEach(eventName => {
      video.addEventListener(eventName, () => syncTimedOverlayVisibility(video.closest(".caption-item")));
    });
  });
  document.querySelectorAll("[data-overlay-preview] .caption-item").forEach(item => {
    bindOverlayDrag(item);
    syncTimedOverlayVisibility(item);
  });
}
function bindOverlayDrag(item){
  const surface = item.querySelector("[data-overlay-surface]");
  if (!surface) return;
  item.querySelectorAll("[data-overlay-drag]").forEach(box => {
    if (box.dataset.overlayKey === "none") return;
    const platform = overlayPlatformForItem(item);
    let drag = null;
    const startDrag = event => {
      if (event.type === "mousedown" && drag) return;
      const resizing = !!event.target?.closest?.("[data-overlay-resize]");
      const surfaceRect = surface.getBoundingClientRect();
      const boxRect = box.getBoundingClientRect();
      drag = {
        type: resizing ? "resize" : "move",
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        startLeft: boxRect.left - surfaceRect.left,
        startTop: boxRect.top - surfaceRect.top,
        startWidth: boxRect.width,
        surfaceWidth: surfaceRect.width,
        surfaceHeight: surfaceRect.height,
        moved: false
      };
      if (item.classList.contains("card")) {
        item.dataset.selectedOverlayLayer = box.dataset.overlayLayer;
        renderLayerStrip(item, overlayLayersForRank(item.dataset.rank, platform));
      }
      if (event.pointerId !== undefined && box.setPointerCapture) box.setPointerCapture(event.pointerId);
      document.addEventListener("pointermove", moveDrag);
      document.addEventListener("pointerup", endDrag, { once: true });
      document.addEventListener("pointercancel", endDrag, { once: true });
      document.addEventListener("mousemove", moveDrag);
      document.addEventListener("mouseup", endDrag, { once: true });
      event.preventDefault();
      event.stopPropagation();
    };
    const moveDrag = event => {
      if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
      const dx = event.clientX - drag.startX;
      const dy = event.clientY - drag.startY;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) drag.moved = true;
      const patch = {};
      if (drag.type === "resize") {
        const minWidth = box.dataset.overlayKey === "image" ? .08 : .18;
        const width = clampNumber((drag.startWidth + dx) / drag.surfaceWidth, minWidth, .9);
        box.style.setProperty("--overlay-width", width);
        patch.width = width;
      } else {
        const boxRect = box.getBoundingClientRect();
        const maxLeft = Math.max(drag.surfaceWidth - boxRect.width, 0);
        const maxTop = Math.max(drag.surfaceHeight - boxRect.height, 0);
        const left = clampNumber(drag.startLeft + dx, 0, maxLeft);
        const top = clampNumber(drag.startTop + dy, 0, maxTop);
        patch.x = drag.surfaceWidth ? left / drag.surfaceWidth : 0;
        patch.y = drag.surfaceHeight ? top / drag.surfaceHeight : 0;
        box.style.setProperty("--overlay-x", patch.x);
        box.style.setProperty("--overlay-y", patch.y);
      }
      patchOverlayLayerForRank(item.dataset.rank, box.dataset.overlayLayer, patch, false, platform);
      event.preventDefault();
      event.stopPropagation();
    };
    const endDrag = event => {
      if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
      const shouldInspect = item.classList.contains("card") && !drag.moved;
      const layerId = box.dataset.overlayLayer;
      const moved = drag.moved;
      drag = null;
      document.removeEventListener("pointermove", moveDrag);
      document.removeEventListener("mousemove", moveDrag);
      document.removeEventListener("pointerup", endDrag);
      document.removeEventListener("pointercancel", endDrag);
      document.removeEventListener("mouseup", endDrag);
      if (item.classList.contains("card")) updateOverlayUi(item);
      else renderFinalStage();
      if (moved && item.classList.contains("card")) {
        item.dataset.overlaySuppressClick = "1";
        box.dataset.overlayJustDragged = "1";
        setTimeout(() => { delete box.dataset.overlayJustDragged; }, 0);
      }
      if (shouldInspect) showOverlayInspectorForLayer(item, layerId);
      event.preventDefault();
      event.stopPropagation();
    };
    const inspectLayer = event => {
      if (box.dataset.overlayJustDragged) return;
      if (!item.classList.contains("card")) return;
      event.preventDefault();
      event.stopPropagation();
      item.dataset.selectedOverlayLayer = box.dataset.overlayLayer;
      showOverlayInspectorForLayer(item, box.dataset.overlayLayer);
    };
    box.onpointerdown = startDrag;
    box.onmousedown = startDrag;
    box.onclick = inspectLayer;
    box.ondblclick = inspectLayer;
    box.querySelectorAll("[data-overlay-resize]").forEach(handle => {
      handle.onpointerdown = startDrag;
      handle.onmousedown = startDrag;
    });
  });
}
function renderFinalStage(){
  const queue = buildExportData().caption_queue || [];
  const summary = document.querySelector("[data-final-summary]");
  if (summary) {
    const cameraCount = queue.filter(item => cameraEditHasMovement(item)).length;
    const effectCount = queue.filter(item => normalizeEffect(item.effect).key !== "none").length;
    const overlayCount = queue.reduce((count, item) => count + normalizeOverlayLayers(item.overlays, item.overlay).length, 0);
    const coverLayerCount = queue.reduce((count, item) => count + normalizeCoverOverlayLayers(item.publish_metadata?.cover?.layers).length, 0);
    const bumperCount = queue.reduce((count, item) => count + Object.keys(normalizeBumpers(item.bumpers)).length, 0);
    summary.textContent = queue.length
      ? `${queue.length} na fila; ${cameraCount} camera; ${effectCount} efeito; ${overlayCount} camada; ${coverLayerCount} capa; ${bumperCount} vinheta.`
      : "Nada na fila.";
  }
}
function currentGalleryPath(){
  const path = window.location.pathname || "/";
  if (path.endsWith("/")) return path.replace(/\\/$/, "");
  return path.replace(/\\/[^/]*$/, "");
}
async function touchCurrentProject(){
  const galleryPath = currentGalleryPath();
  if (!galleryPath || galleryPath === "/index") return null;
  const response = await fetch("/api/projects/touch", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({gallery_path: galleryPath}),
    keepalive: true
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || !payload.ok) throw new Error(payload.error || "Nao consegui atualizar recentes.");
  return payload;
}
function isCurrentGalleryEmpty(){
  return localStorage.getItem(emptyGalleryStorageKey) === currentGalleryPath();
}
function syncProjectEmptyState(){
  document.body.dataset.projectEmpty = isCurrentGalleryEmpty() ? "true" : "false";
}
function markCurrentGalleryEmpty(){
  localStorage.setItem(emptyGalleryStorageKey, currentGalleryPath());
  syncProjectEmptyState();
}
function importFormPayload(form){
  const data = new FormData(form);
  return {
    source_url: String(data.get("source_url") || "").trim(),
    source_path: String(data.get("source_path") || "").trim(),
    output_path: String(data.get("output_path") || "").trim(),
    preview_count: Number(data.get("preview_count") || 10),
    language: String(data.get("language") || "").trim(),
    preset: String(data.get("preset") || "tiktok"),
    duration_profile: String(data.get("duration_profile") || "medium"),
    context_prompt: String(data.get("context_prompt") || "").trim(),
    render_previews: true
  };
}
let settingsLastFocus = null;
function setupSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  const form = document.querySelector("[data-settings-form]");
  const open = document.getElementById("open-settings");
  const close = document.querySelector("[data-settings-close]");
  const test = document.querySelector("[data-settings-test]");
  if (!modal || !form || !open) return;
  open.addEventListener("click", () => openSettingsPanel());
  close?.addEventListener("click", () => closeSettingsPanel());
  modal.addEventListener("click", event => { if (event.target === modal) closeSettingsPanel(); });
  document.addEventListener("keydown", event => {
    if (modal.hidden) return;
    if (event.key === "Escape") closeSettingsPanel();
    if (event.key === "Tab") trapSettingsFocus(event);
  });
  form.addEventListener("submit", event => {
    event.preventDefault();
    saveSettingsForm(form);
  });
  test?.addEventListener("click", () => testSettingsConnection(form));
  loadOpenaiSettings();
}
function openSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal) return;
  settingsLastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  modal.hidden = false;
  modal.classList.remove("is-closing");
  requestAnimationFrame(() => modal.classList.add("is-open"));
  loadOpenaiSettings();
  modal.querySelector("[data-settings-panel]")?.focus();
}
function closeSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal || modal.hidden) return;
  modal.classList.remove("is-open");
  modal.classList.add("is-closing");
  window.setTimeout(() => {
    modal.hidden = true;
    modal.classList.remove("is-closing");
    settingsLastFocus?.focus?.();
    settingsLastFocus = null;
  }, 190);
}
function settingsFocusableElements(modal){
  return Array.from(modal.querySelectorAll("button,input,select,textarea,a[href],[tabindex]:not([tabindex='-1'])"))
    .filter(element => !element.disabled && !element.hidden && element.offsetParent !== null);
}
function trapSettingsFocus(event){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal || modal.hidden) return;
  const focusable = settingsFocusableElements(modal);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
async function loadOpenaiSettings(){
  const form = document.querySelector("[data-settings-form]");
  const status = document.querySelector("[data-settings-status]");
  if (!form) return;
  try {
    const response = await fetch("/api/settings/openai");
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao carregar configuracoes.");
    applySettingsPayload(form, payload.settings || {}, payload.usage || {});
  } catch (error) {
    if (status) status.textContent = error.message || "Nao consegui carregar configuracoes.";
  }
}
function applySettingsPayload(form, settings, usage){
  form.elements.ai_provider.value = settings.ai_provider || "openai";
  form.elements.openai_model.value = settings.openai_model || "gpt-5-mini";
  form.elements.transcribe_model.value = settings.transcribe_model || "whisper-1";
  form.elements.api_key.value = "";
  const status = document.querySelector("[data-settings-status]");
  if (status) {
    const key = settings.key_configured ? "Token configurado" : "Token nao configurado";
    status.textContent = `${key} - ${settings.openai_model || "gpt-5-mini"} / ${settings.transcribe_model || "whisper-1"}`;
  }
  updateOpenaiSettingsIndicator(settings);
  renderSettingsUsage(usage);
}
function updateOpenaiSettingsIndicator(settings){
  const button = document.getElementById("open-settings");
  if (!button) return;
  const provider = String(settings?.ai_provider || "openai");
  const ready = Boolean(settings?.key_configured) && provider !== "local";
  button.classList.toggle("is-openai-ready", ready);
  button.setAttribute("aria-label", ready ? "OpenAI configurada" : "Configuracoes OpenAI");
  button.title = ready ? "OpenAI configurada" : "Configuracoes OpenAI";
}
function settingsPayloadFromForm(form){
  const data = new FormData(form);
  const payload = {
    ai_provider: String(data.get("ai_provider") || "openai"),
    openai_model: String(data.get("openai_model") || "gpt-5-mini"),
    transcribe_model: String(data.get("transcribe_model") || "whisper-1")
  };
  const apiKey = String(data.get("api_key") || "").trim();
  if (apiKey) payload.api_key = apiKey;
  return payload;
}
async function saveSettingsForm(form){
  const status = document.querySelector("[data-settings-status]");
  if (status) status.textContent = "Salvando...";
  try {
    const response = await fetch("/api/settings/openai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settingsPayloadFromForm(form))
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao salvar configuracoes.");
    applySettingsPayload(form, payload.settings || {}, payload.usage || {});
    if (status) status.textContent = `Salvo. ${status.textContent}`;
    refreshImportKeyBanner();
  } catch (error) {
    if (status) status.textContent = error.message || "Nao consegui salvar.";
  }
}
async function testSettingsConnection(form){
  const status = document.querySelector("[data-settings-status]");
  const button = document.querySelector("[data-settings-test]");
  if (status) status.textContent = "Testando conexao...";
  if (button) button.disabled = true;
  try {
    const payload = settingsPayloadFromForm(form);
    const response = await fetch("/api/settings/openai/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "Falha ao testar conexao.");
    if (status) status.textContent = data.message || "Conexao OpenAI validada.";
    updateOpenaiSettingsIndicator({ ...settingsPayloadFromForm(form), key_configured: true });
  } catch (error) {
    if (status) status.textContent = error.message || "Nao consegui validar a conexao.";
    updateOpenaiSettingsIndicator({ ...settingsPayloadFromForm(form), key_configured: false });
  } finally {
    if (button) button.disabled = false;
  }
}
function renderSettingsUsage(usage){
  const target = document.querySelector("[data-settings-usage]");
  if (!target) return;
  const total = Number(usage.estimated_total_usd || 0);
  const count = Number(usage.event_count || 0);
  const last = usage.last_event || {};
  const lastText = last.operation
    ? `Ultimo: ${escapeHtml(last.operation)} em ${escapeHtml(last.model || "-")} - ${formatUsd(last.estimated_usd || 0)}`
    : "Ultimo: sem registro.";
  target.innerHTML = `<strong>Total local estimado: ${formatUsd(total)}</strong><span>${count} evento(s) registrado(s).</span><span>${lastText}</span>`;
}
function formatUsd(value){
  return `$${Number(value || 0).toFixed(4)}`;
}
function setupImportPathButtons(){
  const form = document.querySelector("[data-import-form]");
  if (!form) return;
  const outputPath = form.querySelector("[name=output_path]");
  const sourcePath = form.querySelector("[name=source_path]");
  const status = document.querySelector("[data-import-status]");
  const selectFolder = form.querySelector("[data-select-folder]");
  const selectVideoFile = form.querySelector("[data-select-video-file]");
  if (selectFolder && outputPath) {
    selectFolder.addEventListener("click", async () => {
      selectFolder.disabled = true;
      if (status) status.textContent = "Abrindo seletor de pasta...";
      try {
        const response = await fetch("/api/select-folder", { method: "POST" });
        const payload = await response.json();
        if (!response.ok || !payload.ok) throw new Error(payload.error || "Nao consegui selecionar a pasta.");
        outputPath.value = payload.path || outputPath.value;
        if (status) status.textContent = "Pasta selecionada.";
      } catch (error) {
        if (status) status.textContent = error.message || "Seletor de pasta indisponivel.";
      } finally {
        selectFolder.disabled = false;
      }
    });
  }
  if (selectVideoFile && sourcePath) {
    selectVideoFile.addEventListener("click", async () => {
      selectVideoFile.disabled = true;
      if (status) status.textContent = "Abrindo seletor de video...";
      try {
        const response = await fetch("/api/select-video-file", { method: "POST" });
        const payload = await response.json();
        if (!response.ok || !payload.ok) throw new Error(payload.error || "Nao consegui selecionar o arquivo.");
        sourcePath.value = payload.path || sourcePath.value;
        if (status) status.textContent = "Video local selecionado.";
      } catch (error) {
        if (status) status.textContent = error.message || "Seletor de arquivo indisponivel.";
      } finally {
        selectVideoFile.disabled = false;
      }
    });
  }
}
let importOpenaiState = { provider: "openai", keyConfigured: true };
function importNeedsOpenaiKey(){
  return importOpenaiState.provider === "openai" && !importOpenaiState.keyConfigured;
}
async function refreshImportKeyBanner(){
  const banner = document.querySelector("[data-import-key-banner]");
  if (!banner) return;
  try {
    const response = await fetch("/api/settings/openai");
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao carregar configuracoes.");
    const settings = payload.settings || {};
    importOpenaiState = {
      provider: String(settings.ai_provider || "openai"),
      keyConfigured: Boolean(settings.key_configured)
    };
    updateOpenaiSettingsIndicator(settings);
  } catch (error) {
    console.warn("Nao consegui checar a chave OpenAI:", error);
    importOpenaiState = { provider: "openai", keyConfigured: true };
    updateOpenaiSettingsIndicator({ ai_provider: "openai", key_configured: false });
  }
  banner.hidden = !importNeedsOpenaiKey();
}
function setupImportKeyBanner(){
  const banner = document.querySelector("[data-import-key-banner]");
  if (!banner) return;
  banner.querySelector("[data-import-key-open]")?.addEventListener("click", () => openSettingsPanel());
  refreshImportKeyBanner();
}
async function startImportJob(form){
  const status = document.querySelector("[data-import-status]");
  const result = document.querySelector("[data-import-result]");
  const button = form.querySelector("button[type=submit]");
  const outputPath = form.querySelector("[name=output_path]");
  if (!String(outputPath?.value || "").trim()) {
    if (status) status.textContent = "Escolha a pasta onde os videos finais serao salvos.";
    outputPath?.focus();
    return;
  }
  if (importNeedsOpenaiKey()) {
    if (status) status.textContent = "Adicione sua chave OpenAI nas configuracoes para importar com IA.";
    openSettingsPanel();
    return;
  }
  if (result) result.innerHTML = "";
  if (status) status.textContent = "Criando job de importacao...";
  if (button) button.disabled = true;
  try {
    const response = await fetch("/api/import-jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(importFormPayload(form))
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao importar.");
    if (status) status.textContent = payload.job?.message || "Importacao iniciada.";
    pollImportJob(payload.job.id, button);
  } catch (error) {
    if (button) button.disabled = false;
    if (status) status.textContent = "Nao consegui iniciar a importacao.";
    if (result) result.innerHTML = `<code>${escapeHtml(error.message || String(error))}</code>`;
  }
}
async function pollImportJob(jobId, button){
  const status = document.querySelector("[data-import-status]");
  const result = document.querySelector("[data-import-result]");
  try {
    const response = await fetch(`/api/import-jobs/${encodeURIComponent(jobId)}`);
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Job nao encontrado.");
    const job = payload.job || {};
    if (status) status.textContent = `${job.message || "Processando..."} (${job.status || "running"})`;
    if (job.status === "ready") {
      if (button) button.disabled = false;
      if (result) result.innerHTML = `<a href="${escapeAttr(job.output_url)}">Abrir projeto importado</a>`;
      if (job.output_url) window.location.assign(job.output_url);
      return;
    }
    if (job.status === "failed" || job.status === "cancelled") {
      if (button) button.disabled = false;
      if (result) result.innerHTML = `<code>${escapeHtml(job.stderr || job.message || "Importacao encerrada.")}</code>`;
      return;
    }
    window.setTimeout(() => pollImportJob(jobId, button), 1200);
  } catch (error) {
    if (button) button.disabled = false;
    if (status) status.textContent = "Nao consegui acompanhar a importacao.";
    if (result) result.innerHTML = `<code>${escapeHtml(error.message || String(error))}</code>`;
  }
}
function captionLines(){
  return Number(localStorage.getItem("cutted-caption-lines") || 2);
}
function captionWidth(){
  return Number(localStorage.getItem("cutted-caption-width") || 28);
}
function captionSize(){
  return Number(localStorage.getItem("cutted-caption-size") || defaultCaptionSize());
}
function defaultCaptionSize(){
  const format = document.body.dataset.format || "tiktok";
  return format === "youtube" || format === "facebook" ? 54 : 72;
}
function captionBottom(){
  return Number(localStorage.getItem("cutted-caption-bottom") || defaultCaptionBottom());
}
function defaultCaptionBottom(){
  const format = document.body.dataset.format || "tiktok";
  if (format === "youtube") return 11;
  if (format === "facebook") return 9;
  return 16;
}
function captionMode(){
  const saved = localStorage.getItem("cutted-caption-mode");
  if (saved === "animated" || saved === "on" || saved === "off") return saved;
  return localStorage.getItem("cutted-caption-enabled") === "0" ? "off" : "on";
}
function captionTextColor(){
  return normalizeCaptionColor(localStorage.getItem("cutted-caption-text-color"), "#ffffff");
}
function captionBackgroundColor(){
  return normalizeCaptionBackground(localStorage.getItem("cutted-caption-background-color"));
}
function captionHighlightBackgroundColor(){
  const stored = localStorage.getItem("cutted-caption-highlight-background-color");
  if (stored) return normalizeCaptionHighlightBackground(stored);
  const background = captionBackgroundColor();
  return background === "transparent" ? "#000000" : normalizeCaptionHighlightBackground(background);
}
function captionStyle(){
  return {
    size: captionSize(),
    width: captionWidth(),
    bottom: captionBottom(),
    mode: captionMode(),
    textColor: captionTextColor(),
    backgroundColor: captionBackgroundColor(),
    highlightBackgroundColor: captionHighlightBackgroundColor()
  };
}
function captionEnabled(){
  return captionMode() !== "off";
}
function normalizeCaptionColor(value, fallback){
  const raw = String(value || "").trim();
  return /^#[0-9a-f]{6}$/i.test(raw) ? raw.toLowerCase() : fallback;
}
function normalizeCaptionBackground(value){
  const raw = String(value || "").trim().toLowerCase();
  if (!raw || raw === "transparent" || raw === "none") return "transparent";
  return normalizeCaptionColor(raw, "#000000");
}
function normalizeCaptionHighlightBackground(value){
  return normalizeCaptionColor(value, "#000000");
}
function storeCaptionStyle(style){
  if (!style || typeof style !== "object") return;
  if (Number.isFinite(Number(style.size))) localStorage.setItem("cutted-caption-size", String(clampNumber(Number(style.size), 24, 140)));
  if (Number.isFinite(Number(style.width))) localStorage.setItem("cutted-caption-width", String(clampNumber(Number(style.width), 12, 56)));
  if (Number.isFinite(Number(style.bottom))) localStorage.setItem("cutted-caption-bottom", String(clampNumber(Number(style.bottom), 6, 32)));
  if (style.mode) localStorage.setItem("cutted-caption-mode", normalizeCaptionMode(style.mode));
  if (style.textColor) localStorage.setItem("cutted-caption-text-color", normalizeCaptionColor(style.textColor, captionTextColor()));
  if (style.backgroundColor) localStorage.setItem("cutted-caption-background-color", normalizeCaptionBackground(style.backgroundColor));
  if (style.highlightBackgroundColor) localStorage.setItem("cutted-caption-highlight-background-color", normalizeCaptionHighlightBackground(style.highlightBackgroundColor));
}
function captionSettingsForCard(card){
  if (!card?.dataset?.rank) return defaultCaptionSettings();
  return platformEditForRank(card.dataset.rank, activePlatformForRank(card.dataset.rank)).captions;
}
function syncPreviewCaptionsForOpenCards(){
  document.querySelectorAll(".card[open]").forEach(card => syncPreviewCaptions(card));
}
function syncPreviewCaptions(card, time = null){
  const layer = card?.querySelector("[data-preview-caption-layer]");
  if (!layer) return;
  const captions = captionSettingsForCard(card);
  applyPreviewCaptionStyle(card, layer);
  if (!captions.enabled) {
    layer.dataset.visible = "false";
    layer.innerHTML = "";
    delete layer.dataset.captionPopKey;
    return;
  }
  const context = previewCaptionContextForCard(card, time);
  if (!context?.event) {
    layer.dataset.visible = "false";
    layer.innerHTML = "";
    delete layer.dataset.captionPopKey;
    return;
  }
  layer.dataset.mode = captions.style.mode === "animated" ? "animated" : "static";
  if (captions.style.mode === "animated") {
    const rendered = previewAnimatedCaptionRender(context.event, context.position);
    if (!rendered.html) {
      layer.innerHTML = "";
      delete layer.dataset.captionPopKey;
    } else if (layer.dataset.captionPopKey !== rendered.key || !layer.innerHTML.trim()) {
      layer.innerHTML = rendered.html;
      layer.dataset.captionPopKey = rendered.key;
    }
  } else {
    delete layer.dataset.captionPopKey;
    const lines = wrapPreviewCaptionLines(context.event.text, captions.style.width, captionLines());
    layer.innerHTML = `<span>${lines.map(escapeHtml).join("<br>")}</span>`;
  }
  layer.dataset.visible = "true";
}
function applyPreviewCaptionStyle(card, layer){
  const style = captionSettingsForCard(card).style;
  const media = card?.querySelector(".media");
  const mediaWidth = media ? media.getBoundingClientRect().width : 0;
  const platformWidth = previewCaptionPlatformWidth(card);
  const fontSize = mediaWidth > 0 ? clampNumber((style.size / platformWidth) * mediaWidth, 14, 72) : style.size;
  layer.style.setProperty("--preview-caption-size", `${fontSize.toFixed(2)}px`);
  layer.style.setProperty("--preview-caption-bottom", `${clampNumber(Number(style.bottom || defaultCaptionBottom()), 6, 32).toFixed(1)}%`);
  layer.style.setProperty("--preview-caption-color", style.textColor);
  layer.style.setProperty("--preview-caption-bg", captionBackgroundCss(style.backgroundColor));
  layer.style.setProperty("--preview-caption-highlight-bg", captionBackgroundCss(style.highlightBackgroundColor || "#000000", true));
  layer.style.setProperty("--preview-caption-padding", style.backgroundColor === "transparent" ? "0" : ".12em .28em");
}
function previewCaptionPlatformWidth(card){
  const format = card?.dataset?.previewFormat || document.body.dataset.format || "tiktok";
  return format === "youtube" ? 1920 : 1080;
}
function captionBackgroundCss(value, forceFallback = false){
  if (value === "transparent") return forceFallback ? "#000000cc" : "transparent";
  const color = normalizeCaptionColor(value, "#000000");
  return `${color}cc`;
}
function previewCaptionEventForCard(card, time = null){
  return previewCaptionContextForCard(card, time)?.event || null;
}
function previewCaptionContextForCard(card, time = null){
  const moment = previewMomentForCard(card);
  if (!moment) return null;
  const row = adjustedMoment(moment);
  const values = trimValues(card);
  const video = primaryCameraVideo(card);
  const raw = time === null && video && Number.isFinite(video.currentTime) ? video.currentTime : time;
  const current = clampPreviewTime(values, Number(raw ?? values.trimStart));
  const position = Math.max(0, current - values.trimStart);
  if (captionSettingsForCard(card).style.mode === "animated") {
    const window = previewAnimatedCaptionTimeline(row).find(item => position >= item.start && position < item.end) || null;
    return window ? { event: window, position } : null;
  }
  const events = previewCaptionEvents(row);
  if (!events.length) return null;
  const event = events.find(item => position >= item.start && position < item.end) || null;
  return event ? { event, position } : null;
}
function animatedCaptionLeadSeconds(){
  return .14;
}
function previewMomentForCard(card){
  const rank = String(card?.dataset?.rank || "");
  return (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === rank) || null;
}
function previewCaptionEvents(row){
  const duration = Math.max(Number(row.adjusted_duration || 0), .1);
  const segmentEvents = previewCaptionEventsFromSegments(row);
  if (segmentEvents.length) return normalizePreviewCaptionEvents(segmentEvents, duration);
  const chunks = previewCaptionChunks(previewCaptionSourceText(row), captionWidth(), captionLines(), duration);
  return normalizePreviewCaptionEvents(distributedPreviewCaptionEvents(chunks, duration), duration);
}
function previewCaptionEventsFromSegments(row){
  const segments = Array.isArray(row.caption_segments) ? row.caption_segments : [];
  const clipStart = Number(row.adjusted_start || row.start || 0);
  const clipEnd = Number(row.adjusted_end || row.end || (clipStart + Number(row.adjusted_duration || 0)));
  return segments.map(item => previewCaptionEventFromSegment(item, clipStart, clipEnd)).filter(Boolean);
}
function previewCaptionEventFromSegment(item, clipStart, clipEnd){
  if (!item || typeof item !== "object") return null;
  const start = Math.max(Number(item.start || 0), clipStart) - clipStart;
  const end = Math.min(Number(item.end || 0), clipEnd) - clipStart;
  const text = cleanPreviewCaptionText(String(item.text || ""));
  if (!text || end <= start) return null;
  return { start: Number(start.toFixed(3)), end: Number(Math.max(end, start + .35).toFixed(3)), text };
}
function normalizePreviewCaptionEvents(events, duration){
  return events.slice().sort((a, b) => a.start - b.start || a.end - b.end).map((event, index, source) => {
    const start = clampNumber(event.start, 0, duration);
    let end = clampNumber(event.end, start, duration);
    if (index + 1 < source.length) {
      const nextStart = clampNumber(source[index + 1].start, 0, duration);
      end = Math.min(end, Math.max(start, nextStart - .04));
    }
    return { start: Number(start.toFixed(3)), end: Number(end.toFixed(3)), text: event.text };
  }).filter(event => event.end - event.start >= .12);
}
function distributedPreviewCaptionEvents(chunks, duration){
  const slot = duration / Math.max(chunks.length, 1);
  return chunks.map((text, index) => ({
    start: Number((index * slot).toFixed(3)),
    end: Number((index === chunks.length - 1 ? duration : (index + 1) * slot).toFixed(3)),
    text
  }));
}
function previewAnimatedCaptionHtml(event, position){
  return previewAnimatedCaptionRender(event, position).html;
}
function previewAnimatedCaptionRender(event, position){
  const wordWindow = event?.active ? event : previewAnimatedCaptionWindow(event, position);
  if (!wordWindow) return { key: "", html: "" };
  const key = wordWindow.key || `${Number(event.start || 0).toFixed(2)}-${wordWindow.index || 0}`;
  const html = `<span class="preview-caption-window" data-caption-pop-key="${key}">
    <span class="preview-caption-word preview-caption-side preview-caption-prev">${escapeHtml(wordWindow.previous)}</span>
    <span class="preview-caption-word preview-caption-active">${escapeHtml(wordWindow.active)}</span>
    <span class="preview-caption-word preview-caption-side preview-caption-next">${escapeHtml(wordWindow.next)}</span>
  </span>`;
  return { key, html };
}
function previewAnimatedCaptionWindow(event, position){
  const words = previewSmartAnimatedCaptionWords(event);
  if (!words.length) return null;
  const timings = previewAnimatedCaptionWordTimings(event, words);
  const slot = timings.find(item => position >= item.start && position < item.end) || timings[timings.length - 1];
  const index = slot ? slot.index : 0;
  return {
    index,
    previous: index > 0 ? words[index - 1] : "",
    active: words[index] || words[0],
    next: index + 1 < words.length ? words[index + 1] : ""
  };
}
function previewAnimatedCaptionTimeline(row){
  const duration = Math.max(Number(row.adjusted_duration || 0), .1);
  const raw = [];
  previewCaptionEvents(row).forEach(event => {
    const words = previewSmartAnimatedCaptionWords(event);
    if (!words.length) return;
    const timings = previewAnimatedCaptionWordTimings(event, words);
    timings.forEach((slot, index) => {
      raw.push({
        start: slot.start,
        end: slot.end,
        previous: index > 0 ? timings[index - 1].word : "",
        active: slot.word,
        next: index + 1 < timings.length ? timings[index + 1].word : "",
        sourceStart: event.start
      });
    });
  });
  return previewAnimatedCaptionDisplayWindows(raw, duration);
}
function previewAnimatedCaptionDisplayWindows(windows, duration){
  let previousEnd = 0;
  return windows.map((window, index) => {
    const rawStart = clampNumber(Number(window.start || 0), 0, duration);
    const rawEnd = clampNumber(Number(window.end || rawStart), rawStart, duration);
    const rawDuration = Math.max(rawEnd - rawStart, .08);
    let start = clampNumber(rawStart - animatedCaptionLeadSeconds(), 0, duration);
    let end = clampNumber(rawEnd - animatedCaptionLeadSeconds(), start, duration);
    if (rawStart <= animatedCaptionLeadSeconds()) {
      end = clampNumber(Math.max(end, start + rawDuration), start, duration);
    }
    if (start < previousEnd) {
      start = previousEnd;
      end = clampNumber(Math.max(end, start + .08), start, duration);
    }
    previousEnd = end;
    if (end <= start) return null;
    return {
      key: `${start.toFixed(3)}-${index}`,
      index,
      start: Number(start.toFixed(3)),
      end: Number(end.toFixed(3)),
      previous: window.previous || "",
      active: window.active || "",
      next: window.next || ""
    };
  }).filter(Boolean);
}
function previewAnimatedCaptionWord(word){
  const text = String(word || "");
  return text.length <= 18 ? text : `${text.slice(0, 17)}...`;
}
const PREVIEW_ANIMATED_CAPTION_MIN_DISPLAY_SECONDS = .22;
const PREVIEW_ANIMATED_CAPTION_TARGET_MIN_WORD_SECONDS = .24;
const PREVIEW_ANIMATED_CAPTION_FAST_WORD_SECONDS = .20;
const PREVIEW_ANIMATED_CAPTION_MAX_GROUP_WORDS = 3;
const PREVIEW_ANIMATED_CAPTION_PROPER_NOUN_STOPWORDS = new Set([
  "a", "as", "o", "os", "um", "uma", "uns", "umas", "de", "da", "das", "do", "dos",
  "e", "ou", "mas", "porque", "por", "para", "pra", "com", "sem", "em", "no", "na",
  "nos", "nas", "ao", "aos", "ai", "aí", "entao", "então", "so", "só", "que", "quem",
  "qual", "quando", "onde", "como", "isso", "essa", "esse", "isto", "esta", "este",
  "eu", "tu", "ele", "ela", "nos", "nós", "voces", "vocês", "voce", "você", "meu",
  "minha", "seu", "sua", "me", "te", "se", "lhe", "nao", "não", "sim", "e", "é", "eh",
  "foi", "era", "ser", "ter", "tem", "ta", "tá", "tava", "vai", "vou", "vao", "vão",
  "fui", "faz", "fazer", "da", "dá", "dar", "precisa", "preciso", "precisava", "acho",
  "tipo", "cara", "ne", "né", "olha", "bom", "certo", "agora"
]);
const PREVIEW_ANIMATED_CAPTION_FILLER_WORDS = new Set([
  "ah", "aham", "uhum", "hum", "eh", "Ã©", "e", "ai", "aÃ­", "entao", "entÃ£o",
  "tipo", "assim", "ne", "nÃ©", "cara", "mano", "bom", "olha", "certo"
]);
const PREVIEW_ANIMATED_CAPTION_ATTACH_PREVIOUS = new Set([
]);
const PREVIEW_ANIMATED_CAPTION_ATTACH_NEXT = new Set([
  "a", "as", "o", "os", "um", "uma", "uns", "umas", "me", "te", "se", "meu", "minha", "seu", "sua",
  "de", "da", "das", "do", "dos", "com", "sem", "pra", "para", "por", "em", "no", "na", "nos", "nas", "ao", "aos"
]);
function cleanPreviewAnimatedCaptionText(text){
  const clean = cleanPreviewCaptionText(text);
  const properNouns = previewAnimatedCaptionProperNouns(clean);
  return clean.split(/\\s+/)
    .map(word => previewAnimatedCaptionDisplayWord(word, properNouns))
    .filter(Boolean)
    .join(" ");
}
function previewSmartAnimatedCaptionWords(event){
  const start = Number(event?.start || 0);
  const end = Math.max(Number(event?.end || start + .12), start + .12);
  let words = cleanPreviewAnimatedCaptionText(event?.text || "").split(/\\s+/).filter(Boolean).map(previewAnimatedCaptionWord);
  if (!words.length) return [];
  words = previewSmartAnimatedCaptionDropFillers(words, end - start);
  return previewSmartAnimatedCaptionGroupWords(words, end - start);
}
function previewSmartAnimatedCaptionDropFillers(words, duration){
  const wordSeconds = duration / Math.max(words.length, 1);
  if (wordSeconds >= PREVIEW_ANIMATED_CAPTION_FAST_WORD_SECONDS) return words;
  const filtered = words.filter(word => previewAnimatedCaptionIsNumericToken(word) || !PREVIEW_ANIMATED_CAPTION_FILLER_WORDS.has(previewAnimatedCaptionWordKey(word)));
  return filtered.length ? filtered : words;
}
function previewSmartAnimatedCaptionGroupWords(words, duration){
  const wordSeconds = duration / Math.max(words.length, 1);
  if (wordSeconds >= PREVIEW_ANIMATED_CAPTION_TARGET_MIN_WORD_SECONDS) return words;
  const groups = [];
  words.forEach(word => {
    if (previewSmartAnimatedCaptionShouldAttachToPrevious(groups, word)) {
      groups[groups.length - 1] = `${groups[groups.length - 1]} ${word}`;
      return;
    }
    groups.push(word);
  });
  return previewSmartAnimatedCaptionBalanceGroups(groups);
}
function previewSmartAnimatedCaptionShouldAttachToPrevious(groups, word){
  if (!groups.length) return false;
  const key = previewAnimatedCaptionWordKey(word);
  const previous = groups[groups.length - 1].split(/\\s+/).filter(Boolean).pop() || "";
  if (PREVIEW_ANIMATED_CAPTION_ATTACH_PREVIOUS.has(key)) return previewSmartAnimatedCaptionGroupSize(groups[groups.length - 1]) < PREVIEW_ANIMATED_CAPTION_MAX_GROUP_WORDS;
  if (PREVIEW_ANIMATED_CAPTION_ATTACH_NEXT.has(previewAnimatedCaptionWordKey(previous))) return previewSmartAnimatedCaptionGroupSize(groups[groups.length - 1]) < PREVIEW_ANIMATED_CAPTION_MAX_GROUP_WORDS;
  return key === previewAnimatedCaptionWordKey(previous) && previewSmartAnimatedCaptionGroupSize(groups[groups.length - 1]) < PREVIEW_ANIMATED_CAPTION_MAX_GROUP_WORDS;
}
function previewSmartAnimatedCaptionBalanceGroups(groups){
  const result = [];
  groups.forEach(group => {
    const key = previewAnimatedCaptionWordKey(group);
    if (result.length && PREVIEW_ANIMATED_CAPTION_ATTACH_PREVIOUS.has(key) && previewSmartAnimatedCaptionGroupSize(result[result.length - 1]) < PREVIEW_ANIMATED_CAPTION_MAX_GROUP_WORDS) {
      result[result.length - 1] = `${result[result.length - 1]} ${group}`;
      return;
    }
    result.push(group);
  });
  return result;
}
function previewSmartAnimatedCaptionGroupSize(group){
  return String(group || "").split(/\\s+/).filter(Boolean).length;
}
function previewAnimatedCaptionIsNumericToken(word){
  return /\\d/.test(String(word || ""));
}
function previewAnimatedCaptionProperNouns(text){
  const matches = Array.from(String(text || "").matchAll(/[\\p{L}\\p{N}_]+/gu));
  const result = new Set();
  matches.forEach((match, index) => {
    const word = match[0];
    if (!previewAnimatedCaptionIsCapitalizedWord(word)) return;
    const key = previewAnimatedCaptionWordKey(word);
    if (PREVIEW_ANIMATED_CAPTION_PROPER_NOUN_STOPWORDS.has(key)) return;
    const before = String(text || "").slice(0, match.index || 0);
    const sentenceStart = !before.trim() || /[.!?…]\\s*$/.test(before);
    const previousCapitalized = index > 0 && previewAnimatedCaptionIsCapitalizedWord(matches[index - 1][0]);
    const nextCapitalized = index + 1 < matches.length && previewAnimatedCaptionIsCapitalizedWord(matches[index + 1][0]);
    if (!sentenceStart || previousCapitalized || nextCapitalized) result.add(key);
  });
  return result;
}
function previewAnimatedCaptionDisplayWord(word, properNouns){
  const clean = previewAnimatedCaptionCleanWord(word);
  if (!clean) return "";
  const key = previewAnimatedCaptionWordKey(clean);
  if (previewAnimatedCaptionIsAcronym(clean) || properNouns.has(key)) return clean;
  return clean.toLocaleLowerCase("pt-BR");
}
function previewAnimatedCaptionCleanWord(word){
  const raw = String(word || "").replace(/[^\\p{L}\\p{N}_.,:%]+/gu, "");
  return Array.from(raw).filter((char, index, chars) => {
    if (".,:".includes(char)) {
      return index > 0 && index + 1 < chars.length && /\\p{N}/u.test(chars[index - 1]) && /\\p{N}/u.test(chars[index + 1]);
    }
    if (char === "%") {
      return index > 0 && /\\p{N}/u.test(chars[index - 1]);
    }
    return true;
  }).join("");
}
function previewAnimatedCaptionWordKey(word){
  return String(word || "").replace(/[^\\p{L}\\p{N}_]+/gu, "").toLocaleLowerCase("pt-BR");
}
function previewAnimatedCaptionIsCapitalizedWord(word){
  const letters = Array.from(String(word || "").matchAll(/\\p{L}/gu)).map(match => match[0]);
  return Boolean(letters.length) && letters[0] === letters[0].toLocaleUpperCase("pt-BR") && !previewAnimatedCaptionIsAcronym(word);
}
function previewAnimatedCaptionIsAcronym(word){
  const letters = Array.from(String(word || "").matchAll(/\\p{L}/gu)).map(match => match[0]).join("");
  return letters.length > 1 && letters.length <= 6 && letters === letters.toLocaleUpperCase("pt-BR");
}
function previewAnimatedCaptionWordTimings(event, words){
  const start = Number(event.start || 0);
  const end = Math.max(Number(event.end || start + .12), start + .12);
  const duration = end - start;
  const weights = words.map(previewAnimatedCaptionWordWeight);
  const total = weights.reduce((sum, value) => sum + value, 0) || Math.max(words.length, 1);
  let cursor = start;
  const timings = words.map((word, index) => {
    const wordEnd = index === words.length - 1 ? end : Math.min(end, cursor + (duration * weights[index] / total));
    const timing = { index, word, start: cursor, end: wordEnd };
    cursor = wordEnd;
    return timing;
  });
  return previewMergeFastAnimatedCaptionTimings(timings);
}
function previewMergeFastAnimatedCaptionTimings(timings){
  const groups = timings.map(item => ({ word: item.word, start: item.start, end: item.end }));
  while (groups.length > 1) {
    const index = groups.findIndex(item => item.end - item.start < PREVIEW_ANIMATED_CAPTION_MIN_DISPLAY_SECONDS);
    if (index < 0) break;
    const target = index + 1 < groups.length ? index + 1 : index - 1;
    const firstIndex = Math.min(index, target);
    const secondIndex = Math.max(index, target);
    const first = groups[firstIndex];
    const second = groups[secondIndex];
    groups.splice(firstIndex, secondIndex - firstIndex + 1, {
      word: `${first.word} ${second.word}`,
      start: first.start,
      end: second.end
    });
  }
  return groups.map((item, index) => ({ index, word: item.word, start: item.start, end: item.end }));
}
function previewAnimatedCaptionWordWeight(word){
  const core = String(word || "").replace(/[^\\p{L}\\p{N}_]+/gu, "");
  return clampNumber(Math.sqrt(Math.max(core.length, 1)), .7, 3);
}
function previewCaptionSourceText(row){
  const transcript = String(row.transcript || "").trim();
  if (transcript) return cleanPreviewCaptionText(transcript);
  return cleanPreviewCaptionText(String(row.peak_text || row.title || "Legenda do corte"));
}
const PREVIEW_CAPTION_MOJIBAKE_REPLACEMENTS = new Map([
  ["\u00c3\u00a1", "\u00e1"],
  ["\u00c3\u00a0", "\u00e0"],
  ["\u00c3\u00a2", "\u00e2"],
  ["\u00c3\u00a3", "\u00e3"],
  ["\u00c3\u00a4", "\u00e4"],
  ["\u00c3\u00a9", "\u00e9"],
  ["\u00c3\u00aa", "\u00ea"],
  ["\u00c3\u00ad", "\u00ed"],
  ["\u00c3\u00b3", "\u00f3"],
  ["\u00c3\u00b4", "\u00f4"],
  ["\u00c3\u00b5", "\u00f5"],
  ["\u00c3\u00ba", "\u00fa"],
  ["\u00c3\u00bc", "\u00fc"],
  ["\u00c3\u00a7", "\u00e7"],
  ["\u00c3\u0081", "\u00c1"],
  ["\u00c3\u0080", "\u00c0"],
  ["\u00c3\u0082", "\u00c2"],
  ["\u00c3\u0083", "\u00c3"],
  ["\u00c3\u0089", "\u00c9"],
  ["\u00c3\u008a", "\u00ca"],
  ["\u00c3\u008d", "\u00cd"],
  ["\u00c3\u0093", "\u00d3"],
  ["\u00c3\u0094", "\u00d4"],
  ["\u00c3\u0095", "\u00d5"],
  ["\u00c3\u009a", "\u00da"],
  ["\u00c3\u009c", "\u00dc"],
  ["\u00c3\u0087", "\u00c7"],
  ["\u00c2\u00ba", "\u00ba"],
  ["\u00c2\u00aa", "\u00aa"],
  ["\u00c2\u00b7", "\u00b7"],
  ["\u00c2\u00b4", "\u00b4"]
]);
function repairPreviewCaptionEncoding(value){
  const text = String(value || "");
  if (!/[ÃÂâ]/.test(text)) return text;
  const repaired = repairPreviewCaptionEncodingAsUtf8(text);
  const mapped = replacePreviewCaptionMojibakeSequences(repaired);
  return previewCaptionMojibakeScore(mapped) <= previewCaptionMojibakeScore(text) ? mapped : text;
}
function repairPreviewCaptionEncodingAsUtf8(text){
  try {
    const bytes = Array.from(text, char => {
      const code = char.charCodeAt(0);
      if (code > 255) throw new Error("Not latin-1 text");
      return code;
    });
    const repaired = new TextDecoder("utf-8", { fatal: true }).decode(new Uint8Array(bytes));
    return previewCaptionMojibakeScore(repaired) < previewCaptionMojibakeScore(text) ? repaired : text;
  } catch (_error) {
    return text;
  }
}
function replacePreviewCaptionMojibakeSequences(text){
  let clean = String(text || "");
  PREVIEW_CAPTION_MOJIBAKE_REPLACEMENTS.forEach((target, source) => {
    clean = clean.split(source).join(target);
  });
  return clean;
}
function previewCaptionMojibakeScore(text){
  return (String(text || "").match(/Ã|Â|â€|â™|�/g) || []).length;
}
function cleanPreviewCaptionText(text){
  return repairPreviewCaptionEncoding(text)
    .replace(/[\u201c\u201d]/g, '"')
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/\u2026/g, "...")
    .replace(/\ufeff/g, " ")
    .replace(/[\u2013\u2014]/g, "-")
    .replace(/(^|\\s)(>{1,3}|-{1,2})\\s*/g, " ")
    .replace(/\\s+/g, " ")
    .replace(/\\s+([,.;:!?])/g, "$1")
    .replace(/(\\d)([.,:])\\s+(?=\\d)/g, "$1$2")
    .replace(/([,.;:!?])([^\\s,.;:!?])/g, spaceAfterPreviewCaptionPunctuation)
    .replace(/^(ne\\??|aham|uhum|hum|entao|mas)\\s+/i, "")
    .trim()
    .replace(/^-+|-+$/g, "")
    .trim();
}
function spaceAfterPreviewCaptionPunctuation(match, punctuation, nextChar, offset, value){
  const previousChar = offset > 0 ? String(value || "")[offset - 1] : "";
  if (".,:".includes(punctuation) && /\\d/.test(previousChar) && /\\d/.test(nextChar)) {
    return `${punctuation}${nextChar}`;
  }
  return `${punctuation} ${nextChar}`;
}
function previewCaptionChunks(text, charsPerLine, maxLines, duration){
  const lineWidth = Math.max(12, Number(charsPerLine) || 28);
  const lineCount = Math.max(1, Number(maxLines) || 2);
  const capacity = Math.max(18, lineWidth * lineCount);
  const chunks = greedyPreviewCaptionChunks(String(text || "").split(/\\s+/).filter(Boolean), capacity);
  const limit = Math.max(1, Math.floor(Math.max(duration, 1) / 1.35));
  if (chunks.length > limit) {
    const limited = chunks.slice(0, limit);
    limited[limited.length - 1] = ellipsizePreviewCaption(limited[limited.length - 1]);
    return limited;
  }
  return chunks.length ? chunks : ["Legenda do corte"];
}
function wrapPreviewCaptionLines(text, charsPerLine, maxLines){
  const lineWidth = Math.max(12, Number(charsPerLine) || 28);
  const lineCount = Math.max(1, Number(maxLines) || 2);
  const lines = greedyPreviewCaptionChunks(String(text || "").split(/\\s+/).filter(Boolean), lineWidth);
  if (lines.length <= lineCount) return lines;
  return lines.slice(0, lineCount - 1).concat(lines.slice(lineCount - 1).join(" "));
}
function greedyPreviewCaptionChunks(words, capacity){
  const chunks = [];
  let current = [];
  words.forEach(word => {
    const candidate = current.concat(word).join(" ");
    if (current.length && candidate.length > capacity) {
      chunks.push(current.join(" "));
      current = [word];
    } else {
      current.push(word);
    }
  });
  if (current.length) chunks.push(current.join(" "));
  return chunks;
}
function ellipsizePreviewCaption(text){
  const clean = String(text || "").replace(/[ .,;:]+$/g, "");
  return clean ? `${clean}...` : "...";
}
function syncCaptionInputs(){
  document.querySelectorAll("[data-caption-lines]").forEach(input => { input.value = String(captionLines()); });
  document.querySelectorAll("[data-caption-width]").forEach(input => { input.value = String(captionWidth()); });
  document.querySelectorAll("[data-caption-size]").forEach(input => { input.value = String(captionSize()); });
  document.querySelectorAll("[data-caption-bottom]").forEach(input => { input.value = String(captionBottom()); });
  document.querySelectorAll("[data-caption-text-color]").forEach(input => { input.value = captionTextColor(); });
  document.querySelectorAll("[data-caption-background-color]").forEach(input => { input.value = captionBackgroundColor() === "transparent" ? "#000000" : captionBackgroundColor(); });
  document.querySelectorAll("[data-caption-highlight-background-color]").forEach(input => { input.value = captionHighlightBackgroundColor(); });
  document.querySelectorAll("[data-caption-enabled]").forEach(input => { input.checked = captionEnabled(); });
  document.querySelectorAll("[data-caption-current]").forEach(item => { item.textContent = captionMode() === "animated" ? "Animada" : captionEnabled() ? "Ativada" : "Desligada"; });
}
function captionCommand(){
  const chars = captionWidth();
  const lines = captionLines();
  const script = window.CUTTED_SCRIPT || "cutted.py";
  const coverFrame = renderCoverFrameEnabled() ? " --cover-frame" : "";
  return `python "${script}" caption-selected "caption-queue.json" --out "captioned-clips" --base-dir "." --chars-per-line ${chars} --max-lines ${lines}${coverFrame}`;
}
function renderCoverFrameEnabled(){
  return Boolean(renderQueueState.coverFrame);
}
async function finalizeVideos(){
  const button = document.getElementById("finalize-videos");
  const status = document.querySelector("[data-render-status]");
  const results = document.querySelector("[data-render-results]");
  const data = buildExportData();
  const queue = data.caption_queue || [];
  if (!queue.length) {
    if (status) status.textContent = "Selecione ao menos um corte antes de finalizar.";
    return;
  }
  button.disabled = true;
  if (status) status.textContent = `Renderizando ${queue.length} video(s)...`;
  if (results) results.innerHTML = "";
  try {
    const response = await fetch("/api/finalize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        queue: data,
        chars_per_line: captionWidth(),
        max_lines: captionLines(),
        captions_enabled: queue.some(item => item.captions_enabled !== false),
        cover_frame_enabled: renderCoverFrameEnabled(),
        gallery_path: currentGalleryPath()
      })
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao renderizar.");
    renderFinalizeResults(payload.files || []);
    const exported = payload.export_dir ? ` Exportado em: ${payload.export_dir}` : "";
    if (status) status.textContent = `${payload.count || 0} video(s) finalizado(s).${exported}`;
  } catch (error) {
    if (status) status.textContent = finalizeErrorMessage(error);
  } finally {
    button.disabled = false;
  }
}
function finalizeStorageKey(){
  return `cutted-finalize-results:${currentGalleryPath()}`;
}
function storeFinalizeResults(files){
  if (!Array.isArray(files) || !files.length) return;
  try {
    localStorage.setItem(finalizeStorageKey(), JSON.stringify(files));
  } catch (error) {
    console.warn("Nao foi possivel salvar os resultados renderizados.", error);
  }
}
function storedFinalizeResults(){
  try {
    const raw = localStorage.getItem(finalizeStorageKey());
    const files = raw ? JSON.parse(raw) : [];
    return Array.isArray(files) ? files : [];
  } catch (error) {
    console.warn("Nao foi possivel restaurar os resultados renderizados.", error);
    return [];
  }
}
async function restoreFinalizeResults(){
  const status = document.querySelector("[data-render-status]");
  const cached = storedFinalizeResults();
  if (cached.length) {
    renderFinalizeResults(cached, { skipPersist: true });
    if (status && !status.textContent) status.textContent = `${cached.length} video(s) restaurado(s) desta galeria.`;
  }
  try {
    const response = await fetch(`/api/finalize-results?gallery_path=${encodeURIComponent(currentGalleryPath())}`, { cache: "no-store" });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) return;
    const files = Array.isArray(payload.files) ? payload.files : [];
    if (!files.length) return;
    renderFinalizeResults(files);
    const exported = payload.export_dir ? ` Exportado em: ${payload.export_dir}` : "";
    if (status) {
      status.textContent = payload.ready
        ? `${payload.count || files.length} video(s) renderizado(s) restaurado(s).${exported}`
        : `${payload.count || files.length} video(s) ja pronto(s); render ainda pode estar finalizando.`;
    }
  } catch (error) {
    if (cached.length || !status || status.textContent) return;
    status.textContent = "Nao consegui restaurar a fila renderizada agora.";
  }
}
function renderFinalizeResults(files, options = {}){
  const results = document.querySelector("[data-render-results]");
  if (!results) return;
  const safeFiles = Array.isArray(files) ? files : [];
  if (!safeFiles.length) {
    results.innerHTML = '<div class="effect-empty">Nenhum video renderizado ainda.</div>';
    return;
  }
  if (!options.skipPersist) storeFinalizeResults(safeFiles);
  results.innerHTML = safeFiles.map((file, index) => {
    const camera = normalizeCamera(file.camera);
    const effect = normalizeEffect(file.effect);
    const overlay = normalizeOverlay(file.overlay);
    const bumpers = normalizeBumpers(file.bumpers);
    const bumperText = bumperSummary(bumpers);
    const title = `#${String(file.rank || "").padStart(2, "0")} ${file.label || file.platform || "video"}`;
    const meta = [
      file.width && file.height ? `${file.width}x${file.height}` : "",
      file.final_duration ? fixed(file.final_duration) : file.adjusted_duration ? fixed(file.adjusted_duration) : "",
      cameraHasMovement(camera) ? cameraLabel(camera) : "",
      effect.key !== "none" ? effect.label : "",
      overlay.key !== "none" ? overlay.label : "",
      Object.keys(bumpers).length ? bumperText : ""
    ].filter(Boolean).join(" - ");
    const open = index === 0 ? " open" : "";
    const downloadName = file.download_name || file.url?.split("/").pop() || "cuted-video.mp4";
    const finalFile = file.final_file || file.local_file || "";
    const coverFile = file.final_cover_file || file.local_cover_file || file.cover_file || "";
    const coverFrameUrl = file.cover_frame_url || "";
    const coverFrameFile = file.final_cover_frame_file || file.local_cover_frame_file || file.cover_frame_file || "";
    const coverFrameDownloadName = file.download_cover_frame_name || coverFrameUrl.split("/").pop() || "cuted-tiktok-cover-frame.mp4";
    const finalDir = file.final_dir || "";
    const fileStatus = finalFile ? "Arquivo final exportado" : "Preview temporario";
    return `<details class="result-item"${open}>
      <summary><strong>${escapeHtml(title)}</strong><span>${escapeHtml(meta || "Video finalizado")}</span></summary>
      <div class="result-body">
        <video controls preload="metadata" src="${escapeAttr(file.url)}"></video>
        <div class="result-meta">
          <dl>
            <dt>Status</dt><dd>${escapeHtml(fileStatus)}</dd>
            <dt>Formato</dt><dd>${escapeHtml(file.label || file.platform || "-")}</dd>
            <dt>Duracao</dt><dd>${escapeHtml(file.final_duration ? fixed(file.final_duration) : file.adjusted_duration ? fixed(file.adjusted_duration) : "-")}</dd>
            <dt>Camera</dt><dd>${escapeHtml(cameraLabel(camera))}</dd>
            <dt>Efeito</dt><dd>${escapeHtml(effect.label)}</dd>
            <dt>Chamada</dt><dd>${escapeHtml(overlay.label)}</dd>
            <dt>Vinhetas</dt><dd>${escapeHtml(bumperText)}</dd>
            ${finalFile ? `<dt>Arquivo final</dt><dd><span class="result-path">${escapeHtml(finalFile)}</span></dd>` : ""}
            ${coverFile ? `<dt>Capa final</dt><dd><span class="result-path">${escapeHtml(coverFile)}</span></dd>` : ""}
            ${coverFrameFile ? `<dt>Versao TikTok</dt><dd><span class="result-path">${escapeHtml(coverFrameFile)}</span></dd>` : ""}
            ${finalDir ? `<dt>Pasta final</dt><dd><span class="result-path">${escapeHtml(finalDir)}</span></dd>` : ""}
          </dl>
          <div class="result-actions">
            <a href="${escapeAttr(file.url)}" target="_blank" rel="noopener">Abrir preview</a>
            <a class="secondary" href="${escapeAttr(file.url)}" download="${escapeAttr(downloadName)}">Baixar preview</a>
            ${coverFrameUrl ? `<a class="secondary" href="${escapeAttr(coverFrameUrl)}" target="_blank" rel="noopener">Abrir TikTok</a>` : ""}
            ${coverFrameUrl ? `<a class="secondary" href="${escapeAttr(coverFrameUrl)}" download="${escapeAttr(coverFrameDownloadName)}">Baixar TikTok</a>` : ""}
            ${finalDir ? `<button class="secondary" type="button" data-open-folder="${escapeAttr(finalDir)}">Abrir pasta</button>` : ""}
            ${finalFile ? `<button class="secondary" type="button" data-copy-path="${escapeAttr(finalFile)}">Copiar caminho</button>` : ""}
            ${coverFrameFile ? `<button class="secondary" type="button" data-copy-path="${escapeAttr(coverFrameFile)}">Copiar TikTok</button>` : ""}
          </div>
        </div>
      </div>
    </details>`;
  }).join("");
}
const renderQueueState = {
  profile: localStorage.getItem("cuted-render-profile") || "medium",
  coverFrame: localStorage.getItem("cuted-render-cover-frame") === "1",
  pollId: null,
  activityPollId: null,
  lastFocus: null,
  lastJobs: []
};
function setupRenderQueuePanel(){
  const modal = document.querySelector("[data-render-queue-modal]");
  if (!modal) return;
  document.querySelectorAll("[data-render-profile]").forEach(button => {
    button.classList.toggle("active", button.dataset.renderProfile === renderQueueState.profile);
    button.addEventListener("click", () => setRenderQueueProfile(button.dataset.renderProfile || "medium"));
  });
  document.querySelectorAll("[data-render-cover-frame]").forEach(input => {
    input.checked = renderQueueState.coverFrame;
    input.addEventListener("change", () => setRenderCoverFrameEnabled(input.checked));
  });
  document.querySelector("[data-render-queue-close]")?.addEventListener("click", () => closeRenderQueuePanel());
  modal.addEventListener("click", event => { if (event.target === modal) closeRenderQueuePanel(); });
  document.addEventListener("keydown", event => {
    if (!modal.hidden && event.key === "Escape") closeRenderQueuePanel();
  });
  document.querySelector("[data-render-queue-list]")?.addEventListener("click", event => {
    const target = event.target instanceof Element ? event.target : null;
    const folderButton = target?.closest("[data-open-folder]");
    if (folderButton) openResultFolder(folderButton.dataset.openFolder || "", folderButton);
    const cancelButton = target?.closest("[data-render-cancel]");
    if (cancelButton) cancelRenderQueueJob(cancelButton.dataset.renderCancel || "", cancelButton);
    const removeButton = target?.closest("[data-render-remove]");
    if (removeButton) removeRenderQueueJob(removeButton.dataset.renderRemove || "", removeButton);
  });
  loadRenderQueue();
}
function openRenderQueuePanel(){
  const modal = document.querySelector("[data-render-queue-modal]");
  if (!modal) return;
  renderQueueState.lastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  modal.hidden = false;
  modal.classList.remove("is-closing");
  requestAnimationFrame(() => modal.classList.add("is-open"));
  modal.querySelector("[data-render-queue-panel]")?.focus();
  loadRenderQueue();
  scheduleRenderQueuePoll();
}
function closeRenderQueuePanel(){
  const modal = document.querySelector("[data-render-queue-modal]");
  if (!modal || modal.hidden) return;
  window.clearTimeout(renderQueueState.pollId);
  modal.classList.remove("is-open");
  modal.classList.add("is-closing");
  window.setTimeout(() => {
    modal.hidden = true;
    modal.classList.remove("is-closing");
    renderQueueState.lastFocus?.focus?.();
    renderQueueState.lastFocus = null;
  }, 190);
}
function scheduleRenderQueuePoll(){
  window.clearTimeout(renderQueueState.pollId);
  renderQueueState.pollId = window.setTimeout(async () => {
    const modal = document.querySelector("[data-render-queue-modal]");
    if (!modal || modal.hidden) return;
    await loadRenderQueue();
    scheduleRenderQueuePoll();
  }, 1800);
}
async function loadRenderQueue(){
  const status = document.querySelector("[data-render-queue-status]");
  try {
    const response = await fetch(`/api/render-jobs?gallery_path=${encodeURIComponent(currentGalleryPath())}`, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao carregar fila.");
    renderQueueJobs(payload.jobs || []);
  } catch (error) {
    if (status) status.textContent = error.message || "Nao consegui carregar a fila.";
  }
}
function renderQueueJobs(jobs){
  const list = document.querySelector("[data-render-queue-list]");
  const status = document.querySelector("[data-render-queue-status]");
  const safeJobs = Array.isArray(jobs) ? jobs : [];
  renderQueueState.lastJobs = safeJobs;
  const running = safeJobs.filter(job => job.status === "rendering" || job.status === "queued").length;
  const ready = safeJobs.filter(job => job.status === "ready").length;
  updateHeaderRenderActivity(safeJobs);
  if (status) status.textContent = safeJobs.length ? `${running} em fila; ${ready} pronto(s).` : "Nenhum render em andamento.";
  if (!list) return;
  if (!safeJobs.length) {
    list.innerHTML = '<div class="render-empty">Quando um corte for enviado, ele aparece aqui.</div>';
    return;
  }
  list.innerHTML = safeJobs.map(renderQueueJobHtml).join("");
}
function updateHeaderRenderActivity(jobs){
  const button = document.getElementById("finalize-videos");
  if (!button) return;
  const active = (Array.isArray(jobs) ? jobs : []).some(job => job.status === "rendering" || job.status === "queued");
  button.classList.toggle("is-rendering", active);
  button.setAttribute("aria-label", active ? "Render em andamento" : "Renderizar");
  button.title = active ? "Render em andamento" : "Renderizar";
  scheduleHeaderRenderActivityPoll(active);
}
function scheduleHeaderRenderActivityPoll(active){
  window.clearTimeout(renderQueueState.activityPollId);
  if (!active) return;
  renderQueueState.activityPollId = window.setTimeout(async () => {
    await loadRenderQueue();
  }, 2400);
}
function renderQueueJobHtml(job){
  const summary = job.summary || {};
  const id = String(job.id || "");
  const title = `#${String(summary.rank || "").padStart(2, "0")} ${summary.title || "Render CUTED"}`;
  const eta = Number(job.eta_seconds || 0);
  const meta = [
    summary.platform || "",
    summary.duration ? fixed(summary.duration) : "",
    summary.cover_frame_enabled ? "Capa TikTok" : "",
    renderProfileLabel(job.resource_profile),
    job.speed || "",
    eta > 0 && job.status === "rendering" ? `${formatRenderEta(eta)} restantes` : ""
  ].filter(Boolean).join(" - ");
  const progress = Math.max(0, Math.min(100, Number(job.progress || 0)));
  const folder = job.export_dir || job.output_dir || "";
  const canOpen = job.status === "ready" && folder;
  const canCancel = job.status === "queued" || job.status === "rendering";
  const canRemove = !canCancel;
  return `<article class="render-job-card" data-status="${escapeAttr(job.status || "queued")}">
    <div class="render-job-main">
      <div class="render-job-title"><span class="render-job-pill">${escapeHtml(renderStatusLabel(job.status))}</span><strong>${escapeHtml(title)}</strong></div>
      <div class="render-job-meta">${escapeHtml(job.message || meta || "Render local")}</div>
      <div class="render-job-progress" style="--progress:${progress}%"><span></span></div>
      <div class="render-job-meta">${escapeHtml(`${Math.round(progress)}%${meta ? ` - ${meta}` : ""}`)}</div>
      ${job.error ? `<div class="render-job-meta">${escapeHtml(job.error)}</div>` : ""}
    </div>
    <div class="render-job-actions">
      ${canOpen ? `<button class="primary" type="button" data-open-folder="${escapeAttr(folder)}">Abrir pasta</button>` : `<button type="button" disabled>${escapeHtml(renderStatusLabel(job.status))}</button>`}
      ${canCancel ? `<button type="button" data-render-cancel="${escapeAttr(id)}">Parar</button>` : ""}
      ${canRemove ? `<button type="button" data-render-remove="${escapeAttr(id)}">Remover</button>` : ""}
    </div>
  </article>`;
}
function renderStatusLabel(status){
  const labels = { queued: "Fila", rendering: "Render", ready: "Pronto", failed: "Falha", cancelled: "Cancelado" };
  return labels[status] || "Fila";
}
function renderProfileLabel(profile){
  const labels = { eco: "Eco", medium: "Medio", high: "Alto" };
  return labels[profile] || "Medio";
}
function formatRenderEta(value){
  const seconds = Math.max(0, Math.round(Number(value) || 0));
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return minutes ? `${minutes}m ${String(rest).padStart(2, "0")}s` : `${rest}s`;
}
async function setRenderQueueProfile(profile){
  renderQueueState.profile = profile || "medium";
  localStorage.setItem("cuted-render-profile", renderQueueState.profile);
  document.querySelectorAll("[data-render-profile]").forEach(item => {
    item.classList.toggle("active", item.dataset.renderProfile === renderQueueState.profile);
  });
  const queued = renderQueueState.lastJobs.filter(job => job.status === "queued");
  const rendering = renderQueueState.lastJobs.some(job => job.status === "rendering");
  const status = document.querySelector("[data-render-queue-status]");
  if (!queued.length) {
    if (status && rendering) {
      status.textContent = `${renderProfileLabel(renderQueueState.profile)} salvo para proximos renders. Render atual mantem os threads atuais.`;
    }
    return;
  }
  if (status) status.textContent = `Atualizando ${queued.length} render(es) em fila para ${renderProfileLabel(renderQueueState.profile)}...`;
  try {
    const results = await Promise.all(queued.map(job => updateRenderQueueProfileJob(String(job.id || ""), renderQueueState.profile)));
    const changed = results.filter(item => item.changed).length;
    if (status) status.textContent = changed
      ? `${changed} render(es) em fila atualizados para ${renderProfileLabel(renderQueueState.profile)}.`
      : `${renderProfileLabel(renderQueueState.profile)} salvo para proximos renders.`;
    await loadRenderQueue();
  } catch (error) {
    if (status) status.textContent = error.message || "Nao consegui atualizar o perfil da fila.";
  }
}
function setRenderCoverFrameEnabled(enabled){
  renderQueueState.coverFrame = Boolean(enabled);
  localStorage.setItem("cuted-render-cover-frame", renderQueueState.coverFrame ? "1" : "0");
  document.querySelectorAll("[data-render-cover-frame]").forEach(input => {
    input.checked = renderQueueState.coverFrame;
  });
  const status = document.querySelector("[data-render-queue-status]");
  if (status) {
    status.textContent = renderQueueState.coverFrame
      ? "Capa TikTok ligada para os proximos renders."
      : "Capa TikTok desligada para os proximos renders.";
  }
}
async function updateRenderQueueProfileJob(jobId, profile){
  if (!jobId) return { changed: false };
  const response = await fetch(`/api/render-jobs/${encodeURIComponent(jobId)}/profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ gallery_path: currentGalleryPath(), resource_profile: profile })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || !payload.ok) throw new Error(payload.error || "Nao consegui atualizar o perfil da fila.");
  if (Array.isArray(payload.jobs)) renderQueueState.lastJobs = payload.jobs;
  return payload;
}
function renderQueuePayloadForCard(card){
  const data = buildExportData();
  const rank = String(card.dataset.rank || "");
  const platform = activePlatformForRank(rank);
  const row = (data.caption_queue || []).find(item => String(item.rank) === rank && item.platform === platform);
  if (!row) throw new Error("Este corte ainda nao esta pronto para render.");
  validateActiveRenderRow(card, row, platform);
  return Object.assign({}, data, { caption_queue: [row] });
}
function validateActiveRenderRow(card, row, platform){
  const rank = String(card?.dataset?.rank || "");
  const duration = Number(row.adjusted_duration || cameraTimelineDurationForCard(card));
  const edit = platformEditForRank(rank, platform);
  const expectedPreset = resolutionPresetForPlatform(platform);
  const values = trimValues(card);
  const expectedPath = exportCameraPathForEdit(edit, values.duration, values.trimStart, duration);
  const actualPath = normalizeCameraPath(row.camera_path);
  if (row.resolution_preset !== expectedPreset) {
    throw new Error("O render nao bate com o formato ativo. Reabra o corte e tente de novo.");
  }
  if (JSON.stringify(actualPath) !== JSON.stringify(expectedPath)) {
    throw new Error("A camera ativa mudou antes do envio. Reabra o corte e tente de novo.");
  }
}
async function sendCardToRenderQueue(card){
  const status = card?.__cutedControlSurface;
  if (!card || card.dataset.renderSubmitting === "1") return;
  card.dataset.renderSubmitting = "1";
  try {
    const queue = renderQueuePayloadForCard(card);
    const response = await fetch("/api/render-jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        queue,
        chars_per_line: captionWidth(),
        max_lines: captionLines(),
        captions_enabled: queue.caption_queue.some(item => item.captions_enabled !== false),
        gallery_path: currentGalleryPath(),
        cover_frame_enabled: renderCoverFrameEnabled(),
        resource_profile: renderQueueState.profile
      })
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao enviar para render.");
    if (payload.duplicate) {
      cancelControlSurfaceReady(card);
      card?.__cutedControlSurface?.update?.({ renderQueued: false });
      card?.__cutedControlSurface?.setStatus?.({ kind: "ready", label: "Ja esta renderizando", tone: "green" }, 2600);
      await loadRenderQueue();
      return;
    }
    cancelControlSurfaceReady(card);
    card?.__cutedControlSurface?.update?.({ renderQueued: false });
    card?.__cutedControlSurface?.setStatus?.({ kind: "ready", label: "SENT TO RENDER", tone: "green" }, 1800);
    await loadRenderQueue();
  } catch (error) {
    updateControlSurfaceForCard(card);
    card?.__cutedControlSurface?.update?.({ renderQueued: false });
    status?.setStatus?.({ kind: "error", label: error.message || "Render falhou", tone: "red" }, 2200);
    showAppNotice(error.message || "Nao consegui enviar para render.");
  } finally {
    delete card.dataset.renderSubmitting;
  }
}
async function cancelRenderQueueJob(jobId, button){
  if (!jobId) return;
  await updateRenderQueueJob(`/api/render-jobs/${encodeURIComponent(jobId)}/cancel`, button, "Parando...");
}
async function removeRenderQueueJob(jobId, button){
  if (!jobId) return;
  await updateRenderQueueJob(`/api/render-jobs/${encodeURIComponent(jobId)}/remove`, button, "Removendo...");
}
async function updateRenderQueueJob(url, button, label){
  const previous = button?.textContent || "";
  try {
    if (button) {
      button.disabled = true;
      button.textContent = label;
    }
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gallery_path: currentGalleryPath() })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Nao consegui atualizar a fila.");
    if (Array.isArray(payload.jobs)) renderQueueJobs(payload.jobs);
    else await loadRenderQueue();
  } catch (error) {
    if (button) {
      button.disabled = false;
      button.textContent = previous;
    }
    showAppNotice(error.message || "Nao consegui atualizar a fila.");
  }
}
async function openResultFolder(path, button){
  if (!path) return;
  const previous = button?.textContent || "Abrir pasta";
  try {
    if (button) {
      button.disabled = true;
      button.textContent = "Abrindo...";
    }
    const response = await fetch("/api/open-folder", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({path})
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao abrir pasta.");
    if (button) button.textContent = "Pasta aberta";
  } catch (error) {
    if (button) button.textContent = "Falhou";
    alert(error.message || String(error));
  } finally {
    window.setTimeout(() => {
      if (!button) return;
      button.disabled = false;
      button.textContent = previous;
    }, 1400);
  }
}
async function copyResultPath(path, button){
  try {
    await navigator.clipboard.writeText(path);
    if (button) button.textContent = "Copiado";
  } catch (error) {
    copyTextFallback(path);
    if (button) button.textContent = "Copiado";
  }
}
function copyTextFallback(text){
  const input = document.createElement("textarea");
  input.value = text;
  input.setAttribute("readonly", "");
  input.style.position = "fixed";
  input.style.opacity = "0";
  document.body.appendChild(input);
  input.select();
  document.execCommand("copy");
  input.remove();
}
function clearNewProjectState(){
  Object.keys(state).forEach(key => { delete state[key]; });
  localStorage.removeItem(editorStateStorageKey);
  localStorage.removeItem(editorTabStorageKey);
  localStorage.removeItem("cutted-state");
  localStorage.removeItem("cutted-tab");
  localStorage.removeItem("cutted-caption-lines");
  localStorage.removeItem("cutted-caption-width");
  localStorage.removeItem("cutted-caption-size");
  localStorage.removeItem("cutted-caption-bottom");
  localStorage.removeItem("cutted-caption-mode");
  localStorage.removeItem("cutted-caption-text-color");
  localStorage.removeItem("cutted-caption-background-color");
  localStorage.removeItem("cutted-caption-highlight-background-color");
  localStorage.removeItem("cutted-caption-enabled");
}
function resetCardPanels(card){
  card.querySelectorAll("[data-panel]").forEach(panel => {
    if (panel instanceof HTMLDetailsElement) panel.open = panel.dataset.panel === "cut";
  });
}
function resetCardsForNewProject(){
  document.querySelectorAll(".card").forEach(card => {
    delete card.dataset.selectedOverlayLayer;
    card.dataset.previewFormat = "tiktok";
    setCardState(card.dataset.rank, { cameraMotionMs: defaultCameraMotionMs });
    applyCameraMotionSpeed(card);
    setCardPreviewFormat(card, "tiktok");
    resetCardPanels(card);
    paint(card);
    updateTrimUi(card);
    updatePlatformUi(card);
    updateCardTools(card);
    const menu = card.querySelector("[data-overlay-menu]");
    if (menu) {
      menu.hidden = true;
      menu.innerHTML = "";
    }
  });
}
let workspaceExitLastFocus = null;
function workspaceExitFocusableElements(modal){
  return Array.from(modal.querySelectorAll("button,input,select,textarea,a[href],[tabindex]:not([tabindex='-1'])"))
    .filter(element => !element.disabled && !element.hidden && element.offsetParent !== null);
}
function setupWorkspaceExitModal(){
  const modal = document.querySelector("[data-workspace-exit-modal]");
  if (!modal) return;
  modal.querySelectorAll("[data-workspace-exit-cancel]").forEach(button => {
    button.addEventListener("click", () => closeWorkspaceExitModal());
  });
  modal.querySelector("[data-workspace-exit-confirm]")?.addEventListener("click", () => confirmWorkspaceExit());
  modal.addEventListener("click", event => { if (event.target === modal) closeWorkspaceExitModal(); });
  document.addEventListener("keydown", event => {
    if (modal.hidden) return;
    if (event.key === "Escape") closeWorkspaceExitModal();
    if (event.key === "Tab") trapWorkspaceExitFocus(event);
  });
}
function openWorkspaceExitModal(){
  const modal = document.querySelector("[data-workspace-exit-modal]");
  if (!modal) return;
  workspaceExitLastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  modal.hidden = false;
  modal.classList.remove("is-closing");
  requestAnimationFrame(() => modal.classList.add("is-open"));
  modal.querySelector("[data-workspace-exit-panel]")?.focus();
}
function closeWorkspaceExitModal(){
  const modal = document.querySelector("[data-workspace-exit-modal]");
  if (!modal || modal.hidden) return;
  modal.classList.remove("is-open");
  modal.classList.add("is-closing");
  window.setTimeout(() => {
    modal.hidden = true;
    modal.classList.remove("is-closing");
    workspaceExitLastFocus?.focus?.();
    workspaceExitLastFocus = null;
  }, 190);
}
function trapWorkspaceExitFocus(event){
  const modal = document.querySelector("[data-workspace-exit-modal]");
  if (!modal || modal.hidden) return;
  const focusable = workspaceExitFocusableElements(modal);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
async function confirmWorkspaceExit(){
  save();
  const button = document.querySelector("[data-workspace-exit-confirm]");
  if (button) {
    button.disabled = true;
    button.textContent = "Voltando...";
  }
  try {
    await touchCurrentProject();
  } catch (error) {
    console.warn("CUTED project was not added to recents", error);
  } finally {
    window.location.assign("/index.html");
  }
}
function startNewProject(){
  openWorkspaceExitModal();
}
function finalizeErrorMessage(error){
  const script = window.CUTTED_SCRIPT || "cutted.py";
  const serveCommand = `python "${script}" serve --dir "." --port 8778`;
  return `Nao consegui finalizar pelo navegador atual. Abra a galeria com: ${serveCommand}`;
}
function captionItemHtml(item){
  const previewSrc = cacheBustedPreview(item.clip_file || "", `${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  return `
    <article class="caption-item" data-platform="${escapeAttr(item.platform)}">
      <div class="caption-preview"><video controls preload="metadata" src="${escapeAttr(previewSrc)}"></video></div>
      <div class="caption-item-body">
        <strong>#${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
        <span>${escapeHtml(item.platform_label)}</span><span>${item.width}x${item.height}</span><span>${fixed(item.adjusted_duration)}</span>
        <p>${escapeHtml((item.publish_metadata?.hashtags || []).join(" "))}</p>
        <dl><dt>Inicio</dt><dd>${fixed(item.adjusted_start)}</dd><dt>Fim</dt><dd>${fixed(item.adjusted_end)}</dd></dl>
      </div>
    </article>`;
}
function cacheBustedPreview(value, token){
  if (!value) return "";
  return `${value}${String(value).includes("?") ? "&" : "?"}v=${encodeURIComponent(token)}`;
}
function escapeHtml(value){
  return String(value).replace(/[&<>"']/g, char => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[char]));
}
function escapeAttr(value){ return escapeHtml(value); }
syncProjectEmptyState();
applyTab("edit");
syncCaptionInputs();
document.querySelectorAll(".tabs [data-tab]").forEach(btn => {
  btn.addEventListener("click", () => { applyTab(btn.dataset.tab); renderCaptionQueue(); });
});
setupSettingsPanel();
setupRenderQueuePanel();
setupWorkspaceExitModal();
touchCurrentProject().catch(error => console.warn("CUTED project was not added to recents", error));
setupImportPathButtons();
setupImportKeyBanner();
document.querySelector("[data-empty-import]")?.addEventListener("click", () => applyTab("import"));
document.querySelector("[data-import-form]")?.addEventListener("submit", event => {
  event.preventDefault();
  startImportJob(event.currentTarget);
});
document.querySelectorAll(".card").forEach(card => {
  paint(card);
  updateTrimUi(card);
  updatePlatformUi(card);
  updateCardTools(card);
  applyCameraMotionSpeed(card);
  refreshAiReadinessForCard(card);
  const summary = card.querySelector(".clip-summary");
  if (summary) {
    const isSummaryTimelineTarget = target => target instanceof Element && !target.closest(".cuted-clip-info") && Boolean(target.closest("[data-cuted-control-surface], .cuted-control-bar, .cuted-menu, .cuted-volume-popover, [data-preview-camera-timeline], .timeline-shell, .timeline-canvas, .playhead-control, .trim-handle, .volume-popover, .preview-camera-popover"));
    const stopSummaryTimelinePointer = event => {
      if (!isSummaryTimelineTarget(event.target)) return;
      event.stopPropagation();
    };
    const toggleCard = event => {
      if (isSummaryTimelineTarget(event.target)) {
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      event.preventDefault();
      card.open = !card.open;
      activateCard(card);
    };
    summary.addEventListener("pointerdown", stopSummaryTimelinePointer);
    summary.addEventListener("mousedown", stopSummaryTimelinePointer);
    summary.addEventListener("touchstart", stopSummaryTimelinePointer, { passive: true });
    summary.addEventListener("click", toggleCard);
    summary.addEventListener("keydown", event => {
      if (event.key !== "Enter" && event.key !== " ") return;
      toggleCard(event);
    });
  }
  card.querySelectorAll("[data-card-format-preview]").forEach(button => {
    button.addEventListener("click", () => {
      card.dataset.previewTouched = "1";
      setPreviewPlayback(card, false);
      setCardPreviewFormat(card, button.dataset.cardFormatPreview);
      closePreviewFormatMenus();
      updateCardTools(card);
      renderFinalStage();
    });
  });
  const previewFormatTrigger = card.querySelector("[data-preview-format-trigger]");
  if (previewFormatTrigger) {
    previewFormatTrigger.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      togglePreviewFormatMenu(card);
    });
  }
  bindPreviewFormatDismiss();
  const playButton = card.querySelector("[data-preview-play]");
  if (playButton) {
    playButton.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      togglePreviewPlayback(card);
    });
  }
  const volumeButton = card.querySelector("[data-preview-volume]");
  if (volumeButton) {
    volumeButton.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      togglePreviewVolumePopover(card);
    });
  }
  const volumeSlider = card.querySelector("[data-preview-volume-slider]");
  if (volumeSlider) {
    volumeSlider.addEventListener("input", event => {
      event.stopPropagation();
      setPreviewVolume(card, Number(event.target.value || 0) / 100);
    });
  }
  const motionSlider = card.querySelector("[data-camera-motion-speed]");
  if (motionSlider) {
    motionSlider.addEventListener("input", event => {
      event.stopPropagation();
      setCameraMotionSpeed(card, event.target.value);
    });
  }
  const aiButton = card.querySelector("[data-camera-ai]");
  if (aiButton) {
    aiButton.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      analyzeCameraForCard(card, "ai-director");
    });
    refreshAiReadinessForCard(card);
  }
  bindPreviewVolumeDismiss();
  const video = primaryCameraVideo(card);
  if (video) {
    applyPreviewVolume(video);
    video.addEventListener("play", () => {
      const values = trimValues(card);
      const nextTime = trimPlaybackStart(values, video.currentTime);
      card.dataset.playbackMode = "range";
      delete card.dataset.timelineSeekIntent;
      if (Math.abs(video.currentTime - nextTime) > .05) video.currentTime = nextTime;
      startCameraFrameSync(video, () => syncPreviewPlaybackFrame(card));
      syncCameraFitBackground(card);
      syncPreviewPlaybackState(card);
    });
    video.addEventListener("pause", () => {
      stopCameraFrameSync(video, () => syncPreviewPlaybackFrame(card));
      syncCameraFitBackground(card);
      syncPreviewPlaybackState(card);
    });
    video.addEventListener("ended", () => {
      stopCameraFrameSync(video, () => syncPreviewPlaybackFrame(card));
      syncCameraFitBackground(card);
      syncPreviewPlaybackState(card);
    });
    video.addEventListener("volumechange", () => {
      syncPreviewVolumeButton(card);
    });
    ["loadedmetadata", "loadeddata", "canplay", "durationchange"].forEach(eventName => {
      video.addEventListener(eventName, () => {
        if (!applyPendingTimelineSeek(card, video)) updateTimelinePlayhead(card);
      });
    });
    video.addEventListener("timeupdate", () => {
      const values = trimValues(card);
      updateTimelinePlayhead(card);
      syncCameraFitBackground(card);
      if (trimRangeActive(values) && video.currentTime >= values.duration - values.trimEnd) {
        pauseAtTrimEnd(card, video, values);
      }
    });
  }
  syncPreviewPlaybackState(card);
  syncPreviewVolumeButton(card);
  bindPublishPanel(card);
  card.querySelectorAll("[data-trim]").forEach(input => input.addEventListener("input", () => {
    const current = cardState(card.dataset.rank);
    const duration = Number(card.dataset.duration);
    const startInput = card.querySelector("[data-trim=start]");
    const endInput = card.querySelector("[data-trim=end]");
    let startPos = Number(startInput.value);
    let endPos = Number(endInput.value);
    if (input.dataset.trim === "start") startPos = Math.min(startPos, endPos - 1);
    if (input.dataset.trim === "end") endPos = Math.max(endPos, startPos + 1);
    const patch = { trimStart: Math.max(startPos, 0), trimEnd: Math.max(duration - endPos, 0) };
    setCardState(card.dataset.rank, Object.assign(current, patch));
    updateTrimUi(card);
    seekTrimHandle(card, input.dataset.trim);
    renderCaptionQueue();
  }));
  const scrubInput = card.querySelector("[data-trim-scrub]");
  if (scrubInput) {
    scrubInput.addEventListener("input", () => {
      setPreviewPlayback(card, false);
      const duration = Number(card.dataset.duration);
      const current = clampNumber(Number(scrubInput.value), 0, Math.max(duration, .1));
      seekTimeline(card, current, { userInitiated: true, mode: "free" });
    });
  }
  card.querySelectorAll("[data-platform]").forEach(btn => btn.addEventListener("click", () => {
    const current = cardState(card.dataset.rank);
    const platforms = Array.isArray(current.platforms) ? current.platforms.slice() : [];
    const target = representativePlatform(btn.dataset.platform);
    const normalized = uniquePlatforms(platforms);
    const existing = normalized.indexOf(target);
    if (existing >= 0) normalized.splice(existing, 1);
    else normalized.push(target);
    setCardState(card.dataset.rank, { platforms: normalized, status: current.status === "discarded" ? null : current.status });
    paint(card);
    updatePlatformUi(card);
    renderCaptionQueue();
  }));
  card.querySelectorAll("button[data-action]").forEach(btn => btn.addEventListener("click", () => {
    const patch = btn.dataset.action === "like" ? { status: "liked" } : { status: "discarded", platforms: [] };
    setCardState(card.dataset.rank, patch);
    paint(card);
    updatePlatformUi(card);
    renderCaptionQueue();
  }));
  if (card.open) activateCard(card);
});
document.getElementById("reset-ui").addEventListener("click", startNewProject);
document.getElementById("finalize-videos").addEventListener("click", () => {
  openRenderQueuePanel();
});
document.querySelector("[data-render-results]")?.addEventListener("click", event => {
  const target = event.target instanceof Element ? event.target : null;
  const folderButton = target?.closest("[data-open-folder]");
  if (folderButton) {
    openResultFolder(folderButton.dataset.openFolder || "", folderButton);
    return;
  }
  const copyButton = target?.closest("[data-copy-path]");
  if (!copyButton) return;
  copyResultPath(copyButton.dataset.copyPath || "", copyButton);
});
document.querySelectorAll("[data-caption-lines],[data-caption-width],[data-caption-size],[data-caption-bottom],[data-caption-text-color],[data-caption-background-color],[data-caption-highlight-background-color],[data-caption-enabled]").forEach(input => {
  const update = () => {
    if (input.matches("[data-caption-lines]")) localStorage.setItem("cutted-caption-lines", input.value);
    if (input.matches("[data-caption-width]")) localStorage.setItem("cutted-caption-width", input.value);
    if (input.matches("[data-caption-size]")) localStorage.setItem("cutted-caption-size", input.value);
    if (input.matches("[data-caption-bottom]")) localStorage.setItem("cutted-caption-bottom", input.value);
    if (input.matches("[data-caption-text-color]")) localStorage.setItem("cutted-caption-text-color", normalizeCaptionColor(input.value, "#ffffff"));
    if (input.matches("[data-caption-background-color]")) localStorage.setItem("cutted-caption-background-color", normalizeCaptionBackground(input.value));
    if (input.matches("[data-caption-highlight-background-color]")) localStorage.setItem("cutted-caption-highlight-background-color", normalizeCaptionHighlightBackground(input.value));
    if (input.matches("[data-caption-enabled]")) {
      localStorage.setItem("cutted-caption-enabled", input.checked ? "1" : "0");
      localStorage.setItem("cutted-caption-mode", input.checked ? "on" : "off");
    }
    syncCaptionInputs();
    syncPreviewCaptionsForOpenCards();
    renderFinalStage();
  };
  input.addEventListener("input", update);
  input.addEventListener("change", update);
});
function selectElementText(element){
  if (!element || !window.getSelection || !document.createRange) return;
  const range = document.createRange();
  range.selectNodeContents(element);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
}
renderCaptionQueue();
"""
