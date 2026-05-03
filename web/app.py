from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
import tempfile
import os
from engine.explainer import run_explanation

app = FastAPI(title="CDC Explain AI")

# The complete HTML page as a string
HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <title>CDC Explain AI</title>
    <meta charset="utf-8">
    <style>
        body { font-family: sans-serif; max-width: 900px; margin: 2rem auto; padding: 1rem; }
        .drop-zone {
            border: 2px dashed #aaa; border-radius: 8px; padding: 2rem; text-align: center;
            background-color: #fafafa; margin-bottom: 1rem;
        }
        .drop-zone.dragover { background-color: #e0f0ff; border-color: #2a73cc; }
        input[type="file"] { margin: 0.5rem 0; }
        button {
            background-color: #2a73cc; color: white; border: none; padding: 0.7rem 1.5rem;
            font-size: 1rem; border-radius: 4px; cursor: pointer;
        }
        button:hover { background-color: #1f5ca3; }
        #result {
            background: #f5f5f5; border: 1px solid #ddd; padding: 1.5rem;
            white-space: pre-wrap; font-family: monospace; margin-top: 2rem; border-radius: 4px;
        }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>🔍 CDC Explain AI</h1>
    <p>Upload your simulation files and get an AI root‑cause analysis.</p>

    <form id="upload-form" action="/explain" method="post" enctype="multipart/form-data">
        <div class="drop-zone" id="drop-zone">
            <p>Drop files here or click to browse</p>
            <label>VCD Waveform: <input type="file" name="vcd" required accept=".vcd"></label><br>
            <label>Simulation Log: <input type="file" name="log" required accept=".log,.txt"></label><br>
            <label>CDC Violations (JSON): <input type="file" name="cdc" required accept=".json"></label>
        </div>
        <button type="submit">Explain Failure</button>
    </form>

    <div id="result"></div>

    <script>
        const dropZone = document.getElementById('drop-zone');
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            const fileInputs = document.querySelectorAll('input[type="file"]');
            for (let i = 0; i < Math.min(files.length, fileInputs.length); i++) {
                const dt = new DataTransfer();
                dt.items.add(files[i]);
                fileInputs[i].files = dt.files;
            }
        });

        const form = document.getElementById('upload-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = 'Processing...';
            try {
                const response = await fetch('/explain', { method: 'POST', body: formData });
                const explanation = await response.text();
                resultDiv.innerHTML = explanation;
            } catch (err) {
                resultDiv.innerHTML = 'Error: ' + err.message;
            }
        });
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=HTML_PAGE)

@app.post("/explain")
async def explain(
    vcd: UploadFile = File(...),
    log: UploadFile = File(...),
    cdc: UploadFile = File(...)
):
    # Save uploaded files to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".vcd") as vcd_file:
        vcd_content = await vcd.read()
        vcd_file.write(vcd_content)
        vcd_path = vcd_file.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as log_file:
        log_content = await log.read()
        log_file.write(log_content)
        log_path = log_file.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as cdc_file:
        cdc_content = await cdc.read()
        cdc_file.write(cdc_content)
        cdc_path = cdc_file.name

    # Run the explanation engine
    try:
        explanation = run_explanation(
            log_path=log_path,
            vcd_path=vcd_path,
            cdc_path=cdc_path
        )
        # Fix escaped newlines that some LLMs produce
        explanation = explanation.replace('\\n', '\n')
    except Exception as e:
        explanation = f"Error during explanation: {e}"

    # Wrap in <pre> for better formatting, but keep pre-wrap from CSS as well
    return HTMLResponse(content=f"<pre style='white-space: pre-wrap;'>{explanation}</pre>")
