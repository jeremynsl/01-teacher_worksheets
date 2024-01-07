from fastapi import FastAPI, HTTPException, Security, Depends, BackgroundTasks
from pydantic import BaseModel
import markdown
from weasyprint import HTML
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.staticfiles import StaticFiles
import uuid
import os
import time
from dotenv import load_dotenv
from starlette.responses import FileResponse

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

app = FastAPI()
print(API_KEY)


class MarkdownData(BaseModel):
    markdown_content: str


def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")


# Temporary storage directory
TEMP_DIR = "temp_files"


@app.post("/convert/")
async def convert_markdown_to_pdf(
    background_tasks: BackgroundTasks,
    data: MarkdownData,
    api_key: APIKey = Depends(get_api_key),
):
    try:
        # Generate a unique file name
        unique_filename = f"{uuid.uuid4()}.pdf"
        output_filepath = os.path.join(TEMP_DIR, unique_filename)

        # Convert Markdown to HTML and save as PDF
        html_content = markdown.markdown(data.markdown_content)
        HTML(string=html_content).write_pdf(output_filepath)

        # Provide a URL for downloading the file
        download_url = (
            f"https://nutty-anastasia-jeremynsl.koyeb.app/{TEMP_DIR}/{unique_filename}"
        )

        # Schedule file deletion
        background_tasks.add_task(delete_file_after_delay, output_filepath)

        return {"message": "PDF generated successfully", "download_url": download_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def delete_file_after_delay(file_path, delay=300):
    time.sleep(delay)  # Delay in seconds before deletion
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass  # Handle errors


app.mount(f"/{TEMP_DIR}", StaticFiles(directory=TEMP_DIR), name="temp_files")


# app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/static/privacy.txt")
async def read_privacy():
    return FileResponse("static/privacy.txt")
