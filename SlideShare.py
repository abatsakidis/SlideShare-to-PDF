
import asyncio
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image
from playwright.async_api import async_playwright
import img2pdf


OUTPUT_DIR = Path("slideshare_downloads")
OUTPUT_DIR.mkdir(exist_ok=True)

MIN_WIDTH = 500
MIN_HEIGHT = 300
MAX_SCROLLS = 35

ALLOWED_HOST = "slidesharecdn.com"


def valid_url(url):
    parsed = urlparse(url)
    return (
        parsed.scheme in ("http", "https")
        and parsed.hostname in (
            "slideshare.net",
            "www.slideshare.net",
        )
    )


def safe_filename(text):
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", text)
    return text.strip(" ._")[:90] or "slideshare_presentation"


def is_slide_image(url):
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        return (
            parsed.scheme in ("http", "https")
            and (
                host == ALLOWED_HOST
                or host.endswith("." + ALLOWED_HOST)
            )
            and parsed.path.lower().endswith(
                (".jpg", ".jpeg", ".png", ".webp")
            )
        )
    except ValueError:
        return False


async def collect_images(page):
    """
    Συλλέγει URLs εικόνων από το DOM με τη σειρά εμφάνισής τους.
    Κάνει scrolling ώστε να ενεργοποιηθεί η lazy loading φόρτωση.
    """
    discovered = []
    seen = set()

    async def scan_dom():
        elements = await page.locator("img").evaluate_all(
            """images => images.map(img => ({
                src: img.currentSrc || img.src || "",
                width: img.naturalWidth || 0,
                height: img.naturalHeight || 0,
                alt: img.alt || ""
            }))"""
        )

        for item in elements:
            src = item["src"]

            if not src or not is_slide_image(src):
                continue

            # Αγνοούμε μικρές εικόνες και thumbnails.
            if (
                item["width"] < MIN_WIDTH
                or item["height"] < MIN_HEIGHT
            ):
                continue

            if src not in seen:
                seen.add(src)
                discovered.append(src)

    await scan_dom()

    previous_count = -1
    unchanged_rounds = 0

    for _ in range(MAX_SCROLLS):
        await page.evaluate(
            "() => window.scrollBy(0, Math.max(500, window.innerHeight * 0.8))"
        )

        await page.wait_for_timeout(800)
        await scan_dom()

        if len(discovered) == previous_count:
            unchanged_rounds += 1
        else:
            unchanged_rounds = 0

        previous_count = len(discovered)

        if unchanged_rounds >= 4:
            break

    # Επαναφορά στην κορυφή.
    await page.evaluate("() => window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)

    return discovered


async def download_images(page, urls, folder):
    """
    Κατεβάζει τις εικόνες χρησιμοποιώντας το browser context.
    Δεν επιχειρεί να παρακάμψει περιορισμούς πρόσβασης.
    """
    paths = []

    for index, url in enumerate(urls, start=1):
        try:
            response = await page.request.get(
                url,
                timeout=30000,
            )

            if not response.ok:
                print(f"Παράλειψη εικόνας {index}: HTTP {response.status}")
                continue

            data = await response.body()

            try:
                image = Image.open(BytesIO(data))
                image.load()

                if (
                    image.width < MIN_WIDTH
                    or image.height < MIN_HEIGHT
                ):
                    print(f"Παράλειψη μικρής εικόνας {index}")
                    continue

                # Μετατροπή σε RGB PNG για συμβατότητα με το PDF.
                image = image.convert("RGB")

                path = folder / f"slide_{index:04d}.jpg"
                image.save(path, format="JPEG", quality=95)

                paths.append(path)

                print(
                    f"Εικόνα {index}: "
                    f"{image.width}x{image.height}"
                )

            except Exception as error:
                print(f"Μη έγκυρη εικόνα {index}: {error}")

        except Exception as error:
            print(f"Αποτυχία λήψης εικόνας {index}: {error}")

    return paths


def create_pdf(paths, output_file):
    if not paths:
        raise ValueError("Δεν υπάρχουν εικόνες για δημιουργία PDF.")

    with open(output_file, "wb") as pdf:
        pdf.write(img2pdf.convert([str(p) for p in paths]))


async def main():
    url = input("URL δημόσιας παρουσίασης SlideShare: ").strip()

    if not valid_url(url):
        print("Μη έγκυρο URL. Χρειάζεται διεύθυνση slideshare.net.")
        return

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        context = await browser.new_context(
            viewport={"width": 1440, "height": 1000},
            accept_downloads=False,
        )

        page = await context.new_page()

        try:
            print("Άνοιγμα παρουσίασης...")

            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            if response and response.status >= 400:
                print(f"Η σελίδα επέστρεψε HTTP {response.status}.")
                return

            await page.wait_for_timeout(2500)

            title = await page.title()
            filename = safe_filename(title)
            folder = OUTPUT_DIR / filename
            folder.mkdir(exist_ok=True)

            print("Αναζήτηση δημόσια προσβάσιμων διαφανειών...")

            urls = await collect_images(page)

            print(f"Εντοπίστηκαν {len(urls)} εικόνες υποψήφιες για διαφάνειες.")

            if not urls:
                print(
                    "Δεν εντοπίστηκαν εικόνες διαφανειών. "
                    "Ο viewer μπορεί να χρησιμοποιεί διαφορετική "
                    "δομή ή να απαιτεί εξουσιοδοτημένη πρόσβαση."
                )
                return

            print("Λήψη εικόνων...")
            paths = await download_images(page, urls, folder)

            if not paths:
                print("Δεν ήταν δυνατή η λήψη έγκυρων εικόνων.")
                return

            pdf_path = OUTPUT_DIR / f"{filename}.pdf"
            create_pdf(paths, pdf_path)

            print("\nΟλοκληρώθηκε!")
            print(f"Σελίδες PDF: {len(paths)}")
            print(f"Αρχείο: {pdf_path.resolve()}")

            if len(paths) != len(urls):
                print(
                    "Προσοχή: ορισμένες εικόνες παραλείφθηκαν. "
                    "Έλεγξε το PDF για ελλείπουσες διαφάνειες."
                )

        except Exception as error:
            print(f"Σφάλμα: {error}")

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
