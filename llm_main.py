from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from openai import OpenAI
import configparser
import markdown2
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Set up logging with rotating file handler
log_file = "access_log.txt"
log_handler = RotatingFileHandler(log_file, maxBytes=1 * 1024 * 1024, backupCount=8)  # 1MB per file, keep 8 backups
logging.basicConfig(handlers=[log_handler], level=logging.INFO, format="%(asctime)s - %(message)s")


def log_request(request: Request):
    client_host = request.client.host
    access_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = request.url.path
    logging.info(f"Access Time: {access_time}, Client IP: {client_host}, Accessed Path: {path}")


def load_prompts():
    config = configparser.ConfigParser()
    config.read('config/prompt.ini')
    return config


def load_llm_config():
    llm_config = configparser.ConfigParser()
    llm_config.read('config/llm_config.ini')
    return llm_config


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    log_request(request)
    response = await call_next(request)
    return response


@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    config = load_prompts()
    prompts = config['prompts']
    return templates.TemplateResponse("llm_form.html", {"request": request, "prompts": prompts})


@app.post("/find_patterns", response_class=HTMLResponse)
async def find_patterns(request: Request, text: str = Form(...), prompt_name: str = Form(...)):
    config = load_prompts()
    llm_config = load_llm_config()
    client = OpenAI(base_url=llm_config['settings']['base_url'], api_key=llm_config['settings']['api_key'])

    prompt = config['prompts'][prompt_name]
    completion = client.chat.completions.create(
        model=llm_config['settings']['model'],
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.7,
    )

    results = completion.choices[0].message.content

    # Convert the results to HTML using markdown2
    formatted_results = markdown2.markdown(results)

    return templates.TemplateResponse("llm_results.html", {
        "request": request,
        "results": formatted_results
    })


@app.get("/prompts", response_class=HTMLResponse)
async def get_prompts(request: Request, message: str = "", status: str = ""):
    config = load_prompts()
    prompts = config['prompts']
    return templates.TemplateResponse("llm_prompts.html", {
        "request": request,
        "prompts": prompts,
        "message": message,
        "status": status
    })


@app.post("/save_prompt", response_class=HTMLResponse)
async def save_prompt(request: Request, name: str = Form(...), content: str = Form(...)):
    config = load_prompts()
    config['prompts'][name] = content
    with open('config/prompt.ini', 'w') as configfile:
        config.write(configfile)
    return RedirectResponse(url="/prompts?message=Prompt saved successfully&status=success", status_code=303)


@app.post("/delete_prompt", response_class=HTMLResponse)
async def delete_prompt(request: Request, name: str = Form(...)):
    config = load_prompts()
    if name in config['prompts']:
        config.remove_option('prompts', name)
        with open('config/prompt.ini', 'w') as configfile:
            config.write(configfile)
        return RedirectResponse(url="/prompts?message=Prompt deleted successfully&status=success", status_code=303)
    else:
        return RedirectResponse(url="/prompts?message=Prompt not found&status=error", status_code=303)


@app.get("/llm_settings", response_class=HTMLResponse)
async def get_llm_settings(request: Request, message: str = "", status: str = ""):
    llm_config = load_llm_config()
    base_url = llm_config['settings']['base_url']
    api_key = llm_config['settings']['api_key']
    model = llm_config['settings']['model']
    return templates.TemplateResponse("llm_settings.html", {
        "request": request,
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
        "message": message,
        "status": status
    })


@app.post("/save_llm_settings", response_class=HTMLResponse)
async def save_llm_settings(request: Request, base_url: str = Form(...), api_key: str = Form(...), model: str = Form(...)):
    llm_config = load_llm_config()
    llm_config['settings']['base_url'] = base_url
    llm_config['settings']['api_key'] = api_key
    llm_config['settings']['model'] = model
    with open('config/llm_config.ini', 'w') as configfile:
        llm_config.write(configfile)
    return RedirectResponse(url="/llm_settings?message=Settings saved successfully&status=success", status_code=303)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
