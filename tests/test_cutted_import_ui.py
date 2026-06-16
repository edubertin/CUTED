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

    def test_editor_state_is_scoped_to_current_project(self) -> None:
        html = gallery_html()

        self.assertIn("function galleryStorageKey(name)", html)
        self.assertIn('const editorStateStorageKey = galleryStorageKey("cutted-state");', html)
        self.assertIn('const editorTabStorageKey = galleryStorageKey("cutted-tab");', html)
        self.assertIn('const state = JSON.parse(localStorage.getItem(editorStateStorageKey) || "{}");', html)
        self.assertIn("localStorage.setItem(editorStateStorageKey, JSON.stringify(state));", html)
        self.assertIn("localStorage.setItem(editorTabStorageKey, next);", html)
        self.assertNotIn('localStorage.setItem("cutted-state", JSON.stringify(state));', html)
        self.assertNotIn('const state = JSON.parse(localStorage.getItem("cutted-state") || "{}");', html)

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
        styles = (Path(__file__).resolve().parents[1] / "tools" / "cutted" / "assets" / "control-bar" / "control-bar.css").read_text(
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
        self.assertIn("SENT TO RENDER", script)
        self.assertIn("Ja esta renderizando", html)
        self.assertIn("}, 2600);", html)
        self.assertIn("if (payload.duplicate)", html)
        self.assertIn("cancelControlSurfaceReady(card);", html)
        self.assertIn("update?.({ renderQueued: false });", html)
        self.assertIn("elements.statusAction.addEventListener(\"click\"", script)
        self.assertIn("event.stopPropagation();", script)
        self.assertIn("const transientStatus = state.status && !state.status.persistent ? state.status : null;", script)
        self.assertIn("const statusIsTransient = !state.trimMode && Boolean(transientStatus);", script)
        self.assertIn('classList.toggle("is-status-transient", statusIsTransient);', script)
        self.assertIn('.cuted-control-bar.is-status-transient[data-status-kind="ready"]', styles)
        self.assertIn("right: 108px;", styles)
        self.assertIn("state.renderQueued", script)
        self.assertIn("data-cuted-status-action", script)
        self.assertNotIn('data-cuted-control="send-render"', script)
        self.assertNotIn("openRenderQueuePanel();\n    await loadRenderQueue();", html)
        self.assertNotIn("showAppNotice(label);\n    await loadRenderQueue();", html)

    def test_closed_captions_can_render_in_preview(self) -> None:
        html = gallery_html()

        self.assertIn("data-preview-caption-layer", html)
        self.assertIn(".preview-caption-layer", html)
        self.assertIn("function syncPreviewCaptions", html)
        self.assertIn("function previewCaptionEventsFromSegments", html)
        self.assertIn("function previewCaptionEventForCard", html)
        self.assertIn("syncPreviewCaptionsForOpenCards();", html)
        self.assertIn("syncPreviewCaptions(card, current);", html)
        self.assertIn("caption_segments: moment.caption_segments || []", html)
        self.assertIn("onCaptionToggle: payload => setControlSurfaceCaptions(payload.captionsEnabled, payload.captionStyle)", html)
        self.assertIn("caption_style: captions.style", html)
        self.assertIn("captions_enabled: captions.enabled", html)
        self.assertIn("function captionSettingsForCard(card)", html)
        self.assertIn("storeCaptionStyle(style)", html)
        self.assertIn("captionMode() === \"animated\" ? \"Animada\"", html)
        self.assertIn("function previewAnimatedCaptionHtml", html)

    def test_preview_caption_text_repairs_portuguese_mojibake(self) -> None:
        html = gallery_html()
        broken = "voc\u00c3\u00aa n\u00c3\u00a3o tem rela\u00c3\u00a7\u00c3\u00a3o com informa\u00c3\u00a7\u00c3\u00a3o"

        self.assertEqual(CUTTED.clean_caption_text(broken), "você não tem relação com informação")
        self.assertIn("function repairPreviewCaptionEncoding", html)
        self.assertIn("replacePreviewCaptionMojibakeSequences", html)
        self.assertIn("return repairPreviewCaptionEncoding(text)", html)

    def test_closed_caption_control_bar_menu_is_available(self) -> None:
        asset_dir = Path(__file__).resolve().parents[1] / "tools" / "cutted" / "assets" / "control-bar"
        script = (asset_dir / "control-bar.js").read_text(encoding="utf-8")
        styles = (asset_dir / "control-bar.css").read_text(encoding="utf-8")

        self.assertIn("captionMenuOpen", script)
        self.assertIn("captionPaletteOpen", script)
        self.assertIn("renderCaptionMenu", script)
        self.assertIn("data-cuted-caption-toggle", script)
        self.assertIn("data-cuted-caption-mode=\"animated\"", script)
        self.assertIn("data-cuted-caption-size", script)
        self.assertIn("data-cuted-caption-width", script)
        self.assertIn("data-cuted-caption-bottom", script)
        self.assertIn('renderCaptionColorPicker("text", "A", "#ffffff")', script)
        self.assertIn('renderCaptionColorPicker("background", "BG", "#000000")', script)
        self.assertIn("renderCaptionPalette", script)
        self.assertIn("data-cuted-caption-swatch", script)
        self.assertIn("renderCaptionSwatch", script)
        self.assertIn("onCaptionStyleChange", script)
        self.assertIn(".cuted-caption-menu", styles)
        self.assertIn(".cuted-caption-palette", styles)
        self.assertIn(".cuted-caption-switch", styles)
        self.assertIn(".cuted-caption-swatch", styles)

    def test_caption_ass_style_accepts_control_bar_style(self) -> None:
        preset = CUTTED.PLATFORM_PRESETS["tiktok"]
        style = CUTTED.caption_style_from_row(
            {"caption_style": {"size": 88, "width": 34, "textColor": "#11a2cf", "backgroundColor": "#000000"}},
            preset,
        )
        line = CUTTED.ass_style_line(preset, style)

        self.assertIn("Arial,88,", line)
        self.assertIn("&H00CFA211", line)
        self.assertIn("&H66000000", line)
        self.assertIn(",3,7,0,2,80,80,313,1", line)
        self.assertEqual(style["width"], 34)
        self.assertEqual(style["mode"], "on")

    def test_animated_caption_style_exports_word_pop_events(self) -> None:
        preset = CUTTED.PLATFORM_PRESETS["tiktok"]
        row = {
            "adjusted_duration": 2.0,
            "caption_style": {"mode": "animated", "size": 72, "bottom": 18},
            "caption_segments": [{"start": 0.0, "end": 2.0, "text": "fala rapida agora"}],
        }
        events = CUTTED.caption_events(row, 28, 2, 2.0)
        ass = CUTTED.ass_document_with_style(events, 2.0, preset, 28, 2, row)

        self.assertIn("Arial,59,", ass)
        self.assertIn(",3,7,0,2,80,80,346,1", ass)
        self.assertIn("fala", ass)
        self.assertIn("\\fscx108", ass)

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

    def test_ffmpeg_progress_parser_reports_render_percent(self) -> None:
        self.assertEqual(CUTTED.parse_ffmpeg_progress_seconds("out_time_ms", "1234000"), 1.234)
        self.assertEqual(CUTTED.parse_ffmpeg_progress_seconds("out_time", "00:01:30.500000"), 90.5)
        self.assertEqual(CUTTED.parse_ffmpeg_speed("1.25x"), 1.25)
        self.assertIn("Renderizando 50%", CUTTED.render_progress_message(5, 10, "1.25x", 4))
        self.assertIn("-progress", CUTTED.ffmpeg_command_with_progress(["ffmpeg", "-y"]))

    def test_render_jobs_support_cancel_remove_and_process_cancel(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertIn('"/api/render-jobs/[^/]+/remove"', source)
        self.assertIn('"/api/render-jobs/[^/]+/profile"', source)
        self.assertIn("def remove_render_job(job_id: str, gallery_dir: Path)", source)
        self.assertIn("def update_render_job_profile(job_id: str, gallery_dir: Path, profile_value: object)", source)
        self.assertIn("def render_job_cancelled(job_id: object)", source)
        self.assertIn("process = subprocess.Popen(", source)
        self.assertIn("update_render_job_progress(job_id, last_seconds, duration, last_speed)", source)
        self.assertIn("process.terminate()", source)
        self.assertIn('raise RuntimeError("Render cancelado.")', source)

    def test_render_queue_profile_and_progress_ui_are_available(self) -> None:
        html = gallery_html()

        self.assertIn("setRenderQueueProfile", html)
        self.assertIn("updateRenderQueueProfileJob", html)
        self.assertIn("/profile", html)
        self.assertIn("job.speed", html)
        self.assertIn("job.eta_seconds", html)
        self.assertIn("formatRenderEta", html)
        self.assertIn("Render atual mantem os threads atuais", html)

    def test_render_camera_path_is_rebased_after_trim(self) -> None:
        html = gallery_html()

        self.assertIn("function exportCameraPathForEdit", html)
        self.assertIn("Object.assign({}, active, { time: 0 })", html)
        self.assertIn("time <= safeTrimStart + .001", html)
        self.assertIn("time - safeTrimStart", html)
        self.assertIn("function sourceDurationForMoment", html)
        self.assertIn("exportCameraPathForEdit(edit, sourceDuration, trimStart, adjustedDuration)", html)
        self.assertIn("exportCameraPathForEdit(edit, sourceDurationForMoment(moment), moment.trim_start_seconds, moment.adjusted_duration)", html)
        self.assertIn("exportCameraPathForEdit(edit, values.duration, values.trimStart, duration)", html)
        self.assertNotIn("cameraPathForEdit(edit, moment.adjusted_duration);", html)

    def test_export_prefers_generated_publish_metadata(self) -> None:
        html = gallery_html()

        self.assertIn("moment.publish_metadata && typeof moment.publish_metadata === \"object\"", html)
        self.assertIn("const edit = publishEditForRank(moment.rank)", html)
        self.assertIn("Object.assign({}, generated", html)
        self.assertIn("publishCaptionHintFromEdit(edit, generated", html)
        self.assertIn("cover: publishCoverFromEdit(edit, generated, moment)", html)
        self.assertIn("const zoom = normalizePublishCoverZoom(edit.coverZoom", html)
        self.assertIn("zoom,", html)
        self.assertIn("x: normalizePublishCoverPosition(edit.coverX ?? cover.x, zoom)", html)
        self.assertIn("y: normalizePublishCoverPosition(edit.coverY ?? cover.y, zoom)", html)
        self.assertIn('parts.join("\\n\\n")', html)

    def test_publish_panel_edits_are_bound_to_card_state(self) -> None:
        html = gallery_html()

        self.assertIn("function bindPublishPanel(card)", html)
        self.assertIn("data-publish-field", html)
        self.assertIn("data-publish-cover-option", html)
        self.assertIn("data-publish-cover-zoom", html)
        self.assertIn("data-publish-cover-preview", html)
        self.assertIn("function bindPublishCoverDrag(card)", html)
        self.assertIn("function movePublishCoverDrag(card, drag, event)", html)
        self.assertIn("publish.coverFrame", html)
        self.assertIn("publish.coverZoom", html)
        self.assertIn("publish.coverX", html)
        self.assertIn("publish.coverY", html)
        self.assertIn("publish[input.dataset.publishField]", html)
        self.assertIn("setCardState(card.dataset.rank, { publish })", html)

    def test_import_progress_names_publish_seo_stage(self) -> None:
        stages = CUTTED.import_job_running_stages("youtube", "openai")

        self.assertIn(("Publicacao IA", "Analisando SEO e tendencias..."), stages)
        self.assertIn('data-import-step="publish"', CUTTED.project_home_import_loading_html("assets/brand/cuted-logo-transparent.png"))

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

    def test_finalized_file_urls_normalizes_base_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gallery_dir = Path(tmp) / "gallery"
            out_dir = gallery_dir / "captioned-clips"
            out_dir.mkdir(parents=True)
            file_path = out_dir / "clip-002-tiktok-captioned.mp4"
            file_path.write_bytes(b"video")
            aliased_base_dir = gallery_dir / "nested" / ".."

            files = CUTTED.finalized_file_urls([{"file": str(file_path)}], aliased_base_dir)

            self.assertEqual(files[0]["url"], "captioned-clips/clip-002-tiktok-captioned.mp4")

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
        self.assertIn('label: "AI camera already exists"', script)
        self.assertIn("state.ready || state.discarded || state.busy", script)
        self.assertIn("dataset.ready = String(state.ready || state.discarded)", script)
        self.assertIn('classList.toggle("is-busy"', script)
        self.assertIn(".cuted-control-bar.is-busy .cuted-audio-group", styles)
        self.assertIn('.cuted-control-bar[data-status-kind="ai"] .cuted-ready-region', styles)
        self.assertIn('.cuted-control-bar[data-status-kind="mapping"] .cuted-ready-region', styles)
        self.assertIn('.cuted-control-bar[data-status-kind="mapping"] .cuted-action-group', styles)
        self.assertIn('.cuted-control-bar[data-status-kind="mapping"] .cuted-ready-divider', styles)

    def test_caption_settings_are_scoped_to_active_platform_render_row(self) -> None:
        html = gallery_html()

        self.assertIn("captions: normalizeCaptionSettings(captionSource, captionBase)", html)
        self.assertIn("captionsEnabled: edit.captions.enabled", html)
        self.assertIn("captionStyle: edit.captions.style", html)
        self.assertIn("setPlatformEditForRank(rank, platform, {", html)
        self.assertIn("captions: normalizeCaptionSettings({", html)
        self.assertIn("const captions = normalizeCaptionSettings(edit.captions)", html)
        self.assertIn("captions_enabled: captions.enabled", html)
        self.assertIn("caption_style: captions.style", html)
        self.assertIn("captions_enabled: queue.some(item => item.captions_enabled !== false)", html)
        self.assertIn("captions_enabled: queue.caption_queue.some(item => item.captions_enabled !== false)", html)

    def test_render_queue_does_not_expose_submit_action(self) -> None:
        html = gallery_html()

        self.assertIn("function renderQueueJobHtml(job)", html)
        self.assertNotIn("<button type=\"button\" disabled>Submit</button>", html)

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
        self.assertIn(".brand-logo{transform:translateY(-16px)", source)
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
        self.assertIn(".clip-control-surface .cuted-effect-menu,.clip-control-surface .cuted-insert-menu,.clip-control-surface .cuted-caption-menu,.clip-control-surface .cuted-format-menu,.clip-control-surface .cuted-volume-popover{z-index:3200}", source)
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
        self.assertIn("data-cuted-insert-exit", script)
        self.assertIn("setInsertStatus", script)
        self.assertIn("Start video inserted", script)
        self.assertIn(".cuted-insert-options", styles)
        self.assertNotIn("scheduleInsertAutoClose", script)
        self.assertIn('document.addEventListener("click", dismissClick, true)', script)
        self.assertIn('document.removeEventListener("click", dismissClick, true)', script)
        self.assertNotIn('kind: "volume"', script)
        self.assertNotIn("Volume controls", script)
        self.assertIn(".cuted-volume-popover", styles)
        self.assertIn("top: calc(100% + 14px)", styles)
        self.assertIn("flex: 0 0 58px", styles)

    def test_control_bar_trim_tool_toggles_live_timeline_handles(self) -> None:
        root = Path(__file__).resolve().parents[1]
        script = (root / "tools" / "cutted" / "assets" / "control-bar" / "control-bar.js").read_text(
            encoding="utf-8"
        )
        styles = (root / "tools" / "cutted" / "assets" / "control-bar" / "control-bar.css").read_text(
            encoding="utf-8"
        )
        source = (root / "tools" / "cutted" / "scripts" / "cutted.py").read_text(encoding="utf-8")
        timeline = (root / "prototypes" / "live-timeline" / "src" / "liveTimeline.ts").read_text(encoding="utf-8")
        timeline_styles = (root / "prototypes" / "live-timeline" / "src" / "timeline.css").read_text(
            encoding="utf-8"
        )

        self.assertIn('data-cuted-control="trim"', script)
        self.assertIn("trimApplied: false", script)
        self.assertIn("onTrimConfirm", script)
        self.assertIn("buildTrimStatus()", script)
        self.assertIn("renderTrimStatus()", script)
        self.assertIn("CONFIRME", script)
        self.assertIn("is-trim-applied", script)
        self.assertIn("restoreTrimStatus()", script)
        self.assertIn("confirmTrimMode()", script)
        self.assertIn("onTrimToggle", script)
        self.assertIn('label: "TRIM"', script)
        self.assertIn("state.trimMode = true", script)
        self.assertIn("state.trimMode = false", script)
        self.assertIn('trimMode: !busy && card.dataset.trimMode === "1"', source)
        self.assertIn("trimApplied: trimRangeActive(trim)", source)
        self.assertIn("setControlSurfaceTrimMode(card, payload.trimMode)", source)
        self.assertIn('trimEnabled: card.dataset.trimMode === "1"', source)
        self.assertIn("trimEnabled?: boolean", timeline)
        self.assertIn("state.trimEnabled", timeline)
        self.assertIn('[data-trim-enabled="false"] .trim-handle', timeline_styles)
        self.assertIn('[data-status-kind="trim"]', styles)
        self.assertIn("cuted-trim-blade-top", styles)
        self.assertIn(".cuted-trim-button.is-trim-applied", styles)

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

    def test_workspace_new_project_button_confirms_exit_to_home(self) -> None:
        html = CUTTED.page_html("Projeto", "", "{}", "assets/brand/cuted-logo-transparent.png")
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertIn("data-workspace-exit-modal", html)
        self.assertIn("Sair deste projeto?", html)
        self.assertIn("Voltar para recentes", html)
        self.assertIn("function setupWorkspaceExitModal()", source)
        self.assertIn("function openWorkspaceExitModal()", source)
        self.assertIn("async function touchCurrentProject()", source)
        self.assertIn('fetch("/api/projects/touch"', source)
        self.assertIn("async function confirmWorkspaceExit()", source)
        self.assertIn("save();\n  const button = document.querySelector(\"[data-workspace-exit-confirm]\");", source)
        self.assertIn("await touchCurrentProject();", source)
        self.assertIn('touchCurrentProject().catch(error => console.warn("CUTED project was not added to recents", error));', source)
        self.assertIn('window.location.assign("/index.html");', source)
        self.assertIn("function startNewProject(){\n  openWorkspaceExitModal();\n}", source)
        self.assertNotIn('confirm("Iniciar novo projeto?', source)

    def test_edit_header_icon_buttons_follow_cuted_style(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertIn("def header_action_icon_svg(name: str) -> str:", source)
        self.assertIn('"new-project"', source)
        self.assertIn('"render"', source)
        self.assertIn(".header-actions .header-icon-button,#reset-ui.header-icon-button,#finalize-videos.header-icon-button,#open-settings.header-icon-button", source)
        self.assertIn(".header-actions{position:absolute;right:26px;top:50%;display:flex;justify-content:flex-end;align-items:center;gap:10px;width:auto;margin:0;transform:translateY(-50%)}", source)
        self.assertIn("header{grid-template-columns:1fr!important;justify-items:center;padding:18px 26px 2px!important}", source)
        self.assertIn("#reset-ui.header-icon-button,#finalize-videos.header-icon-button,#open-settings.header-icon-button{width:56px!important;height:56px!important;min-width:56px!important;", source)
        self.assertIn("background:linear-gradient(145deg,rgba(17,162,207,.16),rgba(175,207,42,.08) 48%,rgba(5,5,5,.84)),rgba(5,5,5,.88)!important", source)
        self.assertIn("transform:translateY(-2px) scale(1.035)", source)
        self.assertIn(".header-actions .header-render-button,#finalize-videos.header-render-button{width:56px!important;height:56px!important", source)
        self.assertNotIn("border-color:rgba(231,231,232,.22)!important;background:var(--color-brand-white)!important;color:var(--color-brand-black)!important", source)
        self.assertIn("#finalize-videos.header-render-button.is-rendering", source)
        self.assertIn("background:linear-gradient(180deg,rgba(175,207,42,.2),rgba(17,162,207,.065)),rgba(12,14,9,.72)!important", source)
        self.assertIn("cuted-render-icon-drift", source)
        self.assertIn('button.classList.toggle("is-rendering", active)', source)
        self.assertIn("border-color:rgba(175,207,42,.78)!important", source)
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

    def test_import_progress_event_is_parsed_for_job_snapshot(self) -> None:
        event = CUTTED.parse_import_progress_line(
            'CUTED_IMPORT_EVENT {"stage":"previews","label":"Previews","message":"Renderizando previews...","percent":82,"step":2,"steps":4,"detail":"2 de 4 previews"}'
        )

        self.assertIsNotNone(event)
        self.assertEqual(event["stage"], "previews")
        self.assertEqual(event["label"], "Previews")
        self.assertEqual(event["percent"], 82)
        self.assertEqual(event["step"], 2)
        self.assertEqual(event["steps"], 4)
        self.assertEqual(event["detail"], "2 de 4 previews")

    def test_import_job_snapshot_prefers_real_progress_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job = CUTTED.ImportJob(
                "job123",
                "running",
                time.time() - 30,
                time.time(),
                Path(tmp),
                Path(tmp),
                "/projects/job123/index.html",
                None,
                "Importacao iniciada.",
                "local",
                "local",
            )
            job.progress = {
                "stage": "previews",
                "label": "Previews",
                "message": "Renderizando previews...",
                "percent": 84,
                "step": 3,
                "steps": 4,
            }
            job.events.append(job.progress)

            payload = CUTTED.import_job_to_dict(job)

        self.assertEqual(payload["progress"]["stage"], "previews")
        self.assertEqual(payload["progress"]["percent"], 84)
        self.assertEqual(payload["events"][0]["step"], 3)

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
