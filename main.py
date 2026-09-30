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
    page_title="포스터 → 캘린더",
    page_icon="📅",
    layout="wide"
)

# =========================================================
# OCR
# =========================================================
def ocr_image(image):
    """OCR.Space를 이용해 포스터의 글자를 읽습니다."""
    try:
        image = image.convert("RGB")
        max_width = 1800

        if image.width > max_width:
            ratio = max_width / image.width
            image = image.resize(
                (max_width, int(image.height * ratio))
            )

        image_bytes = io.BytesIO()
        image.save(image_bytes, format="JPEG", quality=90)
        image_data = image_bytes.getvalue()

        boundary = "----PosterCalendarBoundary"
        parts = [
            (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="apikey"\r\n\r\n'
                "helloworld\r\n"
            ),
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
        request.add_header("User-Agent", "PosterCalendar/2.0")

        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        if result.get("IsErroredOnProcessing"):
            return "", "OCR 서버가 이미지를 읽지 못했습니다."

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
            return "", "읽어낸 글자가 없습니다."

        return final_text, ""

    except Exception:
        return "", (
            "OCR 연결에 실패했습니다. "
            "아래에서 행사 정보를 직접 입력할 수 있습니다."
        )


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
def extract_time(text):
    match = re.search(
        r"\b([01]?\d|2[0-3])\s*[:.]\s*([0-5]\d)\b",
        text
    )
    if match:
        return f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"

    match = re.search(
        r"(오전|오후)\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?",
        text
    )
    if match:
        hour = int(match.group(2))
        minute = int(match.group(3) or 0)

        if match.group(1) == "오후" and hour < 12:
            hour += 12
        if match.group(1) == "오전" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    return ""


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


def extract_location(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    keywords = [
        "장소", "venue", "location", "문화관", "문화회관",
        "센터", "홀", "아트센터", "갤러리", "대학교",
        "대학", "스튜디오"
    ]

    for line in lines:
        if any(keyword.lower() in line.lower() for keyword in keywords):
            cleaned = re.sub(
                r"^(장소|venue|location)\s*[:：]?\s*",
                "",
                line,
                flags=re.IGNORECASE
            )
            return cleaned

    return ""


def extract_organizer(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        if (
            "주최" in line
            or "주관" in line
            or "organizer" in line.lower()
        ):
            return re.sub(
                r"^(주최|주관|organizer)\s*[:：]?\s*",
                "",
                line,
                flags=re.IGNORECASE
            )

    return ""


def extract_fee(text):
    keywords = ["무료", "참가비", "입장료", "티켓", "원", "₩"]
    found = []

    for line in text.splitlines():
        line = line.strip()
        if line and any(k.lower() in line.lower() for k in keywords):
            found.append(line)

    return "\n".join(found[:3])


def extract_title(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        return ""

    excluded = [
        "event", "notice", "program", "poster", "일시",
        "장소", "문의", "주최", "주관", "신청", "접수", "마감"
    ]

    for line in lines[:12]:
        lower = line.lower()

        if len(line) < 2:
            continue
        if any(word in lower for word in excluded):
            continue
        if re.search(r"\d{1,2}\s*[:시]", line):
            continue

        return line

    return lines[0]


# =========================================================
# EVENT DATA / REVIEW
# =========================================================
def make_event_data(text, source_name=""):
    date_candidates = extract_event_dates(text)
    deadline = extract_deadline(text)

    data = {
        "source_name": source_name,
        "title": extract_title(text),
        "date_candidates": date_candidates,
        "selected_date": date_candidates[0] if date_candidates else "",
        "date": date_candidates[0] if date_candidates else "",
        "deadline": deadline,
        "start_time": extract_time(text),
        "end_date": date_candidates[0] if date_candidates else "",
        "end_time": "",
        "location": extract_location(text),
        "organizer": extract_organizer(text),
        "fee": extract_fee(text),
        "url": extract_url(text),
        "description": text,
        "ocr_text": text,
        "added": False,
        "confirmed": False,
    }

    reasons = []

    if not data["title"]:
        reasons.append("행사명을 찾지 못했습니다.")
    if not date_candidates:
        reasons.append("행사 날짜를 찾지 못했습니다.")
    if len(date_candidates) > 1:
        reasons.append("행사 날짜 후보가 여러 개 발견되었습니다.")
    if not data["location"]:
        reasons.append("장소를 확실하게 찾지 못했습니다.")
    if not data["start_time"]:
        reasons.append("시작 시간을 찾지 못했습니다.")

    data["review_reasons"] = reasons
    data["needs_review"] = bool(reasons)

    return data


def empty_event_data(source_name=""):
    return {
        "source_name": source_name,
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
        "fee": "",
        "url": "",
        "description": "",
        "ocr_text": "",
        "added": False,
        "confirmed": False,
        "needs_review": True,
        "review_reasons": ["OCR 결과를 확인해주세요."]
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
    location = data.get("location", "").strip()
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
                "location": location,
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
    location = data.get("location", "").strip()
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
                f"LOCATION:{ics_escape(location)}",
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
                f"LOCATION:{ics_escape(location)}",
                f"DESCRIPTION:{ics_escape(description)}",
                "END:VEVENT",
                "END:VCALENDAR"
            ]

        return "\r\n".join(lines)

    except Exception:
        return None


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
st.title("📅 포스터 → 캘린더")
st.write(
    "행사 포스터를 여러 장 올리면 행사 정보를 읽고 "
    "캘린더 일정으로 정리합니다."
)

st.info(
    "🔒 이 버전은 OpenAI API를 사용하지 않습니다. "
    "OCR 결과는 캘린더에 추가하기 전에 직접 확인할 수 있습니다."
)

uploaded_files = st.file_uploader(
    "행사 포스터를 업로드하세요. 여러 장을 한 번에 선택할 수 있습니다.",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📁 선택한 포스터: **{len(uploaded_files)}장**")

    if st.button(
        "🔎 선택한 포스터 모두 읽기",
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
                    text,
                    uploaded_file.name
                )
                new_events.append(event)
            else:
                event = empty_event_data(uploaded_file.name)
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
    st.subheader("📋 행사 정보 확인")

    for index, data in enumerate(st.session_state.events):
        source_name = data.get("source_name", f"행사 {index + 1}")

        with st.container(border=True):
            st.markdown(f"### {index + 1}. {source_name}")

            if data.get("ocr_error"):
                st.warning(data["ocr_error"])

            if data.get("needs_review"):
                st.warning("⚠️ OCR 결과 확인이 필요합니다.")
                for reason in data.get("review_reasons", []):
                    st.write(f"• {reason}")

            data["title"] = st.text_input(
                "행사명",
                value=data.get("title", ""),
                key=f"title_{index}"
            )

            candidates = data.get("date_candidates", [])

            if len(candidates) > 1:
                labels = [
                    f"{date} (후보 {i + 1})"
                    for i, date in enumerate(candidates)
                ]

                current = data.get("selected_date", candidates[0])
                current_index = (
                    candidates.index(current)
                    if current in candidates else 0
                )

                selected_index = st.selectbox(
                    "📅 행사 날짜 선택",
                    range(len(candidates)),
                    index=current_index,
                    format_func=lambda x: labels[x],
                    key=f"date_select_{index}"
                )

                data["selected_date"] = candidates[selected_index]
                data["date"] = candidates[selected_index]

                st.info(
                    "포스터에서 여러 날짜가 발견되었습니다. "
                    "캘린더에 넣을 행사 날짜를 선택해주세요."
                )

            elif len(candidates) == 1:
                data["date"] = st.text_input(
                    "행사 날짜",
                    value=data.get("date", ""),
                    placeholder="2026-10-12",
                    key=f"date_{index}"
                )
            else:
                data["date"] = st.text_input(
                    "행사 날짜",
                    value=data.get("date", ""),
                    placeholder="2026-10-12",
                    key=f"date_manual_{index}"
                )

            data["deadline"] = st.text_input(
                "📝 신청 마감일",
                value=data.get("deadline", ""),
                placeholder="2026-10-05",
                key=f"deadline_{index}"
            )

            if data.get("deadline"):
                st.caption(
                    f"신청 마감일: {data['deadline']} "
                    "※ 캘린더 행사 날짜와 별도로 관리됩니다."
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

            col1, col2 = st.columns(2)

            with col1:
                data["end_date"] = st.text_input(
                    "종료 날짜",
                    value=data.get("end_date", "") or data.get("date", ""),
                    placeholder="2026-10-12",
                    key=f"end_date_{index}"
                )

            with col2:
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

            data["description"] = st.text_area(
                "설명",
                value=data.get("description", ""),
                height=120,
                key=f"description_{index}"
            )

            if data.get("needs_review"):
                data["confirmed"] = st.checkbox(
                    "⚠️ OCR 결과와 수정한 정보를 확인했습니다.",
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
                    "같은 행사 날짜·장소로 다시 추가할 수 없습니다."
                )
                continue

            if data.get("needs_review") and not data.get("confirmed"):
                st.info(
                    "정보를 확인했다고 체크하면 "
                    "캘린더 추가 기능을 사용할 수 있습니다."
                )
                continue

            if not data.get("date"):
                st.warning("행사 날짜를 입력해주세요.")
                continue

            calendar_url = make_google_calendar_url(data)
            ics = make_ics(data)

            if calendar_url:
                st.link_button(
                    "🗓️ Google Calendar에 추가",
                    calendar_url,
                    use_container_width=True
                )

            if ics:
                st.download_button(
                    "📥 .ics 파일 다운로드",
                    data=ics,
                    file_name=f"event_{index + 1}.ics",
                    mime="text/calendar",
                    use_container_width=True,
                    key=f"ics_{index}"
                )

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

            with st.expander("📄 OCR 원문 보기"):
                st.text(data.get("ocr_text", ""))


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
    "Poster Calendar · 여러 포스터 · 날짜 선택 · 마감일 구분 · OCR 확인 · 중복 방지"
)
