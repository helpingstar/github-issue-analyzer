from github_issue_analyzer.models import QuestionSpec
from github_issue_analyzer.workflow.clarification import parse_clarification_comment_body


def test_parse_single_select_with_checked_box() -> None:
    body = """
### Q1. 입력/출력 변경 여부를 선택해 주세요.
- 타입: `single-select`
- 허용 선택 수: `1~1`
- [x] 있음
- [ ] 없음 (N/A)
- [ ] 아직 미정
""".strip()
    question = QuestionSpec(
        question_id="Q1",
        slot="input_output",
        type="single-select",
        min_select=1,
        max_select=1,
        prompt="입력/출력 변경 여부를 선택해 주세요.",
        options=["있음", "없음 (N/A)", "아직 미정"],
    )

    result = parse_clarification_comment_body(body, [question], [])

    assert result.valid is True
    assert result.complete is True
    assert result.answers[0].selected_options == ["있음"]


def test_parse_free_text_fallback() -> None:
    body = """
### Q1. 완료 조건을 선택해 주세요.
- [ ] 동작 구현만
- [ ] 테스트 포함
- [ ] 테스트 + 문서 포함
""".strip()
    question = QuestionSpec(
        question_id="Q1",
        slot="done_criteria",
        type="single-select",
        min_select=1,
        max_select=1,
        prompt="완료 조건을 선택해 주세요.",
        options=["동작 구현만", "테스트 포함", "테스트 + 문서 포함"],
    )

    result = parse_clarification_comment_body(body, [question], ["Q1: E2E 테스트까지 포함"])

    assert result.valid is True
    assert result.complete is True
    assert result.answers[0].free_text == "E2E 테스트까지 포함"
