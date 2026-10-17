from __future__ import annotations

import hashlib
import os
from pathlib import Path

import streamlit as st

from receipt_sorter import CATEGORIES, csv_bytes, extract_receipt, organize_receipt, write_csv


st.set_page_config(page_title="Pocket Ledger", page_icon="🧾", layout="wide")
st.markdown(
    """
    <style>
      .block-container { max-width: 1050px; padding-top: 2.5rem; }
      .hero { padding: 1.6rem 1.8rem; border-radius: 18px; background: linear-gradient(120deg, #e9f5ee, #f4f6e9); margin-bottom: 1.2rem; }
      .hero h1 { margin: 0 0 .4rem; color: #183a2b; font-size: 2.4rem; }
      .hero p { margin: 0; color: #41604f; font-size: 1.05rem; }
      div[data-testid="stFileUploader"] { border-radius: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>Pocket Ledger</h1>'
    "<p>Your receipts, organized on your computer. No cloud uploads. No spreadsheet busywork.</p></div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Local model")
    model = st.text_input("Ollama model", value=os.environ.get("OLLAMA_MODEL", "gemma3:4b"))
    st.caption("Ollama must be running on this computer. Pull the model once before going offline.")
    st.divider()
    st.subheader("Where to save")
    output_location = st.text_input("Output folder", value="sorted_receipts")
    st.caption("Files are copied here; your originals are left untouched.")

st.markdown("### Add receipts")
st.write("Upload a few files or point the app at a folder on this computer.")
source_type = st.radio("Choose how to add receipts", ["Upload files", "Local folder"], horizontal=True)
supported_extensions = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".pdf"}
inputs: list[tuple[str, bytes | Path]] = []
input_errors: list[str] = []

if source_type == "Upload files":
    uploads = st.file_uploader(
        "Receipt files",
        type=sorted(extension.lstrip(".") for extension in supported_extensions),
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploads:
        inputs.extend((uploaded.name, uploaded.getvalue()) for uploaded in uploads)
else:
    folder_location = st.text_input("Path to a folder on this computer", placeholder="/home/you/Receipts")
    if folder_location.strip():
        source_dir = Path(folder_location).expanduser()
        if not source_dir.is_dir():
            input_errors.append(f"`{source_dir}` is not a readable folder.")
        else:
            try:
                for file_path in sorted(source_dir.iterdir()):
                    if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                        inputs.append((file_path.name, file_path))
            except OSError as exc:
                input_errors.append(f"Could not scan `{source_dir}`: {exc}")
            if not inputs and not input_errors:
                input_errors.append(f"No supported receipt files were found directly inside `{source_dir}`.")

for error in input_errors:
    st.error(error)

if "rows" not in st.session_state:
    st.session_state.rows = []
if "processed_names" not in st.session_state:
    st.session_state.processed_names = set()

st.info(
    "Private by design: files are handled by this local app and sent only to Ollama at "
    "`127.0.0.1`. Install the model while online; receipt processing itself needs no internet."
)

if inputs and st.button("Sort receipts", type="primary", use_container_width=True):
    if not model.strip():
        st.error("Enter the name of an Ollama model, such as `gemma3:4b`.")
    elif not output_location.strip():
        st.error("Choose an output folder.")
    else:
        output_dir = Path(output_location).expanduser()
        progress = st.progress(0, text="Getting receipts ready…")
        failures: list[str] = []
        for index, (file_name, source) in enumerate(inputs, start=1):
            try:
                contents = source if isinstance(source, bytes) else source.read_bytes()
                identity = f"{file_name}:{hashlib.sha256(contents).hexdigest()}"
                if identity in st.session_state.processed_names:
                    failures.append(f"{file_name}: already processed in this session.")
                    progress.progress(index / len(inputs), text=f"Checked {file_name}")
                    continue
                receipt = extract_receipt(file_name, contents, model.strip())
                relative_path = organize_receipt(output_dir, file_name, contents, receipt)
                row = {
                    **receipt,
                    "source_file": file_name,
                    "sorted_path": relative_path,
                }
                st.session_state.rows.append(row)
                st.session_state.processed_names.add(identity)
            except (RuntimeError, ValueError, OSError) as exc:
                failures.append(f"{file_name}: {exc}")
            progress.progress(index / len(inputs), text=f"Processed {file_name}")

        if st.session_state.rows:
            try:
                csv_path = write_csv(output_dir, st.session_state.rows)
                st.success(f"Saved organized receipts and CSV to `{output_dir.resolve()}`.")
                st.caption(f"CSV file: `{csv_path}`")
            except OSError as exc:
                st.error(f"Could not save the CSV to `{output_dir}`: {exc}")
        for failure in failures:
            st.error(failure)

if st.session_state.rows:
    st.markdown("### Extracted receipts")
    st.caption("Review model-extracted values before relying on them for bookkeeping or tax reporting.")
    edited_rows = st.data_editor(
        st.session_state.rows,
        column_config={
            "category": st.column_config.SelectboxColumn("Category", options=CATEGORIES),
            "amount": st.column_config.TextColumn("Amount"),
            "date": st.column_config.TextColumn("Date (YYYY-MM-DD)"),
        },
        disabled=["source_file", "sorted_path"],
        hide_index=True,
        use_container_width=True,
        key="receipt_editor",
    )
    st.session_state.rows = edited_rows.to_dict(orient="records")
    export_dir = Path(output_location).expanduser()
    try:
        saved_csv = write_csv(export_dir, st.session_state.rows)
        st.download_button(
            "Download CSV",
            data=csv_bytes(st.session_state.rows),
            file_name="receipts.csv",
            mime="text/csv",
            type="primary",
        )
        st.caption(f"Latest edits are saved to `{saved_csv}`.")
    except OSError as exc:
        st.error(f"Could not save the CSV to `{export_dir}`: {exc}")
