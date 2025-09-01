from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import StreamingHttpResponse, JsonResponse
from .services.crawlers import linkedin_crawler, internshala_crawler, remoteok_crawler

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
    job_query = request.GET.get("job", "")
    location = request.GET.get("location", "")
    selected_site = request.GET.get("site", "")
    page = int(request.GET.get("page", 1)) 

    results = []

    if job_query and location and selected_site:
        if selected_site == "linkedin":
            start = (page - 1) * 25
            results = linkedin_crawler(job_query, location, start=start)

        elif selected_site == 'internshala':
            start = (page - 1)* 25
            results = internshala_crawler(job_query, location, start=start)
        elif selected_site == 'remoteok':
            start = (page - 1) * 25
            results = remoteok_crawler(job_query, location, start=0, per_page=25)
    context = {
        "results": results,
        "job_query": job_query,
        "location": location,
        "selected_site": selected_site,
        "page": page,
    }
    return render(request, "home.html", context)


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
