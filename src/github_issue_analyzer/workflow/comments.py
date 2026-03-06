from __future__ import annotations

from datetime import UTC, datetime

from github_issue_analyzer.models import EstimateResult, QuestionSpec, WorkflowState


STATE_LABELS = {
    WorkflowState.NEEDS_CLARIFICATION: "ai:needs-clarification",
    WorkflowState.READY_FOR_ESTIMATE: "ai:ready-for-estimate",
    WorkflowState.ESTIMATING: "ai:estimating",
    WorkflowState.ESTIMATED: "ai:estimated",
    WorkflowState.STALE: "ai:stale",
    WorkflowState.REFRESHING: "ai:refreshing",
    WorkflowState.STOPPED: "ai:stopped",
    WorkflowState.ERROR: "ai:error",
}

CONFIDENCE_LABELS = {
    "low": "ai:confidence:low",
    "medium": "ai:confidence:medium",
    "high": "ai:confidence:high",
}

BOOTSTRAP_LABEL_SPECS = {
    "ai:analyze": ("1d76db", "Issue Analyzer trigger label"),
    "ai:needs-clarification": ("fbca04", "Analyzer needs more detail"),
    "ai:ready-for-estimate": ("0e8a16", "Analyzer has enough detail to estimate"),
    "ai:estimating": ("5319e7", "Analyzer is running estimate"),
    "ai:estimated": ("0052cc", "Analyzer posted an estimate"),
    "ai:stale": ("b60205", "Analyzer estimate is stale"),
    "ai:refreshing": ("c5def5", "Analyzer is refreshing"),
    "ai:stopped": ("6a737d", "Analyzer workflow was stopped"),
    "ai:error": ("d93f0b", "Analyzer encountered an error"),
    "ai:confidence:low": ("f9d0c4", "Low confidence estimate"),
    "ai:confidence:medium": ("fef2c0", "Medium confidence estimate"),
    "ai:confidence:high": ("c2e0c6", "High confidence estimate"),
}


def render_clarification_comment(
    missing_slots: list[str], question_specs: list[QuestionSpec], round_number: int
) -> str:
    lines = [
        "[Issue Analyzer]",
        "",
        f"현재 부족한 항목: {', '.join(missing_slots)}",
        "아래 체크리스트를 직접 수정해 답변해 주세요.",
        "선택지에 없으면 새 댓글로 `Q번호: 내용` 형식으로 답해 주세요.",
        "",
        f"<!-- issue-analyzer:clarification round={round_number} -->",
    ]

    for spec in question_specs:
        lines.extend(
            [
                "",
                f"### {spec.question_id}. {spec.prompt}",
                f"- 타입: `{spec.type}`",
                f"- 허용 선택 수: `{spec.min_select}~{spec.max_select}`",
            ]
        )
        for option in spec.options:
            lines.append(f"- [ ] {option}")
        if spec.option_descriptions:
            lines.append("")
            lines.append("옵션 설명:")
            for option, description in zip(spec.options, spec.option_descriptions, strict=False):
                lines.append(f"- `{option}`: {description}")
        if spec.recommended_option:
            lines.append(f"- 추천: `{spec.recommended_option}`")

    lines.extend(
        [
            "",
            "답변이 모두 유효해지면 다음 단계로 자동 진행합니다.",
        ]
    )
    return "\n".join(lines)


def render_estimate_comment(base_branch: str, estimate: EstimateResult) -> str:
    now = datetime.now(UTC).isoformat()
    return "\n".join(
        [
            "[Issue Analyzer]",
            "",
            f"- 분석 시각: `{now}`",
            f"- 기준 브랜치: `{base_branch}`",
            f"- 기준 커밋: `{estimate.base_commit}`",
            f"- 예상 추가: `+{estimate.lines_added_min} ~ +{estimate.lines_added_max} lines`",
            f"- 예상 수정: `{estimate.lines_modified_min} ~ {estimate.lines_modified_max} lines touched`",
            f"- 예상 삭제: `{estimate.lines_deleted_min} ~ {estimate.lines_deleted_max} lines`",
            f"- 총 영향 범위: `{estimate.lines_total_min} ~ {estimate.lines_total_max} lines`",
            f"- 신뢰도: `{estimate.confidence.value}`",
            "- 주요 파일 후보:",
            *[f"  - `{path}`" for path in estimate.files],
            "- 근거:",
            *[f"  - {reason}" for reason in estimate.reasons],
            "",
            "`/refresh` 로 전체 재평가를 다시 실행할 수 있습니다.",
        ]
    )


def render_stale_comment(previous_commit: str, current_commit: str, matched_files: list[str]) -> str:
    lines = [
        "[Issue Analyzer]",
        "",
        "이전 추정이 stale 상태로 전환되었습니다.",
        f"- 이전 기준 커밋: `{previous_commit}`",
        f"- 현재 기준 커밋: `{current_commit}`",
        "- 겹친 파일:",
        *[f"  - `{path}`" for path in matched_files],
        "",
        "`/refresh` 로 전체 재평가를 다시 실행할 수 있습니다.",
    ]
    return "\n".join(lines)


def render_requirements_changed_comment() -> str:
    return "\n".join(
        [
            "[Issue Analyzer]",
            "",
            "기존 추정 이후 요구사항 변경이 감지되어 상태를 `needs-clarification`으로 되돌렸습니다.",
            "필요하면 내용을 보완한 뒤 `/refresh` 로 전체 재평가를 다시 실행해 주세요.",
        ]
    )


def render_error_comment(error_message: str) -> str:
    return "\n".join(
        [
            "[Issue Analyzer]",
            "",
            "처리 중 오류가 발생했습니다.",
            f"- 오류: `{error_message}`",
        ]
    )
