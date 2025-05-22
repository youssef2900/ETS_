import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Document Tracker", layout="wide")

# تحميل البيانات
try:
    df = pd.read_csv("documents.csv")
except FileNotFoundError:
    df = pd.DataFrame(columns=[
        "File Name", "Doc Ref", "Document Title", "Status", "Discipline",
        "File Type", "Rev Date", "Delivery Date", "Project", "Originator", "Project Stage"
    ])

# الحالات المسموحة فقط (اختصارات الموافقة)
status_options = [
    "A - Approved",
    "B - Approved with Comments",
    "C - Revise and Resubmit",
    "D - Rejected"
]

discipline_options = [
    "Architecture", "Civil", "Electrical", "Mechanical", "Surveying"
]

# إضافة مستند جديد
st.title("📁 Document Tracker")

with st.form("add_doc"):
    st.subheader("➕ Add New Document")
    file_name = st.text_input("File Name")
    doc_ref = st.text_input("Document Ref")
    title = st.text_input("Document Title")
    status = st.selectbox("Status (Optional)", [""] + status_options)
    discipline = st.selectbox("Discipline", ["Select..."] + discipline_options)
    file_type = st.text_input("File Type")
    rev_date = st.date_input("Revision Date", value=datetime.date.today())
    delivery_date = st.date_input("Delivery Date", value=datetime.date.today())
    project = st.text_input("Project")
    originator = st.text_input("Originator")
    stage = st.text_input("Project Stage")
    submitted = st.form_submit_button("Save")

    if submitted:
        if (not file_name or not doc_ref or not title or
            discipline == "Select..." or not file_type or
            not delivery_date or not project or not originator or not stage):
            st.warning("❗ Please fill in all required fields before saving.")
        else:
            new_row = {
                "File Name": file_name,
                "Doc Ref": doc_ref,
                "Document Title": title,
                "Status": status,
                "Discipline": discipline,
                "File Type": file_type,
                "Rev Date": rev_date,
                "Delivery Date": delivery_date,
                "Project": project,
                "Originator": originator,
                "Project Stage": stage
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv("documents.csv", index=False)
            st.success("✅ Document added!")
            st.rerun()

# تلوين الصفوف
def highlight_row(row):
    if row["Status"] in ["C - Revise and Resubmit", "D - Rejected"]:
        return ['background-color: #ffcccc; font-weight: bold'] * len(row)
    return [''] * len(row)

# بحث
st.markdown("## 🔍 Search")
search_term = st.text_input("Search keyword:")
if search_term:
    search_results = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
    styled_search = search_results.style.apply(highlight_row, axis=1)
    st.dataframe(styled_search)

# فلترة
with st.expander("🔎 Filter Documents"):
    selected_status = st.selectbox("Filter by Status", ["All"] + status_options)
    selected_discipline = st.selectbox("Filter by Discipline", ["All"] + discipline_options)
    originators = df["Originator"].dropna().unique().tolist()
    selected_originator = st.selectbox("Filter by Originator", ["All"] + originators)
    doc_refs = df["Doc Ref"].dropna().unique().tolist()
    selected_doc_ref = st.selectbox("Filter by Document Ref", ["All"] + doc_refs)

    filtered_df = df.copy()
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df["Status"] == selected_status]
    if selected_discipline != "All":
        filtered_df = filtered_df[filtered_df["Discipline"] == selected_discipline]
    if selected_originator != "All":
        filtered_df = filtered_df[filtered_df["Originator"] == selected_originator]
    if selected_doc_ref != "All":
        filtered_df = filtered_df[filtered_df["Doc Ref"] == selected_doc_ref]

    styled_filtered_df = filtered_df.style.apply(highlight_row, axis=1)
    st.dataframe(styled_filtered_df)

# تعديل وحذف
st.markdown("## 🗂️ Manage Documents")
if not df.empty:
    for i, row in df.iterrows():
        with st.expander(f"{row['File Name']} — {row['Status']}"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✏️ Edit {i}", key=f"edit_{i}"):
                    st.session_state["edit_index"] = i
            with col2:
                if st.button(f"🗑️ Delete {i}", key=f"delete_{i}"):
                    df.drop(index=i, inplace=True)
                    df.reset_index(drop=True, inplace=True)
                    df.to_csv("documents.csv", index=False)
                    st.success("🗑️ Deleted successfully.")
                    st.rerun()

# نموذج تعديل
if "edit_index" in st.session_state:
    idx = st.session_state["edit_index"]
    st.markdown("## ✏️ Edit Document")
    edited = {}
    for col in df.columns:
        val = st.text_input(f"{col}", value=str(df.loc[idx, col]), key=f"edit_{col}")
        edited[col] = val
    if st.button("💾 Save Changes"):
        for col in df.columns:
            df.at[idx, col] = edited[col]
        df.to_csv("documents.csv", index=False)
        del st.session_state["edit_index"]
        st.success("✅ Changes saved!")
        st.rerun()

# عرض الجدول
st.markdown("## 📋 All Documents")
styled_df = df.style.apply(highlight_row, axis=1)
st.dataframe(styled_df)

# طباعة
st.markdown("""
    <script>
    function printTable() {
        var divToPrint = document.querySelector("section.main");
        var newWin = window.open('', 'Print-Window');
        newWin.document.open();
        newWin.document.write('<html><head><title>Print Table</title></head><body onload="window.print()">'+divToPrint.innerHTML+'</body></html>');
        newWin.document.close();
        setTimeout(function(){newWin.close();},10);
    }
    </script>
    <button onclick="printTable()">🖨️ Print Table</button>
""", unsafe_allow_html=True)

# تصدير PDF
def generate_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="📄 Document Tracker Report", ln=1, align='C')
    pdf.ln(5)
    for index, row in dataframe.iterrows():
        for col in dataframe.columns:
            text = f"{col}: {row[col]}"
            pdf.cell(200, 6, txt=text, ln=1)
        pdf.ln(3)
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

st.markdown("## 📤 Export")
if st.button("📄 Generate PDF"):
    pdf_buffer = generate_pdf(df)
    st.download_button(
        label="⬇️ Download PDF",
        data=pdf_buffer,
        file_name="documents.pdf",
        mime="application/pdf"
    )

st.download_button("⬇️ Download CSV", df.to_csv(index=False), "documents.csv")
