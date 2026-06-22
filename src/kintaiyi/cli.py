"""
kintaiyi CLI - 太乙神數命令列工具

Usage examples:
    kintaiyi calculate --year 2026 --month 3 --day 24 --hour 12 --minute 30 --mode year
    kintaiyi calculate --date 2026-03-24 --time 12:30 --mode day
    kintaiyi calculate --date 2026-03-24 --time 12:30 --mode life --sex male
"""

import json
from datetime import datetime
from enum import Enum

import typer

from . import __version__

app = typer.Typer(
    name="kintaiyi",
    help="태을신수(太乙神數) 포국 도구 - Taiyi Shenshu Divination Calculator",
    add_completion=False,
)


class Mode(str, Enum):
    year = "year"
    month = "month"
    day = "day"
    hour = "hour"
    minute = "minute"
    life = "life"


class OutputFormat(str, Enum):
    text = "text"
    json = "json"
    markdown = "markdown"


# Mapping from CLI mode names to ji_style integers used by Taiyi
_MODE_TO_JI_STYLE: dict[str, int] = {
    "year": 0,
    "month": 1,
    "day": 2,
    "hour": 3,
    "minute": 4,
    "life": 5,
}


def _parse_date_time(
    date_str: str | None,
    time_str: str | None,
    year: int | None,
    month: int | None,
    day: int | None,
    hour: int | None,
    minute: int | None,
) -> tuple[int, int, int, int, int]:
    """Resolve date/time from either --date/--time or individual components."""
    if date_str is not None:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise typer.BadParameter(f"잘못된 날짜 형식: '{date_str}'. YYYY-MM-DD 형식이어야 합니다.") from None
        year = d.year
        month = d.month
        day = d.day

    if time_str is not None:
        try:
            t = datetime.strptime(time_str, "%H:%M")
        except ValueError:
            raise typer.BadParameter(f"잘못된 시간 형식: '{time_str}'. HH:MM 형식이어야 합니다.") from None
        hour = t.hour
        minute = t.minute

    now = datetime.now()
    year = year if year is not None else now.year
    month = month if month is not None else now.month
    day = day if day is not None else now.day
    hour = hour if hour is not None else now.hour
    minute = minute if minute is not None else now.minute

    return year, month, day, hour, minute


def _format_text(result: dict) -> str:
    """Format a result dict as plain text."""
    lines: list[str] = []
    for key, value in result.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def _format_json(result: dict) -> str:
    """Format a result dict as JSON."""
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)


def _format_markdown(result: dict) -> str:
    """Format a result dict as Markdown table."""
    lines: list[str] = ["| 항목 | 내용 |", "| --- | --- |"]
    for key, value in result.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


_FORMATTERS = {
    "text": _format_text,
    "json": _format_json,
    "markdown": _format_markdown,
}


@app.command()
def calculate(
    year: int | None = typer.Option(None, "--year", "-y", help="연도(公元年)"),
    month: int | None = typer.Option(None, "--month", "-m", help="월(月)"),
    day: int | None = typer.Option(None, "--day", "-d", help="일(日)"),
    hour: int | None = typer.Option(None, "--hour", "-H", help="시(時, 0-23)"),
    minute: int | None = typer.Option(None, "--minute", "-M", help="분(分, 0-59)"),
    date: str | None = typer.Option(None, "--date", help="날짜 (YYYY-MM-DD 형식)"),
    time: str | None = typer.Option(None, "--time", help="시간 (HH:MM 형식)"),
    mode: Mode = typer.Option(Mode.year, "--mode", help="계산 모드 (year/month/day/hour/minute/life)"),
    output: OutputFormat = typer.Option(OutputFormat.text, "--output", "-o", help="출력 형식 (text/json/markdown)"),
    method: int = typer.Option(0, "--method", help="태을 방법: 0=통종(統宗), 1=금경(金鏡), 2=도금가(淘金歌), 3=태을국(太乙局)"),
    sex: str | None = typer.Option(None, "--sex", "-s", help="명법 모드 성별: male(남) 또는 female(여)"),
) -> None:
    """태을신수(太乙神數) 포국을 계산합니다."""
    from .kintaiyi import Taiyi

    y, m, d, h, mi = _parse_date_time(date, time, year, month, day, hour, minute)

    taiyi = Taiyi(y, m, d, h, mi)

    if mode.value == "life":
        sex_map = {"male": "男", "female": "女"}
        sex_val = sex_map.get(sex, sex) if sex else None
        if sex_val not in ("男", "女"):
            raise typer.BadParameter("명법(life) 모드에는 --sex (male/남 또는 female/여)가 필요합니다.")
        result = taiyi.taiyi_life(sex_val)
    else:
        ji_style = _MODE_TO_JI_STYLE[mode.value]
        result = taiyi.pan(ji_style, method)

    formatter = _FORMATTERS[output.value]
    typer.echo(formatter(result))


@app.command()
def version() -> None:
    """kintaiyi 버전을 표시합니다."""
    typer.echo(f"kintaiyi {__version__}")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
