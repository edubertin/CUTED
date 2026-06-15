from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "cutted" / "scripts" / "cutted.py"
SPEC = importlib.util.spec_from_file_location("cutted_publish_intelligence_test_module", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load cutted.py for publish intelligence tests.")
CUTTED = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CUTTED
SPEC.loader.exec_module(CUTTED)


def sample_moment() -> CUTTED.Moment:
    return CUTTED.Moment(
        rank=1,
        start=10.0,
        end=38.0,
        peak=18.0,
        score=0.91,
        title="IA muda o trabalho",
        reason="Trecho com uma tese clara.",
        transcript="A inteligencia artificial esta mudando o trabalho criativo de um jeito muito rapido.",
        peak_text="Voce ainda vai trabalhar junto com IA",
        clip_file="clips/clip-001.mp4",
        frame_file="frames/clip-001.jpg",
    )


class PublishIntelligenceTests(unittest.TestCase):
    def test_fallback_publish_intelligence_populates_moment_metadata(self) -> None:
        [moment] = CUTTED.fallback_publish_intelligence([sample_moment()], "Podcast de IA", "local-fallback")

        metadata = moment.publish_metadata or {}

        self.assertEqual(metadata["version"], "publish-intelligence-v1")
        self.assertIn("#IA", metadata["hashtags"])
        self.assertEqual(metadata["cover"]["selected_frame"], "frames/clip-001.jpg")
        self.assertEqual(metadata["trend_context"]["search_budget"], "single")

    def test_merge_publish_intelligence_uses_ai_payload_with_cover_frame(self) -> None:
        payload = {
            "trend_context": {
                "query": "trends IA trabalho criativo",
                "summary": "IA aplicada ao trabalho segue forte.",
                "matched_terms": ["IA", "trabalho"],
                "source_urls": ["https://example.com/trend"],
                "confidence": 0.7,
            },
            "clips": [{
                "rank": 1,
                "hook": "A IA vai mudar seu trabalho?",
                "title": "IA e trabalho criativo",
                "description": "Um corte direto sobre colaboracao com IA.",
                "hashtags": ["#IA", "#TrabalhoCriativo"],
                "cover": {
                    "selected_frame": "frames/clip-001.jpg",
                    "candidates": ["frames/clip-001.jpg"],
                    "reason": "Melhor expressao do pico.",
                },
                "confidence": 0.8,
            }],
        }

        [moment] = CUTTED.merge_publish_intelligence([sample_moment()], payload, "openai-web")
        metadata = moment.publish_metadata or {}

        self.assertEqual(metadata["hook"], "A IA vai mudar seu trabalho?")
        self.assertIn("#TrabalhoCriativo", metadata["hashtags"])
        self.assertEqual(metadata["trend_context"]["source"], "openai-web")

    def test_card_html_renders_publish_side_panels(self) -> None:
        [moment] = CUTTED.fallback_publish_intelligence([sample_moment()], "Podcast de IA", "local-fallback")

        html = CUTTED.card_html(moment)

        self.assertIn('data-publish-panel="cover"', html)
        self.assertIn('data-publish-panel="copy"', html)
        self.assertIn("Publicacao IA", html)
        self.assertIn("frames/clip-001.jpg", html)


if __name__ == "__main__":
    unittest.main()
