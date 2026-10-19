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
