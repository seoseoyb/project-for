
import streamlit as st
from PIL import Image
import urllib.request, urllib.parse, json, io, re
from datetime import datetime
st.set_page_config(page_title="행사 포스터 일정 자동 등록", page_icon="📅", layout="wide")
st.markdown('<style>.stApp{background:#f8f4ff;color:#51485d}.stButton button{border-radius:12px}h1,h2,h3{color:#55466f}</style>', unsafe_allow_html=True)
st.title("📅 행사 포스터 일정 자동 등록")
st.caption("포스터의 행사 날짜와 신청 마감일을 구분해 확인하고 캘린더 파일로 저장하세요.")
def read_poster(img):
    key = st.secrets.get("OCR_API_KEY", "")
    if not key:
        return "", "Streamlit Secrets에 OCR_API_KEY가 설정되지 않았어요."
    try:
        img = img.convert("RGB")
        if img.width > 1800:
            img = img.resize((1800, int(img.height * 1800 / img.width)))
        buf = io.BytesIO(); img.save(buf, format="JPEG", quality=90)
        boundary = "----PosterBoundary"
        fields = [("language", "kor"), ("OCREngine", "3"), ("scale", "true")]
        body = b""
        for name, value in fields:
            body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n").encode()
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"poster.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() + buf.getvalue() + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request("https://api.ocr.space/parse/image", data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}"); req.add_header("apikey", key)
        with urllib.request.urlopen(req, timeout=45) as r: data = json.loads(r.read().decode("utf-8"))
        results = data.get("ParsedResults", [])
        text = "\n".join(x.get("ParsedText", "") for x in results).strip()
        return (text, "") if text else ("", "포스터에서 글자를 찾지 못했어요.")
    except Exception as e:
        return "", f"글자 인식 실패: {e}"
def find_dates(text):
    found = []
    patterns = [re.compile(r"(?<!\d)(20\d{2})\s*[./년-]\s*(\d{1,2})\s*[./월-]\s*(\d{1,2})\s*일?"), re.compile(r"(?<!\d)(\d{1,2})\s*월\s*(\d{1,2})\s*일"), re.compile(r"(?<!\d)(\d{1,2})\s*[./-]\s*(\d{1,2})(?!\d)")]
    for line in text.splitlines():
        compact = re.sub(r"\s+", "", line)
        deadline_label = any(x in compact for x in ("신청마감", "접수마감", "모집마감", "마감일", "신청기간", "접수기간", "접수종료"))
        for p in patterns:
            for m in p.finditer(line):
                g = m.groups()
                try:
                    if len(g) == 3 and g[0].startswith("20"): y, mo, d = map(int, g)
                    else: y, mo, d = datetime.now().year, int(g[0]), int(g[1])
                    date = datetime(y, mo, d).strftime("%Y-%m-%d")
                    is_deadline = deadline_label or ("마감" in line and abs(m.start()-line.find("마감")) < 16)
                    found.append((date, is_deadline, line.strip()))
                except ValueError: pass
    unique = []
    for item in found:
        if item not in unique: unique.append(item)
    return unique
def make_ics(title, date, start, end, place, desc):
    day = date.replace("-", "")
    def clock(v):
        try: return datetime.strptime(v, "%H:%M").strftime("%H%M%S")
        except Exception: return "100000"
    start_dt = day + "T" + clock(start); end_dt = day + "T" + clock(end)
    esc = lambda s: str(s).replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
    return "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Poster Calendar//KO", "BEGIN:VEVENT", "DTSTART:"+start_dt, "DTEND:"+end_dt, "SUMMARY:"+esc(title), "LOCATION:"+esc(place), "DESCRIPTION:"+esc(desc), "END:VEVENT", "END:VCALENDAR"])
uploads = st.file_uploader("행사 포스터 이미지 선택 (여러 장 가능)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
if uploads:
    if st.button("🔎 포스터 정보 읽기", type="primary"):
        st.session_state.results = []
        for file in uploads:
            with st.spinner(f"{file.name} 읽는 중..."):
                text, error = read_poster(Image.open(file))
            st.session_state.results.append({"name": file.name, "image": file.getvalue(), "text": text, "error": error})
if st.session_state.get("results"):
    for i, item in enumerate(st.session_state.results):
        st.divider(); st.subheader(f"포스터 {i+1}: {item['name']}")
        left, right = st.columns([1, 1.5])
        with left: st.image(item["image"], use_container_width=True)
        with right:
            if item["error"]: st.warning(item["error"])
            text = st.text_area("인식한 포스터 글자 (필요하면 수정)", item["text"], height=150, key=f"text_{i}")
            dates = find_dates(text); event_dates = list(dict.fromkeys(x[0] for x in dates if not x[1])); deadlines = list(dict.fromkeys(x[0] for x in dates if x[1]))
            title_guess = next((line.strip() for line in text.splitlines() if line.strip() and not re.search(r"20\d{2}|\d{1,2}\s*월\s*\d{1,2}\s*일|마감|접수|신청", line)), "행사명 확인 필요")
            title = st.text_input("행사명", title_guess, key=f"title_{i}")
            if event_dates: date = st.selectbox("행사 날짜", event_dates, key=f"date_{i}")
            else: date = st.text_input("행사 날짜 (YYYY-MM-DD)", "", key=f"date_manual_{i}")
            deadline = st.selectbox("신청 마감일", ["인식되지 않음"] + deadlines, key=f"deadline_{i}")
            if deadline == "인식되지 않음": st.caption("마감일은 포스터에 명시된 경우에만 표시돼요.")
            a, b = st.columns(2)
            with a: start = st.text_input("시작 시간", "10:00", key=f"start_{i}")
            with b: end = st.text_input("종료 시간", "18:00", key=f"end_{i}")
            place = st.text_input("장소", "", key=f"place_{i}")
            desc = st.text_area("추가 내용 (선택)", "", key=f"desc_{i}")
            try:
                if date and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                    st.download_button("📅 캘린더 일정 파일 다운로드", make_ics(title, date, start, end, place, desc), file_name=f"event_{i+1}.ics", mime="text/calendar", key=f"ics_{i}")
                elif date: st.info("날짜를 YYYY-MM-DD 형식으로 입력해 주세요.")
            except Exception as e: st.error(f"일정 파일 생성 오류: {e}")

