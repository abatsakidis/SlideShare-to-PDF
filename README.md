# SlideShare to PDF

A Python tool that uses Playwright to open publicly accessible SlideShare presentations, detect publicly available slide images, and combine them into a PDF document.

## Features

- Opens SlideShare presentation URLs using Playwright and Chromium.
- Detects publicly accessible slide images in the page.
- Scrolls through the page to trigger lazy-loaded images.
- Filters out small images and potential thumbnails.
- Downloads detected images and converts them into PDF pages.
- Saves the generated PDF and downloaded images locally.
- Provides basic error handling for network requests and invalid images.

## Requirements

- Python 3.10 or newer recommended.
- A working internet connection.
- Access to the public SlideShare presentation.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/abatsakidis/SlideShare-to-PDF.git
cd SlideShare-to-PDF
```
### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Install Playwright Chromium

```bash
python -m playwright install chromium
```

On Linux, you may need additional system dependencies. You can install them using:

```bash
python -m playwright install --with-deps chromium
```

## Usage

Run the script:

```bash
python slideshare_playwright.py
```

Enter the URL of a publicly accessible SlideShare presentation when prompted.

Example:

```text
URL δημόσιας παρουσίασης SlideShare: https://www.slideshare.net/username/example-presentation
```

If suitable slide images are detected and downloaded successfully, the script generates a PDF in the `slideshare_downloads/` directory.

## Output

The output directory may look like this:

```text
slideshare_downloads/
├── Example_Presentation.pdf
└── Example_Presentation/
    ├── slide_0001.jpg
    ├── slide_0002.jpg
    ├── slide_0003.jpg
    └── ...
```

The PDF contains one image per page. The original text and elements are not editable.

## Limitations

- The script does not guarantee that every slide will be detected.
- SlideShare may change its page structure, image URLs, or viewer implementation.
- Some presentations may require authentication or may not expose slide images publicly.
- Images may be thumbnails rather than full-resolution slides.
- The detected image order may not always match the original slide order.
- The script does not bypass authentication, access controls, or content restrictions.
- An official downloadable PDF, when available, may provide better quality and completeness.

## Dependencies

The project uses the following Python packages:

- [Playwright](https://playwright.dev/python/) — browser automation.
- [Pillow](https://pillow.readthedocs.io/) — image processing.
- [img2pdf](https://pypi.org/project/img2pdf/) — PDF generation.

See `requirements.txt` for the dependency list.

## Legal and Responsible Use

Use this tool only for presentations and content you are authorized to download or reproduce.

Respect the copyright of presentation authors, SlideShare's terms of service, and any applicable access restrictions. The tool is intended for publicly accessible content and does not attempt to bypass authentication or other protections.

## Troubleshooting

### No slide images found

The presentation may load images dynamically or use a viewer structure that the script does not recognize. Check whether the presentation is publicly accessible and whether downloading is permitted.

### Some slides are missing

The current image-detection logic may not identify every slide or may filter out smaller images. Inspect the generated PDF and consider using SlideShare's official download option if available.

### Chromium is missing

Run:

```bash
python -m playwright install chromium
```

## License

Choose a license appropriate for your project before publishing it. If you intend to make the code open source, consider adding a `LICENSE` file.

---

**Disclaimer:** This project is provided for educational purposes. It is not affiliated with or endorsed by SlideShare.
