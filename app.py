from flask import Flask, request, render_template_string, send_file, session, after_this_request
import subprocess
import os
import tempfile
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Templates ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>tex2svg</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        textarea { width: 100%; box-sizing: border-box; }
        .container { display: flex; gap: 2em; }
        .form-container { flex: 1; }
        .result-container { flex: 1; }
    </style>
</head>
<body>
    <h1>LaTeX to SVG Converter</h1>
    <div class="container">
        <div class="form-container">
            <form method="post">
                <p><strong>LaTeX Snippet:</strong></p>
                <textarea name="latex" rows="10">{{ latex_snippet }}</textarea>
                <p><strong>Template:</strong></p>
                <textarea name="template" rows="15">{{ template }}</textarea>
                <br><br>
                <button type="submit">Convert</button>
            </form>
        </div>
        <div class="result-container">
            <h2>Result:</h2>
            {% if svg_path %}
                <a href="/download">
                    <button>Download SVG</button>
                </a>
                <hr>
                <div>{{ svg_output|safe }}</div>
            {% elif error %}
                <hr>
                <pre>{{ error }}</pre>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# --- Helper Functions ---

def tex_to_svg(latex_snippet, template_content):
    # Create a temporary directory to store intermediate files
    with tempfile.TemporaryDirectory() as tempdir:
        svg_filename = f"{uuid.uuid4()}.svg"
        output_svg_path = os.path.join(tempfile.gettempdir(), svg_filename)
        tex_path = os.path.join(tempdir, 'input.tex')

        # Prepare the full TeX document
        document = template_content.replace('%%content%%', latex_snippet)
        with open(tex_path, 'w') as f:
            f.write(document)

        # Run pdflatex to convert TeX to PDF
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-output-directory', tempdir, tex_path],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"pdflatex failed with return code {result.returncode}:\n{result.stdout}\n{result.stderr}")

        pdf_path = os.path.join(tempdir, 'input.pdf')

        # Run pdf2svg to convert PDF to SVG
        result = subprocess.run(
            ['pdf2svg', pdf_path, output_svg_path],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"pdf2svg failed with return code {result.returncode}:\n{result.stdout}\n{result.stderr}")

        # Read the generated SVG content
        with open(output_svg_path, 'r') as f:
            svg_content = f.read()

        return svg_content, output_svg_path

def cleanup_old_svg():
    """Remove the old SVG file from the session and filesystem."""
    old_svg_path = session.pop('svg_path', None)
    if old_svg_path and os.path.exists(old_svg_path):
        try:
            os.remove(old_svg_path)
        except OSError as e:
            app.logger.error(f"Error removing old file {old_svg_path}: {e}")

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    # Set default values for the form
    default_snippet = "\\begin{tikzpicture}\n    \\draw (0,0) circle (1in);\n\\end{tikzpicture}"
    with open(os.path.join(os.path.dirname(__file__), 'template.tex'), 'r') as f:
        default_template = f.read()

    context = {
        'latex_snippet': default_snippet,
        'template': default_template,
        'svg_output': None,
        'svg_path': None,
        'error': None
    }

    if request.method == 'POST':
        cleanup_old_svg() # Clean up any previous file first

        context['latex_snippet'] = request.form['latex']
        context['template'] = request.form['template']

        try:
            svg_output, svg_path = tex_to_svg(context['latex_snippet'], context['template'])
            session['svg_path'] = svg_path
            context['svg_output'] = svg_output
            context['svg_path'] = svg_path
        except (subprocess.CalledProcessError, RuntimeError) as e:
            context['error'] = f"Error during conversion:\n{e}"

    return render_template_string(HTML_TEMPLATE, **context)

@app.route('/download')
def download_svg():
    path = session.get('svg_path', None)
    if not path or not os.path.exists(path):
        return "No file to download or file has expired.", 404

    @after_this_request
    def cleanup(response):
        # Schedule the file for deletion after the request is complete
        try:
            os.remove(path)
            session.pop('svg_path', None)
        except OSError as e:
            app.logger.error(f"Error removing file {path}: {e}")
        return response

    return send_file(path, as_attachment=True, download_name='output.svg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5666)
