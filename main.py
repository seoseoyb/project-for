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
