from __future__ import annotations

import importlib.util
import base64
import sys
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

        self.assertIn("preview-transport-group", html)
        self.assertIn("preview-topbar", html)
        self.assertLess(html.index("preview-transport-group"), html.index("preview-format-menu"))
        self.assertIn("data-preview-format-trigger", html)
        self.assertIn("data-preview-format-options", html)
        self.assertIn("data-preview-camera-timeline", html)
        self.assertIn("data-preview-audio-waveform", CUTTED.page_html("Teste", html, "{}", ""))
        self.assertIn("data-preview-volume", html)
        self.assertIn("data-preview-volume-popover", html)
        self.assertIn("data-preview-volume-slider", html)
        self.assertIn("data-overlay-place-camera", CUTTED.page_html("Teste", html, "{}", ""))
        self.assertNotIn("data-preview-volume-down", html)
        self.assertNotIn("data-preview-volume-up", html)
        self.assertNotIn("data-preview-volume-zero", html)
        self.assertNotIn("data-preview-volume-value", html)

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
        self.assertGreaterEqual(float(row["y"]), 35.0)
        self.assertAlmostEqual(float(row["width"]), 20.0)
        self.assertAlmostEqual(float(row["confidence"]), 0.78)

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

    def test_page_exports_resolution_workspace_contract(self) -> None:
        html = CUTTED.page_html("Teste", "", "{}", "assets/brand/cuted-logo-transparent.png")

        self.assertIn("const resolutionPresets", html)
        self.assertIn("destination_resolution_map", html)
        self.assertIn("resolution_edits", html)
        self.assertIn("Direcione este formato uma vez", html)

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
        self.assertAlmostEqual(float(result[1]["time"]) - float(result[0]["time"]), 3.8, places=1)

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
