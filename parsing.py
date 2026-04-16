import asyncio
import json
import re
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode

def token_level_eval(text, gold_text, titolo):
    text = re.split(r'[\s]+', text.lower())
    set_token_parsati = set(text)
    #print(set_token_parsati)
    gold_text = re.split(r'[\s]+', gold_text.lower())
    set_token_gs = set(gold_text)
    #print(set_token_gs)
    res = set_token_gs.intersection(set_token_parsati)
    print(set_token_parsati-res)
    
    precision = len(res) / len(set_token_parsati) if set_token_parsati else 0
    recall = len(res) / len(set_token_gs) if set_token_gs else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0
    print(f"titolo {titolo}, precision: {precision:.4f}, recall: {recall:.4f}, F1-score: {f1:.4f}")


def parse_markdown_to_clean(text):

    # 1. Rimuovi link wikipedia residui tipo "Testo (disambigua)")
    text = re.sub(r'"[^"]*\([^)]*\)"\)', '', text)

    # 2. Rimuovi grassetto **testo** mantenendo il testo
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)

    # 3. Rimuovi corsivo _testo_ mantenendo il testo
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # 4. Rimuovi [citation needed] e varianti
    text = re.sub(r'\[citation needed\]', '', text)

    # 5. Rimuovi sezioni ## e ### finali
    sections_to_remove = [
        'See also', 'References', 'External links', 'Further reading',
        'Notes', 'Sources', 'Footnotes', 'Bibliography', 'Related articles',
        'Citations', 'Works cited', 'General references', 'Inline notes',
        'Explanatory notes', 'Navigation menu', 'Contents',
    ]
    for section in sections_to_remove:
        pattern = rf'##\s+{re.escape(section)}.*?(?=##|\Z)'
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

    # 6. Rimuovi righe che sono solo ## titolo
    text = re.sub(r'^#{1,3}\s+.*$', '', text, flags=re.MULTILINE)

    # 7. Rimuovi backslash
    text = re.sub(r'\\', '', text)

    # 8. Rimuovi virgolette iniziali e finali del testo intero
    text = text.strip('"')

    # 9. Rimuovi link vuoti [](url)
    text = re.sub(r'\[\]\([^\)]*\)', '', text)

    # 10. Rimuovi link markdown [testo](url) → testo
    text = re.sub(r'\[([^\]]*)\]\([^\)]+\)', r'\1', text)

    # 11. Rimuovi riferimenti numerici [1], [23]
    text = re.sub(r'\[\d+\]', '', text)

    # 12. Rimuovi tag HTML residui
    text = re.sub(r'<[^>]+>', '', text)

    # 13. Rimuovi righe che sono solo simboli
    text = re.sub(r'^\s*[\|\*\#]+\s*$', '', text, flags=re.MULTILINE)

    # 14. Elimina link con singolo carattere [[a]](url)
    text = re.sub(r'\[\[[a-zA-Z]\]\]\([^\)]*\)', '', text)

    # 15. Mantieni testo da link doppia parentesi [[testo]](url) → testo
    text = re.sub(r'\[\[([^\]]+)\]\]\([^\)]*\)', r'\1', text)

    # 16. Pulisci spazi eccessivi
    text = re.sub(r'\n\n\n+', '\n\n', text)
    text = text.strip()

    text = re.sub(r'\n', '', text)

    # elimina possibilita di parola.parola ma senza considerare i numeri decimali, ad esempio "3.14" non deve essere modificato, ma "parola.parola" deve diventare "parola. parola"
    text = re.sub(r'(?<!\d)\.(?!\d)', '. ', text)

    text = re.sub(r'\[\]\(https?://[^\)]*\)', '', text)

    # [(https://en.wikipedia.org/wiki/Wikipedia:Citationneeded "Wikipedia:Citation needed")]
    text = re.sub(r'\[\(https?://[^\)]*\)\]', '', text)
    # "Mars , Jupiter , Juno " → "Mars, Jupiter, Juno"
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r' ,', ',', text)
    text = re.sub(r' \.', '.', text)

    return text


async def main():
    wikipedia_urls = [
        "https://en.wikipedia.org/wiki/BabelNet",
        "https://en.wikipedia.org/wiki/Edward_Short,_Baron_Glenamara",
        "https://en.wikipedia.org/wiki/Minerva",
    ]

    data_tot = {}

    browser_config = BrowserConfig(verbose=True, headless=True, java_script_enabled=True)
    run_config = CrawlerRunConfig(
        #css_selector="#mw-content-text .mw-parser-output p, #mw-content-text .mw-parser-output h2, #mw-content-text .mw-parser-output h3",
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=0,
        excluded_tags=["nav", "footer", "header", "aside", "script", "style", "table", "figure", "figcaption"],
        excluded_selector=".noprint, .hatnote, .infobox, .metadata, .navbox, .reflist, .references, .citation, .mw-editsection, .mw-references-wrap",
    )

    # Carica i dati gold standard
    with open('gs.json', 'r', encoding='utf-8') as f:
        gold_data = json.load(f)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=wikipedia_urls, config=run_config)

        i = 0
        for result in results:
            if result.success:

                # ✅ USA la nuova funzione al posto della vecchia clean_markdown
                #print(result.html[:300])
                print("---\n")
                #print(result.cleaned_html[:300])
                

                cleaned_text = parse_markdown_to_clean(result.markdown)  #fit rispetta il selettore CSS, raw è tutto il testo estratto

                data = {
                    "url": result.url,
                    "domain": "en.wikipedia.org",
                    "title": result.metadata.get('title', 'N/A'),
                    "parsed_text": cleaned_text
                }
                data_tot[result.url] = data
                #print(result.metadata)
                
                print("...\n")
                print(result.metadata.get('title', 'N/A'))
                token_level_eval(cleaned_text, gold_data[result.metadata.get('title', 'N/A')]["gold_text"], result.metadata.get('title', 'N/A'))
                

            else:
                print(f"✗ Errore su {result.url}: {result.error_message}")

    with open('wikipedia_data.json', 'w', encoding='utf-8') as f:
        json.dump(data_tot, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Dati salvati in 'wikipedia_data.json' ({len(data_tot)} articoli)")


if __name__ == "__main__":
    asyncio.run(main())
