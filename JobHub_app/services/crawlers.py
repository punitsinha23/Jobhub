import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote_plus
'''from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager'''



def format_date(date_str: str) -> str:
    """
    Try to format dates from LinkedIn, Internshala, and RemoteOK consistently.
    - Handles ISO dates (RemoteOK)
    - Handles '2 days ago', 'Few hours ago' (LinkedIn, Internshala)
    - Falls back to original string if parsing fails
    """
    if not date_str or date_str == "Unknown":
        return "Unknown"

    # RemoteOK ISO format
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except:
        pass

    # LinkedIn & Internshala relative text like "2 days ago"
    if "day" in date_str or "hour" in date_str or "minute" in date_str or "Just" in date_str:
        return date_str.strip()

    # Try generic parsing
    try:
        dt = datetime.strptime(date_str, "%d %b %Y")
        return dt.strftime("%d %b %Y")
    except:
        return date_str.strip()


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
            "posted": format_date(posted.get_text(strip=True) if posted else "Unknown")
        })

    return jobs


def build_internshala_url(query: str, location: str = "", page: int = 1):
    q = quote_plus(query.lower().replace(" ", "-"))
    loc = quote_plus(location.lower().replace(" ", "-")) if location else ""
    
    if loc:
        url = f"https://internshala.com/internships/{q}-internship-in-{loc}/"
    else:
        url = f"https://internshala.com/internships/{q}-internship/"
    
    if page > 1:
        url += f"page-{page}/"
    
    return url


def internshala_crawler(query: str, location: str = "", page: int = 1):
    url = build_internshala_url(query, location, page)
    print("Fetching:", url)

    r = requests.get(url, headers=HEADERS, timeout=15)
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
        link = "https://internshala.com" + title_tag["href"] if title_tag else "#"

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "stipend": stipend,
            "duration": duration,
            "posted": format_date(posted),
            "url": link
        })

    return jobs


def remoteok_crawler(job: str = "", location: str = "", start: int = 0, per_page: int = 25):
    url = "https://remoteok.com/api"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return []

    jobs = []
    data = r.json()

    for card in data[1:]:
        title = card.get("position", "")
        company = card.get("company", "")
        tags = " ".join(card.get("tags", []))
        description = card.get("description", "")
        posted = card.get("date", "Unknown")
        job_url = card.get("url", "#")

        if job:
            text_blob = f"{title} {company} {tags} {description}".lower()
            if job.lower() not in text_blob:
                continue

        jobs.append({
            "title": title or "No Title",
            "company": company or "Unknown",
            "location": "Remote",
            "url": job_url,
            "posted": format_date(posted)
        })

    return jobs[start:start + per_page]

def timesjobs_crawler(title: str, location: str = "", start_page: int = 1, limit: int = 10):
    url = "https://www.timesjobs.com/candidate/job-search.html"
    params = {
        "searchType": "personalizedSearch",
        "from": "submit",
        "txtKeywords": title,
        "txtLocation": location,
        "sequence": 1,
        "startPage": start_page,
    }

    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print("TimesJobs request failed:", e)
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    cards = soup.find_all("li", class_="clearfix job-bx wht-shd-bx")

    jobs = []
    for card in cards[:limit]:
        try:
            job_title = card.h2.get_text(strip=True) if card.h2 else "No title"

            company_tag = card.find("h3", class_="joblist-comp-name")
            company = company_tag.get_text(strip=True) if company_tag else "Unknown"

            loc_ul = card.find("ul", class_="top-jd-dtl clearfix")
            loc = loc_ul.li.get_text(strip=True) if loc_ul and loc_ul.li else "N/A"

            posted_tag = card.find("span", class_="sim-posted")
            posted = format_date(posted_tag.get_text(strip=True) if posted_tag else "N/A")

            url_tag = card.h2.a
            job_url = url_tag["href"] if url_tag else "#"

            jobs.append({
                "title": job_title,
                "company": company,
                "location": loc,
                "posted": posted,
                "url": job_url
            })

        except Exception as e:
            # Skip card if parsing fails
            print("Skipping a card due to error:", e)
            continue

    return jobs
