# views.py
import urllib.parse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse, JsonResponse
from .services.crawlers import (
    linkdin_crawler, remoteok_crawler, indeed_crawler,
    weworkremotely_crawler, timesjobs_crawler, internshala_crawler
)
import requests
import json
import os
import dotenv

dotenv.load_dotenv()
API_KEY = os.getenv('API_KEY')
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3-0324"

SYSTEM_PROMPT = '''
You are an industry expert in job recruitment and a friendly, funny advisor. 
- Only answer job-related queries.
- Be lighthearted, funny, uplifting, and approachable.
- Ask clarifying questions only if absolutely necessary, but focus on giving helpful recommendations.
- Provide multiple job recommendations whenever possible, from different sites on the internet.
- Be professional and concise, but add friendly commentary.
- Include links to the jobs when possible.
- Format each job listing as: Job Title | Company | Location | [Apply Here](link)
'''


def home(request):
    results = []
    selected_site = ""
    job_query = ""
    location = ""
    
    sites = ['linkdin', 'remoteok', 'timesjobs', 'internshala', 'indeed', 'weworkremotely']

    if request.method == "POST":
        job_query = request.POST.get("job", "")
        selected_site = request.POST.get("site", "")
        location = request.POST.get("location", "")

        # Your crawling logic here
        if selected_site == "linkdin":
            results = linkdin_crawler(job_query, location)
        elif selected_site == "remoteok":
            results = remoteok_crawler(job_query)
        elif selected_site == "timesjobs":
            results = timesjobs_crawler(job_query)
        elif selected_site == "internshala":
            results = internshala_crawler(job_query)
        elif selected_site == "indeed":
            results = indeed_crawler(job_query, location)
        elif selected_site == "weworkremotely":
            results = weworkremotely_crawler(job_query)

    return render(request, "home.html", {
        "results": results,
        "selected_site": selected_site,
        "job_query": job_query,
        "location": location,
        "sites": sites,  # <---- important
    })


@csrf_exempt
def chat_bot(request):
    if request.method == "GET":
        return render(request, "chatbot.html")

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        user_input = data.get("message", "")

        def stream():
            with requests.post(
                url=ENDPOINT,
                headers={
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': MODEL,
                    'messages': [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {'role': 'user', 'content': user_input}
                    ],
                    'stream': True
                },
                stream=True
            ) as r:
                for line in r.iter_lines():
                    if line.startswith(b"data: "):
                        chunk = line[len(b"data: "):]
                        if chunk == b"[DONE]":
                            break
                        try:
                            data = json.loads(chunk.decode("utf-8"))
                            delta = data['choices'][0]['delta'].get('content', "")
                            yield delta
                        except:
                            continue

        return StreamingHttpResponse(stream(), content_type='text/html')
