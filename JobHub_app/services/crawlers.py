import urllib.parse
from patchright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ---------------------------
# Generic scraper function
# ---------------------------
def scrape_page(url, schema):
    """Generic scraper using Playwright + BeautifulSoup according to a schema."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    results = []
    for element in soup.select(schema["baseSelector"]):
        item = {}
        for field in schema["fields"]:
            node = element.select_one(field["selector"])
            if not node:
                item[field["name"]] = ""
                continue
            if field["type"] == "text":
                item[field["name"]] = node.get_text(strip=True)
            elif field["type"] == "attribute":
                item[field["name"]] = node.get(field["attribute"], "")
        results.append(item)
    return results

# ---------------------------
# Filter function
# ---------------------------
def filter_jobs(jobs, title_keyword=None, location_keyword=None):
    """Filter jobs by title and/or location."""
    filtered = []
    for job in jobs:
        title_match = True
        location_match = True

        if title_keyword:
            title_match = title_keyword.lower() in job.get("title", "").lower()
        if location_keyword:
            location_match = location_keyword.lower() in job.get("location", "").lower()

        if title_match and location_match:
            filtered.append(job)
    return filtered

# ---------------------------
# Individual crawlers
# ---------------------------
def linkdin_crawler(title: str, location: str = ""):
    title_encoded = urllib.parse.quote_plus(title)
    location_encoded = urllib.parse.quote_plus(location + ", India") if location else ""
    url = f"https://www.linkedin.com/jobs/search/?keywords={title_encoded}&location={location_encoded}"
    schema = {
        "baseSelector": "ul.jobs-search__results-list > li",
        "fields": [
            {"name": "title", "selector": "h3.base-search-card__title", "type": "text"},
            {"name": "company", "selector": "h4.base-search-card__subtitle", "type": "text"},
            {"name": "location", "selector": "span.job-search-card__location", "type": "text"},
            {"name": "posted", "selector": "time", "type": "text"},
            {"name": "url", "selector": "a.base-card__full-link", "type": "attribute", "attribute": "href"},
        ],
    }
    return scrape_page(url, schema)

def remoteok_crawler(search_term: str):
    url = f"https://remoteok.com/remote-{search_term}-jobs"
    schema = {
    "baseSelector": "tr.job",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "company", "selector": ".companyLink", "type": "text"},
        {"name": "location", "selector": ".location", "type": "text"},
        {"name": "date", "selector": "time", "type": "text"},
        {"name": "url", "selector": "a.preventLink", "type": "attribute", "attribute": "href"},
    ],
}

    jobs = scrape_page(url, schema)
    for job in jobs:
        if job.get("url", "").startswith("/"):
            job["url"] = f"https://remoteok.com{job['url']}"
    return jobs

def indeed_crawler(title: str, location: str = ""):
    title_encoded = urllib.parse.quote_plus(title)
    location_encoded = urllib.parse.quote_plus(location) if location else ""
    url = f"https://www.indeed.com/jobs?q={title_encoded}&l={location_encoded}"
    schema = {
    "baseSelector": "a.tapItem",  # anchor wrapper for each job card
    "fields": [
        {"name": "title", "selector": "h2.jobTitle span", "type": "text"},
        {"name": "company", "selector": "span.companyName", "type": "text"},
        {"name": "location", "selector": "div.companyLocation", "type": "text"},
        {"name": "date", "selector": "span.date", "type": "text"},
        {"name": "url", "selector": "a.tapItem", "type": "attribute", "attribute": "href"},
    ],
}

    jobs = scrape_page(url, schema)
    for job in jobs:
        if job.get("url", "").startswith("/"):
            job["url"] = f"https://www.indeed.com{job['url']}"
    return jobs

def weworkremotely_crawler(title: str):
    url = f"https://weworkremotely.com/remote-jobs/search?term={title}"
    schema = {
    "baseSelector": "section.jobs li:not(.view-all)",  # avoid header/footer
    "fields": [
        {"name": "title", "selector": "span.title", "type": "text"},
        {"name": "company", "selector": "span.company", "type": "text"},
        {"name": "location", "selector": "span.region", "type": "text"},
        {"name": "posted", "selector": "time", "type": "text"},
        {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
    ],
}

    jobs = scrape_page(url, schema)
    for job in jobs:
        if job.get("url", "").startswith("/"):
            job["url"] = f"https://weworkremotely.com{job['url']}"
    return jobs

def timesjobs_crawler(title: str):
    url = f"https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={title}&txtLocation="
    schema = {
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
    jobs = scrape_page(url, schema)
    for job in jobs:
        if job.get("url", "").startswith("/"):
            job["url"] = f"https://www.timesjobs.com{job['url']}"
    return jobs

def internshala_crawler(title: str):
    url = f"https://internshala.com/internships/{title}-internship"
    schema = {
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
    jobs = scrape_page(url, schema)
    for job in jobs:
        if job.get("url", "").startswith("/"):
            job["url"] = f"https://internshala.com{job['url']}"
    return jobs
