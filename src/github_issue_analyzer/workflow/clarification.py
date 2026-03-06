from __future__ import annotations

import re
from collections import defaultdict

from github_issue_analyzer.models import (
    ClarificationAnswer,
    ClarificationParseResult,
    QuestionSpec,
)


QUESTION_HEADER_RE = re.compile(r"^###\s+(Q\d+)\.", re.MULTILINE)
CHECKED_OPTION_RE = re.compile(r"^- \[(?P<mark>[ xX])\]\s+(?P<label>.+)$")
FREE_TEXT_RE = re.compile(r"^(Q\d+)\s*:\s*(.+)$", re.DOTALL)


def parse_clarification_comment_body(
    body: str,
    question_specs: list[QuestionSpec],
    free_text_comments: list[str],
) -> ClarificationParseResult:
    sections = _extract_sections(body)
    free_text_by_question = _group_free_text_answers(free_text_comments)

    answers: list[ClarificationAnswer] = []
    errors: list[str] = []
    all_complete = True

    for question in question_specs:
        section = sections.get(question.question_id, "")
        checked = _extract_checked_options(section, question.options)
        free_text_values = free_text_by_question.get(question.question_id, [])

        if checked and free_text_values:
            errors.append(f"{question.question_id}: 체크 응답과 자유 입력을 동시에 사용할 수 없습니다.")
            continue

        if len(free_text_values) > 1:
            errors.append(f"{question.question_id}: 자유 입력은 하나만 허용됩니다.")
            continue

        if free_text_values:
            answers.append(
                ClarificationAnswer(
                    question_id=question.question_id,
                    prompt=question.prompt,
                    free_text=free_text_values[0],
                )
            )
            continue

        count = len(checked)
        if count == 0:
            all_complete = False
            continue

        if not question.min_select <= count <= question.max_select:
            errors.append(
                f"{question.question_id}: 허용 선택 수는 {question.min_select}~{question.max_select}개입니다."
            )
            continue

        answers.append(
            ClarificationAnswer(
                question_id=question.question_id,
                prompt=question.prompt,
                selected_options=checked,
            )
        )

    return ClarificationParseResult(
        valid=not errors,
        complete=all_complete and not errors and len(answers) == len(question_specs),
        answers=answers,
        errors=errors,
    )


def _extract_sections(body: str) -> dict[str, str]:
    matches = list(QUESTION_HEADER_RE.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1)] = body[start:end]
    return sections


def _extract_checked_options(section: str, allowed_options: list[str]) -> list[str]:
    checked: list[str] = []
    allowed = set(allowed_options)
    for line in section.splitlines():
        match = CHECKED_OPTION_RE.match(line.strip())
        if not match:
            continue
        if match.group("mark").lower() != "x":
            continue
        label = match.group("label").strip()
        if label in allowed:
            checked.append(label)
    return checked


def _group_free_text_answers(comments: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for body in comments:
        match = FREE_TEXT_RE.match(body.strip())
        if match:
            grouped[match.group(1)].append(match.group(2).strip())
    return grouped
