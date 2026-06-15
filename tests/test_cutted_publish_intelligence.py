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


def raw_podcast_moment() -> CUTTED.Moment:
    return CUTTED.Moment(
        rank=2,
        start=44.0,
        end=70.0,
        peak=50.0,
        score=0.88,
        title=">> Já até queimado, né? Porque é 400 V",
        reason="Discussao sobre cobranca e clima tenso.",
        transcript=">> Já até queimado, né? Porque é 400 V. A Tati Cariani cobrou o Bistecone e o Toguro na frente de todo mundo.",
        peak_text=">> A Tati Cariani cobrou o Bistecone",
        clip_file="clips/clip-002.mp4",
        frame_file="frames/clip-002.jpg",
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

    def test_fallback_cleans_transcript_markers_and_uses_origin_context(self) -> None:
        context = CUTTED.PublishSourceContext(
            label="TATI CARIANI COBROU BISTECONE E TOGURO",
            kind="youtube",
            title="TATI CARIANI COBROU BISTECONE E TOGURO - O CLIMA ESQUENTOU",
            user_context="Priorize tensao e nomes citados.",
            source_url="https://youtube.example/watch",
        )

        [moment] = CUTTED.fallback_publish_intelligence([raw_podcast_moment()], context, "local-fallback")
        metadata = moment.publish_metadata or {}
        joined = " ".join(str(metadata.get(key) or "") for key in ("title", "hook", "description"))

        self.assertNotIn(">>", joined)
        self.assertIn("#Tati", metadata["hashtags"])
        self.assertIn("#Cariani", metadata["hashtags"])
        self.assertNotIn("#IA", metadata["hashtags"])

    def test_clean_publish_line_normalizes_broken_punctuation(self) -> None:
        cleaned = CUTTED.clean_publish_line(">> Então,?  isso  aconteceu!!", "", 80)

        self.assertEqual(cleaned, "Isso aconteceu!")

    def test_fallback_hook_avoids_weak_ending(self) -> None:
        hook = CUTTED.fallback_publish_hook("Não, não tem. Na verdade, tem que", "Tati cobrou Bistecone")

        self.assertEqual(hook, "Tati cobrou Bistecone?")

    def test_source_title_hashtags_preserve_youtube_context(self) -> None:
        tags = CUTTED.source_title_hashtags("TATI CARIANI COBROU BISTECONE E TOGURO - O CLIMA ESQUENTOU", 5)

        self.assertEqual(tags, ["#Tati", "#Cariani", "#Bistecone", "#Toguro", "#ClimaEsquentou"])


if __name__ == "__main__":
    unittest.main()
