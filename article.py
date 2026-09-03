import logging
import os
import re
from html import escape
from typing import Optional

import httpx
from urllib.parse import urljoin
from bs4 import BeautifulSoup, NavigableString, Tag
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

ENDPOINT = os.getenv("ARTICLE_ENDPOINT")

if not ENDPOINT:
    raise RuntimeError("ARTICLE_ENDPOINT not found in .env")

ENDPOINT = ENDPOINT.rstrip("/")

# handling relative urls
BASE_ENDPOINT = ENDPOINT + "/"


def normalize_image_url(image: Optional[str]) -> Optional[str]:

    if not image:
        return None

    image = image.strip()

    if image.startswith(("http://", "https://")):
        return image

    if image.startswith("//"):
        return "https:" + image

    return urljoin(BASE_ENDPOINT, image)

PARAGRAPH = "paragraph"
HEADING = "heading"
QUOTE = "quote"
IMAGE = "image"
LIST = "list"

MAX_RETRIES = 3


async def fetch_hero_image(article_url: str) -> tuple[Optional[str], Optional[str]]:
    """Fallback hero image lookup on original publisher."""

    logger.info("Hero image: trying original publisher")

    try:

        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/137.0 Safari/537.36"
                )
            },
        ) as client:

            response = await client.get(article_url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        meta = soup.find("meta", property="og:image")

        if meta and meta.get("content"):

            logger.info("Hero image source: og")

            return meta["content"], "og"

        meta = soup.find(
            "meta",
            attrs={"name": "twitter:image"},
        )

        if meta and meta.get("content"):

            logger.info("Hero image source: twitter")

            return meta["content"], "twitter"

    except Exception as e:

        logger.warning(
            "Original hero lookup failed: %s",
            e,
        )

    return None, None


async def fetch_article(article_url: str) -> dict:

    target = f"{ENDPOINT}/{article_url}"

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            logger.info(
                "Fetching article (%d/%d): %s",
                attempt,
                MAX_RETRIES,
                target,
            )

            async with httpx.AsyncClient(
                timeout=60,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/137.0 Safari/537.36"
                    )
                },
            ) as client:

                response = await client.get(target)
                response.raise_for_status()

            article = parse_article(response.text)

            if article["hero_image"] is None:

                hero, source = await fetch_hero_image(article_url)

                if hero:

                    article["hero_image"] = hero
                    article["hero_source"] = source

            logger.info(
                "Hero image source: %s",
                article["hero_source"] or "none",
            )

            return article

        except Exception as e:

            last_error = e

            logger.warning(
                "Attempt %d/%d failed: %s",
                attempt,
                MAX_RETRIES,
                e,
            )

    logger.error(
        "All %d attempts failed.",
        MAX_RETRIES,
    )

    raise last_error

def to_telegram_html(node) -> str:
    """Convert supported HTML to Telegram HTML."""

    result = ""

    for child in node.children:

        if isinstance(child, NavigableString):
            result += escape(str(child))
            continue

        if not isinstance(child, Tag):
            continue

        name = child.name.lower()

        if name in ("strong", "b"):

            result += f"<b>{to_telegram_html(child)}</b>"

        elif name in ("em", "i"):

            result += f"<i>{to_telegram_html(child)}</i>"

        elif name == "u":

            result += f"<u>{to_telegram_html(child)}</u>"

        elif name == "s":

            result += f"<s>{to_telegram_html(child)}</s>"

        elif name == "code":

            result += (
                "<code>"
                f"{escape(child.get_text())}"
                "</code>"
            )

        elif name == "pre":

            result += (
                "<pre>"
                f"{escape(child.get_text())}"
                "</pre>"
            )

        elif name == "br":

            result += "\n"

        elif name == "a":

            href = (child.get("href") or "").strip()

            text = to_telegram_html(child)

            if href:

                result += (
                    f'<a href="{escape(href)}">'
                    f"{text}"
                    "</a>"
                )

            else:

                result += text

        else:

            result += to_telegram_html(child)

    return result.strip()


def extract_cover_image(
    soup: BeautifulSoup,
) -> tuple[Optional[str], Optional[str]]:
    """Extract the best available cover image from the endpoint."""

    cover = soup.find(
        "img",
        attrs={"alt": "Post cover image"},
    )

    if cover:

        # making changes here
        image = normalize_image_url(
            cover.get("data-zoom-src")
            or cover.get("src")
        )

        if image:

            logger.info(
                "Hero image source: freedium"
            )

            return image, "freedium"
            #end

    for script in soup.find_all("script"):

        content = script.string or script.get_text()

        if not content:
            continue

        match = re.search(
            r'"postImage"\s*:\s*"([^"]+)"',
            content,
        )

        if match:

            logger.info(
                "Hero image source: postImage"
            )

            image = normalize_image_url(
                match.group(1)
            )

            if image:

                return (
                    image,
                    "postImage",
                )

    meta = soup.find(
        "meta",
        property="og:image",
    )

    if meta and meta.get("content"):

        logger.info(
            "Hero image source: endpoint-og"
        )

        image = normalize_image_url(
            meta["content"]
        )

        if image:

            return (
                image,
                "endpoint-og",
            )

    return None, None


def extract_figure_image(
    figure: Tag,
) -> Optional[str]:

    img = figure.find("img")

    if img is None:
        return None

    candidates = [
        img.get("src"),
        img.get("data-src"),
        img.get("data-original"),
        img.get("data-zoom-src"),
    ]

    srcset = img.get("srcset")

    if srcset:

        first = srcset.split(",")[0].strip()

        if first:

            candidates.append(
                first.split()[0]
            )

    source = figure.find("source")

    if source:

        srcset = source.get("srcset")

        if srcset:

            first = srcset.split(",")[0].strip()

            if first:

                candidates.append(
                    first.split()[0]
                )

    for candidate in candidates:

        candidate = normalize_image_url(candidate)

        if candidate:
            return candidate

    return None




def parse_article(html: str) -> dict:

    soup = BeautifulSoup(html, "html.parser")

    article = soup.find("article")

    if article is None:
        raise Exception("Article element not found.")

    title = ""
    subtitle = ""
    author = ""
    date = ""

    header = article.find("header")

    if header:

        h1 = header.find("h1")

        if h1:
            title = h1.get_text(" ", strip=True)

        paragraphs = header.find_all("p")

        if len(paragraphs) >= 1:
            date = paragraphs[0].get_text(" ", strip=True)

        if len(paragraphs) >= 2:
            subtitle = paragraphs[1].get_text(" ", strip=True)

        for p in paragraphs:

            text = p.get_text(" ", strip=True)

            if text.startswith("By"):
                author = text
                break

    prose = article.select_one("div.prose")

    if prose is None:
        raise Exception("Article body not found.")

    hero_image, hero_source = extract_cover_image(soup)

    blocks = []
    body_images = 0

    for node in prose.children:

        if getattr(node, "name", None) is None:
            continue

        if node.name == "p":

            html = to_telegram_html(node)

            if html:

                blocks.append({
                    "type": PARAGRAPH,
                    "html": html,
                })

        elif node.name in ("h2", "h3", "h4"):

            blocks.append({
                "type": HEADING,
                "html": to_telegram_html(node),
            })

        elif node.name == "blockquote":

            blocks.append({
                "type": QUOTE,
                "html": to_telegram_html(node),
            })

        elif node.name == "figure":

            image_url = extract_figure_image(node)

            if not image_url:
                continue

            body_images += 1

            is_hero = False

            if hero_image is None:

                hero_image = image_url
                hero_source = "article"
                is_hero = True

                logger.info(
                    "Hero image source: article"
                )

            elif hero_image == image_url:

                is_hero = True

            caption = ""

            figcaption = node.find("figcaption")

            if figcaption:

                caption = figcaption.get_text(
                    " ",
                    strip=True,
                )

            blocks.append({
                "type": IMAGE,
                "url": image_url,
                "caption": caption,
                "is_hero": is_hero,
            })

        elif node.name in ("ul", "ol"):

            ordered = node.name == "ol"

            items = []

            for i, li in enumerate(
                node.find_all(
                    "li",
                    recursive=False,
                ),
                start=1,
            ):

                item = to_telegram_html(li)

                if not item:
                    continue

                if ordered:
                    items.append(f"{i}. {item}")
                else:
                    items.append(item)

            if items:

                blocks.append({
                    "type": LIST,
                    "items": items,
                })

    logger.info(
        "Parsed article '%s' (blocks=%d, body_images=%d)",
        title,
        len(blocks),
        body_images,
    )

    return {
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "date": date,
        "hero_image": hero_image,
        "hero_source": hero_source,
        "blocks": blocks,
    }
