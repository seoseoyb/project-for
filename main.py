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
    page_icon="🐈‍⬛",
    layout="wide"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Jua&display=swap');

    /* 전체 테마: 따뜻한 크림 + 라벤더 포인트 */
    .stApp {
        font-family: "Jua", "Gowun Dodum", "Malgun Gothic", sans-serif;
        background: linear-gradient(180deg, #f7f7f8 0%, #ffffff 44%, #f4f4f5 100%);
        color: #202024;
    }

    /* 앱 전체를 동글동글한 글씨로 통일 */
    .stApp p, .stApp label, .stApp input, .stApp textarea,
    .stApp select, .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stFileUploaderDropzone"] {
        font-family: "Gowun Dodum", "Jua", "Malgun Gothic", sans-serif !important;
    }

    /* Streamlit 아이콘은 아이콘 폰트를 유지 */
    .stApp .material-symbols-outlined,
    .stApp .material-icons,
    .stApp [class*="material-symbols"] {
        font-family: "Material Symbols Outlined" !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: "Jua", "Gowun Dodum", sans-serif !important;
        font-weight: 400 !important;
        letter-spacing: -0.02em;
    }

    /* 상단 제목 영역 */
    .main-title-wrap {
        text-align: center;
        padding: 24px 12px 12px 12px;
    }

    .main-title-wrap .main-title {
        font-family: "Jua", "Gowun Dodum", sans-serif;
        font-size: clamp(32px, 4vw, 48px);
        line-height: 1.25;
        color: #17171b;
        margin: 0;
    }

    .main-title-wrap .main-subtitle {
        margin-top: 10px;
        color: #66666f;
        font-family: "Gowun Dodum", "Jua", sans-serif;
        font-size: 16px;
        font-weight: 400;
    }

    /* 업로드 영역 */
    [data-testid="stFileUploader"] {
        background: rgba(255,255,255,.98);
        border: 2px dashed #bdbdc5;
        border-radius: 18px 24px 20px 14px;
        padding: 9px;
        box-shadow: 3px 4px 0 rgba(20,20,24,.05), 0 10px 22px rgba(20,20,24,.06);
    }

    /* 메인 정보 찾기 버튼 */
    div.stButton > button[kind="primary"] {
        border-radius: 16px !important;
        min-height: 52px !important;
        font-family: "Jua", "Gowun Dodum", sans-serif !important;
        font-size: 18px !important;
        letter-spacing: -0.01em;
        border: 0 !important;
        box-shadow: 0 7px 18px rgba(20,20,24,0.16);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 22px rgba(20,20,24,0.22);
    }

    /* ───────── 다이어리 노트형 행사 카드 ───────── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        position: relative;
        margin: 28px 0 34px 0 !important;
        padding: 28px 28px 24px 42px !important;
        border-radius: 10px 18px 14px 12px !important;
        border: 1px solid #e5e5e9 !important;
        border-left: 3px solid #242429 !important;
        background-color: #ffffff !important;
        background-image:
            linear-gradient(to right, transparent 0, transparent 31px, rgba(30,30,35,.06) 32px, transparent 33px),
            repeating-linear-gradient(to bottom, transparent 0, transparent 31px, rgba(30,30,35,.035) 32px, transparent 33px);
        box-shadow: 4px 7px 0 rgba(20,20,24,.05), 0 14px 30px rgba(20,20,24,.08);
        overflow: visible !important;
    }

    /* 노트 위에 붙인 마스킹테이프 */
    [data-testid="stVerticalBlockBorderWrapper"]::before {
        content: "";
        position: absolute;
        z-index: 5;
        top: -13px;
        left: 50%;
        transform: translateX(-50%) rotate(-2deg);
        width: 108px;
        height: 28px;
        border-radius: 5px;
        background: rgba(28,28,33,.92);
        box-shadow: 0 2px 5px rgba(20,20,24,.12);
    }

    /* 노트의 왼쪽 바인더 구멍 느낌 */
    [data-testid="stVerticalBlockBorderWrapper"]::after {
        content: "";
        position: absolute;
        left: 8px;
        top: 42px;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: #f1a8bd;
        box-shadow: 0 39px #f1a8bd, 0 78px #f1a8bd, 0 117px #f1a8bd, 0 156px #f1a8bd, 0 195px #f1a8bd;
    }

    .event-title {
        font-family: "Jua", "Gowun Dodum", sans-serif;
        font-size: 32px;
        font-weight: 400;
        line-height: 1.25;
        margin-bottom: 22px;
        color: #1c1c21;
    }

    .event-main-info {
        display: flex;
        gap: 12px;
        margin-bottom: 18px;
    }

    .info-item {
        flex: 1;
        padding: 15px 18px;
        border-radius: 12px;
        background: #f7f7f8;
        border: 1px dashed #d7d7dd;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.9);
    }

    .info-label {
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 6px;
        opacity: 0.72;
    }

    .info-value {
        font-size: 20px;
        font-weight: 750;
    }

    .event-sub-info {
        display: grid;
        gap: 8px;
        font-size: 16px;
        line-height: 1.55;
        margin-bottom: 18px;
    }

    .event-description {
        border-top: 1px solid #e8e8ec;
        padding-top: 16px;
    }

    .keyword-text {
        font-size: 16px;
        line-height: 1.7;
    }

    /* 다이어리 메모지 느낌의 핵심 정보 */
    .diary-note {
        position: relative;
        margin: 11px 0 14px 0;
        padding: 14px 18px 15px 18px;
        border-radius: 8px 13px 10px 7px;
        border: 1px dashed #d7d7dd;
        background: rgba(255,255,255,.96);
        box-shadow: 2px 3px 0 rgba(20,20,24,.05);
    }

    .diary-note::after {
        content: "";
        position: absolute;
        right: 10px;
        top: 8px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid #f1a8bd;
        background: #ffffff;
    }

    .diary-label {
        font-size: 13px;
        font-weight: 700;
        color: #686871;
        margin-bottom: 4px;
    }

    .diary-value {
        font-size: 18px;
        color: #29292f;
    }

    /* 확장/수정 버튼 안의 아이콘이 글씨와 겹치지 않도록 아이콘 폰트를 강제로 분리 */
    .stApp span[class*="material-symbols"],
    .stApp span[class*="material-icons"],
    .stApp i[class*="material-symbols"],
    .stApp i[class*="material-icons"] {
        font-family: "Material Symbols Outlined", "Material Icons" !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
    }

    /* 정보 수정 / OCR 확인 영역 — 글자와 펼침 아이콘이 절대 겹치지 않게 */
    .stApp [data-testid="stExpander"] summary {
        min-height: 52px !important;
        padding: 9px 16px !important;
        border-radius: 14px !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        overflow: hidden !important;
        box-sizing: border-box !important;
    }
    .stApp [data-testid="stExpander"] summary > div {
        display: flex !important;
        align-items: center !important;
        min-width: 0 !important;
        flex: 1 1 auto !important;
    }
    .stApp [data-testid="stExpander"] summary p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.45 !important;
        font-family: "Gowun Dodum", "Jua", sans-serif !important;
        font-weight: 400 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    .stApp [data-testid="stExpander"] summary span[class*="material"] {
        flex: 0 0 24px !important;
        width: 24px !important;
        min-width: 24px !important;
        height: 24px !important;
        line-height: 24px !important;
        font-family: "Material Symbols Outlined", "Material Icons" !important;
        font-weight: normal !important;
        letter-spacing: normal !important;
        overflow: hidden !important;
    }

    .event-display-title {
        font-family: "Jua", "Gowun Dodum", sans-serif;
        font-size: clamp(28px, 3.2vw, 42px);
        line-height: 1.2;
        font-weight: 400;
        color: #17171b;
        margin: 4px 0 2px 0;
        letter-spacing: -0.02em;
    }
    .event-display-subtitle {
        font-family: "Gowun Dodum", "Jua", sans-serif;
        font-size: 15px;
        line-height: 1.45;
        font-weight: 400;
        color: #777780;
        margin: 0 0 18px 1px;
    }

    /* 검은 고양이 테마: 깔끔한 흑백 + 말랑한 핑크 젤리 포인트 */
    .stApp {
        background: linear-gradient(180deg, #f6f6f7 0%, #ffffff 34%, #f7f7f8 100%);
        color: #202024;
    }
    .main-title-wrap {
        position: relative;
        padding-top: 30px;
        padding-bottom: 20px;
    }
    .main-title-wrap::before {
        content: "🐈‍⬛";
        display: block;
        font-size: 43px;
        line-height: 1.1;
        margin-bottom: 8px;
        filter: drop-shadow(0 4px 0 rgba(20,20,24,.06));
    }
    .main-title-wrap::after {
        content: "肉球  •  pink beans  •  肉球";
        display: block;
        margin-top: 12px;
        color: #e58da8;
        font-family: "Gowun Dodum", sans-serif;
        font-size: 12px;
        letter-spacing: .14em;
    }
    .main-title-wrap .main-title { color: #17171b; }
    .main-title-wrap .main-subtitle { color: #686871; }
    [data-testid="stFileUploader"] {
        position: relative;
        background: #fff;
        border: 2px dashed #c8c8cf;
        border-radius: 22px;
        box-shadow: 0 8px 24px rgba(20,20,24,.045);
    }
    [data-testid="stFileUploader"]::after {
        content: "🐾";
        position: absolute;
        right: 15px;
        bottom: 10px;
        font-size: 23px;
        opacity: .82;
        pointer-events: none;
    }
    div.stButton > button[kind="primary"] {
        background: #242429 !important;
        color: #fff !important;
        border: 1px solid #242429 !important;
        border-radius: 17px !important;
        box-shadow: 0 5px 0 #dedee3, 0 9px 18px rgba(20,20,24,.10) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #3a3a42 !important;
        border-color: #3a3a42 !important;
        box-shadow: 0 3px 0 #dedee3, 0 8px 18px rgba(20,20,24,.13) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #e1e1e5 !important;
        border-left-color: #242429 !important;
        background-color: #fff !important;
        background-image: none !important;
        border-radius: 20px !important;
        box-shadow: 0 8px 24px rgba(20,20,24,.055) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]::before {
        content: "🐾";
        display: flex;
        align-items: center;
        justify-content: center;
        width: 43px;
        height: 28px;
        background: #f9dce5;
        color: #28282d;
        border-radius: 999px;
        font-size: 16px;
        box-shadow: none;
        transform: translateX(-50%) rotate(-5deg);
    }
    [data-testid="stVerticalBlockBorderWrapper"]::after {
        background: #f1a8bd;
        box-shadow: 0 39px #f1a8bd, 0 78px #f1a8bd, 0 117px #f1a8bd, 0 156px #f1a8bd, 0 195px #f1a8bd;
    }
    .event-title, .event-display-title { color: #17171b !important; }
    .info-item {
        background: #f8f8f9;
        border: 1px solid #e2e2e6;
        border-radius: 16px;
    }
    .diary-note {
        border: 1px solid #e4e4e8;
        background: #fff;
        border-radius: 14px;
        box-shadow: 0 3px 0 rgba(20,20,24,.035);
    }
    .diary-note::after {
        background: #f7c8d7;
        border-color: #f1a8bd;
    }
    .diary-label { color: #777780; }
    .diary-value { color: #29292f; }
    .stApp [data-testid="stExpander"] summary {
        background: #f8f8f9;
        border: 1px solid #e5e5e9;
        border-radius: 15px !important;
    }
    .stApp [data-testid="stExpander"] summary:hover { border-color: #f1a8bd; }
    .stApp [data-testid="stFileUploaderDropzone"] { background: transparent; }
    .stApp [data-testid="stProgressBar"] > div > div { background-color: #f1a8bd; }

    @media (max-width: 700px) {
        .event-title { font-size: 25px; }
        .event-main-info { flex-direction: column; }
        .main-title-wrap .main-title { font-size: 32px; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# OCR
# =========================================================
def ocr_image(image):
    """OCR.Space로 한국어와 영어를 각각 읽고 결과를 합칩니다."""
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

        def request_ocr(language):
            boundary = "----PosterCalendarBoundary"
            parts = [
                (f"--{boundary}\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\n{language}\r\n"),
                (f"--{boundary}\r\nContent-Disposition: form-data; name=\"isOverlayRequired\"\r\n\r\nfalse\r\n"),
                (f"--{boundary}\r\nContent-Disposition: form-data; name=\"OCREngine\"\r\n\r\n3\r\n"),
                (f"--{boundary}\r\nContent-Disposition: form-data; name=\"scale\"\r\n\r\ntrue\r\n"),
                (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"poster.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n"),
            ]
            request_body = "".join(parts).encode("utf-8") + image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
            request = urllib.request.Request("https://api.ocr.space/parse/image", data=request_body, method="POST")
            request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
            request.add_header("apikey", api_key)
            request.add_header("User-Agent", "PosterCalendar/2.2")
            with urllib.request.urlopen(request, timeout=45) as response:
                result = json.loads(response.read().decode("utf-8"))
            if result.get("IsErroredOnProcessing"):
                message = result.get("ErrorMessage") or result.get("ErrorDetails") or "OCR 처리 오류"
                if isinstance(message, list):
                    message = " / ".join(str(x) for x in message)
                return "", str(message)
            parsed = result.get("ParsedResults", [])
            return "\n".join(item.get("ParsedText", "") for item in parsed if item.get("ParsedText")).strip(), ""

        # 한국어 결과를 기본으로 사용하고 영어 인식 결과를 보완합니다.
        korean_text, korean_error = request_ocr("kor")
        english_text, english_error = request_ocr("eng")
        if not korean_text and not english_text:
            return "", f"포스터 글자 읽기에 실패했습니다: {korean_error or english_error or '읽어낸 글자가 없습니다.'}"

        combined_lines = []
        seen = set()
        for line in (korean_text + "\n" + english_text).splitlines():
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
    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in raw_lines if line]
    if not lines:
        return []

    patterns = [
        re.compile(r"(?<!\d)(20\d{2})\s*[.\-/년]\s*(\d{1,2})\s*[.\-/월]\s*(\d{1,2})\s*일?(?!\d)"),
        re.compile(r"(?<!\d)(20\d{2})\s+(\d{1,2})\s+(\d{1,2})(?!\d)"),
        re.compile(r"(?<!\d)(\d{1,2})\s*월\s*(\d{1,2})\s*일"),
        re.compile(r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})(?!\d)"),
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
                    else:
                        month, day = map(int, groups)
                        year = datetime.now().year
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

    # "2020년 5월 20-22일"처럼 월/연도가 시작 날짜에만 있는 범위 보완
    for line_index, line in enumerate(lines):
        patterns_range = [
            re.compile(r"(?<!\d)(20\d{2})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*(?:일)?\s*[~～〜–—-]\s*(\d{1,2})\s*일"),
            re.compile(r"(?<!\d)(\d{1,2})\s*월\s*(\d{1,2})\s*(?:일)?\s*[~～〜–—-]\s*(\d{1,2})\s*일"),
        ]
        for pi, rp in enumerate(patterns_range):
            rm = rp.search(line)
            if not rm:
                continue
            try:
                if pi == 0:
                    yy, mm, d1, d2 = map(int, rm.groups())
                else:
                    mm, d1, d2 = map(int, rm.groups())
                    ym = re.search(r"20\d{2}", text)
                    yy = int(ym.group()) if ym else datetime.now().year
                for day, offset in ((d1, 0), (d2, 100)):
                    dt = datetime(yy, mm, day)
                    found.append({"date": dt.strftime("%Y-%m-%d"), "context": line,
                                  "is_deadline": False, "position": line_index * 10000 + rm.start() + offset,
                                  "line_index": line_index, "has_event_label": True, "has_deadline_label": False})
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
        if not item["is_deadline"] and item["date"] not in result:
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


def extract_location(text):
    """라벨뿐 아니라 장소명 자체, 주소, 개최 문맥을 함께 살펴 장소를 추정합니다."""
    text = clean_extracted_lines(text or "")
    lines = [re.sub(r"\s+", " ", line).strip(" \t:：|-") for line in text.splitlines() if line.strip()]
    if not lines:
        return ""

    # 1) 장소 라벨이 명시된 경우 가장 우선합니다.
    label_re = re.compile(r"^(?:장소|행사장소|공연장|개최장소|장소안내|venue|location)\s*[:：|]?\s*(.*)$", re.I)
    for i, line in enumerate(lines):
        m = label_re.match(line)
        if not m:
            continue
        value = m.group(1).strip(" :：|-|")
        if value and not re.match(r"^(?:확인 필요|미정|추후 공지|일시|날짜|시간)$", value, re.I):
            return value
        # 라벨과 장소명이 다른 줄에 인식된 경우
        for nxt in lines[i + 1:i + 3]:
            if not re.match(r"^(?:일시|날짜|시간|참가|참여|주최|주관|문의|신청|접수|마감|기간|프로그램)\b", nxt, re.I):
                if not is_non_location_line(nxt):
                    return nxt.strip(" :：|-|")

    # 2) '킨텍스에서 개최', 'OO에서 진행됩니다'처럼 문장으로 쓰인 장소
    for line in lines:
        if is_non_location_line(line):
            continue
        place_pattern = r"([가-힣A-Za-z0-9· .-]{2,70}?(?:전시장|전시관|컨벤션센터|컨벤션홀|문화회관|문화관|아트센터|예술회관|체육관|운동장|야외광장|광장|공원|캠퍼스|대학|학교|플라자|전시실|공연장|콘서트홀|센터|갤러리|경기장|역|빌딩|타워))"
        place_matches = list(re.finditer(place_pattern, line, re.I))
        if place_matches:
            place_match = max(place_matches, key=lambda match: len(match.group(1)))
            suffix = line[place_match.end():]
            if re.match(r"\s*(?:에서|으로|에\s*위치|에서\s*개최|에서\s*진행)", suffix):
                candidate = place_match.group(1).strip(" ,.:：|-|")
                # 문장 앞의 설명을 제거하고 장소명에 가까운 구절만 반환
                candidate = re.split(r"(?:이번\s*행사는?|행사는?|장소는?|개최지는?)\s*", candidate)[-1].strip()
                if candidate:
                    return candidate

    # 3) 주소처럼 보이는 줄은 장소 후보로 사용합니다.
    address_patterns = [
        r"(?:대한민국\s*)?(?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[가-힣\s0-9-]{2,}(?:로|길|대로)\s*\d*[가-힣0-9-]*",
        r"[가-힣0-9]+(?:시|군|구)\s*[가-힣0-9]+(?:읍|면|동|리)\s*[가-힣0-9-]*(?:로|길|대로)\s*\d*",
        r"\b\d{1,5}\s+[A-Za-z][A-Za-z .'-]+(?:Street|Road|Ave|Avenue|Blvd)\b",
    ]
    for line in lines:
        if not is_non_location_line(line):
            for pattern in address_patterns:
                m = re.search(pattern, line, re.I)
                if m:
                    return m.group(0).strip()

    # 4) 장소 라벨이 없어도 장소명에서 자주 쓰이는 시설·공간 표현을 찾아냅니다.
    # '킨텍스 제2전시장 야외광장'처럼 시설명이 한 줄에만 있는 경우도 포함합니다.
    venue_terms = [
        "킨텍스", "전시장", "전시관", "야외광장", "광장", "컨벤션센터", "컨벤션홀",
        "문화회관", "문화관", "아트센터", "예술회관", "공연장", "콘서트홀", "체육관",
        "대강당", "소극장", "대극장", "센터", "홀", "갤러리", "운동장", "야외무대",
        "공원", "엑스포", "전시실", "캠퍼스", "대학교", "학교", "플라자", "경기장",
        "월드컵경기장", "마당", "수목원", "박물관", "미술관", "도서관", "역사", "역",
        "빌딩", "타워", "주차장", "문화공간", "잔디광장", "야외", "venue", "hall",
        "auditorium", "stadium", "park", "theater", "theatre", "arena", "center", "centre", "gallery"
    ]
    candidates = []
    for i, line in enumerate(lines):
        if is_non_location_line(line):
            continue
        lower = line.lower()
        hits = sum(1 for term in venue_terms if term.lower() in lower)
        if hits:
            # 너무 긴 홍보 문장은 피하고, 장소명이 포함된 구절을 우선합니다.
            candidate = line.strip(" ,.:：|-|")
            candidate = re.sub(r"^(?:위치|주소)\s*[:：]?\s*", "", candidate, flags=re.I)
            if len(candidate) <= 90:
                candidates.append((hits, len(candidate), i, candidate))
    if candidates:
        # 장소 단서가 많은 줄을 우선하고, 동점이면 짧고 구체적인 줄을 선택
        candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
        return candidates[0][3]

    # 5) 위치/개최 문맥 바로 옆에 있는 짧은 독립 줄도 후보로 검토합니다.
    for i, line in enumerate(lines):
        if re.search(r"(?:위치|주소|오시는\s*길|개최\s*장소|행사\s*장소|장소\s*안내)", line, re.I):
            for nxt in lines[i:i + 3]:
                if not is_non_location_line(nxt) and 2 <= len(nxt) <= 70:
                    return nxt.strip(" ,.:：|-|")
    return ""


def is_non_location_line(line):
    """장소 후보 탐색 시 행사명·일정·홍보 문구 등을 걸러냅니다."""
    line = (line or "").strip()
    if not line or len(line) < 2:
        return True
    if re.search(r"(?:주최|주관|문의|신청|접수|참가비|입장료|참가\s*대상|참여\s*방법|초청\s*가수|출연진|일시|행사\s*날짜|기간|마감|http|www\.)", line, re.I):
        return True
    if re.search(r"(?:20\d{2}\s*[./년-]\s*\d{1,2}|\d{1,2}\s*월\s*\d{1,2}\s*일|\d{1,2}[:.]\d{2})", line):
        return True
    # 일반적인 행사명/슬로건만 있는 줄은 장소 후보로 쓰지 않습니다.
    if re.search(r"(?:페스티벌|축제|콘서트|공연|마켓|박람회|대회|행사|음악회|영화제|festival|concert|event)", line, re.I) and not re.search(r"(?:킨텍스|전시장|전시관|광장|센터|홀|공원|운동장|경기장|캠퍼스|대학교|학교|플라자|공연장|문화관|문화회관|아트센터|예술회관|역|빌딩|타워)", line, re.I):
        return True
    return False


def extract_organizer(text):
    text = clean_extracted_lines(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if re.search(r"^(주최|주관|주최\s*·\s*주관|organizer|hosted\s*by|presented\s*by)\s*[:：]?", line, re.I):
            return clean_labeled_value(line, ["주최·주관", "주최 · 주관", "주최", "주관", "organizer", "hosted by", "presented by"])
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
        ("🎤 초청 가수 라인업", [r"초청\s*가수", r"초청가수", r"출연진", r"출연\s*가수", r"아티스트", r"초청\s*아티스트", r"invited\s*singers?", r"special\s*guest(?:s)?", r"guest\s*artists?", r"line[ -]?up", r"performers?"]),
        ("🐾 주최·주관", [r"주최\s*·?\s*주관", r"주최", r"주관", r"organizer", r"hosted\s*by", r"presented\s*by"]),
        ("🐾 나이 제한", [r"나이\s*제한", r"연령\s*제한", r"관람\s*연령", r"입장\s*연령", r"age(?:\s*limit)?", r"ages?"]),
        ("🐾 주의 사항", [r"주의\s*사항", r"유의\s*사항", r"안내\s*사항", r"입장\s*안내", r"주의", r"please\s*note", r"important\s*notes?", r"notice", r"warnings?", r"no\s+\w+", r"prohibited"]),
    ]
    for label, patterns in groups:
        values = _extract_labeled_values(text, patterns)
        # 항목이 포스터에 없으면 '정보 확인 필요' 대신 '-'로 표시합니다.
        result.append({"label": label, "value": " / ".join(values[:3]) if values else "-"})
    # 프로그램 정보는 실제로 적혀 있을 때만 별도 표시합니다.
    for label, patterns in [("🎬 주요 프로그램", [r"주요\s*프로그램", r"프로그램", r"공연\s*내용", r"programs?"])]:
        values = _extract_labeled_values(text, patterns)
        if values:
            result.append({"label": label, "value": " / ".join(values[:2])})
    return result


def extract_participation_info(text):
    """참가비·참가대상·참여방법은 핵심 내용과 분리해 보여줍니다."""
    groups = [
        ("💰 참가비", [r"참가\s*비", r"참여\s*비", r"입장료", r"참가비용"]),
        ("👥 참가 대상", [r"참가\s*대상", r"참여\s*대상", r"대상"]),
        ("📝 참여 방법", [r"참여\s*방법", r"참가\s*방법", r"신청\s*방법", r"접수\s*방법", r"신청\s*및\s*접수"]),
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
    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in raw_lines if line]
    if not lines:
        return ""

    title_type_words = [
        "축제", "페스티벌", "콘서트", "공연", "전시", "대회", "행사", "음악회",
        "마켓", "박람회", "데이", "페어", "쇼", "캠프", "파티", "페스타",
        "경기", "체험전", "발표회", "음악제", "영화제", "문화제",
        "festival", "concert", "event", "day", "fest", "fair", "exhibition", "show", "market", "conference"
    ]
    excluded_words = [
        "일시", "기간", "일정", "장소", "문의", "주최", "주관", "신청", "접수",
        "마감", "등록", "주소", "홈페이지", "http", "www.", "참가비", "입장료",
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
        if not line or is_metadata(line) or not 3 <= len(line) <= 65:
            continue
        score = 0
        if i < 10:
            score += 5
        elif i < 20:
            score += 2
        if re.search(r"[가-힣]", line):
            score += 3
        if any(word in line for word in title_type_words):
            score += 12
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
                if is_metadata(part):
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

    # 상단 제목이 여러 줄로 나뉘는 포스터의 제목 후보 보강
    top_parts = []
    for raw in lines[:6]:
        candidate = clean_line(raw)
        if candidate and not is_metadata(candidate) and 3 <= len(candidate) <= 30:
            if not re.search(r"20\d{2}년?\s*\d{1,2}월|오후|오전|OPEN|서울|광진구|캠퍼스", candidate, re.I):
                top_parts.append(candidate)
    if top_parts:
        combined_top = " ".join(top_parts[:2]).strip()
        if 4 <= len(combined_top) <= 45:
            candidates.append((28, 0, combined_top))

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
    year = re.search(r"(?<!\\d)(20\\d{2})(?!\\d)", text)
    if year and not re.search(r"\\b20\\d{2}\\b", best):
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
            st.markdown(f'<div class="diary-note"><div class="diary-label">📅 행사 날짜</div><div class="diary-value">{date_range}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="diary-note"><div class="diary-label">⏰ {time_label}</div><div class="diary-value">{time_text}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="diary-note"><div class="diary-label">📍 장소</div><div class="diary-value">{location}</div></div>', unsafe_allow_html=True)

        st.divider()
        st.markdown('<div style="font-size:1.8rem;font-weight:900;margin:0.25rem 0 0.8rem 0;">🐾 추가 정보</div>', unsafe_allow_html=True)
        special_info = data.get("special_info", []) or [
            {"label": "🎤 초청 가수 라인업", "value": "-"},
            {"label": "🏷️ 주최·주관", "value": "-"},
            {"label": "🔞 나이 제한", "value": "-"},
            {"label": "⚠️ 주의 사항", "value": "-"},
        ]
        for item in special_info:
            label = re.sub(r"^🐾\s*", "", item.get("label", ""))
            # 항목별 이모지는 초청 가수/주최·주관/연령/주의 사항의 의미를 유지
            if "초청 가수" in label or "라인업" in label: label = "🎤 초청 가수 라인업"
            elif "주최" in label or "주관" in label: label = "🏷️ 주최·주관"
            elif "나이" in label or "연령" in label: label = "🔞 나이 제한"
            elif "주의" in label: label = "⚠️ 주의 사항"
            st.write(f"**{label}**  {item.get('value') or '-'}")

        # 참가비·참가 대상·참여 방법도 '추가 정보' 영역 안에 통합해 표시합니다.
        for item in data.get("participation_info", []) or []:
            st.write(f"**{item['label']}**  {item['value'] or '-'}")
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
        <div class="main-title">📅 행사 포스터 일정 자동 등록</div>
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
    st.write(f"📁 선택한 포스터: **{len(uploaded_files)}장**")

    if st.button(
        "🔎 선택한 포스터에서 정보 찾기",
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
    st.subheader("📋 행사 정보")

    for index, data in enumerate(st.session_state.events):
        source_name = data.get("source_name", f"행사 {index + 1}")

        with st.container():
            # 한눈에 보는 행사 요약
            render_event_summary(data, index)

            if data.get("ocr_error"):
                st.warning(data["ocr_error"])
            # 자동 추출이 실패한 경우에만 실제 OCR 결과를 확인할 수 있게 합니다.
            if data.get("needs_review") and data.get("ocr_text"):
                with st.expander("🔎 읽어낸 포스터 글자 확인"):
                    st.code(data.get("ocr_text", ""), language=None)

            if data.get("needs_review"):
                st.warning("⚠️ 자동 추출 결과를 확인해주세요.")
                for reason in data.get("review_reasons", []):
                    st.write(f"• {reason}")

            # 여러 날짜가 발견되면 캘린더에 넣을 날짜를 항상 먼저 선택
            candidates = data.get("date_candidates", [])
            if len(candidates) > 1:
                labels = [f"{d} (후보 {i+1})" for i,d in enumerate(candidates)]
                current=data.get("selected_date", candidates[0])
                idx=candidates.index(current) if current in candidates else 0
                selected=st.selectbox("📅 캘린더에 추가할 행사 날짜", range(len(candidates)), index=idx, format_func=lambda x: labels[x], key=f"date_select_top_{index}")
                data["selected_date"]=candidates[selected]; data["date"]=candidates[selected]
                st.info("여러 날짜가 발견되었습니다. 행사 날짜를 선택한 뒤 캘린더에 추가하세요.")

            # 사용자가 수정할 수 있는 영역은 접어서 제공
            with st.expander("✏️ 정보 수정 / 자세히 보기"):
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

                st.markdown("**✨ 포스터에서 발견한 추가 정보**")
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
                    "⚠️ 자동 추출 결과와 수정한 정보를 확인했습니다.",
                    value=data.get("confirmed", False),
                    key=f"confirm_{index}"
                )
            else:
                data["confirmed"] = True

            st.session_state.events[index] = data

            duplicate = is_duplicate(data)

            if duplicate:
                st.error(
                    "🚫 이미 추가한 행사입니다. "
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
                    "📅 이 행사는 5일 이상 진행되는 장기 행사예요.\n\n"
                    "기간의 모든 날짜를 한꺼번에 등록하는 대신, Google Calendar나 휴대전화 캘린더를 열어 "
                    "실제로 참여할 날짜만 직접 선택해 등록해 주세요.\n\n"
                    f"행사 기간: {data.get('date', '')} ~ {data.get('end_date', '')}"
                )
            else:
                calendar_url = make_google_calendar_url(data)
                ics = make_ics(data)

                # 날짜가 있으면 캘린더 등록 기능을 보여주고,
                # 자동 추출이 애매한 경우에는 확인 전까지 버튼을 비활성화합니다.
                if blocked:
                    st.info("⚠️ 위의 정보 확인을 완료하면 캘린더에 추가할 수 있습니다.")

                col1, col2 = st.columns(2)

                with col1:
                    if calendar_url:
                        st.link_button(
                            "🗓️ Google Calendar에 추가",
                            calendar_url,
                            use_container_width=True,
                            disabled=blocked
                        )

                with col2:
                    if ics:
                        st.download_button(
                            "📥 일정 파일 다운로드",
                            data=ics,
                            file_name=f"event_{index + 1}.ics",
                            mime="text/calendar",
                            use_container_width=True,
                            key=f"ics_{index}",
                            disabled=blocked
                        )
                        st.caption("Google Calendar 외 다른 캘린더에서도 사용할 수 있는 일정 파일입니다.")

                if st.button(
                    "✅ 캘린더에 추가 완료로 표시",
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
    st.subheader("✅ 이미 추가한 행사")

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

