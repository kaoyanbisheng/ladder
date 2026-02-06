import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="综评核查工具", page_icon="📝", layout="wide")

st.title("🎓 高中综评数据自动化核查工具 (v3.3)")

# Sidebar for instructions
with st.sidebar:
    st.header("📖 使用说明")
    st.info("""
    1. **上传文件**：支持含多个工作表的 Excel。
    2. **自动识别**：系统从工作表名称中提取【年级】和【班级】。
    3. **选择必填项**：在列表中勾选必须完成的项目。
    4. **开始核查**：
       - **验证规则**：单元格内容必须为 **“√”** 才算完成。
    5. **下载报告**：导出未完成学生名单（省学籍辅号为文本格式）。
    """)
    st.divider()
    st.caption("Version 3.3 | 班级多选模式")

# 1. File Upload
st.subheader("1. 数据上传与统计")
uploaded_file = st.file_uploader("请上传综评系统导出的 Excel 文件 (支持多 Sheet)", type=['xlsx', 'xls'])

if uploaded_file:
    try:
        # Read all sheets
        xls = pd.read_excel(uploaded_file, sheet_name=None, dtype={'省学籍辅号': str})
        
        all_data_frames = []
        valid_sheets_count = 0
        
        # Regex patterns
        grade_pattern = re.compile(r'(\d{4}级)')
        class_pattern = re.compile(r'(\d+班)')
        
        # 2. Merge Data & Parse Sheet Names
        for sheet_name, df in xls.items():
            # Check for unique identifier column to ensure it's a valid data sheet
            if '省学籍辅号' in df.columns:
                valid_sheets_count += 1
                
                # Extract Grade
                grade_match = grade_pattern.search(sheet_name)
                grade = grade_match.group(1) if grade_match else "未知年级"
                
                # Extract Class
                class_match = class_pattern.search(sheet_name)
                class_name = class_match.group(1) if class_match else "未知班级"
                
                # Add columns
                df['年级'] = grade
                df['班级'] = class_name
                df['_SourceSheet'] = sheet_name
                
                # Ensure 省学籍辅号 is string
                if '省学籍辅号' in df.columns:
                    df['省学籍辅号'] = df['省学籍辅号'].astype(str)
                
                all_data_frames.append(df)
        
        if not all_data_frames:
            st.error("❌ 未在文件中找到包含【省学籍辅号】列的有效数据表，请检查文件格式。")
        else:
            # Concatenate all valid sheets
            full_df = pd.concat(all_data_frames, ignore_index=True)
            
            # --- Statistics Display (Updated) ---
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            total_students = len(full_df)
            unique_grades = sorted(full_df['年级'].unique().tolist())
            unique_classes = full_df[['年级', '班级']].drop_duplicates()
            
            col_stat1.metric("总人数", f"{total_students} 人")
            col_stat2.metric("覆盖年级", f"{len(unique_grades)} 个")
            col_stat3.metric("覆盖班级", f"{len(unique_classes)} 个")
            
            with st.expander("📊 班级人数查询", expanded=True):
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    stat_grade = st.selectbox("选择年级查看", options=["全部"] + unique_grades)
                
                with c2:
                    if stat_grade != "全部":
                        classes_in_grade = sorted(full_df[full_df['年级'] == stat_grade]['班级'].unique().tolist())
                        stat_class = st.selectbox("选择班级查看", options=["全部"] + classes_in_grade)
                    else:
                        stat_class = st.selectbox("选择班级查看", options=["全部"], disabled=True)
                
                with c3:
                    # Calculate count
                    if stat_grade == "全部":
                        count = total_students
                        desc = "全校总人数"
                    elif stat_class == "全部":
                        count = len(full_df[full_df['年级'] == stat_grade])
                        desc = f"{stat_grade} 总人数"
                    else:
                        count = len(full_df[(full_df['年级'] == stat_grade) & (full_df['班级'] == stat_class)])
                        desc = f"{stat_grade} {stat_class} 人数"
                    
                    st.metric(desc, f"{count} 人")

            
            # 3. Filtering & Configuration
            st.divider()
            st.subheader("2. 筛选与必填项配置")
            
            col_filter, col_config = st.columns([1, 2])
            
            with col_filter:
                st.markdown("#### 📌 班级筛选")
                
                # Grade Selection (Radio)
                selected_grade = st.radio("第一步：选择年级", options=unique_grades, horizontal=True)
                
                # Class Selection (Multiselect)
                # Filter classes for the selected grade
                grade_classes = sorted(full_df[full_df['年级'] == selected_grade]['班级'].unique().tolist())
                
                # Format options as "2023级01班"
                formatted_options = [f"{selected_grade}{c}" for c in grade_classes]
                
                st.write("第二步：选择班级 (多选)")
                
                if formatted_options:
                    selected_formatted_classes = st.multiselect(
                        "勾选要核查的班级",
                        options=formatted_options,
                        default=formatted_options # Default select all
                    )
                    
                    # Parse selection back to class names
                    selected_classes = [s.replace(selected_grade, "") for s in selected_formatted_classes]
                    
                    filtered_df = full_df[
                        (full_df['年级'] == selected_grade) & 
                        (full_df['班级'].isin(selected_classes))
                    ]
                else:
                    st.warning("该年级下暂无班级数据")
                    filtered_df = pd.DataFrame()

                st.info(f"当前选中: **{len(filtered_df)}** 人")
            
            with col_config:
                st.markdown("#### ✅ 必填项配置")
                st.caption("请勾选需要核查的列：")
                
                # Exclude columns
                exclude_cols = ['省学籍辅号', '学生姓名', '基本信息', '任职情况', '奖惩情况', '年级', '班级', '_SourceSheet']
                candidate_cols = [c for c in full_df.columns if c not in exclude_cols]
                
                # Use DataEditor for Checkbox UI
                config_df = pd.DataFrame({
                    '是否必填': [False] * len(candidate_cols),
                    '列名': candidate_cols
                })
                
                edited_config = st.data_editor(
                    config_df,
                    column_config={
                        "是否必填": st.column_config.CheckboxColumn(
                            "勾选必填",
                            help="选中此项表示该列必须填写 '√'",
                            default=False,
                        ),
                        "列名": st.column_config.TextColumn(
                            "核查项目名称",
                            disabled=True
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=300
                )
                
                target_cols = edited_config[edited_config['是否必填']]['列名'].tolist()

            # 4. Processing
            st.divider()
            if st.button("🚀 开始核查", type="primary", use_container_width=True):
                if not target_cols:
                    st.warning("⚠️ 请至少在右侧列表勾选一项必填列！")
                else:
                    missing_data = []
                    progress_bar = st.progress(0)
                    total_rows = len(filtered_df)
                    
                    for index, (idx, row) in enumerate(filtered_df.iterrows()):
                        missing_items = []
                        for col in target_cols:
                            val = row[col]
                            if str(val).strip() != "√":
                                missing_items.append(col)
                        
                        if missing_items:
                            student_info = {
                                '省学籍辅号': str(row.get('省学籍辅号', '')), # Force string
                                '学生姓名': row.get('学生姓名', ''),
                                '年级': row.get('年级', ''),
                                '班级': row.get('班级', ''),
                                '❌ 未完成项': "、".join(missing_items),
                                '未完成项数量': len(missing_items)
                            }
                            missing_data.append(student_info)
                        
                        progress_bar.progress(min((index + 1) / total_rows, 1.0))
                    
                    progress_bar.empty()
                    
                    # 5. Results
                    st.subheader("3. 核查结果")
                    
                    if missing_data:
                        result_df = pd.DataFrame(missing_data)
                        st.error(f"⚠️ 发现 {len(result_df)} 名学生存在未完成项！")
                        st.dataframe(result_df, use_container_width=True)
                        
                        # Export
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            result_df.to_excel(writer, index=False, sheet_name='未完成名单')
                        
                        st.download_button(
                            label="📥 下载未完成名单 (.xlsx)",
                            data=output.getvalue(),
                            file_name="未完成学生名单.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                    else:
                        st.balloons()
                        st.success("🎉 完美！所有选中学生均已完成填报。")

    except Exception as e:
        st.error(f"❌ 处理出错: {e}")
        st.error("请确保文件格式正确，且包含必要的【省学籍辅号】列。")

else:
    st.info("👋 请在上方上传文件开始使用。")
