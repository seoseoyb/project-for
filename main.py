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

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Jua&display=swap');

    /* 전체 테마: 따뜻한 크림 + 라벤더 포인트 */
    .stApp {
        font-family: "Jua", "Gowun Dodum", "Malgun Gothic", sans-serif;
        background: linear-gradient(180deg, #eee7fb 0%, #f8f4ff 44%, #fff9f1 100%);
        color: #51485d;
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
        color: #4b4266;
        margin: 0;
    }

    .main-title-wrap .main-subtitle {
        margin-top: 10px;
        color: #81778f;
        font-family: "Gowun Dodum", "Jua", sans-serif;
        font-size: 16px;
        font-weight: 400;
    }

    /* 업로드 영역 */
    [data-testid="stFileUploader"] {
        background: rgba(255,253,249,.92);
        border: 2px dashed #cfc0dd;
        border-radius: 18px 24px 20px 14px;
        padding: 9px;
        box-shadow: 3px 4px 0 rgba(218,203,226,.42), 0 10px 22px rgba(84,69,105,.07);
    }

    /* 메인 정보 찾기 버튼 */
    div.stButton > button[kind="primary"] {
        border-radius: 16px !important;
        min-height: 52px !important;
        font-family: "Jua", "Gowun Dodum", sans-serif !important;
        font-size: 18px !important;
        letter-spacing: -0.01em;
        border: 0 !important;
        box-shadow: 0 7px 18px rgba(113, 91, 155, 0.16);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 22px rgba(113, 91, 155, 0.22);
    }

    /* ───────── 다이어리 노트형 행사 카드 ───────── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        position: relative;
        margin: 28px 0 34px 0 !important;
        padding: 28px 28px 24px 42px !important;
        border-radius: 10px 18px 14px 12px !important;
        border: 1px solid #e4d8ea !important;
        border-left: 3px solid #d7c3df !important;
        background-color: #fffdf8 !important;
        background-image:
            linear-gradient(to right, transparent 0, transparent 31px, rgba(218,191,211,.30) 32px, transparent 33px),
            repeating-linear-gradient(to bottom, transparent 0, transparent 31px, rgba(196,185,211,.18) 32px, transparent 33px);
        box-shadow: 4px 7px 0 rgba(214,197,224,.45), 0 14px 30px rgba(84,69,105,.10);
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
        background: rgba(211,194,232,.82);
        box-shadow: 0 2px 5px rgba(90,70,110,.10);
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
        background: #d6c4dd;
        box-shadow: 0 39px #d6c4dd, 0 78px #d6c4dd, 0 117px #d6c4dd, 0 156px #d6c4dd, 0 195px #d6c4dd;
    }

    .event-title {
        font-family: "Jua", "Gowun Dodum", sans-serif;
        font-size: 32px;
        font-weight: 400;
        line-height: 1.25;
        margin-bottom: 22px;
        color: #51445f;
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
        background: #faf6ff;
        border: 1px dashed #d9cce7;
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
        border-top: 1px solid #eee7f4;
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
        border: 1px dashed #d6c6df;
        background: rgba(255,250,244,.88);
        box-shadow: 2px 3px 0 rgba(219,203,227,.34);
    }

    .diary-note::after {
        content: "";
        position: absolute;
        right: 10px;
        top: 8px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 2px solid #d9c9df;
        background: #fffdf8;
    }

    .diary-label {
        font-size: 13px;
        font-weight: 700;
        color: #8a7898;
        margin-bottom: 4px;
    }

    .diary-value {
        font-size: 18px;
        color: #50465b;
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
        color: #4b4266;
        margin: 4px 0 2px 0;
        letter-spacing: -0.02em;
    }
    .event-display-subtitle {
        font-family: "Gowun Dodum", "Jua", sans-serif;
        font-size: 15px;
        line-height: 1.45;
        font-weight: 400;
        color: #8b7f96;
        margin: 0 0 18px 1px;
    }

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
        if not parsed_results:
            return "", "이미지에서 글자를 찾지 못했습니다."

        texts = [
            item.get("ParsedText", "")
            for item in parsed_results
            if item.get("ParsedText")
        ]
        final_text = "\n".join(texts).strip()

        if not final_text:
            return "", "OCR은 완료되었지만 읽어낸 글자가 없습니다."

        return final_text, ""

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
    text = clean_extracted_lines(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    # 라벨이 있는 장소를 가장 우선
    for line in lines:
        if re.search(r"^(장소|행사장소|공연장|개최장소|장소안내|venue|location)\s*[:：]", line, re.I):
            value = clean_labeled_value(line, ["장소", "행사장소", "공연장", "개최장소", "장소안내", "venue", "location"])
            if value: return value

    # OCR에서 '행사장소' 라벨과 장소명이 서로 다른 줄로 분리되는 경우
    # 예: 행사장소 / 새마을 공원 운동장
    location_labels = ("장소", "행사장소", "공연장", "개최장소", "장소안내", "venue", "location")
    for i, line in enumerate(lines):
        if re.fullmatch(r"(?:장소|행사장소|공연장|개최장소|장소안내|venue|location)", line, re.I):
            for next_line in lines[i + 1:i + 3]:
                if next_line and not re.search(r"^(일시|날짜|시간|참가|참여|주최|주관|문의|신청|접수|마감)", next_line, re.I):
                    return next_line.strip(" :：|-|")

    # '행사장소 새마을 공원 운동장'처럼 한 줄에 붙어 있으나 콜론이 없는 경우
    for line in lines:
        m = re.search(r"^(?:장소|행사장소|공연장|개최장소|장소안내)\s+(.+)$", line, re.I)
        if m and m.group(1).strip():
            return m.group(1).strip(" :：|-|")

    # 장소 단어가 문장 뒤에 붙은 경우
    for line in lines:
        if any(k in line.lower() for k in ["문화회관", "문화관", "아트센터", "예술회관", "공연장", "콘서트홀", "체육관", "대강당", "소극장", "대극장", "센터", "홀", "갤러리", "운동장", "야외무대"]):
            if not any(k in line for k in ["주최", "문의", "신청"]):
                return line
    return ""


def extract_organizer(text):
    text = clean_extracted_lines(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if re.search(r"^(주최|주관|주최\s*·\s*주관|organizer)\s*[:：]", line, re.I):
            return clean_labeled_value(line, ["주최·주관", "주최 · 주관", "주최", "주관", "organizer"])
    # 라벨이 중간에 붙은 경우
    for line in lines:
        if "주최" in line or "주관" in line:
            value = re.sub(r".*?(주최|주관)\s*[:：]?\s*", "", line, count=1)
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
        ("🎤 초청 가수", [r"초청\s*가수", r"초청가수"]),
        ("🎤 출연진", [r"출연진", r"출연\s*아티스트", r"게스트"]),
        ("🎬 주요 프로그램", [r"주요\s*프로그램", r"프로그램", r"공연\s*내용"]),
    ]
    for label, patterns in groups:
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
        "경기", "체험전", "발표회", "음악제", "영화제", "문화제"
    ]
    excluded_words = [
        "일시", "기간", "일정", "장소", "문의", "주최", "주관", "신청", "접수",
        "마감", "등록", "주소", "홈페이지", "http", "www.", "참가비", "입장료",
        "문의처", "참가 대상", "참여 방법", "참여방법", "신청 방법"
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
            pos = line.find(word)
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
    return best or clean_line(lines[0]) or lines[0][:50]


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
    deadline = extract_deadline(text)
    start_time, end_time = extract_time_range(text)
    special_info = extract_special_info(text)
    data = {
        "source_name": source_name, "image_bytes": image_bytes,
        "title": extract_title(text), "title_subtitle": split_title_for_display(extract_title(text))[1], "date_candidates": date_candidates,
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
    title=data.get("title", "").strip() or "행사명 확인 필요"
    date=data.get("date", "").strip() or "날짜 확인 필요"
    end_date=data.get("end_date", "").strip() or date
    start_time=data.get("start_time", "").strip(); end_time=data.get("end_time", "").strip()
    location=data.get("location", "").strip() or "장소 확인 필요"
    organizer=data.get("organizer", "").strip() or "주최·주관 정보 확인 필요"
    deadline=data.get("deadline", "").strip()
    def pretty(v):
        try: return datetime.strptime(v, "%Y-%m-%d").strftime("%Y.%m.%d")
        except Exception: return v
    date_range=pretty(date) if date==end_date else f"{pretty(date)} ~ {pretty(end_date)}"
    time_text=f"{start_time} ~ {end_time}" if start_time and end_time else (start_time or "시간 확인 필요")
    with st.container(border=True):
        image_col, info_col=st.columns([1, 1.7])
        with image_col:
            if data.get("image_bytes"):
                st.image(io.BytesIO(data["image_bytes"]), caption=data.get("source_name", "포스터"), width="stretch")
        with info_col:
            st.caption(f"EVENT {index+1}")
            title_main, title_sub = split_title_for_display(title)
            st.markdown(
                f'<div class="event-display-title">{title_main}</div>'
                + (f'<div class="event-display-subtitle">{title_sub}</div>' if title_sub else ""),
                unsafe_allow_html=True
            )
            c1,c2=st.columns(2)
            with c1:
                st.markdown("**📅 행사 날짜**"); st.markdown(f"### {date_range}")
            with c2:
                st.markdown("**⏰ 시간**"); st.markdown(f"### {time_text}")
            st.markdown(f'<div class="diary-note"><div class="diary-label">📍 장소</div><div class="diary-value">{location}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="diary-note"><div class="diary-label">🏢 주최·주관</div><div class="diary-value">{organizer}</div></div>', unsafe_allow_html=True)
            if deadline: st.markdown(f'<div class="diary-note"><div class="diary-label">📝 신청 마감</div><div class="diary-value">{pretty(deadline)}</div></div>', unsafe_allow_html=True)
        if data.get("special_info"):
            st.divider(); st.markdown("**✨ 추가 정보**")
            for item in data["special_info"]:
                st.write(f"{item['label']}  {item['value']}")

        if data.get("participation_info"):
            st.divider(); st.markdown("**🙋 참가 정보**")
            for item in data["participation_info"]:
                st.write(f"{item['label']}  {item['value']}")

        st.divider(); st.markdown("**💡 핵심 내용**")
        st.write(make_keyword_summary(data.get("ocr_text", ""), data))


# =========================================================
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

            calendar_url = make_google_calendar_url(data)
            ics = make_ics(data)
            blocked = data.get("needs_review") and not data.get("confirmed")

            # 날짜가 있으면 모든 행사에 캘린더 영역을 보여주고,
            # 자동 추출이 애매한 경우에는 확인 전까지 버튼만 비활성화합니다.
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
                use_container_width=True
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

