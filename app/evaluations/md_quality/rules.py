from __future__ import annotations

import re

from app.evaluations.md_quality.schemas import DimensionScore, QualityIssue


def evaluate_encoding(markdown: str) -> DimensionScore:
    issues: list[QualityIssue] = []
    cid_count = len(re.findall(r"\(cid:\d+\)", markdown))
    replacement_count = markdown.count("\ufffd") + markdown.count("�")
    if cid_count:
        issues.append(QualityIssue("encoding.cid_tokens", "high", f"检测到 {cid_count} 个 CID 字体编码残留。"))
    if replacement_count:
        issues.append(QualityIssue("encoding.replacement_chars", "medium", f"检测到 {replacement_count} 个替换字符。"))
    penalty = min(60, cid_count * 2 + replacement_count * 3)
    return DimensionScore("encoding", max(0.0, 100.0 - penalty), issues)


def evaluate_structure(markdown: str) -> DimensionScore:
    issues: list[QualityIssue] = []
    char_count = len(markdown)
    headings = re.findall(r"(?m)^(\s{0,3}#{1,6})\s+", markdown)
    if char_count < 80:
        issues.append(QualityIssue("structure.too_short", "high", "输出文本过短，疑似转换失败。"))
    if not headings:
        issues.append(QualityIssue("structure.no_headings", "low", "未检测到 Markdown 标题。"))
    levels = [len(h.strip()) for h in headings]
    for prev, cur in zip(levels, levels[1:]):
        if cur - prev > 1:
            issues.append(QualityIssue("structure.heading_jump", "medium", "标题层级存在跳跃。"))
            break
    penalty = 0
    penalty += 35 if char_count < 80 else 0
    penalty += 8 if not headings else 0
    penalty += 12 if any(issue.rule_id == "structure.heading_jump" for issue in issues) else 0
    return DimensionScore("structure", max(0.0, 100.0 - penalty), issues)


def evaluate_tables(markdown: str) -> DimensionScore:
    issues: list[QualityIssue] = []
    md_table_lines = [line for line in markdown.splitlines() if "|" in line and re.search(r"\|.*\|", line)]
    html_table = bool(re.search(r"<table\b", markdown, re.IGNORECASE))
    detected = html_table or len(md_table_lines) >= 2
    if not detected:
        issues.append(QualityIssue("table.not_detected", "low", "未检测到 Markdown/HTML 表格。"))
    inconsistent_rows = 0
    widths = [len(line.strip("|").split("|")) for line in md_table_lines if not re.fullmatch(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?", line.strip())]
    if widths and len(set(widths)) > 1:
        inconsistent_rows = len(widths)
        issues.append(QualityIssue("table.inconsistent_columns", "medium", "Markdown 表格列数不一致。"))
    penalty = 0 if detected else 8
    penalty += min(25, inconsistent_rows * 2)
    return DimensionScore("table", max(0.0, 100.0 - penalty), issues)


def evaluate_readability(markdown: str) -> DimensionScore:
    issues: list[QualityIssue] = []
    long_alpha_tokens = re.findall(r"[A-Za-z]{35,}", markdown)
    if len(long_alpha_tokens) >= 5:
        issues.append(QualityIssue("readability.long_tokens", "medium", "检测到多个超长英文 token，可能存在词粘连。"))
    excessive_blank_blocks = len(re.findall(r"\n{5,}", markdown))
    if excessive_blank_blocks:
        issues.append(QualityIssue("readability.blank_blocks", "low", "检测到过多连续空行。"))
    penalty = min(30, len(long_alpha_tokens) * 2 + excessive_blank_blocks * 3)
    return DimensionScore("readability", max(0.0, 100.0 - penalty), issues)

