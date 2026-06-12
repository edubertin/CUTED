from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "cutted" / "scripts" / "cutted.py"
SPEC = importlib.util.spec_from_file_location("cutted_project_home_test_module", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load cutted.py for project home tests.")
CUTTED = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CUTTED
SPEC.loader.exec_module(CUTTED)


class CuttedProjectHomeTests(unittest.TestCase):
    def test_project_catalog_round_trip_keeps_recent_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "projects.json"

            CUTTED.upsert_project_catalog_entry(
                {"id": "older", "title": "Older", "path": str(Path(tmp) / "older"), "last_opened_at": "2026-01-01T00:00:00"},
                catalog_path,
            )
            CUTTED.upsert_project_catalog_entry(
                {"id": "newer", "title": "Newer", "path": str(Path(tmp) / "newer"), "last_opened_at": "2026-02-01T00:00:00"},
                catalog_path,
            )

            catalog = CUTTED.read_project_catalog(catalog_path)
            projects = catalog["projects"]

            self.assertEqual(catalog["version"], CUTTED.PROJECT_CATALOG_VERSION)
            self.assertEqual([item["id"] for item in projects], ["newer", "older"])

    def test_project_catalog_recovers_from_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "projects.json"
            catalog_path.write_text("{invalid", encoding="utf-8")

            catalog = CUTTED.read_project_catalog(catalog_path)

            self.assertEqual(catalog, CUTTED.empty_project_catalog())

    def test_project_home_html_is_clean_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            project_dir = workspace / "_imports" / "sample"
            project_dir.mkdir(parents=True)
            recent = [{
                "id": "sample",
                "title": "Sample",
                "path": str(project_dir),
                "url": "/_imports/sample/index.html",
                "clip_count": 3,
                "render_count": 1,
                "size_bytes": 2048,
            }]

            html = CUTTED.project_home_html(workspace, "assets/brand/cuted-logo-transparent.png", recent)

            self.assertIn("data-project-home", html)
            self.assertIn("Novo projeto", html)
            self.assertIn("data-home-import", html)
            self.assertIn("data-project-list", html)
            self.assertIn("id=\"open-settings\"", html)
            self.assertIn("data-settings-modal", html)
            self.assertIn("data-import-loading", html)
            self.assertIn("data-import-loading-message", html)
            self.assertIn("project-table-head", html)
            self.assertIn("project-row", html)
            self.assertIn("Sample", html)
            self.assertNotIn("data-tab=\"edit\"", html)
            self.assertNotIn("1. Importar", html)
            self.assertNotIn("project-intro", html)

    def test_project_home_shows_mock_rows_without_real_projects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)

            html = CUTTED.project_home_html(workspace, "assets/brand/cuted-logo-transparent.png", [])

            self.assertIn("home-brand-logo", html)
            self.assertIn("data-project-mock=\"true\"", html)
            self.assertEqual(html.count('data-project-id="mock-'), 4)
            self.assertIn("Podcast cortes virais", html)
            self.assertIn("data-new-project", html)
            self.assertIn("data-open-workspace", html)
            self.assertIn("mockProjects", html)

    def test_project_home_new_project_state_uses_compact_import_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)

            html = CUTTED.project_home_html(workspace, "assets/brand/cuted-logo-transparent.png", [])

            self.assertIn('data-project-library', html)
            self.assertIn('data-show-projects', html)
            self.assertIn('name="source_mode" type="radio" value="local"', html)
            self.assertIn('aria-label="Video local" checked', html)
            self.assertIn('name="source_mode" type="radio" value="youtube"', html)
            self.assertIn('aria-label="YouTube"', html)
            self.assertIn('new-project-config-grid', html)
            self.assertIn('source-config-block', html)
            self.assertIn('tuning-config-block', html)
            self.assertIn('new-project-block-title', html)
            self.assertIn('<strong>Midia</strong>', html)
            self.assertIn('<strong>Cortes</strong>', html)
            self.assertIn('<strong>Local</strong>', html)
            self.assertIn('<strong>YouTube</strong>', html)
            self.assertIn('Sugestoes e duracao', html)
            self.assertIn('cut-count-field', html)
            self.assertIn('Quantidade</span>', html)
            self.assertIn('aria-label="Quantidade de cortes"', html)
            self.assertIn('duration-option-long', html)
            self.assertIn('data-source-panel="local"', html)
            self.assertIn('data-source-panel="youtube"', html)
            self.assertIn('data-cuted-icon="local-video"', html)
            self.assertIn('data-cuted-icon="youtube"', html)
            self.assertIn('data-cuted-icon="folder-video"', html)
            self.assertIn('data-cuted-icon="mic"', html)
            self.assertIn('title="Curto: 20 a 45 segundos"', html)
            self.assertIn('title="Medio: 30 a 70 segundos"', html)
            self.assertIn('title="Longo: 60 a 120 segundos"', html)
            self.assertIn('<strong>S</strong>', html)
            self.assertIn('<strong>M</strong>', html)
            self.assertIn('<strong>L</strong>', html)
            self.assertIn('<small>20-45s</small>', html)
            self.assertIn('<small>30-70s</small>', html)
            self.assertIn('<small>60-120s</small>', html)
            self.assertNotIn('data-cuted-icon="clock"', html)
            self.assertIn('import-submit-button', html)
            self.assertIn('data-context-audio', html)
            self.assertNotIn('>Audio</button>', html)
            self.assertIn('data-import-key-open', html)
            self.assertIn('Renders salvos automaticamente no projeto.', html)
            self.assertNotIn('name="output_path"', html)

    def test_bootstrap_workspace_writes_project_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)

            CUTTED.bootstrap_workspace_gallery(workspace)
            html = (workspace / "index.html").read_text(encoding="utf-8")

            self.assertIn("data-project-home", html)
            self.assertIn("home-brand-logo", html)
            self.assertNotIn("home-logo-spark-left", html)
            self.assertIn("data-project-mock=\"true\"", html)
            self.assertTrue(CUTTED.workspace_index_is_empty_shell(workspace / "index.html"))

    def test_project_delete_can_forget_or_remove_workspace_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            catalog_path = workspace / "projects.json"
            project_dir = workspace / "_imports" / "sample"
            project_dir.mkdir(parents=True)
            (project_dir / "index.html").write_text("ok", encoding="utf-8")
            original_catalog_path = CUTTED.project_catalog_path
            CUTTED.project_catalog_path = lambda: catalog_path
            try:
                CUTTED.upsert_project_catalog_entry({"id": "sample", "title": "Sample", "path": str(project_dir)})

                result = CUTTED.delete_project_from_catalog("sample", workspace, False)

                self.assertTrue(result["ok"])
                self.assertTrue(project_dir.exists())

                CUTTED.upsert_project_catalog_entry({"id": "sample", "title": "Sample", "path": str(project_dir)})
                result = CUTTED.delete_project_from_catalog("sample", workspace, True)

                self.assertTrue(result["deleted_files"])
                self.assertFalse(project_dir.exists())
            finally:
                CUTTED.project_catalog_path = original_catalog_path

    def test_project_entry_from_gallery_reads_import_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            gallery = workspace / "_imports" / "demo"
            gallery.mkdir(parents=True)
            (gallery / "import-request.json").write_text(
                json.dumps({"source_path": str(workspace / "video.mp4")}),
                encoding="utf-8",
            )
            (gallery / "moments.json").write_text(json.dumps({"moments": [{}, {}]}), encoding="utf-8")

            entry = CUTTED.project_entry_from_gallery(gallery, workspace)

            self.assertEqual(entry["title"], "video.mp4")
            self.assertEqual(entry["clip_count"], 2)
            self.assertTrue(str(entry["id"]).startswith("demo-"))


if __name__ == "__main__":
    unittest.main()
