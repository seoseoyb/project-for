

붙여넣은 텍스트 (1)(1).txt
문서
지금 내 깃허브에 이런데 뭐 행사명도 날짜도 시간도 다 확인 필요로 뜨네 왜이래

스크린샷 2026-10-02 103022.png
이렇게 떠

아 맞아. 이번에는 원인을 제대로 잡았어. 😭
특히 “시간이 날짜로 뜨는 문제”는 날짜 인식 쪽만 고쳐서는 해결이 안 되는 문제였어.

🛠️ 이번에 제대로 수정한 부분
1. 2026.10.30을 시간 10:30으로 읽어버리는 문제 수정

기존 시간 인식이 10.30을 시간으로 인식할 수 있었는데, 이게 2026.10.30 안에 포함되어 있어서:

2026.10.30 → 날짜이면서 동시에 10:30으로 인식

하는 문제가 생길 수 있었어.

이번에는 시간 인식에서 앞에 날짜 숫자가 붙어 있는 10.30은 시간으로 잡지 않도록 수정했어.

반면:

10.30 ~ 16.30

처럼 실제 시간 범위는 계속 인식하도록 했어.

2. 핵심 내용도 이제 단순히 축제만 나오지 않게 수정

예를 들어 포스터에

노래 / 가수 / 음악 / 밴드 + 페스티벌

같은 단어가 있으면

음악 페스티벌

로 표시되게 했어.

예를 들면:

음악 + 페스티벌 → 음악 페스티벌

음악 + 공연 → 음악 공연

가수 + 축제 → 음악 행사

공연 + 페스티벌 → 공연 페스티벌

전시 → 전시

체험 → 체험

스포츠 → 스포츠

마켓 → 마켓

강연 → 강연

대회 → 대회

그래서 이제 축제라는 단어 하나만 던지는 방식이 아니라 포스터 안에 실제로 어떤 키워드가 있는지 조합해서 보여주도록 바꿨어.

3. 읽어낸 포스터 글자 확인 / 정보 수정 글자 겹침도 수정

이건 전체 글꼴을 바꾸면서 Streamlit의 아이콘용 글꼴까지 고운돋움으로 덮어써버린 게 원인이었어.

그래서 이번에는:

일반 글씨 → 고운돋움

제목 → Jua

Streamlit 아이콘 → 아이콘 전용 폰트

로 분리했어.

그리고 두 영역의 높이와 내부 여백도 늘려서

🔎 읽어낸 포스터 글자 확인
✏️ 정보 수정 / 자세히 보기

가 아이콘이나 화살표와 겹치지 않도록 수정했어.

📅 날짜 2개 선택 기능도 그대로 유지
이건 건드리지 않았어.

날짜 후보가 여러 개면

📅 캘린더에 추가할 행사 날짜

에서 원하는 날짜를 선택하고, 선택한 날짜가 캘린더에 들어가는 구조 그대로야.

그리고 캘린더 기본 정보도 기존 요청대로:

제목 + 날짜 + 시간

중심으로 들어가고, 사용자가 정보 수정에서 바꾼 내용이 반영되도록 되어 있어.

문법 검사도 다시 통과했어.

수정된 main.py 다운로드

이번에는 특히 시간에 날짜가 뜨는 문제를 가장 먼저 확인해봐.
이 버전에서도 똑같이 뜬다면 그때는 코드 추측으로 계속 고치는 게 아니라, 앱의 🔎 읽어낸 포스터 글자 확인에 실제로 나온 OCR 결과를 기준으로 딱 어느 단계에서 잘못되는지 잡으면 돼.


main_updated.py
코드


아 그리고 글씨체 아까 동그란게 좋았는데 바꼈어ㅜㅜ 동그란거로 다시 바꿔줘 그리고 다이어리식 카드로 수정해줘 더 이쁘게! 뭔가 다이어리 노트 식으로.. 뭔말알? 알잘딱깔센 해줘ㅜㅜ

응응 뭔 말인지 알아 ㅋㅋㅋ 😭💜
이번엔 “보라색 배경에 카드 몇 개”가 아니라 아예 다이어리 노트 한 장을 펼쳐놓은 느낌으로 바꿨어.

📔 이번 디자인 방향
전체 글씨 → 동글동글한 Jua 폰트로 통일

제목만 둥근 게 아니라 안내문, 버튼, 정보, 입력창까지 전부 같은 느낌

행사 정보 카드 → 다이어리 종이

크림색 종이

실제 노트처럼 가로 줄무늬

왼쪽 바인더 구멍 느낌

위쪽에 마스킹테이프를 붙인 느낌

살짝 삐뚤어진 듯한 둥근 모서리

종이가 살짝 떠 있는 그림자

장소 / 주최·주관 / 신청 마감

그냥 텍스트로 나열하지 않고 작은 메모지처럼 표시

포스터 업로드 영역

점선 + 종이 느낌으로 변경

메인 제목

계속 화면 가운데 정렬

정보 수정 / 읽어낸 포스터 글자 확인

아이콘용 글꼴과 일반 글꼴을 분리해서 글자 겹침 방지

버튼 높이와 여백도 늘림

특히 이번에는 stApp의 모든 span에 무작정 폰트를 덮어씌우는 방식은 피했어. 그게 Streamlit의 화살표/아이콘까지 일반 글씨로 바뀌어서 겹치는 문제를 만들 수 있었거든.

그리고 수정한 파일은 실제로 저장하고 Python 문법 검사도 통과했어.

📥 새 버전
다이어리 디자인으로 수정된 main.py

이번 버전은 느낌으로 말하면
“행사 정보를 자동으로 적어주는 귀여운 디지털 다이어리” 컨셉이야. 📔✨


main_updated.py
코드


아 여전히 정보수정 쪽에서 겹쳐서 나와ㅜㅜ 아아까 너가 수정했을 땐 안이랬는데 다시 이러네 안이러도록 해줘 그리고 글씨체 동글동글 너무 좋아 근데 제목이 아닌 부분 글씨체는 동글동글은 유지하되 조금 얇게 해줘 그리고 페스티벌 이름에서 작게 소제목이나 부가설명처럼 있는거는 앱에서 행사 제목 뜰 때에도 반영해서 좀 작게 떴으면 좋겠어 아예 다 크게 쓰는게 아니라!

응응 이번엔 세 가지를 같이 손봤어 🥹💜

「정보 수정 / 자세히 보기」 겹침 문제

글씨 영역과 펼침 화살표 영역을 아예 분리해서 배치했어.

글씨가 화살표 위로 침범하지 않도록 수정했고, 긴 문구는 자동으로 말줄임 처리되게 했어.

OCR 확인용 펼침 메뉴도 같은 방식으로 적용했어.

글씨체

제목/행사명 → 지금처럼 동글동글한 Jua

설명, 날짜, 장소, 입력창 등 일반 글씨 → Gowun Dodum으로 바꿔서 동글동글한 느낌은 유지하면서 조금 더 얇고 깔끔하게 했어.

그래서 전체적으로 제목만 톡 튀고 나머지는 덜 답답하게 보일 거야.

행사명 + 작은 부제

행사명이 메인 제목 - 부가 설명, 메인 제목 | 부가 설명, 메인 제목 · 부가 설명, (부제) 같은 형태로 인식되면

메인 행사명은 크게

부가 설명은 바로 아래 작게
나오도록 넣었어.

캘린더에 들어가는 행사명 자체는 기존 행사명으로 유지돼.

그리고 수정한 파일은 문법 검사까지 통과했어.

👉 수정된 main.py 다운로드

이번 버전은 네가 말한 “동글동글하지만 본문은 좀 얇게 + 행사명은 크게, 부제는 작게 + 정보수정 겹침 방지” 기준으로 맞춰놨어.


main_updated.py
코드


main_updated.py


1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
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
