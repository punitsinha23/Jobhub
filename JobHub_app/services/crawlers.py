import json
import urllib.parse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


async def linkdin_crawler(title: str, location: str = ""):
    title_encoded = title.replace(" ", "%20")

    location_encoded = ""
    if location:
        if "," not in location:
            location += ", India"
        location_encoded = location.replace(" ", "%20")

        url = f"https://www.linkedin.com/jobs/search/?keywords={title_encoded}&location={location_encoded}"
    else:
        url = f"https://www.linkedin.com/jobs/search/?keywords={title_encoded}"

    browser_config = BrowserConfig(headless=True)

    schema = {
        'name': 'LinkedIn Job Extractor',
        'baseSelector': 'ul.jobs-search__results-list > li',  
        "fields": [
            {"name": "title", "selector": "h3.base-search-card__title", "type": "text"},
            {"name": "company", "selector": "h4.base-search-card__subtitle", "type": "text"},
            {"name": "location", "selector": "span.job-search-card__location", "type": "text"},
            {"name": "date", "selector": "time", "type": "text"},
            {"name": "url", "selector": "a.base-card__full-link", "type": "attribute", "attribute": "href"},
        ],
    }

    extraction = JsonCssExtractionStrategy(schema)
    run_config = CrawlerRunConfig(extraction_strategy=extraction, cache_mode='bypass')

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        if result.success:
            return json.loads(result.extracted_content)
        else:
            print("Extraction failed:", result.error_message)
            return []


async def remoteok_crawler(search_term: str):
    url = f"https://remoteok.com/remote-{search_term}-jobs"
    browser_config = BrowserConfig(headless=True)

    schema = {
        "name": "RemoteOK Job Extractor",
        "baseSelector": ".job",   
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "company", "selector": ".companyLink", "type": "text"},
            {"name": "location", "selector": ".location", "type": "text"},
            {"name": "date", "selector": "time", "type": "text"},
            {"name": "url", "selector": "a.preventLink", "type": "attribute", "attribute": "href"},
        ],
    }

    extraction = JsonCssExtractionStrategy(schema)
    run_config = CrawlerRunConfig(extraction_strategy=extraction, cache_mode="bypass")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        if not result.success:
            return []
        jobs = json.loads(result.extracted_content)
        # fix relative URLs
        for job in jobs:
            if job.get("url", "").startswith("/"):
                job["url"] = f"https://remoteok.com{job['url']}"
        return jobs


async def indeed_crawler(title: str, location: str = ""):
    title_encoded = urllib.parse.quote_plus(title)
    location_encoded = urllib.parse.quote_plus(location) if location else ""

    url = f"https://www.indeed.com/jobs?q={title_encoded}&l={location_encoded}"

    browser_config = BrowserConfig(headless=True)

    schema = {
            "name": "Indeed Job Extractor",
            "baseSelector": "div.job_seen_beacon",
            "fields": [           
                {"name": "title", "selector": "h2.jobTitle span, h2.jobsearch-JobInfoHeader-title", "type": "text"},
                {"name": "company", "selector": "span.companyName, div[data-company-name='true']", "type": "text"},

                {"name": "location", "selector": "div.companyLocation, div[data-testid='inlineHeader-companyLocation']", "type": "text"},

                {"name": "date", "selector": "span.date", "type": "text"},
                {"name": "url", "selector": "h2.jobTitle a", "type": "attribute", "attribute": "href"},
            ],
        }

    extraction = JsonCssExtractionStrategy(schema)
    run_config = CrawlerRunConfig(extraction_strategy=extraction, cache_mode="bypass")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

        if not result.success:
            print("Extraction failed:", result.error_message)
            return []

        jobs = json.loads(result.extracted_content)

        # Fix relative URLs
        for job in jobs:
            if job.get("url", "").startswith("/"):
                job["url"] = f"https://www.indeed.com{job['url']}"

        return jobs

async def weworkremotely_crawler(title: str):
    url = f"https://weworkremotely.com/remote-jobs/search?term={title}"
    browser_config = BrowserConfig(headless=True)

    schema = {
        "name": "WeWorkRemotely Job Extractor",
        "baseSelector": "li.new-listing-container.feature",
        "fields": [
            {"name": "title", "selector": "h4.new-listing__header__title", "type": "text"},
            {"name": "company", "selector": "p.new-listing__company-name", "type": "text"},
            {"name": "location", "selector": "p.new-listing__company-headquarters", "type": "text"},
            {"name": "posted", "selector": "p.new-listing__header__icons__date", "type": "text"},
            {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
        ],
    }

    extraction = JsonCssExtractionStrategy(schema)
    run_config = CrawlerRunConfig(extraction_strategy=extraction, cache_mode="bypass")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        if not result.success:
            return []
        jobs = json.loads(result.extracted_content)
        for job in jobs:
            if job.get("url", "").startswith("/"):
                job["url"] = f"https://weworkremotely.com{job['url']}"
        return jobs

async def timesjobs_crawler(title: str):
    url = f"https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={title}&txtLocation="
    browser_config = BrowserConfig(headless=True)

    schema = {
        "name": "TimesJobs Extractor",
        "baseSelector": "li.clearfix.job-bx.wht-shd-bx",
        "fields": [
            {"name": "title", "selector": "h2 a", "type": "text"},
            {"name": "company", "selector": "h3.joblist-comp-name", "type": "text"},
            {"name": "skills", "selector": "span.srp-skills", "type": "text"},
            {"name": "experience", "selector": "ul.top-jd-dtl.clearfix li", "type": "text"},
            {"name": "posted", "selector": "span.sim-posted span", "type": "text"},
            {"name": "url", "selector": "h2 a", "type": "attribute", "attribute": "href"},
        ],
    }

    extraction = JsonCssExtractionStrategy(schema)
    run_config = CrawlerRunConfig(extraction_strategy=extraction, cache_mode="bypass")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        if not result.success:
            return []
        jobs = json.loads(result.extracted_content)
        for job in jobs:
            if job.get("url", "").startswith("/"):
                job["url"] = f"https://www.timesjobs.com{job['url']}"
        return jobs

async def internshala_crawler(title: str):
    url = f"https://internshala.com/internships/{title}-internship"
    browser_config = BrowserConfig(headless=True)

    schema = {
        "name": "Internshala Job Extractor",
        "baseSelector": "div.individual_internship",
        "fields": [
            {"name": "title", "selector": "h3.job-internship-name a.job-title-href", "type": "text"},
            {"name": "company", "selector": "p.company-name", "type": "text"},
            {"name": "location", "selector": "div.row-1-item.locations a", "type": "text"},
            {"name": "stipend", "selector": "span.stipend", "type": "text"},
            {"name": "duration", "selector": "div.row-1-item span", "type": "text"},
            {"name": "url", "selector": "h3.job-internship-name a.job-title-href", "type": "attribute", "attribute": "href"},
        ],
    }

    extraction = JsonCssExtractionStrategy(schema)
    run_config = CrawlerRunConfig(extraction_strategy=extraction, cache_mode="bypass")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        if not result.success:
            return []
        jobs = json.loads(result.extracted_content)
        for job in jobs:
            if job.get("url", "").startswith("/"):
                job["url"] = f"https://internshala.com{job['url']}"
        return jobs
