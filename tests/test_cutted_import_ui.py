from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "cutted" / "scripts" / "cutted.py"
SPEC = importlib.util.spec_from_file_location("cutted_import_ui_test_module", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load cutted.py for import UI tests.")
CUTTED = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CUTTED
SPEC.loader.exec_module(CUTTED)

LAUNCHER_PATH = Path(__file__).resolve().parents[1] / "packaging" / "cuted_launcher.py"
LAUNCHER_SPEC = importlib.util.spec_from_file_location("cuted_launcher_test_module", LAUNCHER_PATH)
if LAUNCHER_SPEC is None or LAUNCHER_SPEC.loader is None:
    raise RuntimeError("Unable to load cuted_launcher.py for launcher tests.")
LAUNCHER = importlib.util.module_from_spec(LAUNCHER_SPEC)
sys.modules[LAUNCHER_SPEC.name] = LAUNCHER
LAUNCHER_SPEC.loader.exec_module(LAUNCHER)


def gallery_html() -> str:
    return CUTTED.page_html("Teste", "", "{}", "assets/brand/cuted-logo-transparent.png")


class CuttedImportUiTests(unittest.TestCase):
    def test_import_form_has_no_desktop_button(self) -> None:
        html = gallery_html()

        self.assertNotIn("data-use-desktop", html)
        self.assertIn("data-select-folder", html)

    def test_import_output_path_starts_empty_with_placeholder(self) -> None:
        html = gallery_html()

        self.assertIn('name="output_path" type="text" value=""', html)
        self.assertIn('placeholder="Selecione a pasta dos videos finais"', html)

    def test_import_form_has_openai_key_banner(self) -> None:
        html = gallery_html()

        self.assertIn("data-import-key-banner", html)
        self.assertIn("data-import-key-open", html)
        self.assertIn("Adicione sua chave OpenAI aqui para importar com IA.", html)
        self.assertIn("importNeedsOpenaiKey", html)
        self.assertIn("Escolha a pasta onde os videos finais serao salvos.", html)

    def test_import_form_prioritizes_local_video(self) -> None:
        html = gallery_html()

        self.assertIn('name="source_path" type="text"', html)
        self.assertIn("data-select-video-file", html)
        self.assertIn("Fluxo principal", html)
        self.assertIn("Link do YouTube (experimental)", html)
        self.assertNotIn("youtube_cookies_from_browser", html)
        self.assertNotIn("youtube_cookies_file", html)

    def test_import_payload_excludes_youtube_cookie_fields(self) -> None:
        html = gallery_html()

        self.assertIn('source_path: String(data.get("source_path")', html)
        self.assertNotIn("youtube_cookies_from_browser", html)
        self.assertNotIn("youtube_cookies_file", html)

    def test_import_ready_auto_opens_project(self) -> None:
        html = gallery_html()

        self.assertIn("window.location.assign(job.output_url)", html)

    def test_render_results_are_restored_from_gallery(self) -> None:
        html = gallery_html()

        self.assertIn("/api/finalize-results", html)
        self.assertIn("finalizeStorageKey", html)
        self.assertIn("restoreFinalizeResults", html)
        self.assertIn('if (next === "final") restoreFinalizeResults();', html)

    def test_render_queue_modal_and_controls_are_available(self) -> None:
        html = gallery_html()
        script = (Path(__file__).resolve().parents[1] / "tools" / "cutted" / "assets" / "control-bar" / "control-bar.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("data-render-queue-modal", html)
        self.assertIn('data-render-profile="eco"', html)
        self.assertIn('data-render-profile="medium"', html)
        self.assertIn('data-render-profile="high"', html)
        self.assertIn("/api/render-jobs", html)
        self.assertIn("openRenderQueuePanel", html)
        self.assertIn("sendCardToRenderQueue", html)
        self.assertIn("data-render-cancel", html)
        self.assertIn("data-render-remove", html)
        self.assertIn("/api/render-jobs/${encodeURIComponent(jobId)}/remove", html)
        self.assertIn("SEND TO RENDER", script)
        self.assertIn("elements.statusAction.addEventListener(\"click\"", script)
        self.assertIn("state.renderQueued", script)
        self.assertIn("data-cuted-status-action", script)
        self.assertNotIn('data-cuted-control="send-render"', script)
        self.assertNotIn("openRenderQueuePanel();\n    await loadRenderQueue();", html)

    def test_render_resource_profiles_apply_threads_and_priority(self) -> None:
        rows = [{"rank": 1}, {"rank": 2}]

        CUTTED.apply_render_resource_to_rows(rows, "eco")
        self.assertEqual(rows[0]["_render_threads"], 1)
        self.assertEqual(rows[0]["_render_priority"], "idle")
        self.assertIn("-threads", CUTTED.ffmpeg_codec_thread_args(rows[0]))

        rows = [{"rank": 1}]
        CUTTED.apply_render_resource_to_rows(rows, "high")
        self.assertGreaterEqual(rows[0]["_render_threads"], 1)
        self.assertEqual(rows[0]["_render_priority"], "below_normal")

    def test_render_jobs_support_cancel_remove_and_process_cancel(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertIn('"/api/render-jobs/[^/]+/remove"', source)
        self.assertIn("def remove_render_job(job_id: str, gallery_dir: Path)", source)
        self.assertIn("def render_job_cancelled(job_id: object)", source)
        self.assertIn("process = subprocess.Popen(", source)
        self.assertIn("process.terminate()", source)
        self.assertIn('raise RuntimeError("Render cancelado.")', source)

    def test_partial_captioned_files_are_recovered_before_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gallery_dir = Path(tmp)
            out_dir = gallery_dir / "captioned-clips"
            out_dir.mkdir()
            (out_dir / "clip-002-tiktok-captioned.mp4").write_bytes(b"video")
            (out_dir / "clip-003-tiktok-captioned.mp4").write_bytes(b"")
            (gallery_dir / "caption-queue.json").write_text(
                json.dumps({
                    "caption_queue": [{
                        "rank": 2,
                        "platform": "tiktok",
                        "platform_label": "Vertical 9:16",
                        "adjusted_duration": 91.2,
                    }]
                }),
                encoding="utf-8",
            )

            result = CUTTED.finalized_results_from_gallery(gallery_dir)

            self.assertFalse(result["ready"])
            self.assertTrue(result["partial"])
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["files"][0]["url"], "captioned-clips/clip-002-tiktok-captioned.mp4")
            self.assertEqual(result["files"][0]["adjusted_duration"], 91.2)

    def test_camera_analysis_fetch_has_timeout(self) -> None:
        html = gallery_html()

        self.assertIn("const cameraAnalysisFetchTimeoutMs = 180000", html)
        self.assertIn("const cameraReadinessPollMs = 3500", html)
        self.assertIn("new AbortController()", html)
        self.assertIn("IA ainda esta aplicando", html)

    def test_ai_button_waits_for_map_and_uses_applying_copy(self) -> None:
        html = gallery_html()

        self.assertIn("/api/camera/status", html)
        self.assertIn("refreshAiReadinessForCard(card)", html)
        self.assertIn("Mapeando video...", html)
        self.assertIn("Aplicando ${smartCameraModes[smartMode].label}...", html)
        self.assertNotIn("Dirigindo", html)

    def test_preview_has_camera_motion_speed_slider(self) -> None:
        html = gallery_html()

        self.assertIn("data-camera-motion-speed", html)
        self.assertIn("defaultCameraMotionMs = 700", html)
        self.assertIn("--camera-transition-ms", html)
        self.assertIn("setCameraMotionSpeed(card", html)

    def test_page_can_inject_live_timeline_assets(self) -> None:
        html = CUTTED.page_html(
            "Teste",
            "",
            "{}",
            "assets/brand/cuted-logo-transparent.png",
            {"css": "assets/live-timeline/live-timeline.css", "js": "assets/live-timeline/live-timeline.js"},
        )

        self.assertIn('href="assets/live-timeline/live-timeline.css"', html)
        self.assertIn('src="assets/live-timeline/live-timeline.js"', html)
        self.assertLess(html.index("live-timeline.css"), html.index("<style>"))
        self.assertLess(html.index("live-timeline.js"), html.index("window.CUTTED_DATA"))

    def test_page_can_inject_control_bar_assets(self) -> None:
        html = CUTTED.page_html(
            "Teste",
            "",
            "{}",
            "assets/brand/cuted-logo-transparent.png",
            {},
            {"css": "assets/control-bar/control-bar.css", "js": "assets/control-bar/control-bar.js"},
        )

        self.assertIn('href="assets/control-bar/control-bar.css"', html)
        self.assertIn('src="assets/control-bar/control-bar.js"', html)
        self.assertLess(html.index("control-bar.css"), html.index("<style>"))
        self.assertLess(html.index("control-bar.js"), html.index("window.CUTTED_DATA"))

    def test_live_timeline_assets_are_copied_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            assets = CUTTED.write_live_timeline_assets(Path(tmp))

            self.assertRegex(assets["css"], r"^assets/live-timeline/live-timeline\.css\?v=[0-9a-f]{10}$")
            self.assertRegex(assets["js"], r"^assets/live-timeline/live-timeline\.js\?v=[0-9a-f]{10}$")
            self.assertTrue((Path(tmp) / "assets" / "live-timeline" / "live-timeline.css").exists())
            self.assertTrue((Path(tmp) / "assets" / "live-timeline" / "live-timeline.js").exists())

    def test_control_bar_assets_are_copied_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            assets = CUTTED.write_control_bar_assets(Path(tmp))

            self.assertRegex(assets["css"], r"^assets/control-bar/control-bar\.css\?v=[0-9a-f]{10}$")
            self.assertRegex(assets["js"], r"^assets/control-bar/control-bar\.js\?v=[0-9a-f]{10}$")
            self.assertTrue((Path(tmp) / "assets" / "control-bar" / "control-bar.css").exists())
            self.assertTrue((Path(tmp) / "assets" / "control-bar" / "control-bar.js").exists())

    def test_control_bar_asset_preserves_discard_contract(self) -> None:
        asset_dir = Path(__file__).resolve().parents[1] / "tools" / "cutted" / "assets" / "control-bar"
        script = (asset_dir / "control-bar.js").read_text(encoding="utf-8")
        styles = (asset_dir / "control-bar.css").read_text(encoding="utf-8")

        self.assertIn("setDiscarded(discarded = true)", script)
        self.assertIn("subscribe(listener)", script)
        self.assertIn('CustomEvent("cuted-control-bar:statechange"', script)
        self.assertIn("CUT DISCARDED", script)
        self.assertIn("settings.mockBumpers", script)
        self.assertIn(".cuted-control-bar.is-discarded", styles)
        self.assertIn(".cuted-render-zone.is-locked", styles)

    def test_control_surface_uses_app_state_for_discarded(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertIn('discarded: current.status === "discarded"', source)
        self.assertIn('current.status === "discarded"', source)
        self.assertIn('label: "CUT DISCARDED"', source)
        self.assertIn("mockBumpers: false", source)

    def test_control_surface_does_not_persist_effect_feedback(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        script = (Path(__file__).resolve().parents[1] / "tools" / "cutted" / "assets" / "control-bar" / "control-bar.js").read_text(
            encoding="utf-8"
        )

        self.assertNotIn('kind: "effect", label: `Effect preview: ${effect.label}`', source)
        self.assertIn("keepLocalStatus", script)
        self.assertIn("!state.status.persistent && statusClock.id", script)
        self.assertIn('statusMeter.style.setProperty("--status-progress", "0%")', script)
        self.assertNotIn("statusProgress", script)

    def test_control_surface_ready_cancel_restores_discarded(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertIn('if (current.status === "discarded")', source)
        self.assertIn('setCardState(card.dataset.rank, { status: null, platforms: [] })', source)
        self.assertIn("renderFinalStage();", source)

    def test_control_surface_locks_during_mapping_and_ai_apply(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        asset_dir = Path(__file__).resolve().parents[1] / "tools" / "cutted" / "assets" / "control-bar"
        script = (asset_dir / "control-bar.js").read_text(encoding="utf-8")
        styles = (asset_dir / "control-bar.css").read_text(encoding="utf-8")

        self.assertIn("const busy = controlSurfaceBusy(card)", source)
        self.assertIn("busy,", source)
        self.assertIn("refreshAiReadinessForCard(card);", source)
        self.assertIn('if (card.dataset.aiApplying === "1") return;', source)
        self.assertNotIn('if (!button || card.dataset.aiApplying === "1") return;', source)
        self.assertIn("updateControlSurfaceForCard(card);", source)
        self.assertIn('label: "Projeto sendo mapeado..."', source)
        self.assertIn('label: "IA ajustando keyframes..."', source)
        self.assertIn("state.ready || state.discarded || state.busy", script)
        self.assertIn("dataset.ready = String(state.ready || state.discarded)", script)
        self.assertIn('classList.toggle("is-busy"', script)
        self.assertIn(".cuted-control-bar.is-busy .cuted-audio-group", styles)

    def test_control_surface_timeline_click_does_not_toggle_card(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertIn("const isSummaryTimelineTarget", source)
        self.assertIn('!target.closest(".cuted-clip-info")', source)
        self.assertIn("[data-preview-camera-timeline], .timeline-shell", source)
        self.assertIn('summary.addEventListener("pointerdown", stopSummaryTimelinePointer)', source)
        self.assertIn('summary.addEventListener("touchstart", stopSummaryTimelinePointer, { passive: true })', source)

    def test_control_surface_card_layout_is_compact_and_centered(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        styles = (Path(__file__).resolve().parents[1] / "tools" / "cutted" / "assets" / "control-bar" / "control-bar.css").read_text(
            encoding="utf-8"
        )

        self.assertIn("clipInfo: controlSurfaceClipInfo(card)", source)
        self.assertIn("body{position:relative;background:linear-gradient(180deg,#050505 0%,#070907 58%,#050505 100%)", source)
        self.assertIn("body::before{position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(circle at 16% 8%,rgba(17,162,207,.22)", source)
        self.assertIn("animation:cuted-edit-bg-breathe 22s ease-in-out infinite", source)
        self.assertIn("@keyframes cuted-edit-bg-breathe{0%,100%{opacity:.5}50%{opacity:.82}}", source)
        self.assertIn("header,main,.empty-project-stage,.settings-backdrop,.app-notice{position:relative;z-index:1}", source)
        self.assertIn("header{padding:18px 26px 2px!important;background:transparent!important;border-bottom:0!important", source)
        self.assertIn(".brand-logo{width:min(672px,62vw);height:101px;transform:translateY(4px)", source)
        self.assertIn(".brand-logo{transform:translateY(-6px)", source)
        self.assertIn(".brand-lockup p{display:none!important}", source)
        self.assertIn("main{padding-top:0}", source)
        self.assertIn(".clip-control-surface .cuted-control-bar{width:100%;max-width:none", source)
        self.assertIn(".clip-row-timeline,.clip-row-timeline.preview-camera-timeline{display:none!important}", source)
        self.assertIn(".card[open] .clip-row-timeline,.card[open] .clip-row-timeline.preview-camera-timeline{display:block!important", source)
        self.assertIn(".card,.card[open]{border:0!important;background:transparent!important", source)
        self.assertIn(".clip-summary,.card[open] .clip-summary{grid-template-columns:1fr;align-items:stretch;gap:0;min-height:0;padding:0", source)
        self.assertIn(".clip-control-surface .cuted-render-zone{flex:1 1 auto", source)
        self.assertIn(".clip-control-surface .cuted-clip-info{flex:0 1 30%;max-width:30%", source)
        self.assertIn(".card[open] .clip-row-timeline.preview-camera-timeline--live{width:100%;margin:-12px 0 0", source)
        self.assertIn(".editor-shell{display:grid;grid-template-columns:1fr;padding:0 0 16px;margin-top:-18px", source)
        self.assertIn(".editor-preview{gap:0}.preview-frame{gap:0}", source)
        self.assertIn(".clip-control-surface .cuted-render-zone{justify-content:flex-end;padding-left:clamp(96px,12vw,190px);gap:14px", source)
        self.assertIn(".clip-control-surface .cuted-ready-region{flex:0 0 116px;width:116px;min-height:54px;margin-left:14px", source)
        self.assertIn(".clip-control-surface .cuted-tool-buttons{justify-content:flex-end}", source)
        self.assertIn(".clip-control-surface .cuted-format-trigger{flex:0 0 132px;width:132px;height:58px", source)
        self.assertIn(".clip-control-surface .cuted-format-copy small{display:block;font-size:10px", source)
        self.assertIn(".clip-control-surface{position:relative;z-index:2600}", source)
        self.assertIn(".clip-control-surface .cuted-effect-menu,.clip-control-surface .cuted-insert-menu,.clip-control-surface .cuted-format-menu,.clip-control-surface .cuted-volume-popover{z-index:3200}", source)
        self.assertIn(".cuted-effect-menu {\n  position: absolute;\n  right: 206px;\n  top: calc(100% + 12px);", styles)
        self.assertIn(".cuted-insert-menu {\n  position: absolute;\n  right: 176px;\n  top: calc(100% + 12px);", styles)
        self.assertNotIn("bottom: 106px", styles)
        self.assertNotIn("bottom: 146px", styles)
        self.assertIn(".cuted-effect-menu::after", styles)
        self.assertIn("top: -17px", styles)
        self.assertIn("border-top: 1px solid rgba(231, 231, 232, 0.48)", styles)
        self.assertIn("border-top: 1px solid rgba(231, 231, 232, 0.46)", styles)
        self.assertIn("margin:0;padding:7px 12px 7px 18px", source)
        self.assertIn(".cuted-clip-info", styles)
        self.assertIn("data-cuted-clip-title", (Path(__file__).resolve().parents[1] / "tools" / "cutted" / "assets" / "control-bar" / "control-bar.js").read_text(encoding="utf-8"))
        self.assertIn("width: min(100%, 930px)", styles)
        self.assertIn("min-height: 112px", styles)
        self.assertIn("justify-content: flex-end", styles)

    def test_control_bar_volume_uses_compact_popover(self) -> None:
        asset_dir = Path(__file__).resolve().parents[1] / "tools" / "cutted" / "assets" / "control-bar"
        script = (asset_dir / "control-bar.js").read_text(encoding="utf-8")
        styles = (asset_dir / "control-bar.css").read_text(encoding="utf-8")

        self.assertIn("volumeMenuOpen: false", script)
        self.assertIn("data-cuted-volume-popover", script)
        self.assertIn("data-cuted-control=\"volume-mute\"", script)
        self.assertIn("<span>INS</span>", script)
        self.assertIn("state.volumeMenuOpen = !state.volumeMenuOpen", script)
        self.assertIn("insertAutoCloseClock", script)
        self.assertIn("scheduleInsertAutoClose", script)
        self.assertIn("}, 2200)", script)
        self.assertIn('document.addEventListener("click", dismissClick, true)', script)
        self.assertIn('document.removeEventListener("click", dismissClick, true)', script)
        self.assertNotIn('kind: "volume"', script)
        self.assertNotIn("Volume controls", script)
        self.assertIn(".cuted-volume-popover", styles)
        self.assertIn("top: calc(100% + 14px)", styles)
        self.assertIn("flex: 0 0 58px", styles)

    def test_cards_include_control_surface_slot(self) -> None:
        html = CUTTED.card_html(
            CUTTED.Moment(
                rank=1,
                start=0.0,
                end=12.0,
                peak=4.0,
                score=90,
                title="Teste",
                reason="",
                transcript="",
                peak_text="Pico",
                clip_file="clips/clip-001.mp4",
                frame_file="frames/clip-001.jpg",
            )
        )

        self.assertIn("data-cuted-control-surface", html)
        self.assertIn('data-clip-title="Teste"', html)
        self.assertIn("data-clip-summary", html)
        self.assertNotIn("clip-control-row", html)
        self.assertNotIn("clip-control-meta", html)
        self.assertIn("clip-control-surface", html)
        self.assertNotIn("clip-status", html)
        self.assertNotIn("Ajuste fino", html)
        self.assertNotIn("data-panel=\"effects\"", html)

    def test_edit_page_header_uses_single_surface_without_flow_tabs(self) -> None:
        html = CUTTED.page_html("Projeto", "", "{}", "assets/brand/cuted-logo-transparent.png")

        self.assertIn('id="finalize-videos" class="header-icon-button header-render-button"', html)
        self.assertIn('id="reset-ui" class="header-icon-button header-new-project"', html)
        self.assertIn('id="open-settings" class="header-icon-button header-settings-button"', html)
        self.assertIn('aria-label="Renderizar"', html)
        self.assertIn('aria-label="Novo projeto"', html)
        self.assertIn('viewBox="0 0 24 24"', html)
        self.assertNotIn('>Renderizar</button>', html)
        self.assertNotIn('>Novo projeto</button>', html)
        self.assertNotIn('<nav class="tabs"', html)
        self.assertNotIn('data-tab="import">1. Importar', html)
        self.assertNotIn('data-tab="edit" class="active"', html)
        self.assertNotIn('data-tab="final">3. Renderizar', html)
        self.assertIn('applyTab("edit");', html)

    def test_edit_header_icon_buttons_follow_cuted_style(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertIn("def header_action_icon_svg(name: str) -> str:", source)
        self.assertIn('"new-project"', source)
        self.assertIn('"render"', source)
        self.assertIn(".header-actions .header-icon-button,#reset-ui.header-icon-button,#finalize-videos.header-icon-button,#open-settings.header-icon-button", source)
        self.assertIn(".header-actions .header-render-button,#finalize-videos.header-render-button{width:58px;height:58px", source)
        self.assertIn("#finalize-videos.header-render-button.is-rendering", source)
        self.assertIn("cuted-render-icon-drift", source)
        self.assertIn('button.classList.toggle("is-rendering", active)', source)
        self.assertIn("border-color:rgba(175,207,42,.48)!important", source)
        self.assertIn(".header-actions .header-icon-button svg{position:relative;z-index:1;width:28px;height:28px", source)
        self.assertIn("#open-settings.header-settings-button.is-openai-ready", source)
        self.assertIn("animation:cuted-openai-gear-spin 5.8s linear infinite", source)
        self.assertIn("@keyframes cuted-openai-gear-spin{to{transform:rotate(360deg)}}", source)
        self.assertIn("function updateOpenaiSettingsIndicator(settings)", source)
        self.assertIn('button.classList.toggle("is-openai-ready", ready)', source)
        self.assertIn('const ready = Boolean(settings?.key_configured) && provider !== "local";', source)
        self.assertIn('updateOpenaiSettingsIndicator({ ...settingsPayloadFromForm(form), key_configured: true });', source)

    def test_openai_settings_uses_centered_animated_dialog(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        html = CUTTED.page_html("Projeto", "", "{}", "assets/brand/cuted-logo-transparent.png")

        self.assertIn("data-settings-panel", html)
        self.assertIn('aria-describedby="settings-description"', html)
        self.assertIn('class="settings-aura"', html)
        self.assertIn('class="settings-title-row"', html)
        self.assertIn('class="settings-close-button"', html)
        self.assertIn(".settings-backdrop{position:fixed!important;inset:0!important;z-index:5000!important", source)
        self.assertIn(".settings-backdrop.is-open{opacity:1;pointer-events:auto}", source)
        self.assertIn(".settings-backdrop.is-closing{opacity:0;pointer-events:none}", source)
        self.assertIn(".settings-backdrop.is-open .settings-panel{transform:translateY(0) scale(1);opacity:1}", source)
        self.assertIn(".settings-panel{scrollbar-width:none}.settings-panel::-webkit-scrollbar{width:0;height:0}", source)
        self.assertIn("@keyframes settings-aura-drift{to{transform:rotate(360deg)}}", source)
        self.assertIn("let settingsLastFocus = null;", source)
        self.assertIn('requestAnimationFrame(() => modal.classList.add("is-open"))', source)
        self.assertIn('modal.querySelector("[data-settings-panel]")?.focus();', source)
        self.assertIn("function trapSettingsFocus(event)", source)
        self.assertIn("settingsLastFocus?.focus?.();", source)

    def test_live_timeline_stops_at_trim_end_instead_of_looping(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "prototypes" / "live-timeline" / "src" / "liveTimeline.ts").read_text(
            encoding="utf-8"
        )

        self.assertIn("state.playhead = state.trimEnd", source)
        self.assertIn("activeCallbacks.onPlayToggle?.(false)", source)
        self.assertNotIn('playUiTone("loop", state)', source)

    def test_ai_director_openai_timeout_is_shorter_than_general_request(self) -> None:
        self.assertEqual(CUTTED.AI_DIRECTOR_OPENAI_TIMEOUT_SECONDS, 45)

    def test_ai_director_waits_for_visual_map_before_openai(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gallery = Path(tmp)
            media = CUTTED.CameraAnalysisMedia(Path(tmp) / "source.mp4", "source-key", "video", "source", 10.0)

            self.assertTrue(CUTTED.ai_director_should_wait_for_visual_map(gallery, media, "ai-director", None))
            self.assertFalse(CUTTED.ai_director_should_wait_for_visual_map(gallery, media, "auto-director", None))

    def test_pending_visual_map_ai_diagnostics_explains_fallback(self) -> None:
        diagnostics = CUTTED.pending_visual_map_ai_diagnostics("ai-director")

        self.assertEqual(diagnostics["status"], "visual_map_pending")
        self.assertIn("Mapa visual", str(diagnostics["error"]))

    def test_fast_camera_sample_times_are_bounded(self) -> None:
        sample_times = CUTTED.camera_fast_sample_times(120.0)

        self.assertLessEqual(len(sample_times), CUTTED.CAMERA_FAST_MAX_FRAMES + 1)
        self.assertLess(len(sample_times), len(CUTTED.camera_sample_times(120.0)))

    def test_ai_director_quality_rejects_speaker_only_path(self) -> None:
        path = [{"time": float(index * 3), "x": 50.0, "zoom": 1.1, "source": "ai-director-dynamic-speaker"} for index in range(6)]
        detections = [
            {"time": float(index * 2), "faces": [{"x": 50.0, "y": 45.0, "w": 12.0, "h": 14.0, "confidence": 0.6}]}
            for index in range(12)
        ]

        report = CUTTED.ai_director_quality_report(path, {}, detections, 30.0)

        self.assertTrue(report["rejected"])
        self.assertEqual(report["reason"], "speaker_only")

    def test_ai_director_quality_accepts_context_variation(self) -> None:
        path = [
            {"time": 0.0, "x": 50.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 5.0, "x": 42.0, "zoom": 1.08, "source": "ai-director-dynamic-speaker"},
            {"time": 9.0, "x": 62.0, "zoom": 1.1, "source": "ai-director-dynamic-reaction"},
        ]
        detections = [
            {"time": float(index * 2), "faces": [{"x": 50.0, "y": 45.0, "w": 12.0, "h": 14.0, "confidence": 0.6}]}
            for index in range(12)
        ]

        report = CUTTED.ai_director_quality_report(path, {}, detections, 30.0)

        self.assertFalse(report["rejected"])

    def test_ai_director_quality_rejects_group_dominant_path(self) -> None:
        path = [
            {"time": 0.0, "x": 50.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 6.0, "x": 52.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 12.0, "x": 48.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 18.0, "x": 51.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 24.0, "x": 42.0, "zoom": 1.08, "source": "ai-director-dynamic-speaker"},
        ]
        detections = [
            {
                "time": float(index * 2),
                "faces": [
                    {"x": 30.0, "y": 45.0, "width": 12.0, "confidence": 0.65},
                    {"x": 72.0, "y": 45.0, "width": 12.0, "confidence": 0.65},
                ],
            }
            for index in range(15)
        ]

        report = CUTTED.ai_director_quality_report(path, {}, detections, 30.0)

        self.assertTrue(report["rejected"])
        self.assertEqual(report["reason"], "group_dominant")
        self.assertGreater(report["group_duration_ratio"], CUTTED.AI_DIRECTOR_MAX_GROUP_DURATION_RATIO)

    def test_recover_previous_good_ai_result_preserves_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gallery = Path(tmp)
            cache_dir = gallery / "camera-analysis"
            cache_dir.mkdir()
            good = {
                "version": CUTTED.CAMERA_ANALYSIS_VERSION,
                "mode": "ai-director",
                "platform": "tiktok",
                "resolution_preset": "vertical_9_16",
                "clip_file": "clips/clip-001.mp4",
                "source": "ai-director",
                "diagnostics": {"ai_director": {"status": "applied", "enabled": True, "frame_samples": 8}},
                "camera_path": [{"time": 0.0, "x": 50.0, "zoom": 1.0}],
            }
            (cache_dir / "clip-001-clip-vertical_9_16-ai-director-good.json").write_text(
                json.dumps(good), encoding="utf-8"
            )
            fallback = {
                "mode": "ai-director",
                "resolution_preset": "vertical_9_16",
                "clip_file": "clips/clip-001.mp4",
                "diagnostics": {"ai_director": {"status": "timeout", "enabled": True}},
            }

            recovered = CUTTED.recover_previous_good_ai_result(gallery, fallback, "ai-director", "tiktok", "clips/clip-001.mp4")

        self.assertIsNotNone(recovered)
        assert recovered is not None
        self.assertTrue(recovered["cache_recovered"])

    def test_side_coverage_adds_missing_right_focus(self) -> None:
        frames = [
            {"time": 0.0, "x": 50.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 8.0, "x": 30.0, "zoom": 1.1, "source": "ai-director-dynamic-speaker"},
        ]
        detections = [
            {
                "time": 10.0 + index * 4.0,
                "faces": [
                    {"x": 30.0, "y": 45.0, "w": 12.0, "h": 14.0, "confidence": 0.65},
                    {"x": 72.0, "y": 45.0, "w": 12.0, "h": 14.0, "confidence": 0.65},
                ],
            }
            for index in range(3)
        ]

        coverage = CUTTED.side_coverage_camera_frames(frames, detections, 30.0, "tiktok", False)

        self.assertTrue(any(float(frame.get("x") or 0) > 58.0 for frame in coverage))
        self.assertTrue(any(str(frame.get("intent")) == "speaker_hold" for frame in coverage))
        self.assertTrue(all(float(frame.get("zoom") or 1.0) <= 1.08 for frame in coverage))

    def test_side_coverage_balances_underrepresented_side(self) -> None:
        frames = [{"time": float(index * 8), "x": 30.0, "zoom": 1.1} for index in range(6)]
        detections = [
            {
                "time": 10.0 + index * 5.0,
                "faces": [
                    {"x": 30.0, "y": 45.0, "width": 12.0, "confidence": 0.65},
                    {"x": 72.0, "y": 45.0, "width": 12.0, "confidence": 0.65},
                ],
            }
            for index in range(6)
        ]

        coverage = CUTTED.side_coverage_camera_frames(frames, detections, 60.0, "tiktok", False)
        merged = CUTTED.merge_camera_path_frames(frames, coverage, 60.0)

        self.assertGreaterEqual(CUTTED.side_counts_from_frames(merged)["right"], 3)
        self.assertNotIn("right", CUTTED.missing_camera_sides(merged, detections))

    def test_max_still_camera_frames_breaks_long_hold(self) -> None:
        frames = [{"time": 0.0, "x": 30.0, "zoom": 1.1, "source": "ai-director-dynamic-speaker"}]
        detections = [
            {
                "time": 14.0,
                "faces": [
                    {"x": 30.0, "y": 45.0, "w": 12.0, "h": 14.0, "confidence": 0.65},
                    {"x": 72.0, "y": 45.0, "w": 12.0, "h": 14.0, "confidence": 0.65},
                ],
            }
        ]

        motion = CUTTED.max_still_camera_frames(frames, detections, 30.0, "tiktok", False)

        self.assertTrue(motion)
        self.assertLessEqual(max(CUTTED.camera_path_gaps(CUTTED.merge_camera_path_frames(frames, motion, 30.0), 30.0)), CUTTED.AI_DIRECTOR_MAX_STILL_SECONDS)

    def test_clean_output_path_keeps_empty_value(self) -> None:
        self.assertEqual(CUTTED.clean_output_path(""), "")
        self.assertEqual(CUTTED.clean_output_path(None), "")
        self.assertEqual(CUTTED.clean_output_path('  "C:\\videos"  '), str(Path("C:\\videos")))

    def test_import_command_uses_plain_experimental_youtube_url(self) -> None:
        metadata = {
            "preview_count": 3,
            "preset": "tiktok",
            "duration_profile": "medium",
            "ai_provider": "local",
            "context_prompt": "",
            "language": "pt",
            "render_previews": True,
        }

        with tempfile.TemporaryDirectory() as tmp:
            command = CUTTED.import_command(Path(tmp), "https://www.youtube.com/watch?v=test", "", metadata)

        self.assertIn("--youtube-url", command)
        self.assertNotIn("--youtube-cookies-from-browser", command)
        self.assertNotIn("--youtube-cookies-file", command)

    def test_import_command_uses_local_video_path(self) -> None:
        metadata = {
            "preview_count": 3,
            "preset": "tiktok",
            "duration_profile": "medium",
            "ai_provider": "local",
            "context_prompt": "",
            "language": "pt",
            "render_previews": True,
        }
        with tempfile.TemporaryDirectory() as tmp:
            video_path = Path(tmp) / "video.mp4"
            video_path.write_bytes(b"fake")

            command = CUTTED.import_command(Path(tmp), "", str(video_path), metadata)

        self.assertIn(str(video_path.resolve()), command)
        self.assertNotIn("--youtube-url", command)

    def test_local_import_limits_initial_preview_count(self) -> None:
        metadata = {"preview_count": 10}

        self.assertEqual(CUTTED.import_preview_count("", metadata), CUTTED.LOCAL_IMPORT_MAX_INITIAL_CLIPS)
        self.assertEqual(CUTTED.import_preview_count("https://www.youtube.com/watch?v=test", metadata), 10)

    def test_visual_map_source_path_uses_local_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            video_path = Path(tmp) / "video.mp4"
            video_path.write_bytes(b"fake")
            metadata = CUTTED.source_media_metadata("local", video_path.name, str(video_path), {}, None, None)
            source = CUTTED.SourceMedia(str(video_path), video_path, video_path.name, (), metadata)

            self.assertEqual(CUTTED.visual_map_source_path(source), video_path.resolve())

    def test_friendly_ytdlp_error_explains_antibot(self) -> None:
        message = CUTTED.friendly_ytdlp_error("Sign in to confirm you're not a bot")

        self.assertIn("anti-bot", message)
        self.assertIn("arquivo local", message)

    def test_import_job_error_message_uses_friendly_youtube_error(self) -> None:
        message = CUTTED.import_job_error_message("[cutted] Error: Sign in to confirm you're not a bot")

        self.assertIn("anti-bot", message)
        self.assertNotIn("[cutted] Error", message)

    def test_import_job_snapshot_includes_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job = CUTTED.ImportJob(
                "job123",
                "running",
                time.time() - 8,
                time.time(),
                Path(tmp),
                Path(tmp),
                "/projects/job123/index.html",
                None,
                "Importacao iniciada.",
                "youtube",
                "openai",
            )

            payload = CUTTED.import_job_to_dict(job)

        self.assertIn("progress", payload)
        self.assertIn("message", payload["progress"])
        self.assertGreaterEqual(payload["progress"]["percent"], 8)
        self.assertIn(payload["progress"]["label"], {"Preparando", "Midia", "Audio", "Analise", "Sugestoes", "Editor"})

    def test_import_request_metadata_requires_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "link ou caminho local"):
            CUTTED.import_request_metadata({"output_path": "C:\\videos"})

    def test_import_request_metadata_uses_automatic_render_destination(self) -> None:
        original_provider = CUTTED.configured_ai_provider
        CUTTED.configured_ai_provider = lambda: "local"
        try:
            metadata = CUTTED.import_request_metadata({"source_path": "video.mp4", "preview_count": 20})
        finally:
            CUTTED.configured_ai_provider = original_provider

        self.assertEqual(metadata["output_path"], "")
        self.assertEqual(metadata["preview_count"], 10)

    def test_next_import_output_dir_uses_projects_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = CUTTED.next_import_output_dir(Path(tmp), "video.mp4")

            self.assertEqual(output_dir.parent.name, CUTTED.PROJECTS_DIR_NAME)
            self.assertEqual(output_dir.parent.parent, Path(tmp))

    def test_render_export_dir_prefers_project_render_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gallery_dir = Path(tmp) / "projects" / "demo"
            render_dir = gallery_dir / "renders"
            gallery_dir.mkdir(parents=True)
            (gallery_dir / "import-request.json").write_text(
                json.dumps({"render_output_path": str(render_dir), "output_path": "C:\\legacy"}),
                encoding="utf-8",
            )

            self.assertEqual(CUTTED.render_export_dir(gallery_dir), render_dir)


class CuttedLaunchTests(unittest.TestCase):
    def test_default_workspace_dir_lives_under_documents(self) -> None:
        workspace = CUTTED.default_workspace_dir()

        self.assertEqual(workspace.name, "CUTED Workspace")
        self.assertEqual(workspace.parent.name, "Documents")

    def test_bootstrap_workspace_gallery_creates_empty_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            CUTTED.bootstrap_workspace_gallery(workspace)

            index_path = workspace / "index.html"
            self.assertTrue(index_path.exists())
            html = index_path.read_text(encoding="utf-8")
            self.assertIn("data-project-home", html)
            self.assertIn("Novo projeto", html)
            self.assertIn("data-import-form", html)
            self.assertNotIn('data-tab="edit"', html)

    def test_bootstrap_workspace_gallery_preserves_existing_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            index_path = workspace / "index.html"
            index_path.write_text("conteudo existente", encoding="utf-8")

            CUTTED.bootstrap_workspace_gallery(workspace)

            self.assertEqual(index_path.read_text(encoding="utf-8"), "conteudo existente")

    def test_bootstrap_workspace_gallery_refreshes_empty_shell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            index_path = workspace / "index.html"
            index_path.write_text('<form data-import-form></form><script>{"moments": []}</script>', encoding="utf-8")

            CUTTED.bootstrap_workspace_gallery(workspace)

            html = index_path.read_text(encoding="utf-8")
            self.assertIn("data-project-home", html)
            self.assertIn('name="source_path"', html)
            self.assertNotIn('data-tab="edit"', html)

    def test_find_free_port_returns_port_in_launch_range(self) -> None:
        port = CUTTED.find_free_port("127.0.0.1")

        self.assertIn(port, CUTTED.LAUNCH_PORT_RANGE)

    def test_launch_command_is_registered(self) -> None:
        argv_backup = sys.argv
        sys.argv = ["cutted.py", "launch", "--no-browser", "--workspace", "ignored"]
        try:
            args = CUTTED.parse_args()
        finally:
            sys.argv = argv_backup

        self.assertEqual(args.command, "launch")
        self.assertTrue(args.no_browser)
        self.assertEqual(args.workspace, Path("ignored"))


class CutedLauncherTests(unittest.TestCase):
    def test_normalized_argv_defaults_to_launch(self) -> None:
        self.assertEqual(LAUNCHER.normalized_argv(["cuted.exe"]), ["cuted.exe", "launch"])

    def test_normalized_argv_strips_frozen_reentry_script(self) -> None:
        argv = ["cuted.exe", "C:\\app\\_internal\\tools\\cutted\\scripts\\CUTTED.PY", "analyze", "--out", "x"]

        self.assertEqual(LAUNCHER.normalized_argv(argv), ["cuted.exe", "analyze", "--out", "x"])

    def test_normalized_argv_keeps_explicit_commands(self) -> None:
        argv = ["cuted.exe", "serve", "--dir", "pasta"]

        self.assertEqual(LAUNCHER.normalized_argv(argv), argv)

    def test_run_python_module_executes_module_with_argv(self) -> None:
        argv_backup = sys.argv
        try:
            exit_code = LAUNCHER.run_python_module(["platform"])
        finally:
            sys.argv = argv_backup

        self.assertEqual(exit_code, 0)

    def test_launcher_loads_cutted_module(self) -> None:
        module = LAUNCHER.load_cutted()

        self.assertTrue(hasattr(module, "launch_workspace"))
        self.assertTrue(hasattr(module, "import_request_metadata"))


if __name__ == "__main__":
    unittest.main()
