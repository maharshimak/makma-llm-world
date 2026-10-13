from makma.providers import grammar_schema
from makma.schemas import HypothesisDraft

def test_schema_simplification_preserves_title_property():
    schema=grammar_schema(HypothesisDraft.model_json_schema())
    assert "title" in schema["properties"]
    assert set(schema["required"])<=set(schema["properties"])
    assert "maxLength" not in schema["properties"]["title"]
