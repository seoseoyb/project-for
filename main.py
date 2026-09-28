import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote
from io import BytesIO


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="포스터 → 캘린더",
    page_icon="📅",
    layout="wide"
)


# =========================================================
# OCR 함수
# =========================================================

def preprocess_image(image):
    """
    OCR 정확도를 높이기 위한 간단한 이미지 전처리
    """

    # RGB 변환
    img = image.convert("RGB")

    # 너무 큰 이미지는 축소
    max_width = 1800

    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height))

    # 회색조
    gray = ImageOps.grayscale(img)

    # 대비 증가
    gray = ImageEnhance.Contrast(gray).enhance(1.5)

    return gray


def run_ocr(image):
    """
    한국어 + 영어 OCR
    """

    processed = preprocess_image(image)

    try:
        text = pytesseract.image_to_string(
            processed,
            lang="kor+eng",
            config="--psm 6"
        )
    except Exception:
        # 한국어 OCR 설정이 안 되어 있어도 영어 OCR 시도
        text = pytesseract.image_to_string(
            processed,
            lang="eng",
            config="--psm 6"
        )

    return text.strip()


# =========================================================
# 텍스트에서 정보 추출
# =========================================================

def extract_date(text):
    """
    여러 형태의 날짜를 찾아서 YYYY-MM-DD로 변환
    """

    patterns = [
        r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})",
        r"(20\d{2})\s+(\d{1,2})\s+(\d{1,2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))

            try:
                return f"{year:04d}-{month:02d}-{day:02d}"
            except Exception:
                pass

    # 월/일만 있는 경우
    match = re.search(
        r"(\d{1,2})[월./-]\s*(\d{1,2})[일./-]?",
        text
    )

    if match:
        month = int(match.group(1))
        day = int(match.group(2))

        current_year = datetime.now().year

        try:
            date_obj = datetime(current_year, month, day)
            return date_obj.strftime("%Y-%m-%d")
        except Exception:
            pass

    return ""


def extract_time(text):
    """
    19:00, 7:00 PM, 오후 7시 등의 시간 추출
    """

    # 19:00 / 19.00
    match = re.search(
        r"\b([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)\b",
        text
    )

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))

        return f"{hour:02d}:{minute:02d}"

    # 오후 7시 30분
    match = re.search(
        r"(오전|오후)\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?",
        text
    )

    if match:
        ampm = match.group(1)
        hour = int(match.group(2))
        minute = int(match.group(3) or 0)

        if ampm == "오후" and hour < 12:
            hour += 12

        if ampm == "오전" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    # 오후 7시
    match = re.search(
        r"(오전|오후)\s*(\d{1,2})\s*시",
        text
    )

    if match:
        ampm = match.group(1)
        hour = int(match.group(2))

        if ampm == "오후" and hour < 12:
            hour += 12

        if ampm == "오전" and hour == 12:
            hour = 0

        return f"{hour:02d}:00"

    return ""


def extract_url(text):
    """
    포스터에 있는 웹사이트 URL 추출
    """

    match = re.search(
        r"https?://[^\s<>\"]+",
        text
    )

    if match:
        return match.group(0).rstrip(".,)")

    # www로 시작하는 경우
    match = re.search(
        r"(www\.[^\s<>\"]+)",
        text
    )

    if match:
        return "https://" + match.group(1).rstrip(".,)")

    return ""


def extract_fee(text):
    """
    참가비/가격 관련 문장 추출
    """

    lines = text.splitlines()

    keywords = [
        "무료",
        "참가비",
        "입장료",
        "티켓",
        "원",
        "KRW",
        "₩"
    ]

    results = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if any(keyword.lower() in line.lower() for keyword in keywords):
            results.append(line)

    return "\n".join(results[:3])


def extract_location(text):
    """
    장소 관련 줄 추정
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    keywords = [
        "장소",
        "장소:",
        "venue",
        "location",
        "홀",
        "센터",
        "문화관",
        "아트센터",
        "갤러리",
        "대학교",
        "대학",
        "스튜디오"
    ]

    for line in lines:
        lower = line.lower()

        if any(keyword.lower() in lower for keyword in keywords):
            cleaned = re.sub(
                r"^(장소|venue|location)\s*[:：]?\s*",
                "",
                line,
                flags=re.IGNORECASE
            )

            if cleaned:
                return cleaned

    return ""


def extract_title(text):
    """
    제목을 완벽하게 이해하는 AI 대신
    포스터 상단의 큰 글씨로 추정할 수 있도록
    첫 번째 의미 있는 줄을 제목 후보로 사용
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    # 너무 짧거나 흔한 정보는 제외
    excluded = [
        "event",
        "notice",
        "program",
        "poster",
        "일시",
        "장소",
        "문의",
        "www"
    ]

    candidates = []

    for line in lines[:12]:
        lower = line.lower()

        if len(line) < 2:
            continue

        if any(word in lower for word in excluded):
            continue

        if re.search(r"\d{1,2}[:시]\d{0,2}", line):
            continue

        candidates.append(line)

    if candidates:
        return candidates[0]

    return lines[0]


def extract_organizer(text):
    """
    주최/주관/주최자 관련 줄 추정
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    keywords = [
        "주최",
        "주관",
        "organizer",
        "host"
    ]

    for line in lines:
        lower = line.lower()

        if any(keyword.lower() in lower for keyword in keywords):
            cleaned = re.sub(
                r"^(주최|주관|organizer|host)\s*[:：]?\s*",
                "",
                line,
                flags=re.IGNORECASE
            )

            if cleaned:
                return cleaned

    return ""


def build_event_data(text):
    """
    OCR 텍스트를 행사 데이터로 변환
    """

    date = extract_date(text)
    start_time = extract_time(text)
    url = extract_url(text)
    fee = extract_fee(text)
    location = extract_location(text)
    title = extract_title(text)
    organizer = extract_organizer(text)

    return {
        "title": title,
        "date": date,
        "start_time": start_time,
        "end_date": date,
        "end_time": "",
        "location": location,
        "organizer": organizer,
        "fee": fee,
        "description": text,
        "url": url,
    }


# =========================================================
# Google Calendar
# =========================================================

def make_google_calendar_url(data):
    title = data["title"].strip()
    date = data["date"].strip()
    start_time = data["start_time"].strip()
    end_time = data["end_time"].strip()
    location = data["location"].strip()
    description = data["description"].strip()

    if not title:
        title = "행사"

    if not date:
        return ""

    # 시간이 없는 경우 종일 일정
    if not start_time:

        date_obj = datetime.strptime(
            date,
            "%Y-%m-%d"
        )

        next_day = date_obj + timedelta(days=1)

        dates = (
            date_obj.strftime("%Y%m%d"),
            next_day.strftime("%Y%m%d")
        )

        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": f"{dates[0]}/{dates[1]}",
            "details": description,
            "location": location,
        }

    else:

        if not end_time:
            # 종료 시간이 없으면 1시간 뒤로 설정
            start_obj = datetime.strptime(
                f"{date} {start_time}",
                "%Y-%m-%d %H:%M"
            )

            end_obj = start_obj + timedelta(hours=1)

            end_date = end_obj.strftime("%Y-%m-%d")
            end_time = end_obj.strftime("%H:%M")

        else:
            end_date = data["end_date"].strip() or date

        start_dt = (
            date.replace("-", "")
            + "T"
            + start_time.replace(":", "")
            + "00"
        )

        end_dt = (
            end_date.replace("-", "")
            + "T"
            + end_time.replace(":", "")
            + "00"
        )

        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": f"{start_dt}/{end_dt}",
            "details": description,
            "location": location,
            "ctz": "Asia/Seoul",
        }

    return (
        "https://calendar.google.com/calendar/render?"
        + urlencode(params)
    )


# =========================================================
# ICS 파일
# =========================================================

def make_ics(data):

    title = data["title"].strip() or "행사"
    date = data["date"].strip()

    if not date:
        return None

    start_time = data["start_time"].strip()
    end_time = data["end_time"].strip()

    location = data["location"].strip()
    description = data["description"].strip()

    if start_time:

        start_obj = datetime.strptime(
            f"{date} {start_time}",
            "%Y-%m-%d %H:%M"
        )

        if end_time:

            end_obj = datetime.strptime(
                f"{date} {end_time}",
                "%Y-%m-%d %H:%M"
            )

        else:

            end_obj = start_obj + timedelta(hours=1)

        dtstart = start_obj.strftime("%Y%m%dT%H%M%S")
        dtend = end_obj.strftime("%Y%m%dT%H%M%S")

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Poster Calendar//EN",
            "BEGIN:VEVENT",
            f"SUMMARY:{title}",
            f"DTSTART;TZID=Asia/Seoul:{dtstart}",
            f"DTEND;TZID=Asia/Seoul:{dtend}",
            f"LOCATION:{location}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
            "END:VCALENDAR"
        ]

    else:

        date_obj = datetime.strptime(
            date,
            "%Y-%m-%d"
        )

        next_day = date_obj + timedelta(days=1)

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Poster Calendar//EN",
            "BEGIN:VEVENT",
            f"SUMMARY:{title}",
            f"DTSTART;VALUE=DATE:{date_obj.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{next_day.strftime('%Y%m%d')}",
            f"LOCATION:{location}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
            "END:VCALENDAR"
        ]

    return "\r\n".join(lines)


# =========================================================
# 화면
# =========================================================

st.title("📅 포스터 → 캘린더")
st.caption(
    "행사 포스터를 업로드하면 무료 OCR로 정보를 읽고 "
    "캘린더 일정으로 정리합니다."
)

st.info(
    "💡 OpenAI API를 사용하지 않습니다. "
    "API 키나 결제 설정이 필요 없습니다."
)


# =========================================================
# 파일 업로드
# =========================================================

uploaded_file = st.file_uploader(
    "행사 포스터를 업로드하세요",
    type=["png", "jpg", "jpeg", "webp"]
)


if uploaded_file:

    image = Image.open(uploaded_file)

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🖼️ 포스터")

        st.image(
            image,
            use_container_width=True
        )

    with col2:

        st.subheader("🔎 OCR 분석")

        if st.button(
            "포스터 읽기",
            type="primary",
            use_container_width=True
        ):

            with st.spinner("포스터의 글자를 읽는 중..."):

                ocr_text = run_ocr(image)

                st.session_state["ocr_text"] = ocr_text
                st.session_state["event_data"] = build_event_data(
                    ocr_text
                )

            st.success("OCR 분석이 완료되었습니다.")

    # OCR 결과가 있으면 표시
    if "ocr_text" in st.session_state:

        ocr_text = st.session_state["ocr_text"]

        st.divider()

        st.subheader("📄 읽은 텍스트")

        with st.expander(
            "OCR 원문 보기",
            expanded=False
        ):
            st.text_area(
                "OCR 결과",
                ocr_text,
                height=200,
                label_visibility="collapsed"
            )

        data = st.session_state["event_data"]

        st.subheader("✏️ 행사 정보 확인")

        st.caption(
            "OCR은 글자를 자동으로 읽은 결과이므로 "
            "날짜/시간/장소가 틀릴 수 있습니다. "
            "캘린더에 추가하기 전에 확인해주세요."
        )

        data["title"] = st.text_input(
            "행사명",
            value=data["title"]
        )

        col1, col2 = st.columns(2)

        with col1:
            data["date"] = st.text_input(
                "날짜",
                value=data["date"],
                placeholder="예: 2026-10-12"
            )

        with col2:
            data["start_time"] = st.text_input(
                "시작 시간",
                value=data["start_time"],
                placeholder="예: 19:00"
            )

        col1, col2 = st.columns(2)

        with col1:
            data["end_date"] = st.text_input(
                "종료 날짜",
                value=data["end_date"],
                placeholder="예: 2026-10-12"
            )

        with col2:
            data["end_time"] = st.text_input(
                "종료 시간",
                value=data["end_time"],
                placeholder="예: 20:00"
            )

        data["location"] = st.text_input(
            "장소",
            value=data["location"]
        )

        data["organizer"] = st.text_input(
            "주최 / 주관",
            value=data["organizer"]
        )

        data["fee"] = st.text_input(
            "참가비",
            value=data["fee"]
        )

        data["url"] = st.text_input(
            "신청 / 관련 URL",
            value=data["url"]
        )

        data["description"] = st.text_area(
            "설명",
            value=data["description"],
            height=150
        )

        # 상태 저장
        st.session_state["event_data"] = data

        st.divider()

        st.subheader("📅 캘린더")

        google_url = make_google_calendar_url(data)

        if google_url:

            st.link_button(
                "🗓️ Google Calendar에 추가",
                google_url,
                use_container_width=True
            )

        else:

            st.warning(
                "날짜를 입력하면 Google Calendar 버튼이 생성됩니다."
            )

        ics_content = make_ics(data)

        if ics_content:

            st.download_button(
                label="📥 .ics 파일 다운로드",
                data=ics_content,
                file_name="event.ics",
                mime="text/calendar",
                use_container_width=True
            )

        else:

            st.info(
                "날짜를 입력하면 .ics 파일을 다운로드할 수 있습니다."
            )

else:

    st.info(
        "👆 위에서 행사 포스터 이미지를 업로드해주세요."
    )


# =========================================================
# 안내
# =========================================================

st.divider()

st.caption(
    "이 앱은 OCR 결과를 자동으로 행사 정보로 정리합니다. "
    "중요한 일정은 캘린더에 추가하기 전에 날짜와 시간을 확인하세요."
)
