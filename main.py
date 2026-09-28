import streamlit as st
import base64
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from urllib.parse import urlencode


# =========================================================
# 페이지 설정
# =========================================================

st.set_page_config(
    page_title="행사 포스터 캘린더",
    page_icon="📅",
    layout="wide",
)


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 5px;
}

.subtitle {
    font-size: 18px;
    color: #666;
    margin-bottom: 30px;
}

.event-card {
    padding: 25px;
    border-radius: 15px;
    border: 1px solid #ddd;
    margin-top: 20px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# OpenAI API 호출
# =========================================================

def analyze_image(image_file):

    # API KEY 가져오기
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        st.error(
            "OPENAI_API_KEY가 설정되어 있지 않습니다."
        )
        st.info(
            "Streamlit Cloud → Settings → Secrets에서 "
            "OPENAI_API_KEY를 추가해주세요."
        )
        return None

    # 이미지 → Base64
    image_bytes = image_file.getvalue()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    mime_type = image_file.type or "image/jpeg"

    image_data_url = (
        f"data:{mime_type};base64,{base64_image}"
    )

    # AI에게 전달할 프롬프트
    prompt = """
이 이미지는 행사 포스터다.

포스터를 자세하게 읽고 행사 정보를 추출해줘.

반드시 JSON 하나만 반환해.
마크다운이나 설명을 추가하지 마.

다음 형식을 정확하게 사용해:

{
  "title": "",
  "date": "",
  "end_date": "",
  "start_time": "",
  "end_time": "",
  "location": "",
  "organizer": "",
  "fee": "",
  "description": "",
  "url": "",
  "uncertainty": []
}

규칙:

- title: 행사 이름
- date: 실제 행사 시작 날짜
- end_date: 행사 종료 날짜. 하루 행사라면 date와 같은 날짜
- start_time: 시작 시간
- end_time: 종료 시간
- location: 행사 장소
- organizer: 주최 또는 주관
- fee: 참가비
- description: 행사 내용을 2~4문장으로 요약
- url: 포스터에 표시된 신청 URL
- uncertainty: 읽기 어렵거나 확실하지 않은 정보

날짜는 반드시 YYYY-MM-DD 형식.

시간은 반드시 HH:MM 형식.

예를 들어 포스터에

2026년 10월 15일
14:00 ~ 17:00
코엑스 컨퍼런스룸

이라고 되어 있다면:

{
  "title": "행사 이름",
  "date": "2026-10-15",
  "end_date": "2026-10-15",
  "start_time": "14:00",
  "end_time": "17:00",
  "location": "코엑스 컨퍼런스룸",
  ...
}

중요:
신청기간과 행사 날짜를 혼동하지 마.
포스터에 없는 정보는 추측하지 마.
"""


    # OpenAI API 요청
    request_body = {
        "model": "gpt-4.1-mini",
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                    {
                        "type": "input_image",
                        "image_url": image_data_url,
                    },
                ],
            }
        ],
    }

    data = json.dumps(
        request_body
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=120,
        ) as response:

            response_data = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as e:

        error_body = e.read().decode(
            "utf-8",
            errors="ignore",
        )

        st.error(
            f"OpenAI API 오류 ({e.code})"
        )

        st.code(error_body)

        return None

    except Exception as e:

        st.error(
            f"API 연결 오류: {str(e)}"
        )

        return None


    # AI 결과 가져오기
    try:

        output_text = response_data["output"][0]["content"][0]["text"]

    except Exception:

        # Responses API 응답 구조가 다를 경우
        output_text = ""

        for output in response_data.get(
            "output",
            [],
        ):

            for content in output.get(
                "content",
                [],
            ):

                if content.get("type") == "output_text":

                    output_text += content.get(
                        "text",
                        "",
                    )


    if not output_text:

        st.error(
            "AI가 결과를 반환하지 않았습니다."
        )

        st.json(response_data)

        return None


    # ```json 제거
    output_text = re.sub(
        r"```json",
        "",
        output_text,
        flags=re.IGNORECASE,
    )

    output_text = re.sub(
        r"```",
        "",
        output_text,
    )

    output_text = output_text.strip()


    # JSON 변환
    try:

        result = json.loads(
            output_text
        )

        return result

    except Exception:

        # JSON 앞뒤에 이상한 텍스트가 붙은 경우
        match = re.search(
            r"\{.*\}",
            output_text,
            re.DOTALL,
        )

        if match:

            try:

                return json.loads(
                    match.group()
                )

            except Exception:
                pass


        st.error(
            "AI 결과를 JSON으로 변환하지 못했습니다."
        )

        st.code(
            output_text
        )

        return None


# =========================================================
# Google Calendar URL
# =========================================================

def create_google_calendar_url(event):

    title = event.get(
        "title",
        "",
    )

    location = event.get(
        "location",
        "",
    )

    description = event.get(
        "description",
        "",
    )

    date = event.get(
        "date",
        "",
    )

    end_date = (
        event.get("end_date")
        or date
    )

    start_time = event.get(
        "start_time",
        "",
    )

    end_time = event.get(
        "end_time",
        "",
    )


    # 날짜가 없는 경우
    if not date:

        return None


    # 시간 없는 종일 행사
    if not start_time:

        start = datetime.strptime(
            date,
            "%Y-%m-%d",
        )

        end = (
            datetime.strptime(
                end_date,
                "%Y-%m-%d",
            )
            + timedelta(days=1)
        )

        dates = (
            start.strftime("%Y%m%d")
            + "/"
            + end.strftime("%Y%m%d")
        )

    else:

        start = datetime.strptime(
            f"{date} {start_time}",
            "%Y-%m-%d %H:%M",
        )

        if end_time:

            end = datetime.strptime(
                f"{end_date} {end_time}",
                "%Y-%m-%d %H:%M",
            )

        else:

            end = start + timedelta(
                hours=1
            )


        dates = (
            start.strftime(
                "%Y%m%dT%H%M%S"
            )
            + "/"
            + end.strftime(
                "%Y%m%dT%H%M%S"
            )
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


# =========================================================
# ICS 파일
# =========================================================

def escape_ics(value):

    return (
        str(value or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def create_ics(event):

    title = escape_ics(
        event.get("title")
    )

    location = escape_ics(
        event.get("location")
    )

    description = escape_ics(
        event.get("description")
    )

    date = event.get(
        "date"
    )

    end_date = (
        event.get("end_date")
        or date
    )

    start_time = event.get(
        "start_time"
    )

    end_time = event.get(
        "end_time"
    )


    # 종일 일정
    if not start_time:

        start = datetime.strptime(
            date,
            "%Y-%m-%d",
        )

        end = (
            datetime.strptime(
                end_date,
                "%Y-%m-%d",
            )
            + timedelta(days=1)
        )

        content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Event Poster Calendar//KR
BEGIN:VEVENT
UID:{datetime.now().timestamp()}@eventposter
DTSTART;VALUE=DATE:{start.strftime("%Y%m%d")}
DTEND;VALUE=DATE:{end.strftime("%Y%m%d")}
SUMMARY:{title}
LOCATION:{location}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR
"""

    else:

        start = datetime.strptime(
            f"{date} {start_time}",
            "%Y-%m-%d %H:%M",
        )

        if end_time:

            end = datetime.strptime(
                f"{end_date} {end_time}",
                "%Y-%m-%d %H:%M",
            )

        else:

            end = start + timedelta(
                hours=1
            )


        content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Event Poster Calendar//KR
BEGIN:VEVENT
UID:{datetime.now().timestamp()}@eventposter
DTSTART;TZID=Asia/Seoul:{start.strftime("%Y%m%dT%H%M%S")}
DTEND;TZID=Asia/Seoul:{end.strftime("%Y%m%dT%H%M%S")}
SUMMARY:{title}
LOCATION:{location}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR
"""


    return content.encode(
        "utf-8"
    )


# =========================================================
# 제목
# =========================================================

st.markdown(
    '<div class="main-title">📅 행사 포스터 → 캘린더</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    '포스터를 올리면 AI가 행사 정보를 자동으로 정리해드립니다.'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# 사용 방법
# =========================================================

with st.expander(
    "💡 어떻게 사용하나요?"
):

    st.write(
        """
        **① 포스터 업로드**

        행사 포스터 이미지를 올립니다.

        **② AI 분석**

        행사명, 날짜, 시간, 장소 등을 자동으로 추출합니다.

        **③ 정보 확인**

        AI가 잘못 읽은 내용은 직접 수정할 수 있습니다.

        **④ 캘린더 추가**

        Google Calendar 또는 `.ics` 파일로 추가합니다.
        """
    )


# =========================================================
# 파일 업로드
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


# =========================================================
# Session
# =========================================================

if "event" not in st.session_state:

    st.session_state.event = None


# =========================================================
# 업로드 후
# =========================================================

if uploaded_file:

    st.divider()

    left, right = st.columns(
        2
    )


    # -----------------------------------------------------
    # 이미지
    # -----------------------------------------------------

    with left:

        st.subheader(
            "🖼️ 포스터"
        )

        st.image(
            uploaded_file,
            use_container_width=True,
        )


    # -----------------------------------------------------
    # 분석
    # -----------------------------------------------------

    with right:

        st.subheader(
            "🤖 AI 분석"
        )

        st.write(
            "포스터에서 행사 정보를 찾아냅니다."
        )


        if st.button(
            "✨ 행사 정보 추출하기",
            type="primary",
            use_container_width=True,
        ):

            with st.spinner(
                "포스터를 분석하고 있습니다..."
            ):

                result = analyze_image(
                    uploaded_file
                )


            if result:

                st.session_state.event = result

                st.success(
                    "행사 정보를 추출했습니다!"
                )


# =========================================================
# 결과
# =========================================================

if st.session_state.event:

    event = st.session_state.event


    st.divider()

    st.subheader(
        "📋 행사 정보 확인"
    )

    st.caption(
        "AI가 추출한 내용입니다. "
        "필요하면 직접 수정해주세요."
    )


    # -----------------------------------------------------
    # 행사명
    # -----------------------------------------------------

    event["title"] = st.text_input(
        "행사명",
        value=event.get(
            "title",
            "",
        ),
    )


    # -----------------------------------------------------
    # 날짜 / 시간
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(
        4
    )


    with col1:

        event["date"] = st.text_input(
            "📅 시작 날짜",
            value=event.get(
                "date",
                "",
            ),
            placeholder="2026-10-15",
        )


    with col2:

        event["end_date"] = st.text_input(
            "📅 종료 날짜",
            value=event.get(
                "end_date",
                "",
            ),
            placeholder="2026-10-15",
        )


    with col3:

        event["start_time"] = st.text_input(
            "🕐 시작 시간",
            value=event.get(
                "start_time",
                "",
            ),
            placeholder="14:00",
        )


    with col4:

        event["end_time"] = st.text_input(
            "🕐 종료 시간",
            value=event.get(
                "end_time",
                "",
            ),
            placeholder="17:00",
        )


    # -----------------------------------------------------
    # 장소
    # -----------------------------------------------------

    event["location"] = st.text_input(
        "📍 장소",
        value=event.get(
            "location",
            "",
        ),
    )


    # -----------------------------------------------------
    # 주최 / 참가비
    # -----------------------------------------------------

    col1, col2 = st.columns(
        2
    )


    with col1:

        event["organizer"] = st.text_input(
            "🏢 주최 / 주관",
            value=event.get(
                "organizer",
                "",
            ),
        )


    with col2:

        event["fee"] = st.text_input(
            "💰 참가비",
            value=event.get(
                "fee",
                "",
            ),
        )


    # -----------------------------------------------------
    # 설명
    # -----------------------------------------------------

    event["description"] = st.text_area(
        "📝 행사 내용",
        value=event.get(
            "description",
            "",
        ),
        height=150,
    )


    # -----------------------------------------------------
    # 신청 링크
    # -----------------------------------------------------

    event["url"] = st.text_input(
        "🔗 신청 링크",
        value=event.get(
            "url",
            "",
        ),
    )


    # -----------------------------------------------------
    # 불확실한 정보
    # -----------------------------------------------------

    uncertainty = event.get(
        "uncertainty",
        [],
    )


    if uncertainty:

        with st.expander(
            "⚠️ AI가 확실하지 않은 부분"
        ):

            for item in uncertainty:

                st.write(
                    "• " + str(item)
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

        ics_file = create_ics(
            event
        )


        col1, col2 = st.columns(
            2
        )


        # Google
        with col1:

            if google_url:

                st.link_button(
                    "🗓️ Google Calendar에 추가",
                    google_url,
                    use_container_width=True,
                )

            else:

                st.warning(
                    "행사 날짜가 필요합니다."
                )


        # ICS
        with col2:

            filename = re.sub(
                r'[\\/:*?"<>|]',
                "_",
                event.get(
                    "title",
                    "event",
                ),
            )

            st.download_button(
                "⬇️ 캘린더 파일 다운로드",
                data=ics_file,
                file_name=f"{filename}.ics",
                mime="text/calendar",
                use_container_width=True,
            )


    except Exception as e:

        st.error(
            f"캘린더 생성 오류: {e}"
        )


# =========================================================
# Footer
# =========================================================

st.divider()

st.caption(
    "📅 Event Poster Calendar · AI 기반 행사 일정 정리"
)
