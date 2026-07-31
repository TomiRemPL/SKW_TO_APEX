"""Testy HTML renderera."""
from apex_export_to_md.renderers.html_renderer import HTMLRenderer
from apex_export_to_md.config import AppConfig
from apex_export_to_md.models import ApexApp, ApexPage, Process


def test_html_renderer_serialize_page_build_option():
    """HTMLRenderer poprawnie serializuje build_option w JSON."""
    proc = Process(name="Proc1", type="Execute Code", build_option="Commented Out")
    page = ApexPage(id=1, name="P1", processes=[proc])
    app = ApexApp(name="App", id="100", pages=[page])

    renderer = HTMLRenderer(AppConfig())
    serialized = renderer._serialize_page(page)
    assert serialized["processes"][0]["build_option"] == "Commented Out"

    output = renderer.render(app)
    assert "<!DOCTYPE html>" in output
    assert "Commented Out" in output
