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


if __name__ == "__main__":
    unittest.main()
