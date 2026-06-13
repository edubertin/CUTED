from __future__ import annotations

import importlib.util
import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "cutted" / "scripts" / "cutted.py"
SPEC = importlib.util.spec_from_file_location("cutted_camera_test_module", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load cutted.py for camera tests.")
CUTTED = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CUTTED
SPEC.loader.exec_module(CUTTED)


def face(x: float, width: float = 8.0) -> dict[str, float]:
    return {
        "x": x,
        "y": 48.0,
        "width": width,
        "height": 18.0,
        "area": width * 18.0,
        "confidence": 0.88,
        "zoom": 1.14,
    }


def person(x: float, width: float = 18.0) -> dict[str, object]:
    return {
        "x": x,
        "y": 43.0,
        "width": width,
        "height": 62.0,
        "area": width * 62.0 * 0.08,
        "body_area": width * 62.0,
        "confidence": 0.82,
        "zoom": 1.12,
        "kind": "person",
        "source": "yolo-person",
    }


def detection(time_value: float, faces: list[dict[str, float]]) -> dict[str, object]:
    primary = max(faces, key=lambda item: float(item["area"])) if faces else None
    return {"time": time_value, "faces": faces, "primary": primary}


def missing_detection(time_value: float) -> dict[str, object]:
    return {"time": time_value, "faces": [], "primary": None, "missing": True}


class CuttedCameraRuleTests(unittest.TestCase):
    def test_visual_map_summary_counts_faces_people_and_groups(self) -> None:
        rows = [
            {"time": 0.0, "faces": [face(35.0), face(65.0)], "persons": [person(50.0)], "primary": face(35.0)},
            {"time": 1.0, "faces": [face(48.0)], "persons": [], "primary": face(48.0)},
            missing_detection(2.0),
        ]

        summary = CUTTED.visual_map_summary(rows, [0.0, 1.0, 2.0])

        self.assertEqual(summary["detection_rows"], 3)
        self.assertEqual(summary["max_faces"], 2)
        self.assertEqual(summary["max_persons"], 1)
        self.assertGreater(summary["face_detection_rate"], 0.0)
        self.assertGreater(summary["group_rate"], 0.0)

    def test_visual_map_segment_detections_rebases_times(self) -> None:
        payload = {
            "detections": [
                {"time": 1.0, "faces": [face(42.0)], "primary": face(42.0)},
                {"time": 3.0, "faces": [face(54.0)], "primary": face(54.0)},
                {"time": 5.0, "faces": [face(62.0)], "primary": face(62.0)},
            ]
        }

        rows = CUTTED.visual_map_segment_detections(payload, 2.0, 3.0)

        self.assertEqual([row["time"] for row in rows], [1.0, 3.0])

    def test_visual_map_camera_analysis_uses_cached_source_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gallery = Path(tmp)
            source_path = gallery / "source.mp4"
            source_path.write_bytes(b"fake")
            payload = {
                "ok": True,
                "version": CUTTED.VISUAL_MAP_VERSION,
                "source": str(source_path.resolve()),
                "fingerprint": {"path": str(source_path.resolve())},
                "metadata": {"width": 1920, "height": 1080, "duration": 10.0},
                "sample_count": 4,
                "vision_engine": "yolo-visual-map",
                "vision_model": "yolo26n.pt",
                "detections": [
                    {"time": 2.0, "faces": [face(35.0), face(65.0)], "primary": face(35.0)},
                    {"time": 3.0, "faces": [face(38.0), face(66.0)], "primary": face(38.0)},
                    {"time": 4.0, "faces": [face(40.0)], "primary": face(40.0)},
                ],
            }
            (gallery / "visual-map.json").write_text(json.dumps(payload), encoding="utf-8")
            media = CUTTED.CameraAnalysisMedia(source_path.resolve(), "cache", "source.mp4", "source", 2.0)

            result = CUTTED.visual_map_camera_analysis(gallery, media, 3.0, "auto-director", "tiktok", "", "")

        self.assertIsNotNone(result)
        self.assertTrue(str(result["source"]).startswith("visual-map"))
        self.assertTrue(result["diagnostics"]["visual_map"]["used"])
        self.assertEqual(result["diagnostics"]["vision_engine"], "yolo-visual-map")

    def test_visual_map_ai_timeout_uses_dense_local_fallback(self) -> None:
        original = CUTTED.ai_director_camera_result

        def timeout_result(*_args: object, **_kwargs: object) -> dict[str, object]:
            return {"camera_path": [], "diagnostics": {"enabled": True, "status": "timeout", "error": "demorou demais"}}

        try:
            CUTTED.ai_director_camera_result = timeout_result
            with tempfile.TemporaryDirectory() as tmp:
                gallery = Path(tmp)
                source_path = gallery / "source.mp4"
                source_path.write_bytes(b"fake")
                payload = {
                    "ok": True,
                    "version": CUTTED.VISUAL_MAP_VERSION,
                    "source": str(source_path.resolve()),
                    "fingerprint": {"path": str(source_path.resolve())},
                    "metadata": {"width": 1920, "height": 1080, "duration": 18.0},
                    "sample_count": 8,
                    "vision_engine": "yolo-visual-map",
                    "detections": [
                        {"time": float(index * 2), "faces": [person(30.0), person(72.0)], "primary": person(30.0)}
                        for index in range(9)
                    ],
                }
                (gallery / "visual-map.json").write_text(json.dumps(payload), encoding="utf-8")
                media = CUTTED.CameraAnalysisMedia(source_path.resolve(), "cache", "source.mp4", "source", 0.0)

                result = CUTTED.visual_map_camera_analysis(gallery, media, 18.0, "ai-director", "tiktok", "", "")
        finally:
            CUTTED.ai_director_camera_result = original

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["source"], "visual-map-ai-director-fallback")
        self.assertEqual(result["diagnostics"]["ai_director"]["status"], "timeout")
        self.assertIn("fallback_quality", result["diagnostics"])
        self.assertTrue(any(str(frame.get("source") or "").startswith("ai-director") for frame in result["camera_path"]))

    def test_clip_visual_map_uses_camera_analysis_cache_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gallery = Path(tmp)
            media = CUTTED.CameraAnalysisMedia(gallery / "clips" / "clip-004.mp4", "cache", "clip-004.mp4", "clip", 0.0)

            path = CUTTED.visual_map_path_for_media(gallery, media)

        self.assertEqual(path.name, "clip-004-visual-map.json")
        self.assertEqual(path.parent.name, "camera-analysis")

    def test_camera_status_waits_for_clip_visual_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gallery = Path(tmp)
            clip = gallery / "clips" / "clip-001.mp4"
            clip.parent.mkdir()
            clip.write_bytes(b"fake")

            status = CUTTED.camera_status_from_payload(
                {"clip_file": "clips/clip-001.mp4", "mode": "ai-director", "platform": "tiktok"},
                gallery,
                start_background=False,
            )

        self.assertFalse(status["ready"])
        self.assertFalse(status["cache_ready"])
        self.assertFalse(status["visual_map"]["ready"])
        self.assertFalse(status["visual_map"]["preparing"])

    def test_camera_status_is_ready_with_clip_visual_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gallery = Path(tmp)
            clip = gallery / "clips" / "clip-001.mp4"
            clip.parent.mkdir()
            clip.write_bytes(b"fake")
            visual_map = gallery / "camera-analysis" / "clip-001-visual-map.json"
            visual_map.parent.mkdir()
            visual_map.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "version": CUTTED.VISUAL_MAP_VERSION,
                        "source": str(clip.resolve()),
                        "fingerprint": {"path": str(clip.resolve())},
                        "detections": [],
                    }
                ),
                encoding="utf-8",
            )

            status = CUTTED.camera_status_from_payload(
                {"clip_file": "clips/clip-001.mp4", "mode": "ai-director", "platform": "tiktok"},
                gallery,
                start_background=False,
            )

        self.assertTrue(status["ready"])
        self.assertFalse(status["cache_ready"])
        self.assertTrue(status["visual_map"]["ready"])

    def test_camera_status_is_ready_with_completed_ai_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gallery = Path(tmp)
            clip = gallery / "clips" / "clip-001.mp4"
            clip.parent.mkdir()
            clip.write_bytes(b"fake")
            cache_dir = gallery / "camera-analysis"
            cache_dir.mkdir()
            (cache_dir / "clip-001-ai-director-cache.json").write_text(
                json.dumps(
                    {
                        "version": CUTTED.CAMERA_ANALYSIS_VERSION,
                        "mode": "ai-director",
                        "resolution_preset": "vertical_9_16",
                        "clip_file": "clips/clip-001.mp4",
                        "camera_path": [{"time": 0.0, "x": 50.0, "zoom": 1.0}],
                        "diagnostics": {"ai_director": {"status": "applied"}},
                    }
                ),
                encoding="utf-8",
            )

            status = CUTTED.camera_status_from_payload(
                {"clip_file": "clips/clip-001.mp4", "mode": "ai-director", "platform": "tiktok"},
                gallery,
                start_background=False,
            )

        self.assertTrue(status["ready"])
        self.assertTrue(status["cache_ready"])
        self.assertFalse(status["visual_map"]["ready"])

    def test_card_preview_uses_compact_camera_timeline(self) -> None:
        moment = CUTTED.Moment(
            rank=1,
            start=0.0,
            end=12.0,
            peak=4.0,
            score=0.8,
            title="Teste",
            reason="",
            transcript="texto",
            peak_text="texto",
            clip_file="clips/clip-001.mp4",
            frame_file="frames/clip-001.jpg",
        )

        html = CUTTED.card_html(moment)

        self.assertIn("data-cuted-control-surface", html)
        self.assertIn("clip-control-surface", html)
        self.assertLess(html.index("data-cuted-control-surface"), html.index("data-preview-camera-timeline"))
        self.assertLess(html.index("data-preview-camera-timeline"), html.index("</summary>"))
        self.assertNotIn("preview-transport-group", html)
        self.assertNotIn("preview-topbar", html)
        self.assertNotIn("data-preview-format-trigger", html)
        self.assertNotIn("data-preview-format-options", html)
        self.assertNotIn("data-card-format-preview=\"tiktok\"", html)
        self.assertNotIn("data-card-format-preview=\"facebook\"", html)
        self.assertNotIn("data-card-format-preview=\"youtube\"", html)
        self.assertNotIn("data-card-format-preview=\"shorts\"", html)
        self.assertNotIn("data-card-format-preview=\"instagram\"", html)
        self.assertNotIn("Timeline do preview", html)
        self.assertIn("data-preview-camera-timeline", html)
        self.assertIn("data-card-row-timeline", html)
        self.assertIn("data-preview-audio-waveform", CUTTED.page_html("Teste", html, "{}", ""))
        self.assertNotIn("data-preview-volume", html)
        self.assertNotIn("data-preview-volume-popover", html)
        self.assertNotIn("data-preview-volume-slider", html)
        self.assertNotIn("data-camera-ai", html)
        self.assertIn("data-bumper-video=\"intro\"", html)
        self.assertIn("data-bumper-video=\"outro\"", html)
        self.assertNotIn("Smart Camera", html)
        self.assertNotIn("data-card-camera", html)
        self.assertIn("data-overlay-place-camera", CUTTED.page_html("Teste", html, "{}", ""))
        self.assertNotIn("data-preview-volume-down", html)
        self.assertNotIn("data-preview-volume-up", html)
        self.assertNotIn("data-preview-volume-zero", html)
        self.assertNotIn("data-preview-volume-value", html)

    def test_page_mounts_live_timeline_with_legacy_fallback(self) -> None:
        html = CUTTED.page_html(
            "Teste",
            "",
            "{}",
            "assets/brand/cuted-logo-transparent.png",
            {"css": "assets/live-timeline/live-timeline.css", "js": "assets/live-timeline/live-timeline.js"},
        )

        self.assertIn("function renderLivePreviewCameraTimeline", html)
        self.assertIn("window.CuttedLiveTimeline", html)
        self.assertIn("renderLegacyPreviewCameraTimeline", html)
        self.assertIn("showVolume: false", html)
        self.assertIn("function renderCardRowTimeline", html)

    def test_export_buttons_use_resolution_formats(self) -> None:
        moment = CUTTED.Moment(
            rank=1,
            start=0.0,
            end=12.0,
            peak=4.0,
            score=0.8,
            title="Teste",
            reason="",
            transcript="texto",
            peak_text="texto",
            clip_file="clips/clip-001.mp4",
            frame_file="frames/clip-001.jpg",
        )

        html = CUTTED.card_html(moment)

        page = CUTTED.page_html("Teste", html, "{}", "")

        self.assertNotIn("data-platform=\"tiktok\">Vertical 9:16", html)
        self.assertNotIn("data-platform=\"facebook\">Vertical 4:5", html)
        self.assertNotIn("data-platform=\"youtube\">Horizontal 16:9", html)
        self.assertNotIn("data-platform=\"shorts\"", html)
        self.assertNotIn("data-platform=\"instagram\"", html)
        self.assertIn("function controlSurfacePlatform", page)
        self.assertIn("function setControlSurfaceFormat", page)

    def test_volume_popover_stays_compact_above_editor_layers(self) -> None:
        html = CUTTED.page_html("Teste", "", "{}", "")

        self.assertIn(".preview-volume-group{z-index:2300}", html)
        self.assertIn(".preview-volume-popover{z-index:2600!important;width:44px!important", html)
        self.assertIn(".preview-volume-slider{width:92px!important;max-width:92px}", html)

    def test_moment_contract_includes_waveform_file(self) -> None:
        moment = CUTTED.Moment(
            rank=1,
            start=0.0,
            end=12.0,
            peak=4.0,
            score=0.8,
            title="Teste",
            reason="",
            transcript="texto",
            peak_text="texto",
            clip_file="clips/clip-001.mp4",
            frame_file="frames/clip-001.jpg",
            waveform_file="waveforms/clip-001.json",
        )

        data = CUTTED.moment_to_dict(moment)

        self.assertEqual(data["waveform_file"], "waveforms/clip-001.json")

    def test_audio_waveform_peaks_are_normalized(self) -> None:
        peaks = CUTTED.normalized_audio_peaks([0.0, 0.25, -0.25, 0.5, -0.5, 1.0, -1.0, 0.0], 4)

        self.assertEqual(len(peaks), 4)
        self.assertEqual(max(peaks), 1.0)
        self.assertGreater(peaks[-1], peaks[0])

    def test_yolo_person_box_converts_to_camera_subject(self) -> None:
        row = CUTTED.yolo_person_row_from_box([100.0, 100.0, 300.0, 800.0], 1000, 1000, 0.78)

        self.assertIsNotNone(row)
        self.assertEqual(row["kind"], "person")
        self.assertAlmostEqual(float(row["x"]), 20.0)
        self.assertAlmostEqual(float(row["y"]), 32.0)
        self.assertAlmostEqual(float(row["width"]), 20.0)
        self.assertAlmostEqual(float(row["confidence"]), 0.78)

    def test_camera_focus_biases_above_chin(self) -> None:
        row = CUTTED.face_row_from_detection(100.0, 100.0, 200.0, 300.0, 1000, 1000, 1.0, False, 1.0)

        self.assertIsNotNone(row)
        self.assertAlmostEqual(float(row["y"]), 32.0)
        self.assertEqual(CUTTED.CAMERA_ANALYSIS_VERSION, "auto-face-v31")

    def test_yolo_persons_merge_without_duplicating_opencv_faces(self) -> None:
        merged = CUTTED.merge_vision_subjects([face(42.0)], [person(43.0), person(75.0)])

        self.assertEqual(len(merged), 2)
        self.assertTrue(any(item.get("kind") == "person" and item["x"] == 75.0 for item in merged))
        self.assertTrue(any(item.get("kind") != "person" and item["x"] == 42.0 for item in merged))

    def test_vision_diagnostics_reports_person_coverage(self) -> None:
        detections = [
            {"time": 0.0, "faces": [person(30.0), person(70.0)], "persons": [person(30.0), person(70.0)]},
            {"time": 1.0, "faces": [person(50.0)], "persons": [person(50.0)]},
        ]

        result = CUTTED.vision_engine_diagnostics(detections)

        self.assertEqual(result["person_detection_frames"], 2)
        self.assertEqual(result["multi_person_frames"], 1)
        self.assertEqual(result["detected_persons_max"], 2)

    def test_ai_director_payload_includes_vision_context(self) -> None:
        detections = [
            {
                "time": 0.0,
                "faces": [face(48.0), person(74.0)],
                "opencv_faces": [face(48.0)],
                "persons": [person(74.0)],
                "primary": face(48.0),
            }
        ]

        payload = CUTTED.ai_director_user_payload("tiktok", "Teste", "", {}, detections, [], 8.0, "ai-director")
        data = CUTTED.json.loads(payload)

        self.assertIn("vision_detection_summary", data)
        self.assertIn("vision_detections", data)
        self.assertEqual(data["vision_detections"][0]["person_count"], 1)

    def test_ai_director_uses_structured_map_without_frames_when_confident(self) -> None:
        detections = [
            {
                "time": float(index),
                "faces": [person(30.0), person(70.0)],
                "persons": [person(30.0), person(70.0)],
                "primary": person(30.0),
            }
            for index in range(12)
        ]

        self.assertFalse(CUTTED.ai_director_needs_frame_samples(detections))

    def test_ai_director_requests_frames_when_visual_map_is_sparse(self) -> None:
        detections = [missing_detection(float(index)) for index in range(10)]

        self.assertTrue(CUTTED.ai_director_needs_frame_samples(detections))

    def test_vertical_destinations_share_resolution_preset(self) -> None:
        self.assertEqual(CUTTED.resolution_key_for_platform("tiktok"), "vertical_9_16")
        self.assertEqual(CUTTED.resolution_key_for_platform("shorts"), "vertical_9_16")
        self.assertEqual(CUTTED.resolution_key_for_platform("instagram"), "vertical_9_16")
        self.assertEqual(CUTTED.resolution_key_for_platform("facebook"), "vertical_4_5")
        self.assertEqual(CUTTED.resolution_key_for_platform("youtube"), "horizontal_16_9")

    def test_platform_viewport_includes_resolution_context(self) -> None:
        viewport = CUTTED.platform_viewport("shorts")

        self.assertEqual(viewport["resolution_preset"], "vertical_9_16")
        self.assertEqual(viewport["resolution_label"], "Vertical 9:16")
        self.assertEqual(viewport["shared_destinations"], ["tiktok", "shorts", "instagram"])

    def test_normalize_platforms_dedupes_shared_resolution_formats(self) -> None:
        platforms = CUTTED.normalize_platforms(["tiktok", "shorts", "instagram", "facebook", "youtube"])

        self.assertEqual(platforms, ["tiktok", "facebook", "youtube"])

    def test_caption_queue_takes_priority_over_legacy_selected_rows(self) -> None:
        row = {"rank": 1, "platform": "tiktok", "resolution_preset": "vertical_9_16"}
        data = {
            "caption_queue": [row],
            "selected": [{"rank": 1, "platforms": ["tiktok", "shorts", "instagram"]}],
        }

        self.assertEqual(CUTTED.caption_rows_from_data(data), [row])

    def test_page_exports_resolution_workspace_contract(self) -> None:
        html = CUTTED.page_html("Teste", "", "{}", "assets/brand/cuted-logo-transparent.png")

        self.assertIn("const resolutionPresets", html)
        self.assertIn("destination_resolution_map", html)
        self.assertIn("resolution_edits", html)
        self.assertIn("Direcione este formato uma vez", html)

    def test_director_plan_from_camera_path_labels_shots(self) -> None:
        path = [
            {"time": 0.0, "x": 50.0, "y": 50.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-group-fit"},
            {"time": 4.0, "x": 48.0, "y": 50.0, "zoom": 1.22, "source": "ai-director"},
            {"time": 8.0, "x": 72.0, "y": 50.0, "zoom": 1.16, "source": "ai-director-cuts-primary"},
        ]

        plan = CUTTED.director_plan_from_camera_path(path, 12.0, "instagram", "ai-director", "ai-director")

        self.assertEqual(plan["resolution_preset"], "vertical_9_16")
        self.assertEqual([shot["label"] for shot in plan["shots"]], ["Group", "Speaker", "Cut"])
        self.assertEqual(plan["shots"][0]["end"], 4.0)

    def test_ai_director_schema_requires_director_plan(self) -> None:
        schema = CUTTED.ai_director_schema()

        self.assertIn("director_plan", schema["required"])
        self.assertIn("director_plan", schema["properties"])
        self.assertIn("shots", schema["properties"]["director_plan"]["required"])

    def test_director_plan_converts_to_camera_path(self) -> None:
        payload = {
            "director_plan": {
                "style": "normal",
                "energy": "normal",
                "shots": [
                    {
                        "id": "shot-001",
                        "start": 0.0,
                        "end": 4.0,
                        "intent": "speaker_close",
                        "label": "Speaker",
                        "subject": "primary",
                        "transition": "smooth",
                        "reason": "Hook",
                    },
                    {
                        "id": "shot-002",
                        "start": 4.0,
                        "end": 8.0,
                        "intent": "reaction_focus",
                        "label": "Reaction",
                        "subject": "secondary",
                        "transition": "smooth",
                        "reason": "Reaction",
                    },
                ],
            }
        }
        detections = [detection(0.0, [face(42.0), face(72.0)]), detection(4.0, [face(42.0), face(72.0)])]

        plan = CUTTED.validated_ai_director_plan(payload, 8.0, "tiktok", "ai-director")
        path = CUTTED.camera_path_from_director_plan(plan, detections, 8.0, "tiktok", "ai-director")

        self.assertEqual(plan["resolution_preset"], "vertical_9_16")
        self.assertEqual(len(path), 2)
        self.assertEqual(path[0]["intent"], "speaker_close")
        self.assertEqual(path[1]["intent"], "reaction_focus")

    def test_ai_director_cache_scope_uses_resolution_preset(self) -> None:
        self.assertEqual(CUTTED.camera_analysis_cache_scope("tiktok", "ai-director"), "vertical_9_16")
        self.assertEqual(CUTTED.camera_analysis_cache_scope("shorts", "ai-director"), "vertical_9_16")
        self.assertEqual(CUTTED.camera_analysis_cache_scope("instagram", "ai-director"), "vertical_9_16")
        self.assertEqual(CUTTED.camera_analysis_cache_scope("instagram", "auto-director"), "instagram")

    def test_page_includes_director_plan_timeline_helpers(self) -> None:
        html = CUTTED.page_html("Teste", "", "{}", "assets/brand/cuted-logo-transparent.png")

        self.assertIn("function directorPlanFromCameraPath", html)
        self.assertIn("directorMarkerLabel", html)
        self.assertIn("director_plan: normalizeDirectorPlan", html)

    def test_preview_timeline_has_director_edit_menu_actions(self) -> None:
        html = CUTTED.page_html("Teste", "", "{}", "assets/brand/cuted-logo-transparent.png")

        self.assertIn("data-preview-camera-popover-intent", html)
        self.assertIn("data-preview-camera-popover-add", html)
        self.assertIn("data-preview-camera-popover-continue", html)
        self.assertIn("data-preview-camera-popover-delete", html)
        self.assertIn("data-preview-camera-popover-close", html)
        self.assertIn("preview-camera-popover-aura", html)
        self.assertNotIn("data-preview-camera-popover-move", html)
        self.assertIn("preview-camera-popover-close", html)
        self.assertIn("updateCameraPathFrameIntentForCard", html)
        self.assertIn("addCameraIntentFrameForCard", html)

    def test_director_speaker_focus_uses_medium_zoom(self) -> None:
        row = detection(0.0, [face(42.0, width=4.0), face(72.0, width=4.0)])

        speaker = CUTTED.director_primary_frame(row, 0.0)
        reaction = CUTTED.director_reaction_frame(row, 3.0)

        self.assertIsNotNone(speaker)
        self.assertIsNotNone(reaction)
        self.assertLessEqual(float(speaker["zoom"]), 1.16)
        self.assertGreater(float(reaction["zoom"]), float(speaker["zoom"]))

    def test_speaker_focus_prefers_real_face_over_person_box(self) -> None:
        body = person(88.0, width=24.0)
        real_face = face(46.0, width=5.0)
        row = {
            "time": 0.0,
            "faces": [body, real_face],
            "persons": [body],
            "primary": body,
        }

        speaker = CUTTED.director_primary_frame(row, 0.0)

        self.assertIsNotNone(speaker)
        self.assertAlmostEqual(float(speaker["x"]), 46.0)
        self.assertLessEqual(float(speaker["zoom"]), 1.1)

    def test_speaker_focus_can_use_yolo_person_when_face_is_missing(self) -> None:
        left_face = face(34.0, width=5.0)
        right_body = person(70.0, width=20.0)
        row = {
            "time": 0.0,
            "faces": [left_face, right_body],
            "opencv_faces": [left_face],
            "persons": [right_body],
            "primary": right_body,
        }

        speaker = CUTTED.director_primary_frame(row, 0.0)

        self.assertIsNotNone(speaker)
        self.assertAlmostEqual(float(speaker["x"]), 70.0)
        self.assertEqual(speaker["intent"], "speaker_hold")
        self.assertLessEqual(float(speaker["zoom"]), 1.08)

    def test_long_group_view_gets_reaction_breakaway(self) -> None:
        frames = [
            {
                "time": 0.0,
                "x": 50.0,
                "y": 50.0,
                "zoom": 1.0,
                "intent": "group_open",
                "source": "ai-director-plan-group_open",
            }
        ]
        detections = [detection(4.0, [face(28.0), face(55.0), face(74.0)])]

        result = CUTTED.group_breakaway_camera_frames(frames, detections, 14.0, "tiktok")
        sources = [frame["source"] for frame in result]

        self.assertEqual(sources, [
            "ai-director-cuts-group-speaker",
            "ai-director-cuts-group-reaction",
            "ai-director-cuts-group-return",
        ])
        self.assertEqual(result[0]["intent"], "speaker_hold")
        self.assertEqual(result[1]["intent"], "reaction_focus")
        self.assertGreaterEqual(float(result[1]["time"]) - float(result[0]["time"]), 4.1)

    def test_dynamic_group_breakaway_avoids_cut_sources(self) -> None:
        frames = [{"time": 0.0, "x": 50.0, "y": 50.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-group-fit"}]
        detections = [detection(4.0, [face(30.0), face(55.0), face(72.0)])]

        result = CUTTED.group_breakaway_camera_frames(frames, detections, 14.0, "tiktok", False, include_fit=True)
        sources = [frame["source"] for frame in result]

        self.assertEqual(sources, [
            "ai-director-dynamic-group-speaker",
            "ai-director-dynamic-group-reaction",
            "ai-director-dynamic-group",
        ])

    def test_missing_speaker_side_gets_medium_speaker_frame(self) -> None:
        frames = [
            {"time": 0.0, "x": 36.0, "y": 50.0, "zoom": 1.08, "intent": "speaker_hold", "source": "ai-director"},
            {"time": 6.0, "x": 72.0, "y": 50.0, "zoom": 1.14, "intent": "reaction_focus", "source": "ai-director"},
        ]
        detections = [
            detection(3.0, [face(34.0), face(72.0)]),
            detection(9.0, [face(35.0), face(73.0)]),
        ]

        result = CUTTED.speaker_side_coverage_camera_frames(frames, detections, 12.0, "tiktok", False)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["intent"], "speaker_hold")
        self.assertGreater(float(result[0]["x"]), 58.0)
        self.assertLessEqual(float(result[0]["zoom"]), 1.08)

    def test_dominant_group_balance_inserts_active_frames(self) -> None:
        frames = [
            {"time": 0.0, "x": 50.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 6.0, "x": 51.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 12.0, "x": 49.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 18.0, "x": 52.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 24.0, "x": 48.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
        ]
        detections = [detection(float(index * 2), [face(30.0), face(72.0)]) for index in range(15)]

        result = CUTTED.dominant_group_balance_camera_frames(frames, detections, 30.0, "tiktok", False)

        self.assertGreaterEqual(len(result), 3)
        self.assertTrue(any(frame["intent"] == "speaker_hold" for frame in result))
        self.assertTrue(any(frame["intent"] == "reaction_focus" for frame in result))

    def test_soft_group_returns_do_not_interrupt_focus_chain(self) -> None:
        frames = [
            {"time": 0.0, "x": 35.0, "zoom": 1.08, "intent": "speaker_hold", "source": "ai-director-dynamic-speaker"},
            {"time": 2.0, "x": 50.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 4.5, "x": 70.0, "zoom": 1.14, "intent": "reaction_focus", "source": "ai-director-dynamic-reaction"},
            {"time": 6.0, "x": 50.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-dynamic-group"},
            {"time": 9.5, "x": 50.0, "zoom": 1.0, "fit": "contain", "source": "ai-director-cuts-group-fit"},
        ]

        result = CUTTED.suppress_soft_group_returns(frames)

        self.assertEqual([frame["time"] for frame in result], [0.0, 4.5, 9.5])
        self.assertEqual(result[-1]["source"], "ai-director-cuts-group-fit")

    def test_dynamic_editorial_path_caps_zoom_and_rejects_edge_focus(self) -> None:
        frames = [
            {"time": 0.0, "x": 12.0, "y": 50.0, "zoom": 1.34, "source": "ai-director-cuts-distant"},
            {"time": 3.0, "x": 56.0, "y": 50.0, "zoom": 1.3, "source": "ai-director-cuts-reaction"},
            {"time": 6.5, "x": 48.0, "y": 50.0, "zoom": 1.24, "source": "ai-director-cuts-primary"},
        ]
        detections = [detection(0.0, [face(28.0), face(72.0)]), detection(3.0, [face(44.0), face(58.0)])]

        result = CUTTED.dynamic_editorial_camera_path(frames, detections, 10.0, "tiktok")

        self.assertTrue(all("cuts" not in str(frame["source"]) for frame in result))
        self.assertTrue(all(float(frame["zoom"]) <= 1.16 for frame in result))
        self.assertTrue(all(20.0 <= float(frame["x"]) <= 80.0 for frame in result))

    def test_solo_dominant_scene_removes_hard_cut_jitter(self) -> None:
        detections = [
            detection(0.0, [face(48.0)]),
            detection(2.0, [face(50.0)]),
            detection(4.0, [face(52.0)]),
            detection(6.0, [face(54.0)]),
            detection(8.0, [face(53.0)]),
        ]
        frames = [
            {"time": 0.0, "x": 46.0, "y": 50.0, "zoom": 1.18, "source": "ai-director-cuts"},
            {"time": 2.0, "x": 58.0, "y": 50.0, "zoom": 1.2, "source": "ai-director-cuts"},
            {"time": 4.0, "x": 45.0, "y": 50.0, "zoom": 1.16, "source": "ai-director-cuts"},
        ]

        result = CUTTED.enforce_editorial_motion_rules(frames, detections, 10.0, "tiktok", False)

        self.assertGreaterEqual(len(result), 1)
        self.assertLessEqual(len(result), 3)
        self.assertTrue(all(frame["source"] == "ai-director-solo" for frame in result))

    def test_edge_heavy_solo_scene_keeps_ai_director_path(self) -> None:
        detections = [
            detection(0.0, [face(78.0)]),
            detection(2.0, [face(80.0)]),
            detection(4.0, [face(82.0)]),
            detection(6.0, [face(79.0)]),
            detection(8.0, [face(81.0)]),
        ]
        frames = [
            {"time": 0.0, "x": 50.0, "y": 50.0, "zoom": 1.0, "source": "ai-director"},
            {"time": 2.0, "x": 78.0, "y": 50.0, "zoom": 1.16, "source": "ai-director-dense-primary"},
            {"time": 5.0, "x": 80.0, "y": 50.0, "zoom": 1.16, "source": "ai-director-dense-primary"},
        ]

        result = CUTTED.enforce_editorial_motion_rules(frames, detections, 10.0, "tiktok", False)

        self.assertEqual(result, frames)
        self.assertTrue(all(frame["source"] != "ai-director-solo" for frame in result))

    def test_low_confidence_scene_forces_fit_even_when_center_is_open(self) -> None:
        detections = [
            missing_detection(0.0),
            missing_detection(3.0),
            missing_detection(6.0),
            missing_detection(9.0),
            missing_detection(12.0),
            missing_detection(15.0),
            missing_detection(18.0),
            missing_detection(21.0),
            detection(24.0, [face(81.0)]),
            missing_detection(27.0),
            missing_detection(30.0),
        ]
        frames = [
            {"time": 0.0, "x": 50.0, "y": 50.0, "zoom": 1.0, "source": "ai-director"},
            {"time": 12.0, "x": 50.0, "y": 48.0, "zoom": 1.02, "source": "ai-director"},
        ]

        result = CUTTED.uncertain_center_camera_frames(frames, detections, 30.0, False)
        times = [frame["time"] for frame in result]

        self.assertIn(0.0, times)
        self.assertIn(6.0, times)
        self.assertIn(12.0, times)
        self.assertTrue(all(frame["fit"] == "contain" for frame in result))

    def test_long_fit_block_gets_short_face_breakaways(self) -> None:
        frames = [
            {
                "time": 0.0,
                "x": 50.0,
                "y": 50.0,
                "zoom": 1.0,
                "fit": "contain",
                "source": "ai-director-uncertain-fit",
            },
            {
                "time": 6.0,
                "x": 50.0,
                "y": 50.0,
                "zoom": 1.0,
                "fit": "contain",
                "source": "ai-director-uncertain-fit",
            },
            {
                "time": 12.0,
                "x": 50.0,
                "y": 50.0,
                "zoom": 1.0,
                "fit": "contain",
                "source": "ai-director-uncertain-fit",
            },
            {"time": 34.0, "x": 52.0, "y": 48.0, "zoom": 1.08, "source": "ai-director"},
        ]
        detections = [
            detection(5.0, [face(28.0), face(72.0)]),
            detection(18.5, [face(30.0), face(70.0)]),
        ]

        result = CUTTED.fit_breakaway_camera_frames(frames, detections, 38.0)
        sources = [frame["source"] for frame in result]

        self.assertEqual(sources.count("ai-director-cuts-fit-primary"), 2)
        self.assertEqual(sources.count("ai-director-cuts-fit-secondary"), 2)
        self.assertEqual(sources.count("ai-director-cuts-fit-return"), 2)
        self.assertTrue(all(result[index]["fit"] == "contain" for index in [2, 5]))

    def test_single_face_fit_breakaway_holds_primary_then_returns(self) -> None:
        frames = [
            {
                "time": 0.0,
                "x": 50.0,
                "y": 50.0,
                "zoom": 1.0,
                "fit": "contain",
                "source": "ai-director-uncertain-fit",
            },
            {"time": 16.0, "x": 52.0, "y": 48.0, "zoom": 1.08, "source": "ai-director"},
        ]
        result = CUTTED.fit_breakaway_camera_frames(frames, [detection(5.0, [face(42.0)])], 20.0)
        sources = [frame["source"] for frame in result]

        self.assertEqual(sources, ["ai-director-cuts-fit-primary", "ai-director-cuts-fit-return"])
        self.assertAlmostEqual(float(result[1]["time"]) - float(result[0]["time"]), 4.4, places=1)

    def test_fit_close_survives_merge_with_uncertain_fit(self) -> None:
        fit = {
            "time": 5.0,
            "x": 50.0,
            "y": 50.0,
            "zoom": 1.0,
            "fit": "contain",
            "source": "ai-director-uncertain-fit",
        }
        close = {
            "time": 5.2,
            "x": 32.0,
            "y": 48.0,
            "zoom": 1.24,
            "source": "ai-director-cuts-fit-primary",
        }

        result = CUTTED.merge_camera_path_frames([fit], [close], 12.0)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "ai-director-cuts-fit-primary")

    def test_short_or_empty_fit_block_does_not_invent_breakaways(self) -> None:
        frames = [
            {
                "time": 0.0,
                "x": 50.0,
                "y": 50.0,
                "zoom": 1.0,
                "fit": "contain",
                "source": "ai-director-uncertain-fit",
            },
            {"time": 8.0, "x": 55.0, "y": 50.0, "zoom": 1.1, "source": "ai-director"},
        ]

        short_result = CUTTED.fit_breakaway_camera_frames(frames, [detection(4.0, [face(55.0)])], 12.0)
        empty_result = CUTTED.fit_breakaway_camera_frames(frames, [missing_detection(4.0)], 24.0)

        self.assertEqual(short_result, [])
        self.assertEqual(empty_result, [])

    def test_close_two_face_transition_stays_smooth(self) -> None:
        detections = [
            detection(0.0, [face(47.0), face(54.0)]),
            detection(2.5, [face(48.0), face(55.0)]),
            detection(5.0, [face(49.0), face(56.0)]),
        ]
        frames = [
            {"time": 0.0, "x": 48.0, "y": 50.0, "zoom": 1.14, "source": "ai-director"},
            {"time": 5.0, "x": 56.0, "y": 50.0, "zoom": 1.14, "source": "ai-director"},
        ]

        result = CUTTED.enforce_editorial_motion_rules(frames, detections, 6.0, "tiktok", False)

        self.assertEqual(len(result), 2)
        self.assertTrue(all("ai-director-cuts" not in str(frame["source"]) for frame in result))

    def test_far_two_face_transition_becomes_hard_cut(self) -> None:
        detections = [
            detection(0.0, [face(24.0), face(76.0)]),
            detection(2.5, [face(23.0), face(77.0)]),
            detection(5.0, [face(24.0), face(76.0)]),
        ]
        frames = [
            {"time": 0.0, "x": 25.0, "y": 50.0, "zoom": 1.18, "source": "ai-director"},
            {"time": 5.0, "x": 75.0, "y": 50.0, "zoom": 1.18, "source": "ai-director"},
        ]

        result = CUTTED.enforce_editorial_motion_rules(frames, detections, 6.0, "tiktok", False)

        self.assertEqual(result[0]["source"], "ai-director-cuts-hold")
        self.assertEqual(result[1]["source"], "ai-director-cuts-distant")

    def test_camera_cache_bypass_is_limited_to_ai_modes(self) -> None:
        payload = {"force_refresh": True}

        self.assertTrue(CUTTED.camera_analysis_bypasses_cache(payload, "ai-director"))
        self.assertTrue(CUTTED.camera_analysis_bypasses_cache(payload, "ai-director-cuts"))
        self.assertFalse(CUTTED.camera_analysis_bypasses_cache(payload, "auto-director"))
        self.assertFalse(CUTTED.camera_analysis_bypasses_cache({}, "ai-director"))

    def test_preview_holds_before_upcoming_hard_cut_or_fit(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        self.assertIn("cameraFrameUsesHardCut(next)", source)
        self.assertIn("cameraFrameUsesGroupFit(next)", source)

    def test_preview_camera_motion_uses_slower_smooth_transition(self) -> None:
        html = CUTTED.page_html("Teste", "", "{}", "assets/brand/cuted-logo-transparent.png")

        self.assertIn("object-position var(--camera-transition-ms,700ms) cubic-bezier(.22,.61,.36,1)", html)
        self.assertIn("transform var(--camera-transition-ms,700ms) cubic-bezier(.22,.61,.36,1)", html)

    def test_manual_fit_blur_uses_group_fit_contract(self) -> None:
        frame = CUTTED.default_camera_path_frame({"key": "fit-blur", "strength": 60}, 0.0)
        html = CUTTED.page_html("Teste", "", "{}", "assets/brand/cuted-logo-transparent.png")

        self.assertEqual(frame["key"], "fit-blur")
        self.assertEqual(frame["fit"], "contain")
        self.assertIn('"fit-blur"', html)
        self.assertIn("Fit com blur", html)

    def test_platform_edit_from_row_includes_bumpers(self) -> None:
        row = {
            "platform_edits": {
                "tiktok": {
                    "bumpers": {
                        "intro": {
                            "label": "intro.mp4",
                            "asset_file": "bumper-assets/intro.mp4",
                            "width": 1080,
                            "height": 1920,
                            "duration": 2.5,
                        }
                    }
                }
            }
        }

        edit = CUTTED.platform_edit_from_row(row, "tiktok")

        self.assertIn("bumpers", edit)
        self.assertEqual(edit["bumpers"]["intro"]["asset_file"], "bumper-assets/intro.mp4")

    def test_platform_edit_from_row_falls_back_to_resolution_edit(self) -> None:
        row = {
            "resolution_edits": {
                "vertical_9_16": {
                    "camera_path": [{"time": 0.0, "x": 50.0, "y": 50.0, "zoom": 1.0}],
                    "effect": {"key": "none"},
                }
            }
        }

        edit = CUTTED.platform_edit_from_row(row, "instagram")

        self.assertIn("camera_path", edit)
        self.assertEqual(edit["effect"]["key"], "none")

    def test_normalize_bumpers_filters_empty_slots(self) -> None:
        row = {
            "bumpers": {
                "intro": {"label": "intro.mp4", "asset_file": "bumper-assets/intro.mp4", "width": 1080, "height": 1920},
                "outro": {"label": "missing.mp4"},
            }
        }

        bumpers = CUTTED.normalize_bumpers_from_row(row)

        self.assertEqual(list(bumpers), ["intro"])
        self.assertEqual(bumpers["intro"]["slot"], "intro")

    def test_decode_data_url_video_accepts_mp4(self) -> None:
        payload = base64.b64encode(b"tiny-video").decode("ascii")

        data, extension = CUTTED.decode_data_url_video(f"data:video/mp4;base64,{payload}")

        self.assertEqual(data, b"tiny-video")
        self.assertEqual(extension, "mp4")


if __name__ == "__main__":
    unittest.main()
