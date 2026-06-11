from __future__ import annotations

import importlib.util
import sys
import tempfile
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

    def test_import_request_metadata_requires_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "link ou caminho local"):
            CUTTED.import_request_metadata({"output_path": "C:\\videos"})

    def test_import_request_metadata_requires_destination(self) -> None:
        with self.assertRaisesRegex(ValueError, "pasta onde os videos finais"):
            CUTTED.import_request_metadata({"source_path": "video.mp4"})


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
            self.assertIn("data-import-form", html)
            self.assertIn('{"moments": []}', html)

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
            self.assertIn('name="source_path"', html)
            self.assertIn('{"moments": []}', html)

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
