import requests
from bs4 import BeautifulSoup
from datetime import datetime

def format_remoteok_date(iso_date: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %I:%M %p")  # Example: 21 Aug 2025, 04:00 PM
    except:
        return "Unknown"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36"
    )
}

def linkedin_crawler(job: str, location: str = "", start: int = 0):
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    params = {"keywords": job, "location": location, "start": start}

    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if r.status_code != 200:
        print(f"LinkedIn error: {r.status_code}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []

    for card in soup.select("li"):
        title = card.select_one("h3.base-search-card__title")
        company = card.select_one("h4.base-search-card__subtitle")
        loc = card.select_one("span.job-search-card__location")
        link = card.select_one("a.base-card__full-link")
        posted = card.select_one("time")

        jobs.append({
            "title": title.get_text(strip=True) if title else "No Title",
            "company": company.get_text(strip=True) if company else "Unknown",
            "location": loc.get_text(strip=True) if loc else "",
            "url": link["href"] if link else "#",
            "posted": posted.get_text(strip=True) if posted else "Unknown"
        })

    return jobs

def internshala_crawler(query: str, location: str = "", start: int = 1):
    """
    Crawl Internshala internships based on query and location.
    Returns a list of dicts with title, company, location, stipend, duration, posted date, and URL.
    """
    url = "https://internshala.com/internships"
    params = {
        "q": query,
        "l": location,
        "page": start
    }

    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if r.status_code != 200:
        print(f"Internshala error: {r.status_code}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    jobs = []

    for card in soup.select(".individual_internship"):
        title_tag = card.select_one(".job-internship-name a")
        company_tag = card.select_one(".company-name")
        location_tag = card.select_one(".locations a")
        stipend_tag = card.select_one(".stipend")
        duration_tag = card.select_one(".ic-16-calendar + span")
        posted_tag = card.select_one(".status-success span")

        title = title_tag.get_text(strip=True) if title_tag else "No Title"
        company = company_tag.get_text(strip=True) if company_tag else "Unknown"
        location = location_tag.get_text(strip=True) if location_tag else "Not specified"
        stipend = stipend_tag.get_text(strip=True) if stipend_tag else "Unpaid"
        duration = duration_tag.get_text(strip=True) if duration_tag else "Not mentioned"
        posted = posted_tag.get_text(strip=True) if posted_tag else "Unknown"
        url = "https://internshala.com" + title_tag["href"] if title_tag else "#"

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "stipend": stipend,
            "duration": duration,
            "posted": posted,
            "url": url
        })
   
    return jobs

def remoteok_crawler(query: str, location: str = "", start: int = 0, per_page: int = 25):
    """
    Crawl RemoteOK jobs based on query and optional location.
    Parameters:
        query: job title or keywords
        location: optional location filter
        start: starting index for pagination
        per_page: number of jobs to return per page
    Returns a list of dicts: title, company, location, posted, salary, url
    """
    tags = query.lower().replace(" ", ",")
    url = f"https://remoteok.com/api?tags={tags}"

    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        print(f"RemoteOK error: {r.status_code}")
        return []

    data = r.json()
    jobs = []

    for job in data[1:]: 
        job_location = job.get("location", "Remote")
        if location:
            if location.lower() not in job_location.lower():
                continue

        jobs.append({
            "title": job.get("position", "No Title"),
            "company": job.get("company", "Unknown"),
            "location": job_location,
            "posted": format_remoteok_date(job.get("date", "Unknown")),
            "salary": job.get("salary", "Not specified"),
            "url": "https://remoteok.com" + job.get("url", "#")
        })

    # Handle pagination using start and per_page
    end_idx = start + per_page
    return jobs[start:end_idx]
