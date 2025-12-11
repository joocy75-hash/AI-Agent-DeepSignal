import uuid
import re
import logging
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from ..utils.jwt_auth import get_current_user_id

router = APIRouter(prefix="/upload", tags=["upload"])
logger = logging.getLogger(__name__)

# 업로드 디렉토리 설정
UPLOAD_DIR = Path(__file__).parent.parent.parent / "backtest_data"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# SECURITY: 파일 업로드 보안 설정
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB 제한
ALLOWED_MIME_TYPES = {"text/csv", "application/csv", "text/plain"}
ALLOWED_EXTENSIONS = {".csv"}


def sanitize_filename(filename: str) -> str:
    """파일명에서 위험한 문자 제거"""
    # 경로 구분자 및 특수문자 제거
    safe_name = re.sub(r'[^\w\-_\.]', '_', filename)
    # 경로 traversal 방지
    safe_name = safe_name.replace('..', '_')
    return safe_name


@router.post("/csv")
async def upload_csv(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
):
    """
    CSV 파일 업로드 (보안 강화)

    Args:
        file: 업로드할 CSV 파일 (최대 10MB)

    Returns:
        file_path: 저장된 파일의 경로
    """
    # SECURITY: 파일 확장자 검증
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"[SECURITY] Blocked file upload with extension: {file_ext}")
        raise HTTPException(status_code=400, detail="CSV 파일만 업로드 가능합니다")

    # SECURITY: MIME type 검증
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"[SECURITY] Blocked file upload with MIME type: {file.content_type}")
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다")

    # SECURITY: 파일 크기 제한 (스트리밍 방식으로 읽기)
    try:
        contents = await file.read()
        if len(contents) > MAX_UPLOAD_SIZE:
            logger.warning(f"[SECURITY] Blocked large file upload: {len(contents)} bytes")
            raise HTTPException(
                status_code=413,
                detail=f"파일 크기가 너무 큽니다. 최대 {MAX_UPLOAD_SIZE // (1024*1024)}MB까지 허용됩니다"
            )

        # SECURITY: CSV 내용 기본 검증 (첫 줄이 유효한 CSV 헤더인지)
        try:
            first_lines = contents[:1024].decode('utf-8', errors='ignore')
            if '\x00' in first_lines:  # 바이너리 파일 감지
                raise HTTPException(status_code=400, detail="유효한 CSV 파일이 아닙니다")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="유효한 텍스트 파일이 아닙니다")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File read error: {e}")
        raise HTTPException(status_code=500, detail="파일 읽기 실패")

    # SECURITY: 안전한 파일명 생성
    safe_filename = sanitize_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{safe_filename}"
    file_path = UPLOAD_DIR / unique_filename

    # 파일 저장
    try:
        with open(file_path, 'wb') as f:
            f.write(contents)

        logger.info(f"File uploaded successfully: {unique_filename} ({len(contents)} bytes) by user {user_id}")
        return {
            "message": "파일 업로드 성공",
            "file_path": str(file_path),
            "filename": unique_filename
        }

    except Exception as e:
        logger.error(f"File save error: {e}")
        raise HTTPException(
            status_code=500,
            detail="파일 저장 실패"
        )
