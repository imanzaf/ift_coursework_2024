import streamlit as st
import requests
import pandas as pd
import altair as alt
import io
import zipfile
import os
from datetime import datetime
from minio import Minio
from pymongo import MongoClient

# -------------------------------
# 1. FastAPI API Base URL
# -------------------------------
API_BASE_URL = "http://localhost:8000"  # FastAPI 地址

# -------------------------------
# 2. Direct MongoDB & MinIO Connection
# -------------------------------
# MongoDB
mongo_client = MongoClient("mongodb://localhost:27019")
mongo_db = mongo_client["csr_db"]
collection_reports = mongo_db["csr_reports"]

# MinIO
minio_client = Minio(
    "localhost:9000",
    access_key="ift_bigdata",
    secret_key="minio_password",
    secure=False,
)
BUCKET_NAME = "csr-reports"

# -------------------------------
# 3. Streamlit 页面设置
# -------------------------------
st.set_page_config(page_title="CSR Dashboard", layout="wide")
st.title("📊 CSR Reports Dashboard (with Sentiment Analysis & Manual Upload)")

st.markdown(
    "🔍 Search, download, visualize, and manually upload CSR reports to MinIO & MongoDB. Includes **sentiment analysis** on reports."
)

# -------------------------------
# 4. Sidebar: Search Filters
# -------------------------------
st.sidebar.header("🔎 Search Filters")
company_query = st.sidebar.text_input("Company (fuzzy)", value="")
year_query = st.sidebar.number_input(
    "Year", min_value=2000, max_value=2100, step=1, value=2023
)
enable_year = st.sidebar.checkbox("Enable Year Filter")


# -------------------------------
# 5. 搜索功能
# -------------------------------
def search_reports(company, enable_year_filter, year):
    params = {}
    if company:
        params["company"] = company
    if enable_year_filter:
        params["year"] = year
    try:
        r = requests.get(f"{API_BASE_URL}/reports", params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            df = pd.DataFrame(data)
            return df
        elif r.status_code == 404:
            st.warning("⚠️ No data found for given filters.")
            return pd.DataFrame()
        else:
            st.error(f"❌ API Error {r.status_code}: {r.text}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Internal Error: {e}")
        return pd.DataFrame()


# -------------------------------
# 6. 搜索按钮
# -------------------------------
if st.sidebar.button("🔍 Search"):
    df = search_reports(company_query, enable_year, year_query)
    if not df.empty:
        st.session_state["search_results"] = df
    else:
        st.warning("No matching reports found.")

# -------------------------------
# 7. 显示搜索结果 & 批量下载
# -------------------------------
if (
    "search_results" in st.session_state
    and not st.session_state["search_results"].empty
):
    st.subheader("📄 Search Results")
    df = st.session_state["search_results"]
    st.dataframe(df)

    # 批量下载
    selected_indexes = st.multiselect("Select Rows to Download", df.index)
    if st.button("📥 Download Selected Reports as ZIP") and selected_indexes:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for idx in selected_indexes:
                row = df.loc[idx]
                download_link = row.get("download_link")
                if download_link:
                    file_resp = requests.get(download_link)
                    if file_resp.status_code == 200:
                        arcname = f"{row['csr_report_year']}_{row['company_name'].replace(' ', '_')}.pdf"
                        zf.writestr(arcname, file_resp.content)
        st.download_button(
            label="Download ZIP",
            data=zip_buf.getvalue(),
            file_name="csr_reports.zip",
            mime="application/zip",
        )

# -------------------------------
# 8. 报告年度分布可视化
# -------------------------------
st.header("📊 CSR Reports Overview")
try:
    all_resp = requests.get(f"{API_BASE_URL}/reports", timeout=5)
    if all_resp.status_code == 200:
        all_data = all_resp.json()
        df_all = pd.DataFrame(all_data)
        if not df_all.empty and "csr_report_year" in df_all.columns:
            chart_data = (
                df_all.groupby("csr_report_year")["company_name"]
                .count()
                .reset_index()
                .rename(columns={"company_name": "report_count"})
            )
            bar_chart = (
                alt.Chart(chart_data)
                .mark_bar()
                .encode(
                    x=alt.X("csr_report_year:O", title="Year"),
                    y=alt.Y("report_count:Q", title="Number of Reports"),
                    tooltip=["csr_report_year", "report_count"],
                )
                .properties(width=600, height=400)
            )
            st.altair_chart(bar_chart, use_container_width=True)
        else:
            st.info("No data available for visualization.")
    else:
        st.error("❌ Failed to retrieve overall data for visualization.")
except Exception as e:
    st.error(f"⚠️ Error fetching data: {e}")


# -------------------------------
# 10. 手动上传至 MinIO & MongoDB
# -------------------------------
st.header("📤 Manually Upload CSR Report")
st.markdown("Use this section to add missing CSR PDF files and insert metadata.")

company_name_input = st.text_input("Company Name", value="")
year_input = st.number_input(
    "Report Year", min_value=2000, max_value=2100, step=1, value=2023
)
csr_report_url_input = st.text_input("CSR Report URL (optional)", value="")
uploaded_pdf = st.file_uploader("Select a PDF file", type=["pdf"])

if st.button("⬆️ Upload to MinIO & Insert MongoDB"):
    if not company_name_input or not uploaded_pdf:
        st.error("Please enter a company name and select a PDF file.")
    else:
        safe_company = company_name_input.replace(" ", "_")
        storage_path = f"{year_input}/{safe_company}.pdf"

        # 上传到 MinIO
        try:
            file_bytes = uploaded_pdf.read()
            minio_client.put_object(
                bucket_name=BUCKET_NAME,
                object_name=storage_path,
                data=io.BytesIO(file_bytes),
                length=len(file_bytes),
                content_type="application/pdf",
            )
            st.success(f"✅ Successfully uploaded PDF to MinIO at {storage_path}")
        except Exception as e:
            st.error(f"❌ Failed to upload PDF: {e}")
            st.stop()

        # 插入 MongoDB
        doc = {
            "company_name": company_name_input,
            "csr_report_year": int(year_input),
            "csr_report_url": csr_report_url_input,
            "storage_path": storage_path,
            "ingestion_time": datetime.now().isoformat(),
        }
        collection_reports.insert_one(doc)
        st.success("✅ Successfully inserted metadata into MongoDB.")
