# tex2svg

This is a web application that converts LaTeX snippets to SVG images. It uses `pdflatex` and `pdf2svg` to perform the conversion.

## Running with Docker

1.  **Build the Docker image:**

    ```bash
    docker build -t tex2svg .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run -p 5000:5000 tex2svg
    ```

3.  **Open the application:**

    Open your web browser and navigate to `http://localhost:5000`.
