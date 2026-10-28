
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

            # 5일 이상 이어지는 장기 행사는 기간 전체를 자동 등록하지 않도록 합니다.
            # 사용자가 실제로 참여할 날짜를 캘린더 앱에서 직접 골라 등록하게 안내합니다.
            long_event = False
            try:
                start_dt = datetime.strptime(str(data.get("date", "")).strip()[:10], "%Y-%m-%d")
                end_value = str(data.get("end_date", "")).strip() or str(data.get("date", "")).strip()
                end_dt = datetime.strptime(end_value[:10], "%Y-%m-%d")
                if end_dt >= start_dt:
                    long_event = (end_dt - start_dt).days + 1 >= 5
            except (ValueError, TypeError):
                long_event = False

            blocked = data.get("needs_review") and not data.get("confirmed")

            if long_event:
                st.info(
                    "📅 장기 행사예요. 참여할 날짜를 Google Calendar에서 직접 선택해 주세요.\n\n"
                    f"행사 기간: {data.get('date', '')} ~ {data.get('end_date', '')}"
                )

            # 장기 행사 여부와 관계없이 캘린더 추가 버튼은 항상 표시합니다.
            calendar_url = make_google_calendar_url(data)
            ics = make_ics(data)

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
                use_container_width=True,
                disabled=blocked
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
