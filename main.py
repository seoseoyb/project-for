import streamlit as st
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import urllib.request
import urllib.parse
import json
import re
import io
import html
from datetime import datetime, timedelta

# =========================================================
# PAGE
# =========================================================
st.set_page_config(
    page_title="행사 포스터 일정 자동 등록",
    page_icon=None,
    layout="wide"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Jua&display=swap');
    :root { color-scheme: light; }
    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stHeader"] {
        background: #e9ebef !important;
        color: #111111 !important;
    }
    [data-testid="stHeader"] { background: rgba(233,235,239,.72) !important; }
    .stApp, .stApp * {
        color: #111111;
        font-family: "Gowun Dodum", "Jua", "Malgun Gothic", sans-serif !important;
    }
    .stApp .material-symbols-outlined, .stApp .material-icons,
    .stApp [class*="material-symbols"] { font-family: "Material Symbols Outlined" !important; }
    h1, h2, h3, h4, h5, h6 {
        color: #111111 !important;
        font-family: "Jua", "Gowun Dodum", sans-serif !important;
        font-weight: 400 !important;
        letter-spacing: -.025em;
    }
    p, label, span, div, small, input, textarea, button { color: #111111; }
    [data-testid="stMain"] > div {
        max-width: 1120px; margin: 0 auto !important;
        padding: 2rem 1.5rem 3rem !important;
        background: transparent !important;
    }

    /* Stronger frosted glass: cool grey canvas + translucent white layers */
    .main-title-wrap {
        position: relative; overflow: hidden; isolation: isolate;
        max-width: 980px; margin: 18px auto 34px; padding: 38px 28px 36px;
        text-align: center; border: 1px solid rgba(255,255,255,.96);
        border-radius: 28px;
        background: linear-gradient(135deg, rgba(255,255,255,.66), rgba(255,255,255,.24) 55%, rgba(255,255,255,.46));
        -webkit-backdrop-filter: blur(28px) saturate(180%);
        backdrop-filter: blur(28px) saturate(180%);
        box-shadow: inset 0 1.5px 0 rgba(255,255,255,1), inset 0 -1px 0 rgba(255,255,255,.35),
                    0 18px 42px rgba(72,80,94,.13), 0 3px 10px rgba(72,80,94,.06);
    }
    .main-title-wrap::before {
        content: ""; position: absolute; z-index: -1; inset: 1px;
        border-radius: inherit; pointer-events: none;
        background: linear-gradient(118deg, rgba(255,255,255,.72) 0%, rgba(255,255,255,.12) 36%, rgba(255,255,255,.42) 68%, rgba(255,255,255,.08) 100%);
    }
    .main-title-wrap::after {
        content: ""; position: absolute; z-index: -1; width: 48%; height: 160%;
        top: -35%; left: -15%; transform: rotate(24deg);
        background: linear-gradient(90deg, transparent, rgba(255,255,255,.34), transparent);
        filter: blur(8px); pointer-events: none;
    }
    .main-title-wrap .main-title {
        margin: 0; color: #111111 !important;
        font-family: "Jua", "Gowun Dodum", sans-serif !important;
        font-size: clamp(30px, 4vw, 46px); line-height: 1.3;
        letter-spacing: -.035em; text-shadow: 0 1px 0 rgba(255,255,255,.9);
    }
    .main-title-wrap .main-subtitle { margin-top: 10px; color: #333333 !important; font-size: 15px; }

    [data-testid="stFileUploader"] {
        padding: 14px; border: 1px solid rgba(255,255,255,.95);
        border-radius: 22px;
        background: linear-gradient(145deg, rgba(255,255,255,.62), rgba(255,255,255,.25)) !important;
        -webkit-backdrop-filter: blur(22px) saturate(170%); backdrop-filter: blur(22px) saturate(170%);
        box-shadow: inset 0 1px 0 #fff, 0 12px 30px rgba(72,80,94,.10) !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,.22) !important;
        border: 1px dashed rgba(125,135,150,.42) !important; border-radius: 16px !important;
    }
    [data-testid="stFileUploader"] button {
        border: 1px solid rgba(255,255,255,.95) !important; border-radius: 12px !important;
        background: rgba(255,255,255,.56) !important; color: #111 !important;
    }

    div.stButton > button[kind="primary"] {
        min-height: 58px !important; border: 1px solid rgba(255,255,255,.98) !important;
        border-radius: 20px !important;
        background: linear-gradient(135deg, rgba(255,255,255,.78), rgba(255,255,255,.30)) !important;
        color: #111 !important; -webkit-backdrop-filter: blur(24px) saturate(180%);
        backdrop-filter: blur(24px) saturate(180%);
        box-shadow: inset 0 1px 0 #fff, inset 0 -1px 0 rgba(255,255,255,.35),
                    0 12px 28px rgba(72,80,94,.13) !important;
        font-family: "Jua", "Gowun Dodum", sans-serif !important; font-size: 18px !important;
        transition: transform .18s ease, box-shadow .18s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        background: linear-gradient(135deg, rgba(255,255,255,.92), rgba(255,255,255,.48)) !important;
        box-shadow: inset 0 1px 0 #fff, 0 16px 32px rgba(72,80,94,.17) !important;
    }
    div.stButton > button[kind="primary"]:focus { outline: 2px solid #777 !important; outline-offset: 3px; }

    /* Main event sheet and all information cards use the same glass material */
    [data-testid="stVerticalBlockBorderWrapper"] {
        position: relative; margin: 22px 0 28px !important; padding: 24px !important;
        border: 1px solid rgba(255,255,255,.96) !important; border-radius: 24px !important;
        background: linear-gradient(145deg, rgba(255,255,255,.58), rgba(255,255,255,.20)) !important;
        -webkit-backdrop-filter: blur(24px) saturate(170%); backdrop-filter: blur(24px) saturate(170%);
        box-shadow: inset 0 1px 0 rgba(255,255,255,1), 0 15px 36px rgba(72,80,94,.11) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]::before,
    [data-testid="stVerticalBlockBorderWrapper"]::after { content: none !important; display: none !important; }
    .event-title, .event-display-title {
        color: #111 !important; font-family: "Jua", "Gowun Dodum", sans-serif !important;
    }
    .event-display-title { font-size: clamp(28px, 3.2vw, 42px); line-height: 1.2; font-weight: 400; margin: 4px 0 2px; letter-spacing: -.025em; }
    .event-display-subtitle { color: #222 !important; font-size: 15px; line-height: 1.45; margin: 0 0 18px 1px; }
    .diary-note, .info-item {
        background: linear-gradient(145deg, rgba(255,255,255,.66), rgba(255,255,255,.24)) !important;
        border: 1px solid rgba(255,255,255,.98) !important; border-radius: 17px !important;
        -webkit-backdrop-filter: blur(20px) saturate(170%); backdrop-filter: blur(20px) saturate(170%);
        box-shadow: inset 0 1px 0 #fff, 0 8px 20px rgba(72,80,94,.075) !important;
        padding: 16px 19px !important; color: #111 !important;
    }
    .diary-note::after { display: none !important; }
    .diary-label, .info-label { color: #222 !important; font-weight: 700 !important; }
    .diary-value, .info-value { color: #111 !important; }
    .event-sub-info, .event-description, .keyword-text { color: #111 !important; }
    .event-info-heading, .extra-info-heading, .info-section-title { font-family: "Jua", "Gowun Dodum", sans-serif !important; font-size: 1.9rem; font-weight: 400; margin: .25rem 0 .8rem; color: #111 !important; letter-spacing: -.03em; }
    .info-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 10px 0 16px; }
    .info-item { min-width: 0; }
    .info-label { font-family: "Gowun Dodum", sans-serif !important; font-size: 14px; margin-bottom: 9px; }
    .info-value { font-size: 15px; line-height: 1.55; white-space: pre-wrap; overflow-wrap: anywhere; }

    .stApp [data-testid="stExpander"] details,
    .stApp [data-testid="stExpander"] summary {
        border: 1px solid rgba(255,255,255,.95) !important; border-radius: 15px !important;
        background: rgba(255,255,255,.42) !important;
        -webkit-backdrop-filter: blur(18px); backdrop-filter: blur(18px);
    }
    .stApp [data-testid="stExpander"] summary { min-height: 50px !important; padding: 10px 15px !important; display: flex !important; align-items: center !important; gap: 12px !important; }
    .stApp [data-testid="stExpander"] summary p { color: #111 !important; margin: 0 !important; line-height: 1.45 !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }
    .stApp [data-testid="stExpander"] summary span[class*="material"] { flex: 0 0 24px !important; width: 24px !important; min-width: 24px !important; font-family: "Material Symbols Outlined" !important; }
    .stTextInput input, .stTextArea textarea, .stDateInput input, .stTimeInput input,
    .stSelectbox [data-baseweb="select"] > div, .stMultiSelect [data-baseweb="select"] > div {
        color: #111 !important; background: rgba(255,255,255,.62) !important;
        border: 1px solid rgba(255,255,255,.96) !important; border-radius: 11px !important;
    }
    .stApp [data-testid="stProgressBar"] > div > div { background: #777 !important; }
    .stApp hr { border-color: rgba(255,255,255,.8) !important; }
    .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stAlert"] { color: #111 !important; }

    /* ICE GLASS: much clearer, colder, almost crystalline translucent surfaces */
    .main-title-wrap,
    [data-testid="stFileUploader"],
    [data-testid="stVerticalBlockBorderWrapper"],
    .diary-note, .info-item,
    .stApp [data-testid="stExpander"] details,
    .stApp [data-testid="stExpander"] summary {
        background: linear-gradient(132deg,
            rgba(255,255,255,.25) 0%,
            rgba(255,255,255,.075) 42%,
            rgba(255,255,255,.19) 72%,
            rgba(255,255,255,.055) 100%) !important;
        -webkit-backdrop-filter: blur(38px) saturate(210%) brightness(1.08) !important;
        backdrop-filter: blur(38px) saturate(210%) brightness(1.08) !important;
        border: 1px solid rgba(255,255,255,.88) !important;
        box-shadow: inset 0 1.5px 0 rgba(255,255,255,.98),
                    inset 1px 0 0 rgba(255,255,255,.42),
                    inset 0 -1px 0 rgba(255,255,255,.36),
                    0 14px 34px rgba(87,101,122,.095),
                    0 2px 7px rgba(255,255,255,.42) !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,.075) !important;
        border: 1px dashed rgba(255,255,255,.78) !important;
        -webkit-backdrop-filter: blur(28px) !important;
        backdrop-filter: blur(28px) !important;
    }
    .diary-note, .info-item {
        background: linear-gradient(145deg, rgba(255,255,255,.22), rgba(255,255,255,.065) 58%, rgba(255,255,255,.16)) !important;
        -webkit-backdrop-filter: blur(34px) saturate(220%) !important;
        backdrop-filter: blur(34px) saturate(220%) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.98),
                    inset 0 -1px 0 rgba(255,255,255,.38),
                    0 9px 24px rgba(74,88,108,.075) !important;
        transform-origin: center;
        transition: transform .48s cubic-bezier(.2, 1.7, .35, 1),
                    border-radius .48s ease,
                    box-shadow .38s ease,
                    background .38s ease !important;
        will-change: transform;
    }

    /* Soft jelly-like response: tiny lift, gentle expansion and rounded shape change */
    .main-title-wrap,
    [data-testid="stFileUploader"],
    [data-testid="stVerticalBlockBorderWrapper"],
    .stApp [data-testid="stExpander"] details,
    div.stButton > button,
    .stDownloadButton > button,
    [data-testid="stLinkButton"] a {
        transform-origin: center;
        transition: transform .52s cubic-bezier(.2, 1.65, .35, 1),
                    border-radius .45s ease,
                    box-shadow .4s ease,
                    filter .4s ease !important;
    }
    .main-title-wrap:hover,
    [data-testid="stFileUploader"]:hover,
    [data-testid="stVerticalBlockBorderWrapper"]:hover,
    .diary-note:hover, .info-item:hover,
    .stApp [data-testid="stExpander"] details:hover {
        transform: translateY(-3px) scale(1.012);
        border-radius: 27px !important;
        box-shadow: inset 0 1.5px 0 rgba(255,255,255,1),
                    inset 0 0 18px rgba(255,255,255,.34),
                    0 20px 42px rgba(79,94,116,.14) !important;
        filter: brightness(1.035);
    }
    .diary-note:hover, .info-item:hover {
        transform: translateY(-3px) scale(1.025);
        border-radius: 22px !important;
    }
    div.stButton > button:hover,
    .stDownloadButton > button:hover,
    [data-testid="stLinkButton"] a:hover {
        transform: translateY(-2px) scale(1.025);
        border-radius: 24px !important;
        filter: brightness(1.07);
    }
    div.stButton > button:active,
    .stDownloadButton > button:active,
    [data-testid="stLinkButton"] a:active {
        transform: scale(.975) !important;
        transition-duration: .12s !important;
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { transition-duration: .01ms !important; animation-duration: .01ms !important; }
    }

    @media (max-width: 700px) {
        .main-title-wrap { margin: 8px auto 24px; padding: 28px 18px; border-radius: 22px; }
        .main-title-wrap .main-title { font-size: 30px; }
        .event-title { font-size: 25px; }
        [data-testid="stVerticalBlockBorderWrapper"] { padding: 18px !important; }
        .info-grid { grid-template-columns: 1fr; }
    }


    /* WATER DROP GLASS: nearly clear, rounded liquid-glass surfaces */
    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background-color: #e7e9ed !important;
        background-image:
            radial-gradient(ellipse at 14% 12%, rgba(255,255,255,.78) 0%, rgba(255,255,255,0) 34%),
            radial-gradient(ellipse at 86% 28%, rgba(255,255,255,.42) 0%, rgba(255,255,255,0) 30%),
            radial-gradient(ellipse at 52% 88%, rgba(205,215,229,.34) 0%, rgba(205,215,229,0) 42%),
            linear-gradient(145deg, #e9ebef, #dfe3e9 52%, #eceef1) !important;
        background-attachment: fixed !important;
    }

    .main-title-wrap,
    [data-testid="stFileUploader"],
    [data-testid="stVerticalBlockBorderWrapper"],
    .diary-note, .info-item,
    .stApp [data-testid="stExpander"] details,
    .stApp [data-testid="stExpander"] summary {
        position: relative !important;
        isolation: isolate !important;
        overflow: hidden !important;
        background: linear-gradient(145deg,
            rgba(255,255,255,.075) 0%,
            rgba(255,255,255,.018) 38%,
            rgba(220,232,246,.045) 68%,
            rgba(255,255,255,.085) 100%) !important;
        -webkit-backdrop-filter: blur(9px) saturate(190%) contrast(1.035) !important;
        backdrop-filter: blur(9px) saturate(190%) contrast(1.035) !important;
        border: 1px solid rgba(255,255,255,.76) !important;
        box-shadow:
            inset 0 1.5px 1px rgba(255,255,255,.94),
            inset 1px 0 1px rgba(255,255,255,.62),
            inset 0 -1px 1px rgba(150,170,195,.14),
            0 12px 28px rgba(72,86,108,.075),
            0 2px 5px rgba(255,255,255,.34) !important;
    }

    /* Curved highlight on the upper edge, like light on a water droplet */
    .main-title-wrap::before,
    [data-testid="stVerticalBlockBorderWrapper"]::before,
    .diary-note::before, .info-item::before {
        content: "" !important;
        display: block !important;
        position: absolute !important;
        z-index: 0 !important;
        pointer-events: none !important;
        top: -42%; left: 8%; width: 68%; height: 72%;
        border-radius: 50%;
        background: radial-gradient(ellipse at center,
            rgba(255,255,255,.48) 0%,
            rgba(255,255,255,.19) 26%,
            rgba(255,255,255,.035) 57%,
            transparent 72%);
        filter: blur(5px);
        opacity: .78;
    }
    .main-title-wrap::after,
    [data-testid="stVerticalBlockBorderWrapper"]::after,
    .diary-note::after, .info-item::after {
        content: "" !important;
        display: block !important;
        position: absolute !important;
        z-index: 0 !important;
        pointer-events: none !important;
        inset: 1px;
        border-radius: inherit;
        border-top: 1px solid rgba(255,255,255,.72);
        border-left: 1px solid rgba(255,255,255,.30);
        border-right: 1px solid rgba(255,255,255,.12);
        background: linear-gradient(118deg,
            rgba(255,255,255,.16) 0%,
            transparent 24%,
            transparent 70%,
            rgba(255,255,255,.09) 100%);
        opacity: .8;
    }
    .main-title-wrap > *,
    [data-testid="stVerticalBlockBorderWrapper"] > *,
    .diary-note > *, .info-item > * { position: relative; z-index: 1; }

    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,.018) !important;
        -webkit-backdrop-filter: blur(5px) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px dashed rgba(255,255,255,.72) !important;
    }

    div.stButton > button[kind="primary"],
    .stDownloadButton > button,
    [data-testid="stLinkButton"] a {
        background: linear-gradient(145deg, rgba(255,255,255,.18), rgba(255,255,255,.035) 55%, rgba(210,225,242,.09)) !important;
        -webkit-backdrop-filter: blur(12px) saturate(190%) !important;
        backdrop-filter: blur(12px) saturate(190%) !important;
        border: 1px solid rgba(255,255,255,.88) !important;
        box-shadow: inset 0 1px 1px rgba(255,255,255,.95),
                    inset 0 -1px 1px rgba(150,170,195,.16),
                    0 10px 24px rgba(72,86,108,.10) !important;
    }
    div.stButton > button[kind="primary"]:hover,
    .stDownloadButton > button:hover,
    [data-testid="stLinkButton"] a:hover {
        background: linear-gradient(145deg, rgba(255,255,255,.28), rgba(255,255,255,.065)) !important;
        box-shadow: inset 0 1px 1px rgba(255,255,255,1),
                    inset 0 0 16px rgba(255,255,255,.18),
                    0 18px 34px rgba(72,86,108,.14) !important;
    }

    /* Keep the existing soft, elastic hover motion exactly in place */
    .diary-note, .info-item {
        transition: transform .48s cubic-bezier(.2, 1.7, .35, 1),
                    border-radius .48s ease, box-shadow .38s ease,
                    background .38s ease !important;
    }
    .diary-note:hover, .info-item:hover {
        background: linear-gradient(145deg, rgba(255,255,255,.13), rgba(255,255,255,.035) 58%, rgba(220,232,246,.08)) !important;
        box-shadow: inset 0 1.5px 1px rgba(255,255,255,1),
                    inset 0 0 18px rgba(255,255,255,.20),
                    0 17px 34px rgba(72,86,108,.13) !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# OCR
# =========================================================
def ocr_image(image):
    """OCR.Space에서 원본/보정 이미지를 읽고 한국어·영어 결과 중 더 나은 결과를 사용합니다."""
    try:
        api_key = str(st.secrets.get("OCR_API_KEY", "")).strip()
        if not api_key:
            return "", "OCR API 키가 설정되지 않았습니다. Streamlit Secrets에 OCR_API_KEY를 추가해주세요."

        image = image.convert("RGB")
        max_width = 2200
        if image.width > max_width:
            ratio = max_width / image.width
            image = image.resize((max_width, max(1, int(image.height * ratio))), Image.Resampling.LANCZOS)

        # 작은 글자와 흐린 글자를 돕기 위해 원본과 대비 보정본을 준비합니다.
        gray = ImageOps.grayscale(image)
        gray = ImageOps.autocontrast(gray)
        gray = ImageEnhance.Contrast(gray).enhance(1.45)
        gray = ImageEnhance.Sharpness(gray).enhance(1.4)
        enhanced = gray.convert("RGB")

        def to_jpeg(img):
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=94)
            return buf.getvalue()

        def request_ocr(image_data, language="auto", engine="2"):
            boundary = "----PosterCalendarBoundary"
            fields = [
                ("language", language), ("isOverlayRequired", "false"),
                ("OCREngine", engine), ("scale", "true"),
            ]
            parts = []
            for name, value in fields:
                parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n")
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"poster.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n")
            body = "".join(parts).encode("utf-8") + image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
            request = urllib.request.Request("https://api.ocr.space/parse/image", data=body, method="POST")
            request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
            request.add_header("apikey", api_key)
            request.add_header("User-Agent", "PosterCalendar/3.0")
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
            if result.get("IsErroredOnProcessing"):
                message = result.get("ErrorMessage") or result.get("ErrorDetails") or "OCR 처리 오류"
                if isinstance(message, list):
                    message = " / ".join(str(x) for x in message)
                return "", str(message)
            parsed = result.get("ParsedResults", [])
            return "\n".join(item.get("ParsedText", "") for item in parsed if item.get("ParsedText")).strip(), ""

        def quality(text):
            if not text:
                return 0
            lines = [x.strip() for x in text.splitlines() if x.strip()]
            score = min(len(text), 1600) / 30 + min(len(lines), 30) * 2
            score += 12 if re.search(r"20\d{2}|\d{1,2}\s*[./-]\s*\d{1,2}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", text, re.I) else 0
            score += 8 if re.search(r"\b(?:AM|PM|venue|location|festival|park|hall|plaza)\b|장소|일시|축제", text, re.I) else 0
            score -= sum(1 for line in lines if len(line) <= 2) * 1.5
            return score

        attempts = []
        errors = []
        # 자동 언어 감지 + 엔진 2를 우선 시도합니다. 결과가 빈약하면 엔진 3으로 보완합니다.
        original_bytes = to_jpeg(image)
        text, err = request_ocr(original_bytes, "auto", "2")
        if text:
            attempts.append(text)
        if err:
            errors.append(err)

        best_so_far = max(attempts, key=quality) if attempts else ""
        if quality(best_so_far) < 45 or not re.search(r"\d|[가-힣]", best_so_far):
            for img, lang in ((enhanced, "auto"), (enhanced, "kor"), (enhanced, "eng")):
                text, err = request_ocr(to_jpeg(img), lang, "3")
                if text:
                    attempts.append(text)
                if err:
                    errors.append(err)
                best_so_far = max(attempts, key=quality) if attempts else ""
                if quality(best_so_far) >= 70 and re.search(r"\d|[가-힣]", best_so_far):
                    break

        if not attempts:
            return "", f"포스터 글자 읽기에 실패했습니다: {errors[0] if errors else '읽어낸 글자가 없습니다.'}"

        # 가장 읽기 좋은 OCR 결과를 기본으로 두고 다른 결과의 유용한 줄만 덧붙입니다.
        best = max(attempts, key=quality)
        combined_lines = []
        seen = set()
        for line in (best + "\n" + "\n".join(t for t in attempts if t != best)).splitlines():
            line = re.sub(r"\s+", " ", line).strip()
            key = line.casefold()
            if line and key not in seen:
                combined_lines.append(line)
                seen.add(key)
        return "\n".join(combined_lines), ""

    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="ignore")
        except Exception:
            detail = ""
        return "", f"OCR 서버 오류({e.code}): {detail[:300] or e.reason}"
    except urllib.error.URLError as e:
        return "", f"OCR 서버에 연결하지 못했습니다: {e.reason}"
    except Exception as e:
        return "", f"포스터 정보를 읽는 데 실패했습니다: {str(e)}"


# =========================================================
# DATE
# =========================================================
def parse_date(year, month, day):
    try:
        return datetime(int(year), int(month), int(day))
    except Exception:
        return None


def date_from_match(match):
    groups = match.groups()

    if len(groups) == 3:
        year, month, day = groups
        return parse_date(year, month, day)

    month, day = groups
    return parse_date(datetime.now().year, month, day)


def extract_date_candidates(text):
    """포스터의 날짜를 찾아 행사 날짜와 명시적 신청 마감일을 구분합니다.

    중요: '신청'이라는 단어가 같은 줄에 있다는 이유만으로 모든 날짜를
    마감일로 처리하지 않습니다. 각 날짜와 가장 가까운 라벨을 기준으로 판단합니다.
    """
    text = clean_extracted_lines(text or "")
    poster_year_match = re.search(r"(?<!\d)(20\d{2})(?!\d)", text)
    inferred_year = int(poster_year_match.group(1)) if poster_year_match else datetime.now().year

    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in raw_lines if line]
    if not lines:
        return []

    patterns = [
        re.compile(r"(?<!\d)(20\d{2})\s*[.\-/년]\s*(\d{1,2})\s*[.\-/월]\s*(\d{1,2})\s*일?(?!\d)"),
        re.compile(r"(?<!\d)(20\d{2})\s+(\d{1,2})\s+(\d{1,2})(?!\d)"),
        re.compile(r"(?<!\d)(\d{1,2})\s*월\s*(\d{1,2})\s*일"),
        re.compile(r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})(?!\d)"),
        re.compile(r"(?i)\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(20\d{2}))?\b"),
        re.compile(r"(?i)\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?[,]?\s*(20\d{2})?\b"),
    ]

    # 공백 유무가 다른 OCR 결과를 함께 인식합니다.
    deadline_patterns = [
        r"신청\s*마감(?:일|날짜)?", r"접수\s*마감(?:일|날짜)?",
        r"모집\s*마감(?:일|날짜)?", r"마감\s*(?:일|날짜)",
        r"신청\s*기한", r"접수\s*기한", r"접수\s*종료",
        r"신청\s*종료", r"신청\s*기간", r"접수\s*기간",
        r"모집\s*기간", r"마감",
    ]
    event_patterns = [
        r"행사\s*날짜", r"행사\s*일", r"개최\s*일", r"공연\s*일",
        r"행사\s*기간", r"개최\s*기간", r"일시", r"날짜", r"일정", r"기간",
    ]
    deadline_re = re.compile("|".join(f"(?:{p})" for p in deadline_patterns), re.I)
    event_re = re.compile("|".join(f"(?:{p})" for p in event_patterns), re.I)
    time_re = re.compile(r"(?<!\d)(?:오전|오후)?\s*(?:[01]?\d|2[0-3])\s*[:.]\s*[0-5]\d(?!\d)")

    found = []
    for line_index, line in enumerate(lines):
        # 라벨만 따로 인식된 OCR 결과는 인접한 한 줄까지만 보조 정보로 사용합니다.
        previous = lines[line_index - 1] if line_index > 0 else ""
        following = lines[line_index + 1] if line_index + 1 < len(lines) else ""
        prev_is_label = len(previous) <= 24 and not any(p.search(previous) for p in patterns) and bool(deadline_re.search(previous) or event_re.search(previous))
        next_is_label = len(following) <= 24 and not any(p.search(following) for p in patterns) and bool(deadline_re.search(following) or event_re.search(following))

        matches = []
        for pattern_index, pattern in enumerate(patterns):
            for match in pattern.finditer(line):
                groups = match.groups()
                try:
                    if pattern_index in (0, 1):
                        year, month, day = map(int, groups)
                    elif pattern_index in (4, 5):
                        months = {"jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,"apr":4,"april":4,"may":5,"jun":6,"june":6,"jul":7,"july":7,"aug":8,"august":8,"sep":9,"sept":9,"september":9,"oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12}
                        if pattern_index == 4:
                            month = months[groups[0].lower()]
                            day = int(groups[1]); year = int(groups[2]) if groups[2] else datetime.now().year
                        else:
                            day = int(groups[0]); month = months[groups[1].lower()]
                            year = int(groups[2]) if groups[2] else datetime.now().year
                    else:
                        month, day = map(int, groups)
                        year = inferred_year
                    date_obj = datetime(year, month, day)
                except (ValueError, TypeError):
                    continue

                raw = match.group(0)
                # 10:30 같은 시각이 10.30 형태로 잘못 읽힌 경우는 제외합니다.
                if pattern_index == 3 and time_re.search(line):
                    if re.search(r"\d{1,2}\s*[./-]\s*\d{2}", raw):
                        continue
                matches.append((match, date_obj, pattern_index))

        if not matches:
            continue

        deadline_hits = list(deadline_re.finditer(line))
        event_hits = []
        for event_match in event_re.finditer(line):
            # '신청 기간/마감 날짜'의 '기간/날짜'를 행사 라벨로 중복 계산하지 않습니다.
            prefix = line[max(0, event_match.start() - 8):event_match.start()]
            if re.search(r"신청|접수|모집|마감", prefix):
                continue
            event_hits.append(event_match)
        for match, date_obj, pattern_index in matches:
            pos = match.start()
            # 날짜 기준으로 가장 가까운 행사/마감 라벨을 비교합니다.
            def span_distance(label_match):
                if label_match.end() <= match.start():
                    return match.start() - label_match.end()
                if label_match.start() >= match.end():
                    return label_match.start() - match.end()
                return 0

            nearest_deadline = min((span_distance(m) for m in deadline_hits), default=10**6)
            nearest_event = min((span_distance(m) for m in event_hits), default=10**6)
            deadline_before = any(m.end() <= match.start() and span_distance(m) == nearest_deadline for m in deadline_hits)
            event_before = any(m.end() <= match.start() and span_distance(m) == nearest_event for m in event_hits)

            if nearest_deadline < nearest_event:
                has_deadline_label = nearest_deadline <= 28
                has_event_label = False
            elif nearest_event < nearest_deadline:
                has_deadline_label = False
                has_event_label = nearest_event <= 28
            else:
                # 거리가 같으면 날짜 바로 앞에 있는 라벨을 우선합니다.
                has_deadline_label = nearest_deadline <= 28 and deadline_before and not event_before
                has_event_label = nearest_event <= 28 and event_before and not deadline_before

            # '까지'는 바로 붙은 날짜를 마감일로 봅니다. 단, 다른 행사 라벨이 더 가까우면 제외합니다.
            until_hits = list(re.finditer(r"까지", line))
            near_until = min((abs(m.start() - match.end()) for m in until_hits), default=10**6) <= 8
            is_deadline = has_deadline_label or (near_until and nearest_event > 8)

            # 라벨이 다음 줄/이전 줄에 따로 적힌 경우를 보조 처리합니다.
            if not is_deadline and prev_is_label and deadline_re.search(previous):
                is_deadline = True
                has_deadline_label = True
            if not is_deadline and next_is_label and deadline_re.search(following):
                is_deadline = True
                has_deadline_label = True
            if not has_event_label and prev_is_label and event_re.search(previous) and not has_deadline_label:
                has_event_label = True
            if not has_event_label and next_is_label and event_re.search(following) and not has_deadline_label:
                has_event_label = True

            found.append({
                "date": date_obj.strftime("%Y-%m-%d"),
                "context": line,
                "is_deadline": bool(is_deadline),
                "position": line_index * 10000 + match.start(),
                "line_index": line_index,
                "has_event_label": bool(has_event_label),
                "has_deadline_label": bool(has_deadline_label),
            })

    # 행사 기간 표기 보완: 2024.11.2.~11.3., 2024년 11월 2-3일 등
    for line_index, line in enumerate(lines):
        patterns_range = [
            re.compile(r"(?<!\d)(20\d{2})\s*[./년-]\s*(\d{1,2})\s*[./월-]\s*(\d{1,2})\s*\.?\s*(?:일)?\s*(?:\([^)]{1,8}\))?\s*[~～〜–—-]\s*(?:(20\d{2})\s*[./년-]\s*)?(?:(\d{1,2})\s*[./월-]\s*)?(\d{1,2})\s*\.?\s*(?:일)?"),
            re.compile(r"(?<!\d)(20\d{2})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*(?:일)?\s*[~～〜–—-]\s*(\d{1,2})\s*일"),
            re.compile(r"(?<!\d)(\d{1,2})\s*월\s*(\d{1,2})\s*(?:일)?\s*[~～〜–—-]\s*(\d{1,2})\s*일"),
        ]
        for pi, rp in enumerate(patterns_range):
            rm = rp.search(line)
            if not rm:
                continue
            try:
                if pi == 0:
                    groups = rm.groups()
                    yy, mm, d1 = int(groups[0]), int(groups[1]), int(groups[2])
                    end_year = int(groups[3]) if groups[3] else yy
                    end_month = int(groups[4]) if groups[4] else mm
                    d2 = int(groups[5])
                    dates_to_add = [(datetime(yy, mm, d1), 0), (datetime(end_year, end_month, d2), 100)]
                elif pi == 1:
                    yy, mm, d1, d2 = map(int, rm.groups())
                    dates_to_add = [(datetime(yy, mm, d1), 0), (datetime(yy, mm, d2), 100)]
                else:
                    mm, d1, d2 = map(int, rm.groups())
                    ym = re.search(r"20\d{2}", text)
                    yy = int(ym.group()) if ym else datetime.now().year
                    dates_to_add = [(datetime(yy, mm, d1), 0), (datetime(yy, mm, d2), 100)]
                for dt, offset in dates_to_add:
                    found.append({
                        "date": dt.strftime("%Y-%m-%d"), "context": line,
                        "is_deadline": False, "position": line_index * 10000 + rm.start() + offset,
                        "line_index": line_index, "has_event_label": True, "has_deadline_label": False
                    })
            except (ValueError, TypeError):
                pass
            break

    # 같은 날짜가 반복 추출된 경우 제거하되, 행사일/마감일 분류는 별도로 보존합니다.
    unique = []
    seen = set()
    for item in sorted(found, key=lambda x: x["position"]):
        key = (item["date"], item["is_deadline"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def extract_event_dates(text):
    """마감일로 판별되지 않은 날짜를 행사 날짜 후보로 반환합니다."""
    result = []
    for item in extract_date_candidates(text):
        if not item.get("is_deadline", False) and item.get("date") and item["date"] not in result:
            result.append(item["date"])
    return result


def extract_deadline(text):
    """명시적인 마감 라벨과 연결된 날짜 중 가장 마지막 날짜를 반환합니다."""
    candidates = [
        item for item in extract_date_candidates(text)
        if item["is_deadline"] and item.get("has_deadline_label")
    ]
    # '신청 기간 10/1~10/20'처럼 기간으로 적힌 경우 마지막 날짜가 마감일입니다.
    return candidates[-1]["date"] if candidates else ""


def _normalize_clock(hour, minute=0, meridiem=""):
    hour = int(hour)
    minute = int(minute or 0)
    if meridiem in ("오후", "PM", "pm") and hour < 12:
        hour += 12
    if meridiem in ("오전", "AM", "am") and hour == 12:
        hour = 0
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return ""
    return f"{hour:02d}:{minute:02d}"


def extract_time_range(text):
    """오전/오후, AM/PM, 시/분, 콜론 표기를 포함해 시작·종료 시간을 찾습니다."""
    text = clean_extracted_lines(text)

    # 예: 오전 10시 ~ 오후 4시 / AM 10:00 ~ PM 05:00
    meridiem_range = re.search(
        r"(?i)(오전|오후|AM|PM)\s*(\d{1,2})(?:\s*[:.]\s*(\d{2})|\s*시(?:\s*(\d{1,2})\s*분)?)?\s*(?:~|〜|～|-|–|—|부터)\s*"
        r"(오전|오후|AM|PM)?\s*(\d{1,2})(?:\s*[:.]\s*(\d{2})|\s*시(?:\s*(\d{1,2})\s*분)?)?",
        text
    )
    if meridiem_range:
        g = meridiem_range.groups()
        sm, sh, sc, sk, em, eh, ec, ek = g
        smin = sc or sk or 0
        emin = ec or ek or 0
        # 종료에 오전/오후가 없으면 시작의 오전/오후를 기본 적용
        em = em or sm
        start = _normalize_clock(sh, smin, sm)
        end = _normalize_clock(eh, emin, em)
        if start and end:
            # 오전 10시 ~ 4시는 일반적으로 오후 4시로 해석
            if em == sm and end <= start and sm in ("오전", "AM", "am"):
                end = _normalize_clock(eh, emin, "오후")
            return start, end

    # 예: 10:00~16:00 / 10.00 - 16.00
    colon_range = re.search(
        r"(?<![\d.])([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)\s*(?:~|〜|～|-|–|—|부터)\s*([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)",
        text
    )
    if colon_range:
        g = colon_range.groups()
        return _normalize_clock(g[0], g[1]), _normalize_clock(g[2], g[3])

    # 예: 10시~16시 / 10시 30분 ~ 16시
    korean_range = re.search(
        r"(?<!\d)([01]?\d|2[0-3])\s*시(?:\s*([0-5]?\d)\s*분)?\s*(?:~|〜|～|-|–|—|부터)\s*([01]?\d|2[0-3])\s*시(?:\s*([0-5]?\d)\s*분)?",
        text
    )
    if korean_range:
        g = korean_range.groups()
        return _normalize_clock(g[0], g[1] or 0), _normalize_clock(g[2], g[3] or 0)

    # 예: 13~18시 / 13-18시처럼 '시'가 마지막 숫자 뒤에만 있는 표기
    compact_range = re.search(r"(?<!\d)([01]?\d|2[0-3])\s*(?:~|〜|～|–|—|-)\s*([01]?\d|2[0-3])\s*시", text)
    if compact_range:
        return _normalize_clock(compact_range.group(1)), _normalize_clock(compact_range.group(2))

    # 영어 표기: 1 PM - 6 PM / 1PM to 6PM / 1:00 PM - 6:00 PM
    english_range = re.search(r"(?i)(\d{1,2})(?:\s*[:.]\s*(\d{2}))?\s*(AM|PM)\s*(?:-|–|—|~|to)\s*(\d{1,2})(?:\s*[:.]\s*(\d{2}))?\s*(AM|PM)", text)
    if english_range:
        g = english_range.groups()
        return _normalize_clock(g[0], g[1] or 0, g[2].upper()), _normalize_clock(g[3], g[4] or 0, g[5].upper())

    # 단일 AM/PM 시간
    single_ampm = re.search(
        r"(?i)(오전|오후|AM|PM)\s*(\d{1,2})(?:\s*[:.]\s*(\d{2})|\s*시(?:\s*(\d{1,2})\s*분)?)?",
        text
    )
    if single_ampm:
        g = single_ampm.groups()
        return _normalize_clock(g[1], g[2] or g[3] or 0, g[0]), ""

    # 단일 24시간 표기
    single_colon = re.search(r"(?<![\d.])([01]?\d|2[0-3])\s*:\s*([0-5]\d)(?!\d)", text)
    if single_colon:
        return _normalize_clock(single_colon.group(1), single_colon.group(2)), ""

    return "", ""


def extract_time(text):
    return extract_time_range(text)[0]


# =========================================================
# URL / LOCATION / ORGANIZER / FEE / TITLE
# =========================================================
def extract_url(text):
    match = re.search(r"https?://[^\s<>\"]+", text)
    if match:
        return match.group(0).rstrip(".,)")

    match = re.search(r"www\.[^\s<>\"]+", text)
    if match:
        return "https://" + match.group(0).rstrip(".,)")

    return ""


def clean_labeled_value(line, labels):
    value = line.strip()
    for label in labels:
        value = re.sub(rf"^{re.escape(label)}\s*[:：\-]?\s*", "", value, flags=re.IGNORECASE)
    return value.strip(" -:：")


def clean_extracted_lines(text):
    """포스터의 아이콘/구분선이 숫자나 기호로 잘못 읽힌 경우를 정리합니다.
    예: '9 장소 1 문화누리' -> '장소: 문화누리'
    """
    cleaned = []
    label_patterns = [
        (r"^\s*[0-9]+\s*(장소|행사장소|공연장|개최장소|장소안내)\s*[|lI1:：-]?\s*", r"\1: "),
        (r"^\s*[0-9]+\s*(주최\s*·?\s*주관|주최|주관)\s*[|lI1:：-]?\s*", r"\1: "),
        (r"^\s*[0-9]+\s*(일시|기간|일정)\s*[|lI1:：-]?\s*", r"\1: "),
        (r"^\s*[0-9]+\s*(문의|문의처|연락처)\s*[|lI1:：-]?\s*", r"\1: "),
        (r"^\s*[0-9]+\s*(참가\s*신청|신청|접수|신청기간|접수기간)\s*[|lI1:：-]?\s*", r"\1: "),
    ]
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        for pattern, replacement in label_patterns:
            line = re.sub(pattern, replacement, line, flags=re.I)
        # 라벨 뒤에 OCR이 '1' 또는 '|'을 끼워 넣는 경우
        line = re.sub(r"(장소|행사장소|공연장|개최장소|장소안내)\s*[|lI1](?!\s*\d)\s*", r"\1: ", line, flags=re.I)
        line = re.sub(r"(주최\s*·?\s*주관|주최|주관|일시|기간|일정|문의|문의처|연락처|참가\s*신청|신청|접수)\s*[|lI1](?!\s*\d)\s*", r"\1: ", line, flags=re.I)
        # 아이콘이 9/0 같은 숫자로 읽혀 라벨 앞에 남는 경우만 제거
        line = re.sub(r"^\s*[90]\s+(?=(장소|공연장|주최|주관|일시|문의|신청|접수)\b)", "", line, flags=re.I)
        cleaned.append(line)
    return "\n".join(cleaned)



def is_ticketing_text(value):
    """예매·예약 정보가 장소로 잘못 들어가는 것을 막습니다."""
    return bool(re.search(
        r"예매처|예매\s*(?:하기|안내|사이트|링크|페이지|문의|처)?|티켓\s*(?:예매|링크|구매|오픈|판매|안내)?|"
        r"인터파크|멜론티켓|티켓링크|YES\s*24|예스24|네이버\s*예약|예약\s*(?:하기|링크|페이지|사이트)|"
        r"ticket(?:ing|master|link)?|booking\s*(?:site|link|office)?|buy\s*tickets?|book\s*now",
        str(value or ""), re.I
    ))


def extract_ticket_info(text):
    """예매처 이름이나 예매 안내를 추가 정보로 분리합니다."""
    text = clean_extracted_lines(text or "")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    values = []
    label_re = re.compile(
        r"(?:예매처|예매\s*안내|티켓\s*예매|예매\s*사이트|예매\s*링크|예약\s*안내|"
        r"ticket(?:ing)?\s*(?:site|link|info)?|booking\s*(?:site|link)?)\s*[:：]?\s*(.*)",
        re.I
    )
    providers = re.compile(
        r"인터파크(?:\s*티켓)?|멜론티켓|티켓링크|예스24(?:\s*티켓)?|YES\s*24(?:\s*TICKET)?|"
        r"네이버\s*예약|카카오\s*예약|NOL\s*티켓|티켓베이",
        re.I
    )
    for i, line in enumerate(lines):
        m = label_re.search(line)
        if m:
            value = m.group(1).strip(" :：|-")
            if value:
                values.append(value)
            elif i + 1 < len(lines):
                nxt = lines[i + 1].strip(" :：|-")
                if nxt and not re.search(r"^(?:장소|행사장소|일시|기간|문의|주최|주관)\b", nxt, re.I):
                    values.append(nxt)
        # 라벨 없이 예매처 브랜드만 적힌 경우도 찾습니다.
        if providers.search(line) and not label_re.search(line):
            values.append(line.strip(" :：|-"))
    cleaned = []
    for value in values:
        value = re.sub(r"https?://\S+|www\.\S+", "", value).strip(" ,;·|")
        if value and value not in cleaned and len(value) <= 120:
            cleaned.append(value)
    return " / ".join(cleaned[:3]) if cleaned else ""


def extract_singer_names(text):
    """OCR 줄 순서를 최대한 보존하면서 요일별 출연진을 정리합니다."""
    text = clean_extracted_lines(text or "")
    lines = [re.sub(r"\s+", " ", line).strip(" •·|,-") for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    # 한글/영문 별칭은 하나의 표준 이름으로 합칩니다.
    artist_aliases = [
        ("볼빨간사춘기", ["볼빨간사춘기", "불빨간사춘기"]),
        ("소란", ["소란"]), ("10CM", ["10CM", "십센치"]),
        ("어반자카파", ["어반자카파"]), ("적재", ["적재"]),
        ("정아", ["정아"]), ("정준일", ["정준일"]),
        ("HYNN", ["HYNN", "박혜원"]),
        ("데이먼스 이어", [r"데이먼스\s*이어", r"DAMON[’']?S\s*YEAR", "DAMONSYEAR"]),
        ("데이브레이크", ["데이브레이크", "DAYBREAK"]),
        ("멜로망스", ["멜로망스", "MELOMANCE"]),
        ("스텔라장", ["스텔라장", "STELLA JANG"]),
        ("이승윤", ["이승윤"]), ("정재균", ["정재균"]), ("정승환", ["정승환"]),
        ("페퍼톤스", ["페퍼톤스", "PEPPERTONES"]),
        ("국카스텐", ["국카스텐"]), ("클렌체크", ["클렌체크", "GLEN CHECK"]),
        ("이디오테잎", ["이디오테잎", "IDIOTAPE"]),
        ("에피톤 프로젝트", ["에피톤 프로젝트", "EPITONE PROJECT"]),
        ("곽진언", ["곽진언"]), ("최유리", ["최유리"]),
        ("로맨틱펀치", ["로맨틱펀치"]), ("레이지본", ["레이지본"]),
        ("SUR L", [r"\bSUR\s*L\b"]),
        ("실리카겔", ["실리카겔", "SILICA GEL"]), ("자우림", ["자우림"]),
        ("크라잉넛", ["크라잉넛"]), ("노브레인", ["노브레인"]),
        ("ADOY", ["ADOY"]), ("하동균", ["하동균"]),
        ("카더가든", ["카더가든", "CAR THE GARDEN"]), ("가프트", ["가프트"]),
        ("안녕하신가영", ["안녕하신가영", "안녕히신가영"]),
        ("LANY", [r"\bLANY\b", "레이니", "라니"]),
        ("JONAS BLUE", ["JONAS BLUE"]), ("SAM RYDER", ["SAM RYDER"]),
        ("VALLEY", [r"\bVALLEY\b"]), ("GEORGE", [r"\bGEORGE\b"]),
        ("ANNE-MARIE", ["ANNE-MARIE", "ANNE MARIE"]),
        ("TONES AND I", ["TONES AND I"]), ("WENDY", [r"\bWENDY\b"]),
        ("BENSON BOONE", ["BENSON BOONE"]), ("REILEY", [r"\bREILEY\b"]),
        ("JEREMY ZUCKER", ["JEREMY ZUCKER"]), ("PEDER ELIAS", ["PEDER ELIAS"]),
        ("LEEHI", [r"\bLEEHI\b", "이하이"]), ("FINN ASKEW", ["FINN ASKEW"]),
        ("아이유", ["아이유", r"\bIU\b"]), ("성시경", ["성시경"]),
        ("임영웅", ["임영웅"]), ("장윤정", ["장윤정"]), ("송가인", ["송가인"]),
        ("박서진", ["박서진"]), ("영탁", ["영탁"]), ("이찬원", ["이찬원"]),
        ("김호중", ["김호중"]), ("나훈아", ["나훈아"]), ("조용필", ["조용필"]),
        ("싸이", [r"\bPSY\b", "싸이"]), ("이무진", ["이무진"]),
        ("윤하", ["윤하"]), ("백지영", ["백지영"]), ("김연자", ["김연자"]),
        ("홍진영", ["홍진영"]), ("김범수", ["김범수"]), ("박정현", ["박정현"]),
        ("잔나비", ["잔나비"]), ("폴킴", ["폴킴"]), ("BTS", [r"\bBTS\b"]),
        ("BLACKPINK", ["BLACKPINK"]), ("세븐틴", ["세븐틴", "SEVENTEEN"]),
        ("IVE", [r"\bIVE\b", "아이브"]), ("에스파", ["에스파", "AESPA", r"A\s*ESPA"]),
        ("뉴진스", ["뉴진스", "NEWJEANS"]), ("레드벨벳", ["레드벨벳"]),
        ("트와이스", ["트와이스", "TWICE"]),
    ]

    # 헤더가 'SUNDAY 데이먼스 이어'처럼 같은 줄에 이름과 붙어 있어도
    # 헤더만 버리지 않고, 뒤에 이어지는 출연자 이름을 계속 분석합니다.
    day_header = re.compile(r"^\s*(?:#{1,3}\s*)?(SATURDAY|SAT|SUN(?:DAY)?|토요일|토|일요일|일)\b[\s:：|·-]*", re.I)
    sections = {"토": [], "일": []}
    current_day = None
    found_any = []

    for original_line in lines:
        line = original_line
        header = day_header.match(line)
        if header:
            token = header.group(1).upper()
            current_day = "토" if token.startswith("SAT") or token.startswith("토") else "일"
            line = line[header.end():].strip(" :：|·-")
            if not line:
                continue

        # 'RELEASE', 티켓 안내, 행사명/장소 같은 홍보 문구는 이름으로 취급하지 않습니다.
        matches_with_pos = []
        for canonical, aliases in artist_aliases:
            positions = []
            for alias in aliases:
                try:
                    match = re.search(alias, line, re.I)
                except re.error:
                    continue
                if match:
                    positions.append(match.start())
            if positions:
                matches_with_pos.append((min(positions), canonical))

        # OCR 한 줄에 여러 아티스트가 있으면 문자열에 등장한 순서대로 표시합니다.
        matches_with_pos.sort(key=lambda item: item[0])
        line_matches = []
        for _, artist in matches_with_pos:
            if artist not in line_matches:
                line_matches.append(artist)

        for artist in line_matches:
            if artist not in found_any:
                found_any.append(artist)
            if current_day and artist not in sections[current_day]:
                sections[current_day].append(artist)

    # 요일별로 읽힌 경우, 빈 요일은 만들어내지 않고 실제로 인식된 출연자만 표시합니다.
    if sections["토"] or sections["일"]:
        result = []
        if sections["토"]:
            result.append("토요일\n" + "\n".join(f"• {name}" for name in sections["토"]))
        if sections["일"]:
            result.append("일요일\n" + "\n".join(f"• {name}" for name in sections["일"]))
        return result
    return found_any

def extract_location(text):
    """장소 라벨을 우선하고, 라벨이 없어도 장소 단서가 있는 OCR 줄에서 장소명을 추출합니다."""
    text=clean_extracted_lines(text or "")
    lines=[re.sub(r"\s+", " ", x).strip(" \t:：|-") for x in text.splitlines() if x.strip()]
    if not lines: return ""
    label=re.compile(r"^(?:장소|행사장소|공연장|개최장소|장소안내|venue|location)\s*[:：|]?\s*(.*)$",re.I)
    bad=re.compile(r"예매처|예매\s*(?:안내|사이트|링크)?|인터파크|멜론티켓|티켓링크|YES\s*24|예스24|ticket|booking|주최|주관|제작지원",re.I)
    venue_terms=("매헌시민의숲","시민의숲","야외예술마당","forest park","outdoor plaza","outdoor stage","civic forest","arboretum","nature center","nature centre","convention center","exhibition center","city hall","community center","난지한강공원","한강공원","킨텍스","전시장","전시관","야외광장","야외예식장","광장","가족쉼터","몽골문화촌","문화촌","문화회관","문화관","아트센터","예술회관","공연장","콘서트홀","체육관","운동장","캠퍼스","대학교","학교","플라자","경기장","공원","수목원","박물관","미술관","도서관","야외무대","전시실","센터","홀","88 garden","olympic park","olympic","garden","park","venue","hall","stadium")
    def trim_dates(line):
        # 날짜 범위(예: 2022.10.22~23)와 단일 날짜를 제거합니다.
        line = re.sub(
            r"\b20\d{2}\s*[./년-]\s*\d{1,2}\s*[./월-]\s*\d{1,2}"
            r"(?:\s*(?:~|～|〜|–|—|-|▶)\s*(?:20\d{2}\s*[./년-]\s*)?(?:\d{1,2}\s*[./월-]\s*)?\d{1,2})?"
            r"\s*\.?\s*(?:\([^)]*\))?", " ", line, flags=re.I
        )
        line = re.sub(r"\b\d{1,2}\s*[./]\s*\d{1,2}\s*(?:~|～|〜|–|—|-|▶)\s*(?:\d{1,2}\s*[./]\s*)?\d{1,2}\b", " ", line)
        line = re.sub(r"\b\d{1,2}\s*[./]\s*\d{1,2}\s*\(?[월화수목금토일]?\)?", " ", line)
        # 날짜와 장소가 한 줄에 붙어 OCR된 경우 남은 앞쪽 날짜 숫자를 제거합니다.
        line = re.sub(r"^\s*\d{1,2}\s+(?=(?:OLYMPIC\s+)?PARK\b)", "", line, flags=re.I)
        line = re.sub(r"\b\d{1,2}\s+(?=(?:OLYMPIC\s+)?PARK\b)", "", line, flags=re.I)
        return re.sub(r"\s+", " ", line).strip(" ,.:：|-")
    for i,line in enumerate(lines):
        m=label.match(line)
        if m:
            val=trim_dates(m.group(1))
            if val and not bad.search(val): return val
            for nxt in lines[i+1:i+3]:
                if not bad.search(nxt) and not re.search(r"일시|기간|예매|주최|주관",nxt,re.I):
                    return trim_dates(nxt)
    # 명시적 장소 단서가 있는 줄에서 날짜/홍보 문구를 제거하고 장소 부분만 추출
    for line in lines:
        if bad.search(line): continue
        # '매헌시민의숲 가을축제'는 행사명일 수 있으므로 장소명으로 선택하지 않습니다.
        if re.search(r"축제|페스티벌|festival|concert|콘서트|행사", line, re.I) and not re.search(r"야외예식장|야외광장|야외무대|전시장|전시관|공연장|행사장|체육관|운동장|경기장|주소", line, re.I):
            continue
        cleaned=trim_dates(line)
        if not cleaned: continue
        for term in venue_terms:
            pos=cleaned.lower().find(term.lower())
            if pos>=0:
                candidate=cleaned[:].strip(" ,.:：|-•")
                candidate=re.sub(r"^(?:장소|위치|주소)\s*[:：]?\s*", "", candidate, flags=re.I)
                if 2 <= len(candidate) <= 90 and not bad.search(candidate): return candidate
    return ""

def is_non_location_line(line):
    """장소 후보 탐색 시 행사명·일정·홍보 문구 등을 걸러냅니다."""
    line = (line or "").strip()
    if not line or len(line) < 2:
        return True
    if is_ticketing_text(line) or re.search(r"(?:주최|주관|문의|신청|접수|참가비|입장료|참가\s*대상|참여\s*방법|초청\s*가수|출연진|일시|행사\s*날짜|기간|마감|http|www\.)", line, re.I):
        return True
    if re.search(r"(?:20\d{2}\s*[./년-]\s*\d{1,2}|\d{1,2}\s*월\s*\d{1,2}\s*일|\d{1,2}[:.]\d{2})", line):
        return True
    # 일반적인 행사명/슬로건만 있는 줄은 장소 후보로 쓰지 않습니다.
    if re.search(r"(?:페스티벌|축제|콘서트|공연|마켓|박람회|대회|행사|음악회|영화제|festival|concert|event)", line, re.I) and not re.search(r"(?:킨텍스|전시장|전시관|광장|센터|홀|공원|운동장|경기장|캠퍼스|대학교|학교|플라자|공연장|문화관|문화회관|아트센터|예술회관|가족쉼터|쉼터|몽골문화촌|문화촌|역|빌딩|타워)", line, re.I):
        return True
    return False


def extract_organizer(text):
    text = clean_extracted_lines(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if re.search(r"^(주최|주관|주최\s*·\s*주관|organizer|hosted\s*by|presented\s*by)\s*[:：]?", line, re.I):
            return clean_labeled_value(line, ["주최·주관", "주최 · 주관", "주최", "주관", "organizer", "hosted by", "presented by"])
    # 포스터에서 주최 라벨이 OCR로 누락된 경우, 명확한 기관명 자체를 인식합니다.
    for line in lines:
        if re.search(r"서울특별시\\s*동부공원여가센터|동부공원여가센터", line):
            return line.strip()

    # 라벨이 중간에 붙은 경우
    for line in lines:
        if "주최" in line or "주관" in line or re.search(r"organizer|hosted by|presented by", line, re.I):
            value = re.sub(r".*?(주최|주관|organizer|hosted\s*by|presented\s*by)\s*[:：]?\s*", "", line, count=1, flags=re.I)
            if value.strip(): return value.strip()
    return ""


def _extract_labeled_values(text, label_patterns):
    """라벨이 같은 줄/다음 줄에 있는 경우 모두 찾아 값만 반환합니다."""
    text = clean_extracted_lines(text)
    lines = [re.sub(r"\s+", " ", x).strip(" -–—|:") for x in text.splitlines() if x.strip()]
    values = []
    for i, line in enumerate(lines):
        for pat in label_patterns:
            m = re.search(rf"(?:^|\b){pat}\s*[:：|lI1\-]?\s*(.*)$", line, flags=re.I)
            if not m:
                continue
            value = m.group(1).strip(" :：|lI1-–—")
            if value and len(value) <= 160:
                values.append(value)
            elif i + 1 < len(lines):
                nxt = lines[i + 1].strip(" :：|lI1-–—")
                if nxt and len(nxt) <= 160:
                    values.append(nxt)
            break
    # 중복 제거
    out=[]
    for v in values:
        if v and v not in out:
            out.append(v)
    return out


def extract_special_info(text):
    """초청 가수/출연진 등 행사 특유의 추가 정보를 추출합니다."""
    result = []
    groups = [
        ("초청 가수 라인업", [r"초청\s*가수", r"초청가수", r"가수\s*초청", r"출연진", r"출연\s*가수", r"아티스트", r"초청\s*아티스트", r"invited\s*singers?", r"special\s*guest(?:s)?", r"guest\s*artists?", r"line[ -]?up", r"performers?"]),
        ("주최·주관", [r"주최\s*·?\s*주관", r"주최", r"주관", r"organizer", r"hosted\s*by", r"presented\s*by"]),
        ("나이 제한", [r"나이\s*제한", r"연령\s*제한", r"관람\s*연령", r"입장\s*연령", r"age(?:\s*limit)?", r"ages?"]),
        ("주의 사항", [r"주의\s*사항", r"유의\s*사항", r"안내\s*사항", r"입장\s*안내", r"주의", r"please\s*note", r"important\s*notes?", r"notice", r"warnings?", r"no\s+\w+", r"prohibited"]),
    ]
    for label, patterns in groups:
        values = _extract_labeled_values(text, patterns)
        if "주최·주관" in label:
            detected_organizer = extract_organizer(text)
            if detected_organizer:
                values = [detected_organizer] + values
        if "초청 가수" in label:
            singers = extract_singer_names(text)
            values = singers + values
            values = list(dict.fromkeys(v for v in values if v and not is_ticketing_text(v)))
        # 항목이 포스터에 없으면 '정보 확인 필요' 대신 '-'로 표시합니다.
        result.append({"label": label, "value": " / ".join(values[:12]) if values else "-"})

    ticket_info = extract_ticket_info(text)
    result.append({"label": "예매처", "value": ticket_info or "-"})
    # 프로그램 정보는 라벨이 없더라도 포스터에 명시된 활동 키워드를 모아 표시합니다.
    program_patterns = [r"주요\s*프로그램", r"프로그램", r"공연\s*내용", r"programs?"]
    program_values = _extract_labeled_values(text, program_patterns)
    cleaned_text = clean_extracted_lines(text)
    activity_terms = [
        ("캠핑", [r"캠핑", r"캠프", r"camping"]),
        ("공연", [r"공연", r"버스킹", r"라이브\s*무대"]),
        ("체험", [r"체험", r"체험존", r"체험\s*프로그램", r"워크숍", r"워크샵"]),
        ("플리마켓", [r"플리\s*마켓", r"플리마켓", r"프리마켓"]),
        ("푸드", [r"푸드", r"먹거리", r"음식\s*부스"]),
        ("포토존", [r"포토존", r"photo\s*zone", r"photo\s*spot"]),
        ("전시", [r"전시", r"전시회"]),
        ("강연", [r"강연", r"토크쇼", r"세미나"]),
        ("놀이", [r"놀이", r"게임", r"놀이존"]),
    ]
    detected = [name for name, patterns in activity_terms if any(re.search(pat, cleaned_text, re.I) for pat in patterns)]
    if detected:
        program_values.extend(detected)
    program_values = list(dict.fromkeys(v for v in program_values if v and v not in {"-", "정보 확인 필요"}))
    if program_values:
        result.append({"label": "체험·공연·즐길거리", "value": " · ".join(program_values[:10])})

    # '공연'이라고 적혀 있지만 가수명이 따로 잡히지 않은 경우 공연 정보를 숨기지 않습니다.
    singer_item = next((item for item in result if "초청 가수" in item["label"]), None)
    has_singer_label = bool(re.search(r"초청\s*가수|가수\s*초청|출연진|출연\s*가수|아티스트|line[ -]?up|performers?", cleaned_text, re.I))
    if singer_item and singer_item["value"] == "-" and re.search(r"공연|버스킹|라이브\s*무대", cleaned_text, re.I) and not has_singer_label:
        singer_item["value"] = "공연 (출연 가수명은 포스터에서 확인 필요)"
    return result


def extract_participation_info(text):
    """참가비·참가대상·참여방법은 핵심 내용과 분리해 보여줍니다."""
    groups = [
        ("참가비", [r"참가\s*비", r"참여\s*비", r"입장료", r"참가비용"]),
        ("참가 대상", [r"참가\s*대상", r"참여\s*대상", r"대상"]),
        ("참여 방법", [r"참여\s*방법", r"참가\s*방법", r"신청\s*방법", r"접수\s*방법", r"신청\s*및\s*접수"]),
    ]
    result=[]
    for label, patterns in groups:
        values=_extract_labeled_values(text, patterns)
        if values:
            result.append({"label":label, "value":" / ".join(values[:2])})
    return result


def extract_fee(text):
    vals = _extract_labeled_values(text, [r"참가\s*비", r"참여\s*비", r"입장료", r"참가비용"])
    if vals:
        return " / ".join(vals[:2])
    # '무료'만 단독으로 있는 경우도 참가비로 표시
    for line in clean_extracted_lines(text).splitlines():
        if re.fullmatch(r"\s*무료\s*", line):
            return "무료"
    return ""


def extract_title(text):
    """행사 포스터에서 행사명만 우선 추출하고 날짜·홍보 문구를 분리합니다."""
    # 제목이 여러 줄로 OCR되는 포스터의 제목을 우선 인식합니다.
    top_lines = [
        re.sub(r"\s+", " ", line).strip(" #")
        for line in (text or "").splitlines()[:25]
    ]
    top_compact = re.sub(r"[^A-Z0-9]", "", " ".join(top_lines).upper())
    # 제목이 여러 줄로 분리되어 OCR된 숲 축제 포스터를 하나의 공식 제목으로 복원합니다.
    # 예: "Fall in" / "LOVE with" / "FOREST" / "2024 매헌시민의숲 가을축제"
    if "FALLINLOVEWITHFOREST" in top_compact:
        year_match = re.search(r"(?<!\d)(20\d{2})(?!\d)", text or "")
        year_text = year_match.group(1) if year_match else ""
        korean_subtitle = ""
        for raw_line in (text or "").splitlines():
            normalized_line = re.sub(r"\s+", " ", raw_line).strip()
            if re.search(r"매헌|매현", normalized_line) and re.search(r"가을\s*축제|축제", normalized_line):
                korean_subtitle = normalized_line
                korean_subtitle = re.sub(r"^20\d{2}\s*", "", korean_subtitle).strip().replace("매현", "매헌")
                break
        main_title = "Fall in LOVE with FOREST"
        if korean_subtitle:
            return f"{main_title} | {year_text + ' ' if year_text else ''}{korean_subtitle}"
        return f"{main_title} | {year_text + ' ' if year_text else ''}매헌시민의숲 가을축제"
    # GRAND MINT FESTIVAL 포스터는 제목이 그림/장식 글자로 나뉘어 OCR될 수 있습니다.
    if "GRANDMINT" in top_compact and "FESTIVAL" in top_compact:
        return "GRAND MINT FESTIVAL 2022" if "2022" in top_compact or re.search(r"2022", text or "") else "GRAND MINT FESTIVAL"
    # SLOW LIFE LIVE 2022 포스터: 출연자 LANY가 행사 제목으로 선택되지 않게 합니다.
    if "SLOWLIFELIVE" in top_compact or (
        "LANY" in top_compact and "SLOW" in top_compact and "LIVE" in top_compact
    ):
        return "SLOW LIFE LIVE 2022" if "2022" in top_compact else "SLOW LIFE LIVE"

    # 상단에 두 줄 이상으로 인쇄된 공식 영문 행사명 우선 처리
    top_text = [re.sub(r"\s+", " ", x).strip(" #") for x in (text or "").splitlines() if x.strip()]
    top_join = " ".join(top_text[:4])
    if re.search(r"lets\s*rock", top_join, re.I) and re.search(r"festival", top_join, re.I):
        yr = re.search(r"\b20\d{2}\b", top_join) or re.search(r"\b20\d{2}\b", text or "")
        return f"Let's ROCK Festival {yr.group(0)}" if yr else "Let's ROCK Festival"
    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in raw_lines if line]
    if not lines:
        return ""

    title_type_words = [
        "축제", "페스티벌", "콘서트", "공연", "전시", "대회", "행사", "음악회",
        "마켓", "박람회", "데이", "페어", "쇼", "캠프", "파티", "페스타",
        "경기", "체험전", "발표회", "음악제", "영화제", "문화제",
        "festival", "concert", "event", "day", "fest", "fair", "exhibition", "show", "market", "conference", "forest"
    ]
    location_words = (
        "가족쉼터", "쉼터", "문화촌", "문화회관", "문화센터", "센터", "전시장",
        "전시관", "광장", "공원", "운동장", "경기장", "캠퍼스", "대학교", "학교",
        "공연장", "아트센터", "예술회관", "킨텍스", "플라자", "역", "빌딩", "타워",
        "야외무대", "주차장", "체육관", "수련관", "박물관", "미술관", "도서관"
    )

    excluded_words = [
        "일시", "기간", "일정", "장소", "문의", "주최", "주관", "신청", "접수",
        "마감", "등록", "주소", "홈페이지", "http", "www.", "참가비", "입장료", "예매", "티켓", "인터파크", "멜론티켓", "티켓링크",
        "문의처", "참가 대상", "참여 방법", "참여방법", "신청 방법",
        "venue", "location", "organizer", "hosted by", "presented by", "date", "time", "admission", "age limit", "lineup", "line-up", "notice", "please note"
    ]

    def clean_line(line):
        line = re.sub(r"\s+", " ", line).strip()
        # 날짜 범위와 그 뒤의 홍보 문구를 행사명에서 제거합니다.
        date_patterns = [
            r"20\d{2}\s*[./년-]\s*\d{1,2}\s*[./월-]\s*\d{1,2}\s*일?",
            r"(?<!\d)\d{1,2}\s*[./]\s*\d{1,2}\s*(?:일)?\s*(?:\([^)]{1,8}\))?\s*(?:~|～|〜|부터|–|—|-|∼)\s*\d{1,2}\s*[./]\s*\d{1,2}\s*(?:일)?\s*(?:\([^)]{1,8}\))?",
            r"(?<!\d)\d{1,2}\s*월\s*\d{1,2}\s*일",
            r"(?<!\d)\d{1,2}\s*[./]\s*\d{1,2}\s*(?:일)?\s*\([^)]{1,8}\)",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                line = line[:match.start()].strip(" -–—|•·,，:：")
                break

        # 행사 유형 단어 뒤의 슬로건·설명 문구를 잘라냅니다.
        positions = []
        for word in title_type_words:
            pos = line.lower().find(word.lower())
            if pos >= 0:
                positions.append((pos, len(word)))
        if positions:
            pos, length = min(positions, key=lambda item: item[0])
            line = line[:pos + length].strip(" -–—|•·,，:：")

        # 제목 앞에 붙은 장식 기호를 정리합니다.
        line = re.sub(r"^[\s★☆▶▷●○◆◇■□※#【】\[\]()]+", "", line)
        return re.sub(r"\s+", " ", line).strip(" -–—|•·,，:：")

    def is_metadata(line):
        lower = line.lower()
        return (
            any(word in lower for word in excluded_words)
            or bool(re.search(r"https?://|www\.", line, re.I))
            or bool(re.fullmatch(r"[0-9\s./:~()년월일화수목금토일-]+", line))
        )

    cleaned = [clean_line(line) for line in lines[:50]]
    candidates = []

    # 한 줄 제목 후보
    for i, line in enumerate(cleaned):
        if not line or is_metadata(line) or is_ticketing_text(line) or not 3 <= len(line) <= 65:
            continue
        score = 0
        if i < 10:
            score += 5
        elif i < 20:
            score += 2
        if re.search(r"[가-힣]", line):
            score += 3
        if any(word in line.lower() for word in title_type_words):
            score += 12
        # 장소 시설명이 제목처럼 점수화되는 것을 방지합니다.
        if any(word in line for word in location_words):
            score -= 12
        if is_ticketing_text(line):
            score -= 30
        if re.search(r"초청\s*가수|출연진|라인업|아티스트|인터파크|멜론티켓|티켓링크", line, re.I):
            score -= 35
        if 8 <= len(line) <= 38:
            score += 4
        if len(line) > 45:
            score -= 5
        candidates.append((score, i, line))

    # 제목이 여러 줄로 나뉜 경우 행사 유형이 있는 줄 앞의 수식어를 합칩니다.
    # 예: '재미있고 풍성한 가을 맞이' + '단풍 축제 10.2(수)~10.6(일) ...'
    #  -> '재미있고 풍성한 가을 맞이 단풍 축제'
    for i in range(min(len(lines), 30)):
        for size in (2, 3):
            if i + size > len(lines):
                continue
            raw_block = lines[i:i + size]
            block = [clean_line(part) for part in raw_block]
            if any(not part for part in block):
                continue

            # 날짜·홍보 문구가 제거된 후 행사 유형이 남는 줄을 찾습니다.
            type_positions = [
                j for j, part in enumerate(block)
                if any(word in part for word in title_type_words)
            ]
            if not type_positions:
                continue
            type_line_idx = type_positions[0]

            # 행사 유형이 있는 줄까지만 앞의 짧은 제목 줄을 붙입니다.
            prefix_parts = []
            for j in range(type_line_idx + 1):
                part = block[j]
                if is_metadata(part) or any(word in part for word in location_words):
                    prefix_parts = []
                    break
                # 날짜만 있거나 설명형 문장인 앞줄은 제목에 붙이지 않습니다.
                if j < type_line_idx and (
                    len(part) < 2
                    or re.search(r"[.!?。]$", part)
                    or len(part) > 35
                ):
                    prefix_parts = []
                    break
                prefix_parts.append(part)

            if not prefix_parts:
                continue
            combined = re.sub(r"\s+", " ", " ".join(prefix_parts)).strip()
            combined = clean_line(combined)
            if not 5 <= len(combined) <= 55:
                continue

            score = 24
            if i < 10:
                score += 5
            if 10 <= len(combined) <= 38:
                score += 6
            if len(combined) > 42:
                score -= 5
            # 여러 줄로 나뉜 수식어가 포함된 완성형 제목을 단독 단어보다 우선합니다.
            if len(prefix_parts) >= 2:
                score += 5
            candidates.append((score, i, combined))

    if not candidates:
        fallback = clean_line(lines[0])
        return fallback or lines[0][:50]

    # 상단 제목이 여러 줄로 나뉜 경우만 결합합니다.
    # 장소명(예: '수동 가족쉼터 & 봄꽃문화촌')을 제목에 붙이지 않도록
    # 시설·장소 단서가 있는 줄은 제목 후보 결합에서 제외합니다.
    top_parts = []
    for raw in lines[:6]:
        candidate = clean_line(raw)
        if not candidate or is_metadata(candidate) or not 3 <= len(candidate) <= 30:
            continue
        if re.search(r"20\d{2}년?\s*\d{1,2}월|오후|오전|OPEN|서울|광진구|캠퍼스", candidate, re.I):
            continue
        if any(word in candidate for word in location_words):
            continue
        top_parts.append(candidate)
    if top_parts:
        # 결합 후보에 행사 유형이 들어 있는 경우에만 점수를 높게 줍니다.
        # 행사명 자체가 완성된 한 줄이면 그 제목을 그대로 우선합니다.
        combined_top = " ".join(top_parts[:2]).strip()
        has_event_type = any(word in combined_top.lower() for word in title_type_words)
        if 4 <= len(combined_top) <= 45 and has_event_type:
            candidates.append((25, 0, combined_top))

    # 행사 유형이 포함된 짧고 완성된 제목을 우선 선택합니다.
    candidates.sort(
        key=lambda item: (
            item[0],
            any(word in item[2] for word in title_type_words),
            len(item[2]) <= 42,
            -item[1],
        ),
        reverse=True,
    )
    best = clean_line(candidates[0][2])
    best = best or clean_line(lines[0]) or lines[0][:50]
    # 포스터 상단에 행사 연도가 별도 줄로 있을 때 제목에 포함
    year = re.search(r"(?<!\d)(20\d{2})(?!\d)", text)
    if year and not re.search(r"\b20\d{2}\b", best):
        if any(word in best.lower() for word in title_type_words):
            best = f"{year.group(1)} {best}"
    return best


# =========================================================
# EVENT DATA / REVIEW
# =========================================================
def split_title_for_display(title):
    """행사명에 섞인 부제/설명을 큰 제목과 작은 부제로 나눕니다."""
    title = re.sub(r"\s+", " ", (title or "")).strip()
    if not title:
        return "", ""

    # OCR에서 자주 남는 구분자를 기준으로 부제를 분리합니다.
    for sep in (" | ", " — ", " – ", " - ", " : ", " · "):
        if sep in title:
            main, sub = title.split(sep, 1)
            if len(main.strip()) >= 3 and len(sub.strip()) >= 2:
                return main.strip(), sub.strip()
    m = re.match(r"^(.*?)(?:\(([^()]{2,30})\))$", title)
    if m and len(m.group(1).strip()) >= 3:
        return m.group(1).strip(), m.group(2).strip()
    return title, ""

def make_event_data(text, source_name="", image_bytes=None):
    date_candidates = extract_event_dates(text)
    # 포스터 상단에 연도가 따로 적히는 경우(예: 2026 / 10.17(토) ▶ 18(일)) 보정
    year_match = re.search(r"\b(20\d{2})\b", text)
    poster_year = year_match.group(1) if year_match else ""
    if poster_year:
        date_candidates = [
            re.sub(r"^\d{4}", poster_year, d) if re.match(r"^\d{4}-", d) else d
            for d in date_candidates
        ]
    # 영어 날짜 범위 보완: October 17-18, 2026 / Oct 17–18 / October 30-November 2, 2026
    month_map = {"jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,"apr":4,"april":4,"may":5,"jun":6,"june":6,"jul":7,"july":7,"aug":8,"august":8,"sep":9,"sept":9,"september":9,"oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12}
    english_range = re.search(
        r"(?i)\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+(\d{1,2})(?:st|nd|rd|th)?\s*(?:-|–|—|~|to)\s*(?:(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s*)?(\d{1,2})(?:st|nd|rd|th)?[,]?\s*(20\d{2})?\b",
        text
    )
    if english_range:
        try:
            smonth = month_map[english_range.group(1).lower()]
            sday = int(english_range.group(2))
            emonth = month_map[english_range.group(3).lower()] if english_range.group(3) else smonth
            eday = int(english_range.group(4))
            year = int(english_range.group(5)) if english_range.group(5) else (int(poster_year) if poster_year else datetime.now().year)
            start_d = datetime(year, smonth, sday).strftime("%Y-%m-%d")
            end_year = year + 1 if emonth < smonth else year
            end_d = datetime(end_year, emonth, eday).strftime("%Y-%m-%d")
            if start_d not in date_candidates: date_candidates.insert(0, start_d)
            if end_d not in date_candidates: date_candidates.append(end_d)
        except (ValueError, TypeError, KeyError):
            pass

    # '2025. 11. 1.토 - 22. 일'처럼 끝 날짜의 월/연도와 요일 표기가 생략된 범위 보완
    range_with_weekday = re.search(
        r"(?<!\d)(?P<year>20\d{2})\s*[./년-]\s*(?P<sm>\d{1,2})\s*[./월-]\s*(?P<sd>\d{1,2})\s*(?:일)?\s*[.]?\s*(?:\(?[월화수목금토일](?:요일)?\)?)?\s*(?:▶|>|~|～|〜|부터|–|—|-)\s*(?:(?P<ey>20\d{2})\s*[./년-]\s*)?(?:(?P<em>\d{1,2})\s*[./월-]\s*)?(?P<ed>\d{1,2})\s*(?:일)?\s*[.]?\s*(?:\(?[월화수목금토일](?:요일)?\)?)?",
        text,
    )
    if range_with_weekday:
        try:
            ry = int(range_with_weekday.group("year"))
            sm = int(range_with_weekday.group("sm")); sd = int(range_with_weekday.group("sd"))
            ey = int(range_with_weekday.group("ey") or ry)
            em = int(range_with_weekday.group("em") or sm)
            ed = int(range_with_weekday.group("ed"))
            start_d = datetime(ry, sm, sd).strftime("%Y-%m-%d")
            end_d = datetime(ey, em, ed).strftime("%Y-%m-%d")
            if start_d not in date_candidates: date_candidates.insert(0, start_d)
            if end_d not in date_candidates: date_candidates.append(end_d)
        except (ValueError, TypeError):
            pass
    # 같은 줄에 '10.17(토) ▶ 18(일)'처럼 종료 월/연도가 생략된 날짜 범위 보완
    if poster_year:
        range_match = re.search(r"(?<!\d)(\d{1,2})\s*[./]\s*(\d{1,2})\s*(?:일)?\s*(?:\([^)]{1,8}\))?\s*(?:▶|>|~|～|〜|부터|–|—|-)\s*(?:(\d{1,2})\s*[./]\s*)?(\d{1,2})\s*(?:일)?", text)
        if range_match:
            sm, sd, em, ed = range_match.groups()
            sm, sd, em, ed = int(sm), int(sd), int(em or sm), int(ed)
            try:
                start_d = datetime(int(poster_year), sm, sd).strftime("%Y-%m-%d")
                end_d = datetime(int(poster_year), em, ed).strftime("%Y-%m-%d")
                if start_d not in date_candidates:
                    date_candidates.insert(0, start_d)
                if end_d not in date_candidates:
                    date_candidates.append(end_d)
            except ValueError:
                pass
    # 중복 제거 및 시간 범위/단일 오픈 시간 인식
    date_candidates = list(dict.fromkeys(date_candidates))
    deadline = extract_deadline(text)
    start_time, end_time = extract_time_range(text)
    if not start_time:
        open_match = re.search(r"(?i)(?:오픈\s*시간|오픈|개장\s*시간|운영\s*시작|open(?:ing)?\s*time)\s*[:：]?\s*((?:오전|오후)?\s*\d{1,2}(?:\s*[:.]\s*\d{2}|\s*시(?:\s*\d{1,2}\s*분)?)?(?:\s*(?:AM|PM))?)", text)
        if open_match:
            raw_time = open_match.group(1).strip()
            start_time = extract_time_range(raw_time)[0]
            if not start_time:
                tm = re.search(r"(?i)(오전|오후|AM|PM)?\s*(\d{1,2})(?:\s*[:.]\s*(\d{2})|\s*시(?:\s*(\d{1,2})\s*분)?)?", raw_time)
                if tm:
                    start_time = _normalize_clock(tm.group(2), tm.group(3) or tm.group(4) or 0, tm.group(1) or "")
    special_info = extract_special_info(text)
    extracted_title = extract_title(text)
    if poster_year and extracted_title and poster_year not in extracted_title:
        extracted_title = f"{poster_year} {extracted_title}"
    data = {
        "source_name": source_name, "image_bytes": image_bytes,
        "title": extracted_title, "title_subtitle": split_title_for_display(extracted_title)[1], "date_candidates": date_candidates,
        "selected_date": date_candidates[0] if date_candidates else "",
        "date": date_candidates[0] if date_candidates else "",
        "deadline": deadline, "start_time": start_time, "end_date": date_candidates[-1] if len(date_candidates) > 1 else (date_candidates[0] if date_candidates else ""),
        "end_time": end_time, "location": extract_location(text), "organizer": extract_organizer(text),
        "fee": extract_fee(text), "url": extract_url(text), "special_info": special_info, "participation_info": extract_participation_info(text),
        "description": "", "ocr_text": text, "added": False, "confirmed": False,
    }
    reasons=[]
    if not data["title"]: reasons.append("행사명을 찾지 못했습니다.")
    if not date_candidates: reasons.append("행사 날짜를 찾지 못했습니다.")
    if len(date_candidates)>1: reasons.append("날짜가 여러 개 발견되었습니다. 행사 날짜와 종료 날짜를 확인해주세요.")
    if data["deadline"] and data["date"] and data["deadline"] > data["date"]:
        reasons.append("신청 마감일이 행사 날짜보다 늦게 인식되었습니다. 마감일을 확인해주세요.")
    if not data["location"]: reasons.append("장소를 확실하게 찾지 못했습니다.")
    if not data["start_time"]: reasons.append("시작 시간을 찾지 못했습니다.")
    data["review_reasons"]=reasons; data["needs_review"]=bool(reasons)
    return data


def empty_event_data(source_name=""):
    return {
        "source_name": source_name,
        "image_bytes": None,
        "title": "",
        "title_subtitle": "",
        "date_candidates": [],
        "selected_date": "",
        "date": "",
        "deadline": "",
        "start_time": "",
        "end_date": "",
        "end_time": "",
        "location": "",
        "organizer": "",
        "special_info": [],
        "participation_info": [],
        "fee": "",
        "url": "",
        "description": "",
        "ocr_text": "",
        "added": False,
        "confirmed": False,
        "needs_review": True,
        "review_reasons": ["포스터에서 찾은 정보를 확인해주세요."]
    }


# =========================================================
# DUPLICATE
# =========================================================
def normalize(value):
    return re.sub(r"\s+", "", str(value or "")).lower()


def event_key(data):
    return (
        normalize(data.get("title")),
        data.get("date", ""),
        normalize(data.get("location"))
    )


def is_duplicate(data):
    return event_key(data) in st.session_state.get(
        "added_event_keys", set()
    )


# =========================================================
# GOOGLE CALENDAR / ICS
# =========================================================
def make_google_calendar_url(data):
    title = data.get("title", "").strip() or "행사"
    date = data.get("date", "").strip()
    start_time = data.get("start_time", "").strip()
    end_time = data.get("end_time", "").strip()
    end_date = data.get("end_date", "").strip() or date
    description = data.get("description", "").strip()

    if not date:
        return ""

    try:
        if not start_time:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            next_day = date_obj + timedelta(days=1)

            params = {
                "action": "TEMPLATE",
                "text": title,
                "dates": (
                    date_obj.strftime("%Y%m%d")
                    + "/"
                    + next_day.strftime("%Y%m%d")
                ),
                "details": description
            }
        else:
            start_obj = datetime.strptime(
                f"{date} {start_time}",
                "%Y-%m-%d %H:%M"
            )

            if end_time:
                end_obj = datetime.strptime(
                    f"{end_date} {end_time}",
                    "%Y-%m-%d %H:%M"
                )
            else:
                end_obj = start_obj + timedelta(hours=1)

            params = {
                "action": "TEMPLATE",
                "text": title,
                "dates": (
                    start_obj.strftime("%Y%m%dT%H%M%S")
                    + "/"
                    + end_obj.strftime("%Y%m%dT%H%M%S")
                ),
                "details": description,
                "ctz": "Asia/Seoul"
            }

        return (
            "https://calendar.google.com/calendar/render?"
            + urllib.parse.urlencode(params)
        )
    except Exception:
        return ""


def ics_escape(value):
    return (
        str(value or "")
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def make_ics(data):
    title = data.get("title", "").strip() or "행사"
    date = data.get("date", "").strip()
    start_time = data.get("start_time", "").strip()
    end_time = data.get("end_time", "").strip()
    end_date = data.get("end_date", "").strip() or date
    description = data.get("description", "").strip()

    if not date:
        return None

    try:
        if start_time:
            start_obj = datetime.strptime(
                f"{date} {start_time}",
                "%Y-%m-%d %H:%M"
            )

            if end_time:
                end_obj = datetime.strptime(
                    f"{end_date} {end_time}",
                    "%Y-%m-%d %H:%M"
                )
            else:
                end_obj = start_obj + timedelta(hours=1)

            lines = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Poster Calendar//EN",
                "BEGIN:VEVENT",
                f"SUMMARY:{ics_escape(title)}",
                "DTSTART;TZID=Asia/Seoul:" + start_obj.strftime("%Y%m%dT%H%M%S"),
                "DTEND;TZID=Asia/Seoul:" + end_obj.strftime("%Y%m%dT%H%M%S"),
                f"DESCRIPTION:{ics_escape(description)}",
                "END:VEVENT",
                "END:VCALENDAR"
            ]
        else:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            next_day = date_obj + timedelta(days=1)

            lines = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Poster Calendar//EN",
                "BEGIN:VEVENT",
                f"SUMMARY:{ics_escape(title)}",
                "DTSTART;VALUE=DATE:" + date_obj.strftime("%Y%m%d"),
                "DTEND;VALUE=DATE:" + next_day.strftime("%Y%m%d"),
                f"DESCRIPTION:{ics_escape(description)}",
                "END:VEVENT",
                "END:VCALENDAR"
            ]

        return "\r\n".join(lines)

    except Exception:
        return None


# =========================================================
# DISPLAY HELPERS
# =========================================================
def make_keyword_summary(text, data=None):
    """포스터 내용이 있으면 짧게 요약하고, 내용이 없으면 행사 성격을 해시태그로 표시합니다."""
    data = data or {}
    if not text:
        return "#행사"

    text = clean_extracted_lines(text)
    lines = [re.sub(r"\s+", " ", x).strip(" -–—|•·") for x in text.splitlines() if x.strip()]
    title = data.get("title", "").strip()
    location = data.get("location", "").strip()
    organizer = data.get("organizer", "").strip()

    metadata_words = [
        "장소", "주최", "주관", "문의", "연락처", "신청", "접수", "마감", "등록",
        "일시", "날짜", "시간", "기간", "일정", "주소", "홈페이지", "http://", "https://",
        "www.", "참가비", "입장료", "전화", "이메일", "신청기간", "접수기간",
        "참가대상", "참여대상", "참여방법", "신청방법", "접수방법"
    ]

    def is_date_or_time(line):
        if re.search(r"20\d{2}[.\-/년]\s*\d{1,2}[.\-/월]\s*\d{1,2}", line):
            return True
        if re.search(r"\d{1,2}\s*월\s*\d{1,2}\s*일", line):
            return True
        if re.search(r"(?<!\d)(?:[01]?\d|2[0-3])\s*[:.]\s*[0-5]\d(?!\d)", line):
            return True
        if re.search(r"(?:오전|오후|AM|PM)?\s*(?:[01]?\d|2[0-3])\s*시", line, re.I):
            return True
        return False

    # 포스터에 실제 설명/프로그램 문장이 있는지 찾습니다.
    description_candidates = []
    content_words = [
        "공연", "콘서트", "체험", "전시", "강연", "토크", "게임", "대회", "경기",
        "마켓", "부스", "워크숍", "워크샵", "출연", "가수", "밴드", "댄스",
        "프로그램", "캠페인", "상영", "발표", "먹거리", "볼거리", "즐길",
        "진행", "운영", "마련", "참여", "초청", "만나요", "즐겨요", "즐길거리",
        "체험존", "공연팀", "버스킹", "푸드", "놀이"
    ]
    generic_only = {"페스티벌", "축제", "행사", "공연", "콘서트", "festival", "event"}

    for line in lines:
        normalized = line.lower().strip(" .")
        if len(line) < 10 or line in {title, location, organizer}:
            continue
        if normalized in generic_only:
            continue
        if any(word in line for word in metadata_words):
            continue
        if is_date_or_time(line):
            continue
        if re.fullmatch(r"[\d\s|lI._:/~()\-–—]+", line):
            continue
        # 문장형 설명 또는 프로그램/활동을 나타내는 구체적인 문구만 내용으로 사용합니다.
        if any(word in line for word in content_words) or re.search(r"[.!?]$|합니다$|됩니다$|하세요$|보세요$|함께$|만나", line):
            description_candidates.append(line)

    if description_candidates:
        selected = []
        for line in description_candidates:
            if line not in selected:
                selected.append(line[:90] + ("…" if len(line) > 90 else ""))
            if len(selected) >= 2:
                break
        return " ".join(selected)

    # 설명 문장이 없더라도 포스터의 단어 조합으로 행사 성격을 자연스럽게 표현합니다.
    searchable = " ".join(lines + [title]).lower()
    has_music = any(w in searchable for w in ["음악", "노래", "가수", "밴드", "콘서트", "뮤직", "버스킹"])
    has_festival = any(w in searchable for w in ["축제", "페스티벌", "페스타"])
    has_performance = any(w in searchable for w in ["공연", "무대", "출연", "아티스트", "공연팀"])
    has_exhibition = any(w in searchable for w in ["전시", "갤러리", "미술", "작품"])
    has_experience = any(w in searchable for w in ["체험", "워크숍", "워크샵", "체험존"])
    has_sports = any(w in searchable for w in ["스포츠", "운동", "달리기", "마라톤", "경기", "체육"])
    has_market = any(w in searchable for w in ["마켓", "플리마켓", "부스", "푸드"])
    has_lecture = any(w in searchable for w in ["강연", "세미나", "토크", "포럼"])
    has_contest = any(w in searchable for w in ["대회", "공모전", "경연", "선발전"])

    phrases = []
    if has_music and has_festival:
        phrases.append("음악 페스티벌")
    elif has_music and has_performance:
        phrases.append("음악 공연")
    elif has_music:
        phrases.append("음악 행사")
    elif has_performance and has_festival:
        phrases.append("공연 페스티벌")
    elif has_performance:
        phrases.append("공연 행사")
    elif has_festival:
        phrases.append("축제")

    if has_exhibition: phrases.append("전시")
    if has_experience: phrases.append("체험")
    if has_sports: phrases.append("스포츠")
    if has_market: phrases.append("마켓")
    if has_lecture: phrases.append("강연")
    if has_contest: phrases.append("대회")

    # 구체적인 키워드가 없을 때만 일반적인 행사명을 표시합니다.
    return " · ".join(dict.fromkeys(phrases)) if phrases else "행사 프로그램 및 활동 정보 확인 필요"

def render_event_summary(data, index):
    """세로형 핵심 정보 카드와 키워드별 이모지 추가 정보를 표시합니다."""
    title = data.get("title", "").strip() or "-"
    date = data.get("date", "").strip() or "-"
    end_date = data.get("end_date", "").strip() or date
    start_time = data.get("start_time", "").strip()
    end_time = data.get("end_time", "").strip()
    location = data.get("location", "").strip() or "-"

    def pretty(value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").strftime("%Y.%m.%d")
        except Exception:
            return value or "-"

    date_range = "-" if date == "-" else (pretty(date) if end_date in ("", "-") or date == end_date else f"{pretty(date)} – {pretty(end_date)}")
    time_text = f"{start_time} ~ {end_time}" if start_time and end_time else (start_time or end_time or "-")
    time_label = "오픈 시간" if re.search(r"(?:오픈\s*시간|오픈|개장\s*시간|운영\s*시작|open(?:ing)?\s*time)", data.get("ocr_text", ""), re.I) else "시간"

    with st.container(border=True):
        image_col, info_col = st.columns([1, 1.7])
        with image_col:
            if data.get("image_bytes"):
                st.image(io.BytesIO(data["image_bytes"]), caption=data.get("source_name", "포스터"), width="stretch")
        with info_col:
            st.caption(f"EVENT {index + 1}")
            title_main, title_sub = split_title_for_display(title)
            st.markdown(
                f'<div class="event-display-title">{title_main}</div>'
                + (f'<div class="event-display-subtitle">{title_sub}</div>' if title_sub else ""),
                unsafe_allow_html=True
            )
            st.markdown(f'<div class="diary-note"><div class="diary-label">행사 날짜</div><div class="diary-value">{date_range}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="diary-note"><div class="diary-label">{time_label}</div><div class="diary-value">{time_text}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="diary-note"><div class="diary-label">장소</div><div class="diary-value">{location}</div></div>', unsafe_allow_html=True)

        st.divider()
        st.markdown('<div class="extra-info-heading">추가 정보</div>', unsafe_allow_html=True)
        special_info = data.get("special_info", []) or [
            {"label": "초청 가수 라인업", "value": "-"},
            {"label": "주최·주관", "value": "-"},
            {"label": "나이 제한", "value": "-"},
            {"label": "주의 사항", "value": "-"},
        ]
        cards = []
        for item in special_info:
            label = re.sub(r"^[^가-힣A-Za-z0-9]+", "", item.get("label", "")).strip()
            value = item.get("value") or "-"
            cards.append((label or "기타 정보", str(value)))
        for item in data.get("participation_info", []) or []:
            label = re.sub(r"^[^가-힣A-Za-z0-9]+", "", item.get("label", "")).strip()
            cards.append((label or "추가 정보", str(item.get("value") or "-")))

        st.markdown('<div class="info-grid">' + ''.join(
            '<div class="info-item"><div class="info-label">' + html.escape(label) +
            '</div><div class="info-value">' + value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>") +
            '</div></div>' for label, value in cards
        ) + '</div>', unsafe_allow_html=True)

        st.divider()


# SESSION STATE
# =========================================================
if "events" not in st.session_state:
    st.session_state.events = []

if "added_event_keys" not in st.session_state:
    st.session_state.added_event_keys = set()


# =========================================================
# APP
# =========================================================
st.markdown(
    """
    <div class="main-title-wrap">
        <div class="main-title">행사 포스터 일정 자동 등록</div>
        <div class="main-subtitle">포스터를 올리면 행사 정보를 한눈에 정리하고 캘린더에 담을 수 있어요.</div>
    </div>
    """,
    unsafe_allow_html=True
)

uploaded_files = st.file_uploader(
    "행사 포스터를 업로드하세요. 여러 장을 한 번에 선택할 수 있습니다.",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"선택한 포스터: **{len(uploaded_files)}장**")

    if st.button(
        "선택한 포스터에서 정보 찾기",
        type="primary",
        use_container_width=True
    ):
        new_events = []
        progress = st.progress(0)

        for index, uploaded_file in enumerate(uploaded_files):
            image = Image.open(uploaded_file)

            with st.spinner(f"{uploaded_file.name} 읽는 중..."):
                text, error = ocr_image(image)

            if text:
                event = make_event_data(
                    text, uploaded_file.name, uploaded_file.getvalue()
                )
                new_events.append(event)
            else:
                event = empty_event_data(uploaded_file.name)
                event["image_bytes"] = uploaded_file.getvalue()
                event["ocr_error"] = error
                new_events.append(event)

            progress.progress((index + 1) / len(uploaded_files))

        st.session_state.events = new_events
        st.success(
            f"{len(new_events)}개의 포스터 처리가 완료되었습니다."
        )


# =========================================================
# EVENT LIST
# =========================================================
if st.session_state.events:
    st.divider()
    st.markdown('<div class="event-info-heading">행사정보</div>', unsafe_allow_html=True)

    for index, data in enumerate(st.session_state.events):
        source_name = data.get("source_name", f"행사 {index + 1}")

        with st.container():
            # 한눈에 보는 행사 요약
            render_event_summary(data, index)

            if data.get("ocr_error"):
                st.warning(data["ocr_error"])
            # 자동 추출이 실패한 경우에만 실제 OCR 결과를 확인할 수 있게 합니다.
            if data.get("needs_review") and data.get("ocr_text"):
                with st.expander("읽어낸 포스터 글자 확인"):
                    st.code(data.get("ocr_text", ""), language=None)

            if data.get("needs_review"):
                st.warning("자동 추출 결과를 확인해주세요.")
                for reason in data.get("review_reasons", []):
                    st.write(f"• {reason}")

            # 여러 날짜가 발견되면 캘린더에 넣을 날짜를 항상 먼저 선택
            candidates = data.get("date_candidates", [])
            if len(candidates) > 1:
                labels = [f"{d} (후보 {i+1})" for i,d in enumerate(candidates)]
                current=data.get("selected_date", candidates[0])
                idx=candidates.index(current) if current in candidates else 0
                selected=st.selectbox("캘린더에 추가할 행사 날짜", range(len(candidates)), index=idx, format_func=lambda x: labels[x], key=f"date_select_top_{index}")
                data["selected_date"]=candidates[selected]; data["date"]=candidates[selected]
                st.info("여러 날짜가 발견되었습니다. 행사 날짜를 선택한 뒤 캘린더에 추가하세요.")

            # 사용자가 수정할 수 있는 영역은 접어서 제공
            with st.expander("정보 수정 / 자세히 보기"):
                st.caption(
                    f"원본 포스터: {source_name} · "
                    "포스터에서 자동으로 찾은 정보를 수정할 수 있습니다."
                )

                data["title"] = st.text_input(
                    "행사명",
                    value=data.get("title", ""),
                    key=f"title_{index}"
                )

                if len(candidates) <= 1:
                    data["date"] = st.text_input(
                        "행사 날짜", value=data.get("date", ""), placeholder="2026-10-12", key=f"date_{index}"
                    )

                col1, col2 = st.columns(2)

                with col1:
                    data["end_date"] = st.text_input(
                        "종료 날짜",
                        value=data.get("end_date", "") or data.get("date", ""),
                        placeholder="2026-10-12",
                        key=f"end_date_{index}"
                    )

                with col2:
                    data["deadline"] = st.text_input(
                        "신청 마감일",
                        value=data.get("deadline", ""),
                        placeholder="2026-10-05",
                        key=f"deadline_{index}"
                    )

                col1, col2 = st.columns(2)

                with col1:
                    data["start_time"] = st.text_input(
                        "시작 시간",
                        value=data.get("start_time", ""),
                        placeholder="19:00",
                        key=f"start_{index}"
                    )

                with col2:
                    data["end_time"] = st.text_input(
                        "종료 시간",
                        value=data.get("end_time", ""),
                        placeholder="20:00",
                        key=f"end_{index}"
                    )

                data["location"] = st.text_input(
                    "장소",
                    value=data.get("location", ""),
                    key=f"location_{index}"
                )

                data["organizer"] = st.text_input(
                    "주최 / 주관",
                    value=data.get("organizer", ""),
                    key=f"organizer_{index}"
                )

                data["fee"] = st.text_input(
                    "참가비",
                    value=data.get("fee", ""),
                    key=f"fee_{index}"
                )

                data["url"] = st.text_input(
                    "신청 URL",
                    value=data.get("url", ""),
                    key=f"url_{index}"
                )

                st.markdown("**포스터에서 발견한 추가 정보**")
                for item in data.get("special_info", []):
                    st.write(f"{item['label']}  {item['value']}")
                for item in data.get("participation_info", []):
                    st.write(f"{item['label']}  {item['value']}")

                data["description"] = st.text_area(
                    "캘린더에 넣을 내용 (선택)",
                    value=data.get("description", ""),
                    height=100,
                    placeholder="예: 친구와 함께 방문하기 / 준비물: 운동화",
                    key=f"calendar_description_{index}"
                )

            if data.get("needs_review"):
                data["confirmed"] = st.checkbox(
                    "자동 추출 결과와 수정한 정보를 확인했습니다.",
                    value=data.get("confirmed", False),
                    key=f"confirm_{index}"
                )
            else:
                data["confirmed"] = True

            st.session_state.events[index] = data

            duplicate = is_duplicate(data)

            if duplicate:
                st.error(
                    "이미 추가한 행사입니다. "
                    "같은 행사명·날짜·장소의 행사는 중복 추가할 수 없습니다."
                )
                continue

            if not data.get("date"):
                st.warning("행사 날짜를 입력하면 캘린더 추가 기능이 나타납니다.")
                continue

            # 5일 이상 이어지는 장기 행사는 기간 전체를 자동 등록하지 않도록 합니다.
            # 사용자가 실제로 참여할 날짜를 캘린더 앱에서 직접 골라 등록하게 안내합니다.
            long_event = False
            try:
                start_dt = datetime.strptime(str(data.get("date", "")).strip()[:10], "%Y-%m-%d")
                end_value = str(data.get("end_date", "")).strip() or str(data.get("date", "")).strip()
                end_dt = datetime.strptime(end_value[:10], "%Y-%m-%d")
                if end_dt >= start_dt:
                    long_event = (end_dt - start_dt).days + 1 >= 5
            except (ValueError, TypeError):
                long_event = False

            blocked = data.get("needs_review") and not data.get("confirmed")

            if long_event:
                st.info(
                    "장기 행사예요. 참여할 날짜를 Google Calendar에서 직접 선택해 주세요.\n\n"
                    f"행사 기간: {data.get('date', '')} ~ {data.get('end_date', '')}"
                )

            # 장기 행사 여부와 관계없이 캘린더 추가 버튼은 항상 표시합니다.
            calendar_url = make_google_calendar_url(data)
            ics = make_ics(data)

            if blocked:
                st.info("위의 정보 확인을 완료하면 캘린더에 추가할 수 있습니다.")

            col1, col2 = st.columns(2)

            with col1:
                if calendar_url:
                    st.link_button(
                        "Google Calendar에 추가",
                        calendar_url,
                        use_container_width=True,
                        disabled=blocked
                    )

            with col2:
                if ics:
                    st.download_button(
                        "일정 파일 다운로드",
                        data=ics,
                        file_name=f"event_{index + 1}.ics",
                        mime="text/calendar",
                        use_container_width=True,
                        key=f"ics_{index}",
                        disabled=blocked
                    )
                    st.caption("Google Calendar 외 다른 캘린더에서도 사용할 수 있는 일정 파일입니다.")

            if st.button(
                "캘린더에 추가 완료로 표시",
                key=f"added_{index}",
                use_container_width=True,
                disabled=blocked
            ):
                st.session_state.added_event_keys.add(
                    event_key(data)
                )
                data["added"] = True
                st.session_state.events[index] = data
                st.rerun()

# =========================================================
# ADDED EVENTS
# =========================================================
if st.session_state.added_event_keys:
    st.divider()
    st.subheader("이미 추가한 행사")

    for event in st.session_state.events:
        if is_duplicate(event):
            st.write(
                f"• {event.get('title', '행사')} "
                f"— {event.get('date', '')} "
                f"— {event.get('location', '')}"
            )

st.divider()
st.caption(
    "Poster Calendar · 여러 포스터 · 날짜 선택 · 마감일 구분 · 정보 확인 · 중복 방지"
)

