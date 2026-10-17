# Pocket Ledger

An offline-first receipt and invoice sorter for freelancers. Add photos or PDFs, extract vendor/date/amount/category locally with Gemma 3 through Ollama, organize copies into folders, and export an editable CSV.

## Privacy

- The app runs on your own computer and sends receipt content only to the Ollama service at `127.0.0.1`.
- Streamlit is configured to listen only on `127.0.0.1`; browser usage statistics are disabled.
- There are no cloud APIs, analytics, or external upload endpoints in the app.
- Original files are never moved or changed; organized copies and `receipts.csv` are saved in the output folder.
- Ollama and the model need to be installed/downloaded while online. After that, turn off your internet connection and process receipts locally.
- Extracted values can be wrong. Review the table before using it for bookkeeping or tax reporting.

## Requirements

- Python 3.10 or newer
- [Ollama](https://ollama.com/download)
- Gemma 3 (the default model is `gemma3:4b`)

## Run

Install Ollama and download the model once:

```bash
ollama pull gemma3:4b
```

Then, from this project directory, set up and launch the app:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local address Streamlit prints (usually `http://localhost:8501`). Start Ollama if it is not already running. Choose **Upload files** to add multiple receipts, or **Local folder** and enter a folder path to scan its files. Folder scanning checks that folder's top level, not subfolders. To use another locally installed Ollama model, enter its name in the sidebar or set `OLLAMA_MODEL` before launching.

## Output

By default, the app creates `sorted_receipts/` in the project directory:

```text
sorted_receipts/
├── Meals/
│   └── 2026/
│       └── Acme_Cafe_2026-02-03_12.50_USD.pdf
├── Office_Supplies/
│   └── Undated/
└── receipts.csv
```

If a generated filename already exists, a numbered suffix is added rather than overwriting it. The CSV includes vendor, date, amount, currency, category, description, original filename, and sorted file path. Correct values in the table and the saved CSV updates.

## Supported input

PDF, PNG, JPG/JPEG, WEBP, and TIFF. Text-based PDFs are read locally; image-only PDFs use the first page for vision extraction.

## Tests

```bash
python -m unittest discover -s tests
```
