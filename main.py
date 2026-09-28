import streamlit as st
from PIL import Image
import urllib.request
import urllib.parse
import urllib.error
import json
import re
from datetime import datetime, timedelta


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="포스터 → 캘린더",
    page_icon="📅",
    layout="wide"
)


# =========================================================
# OCR
# =========================================================

def ocr_image(image):
    """
    외부 OCR 서비스를 이용해서 이미지의 글자를 읽습니다.
    Python OCR 패키지를 사용하지 않기 때문에
    Streamlit Cloud에서 pytesseract 설치 문제가 없습니다.
    """

    try:
        # 이미지를 JPEG로 변환
        image = image.convert("RGB")

        # 너무 큰 이미지는 줄임
        max_width = 1800

        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height))

        # JPEG bytes 만들기
        import io

        image_bytes = io.BytesIO()

        image.save(
            image_bytes,
            format="JPEG",
            quality=90
        )

        image_data = image_bytes.getvalue()

        # multipart/form-data 생성
        boundary = "----PosterCalendarBoundary"

        body = []

        body.append(
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="apikey"\r\n\r\n'
            "helloworld\r\n"
        )

        body.append(
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="language"\r\n\r\n'
            "kor\r\n"
        )

        body.append(
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="isOverlayRequired"\r\n\r\n'
            "false\r\n"
        )

        body.append(
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="OCREngine"\r\n\r\n'
            "2\r\n"
        )

        body.append(
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="poster.jpg"\r\n'
            "Content-Type: image/jpeg\r\n\r\n"
        )

        body_bytes = "".join(body).encode("utf-8")

        ending = f"\r\n--{boundary}--\r\n".encode("utf-8")

        request_body = (
            body_bytes
            + image_data
            + ending
        )

        request = urllib.request.Request(
            "https://api.ocr.space/parse/image",
            data=request_body,
            method="POST"
        )

        request.add_header(
            "Content-Type",
            f"multipart/form-data; boundary={boundary}"
        )

        request.add_header(
            "User-Agent",
            "PosterCalendar/1.0"
        )

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        if result.get("IsErroredOnProcessing"):
            return "", "OCR 서버가 이미지를 읽지 못했습니다."

        parsed_results = result.get(
            "ParsedResults",
            []
        )

        if not parsed_results:
            return "", "이미지에서 글자를 찾지 못했습니다."

        texts = []

        for item in parsed_results:
            parsed_text = item.get(
                "ParsedText",
                ""
            )

            if parsed_text:
                texts.append(parsed_text)

        final_text = "\n".join(texts).strip()

        if not final_text:
            return "", "읽어낸 글자가 없습니다."

        return final_text, ""

    except Exception as e:

        return "", (
            "OCR 연결에 실패했습니다. "
            "아래에서 행사 정보를 직접 입력할 수 있습니다."
        )


# =========================================================
# DATE
# =========================================================

def extract_date(text):

    patterns = [
        r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})",
        r"(20\d{2})\s+(\d{1,2})\s+(\d{1,2})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:

            try:

                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))

                date_obj = datetime(
                    year,
                    month,
                    day
                )

                return date_obj.strftime(
                    "%Y-%m-%d"
                )

            except Exception:
                pass

    # 10월 12일
    match = re.search(
        r"(\d{1,2})\s*월\s*(\d{1,2})\s*일",
        text
    )

    if match:

        try:

            year = datetime.now().year
            month = int(match.group(1))
            day = int(match.group(2))

            date_obj = datetime(
                year,
                month,
                day
            )

            return date_obj.strftime(
                "%Y-%m-%d"
            )

        except Exception:
            pass

    return ""


# =========================================================
# TIME
# =========================================================

def extract_time(text):

    # 19:00
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

    return ""


# =========================================================
# URL
# =========================================================

def extract_url(text):

    match = re.search(
        r"https?://[^\s<>\"]+",
        text
    )

    if match:
        return match.group(0).rstrip(
            ".,)"
        )

    match = re.search(
        r"www\.[^\s<>\"]+",
        text
    )

    if match:
        return (
            "https://"
            + match.group(0).rstrip(".,)")
        )

    return ""


# =========================================================
# LOCATION
# =========================================================

def extract_location(text):

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
        "문화관",
        "문화회관",
        "센터",
        "홀",
        "아트센터",
        "갤러리",
        "대학교",
        "대학",
        "스튜디오"
    ]

    for line in lines:

        lower = line.lower()

        if any(
            keyword.lower() in lower
            for keyword in keywords
        ):

            cleaned = re.sub(
                r"^(장소|venue|location)\s*[:：]?\s*",
                "",
                line,
                flags=re.IGNORECASE
            )

            return cleaned

    return ""


# =========================================================
# ORGANIZER
# =========================================================

def extract_organizer(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines:

        if (
            "주최" in line
            or "주관" in line
            or "organizer" in line.lower()
        ):

            cleaned = re.sub(
                r"^(주최|주관|organizer)\s*[:：]?\s*",
                "",
                line,
                flags=re.IGNORECASE
            )

            return cleaned

    return ""


# =========================================================
# FEE
# =========================================================

def extract_fee(text):

    lines = text.splitlines()

    keywords = [
        "무료",
        "참가비",
        "입장료",
        "티켓",
        "원",
        "₩"
    ]

    found = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if any(
            keyword.lower() in line.lower()
            for keyword in keywords
        ):

            found.append(line)

    return "\n".join(found[:3])


# =========================================================
# TITLE
# =========================================================

def extract_title(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    excluded = [
        "event",
        "notice",
        "program",
        "poster",
        "일시",
        "장소",
        "문의",
        "주최",
        "주관"
    ]

    for line in lines[:10]:

        lower = line.lower()

        if len(line) < 2:
            continue

        if any(
            word in lower
            for word in excluded
        ):
            continue

        if re.search(
            r"\d{1,2}\s*[:시]",
            line
        ):
            continue

        return line

    return lines[0]


# =========================================================
# EVENT DATA
# =========================================================

def make_event_data(text):

    date = extract_date(text)

    return {
        "title": extract_title(text),
        "date": date,
        "start_time": extract_time(text),
        "end_date": date,
        "end_time": "",
        "location": extract_location(text),
        "organizer": extract_organizer(text),
        "fee": extract_fee(text),
        "url": extract_url(text),
        "description": text
    }


# =========================================================
# GOOGLE CALENDAR
# =========================================================

def make_google_calendar_url(data):

    title = data.get(
        "title",
        ""
    ).strip() or "행사"

    date = data.get(
        "date",
        ""
    ).strip()

    start_time = data.get(
        "start_time",
        ""
    ).strip()

    end_time = data.get(
        "end_time",
        ""
    ).strip()

    end_date = data.get(
        "end_date",
        ""
    ).strip() or date

    location = data.get(
        "location",
        ""
    ).strip()

    description = data.get(
        "description",
        ""
    ).strip()

    if not date:
        return ""

    # 종일 일정
    if not start_time:

        date_obj = datetime.strptime(
            date,
            "%Y-%m-%d"
        )

        next_day = date_obj + timedelta(
            days=1
        )

        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": (
                date_obj.strftime("%Y%m%d")
                + "/"
                + next_day.strftime("%Y%m%d")
            ),
            "details": description,
            "location": location
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

            end_obj = start_obj + timedelta(
                hours=1
            )

        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": (
                start_obj.strftime("%Y%m%dT%H%M%S")
                + "/"
                + end_obj.strftime("%Y%m%dT%H%M%S")
            ),
            "details": description,
            "location": location,
            "ctz": "Asia/Seoul"
        }

    return (
        "https://calendar.google.com/calendar/render?"
        + urllib.parse.urlencode(params)
    )


# =========================================================
# ICS
# =========================================================

def make_ics(data):

    title = data.get(
        "title",
        ""
    ).strip() or "행사"

    date = data.get(
        "date",
        ""
    ).strip()

    if not date:
        return None

    start_time = data.get(
        "start_time",
        ""
    ).strip()

    end_time = data.get(
        "end_time",
        ""
    ).strip()

    location = data.get(
        "location",
        ""
    ).strip()

    description = data.get(
        "description",
        ""
    ).strip()

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

            end_obj = start_obj + timedelta(
                hours=1
            )

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Poster Calendar//EN",
            "BEGIN:VEVENT",
            f"SUMMARY:{title}",
            "DTSTART;TZID=Asia/Seoul:"
            + start_obj.strftime(
                "%Y%m%dT%H%M%S"
            ),
            "DTEND;TZID=Asia/Seoul:"
            + end_obj.strftime(
                "%Y%m%dT%H%M%S"
            ),
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

        next_day = date_obj + timedelta(
            days=1
        )

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Poster Calendar//EN",
            "BEGIN:VEVENT",
            f"SUMMARY:{title}",
            "DTSTART;VALUE=DATE:"
            + date_obj.strftime("%Y%m%d"),
            "DTEND;VALUE=DATE:"
            + next_day.strftime("%Y%m%d"),
            f"LOCATION:{location}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
            "END:VCALENDAR"
        ]

    return "\r\n".join(lines)


# =========================================================
# APP
# =========================================================

st.title("📅 포스터 → 캘린더")

st.write(
    "행사 포스터를 올리면 행사 정보를 읽어 "
    "캘린더 일정으로 정리합니다."
)

st.info(
    "🔒 이 버전은 OpenAI API를 사용하지 않습니다. "
    "OpenAI API Key도 필요하지 않습니다."
)


uploaded_file = st.file_uploader(
    "행사 포스터를 업로드하세요.",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp"
    ]
)


if uploaded_file:

    image = Image.open(
        uploaded_file
    )

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🖼️ 포스터")

        st.image(
            image,
            use_container_width=True
        )

    with col2:

        st.subheader("🔎 행사 정보 읽기")

        if st.button(
            "포스터 읽기",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "포스터를 읽는 중입니다..."
            ):

                text, error = ocr_image(
                    image
                )

            if text:

                st.session_state[
                    "ocr_text"
                ] = text

                st.session_state[
                    "event_data"
                ] = make_event_data(text)

                st.success(
                    "포스터 읽기가 완료되었습니다."
                )

            else:

                st.warning(
                    error
                )

                st.info(
                    "OCR에 실패해도 아래에서 "
                    "행사 정보를 직접 입력할 수 있습니다."
                )

                st.session_state[
                    "ocr_text"
                ] = ""

                st.session_state[
                    "event_data"
                ] = {
                    "title": "",
                    "date": "",
                    "start_time": "",
                    "end_date": "",
                    "end_time": "",
                    "location": "",
                    "organizer": "",
                    "fee": "",
                    "url": "",
                    "description": ""
                }


# =========================================================
# EVENT EDITOR
# =========================================================

if "event_data" in st.session_state:

    data = st.session_state[
        "event_data"
    ]

    st.divider()

    st.subheader(
        "✏️ 행사 정보 확인 / 수정"
    )

    st.caption(
        "자동으로 읽은 정보가 틀릴 수 있으니 "
        "캘린더에 추가하기 전에 확인해주세요."
    )

    data["title"] = st.text_input(
        "행사명",
        value=data.get("title", "")
    )

    col1, col2 = st.columns(2)

    with col1:

        data["date"] = st.text_input(
            "행사 날짜",
            value=data.get("date", ""),
            placeholder="2026-10-12"
        )

    with col2:

        data["start_time"] = st.text_input(
            "시작 시간",
            value=data.get("start_time", ""),
            placeholder="19:00"
        )

    col1, col2 = st.columns(2)

    with col1:

        data["end_date"] = st.text_input(
            "종료 날짜",
            value=data.get("end_date", ""),
            placeholder="2026-10-12"
        )

    with col2:

        data["end_time"] = st.text_input(
            "종료 시간",
            value=data.get("end_time", ""),
            placeholder="20:00"
        )

    data["location"] = st.text_input(
        "장소",
        value=data.get("location", "")
    )

    data["organizer"] = st.text_input(
        "주최 / 주관",
        value=data.get("organizer", "")
    )

    data["fee"] = st.text_input(
        "참가비",
        value=data.get("fee", "")
    )

    data["url"] = st.text_input(
        "신청 URL",
        value=data.get("url", "")
    )

    data["description"] = st.text_area(
        "설명",
        value=data.get("description", ""),
        height=150
    )

    st.session_state[
        "event_data"
    ] = data

    st.divider()

    st.subheader(
        "📅 캘린더에 추가"
    )

    calendar_url = make_google_calendar_url(
        data
    )

    if calendar_url:

        st.link_button(
            "🗓️ Google Calendar에 추가",
            calendar_url,
            use_container_width=True
        )

    else:

        st.warning(
            "먼저 행사 날짜를 입력해주세요."
        )

    ics = make_ics(data)

    if ics:

        st.download_button(
            "📥 .ics 파일 다운로드",
            data=ics,
            file_name="event.ics",
            mime="text/calendar",
            use_container_width=True
        )

    else:

        st.info(
            "날짜를 입력하면 .ics 파일을 받을 수 있습니다."
        )


# =========================================================
# OCR TEXT
# =========================================================

if st.session_state.get(
    "ocr_text",
    ""
):

    with st.expander(
        "📄 OCR 원문 보기"
    ):

        st.text(
            st.session_state["ocr_text"]
        )


st.divider()

st.caption(
    "Poster Calendar · OpenAI API 없이 작동하는 버전"
)
