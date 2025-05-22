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

with st.form("add_form"):
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
    submit = st.form_submit_button("💾 Save")

    if submit:
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
            st.success("✅ Document added successfully!")
            st.rerun()

# فلترة
with st.expander("🔎 Filter Documents"):
    st.markdown("### Filter Options")
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
    st.dataframe(filtered_df)

# قسم العرض الاحترافي 📝 Manage Documents
st.subheader("📝 Manage Documents")

for i, row in df.iterrows():
    st.markdown(f"""
    <div style="border:1px solid #DDD;padding:15px;border-radius:8px;margin-bottom:10px;
                background-color:{'#ffe6e6' if row['Status'] in ['C - Revise and Resubmit', 'D - Rejected'] else '#f9f9f9'}">
        <strong>{row['File Name']}</strong><br>
        <small>Status: <b>{row['Status'] or 'Not Set'}</b> | Discipline: {row['Discipline']}</small>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("✏️ Edit or Delete"):
        edited_row = {}
        for col in df.columns:
            edited_row[col] = st.text_input(f"{col}", value=str(row[col]), key=f"{col}_{i}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Save Changes", key=f"save_{i}"):
                for col in df.columns:
                    df.at[i, col] = edited_row[col]
                df.to_csv("documents.csv", index=False)
                st.success("✅ Changes saved!")
                st.rerun()
        with col2:
            if st.button("🗑️ Delete", key=f"delete_{i}"):
                df.drop(index=i, inplace=True)
                df.reset_index(drop=True, inplace=True)
                df.to_csv("documents.csv", index=False)
                st.warning("🗑️ Document deleted.")
                st.rerun()

# عرض كل المستندات
st.subheader("📋 All Documents")
def highlight(row):
    if row["Status"] in ["C - Revise and Resubmit", "D - Rejected"]:
        return ['background-color: #ffcccc'] * len(row)
    return [''] * len(row)

st.dataframe(df.style.apply(highlight, axis=1))

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
def export_pdf(data):
    pdf = FPDF()
    pdf.add_page()

    # تأكد من وجود الخط الداعم
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=10)

    pdf.cell(200, 10, "📄 Document Tracker Report", ln=1, align='C')
    pdf.ln(5)
    for i, row in data.iterrows():
        for col in data.columns:
            text = f"{col}: {row[col]}"
            pdf.cell(200, 6, txt=text, ln=1)
        pdf.ln(2)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

st.subheader("📤 Export")
if st.button("📄 Generate PDF"):
    pdf_file = export_pdf(df)
    st.download_button("⬇️ Download PDF", data=pdf_file, file_name="documents.pdf", mime="application/pdf")

st.download_button("⬇️ Download CSV", data=df.to_csv(index=False), file_name="documents.csv")
