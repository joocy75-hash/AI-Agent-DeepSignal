#!/usr/bin/env python3
"""
스킬 패키징 스크립트

스킬 디렉토리를 검증하고 배포 가능한 형태로 패키징합니다.

사용법:
    python scripts/package_skill.py ./skills/backend-trading-api
    python scripts/package_skill.py ./skills/frontend-trading-dashboard --output ./dist
    python scripts/package_skill.py ./skills/backend-trading-api --validate-only
"""

import argparse
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 스킬 구조 정의
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIRED_FILES = ["SKILL.md"]
OPTIONAL_DIRS = ["references", "scripts", "assets", "examples"]
MAX_SKILL_MD_LINES = 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 검증 함수들
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def validate_skill_structure(skill_path: Path) -> tuple[bool, list[str]]:
    """스킬 디렉토리 구조 검증"""
    errors = []
    warnings = []

    # 필수 파일 확인
    for required_file in REQUIRED_FILES:
        file_path = skill_path / required_file
        if not file_path.exists():
            errors.append(f"필수 파일 누락: {required_file}")

    # SKILL.md 라인 수 확인
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        with open(skill_md, "r", encoding="utf-8") as f:
            line_count = len(f.readlines())
        if line_count > MAX_SKILL_MD_LINES:
            warnings.append(
                f"SKILL.md가 {line_count}줄입니다. "
                f"권장: {MAX_SKILL_MD_LINES}줄 이하 (상세 내용은 references/로 분리)"
            )

    # 선택적 디렉토리 확인
    has_content_dir = False
    for optional_dir in OPTIONAL_DIRS:
        dir_path = skill_path / optional_dir
        if dir_path.exists() and dir_path.is_dir():
            has_content_dir = True
            # 빈 디렉토리 확인
            if not any(dir_path.iterdir()):
                warnings.append(f"빈 디렉토리: {optional_dir}/")

    if not has_content_dir:
        warnings.append(
            f"콘텐츠 디렉토리가 없습니다. "
            f"권장 디렉토리: {', '.join(OPTIONAL_DIRS)}"
        )

    return len(errors) == 0, errors + warnings


def validate_skill_md_content(skill_path: Path) -> tuple[bool, list[str]]:
    """SKILL.md 내용 검증"""
    issues = []
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        return False, ["SKILL.md 파일이 없습니다."]

    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()

    # 필수 섹션 확인
    required_sections = ["# ", "## "]
    if not any(section in content for section in required_sections):
        issues.append("SKILL.md에 헤더(#)가 없습니다.")

    # 트리거 조건/설명 확인
    trigger_keywords = ["트리거", "trigger", "사용 시점", "언제", "when"]
    if not any(keyword.lower() in content.lower() for keyword in trigger_keywords):
        issues.append(
            "SKILL.md에 트리거 조건/사용 시점 설명이 없습니다. "
            "AI가 언제 이 스킬을 사용해야 하는지 명시하세요."
        )

    # 코드 블록 확인
    if "```" not in content:
        issues.append("SKILL.md에 코드 예제가 없습니다. 실용적인 예제를 추가하세요.")

    return len(issues) == 0, issues


def validate_references(skill_path: Path) -> tuple[bool, list[str]]:
    """references 디렉토리 검증"""
    issues = []
    refs_dir = skill_path / "references"

    if not refs_dir.exists():
        return True, []  # 선택적이므로 없어도 OK

    for ref_file in refs_dir.glob("*.md"):
        with open(ref_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 최소 내용 확인
        if len(content.strip()) < 100:
            issues.append(f"references/{ref_file.name}: 내용이 너무 짧습니다.")

        # 헤더 확인
        if "#" not in content:
            issues.append(f"references/{ref_file.name}: 헤더(#)가 없습니다.")

    return len(issues) == 0, issues


def validate_scripts(skill_path: Path) -> tuple[bool, list[str]]:
    """scripts 디렉토리 검증"""
    issues = []
    scripts_dir = skill_path / "scripts"

    if not scripts_dir.exists():
        return True, []

    for script_file in scripts_dir.glob("*.py"):
        with open(script_file, "r", encoding="utf-8") as f:
            content = f.read()

        # docstring 확인
        if '"""' not in content and "'''" not in content:
            issues.append(f"scripts/{script_file.name}: docstring이 없습니다.")

        # 문법 검증
        try:
            compile(content, script_file.name, "exec")
        except SyntaxError as e:
            issues.append(f"scripts/{script_file.name}: 문법 오류 - {e}")

    return len(issues) == 0, issues


def validate_assets(skill_path: Path) -> tuple[bool, list[str]]:
    """assets 디렉토리 검증"""
    errors = []
    warnings = []
    assets_dir = skill_path / "assets"

    if not assets_dir.exists():
        return True, []

    valid_extensions = {".jsx", ".tsx", ".js", ".ts", ".css", ".scss", ".json", ".svg"}

    for asset_file in assets_dir.iterdir():
        if asset_file.is_file():
            if asset_file.suffix.lower() not in valid_extensions:
                errors.append(
                    f"assets/{asset_file.name}: "
                    f"지원하지 않는 확장자입니다. 지원: {valid_extensions}"
                )

            # 파일 크기 확인 (10KB 이상이면 경고, 오류 아님)
            if asset_file.stat().st_size > 10 * 1024:
                warnings.append(
                    f"assets/{asset_file.name}: "
                    f"[경고] 파일이 큽니다 ({asset_file.stat().st_size // 1024}KB). "
                    "템플릿은 가능한 간결하게 유지하세요."
                )

    # 경고는 출력하지만 통과로 처리
    return len(errors) == 0, errors + warnings


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 패키징 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def generate_manifest(skill_path: Path) -> dict:
    """스킬 매니페스트 생성"""
    skill_name = skill_path.name

    # SKILL.md에서 설명 추출
    skill_md = skill_path / "SKILL.md"
    description = ""
    if skill_md.exists():
        with open(skill_md, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # 첫 번째 헤더 다음 텍스트를 설명으로 사용
            for i, line in enumerate(lines):
                if line.startswith("# "):
                    # 다음 비어있지 않은 줄 찾기
                    for next_line in lines[i + 1 :]:
                        if next_line.strip() and not next_line.startswith("#"):
                            description = next_line.strip()
                            break
                    break

    # 파일 목록 생성
    files = []
    for file_path in skill_path.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(skill_path)
            files.append({
                "path": str(relative_path),
                "size": file_path.stat().st_size,
                "type": file_path.suffix[1:] if file_path.suffix else "unknown",
            })

    return {
        "name": skill_name,
        "version": "1.0.0",
        "description": description[:200] if description else f"{skill_name} 스킬",
        "created_at": datetime.now().isoformat(),
        "files": files,
        "file_count": len(files),
        "total_size": sum(f["size"] for f in files),
    }


def create_package(
    skill_path: Path, output_dir: Optional[Path] = None
) -> Optional[Path]:
    """스킬을 ZIP 파일로 패키징"""
    skill_name = skill_path.name

    if output_dir is None:
        output_dir = Path.cwd() / "dist" / "skills"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 매니페스트 생성
    manifest = generate_manifest(skill_path)

    # 임시 매니페스트 파일 생성
    manifest_path = skill_path / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # ZIP 파일 생성
    timestamp = datetime.now().strftime("%Y%m%d")
    zip_filename = f"{skill_name}-{timestamp}.zip"
    zip_path = output_dir / zip_filename

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in skill_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(skill_path)
                zipf.write(file_path, arcname)

    # 임시 매니페스트 삭제
    manifest_path.unlink()

    return zip_path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main():
    parser = argparse.ArgumentParser(
        description="스킬 패키징 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python scripts/package_skill.py ./skills/backend-trading-api
  python scripts/package_skill.py ./skills/frontend-trading-dashboard --output ./dist
  python scripts/package_skill.py ./skills/backend-trading-api --validate-only
        """,
    )
    parser.add_argument("skill_path", type=str, help="스킬 디렉토리 경로")
    parser.add_argument(
        "--output", "-o", type=str, help="출력 디렉토리 (기본: ./dist/skills)"
    )
    parser.add_argument(
        "--validate-only",
        "-v",
        action="store_true",
        help="검증만 수행 (패키징하지 않음)",
    )
    parser.add_argument(
        "--strict", "-s", action="store_true", help="경고도 오류로 처리"
    )

    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()

    if not skill_path.exists():
        print(f"오류: 경로가 존재하지 않습니다: {skill_path}")
        sys.exit(1)

    if not skill_path.is_dir():
        print(f"오류: 디렉토리가 아닙니다: {skill_path}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"스킬 검증: {skill_path.name}")
    print(f"{'=' * 60}\n")

    # 검증 실행
    all_issues = []
    validators = [
        ("구조 검증", validate_skill_structure),
        ("SKILL.md 검증", validate_skill_md_content),
        ("references 검증", validate_references),
        ("scripts 검증", validate_scripts),
        ("assets 검증", validate_assets),
    ]

    all_passed = True
    for name, validator in validators:
        passed, issues = validator(skill_path)
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")

        if issues:
            for issue in issues:
                prefix = "    ⚠" if "권장" in issue or "경고" in issue else "    ✗"
                print(f"{prefix} {issue}")
            all_issues.extend(issues)

        if not passed:
            all_passed = False

    print()

    # 검증 결과
    if args.strict and all_issues:
        all_passed = False

    if not all_passed:
        print(f"{'=' * 60}")
        print("검증 실패: 위의 오류를 수정하세요.")
        print(f"{'=' * 60}\n")
        sys.exit(1)

    print(f"{'=' * 60}")
    print("검증 통과!")
    print(f"{'=' * 60}\n")

    # 패키징
    if not args.validate_only:
        print("패키징 중...")
        output_dir = Path(args.output) if args.output else None
        zip_path = create_package(skill_path, output_dir)

        if zip_path:
            print(f"\n패키지 생성 완료: {zip_path}")
            print(f"파일 크기: {zip_path.stat().st_size / 1024:.1f} KB")
        else:
            print("패키징 실패")
            sys.exit(1)

    print()


if __name__ == "__main__":
    main()
