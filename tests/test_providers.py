import httpx
import pytest
from makma.providers import OllamaProvider,OpenAICompatibleProvider,MockProvider,ModelRouter,InvalidModelOutput,check_endpoint
from makma.schemas import Cognition

VALID={"thought_summary":"Check evidence","current_goal":"Retrieve sources","confidence":.5}


async def test_repair_once_then_safe_failure():
    provider=MockProvider(["not JSON","also not JSON",VALID])
    with pytest.raises(InvalidModelOutput):
        await ModelRouter(provider,"mock").structured([],Cognition)
    assert len(provider.calls)==2


async def test_repair_recovers_and_accounts_both_requests():
    provider=MockProvider(["bad",VALID])
    tokens=[]
    result=await ModelRouter(provider,"mock").structured([],Cognition,on_usage=lambda c:tokens.append(c.tokens))
    assert result.confidence==.5 and sum(tokens)==20


async def test_extra_result_fields_rejected():
    provider=MockProvider([{**VALID,"benchmark_result":{"improvement":40}}]*2)
    with pytest.raises(InvalidModelOutput):
        await ModelRouter(provider,"mock").structured([],Cognition)


async def test_ollama_contract(settings):
    def handler(request):
        import json
        if request.url.path=="/api/tags":
            return httpx.Response(200,json={"models":[{"name":settings.model}]})
        body=json.loads(request.content)
        assert body["think"] is False and body["stream"] is False
        assert body["format"]["type"]=="object"
        assert body["options"]["num_ctx"]==4096
        return httpx.Response(200,json={"message":{"content":"{}"},"prompt_eval_count":12,"eval_count":8})
    provider=OllamaProvider(settings,httpx.MockTransport(handler))
    assert (await provider.health())["available"]
    assert (await provider.complete([],Cognition.model_json_schema(),256)).tokens==20
    await provider.close()


async def test_compatible_provider_preserves_v1_path(settings):
    paths=[]
    def handler(request):
        paths.append(request.url.path)
        return httpx.Response(200,json={"choices":[{"message":{"content":"{}"}}],"usage":{"total_tokens":4}})
    provider=OpenAICompatibleProvider(settings,httpx.MockTransport(handler))
    await provider.complete([],{},20)
    assert paths==["/v1/chat/completions"]
    await provider.close()


def test_remote_model_requires_explicit_opt_in():
    with pytest.raises(ValueError):
        check_endpoint("https://example.com/v1",False)
    check_endpoint("http://127.0.0.1:11434",False)

