import streamlit as st
import boto3
from werkzeug.utils import secure_filename
import mimetypes
from io import BytesIO
import fitz  # PyMuPDF
from docx import Document
import pandas as pd
import csv

# S3 config
s3 = boto3.client(
    "s3",
    aws_access_key_id="tid_sbiBCkRyuLVKoxZ_hYFoLkYOOnGffaZZGJgsNYdbgAKzEigDH_",
    aws_secret_access_key="tsec_8D6kPaJ2B3+U1hfOyzSJb3ktW6JOmkDK_A0aYUnrgu_7e4ot36BL-New9rna3_k6010Wmz",
    endpoint_url="https://fly.storage.tigris.dev",
)

BUCKET_NAME = "artifacts"
TIGRIS_BASE_URL = f"https://{BUCKET_NAME}.fly.storage.tigris.dev"

# ------------------------
# SIDEBAR: Upload + chọn
# ------------------------
st.sidebar.title("📁 Quản lý tài liệu")

uploaded_file = st.sidebar.file_uploader(
    "⬆️ Upload tài liệu",
    type=["pdf", "png", "jpg", "jpeg", "txt", "docx", "csv", "xlsx"],
)
if uploaded_file:
    filename = secure_filename(uploaded_file.name)
    s3.upload_fileobj(uploaded_file, BUCKET_NAME, filename)
    st.sidebar.success("✅ Upload thành công!")

# Lấy danh sách file từ S3
objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
file_names = []
if "Contents" in objects:
    file_list = sorted(
        objects["Contents"], key=lambda x: x["LastModified"], reverse=True
    )
    file_names = [obj["Key"] for obj in file_list]

selected_file = st.sidebar.selectbox(
    "📄 Chọn tài liệu", file_names if file_names else []
)

# ------------------------
# MAIN VIEW: Hiển thị nội dung
# ------------------------

if selected_file:
    mime_type, _ = mimetypes.guess_type(selected_file)
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=selected_file)
    file_bytes = obj["Body"].read()
    file_stream = BytesIO(file_bytes)

    if mime_type:
        if mime_type == "application/pdf":
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text = page.get_text()
                if text.strip():
                    st.markdown(text)
                else:
                    img = page.get_pixmap(dpi=150)
                    img_data = BytesIO(img.tobytes("png"))
                    st.image(img_data)
        elif mime_type.startswith("image/"):
            st.image(file_stream, use_column_width=True)
        elif mime_type == "text/plain":
            content = file_bytes.decode("utf-8")
            st.text(content)
        elif (
            mime_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            doc = Document(file_stream)
            for para in doc.paragraphs:
                st.markdown(para.text)
        elif mime_type == "text/csv" or selected_file.endswith(".csv"):
            # Đọc và hiển thị CSV
            df = pd.read_csv(file_stream)
            st.dataframe(df)
        elif (
            mime_type
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            or selected_file.endswith(".xlsx")
        ):
            # Đọc và hiển thị Excel
            df = pd.read_excel(file_stream)
            st.dataframe(df)
        else:
            st.warning("⚠️ Không hỗ trợ hiển thị loại tài liệu này.")
    else:
        st.warning("❓ Không xác định được định dạng file.")
else:
    st.info("📭 Chưa có tài liệu nào được chọn.")
