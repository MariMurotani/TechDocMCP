import sys
from pathlib import Path
import types

import pytest

# Ensure src/ is importable when running from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Preload lightweight stubs so build_index import succeeds without optional deps.
if "sentence_transformers" not in sys.modules:
    fake_st = types.SimpleNamespace()

    class FakeSentenceTransformer:
        def __init__(self, *_args, **_kwargs):
            pass

        def encode(self, text):  # pragma: no cover - stub behavior
            return [0.0] * 384

    fake_st.SentenceTransformer = FakeSentenceTransformer
    sys.modules["sentence_transformers"] = fake_st

if "frontmatter" not in sys.modules:
    class _FakeFMPost:
        def __init__(self, content=""):
            self.content = content

    def _fake_load(_path):  # pragma: no cover - stub behavior
        return _FakeFMPost("")

    sys.modules["frontmatter"] = types.SimpleNamespace(load=_fake_load)

if "markdown" not in sys.modules:
    def _fake_markdown(text):  # pragma: no cover - stub behavior
        return text

    sys.modules["markdown"] = types.SimpleNamespace(markdown=_fake_markdown)

if "trafilatura" not in sys.modules:
    def _fake_extract(_html, **_kwargs):  # pragma: no cover - stub behavior
        return ""

    sys.modules["trafilatura"] = types.SimpleNamespace(extract=_fake_extract)


import build_index  # noqa: E402  pylint: disable=wrong-import-position


@pytest.fixture
def docs_base(monkeypatch):
    base = "/base/docs/"
    monkeypatch.setattr(build_index, "LOCAL_DOCS_BASE", base)
    return base


def test_path_to_url_converts_html(docs_base):
    path = f"{docs_base}python/docs.python.org/3/tutorial/index.html"
    assert build_index.path_to_url(path) == "https://docs.python.org/3/tutorial/index"


def test_path_to_url_converts_markdown(docs_base):
    path = f"{docs_base}aws_design/aws.amazon.com/well-architected/intro.md"
    assert build_index.path_to_url(path) == "https://aws.amazon.com/well-architected/intro"


def test_path_to_url_outside_base_returns_original():
    path = "/other/location/page.html"
    assert build_index.path_to_url(path) == path


def test_detect_category_known():
    assert build_index.detect_category("/any/vue/guide/index.html") == "vue"


def test_detect_category_unknown():
    assert build_index.detect_category("/any/unknown/guide/index.html") == "unknown"


def test_should_skip_file_for_index_pages():
    assert build_index.should_skip_file("genindex.html", "/tmp/genindex.html") is True
    assert build_index.should_skip_file("search.html", "/tmp/docs/search.html") is True


def test_should_skip_file_for_normal_page():
    assert build_index.should_skip_file("howto.html", "/tmp/howto.html") is False


def test_is_allowed_domain_blocked(monkeypatch, docs_base):
    monkeypatch.setattr(build_index, "DOMAIN_BLOCKLIST", ["google-analytics.com"])
    path = f"{docs_base}vue/google-analytics.com/page.html"
    assert build_index.is_allowed_domain(path) is False


def test_is_allowed_domain_allowed(monkeypatch, docs_base):
    monkeypatch.setattr(build_index, "DOMAIN_BLOCKLIST", ["google-analytics.com"])
    path = f"{docs_base}vue/vuejs.org/guide.html"
    assert build_index.is_allowed_domain(path) is True
