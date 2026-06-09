from __future__ import annotations

import importlib.util
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


def detection(time_value: float, faces: list[dict[str, float]]) -> dict[str, object]:
    primary = max(faces, key=lambda item: float(item["area"])) if faces else None
    return {"time": time_value, "faces": faces, "primary": primary}


def missing_detection(time_value: float) -> dict[str, object]:
    return {"time": time_value, "faces": [], "primary": None, "missing": True}


class CuttedCameraRuleTests(unittest.TestCase):
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
            {"time": 20.0, "x": 52.0, "y": 48.0, "zoom": 1.08, "source": "ai-director"},
        ]
        detections = [
            detection(5.0, [face(28.0), face(72.0)]),
            detection(12.5, [face(30.0), face(70.0)]),
        ]

        result = CUTTED.fit_breakaway_camera_frames(frames, detections, 24.0)
        sources = [frame["source"] for frame in result]

        self.assertEqual(sources.count("ai-director-cuts-fit-close"), 2)
        self.assertEqual(sources.count("ai-director-cuts-fit-return"), 2)
        self.assertTrue(all(result[index]["fit"] == "contain" for index in [1, 3]))

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


if __name__ == "__main__":
    unittest.main()
