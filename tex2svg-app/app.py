from flask import Flask, request, render_template_string, send_file
import subprocess
import os
import tempfile

app = Flask(__name__)

def tex_to_svg(latex_snippet, template_content):
    with tempfile.TemporaryDirectory() as tempdir:
        template_path = os.path.join(tempdir, 'template.tex')
        with open(template_path, 'w') as f:
            f.write(template_content)

        tex_path = os.path.join(tempdir, 'input.tex')
        with open(template_path, 'r') as f:
            template_content = f.read()

        document = template_content.replace('%%content%%', latex_snippet)
        with open(tex_path, 'w') as f:
            f.write(document)

        subprocess.run(['pdflatex', '-interaction=nonstopmode', '-output-directory', tempdir, tex_path], check=True)

        pdf_path = os.path.join(tempdir, 'input.pdf')
        svg_path = os.path.join(tempdir, 'output.svg')

        subprocess.run(['pdf2svg', pdf_path, svg_path], check=True)

        with open(svg_path, 'r') as f:
            svg_content = f.read()

        return svg_content

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        latex_snippet = request.form['latex']
        template = request.form['template']

        try:
            svg_output = tex_to_svg(latex_snippet, template)
        except subprocess.CalledProcessError as e:
            svg_output = f"<pre>Error during conversion: {e}</pre>"

        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>tex2svg</title>
                <style>
                    body { font-family: sans-serif; margin: 2em; }
                    textarea { width: 100%; }
                </style>
            </head>
            <body>
                <h1>LaTeX to SVG Converter</h1>
                <form method="post">
                    <textarea name="latex" rows="10" cols="50">{{ latex_snippet }}</textarea>
                    <br>
                    <textarea name="template" rows="10" cols="50">{{ template }}</textarea>
                    <br>
                    <button type="submit">Convert</button>
                </form>
                <hr>
                <h2>Result:</h2>
                <div>{{ svg_output|safe }}</div>
            </body>
            </html>
        ''', latex_snippet=latex_snippet, template=template, svg_output=svg_output)

    with open(os.path.join(os.path.dirname(__file__), 'template.tex'), 'r') as f:
        default_template = f.read()

    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>tex2svg</title>
            <style>
                body { font-family: sans-serif; margin: 2em; }
                textarea { width: 100%; }
            </style>
        </head>
        <body>
            <h1>LaTeX to SVG Converter</h1>
            <form method="post">
                <textarea name="latex" rows="10" cols="50">\\begin{tikzpicture}
    \\draw (0,0) circle (1in);
\\end{tikzpicture}</textarea>
                <br>
                <textarea name="template" rows="10" cols="50">{{ default_template }}</textarea>
                <br>
                <button type="submit">Convert</button>
            </form>
        </body>
        </html>
    ''', default_template=default_template)

if __name__ == '__main__':
    app.run(host='0.0.0.0')