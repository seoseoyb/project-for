
import streamlit as st
from PIL import Image
import urllib.request
import urllib.parse
import json
import re
import io
from datetime import datetime, timedelta

# =========================================================
# PAGE
# =========================================================
st.set_page_config(
    page_title="행사 포스터 일정 자동 등록",
    page_icon="📅",
    layout="wide"
)

st.markdown('\n    <style>\n    @import url(\'https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Jua&display=swap\');\n\n    /* 전체 테마: 따뜻한 크림 + 라벤더 포인트 */\n    .stApp {\n        font-family: "Jua", "Gowun Dodum", "Malgun Gothic", sans-serif;\n        background: linear-gradient(180deg, #eee7fb 0%, #f8f4ff 44%, #fff9f1 100%);\n        color: #51485d;\n    }\n\n    /* 앱 전체를 동글동글한 글씨로 통일 */\n    .stApp p, .stApp label, .stApp input, .stApp textarea,\n    .stApp select, .stApp [data-testid="stMarkdownContainer"],\n    .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stFileUploaderDropzone"] {\n        font-family: "Gowun Dodum", "Jua", "Malgun Gothic", sans-serif !important;\n    }\n\n    /* Streamlit 아이콘은 아이콘 폰트를 유지 */\n    .stApp .material-symbols-outlined,\n    .stApp .material-icons,\n    .stApp [class*="material-symbols"] {\n        font-family: "Material Symbols Outlined" !important;\n    }\n\n    h1, h2, h3, h4, h5, h6 {\n        font-family: "Jua", "Gowun Dodum", sans-serif !important;\n        font-weight: 400 !important;\n        letter-spacing: -0.02em;\n    }\n\n    /* 상단 제목 영역 */\n    .main-title-wrap {\n        text-align: center;\n        padding: 24px 12px 12px 12px;\n    }\n\n    .main-title-wrap .main-title {\n        font-family: "Jua", "Gowun Dodum", sans-serif;\n        font-size: clamp(32px, 4vw, 48px);\n        line-height: 1.25;\n        color: #4b4266;\n        margin: 0;\n    }\n\n    .main-title-wrap .main-subtitle {\n        margin-top: 10px;\n        color: #81778f;\n        font-family: "Gowun Dodum", "Jua", sans-serif;\n        font-size: 16px;\n        font-weight: 400;\n    }\n\n    /* 업로드 영역 */\n    [data-testid="stFileUploader"] {\n        background: rgba(255,253,249,.92);\n        border: 2px dashed #cfc0dd;\n        border-radius: 18px 24px 20px 14px;\n        padding: 9px;\n        box-shadow: 3px 4px 0 rgba(218,203,226,.42), 0 10px 22px rgba(84,69,105,.07);\n    }\n\n    /* 메인 정보 찾기 버튼 */\n    div.stButton > button[kind="primary"] {\n        border-radius: 16px !important;\n        min-height: 52px !important;\n        font-family: "Jua", "Gowun Dodum", sans-serif !important;\n        font-size: 18px !important;\n        letter-spacing: -0.01em;\n        border: 0 !important;\n        box-shadow: 0 7px 18px rgba(113, 91, 155, 0.16);\n        transition: transform 0.15s ease, box-shadow 0.15s ease;\n    }\n\n    div.stButton > button[kind="primary"]:hover {\n        transform: translateY(-2px);\n        box-shadow: 0 10px 22px rgba(113, 91, 155, 0.22);\n    }\n\n    /* ───────── 다이어리 노트형 행사 카드 ───────── */\n    [data-testid="stVerticalBlockBorderWrapper"] {\n        position: relative;\n        margin: 28px 0 34px 0 !important;\n        padding: 28px 28px 24px 42px !important;\n        border-radius: 10px 18px 14px 12px !important;\n        border: 1px solid #e4d8ea !important;\n        border-left: 3px solid #d7c3df !important;\n        background-color: #fffdf8 !important;\n        background-image:\n            linear-gradient(to right, transparent 0, transparent 31px, rgba(218,191,211,.30) 32px, transparent 33px),\n            repeating-linear-gradient(to bottom, transparent 0, transparent 31px, rgba(196,185,211,.18) 32px, transparent 33px);\n        box-shadow: 4px 7px 0 rgba(214,197,224,.45), 0 14px 30px rgba(84,69,105,.10);\n        overflow: visible !important;\n    }\n\n    /* 노트 위에 붙인 마스킹테이프 */\n    [data-testid="stVerticalBlockBorderWrapper"]::before {\n        content: "";\n        position: absolute;\n        z-index: 5;\n        top: -13px;\n        left: 50%;\n        transform: translateX(-50%) rotate(-2deg);\n        width: 108px;\n        height: 28px;\n        border-radius: 5px;\n        background: rgba(211,194,232,.82);\n        box-shadow: 0 2px 5px rgba(90,70,110,.10);\n    }\n\n    /* 노트의 왼쪽 바인더 구멍 느낌 */\n    [data-testid="stVerticalBlockBorderWrapper"]::after {\n        content: "";\n        position: absolute;\n        left: 8px;\n        top: 42px;\n        width: 9px;\n        height: 9px;\n        border-radius: 50%;\n        background: #d6c4dd;\n        box-shadow: 0 39px #d6c4dd, 0 78px #d6c4dd, 0 117px #d6c4dd, 0 156px #d6c4dd, 0 195px #d6c4dd;\n    }\n\n    .event-title {\n        font-family: "Jua", "Gowun Dodum", sans-serif;\n        font-size: 32px;\n        font-weight: 400;\n        line-height: 1.25;\n        margin-bottom: 22px;\n        color: #51445f;\n    }\n\n    .event-main-info {\n        display: flex;\n        gap: 12px;\n        margin-bottom: 18px;\n    }\n\n    .info-item {\n        flex: 1;\n        padding: 15px 18px;\n        border-radius: 12px;\n        background: #faf6ff;\n        border: 1px dashed #d9cce7;\n        box-shadow: inset 0 1px 0 rgba(255,255,255,0.9);\n    }\n\n    .info-label {\n        font-size: 14px;\n        font-weight: 700;\n        margin-bottom: 6px;\n        opacity: 0.72;\n    }\n\n    .info-value {\n        font-size: 20px;\n        font-weight: 750;\n    }\n\n    .event-sub-info {\n        display: grid;\n        gap: 8px;\n        font-size: 16px;\n        line-height: 1.55;\n        margin-bottom: 18px;\n    }\n\n    .event-description {\n        border-top: 1px solid #eee7f4;\n        padding-top: 16px;\n    }\n\n    .keyword-text {\n        font-size: 16px;\n        line-height: 1.7;\n    }\n\n    /* 다이어리 메모지 느낌의 핵심 정보 */\n    .diary-note {\n        position: relative;\n        margin: 11px 0 14px 0;\n        padding: 14px 18px 15px 18px;\n        border-radius: 8px 13px 10px 7px;\n        border: 1px dashed #d6c6df;\n        background: rgba(255,250,244,.88);\n        box-shadow: 2px 3px 0 rgba(219,203,227,.34);\n    }\n\n    .diary-note::after {\n        content: "";\n        position: absolute;\n        right: 10px;\n        top: 8px;\n        width: 12px;\n        height: 12px;\n        border-radius: 50%;\n        border: 2px solid #d9c9df;\n        background: #fffdf8;\n    }\n\n    .diary-label {\n        font-size: 13px;\n        font-weight: 700;\n        color: #8a7898;\n        margin-bottom: 4px;\n    }\n\n    .diary-value {\n        font-size: 18px;\n        color: #50465b;\n    }\n\n    /* 확장/수정 버튼 안의 아이콘이 글씨와 겹치지 않도록 아이콘 폰트를 강제로 분리 */\n    .stApp span[class*="material-symbols"],\n    .stApp span[class*="material-icons"],\n    .stApp i[class*="material-symbols"],\n    .stApp i[class*="material-icons"] {\n        font-family: "Material Symbols Outlined", "Material Icons" !important;\n        font-weight: normal !important;\n        font-style: normal !important;\n        letter-spacing: normal !important;\n    }\n\n    /* 정보 수정 / OCR 확인 영역 — 글자와 펼침 아이콘이 절대 겹치지 않게 */\n    .stApp [data-testid="stExpander"] summary {\n        min-height: 52px !important;\n        padding: 9px 16px !important;\n        border-radius: 14px !important;\n        display: flex !important;\n        align-items: center !important;\n        gap: 12px !important;\n        overflow: hidden !important;\n        box-sizing: border-box !important;\n    }\n    .stApp [data-testid="stExpander"] summary > div {\n        display: flex !important;\n        align-items: center !important;\n        min-width: 0 !important;\n        flex: 1 1 auto !important;\n    }\n    .stApp [data-testid="stExpander"] summary p {\n        margin: 0 !important;\n        padding: 0 !important;\n        line-height: 1.45 !important;\n        font-family: "Gowun Dodum", "Jua", sans-serif !important;\n        font-weight: 400 !important;\n        white-space: nowrap !important;\n        overflow: hidden !important;\n        text-overflow: ellipsis !important;\n    }\n    .stApp [data-testid="stExpander"] summary span[class*="material"] {\n        flex: 0 0 24px !important;\n        width: 24px !important;\n        min-width: 24px !important;\n        height: 24px !important;\n        line-height: 24px !important;\n        font-family: "Material Symbols Outlined", "Material Icons" !important;\n        font-weight: normal !important;\n        letter-spacing: normal !important;\n        overflow: hidden !important;\n    }\n\n    .event-display-title {\n        font-family: "Jua", "Gowun Dodum", sans-serif;\n        font-size: clamp(28px, 3.2vw, 42px);\n        line-height: 1.2;\n        font-weight: 400;\n        color: #4b4266;\n        margin: 4px 0 2px 0;\n        letter-spacing: -0.02em;\n    }\n    .event-display-subtitle {\n        font-family: "Gowun Dodum", "Jua", sans-serif;\n        font-size: 15px;\n        line-height: 1.45;\n        font-weight: 400;\n        color: #8b7f96;\n        margin: 0 0 18px 1px;\n    }\n\n    @media (max-width: 700px) {\n        .event-title { font-size: 25px; }\n        .event-main-info { flex-direction: column; }\n        .main-title-wrap .main-title { font-size: 32px; }\n    }\n    </style>\n', unsafe_allow_html=True)

# =========================================================
# OCR
# =========================================================
def ocr_image(image):
    """OCR.Space를 이용해 포스터의 글자를 읽습니다."""
    try:
        api_key = st.secrets.get("OCR_API_KEY", "").strip()
        if not api_key:
            return "", "OCR API 키가 설정되지 않았습니다. Streamlit Secrets에 OCR_API_KEY를 추가해주세요."

        image = image.convert("RGB")
        max_width = 1800

        if image.width > max_width:
            ratio = max_width / image.width
            image = image.resize((max_width, int(image.height * ratio)))

        image_bytes = io.BytesIO()
        image.save(image_bytes, format="JPEG", quality=90)
        image_data = image_bytes.getvalue()

        boundary = "----PosterCalendarBoundary"
        parts = [
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="language"\r\n\r\n'
                "kor\r\n"
            ),
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="isOverlayRequired"\r\n\r\n'
                "false\r\n"
            ),
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="OCREngine"\r\n\r\n'
                "3\r\n"
            ),
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="scale"\r\n\r\n'
                "true\r\n"
            ),
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="file"; filename="poster.jpg"\r\n'
                "Content-Type: image/jpeg\r\n\r\n"
            )
        ]

        body = "".join(parts).encode("utf-8")
        ending = f"\r\n--{boundary}--\r\n".encode("utf-8")
        request_body = body + image_data + ending

        request = urllib.request.Request(
            "https://api.ocr.space/parse/image",
            data=request_body,
            method="POST"
        )
        request.add_header(
            "Content-Type",
            f"multipart/form-data; boundary={boundary}"
        )
        request.add_header("apikey", api_key)
        request.add_header("User-Agent", "PosterCalendar/2.1")

        with urllib.request.urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))

        if result.get("IsErroredOnProcessing"):
            error_message = result.get("ErrorMessage") or result.get("ErrorDetails")
            if isinstance(error_message, list):
                error_message = " / ".join(str(x) for x in error_message)
            return "", f"포스터 글자 읽기에 실패했습니다: {error_message or 'OCR 처리 오류'}"

        parsed_results = result.get("ParsedResults", [])
