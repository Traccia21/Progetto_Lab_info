import asyncio
import json
import re
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    wikipedia_urls = [
        "https://it.wikipedia.org/wiki/Minerva_(divinit%C3%A0)",
        "https://it.wikipedia.org/wiki/Roma",
        "https://it.wikipedia.org/wiki/Dante_Alighieri",
    ]

    data_tot = {}

    browser_config = BrowserConfig(verbose=True, headless=True)

    run_config = CrawlerRunConfig(
        # Seleziona solo paragrafi e titoli, escludendo infobox e navigation
        css_selector="#mw-content-text .mw-parser-output p, #mw-content-text .mw-parser-output h2, #mw-content-text .mw-parser-output h3",
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=0,
        excluded_tags=["nav", "footer", "header", "aside", "script", "style", "table"],
        remove_overlay_elements=True,
    )

    def clean_markdown(text):
        # 1. Converti link markdown in solo testo → [testo](url) diventa testo
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # 2. Rimuovi riferimenti numerici [1], [23]
        text = re.sub(r'\[\d+\]', '', text)

        # 3. Rimuovi tag HTML residui
        text = re.sub(r'<[^>]+>', '', text)

        # 4. Rimuovi sezioni non informative (italiano + inglese)
        sections_to_remove = [
            'See also', 'References', 'External links', 'Further reading',
            'Notes', 'Sources', 'Footnotes', 'Bibliography',
            'Voci correlate', 'Note', 'Altri progetti', 'Collegamenti esterni'
        ]
        for section in sections_to_remove:
            pattern = rf'## {section}.*?(?=##|\Z)'
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

        # 5. Rimuovi righe che sono solo link o simboli
        text = re.sub(r'^\s*[\|\*\#]+\s*$', '', text, flags=re.MULTILINE)

        # 6. Pulisci spazi eccessivi
        text = re.sub(r'\n\n\n+', '\n\n', text)
        text = text.strip()

        return text

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=wikipedia_urls, config=run_config)

        for result in results:
            if result.success:
                cleaned_text = clean_markdown(result.markdown.raw_markdown)

                data = {
                    "url": result.url,
                    "domain": "it.wikipedia.org",
                    "title": result.metadata.get('title', 'N/A'),
                    "parsed_text": cleaned_text
                }
                data_tot[result.url] = data

                print(f"✓ {result.metadata.get('title', 'N/A')}")
                print(f"  Lunghezza: {len(result.markdown.raw_markdown)} → Pulito: {len(cleaned_text)} caratteri\n")
                print(cleaned_text[:500])
                print("...\n")

            else:
                print(f"✗ Errore su {result.url}: {result.error_message}")

    with open('wikipedia_data.json', 'w', encoding='utf-8') as f:
        json.dump(data_tot, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Dati salvati in 'wikipedia_data.json' ({len(data_tot)} articoli)")


if __name__ == "__main__":
    asyncio.run(main())