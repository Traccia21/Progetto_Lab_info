import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

#async indica che la funzione può essere sospesa
#infatti viene chiamata la await successivamente, che indica che la funzione Parsing si mette in pausa in quel punto
async def main():
    # Lista degli URL selezionati per il dominio Wikipedia (English)
    wikipedia_urls = [
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://en.wikipedia.org/wiki/Rome",
    "https://en.wikipedia.org/wiki/Dante_Alighieri",
    "https://en.wikipedia.org/wiki/Climate_change",
    "https://en.wikipedia.org/wiki/Internet"
    ]

    data = {}
    #configurazione del browser
    browser_config = BrowserConfig(verbose=True,headless = False)



    run_config = CrawlerRunConfig(
    # Estrae SOLO il contenuto dell'articolo, ignorando tutto il resto
    css_selector="#mw-content-text",

    # 2. Usa parametri di pulizia nativi più semplici
    #aggiunto '.mw footer' perché faccio riferimento all'elemento html <div class = "mw-footer"...
    excluded_tags=['nav', 'footer', 'header', 'aside', 'script', 'style'],
    
    # 3. Fondamentale: forza il bypass della cache
    cache_mode=CacheMode.BYPASS, 

    # 4. Aspetta il caricamento del div principale di Wikipedia
    wait_for="#mw-content-text",
    
    # 5. Riduci o elimina soglie di parole che scartano il testo
    word_count_threshold=0,
    # Processamento specifico per pulire il markdown
    remove_overlay_elements=True
)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        results = await crawler.arun_many(urls=wikipedia_urls, config=run_config)

        for result in results:
            if result.success:
                # Struttura richiesta dall'Obiettivo 1 e 4
                data = {
                    "url": result.url,
                    "domain": "en.wikipedia.org",
                    "title": result.metadata.get('title', 'N/A'),
                    "html_text": result.html,
                    "parsed_text": result.markdown # Testo pulito in Markdown
                }
                print(result.markdown)
            else:
                # Gestione errore per URL irraggiungibile [cite: 474, 494]
                print(f"Errore su {result.url}: {result.error_message}")
    



if __name__ == "__main__":
    asyncio.run(main())
