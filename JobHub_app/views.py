from django.shortcuts import render
import asyncio
from .services.crawlers import (
    linkdin_crawler, remoteok_crawler, indeed_crawler,
    weworkremotely_crawler, timesjobs_crawler, internshala_crawler
)
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import re
import dotenv
import os

dotenv.load_dotenv

API_KEY = "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"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3-0324"

SYSTEM_PROMPT = '''
You are an industry expert in job recruitment and a friendly, funny advisor. 
- Only answer job-related queries.
- Be lighthearted, funny, uplifting, and approachable in your tone.
- Ask clarifying questions only if absolutely necessary, but focus on giving helpful recommendations.
- Provide multiple job recommendations whenever possible, from different sites on the internet.
- Be professional and concise, but add friendly commentary.
- Include links to the jobs when possible.
- Keep light humor in intro/outro.
- Make the actual listings short, clear, and professional.
- Help the user find opportunities efficiently without overwhelming them with too many questions.
- Format each job listing as: Job Title | Company | Location | [Apply Here](link)
'''



def home(request):
    results = []
    selected_site = ""
    job_query = ""
    loading = False  

    if request.method == "POST":
        job_query = request.POST.get("job", "")
        selected_site = request.POST.get("site", "").lower()
        location = request.POST.get('location')
        loading = True  

        
        if selected_site == 'linkdin':
            results = asyncio.run(linkdin_crawler(job_query , location))
        elif selected_site == 'indeed':
            results = asyncio.run(indeed_crawler(job_query , location))
        elif selected_site == 'remoteok':
            results = asyncio.run(remoteok_crawler(job_query))
        elif selected_site == 'weworkremotely':
            results = asyncio.run(weworkremotely_crawler(job_query))
        elif selected_site == 'timesjobs':
            results = asyncio.run(timesjobs_crawler(job_query))
        elif selected_site == 'internshala':
            results = asyncio.run(internshala_crawler(job_query))
        else:
            results = []

        loading = False  

    return render(request, 'home.html', {
        "results": results,
        "selected_site": selected_site,
        "job_query": job_query,
        "loading": loading,      
    })


@csrf_exempt
def chat_bot(request):
    if request.method == "GET":
        return render(request, "chatbot.html")

    elif request.method == "POST":
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
