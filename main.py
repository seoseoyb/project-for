import base64
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import streamlit as st
from openai import OpenAI


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="행사 포스터 → 캘린더",
    page_icon="📅",
    layout="wide",
)

KST = ZoneInfo("Asia/Seoul")


# =========================================================
# 함수
# =========================================================

def image_to_data_url(uploaded_file):
    """업로드된 이미지를 Base64 Data URL로 변환"""
    image_bytes = uploaded_file.getvalue()
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    mime_type = uploaded_file.type or "image/jpeg"

    return f"data:{mime_type};base64,{encoded}"


def extract_event_from_image(uploaded_file):
    """AI를 이용해서 포스터에서 행사 정보를 추출"""

    client = OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )

    image_url = image_to_data_url(uploaded_file)

    prompt = """
너는 행사 포스터를 분석해서 캘린더에 넣을 정보를 추출하는 AI다.

포스터 이미지를 자세하게 읽고 아래 JSON 형식으로만 답변해라.

중요한 규칙:

1. 포스터에 실제로 적혀 있는 정보만 사용한다.
2. 모르는 정보는 추측하지 말고 빈 문자열로 둔다.
3. 신청 기간과 행사 날짜를 혼동하지 않는다.
4. 행사 날짜가 여러 날이면 시작 날짜와 종료 날짜을 각각 넣는다.
5. 시간은 24시간 형식 HH:MM으로 작성한다.
6. 장소는 건물명, 행사장, 층, 주소 등이 보이면 최대한 자세하게 적는다.
7. 행사 설명은 포스터 내용을 바탕으로 2~4문장 정도로 요약한다.
8. 포스터에 신청 URL이 명확하게 보이는 경우에만 registration_url에 넣는다.
9. 읽기 어려운 부분이나 애매한 부분은 uncertainty 배열에 적는다.

반드시 아래 JSON 구조를 지켜라.

{
    "title": "",
    "event_date": "",
    "end_date": "",
    "start_time": "",
    "end_time": "",
    "location": "",
    "organizer": "",
    "fee": "",
    "description": "",
    "registration_url": "",
    "uncertainty": []
}

날짜:
YYYY-MM-DD

시간:
HH:MM

예:
{
    "title": "2026 서울 AI 컨퍼런스",
    "event_date": "2026-10-15",
    "end_date": "2026-10-15",
    "start_time": "14:00",
    "end_time": "17:00",
    "location": "코엑스 컨퍼런스룸 3층",
    "organizer": "OO대학교",
    "fee": "무료",
    "description": "생성형 AI의 미래와 산업 활용 사례를 다루는 컨퍼런스입니다.",
    "registration_url": "https://example.com",
    "uncertainty": []
}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                    {
                        "type": "input_image",
                        "image_url": image_url,
                        "detail": "high",
                    },
                ],
            }
        ],
    )

    result = response.output_text.strip()

    # ```json 제거
    result = re.sub(
        r"^```json\s*",
        "",
        result,
        flags=re.IGNORECASE,
    )

    result = re.sub(
        r"\s*```$",
        "",
        result,
    )

    return json.loads(result)


def parse_datetime(date_string, time_string=None):
    """문자열을 datetime으로 변환"""

    if not date_string:
        return None

    if time_string:
        dt = datetime.strptime(
            f"{date_string} {time_string}",
            "%Y-%m-%d %H:%M",
        )
    else:
        dt = datetime.strptime(
            date_string,
            "%Y-%m-%d",
        )

    return dt.replace(tzinfo=KST)


def build_description(event):
    """캘린더 설명 생성"""

    description = []

    if event.get("description"):
        description.append(
            event["description"]
        )

    if event.get("organizer"):
        description.append(
            f"주최/주관: {event['organizer']}"
        )

    if event.get("fee"):
        description.append(
            f"참가비: {event['fee']}"
        )

    if event.get("registration_url"):
        description.append(
            f"신청 링크: {event['registration_url']}"
        )

    return "\n".join(description)


def create_google_calendar_url(event):
    """Google Calendar 일정 생성 URL"""

    title = event.get("title", "")
    location = event.get("location", "")
    description = build_description(event)

    event_date = event.get("event_date")
    end_date = event.get("end_date") or event_date

    start_time = event.get("start_time")
    end_time = event.get("end_time")

    # 시간이 없는 경우 → 종일 일정
    if not start_time:

        start = datetime.strptime(
            event_date,
            "%Y-%m-%d",
        )

        end = datetime.strptime(
            end_date,
            "%Y-%m-%d",
        ) + timedelta(days=1)

        dates = (
            start.strftime("%Y%m%d")
            + "/"
            + end.strftime("%Y%m%d")
        )

    else:

        start = parse_datetime(
            event_date,
            start_time,
        )

        end = parse_datetime(
            end_date,
            end_time or start_time,
        )

        dates = (
            start.strftime("%Y%m%dT%H%M%S")
            + "/"
            + end.strftime("%Y%m%dT%H%M%S")
        )

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": dates,
        "ctz": "Asia/Seoul",
        "location": location,
        "details": description,
    }

    return (
        "https://calendar.google.com/calendar/render?"
        + urlencode(params)
    )


def escape_ics(value):
    """ICS 문자열 escape"""

    return (
        str(value or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
        .replace("\r", "")
    )


def create_ics(event):
    """Apple Calendar / Outlook 등에 사용할 ICS 생성"""

    title = escape_ics(
        event.get("title")
    )

    location = escape_ics(
        event.get("location")
    )

    description = escape_ics(
        build_description(event)
    )

    uid = (
        datetime.now()
        .strftime("%Y%m%d%H%M%S")
        + "@event-calendar"
    )

    event_date = event.get("event_date")
    end_date = event.get("end_date") or event_date

    start_time = event.get("start_time")
    end_time = event.get("end_time")

    # 종일 일정
    if not start_time:

        start = datetime.strptime(
            event_date,
            "%Y-%m-%d",
        )

        end = (
            datetime.strptime(
                end_date,
                "%Y-%m-%d",
            )
            + timedelta(days=1)
        )

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Event Poster Calendar//KR",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{datetime.now(KST).strftime('%Y%m%dT%H%M%S')}",
            f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
            f"SUMMARY:{title}",
            f"LOCATION:{location}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
            "END:VCALENDAR",
        ]

    # 시간 있는 일정
    else:

        start = parse_datetime(
            event_date,
            start_time,
        )

        end = parse_datetime(
            end_date,
            end_time or start_time,
        )

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Event Poster Calendar//KR",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{datetime.now(KST).strftime('%Y%m%dT%H%M%S')}",
            f"DTSTART;TZID=Asia/Seoul:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND;TZID=Asia/Seoul:{end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{title}",
            f"LOCATION:{location}",
            f"DESCRIPTION:{description}",
            "END:VEVENT",
            "END:VCALENDAR",
        ]

    return (
        "\r\n".join(lines) + "\r\n"
    ).encode("utf-8")


# =========================================================
# 화면
# =========================================================

st.title("📅 행사 포스터 → 캘린더")

st.markdown(
    """
### 포스터 한 장으로 행사 일정을 만들어보세요.

행사 포스터를 업로드하면 AI가

**행사명 · 날짜 · 시간 · 장소 · 주최 · 참가비 · 행사내용 · 신청링크**

를 자동으로 찾아줍니다.
"""
)


# =========================================================
# 사이드바
# =========================================================

with st.sidebar:

    st.header("⚙️ 설정")

    st.markdown(
        """
### 사용 방법

**1.** 행사 포스터 업로드

**2.** AI 정보 추출

**3.** 결과 확인 및 수정

**4.** 캘린더 추가
"""
    )

    st.divider()

    st.caption(
        "AI가 읽은 정보는 반드시 확인한 후 "
        "캘린더에 등록하세요."
    )


# =========================================================
# 업로드
# =========================================================

uploaded_file = st.file_uploader(
    "📸 행사 포스터를 업로드하세요",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp",
    ],
)


# session state
if "event" not in st.session_state:
    st.session_state.event = None


# =========================================================
# 포스터 표시
# =========================================================

if uploaded_file:

    st.divider()

    col1, col2 = st.columns(
        [1, 1]
    )

    with col1:

        st.subheader("🖼️ 포스터")

        st.image(
            uploaded_file,
            use_container_width=True,
        )

    with col2:

        st.subheader("🤖 AI 분석")

        if st.button(
            "✨ 행사 정보 추출하기",
            type="primary",
            use_container_width=True,
        ):

            if "OPENAI_API_KEY" not in st.secrets:

                st.error(
                    "OPENAI_API_KEY가 설정되어 있지 않습니다."
                )

            else:

                with st.spinner(
                    "포스터를 분석하고 있습니다..."
                ):

                    try:

                        event = (
                            extract_event_from_image(
                                uploaded_file
                            )
                        )

                        st.session_state.event = event

                        st.success(
                            "행사 정보를 추출했습니다!"
                        )

                    except json.JSONDecodeError:

                        st.error(
                            "AI 응답을 읽지 못했습니다. "
                            "다시 시도해주세요."
                        )

                    except Exception as e:

                        st.error(
                            f"오류가 발생했습니다: {e}"
                        )


# =========================================================
# 행사 정보
# =========================================================

if st.session_state.event:

    event = st.session_state.event

    st.divider()

    st.subheader("📝 행사 정보")

    st.caption(
        "AI가 추출한 정보입니다. "
        "틀린 내용이 있다면 직접 수정하세요."
    )

    col1, col2 = st.columns(2)

    with col1:

        event["title"] = st.text_input(
            "행사명",
            value=event.get("title", ""),
        )

        event["event_date"] = st.text_input(
            "행사 날짜",
            value=event.get(
                "event_date",
                "",
            ),
            placeholder="2026-10-15",
        )

        event["start_time"] = st.text_input(
            "시작 시간",
            value=event.get(
                "start_time",
                "",
            ),
            placeholder="14:00",
        )

        event["location"] = st.text_input(
            "📍 장소",
            value=event.get(
                "location",
                "",
            ),
        )

        event["organizer"] = st.text_input(
            "주최 / 주관",
            value=event.get(
                "organizer",
                "",
            ),
        )

    with col2:

        event["end_date"] = st.text_input(
            "종료 날짜",
            value=event.get(
                "end_date",
                "",
            ),
            placeholder="2026-10-15",
        )

        event["end_time"] = st.text_input(
            "종료 시간",
            value=event.get(
                "end_time",
                "",
            ),
            placeholder="17:00",
        )

        event["fee"] = st.text_input(
            "💰 참가비",
            value=event.get(
                "fee",
                "",
            ),
        )

        event["registration_url"] = st.text_input(
            "🔗 신청 링크",
            value=event.get(
                "registration_url",
                "",
            ),
        )

    event["description"] = st.text_area(
        "📖 행사 내용",
        value=event.get(
            "description",
            "",
        ),
        height=160,
    )


    # =====================================================
    # AI 불확실성
    # =====================================================

    uncertainty = event.get(
        "uncertainty",
        [],
    )

    if uncertainty:

        with st.expander(
            "⚠️ AI가 확신하지 못한 부분"
        ):

            for item in uncertainty:

                st.write(
                    f"• {item}"
                )


    # =====================================================
    # 캘린더
    # =====================================================

    st.divider()

    st.subheader(
        "📆 캘린더에 추가"
    )

    try:

        google_url = (
            create_google_calendar_url(
                event
            )
        )

        ics_data = create_ics(
            event
        )

        col1, col2 = st.columns(2)

        with col1:

            st.link_button(
                "🗓️ Google Calendar에 추가",
                google_url,
                use_container_width=True,
            )

        with col2:

            safe_filename = re.sub(
                r'[\\/:*?"<>|]+',
                "_",
                event.get(
                    "title",
                    "event",
                ),
            )

            st.download_button(
                "⬇️ .ics 파일 다운로드",
                data=ics_data,
                file_name=f"{safe_filename}.ics",
                mime="text/calendar",
                use_container_width=True,
            )

    except Exception as e:

        st.error(
            f"캘린더 생성 오류: {e}"
        )


# =========================================================
# 아무것도 없을 때
# =========================================================

else:

    st.info(
        "👆 위에서 행사 포스터를 업로드해보세요."
    )
