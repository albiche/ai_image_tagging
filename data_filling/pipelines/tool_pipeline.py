# data_filling/pipelines/tool_pipeline.py

import os, tempfile, requests
from io import BytesIO
from typing import List


from PIL import Image, ImageOps

from data_filling.utils.constants import SUPPORTED_MEDIA_EXTENSIONS
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry



# ------------------------------------------------------------------ #
#  Conversion PNG → JPG (qualité max, sans transparence)
# ------------------------------------------------------------------ #
def convert_png_to_jpg(png_path: str) -> str:
    with Image.open(png_path) as im:
        rgb = im.convert("RGB")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        rgb.save(tmp.name, "JPEG", quality=95)
        return tmp.name


# ------------------------------------------------------------------ #
#  Recherche des médias dans un dossier + option convert_png
# ------------------------------------------------------------------ #
def gather_media_files(row_dir: str, *, convert_png: bool) -> List[str]:
    media_paths, temp_files = [], []
    for f in os.listdir(row_dir):
        path = os.path.join(row_dir, f)
        if not f.lower().endswith(SUPPORTED_MEDIA_EXTENSIONS):
            continue
        if convert_png and f.lower().endswith(".png"):
            try:
                jpg = convert_png_to_jpg(path)
                temp_files.append(jpg)
                media_paths.append(jpg)
            except Exception as e:
                print(f"⚠️ PNG convert error « {f} »: {e}")
        else:
            media_paths.append(path)
    return media_paths, temp_files


# ------------------------------------------------------------------ #
#  Télécharge une image URL → fichier temporaire
# ------------------------------------------------------------------ #


def download_image_tmp(url: str, retries: int = 5, backoff_factor: float = 0.5, timeout: int = 30) -> str:
    """
    Télécharge l'image depuis l'URL dans un fichier temporaire local,
    avec gestion des retries et backoff.
    """
    import tempfile

    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Petit retry manuel sur les erreurs de lecture
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                tmp_path = tmp_file.name

            return tmp_path

        except (requests.exceptions.RequestException, requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError) as e:
            print(f"⚠️ download attempt {attempt} failed: {e}")
            if attempt < retries:
                sleep_time = backoff_factor * (2 ** (attempt - 1))
                print(f"🔄 Retrying in {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
            else:
                raise e



import tempfile
from PIL import Image, ImageOps
import os


def optimize_image(
        input_path: str,
        max_size: int = 1024,
        padding: int = 10,
        save_as_jpeg: bool = True
) -> str:
    """
    Optimise une image : crop autour du contenu utile, resize, padding.
    Peut forcer la sortie en JPEG ou conserver le format d'origine.

    Retourne le chemin du fichier temporaire optimisé.
    """
    with Image.open(input_path) as im:
        # Uniformiser en RGBA pour gérer la transparence
        im = im.convert("RGBA")

        # Trouver la bounding box utile
        gray = ImageOps.grayscale(im)
        inverted = ImageOps.invert(gray)
        bbox = inverted.getbbox()

        if bbox:
            im_cropped = im.crop(bbox)
        else:
            im_cropped = im

        # Ajouter un padding
        if padding > 0:
            new_w = im_cropped.width + 2 * padding
            new_h = im_cropped.height + 2 * padding
            new_img = Image.new("RGBA", (new_w, new_h), (255, 255, 255, 0))
            new_img.paste(im_cropped, (padding, padding))
            im_cropped = new_img

        # Redimensionner si trop grand
        if max(im_cropped.width, im_cropped.height) > max_size:
            im_cropped.thumbnail((max_size, max_size), Image.LANCZOS)

        # Choisir format de sortie
        if save_as_jpeg:
            # Forcer la conversion sans alpha sur fond blanc
            bg = Image.new("RGB", im_cropped.size, (255, 255, 255))
            bg.paste(im_cropped, mask=im_cropped.split()[-1])
            im_cropped = bg
            suffix = ".jpg"
            fmt = "JPEG"
        else:
            # Conserver la transparence
            suffix = ".png"
            fmt = "PNG"

        # Sauvegarder dans un fichier temporaire
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        if fmt == "JPEG":
            im_cropped.save(tmp.name, fmt, quality=90, optimize=True)
        else:
            im_cropped.save(tmp.name, fmt, optimize=True)

        return tmp.name
