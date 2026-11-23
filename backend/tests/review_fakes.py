import json

from langchain_core.messages import AIMessage

from app.schemas import EvidenceReview


class FakeEvidenceReviewer:
    def invoke(self, messages):
        payload = json.loads(messages[-1].content)
        return {
            "raw": AIMessage(
                content="",
                usage_metadata={
                    "input_tokens": 100,
                    "output_tokens": 30,
                    "total_tokens": 130,
                },
            ),
            "parsed": EvidenceReview(
                short_answer=payload["draft_answer"],
                passage_ids=[payload["passages"][0]["id"]],
                information_missing=False,
                missing_information="",
            ),
            "parsing_error": None,
        }
