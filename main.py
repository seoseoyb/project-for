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
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');

    .stApp, .stApp * {
        font-family: "Noto Sans KR", "Pretendard", "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
    }

    h1 {
        font-family: "Noto Sans KR", "Pretendard", "Malgun Gothic", "Apple SD Gothic Neo", sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.03em;
    }

    .event-card {
        padding: 24px 26px;
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 18px;
        margin: 8px 0 18px 0;
        background: rgba(128,128,128,0.06);
    }

    .event-number {
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 1.5px;
        opacity: 0.6;
        margin-bottom: 4px;
    }

    .event-title {
        font-size: 32px;
        font-weight: 800;
        line-height: 1.25;
        margin-bottom: 22px;
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
        background: rgba(128,128,128,0.10);
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
        border-top: 1px solid rgba(128,128,128,0.2);
        padding-top: 16px;
    }

    .keyword-text {
        font-size: 16px;
        line-height: 1.7;
    }

    @media (max-width: 700px) {
        .event-title {
            font-size: 25px;
        }
        .event-main-info {
            flex-direction: column;
        }
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
                "2\r\n"
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
    """
    포스터에서 발견되는 날짜를 모두 찾고,
    '마감/신청/접수' 주변의 날짜는 신청 마감일 후보로 분류합니다.
    """
    patterns = [
        r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})",
        r"(20\d{2})\s+(\d{1,2})\s+(\d{1,2})",
        r"(\d{1,2})\s*월\s*(\d{1,2})\s*일",
        r"(\d{1,2})\s*[./-]\s*(\d{1,2})"
    ]

    found = []

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            date_obj = date_from_match(match)
            if not date_obj:
                continue

            start = max(0, match.start() - 35)
            end = min(len(text), match.end() + 35)
            context = text[start:end]

            deadline_words = [
                "마감", "신청", "접수", "등록", "지원",
                "신청기간", "접수기간", "까지"
            ]

            is_deadline = any(
                word in context
                for word in deadline_words
            )

            found.append({
                "date": date_obj.strftime("%Y-%m-%d"),
                "context": context.replace("\n", " "),
                "is_deadline": is_deadline,
                "position": match.start()
            })

    unique = []
    seen = set()

    for item in sorted(found, key=lambda x: x["position"]):
        key = (item["date"], item["is_deadline"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


def extract_event_dates(text):
    return [
        item["date"]
        for item in extract_date_candidates(text)
        if not item["is_deadline"]
    ]


def extract_deadline(text):
    candidates = [
        item["date"]
        for item in extract_date_candidates(text)
        if item["is_deadline"]
    ]
    return candidates[0] if candidates else ""


# =========================================================
# TIME
# =========================================================
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
        r"(?<!\d)([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)\s*(?:~|〜|～|-|–|—|부터)\s*([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)",
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
    single_colon = re.search(r"(?<!\d)([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)(?!\d)", text)
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
        line = re.sub(r"(장소|행사장소|공연장|개최장소|장소안내)\s*[|lI1]\s*", r"\1: ", line, flags=re.I)
        line = re.sub(r"(주최\s*·?\s*주관|주최|주관|일시|기간|일정|문의|문의처|연락처|참가\s*신청|신청|접수)\s*[|lI1]\s*", r"\1: ", line, flags=re.I)
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
    """포스터의 제목이 여러 줄로 나뉘어 있어도 하나의 행사명으로 묶어 찾습니다."""
    raw_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in raw_lines if line]
    if not lines:
        return ""

    excluded_words = [
        "일시", "기간", "일정", "장소", "문의", "주최", "주관", "주최주관",
        "신청", "접수", "마감", "등록", "주소", "홈페이지", "http", "www.",
        "무료", "입장료", "참가비", "문의처", "전화", "연락처"
    ]
    title_type_words = [
        "축제", "페스티벌", "콘서트", "공연", "전시", "대회", "행사", "음악회",
        "마켓", "박람회", "데이", "페어", "쇼", "캠프", "파티", "페스타"
    ]
    generic_only = set(title_type_words + ["festival", "concert", "event", "day"])

    def is_metadata(line):
        lower = line.lower()
        if any(word in lower for word in excluded_words):
            return True
        if re.search(r"20\d{2}[.\-/년]\s*\d{1,2}[.\-/월]\s*\d{1,2}", line):
            return True
        if re.search(r"\d{1,2}\s*월\s*\d{1,2}\s*일", line):
            return True
        if re.search(r"\d{1,2}\s*[:.]\s*\d{2}", line):
            return True
        if re.search(r"\d{1,2}\s*시(?:\s*\d{1,2}\s*분)?", line) and len(line) < 35:
            return True
        return False

    def clean(line):
        return re.sub(r"\s+", " ", line).strip(" -–—|•·")

    # OCR 순서상 제목이 위쪽에 있을 가능성이 높으므로 앞부분을 중심으로 탐색합니다.
    top_lines = lines[:30]
    candidates = []

    # 한 줄 후보
    for i, line in enumerate(top_lines):
        line = clean(line)
        if not line or is_metadata(line) or len(line) > 80:
            continue
        lower = line.lower()
        score = 0
        if i < 6:
            score += 4
        elif i < 12:
            score += 2
        if len(line) >= 4:
            score += 2
        if re.search(r"[가-힣]", line):
            score += 3
        if re.search(r"[A-Za-z]", line):
            score += 1
        if any(k in lower for k in title_type_words):
            score += 5
        # 행사 유형 단어만 있는 경우에는 제목으로 선택하지 않습니다.
        if lower.strip(" .") in generic_only:
            score -= 12
        if re.fullmatch(r"20\d{2}", line):
            score -= 5
        candidates.append((score, i, line))

    # 제목이 시각적으로 여러 줄로 분리된 경우를 위해 2~3줄을 묶습니다.
    # 예: ['2018', '롱런', '페스티벌'] -> '2018 롱런 페스티벌'
    #     ['함께 뛰는 재미', '스포츠 데이'] -> '함께 뛰는 재미 스포츠 데이'
    for i in range(min(len(top_lines), 18)):
        for size in (2, 3):
            if i + size > len(top_lines):
                continue
            block = [clean(x) for x in top_lines[i:i+size]]
            if any(not x or is_metadata(x) for x in block):
                continue
            if any(len(x) > 60 for x in block):
                continue
            combined = re.sub(r"\s+", " ", " ".join(block)).strip()
            if len(combined) < 4 or len(combined) > 100:
                continue

            score = 0
            if i < 5:
                score += 6
            elif i < 10:
                score += 3
            if any(re.search(r"[가-힣]", x) for x in block):
                score += 4
            if any(re.search(r"[A-Za-z]", x) for x in block):
                score += 1
            type_count = sum(1 for x in block if any(k in x.lower() for k in title_type_words))
            if type_count:
                score += 6
            # 여러 줄로 쪼개진 행사명을 합친 후보를 우선합니다.
            score += 5
            # 메타데이터처럼 보이는 조합은 제외합니다.
            if any(re.search(r"20\d{2}[.\-/년]\s*\d{1,2}", x) for x in block[1:]):
                score -= 8
            candidates.append((score, i, combined))

    if not candidates:
        return lines[0]

    # 행사 유형 단어가 포함된 완성형 제목을 우선하되, '페스티벌' 하나만 고르는 것을 방지합니다.
    candidates.sort(key=lambda x: (x[0], len(x[2])), reverse=True)
    best = candidates[0][2]

    # 최종 안전장치: 유형 단어 하나만 남은 경우, 그보다 앞쪽의 의미 있는 후보를 선택합니다.
    if best.lower().strip(" .") in generic_only:
        meaningful = [c for c in candidates if c[2].lower().strip(" .") not in generic_only]
        if meaningful:
            best = meaningful[0][2]

    return best


# =========================================================
# EVENT DATA / REVIEW
# =========================================================
def make_event_data(text, source_name="", image_bytes=None):
    date_candidates = extract_event_dates(text)
    deadline = extract_deadline(text)
    start_time, end_time = extract_time_range(text)
    special_info = extract_special_info(text)
    data = {
        "source_name": source_name, "image_bytes": image_bytes,
        "title": extract_title(text), "date_candidates": date_candidates,
        "selected_date": date_candidates[0] if date_candidates else "",
        "date": date_candidates[0] if date_candidates else "",
        "deadline": deadline, "start_time": start_time, "end_date": date_candidates[0] if date_candidates else "",
        "end_time": end_time, "location": extract_location(text), "organizer": extract_organizer(text),
        "fee": extract_fee(text), "url": extract_url(text), "special_info": special_info, "participation_info": extract_participation_info(text),
        "description": "", "ocr_text": text, "added": False, "confirmed": False,
    }
    reasons=[]
    if not data["title"]: reasons.append("행사명을 찾지 못했습니다.")
    if not date_candidates: reasons.append("행사 날짜를 찾지 못했습니다.")
    if len(date_candidates)>1: reasons.append("행사 날짜 후보가 여러 개 발견되었습니다.")
    if not data["location"]: reasons.append("장소를 확실하게 찾지 못했습니다.")
    if not data["start_time"]: reasons.append("시작 시간을 찾지 못했습니다.")
    data["review_reasons"]=reasons; data["needs_review"]=bool(reasons)
    return data


def empty_event_data(source_name=""):
    return {
        "source_name": source_name,
        "image_bytes": None,
        "title": "",
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
    """날짜/시간/장소/문의 같은 메타정보를 빼고 행사 활동·프로그램 중심으로 요약합니다."""
    if not text:
        return "행사 내용이 없습니다."
    text = clean_extracted_lines(text)
    lines=[re.sub(r"\s+", " ", x).strip(" -–—|•·") for x in text.splitlines() if x.strip()]
    title=(data or {}).get("title", "").strip()
    location=(data or {}).get("location", "").strip()
    organizer=(data or {}).get("organizer", "").strip()
    excluded_words=[
        "장소", "주최", "주관", "문의", "연락처", "신청", "접수", "마감", "등록",
        "일시", "날짜", "시간", "주소", "홈페이지", "http://", "https://", "www.",
        "참가비", "입장료", "전화", "이메일", "이메일주소", "신청기간"
    ]
    activity_words=[
        "공연", "콘서트", "체험", "전시", "강연", "토크", "게임", "대회", "경기",
        "마켓", "부스", "워크숍", "워크샵", "축하", "출연", "가수", "밴드", "댄스",
        "이벤트", "프로그램", "행사", "축제", "페스티벌", "캠페인", "상영", "발표"
    ]
    useful=[]
    for line in lines:
        if len(line)<4 or line == title or line == location or line == organizer:
            continue
        if any(w in line for w in excluded_words):
            continue
        if re.search(r"20\d{2}.*\d{1,2}.*\d{1,2}", line):
            continue
        if re.search(r"\d{1,2}\s*[:시]\s*\d{0,2}", line):
            continue
        # 숫자/기호만 남은 OCR 오류 제거
        if re.fullmatch(r"[\d\s|lI._-]+", line):
            continue
        # 행사명 유형 단어만 있는 줄은 핵심 내용으로 쓰지 않음
        if line.lower().strip() in {"페스티벌","축제","행사","공연","콘서트","festival","event"}:
            continue
        score=sum(2 for w in activity_words if w in line)
        if score or len(line)>=8:
            useful.append((score,line))
    useful.sort(key=lambda x:x[0], reverse=True)
    selected=[]
    for _,line in useful:
        if line not in selected:
            selected.append(line)
        if len(selected)>=4:
            break
    return "  ·  ".join(x[:70] + ("…" if len(x)>70 else "") for x in selected) or "포스터에 행사 활동이나 프로그램 정보가 표시되어 있지 않습니다."

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
            st.markdown(f"# {title}")
            c1,c2=st.columns(2)
            with c1:
                st.markdown("**📅 행사 날짜**"); st.markdown(f"### {date_range}")
            with c2:
                st.markdown("**⏰ 시간**"); st.markdown(f"### {time_text}")
            st.markdown(f"**📍 장소**  {location}")
            st.markdown(f"**🏢 주최·주관**  {organizer}")
            if deadline: st.markdown(f"**📝 신청 마감**  {pretty(deadline)}")
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
st.title("📅 행사 포스터 일정 자동 등록")
st.write(
    "행사 포스터를 여러 장 올리면 행사 정보를 읽고 "
    "캘린더 일정으로 정리합니다."
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

