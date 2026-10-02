import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import digest as d


def _paper(**overrides):
    paper = {
        "id": "2601.00001", "title": "Optical Variability of Quasars",
        "abstract": "We measure quasar structure functions and infer variability timescales.",
        "authors": ["A. Astronomer"], "category": "astro-ph.GA",
        "published": "2026-01-01", "url": "https://arxiv.org/abs/2601.00001",
        "known_authors": [], "keyword_hits": 80.0, "keyword_hits_raw": 8,
    }
    paper.update(overrides)
    return paper


def _config():
    return {"researcher_name": "Colin Burke", "research_context": "I study quasar variability.",
            "keywords": {"quasar": 10}, "categories": ["astro-ph.GA"],
            "openai_model": "gpt-5.6-luna", "enable_vertex_gemini": False,
            "min_score": 6, "max_papers": 12}


def test_openai_uses_responses_parse_and_renderer_fields():
    parsed = d.PaperAnalysis(
        relevance_score=9, plain_summary="Measures optical structure functions. Finds a timescale trend.",
        why_interesting="Directly relevant to quasar stochastic variability.", emoji="🌌",
        highlight_phrase="Quasar variability timescales constrained", kw_tags=["quasars"],
        method_tags=["structure function"], is_new_catalog=False, cite_worthy=True,
        new_result="timescale trend")
    client = MagicMock()
    client.responses.parse.return_value = SimpleNamespace(output_parsed=parsed)
    with patch.object(d, "OpenAI", return_value=client):
        result, error = d._analyse_with_openai([_paper()], _config(), "test-key")
    assert error is None
    assert result[0]["relevance_score"] == 9
    kwargs = client.responses.parse.call_args.kwargs
    assert kwargs["model"] == "gpt-5.6-luna"
    assert kwargs["text_format"] is d.PaperAnalysis
    assert kwargs["store"] is False


def test_openai_is_preferred_when_key_is_present():
    expected = [_paper(relevance_score=9)]
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True), \
         patch.object(d, "HAS_OPENAI", True), \
         patch.object(d, "_analyse_with_openai", return_value=(expected, None)) as openai_call, \
         patch.object(d, "_analyse_with_claude") as claude_call:
        result, method = d.analyse_papers([_paper()], _config())
    assert result == expected and method == "openai"
    openai_call.assert_called_once()
    claude_call.assert_not_called()


def test_missing_openai_key_uses_keyword_fallback_without_gcp():
    with patch.dict(os.environ, {}, clear=True), patch.object(d, "HAS_VERTEX_GEMINI", True), \
         patch.object(d, "_analyse_with_vertex_gemini") as vertex:
        result, method = d.analyse_papers([_paper()], _config())
    assert method == "keywords" and result
    vertex.assert_not_called()
