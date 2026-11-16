            if st.button(
                f"应用到「{category}」",
                key=f"apply_{category}",
                use_container_width=True
            ):

                set_category_knowledge(
                    category,
                    category_level
                )

                st.rerun()


            st.divider()


            for subject in subjects:

                level = (
                    st.selectbox(
                        subject,
                        LEVEL_OPTIONS,
                        key=(
                            f"knowledge_"
                            f"{category}_"
                            f"{subject}"
                        )
                    )
                )


                knowledge_profile[
                    category
                ][subject] = level


    # =====================================================
    # 用户自己的学习资料
    # =====================================================

    st.divider()

    st.header(
        "📂 我的学习资料"
    )


    st.caption(
        "可以上传自己的 PDF 学习资料。"
        "这些资料会作为 Global AI 官方课程资料的补充知识来源。"
    )


    st.info(
        "Global AI 课程资料优先，"
        "个人上传资料用于补充解释和学习。"
    )


    uploaded_files = (
        st.file_uploader(
            "上传 PDF 学习资料",
            type=["pdf"],
            accept_multiple_files=True,
            key="user_material_uploader"
        )
    )


    # =====================================================
    # 保存上传文件
    # =====================================================

    if uploaded_files:

        newly_added = []


        for uploaded_file in (
            uploaded_files
        ):

            # 防止目录路径注入
            safe_filename = (
                os.path.basename(
                    uploaded_file.name
                )
            )


            save_path = (
                os.path.join(
                    USER_MATERIAL_DIR,
                    safe_filename
                )
            )


            if not os.path.exists(
                save_path
            ):

                with open(
                    save_path,
                    "wb"
                ) as f:

                    f.write(
                        uploaded_file.getbuffer()
                    )


                newly_added.append(
                    safe_filename
                )


        if newly_added:

            for filename in newly_added:

                st.success(
                    f"已添加：{filename}"
                )


            st.caption(
                "新资料会在下一次 Tutor 检索时自动进入知识库。"
            )


    # =====================================================
    # 已上传文件
    # =====================================================

    existing_materials = [

        filename

        for filename
        in os.listdir(
            USER_MATERIAL_DIR
        )

        if filename.lower().endswith(
            ".pdf"
        )
    ]


    if existing_materials:

        with st.expander(
            f"📚 已添加的学习资料（{len(existing_materials)}）"
        ):

            for filename in sorted(
                existing_materials
            ):

                st.write(
                    f"📄 {filename}"
                )


    else:

        st.caption(
            "目前还没有添加个人学习资料。"
        )


    # =====================================================
    # 学习记录
    # =====================================================

    st.divider()

    st.header(
        "📖 学习记录"
    )


    all_records = (
        get_learning_records()
    )


    daily_records = (
        get_learning_records_by_date()
    )
