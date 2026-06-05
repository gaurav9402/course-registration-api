from fastapi import FastAPI, UploadFile, File, HTTPException
from bs4 import BeautifulSoup
import re

app = FastAPI()

courses = {
    "COSC3506": {
        "course_code": "COSC 3506",
        "title": "Software Systems Development",
        "credits": 3,
        "prerequisites": ["COSC 2007"],
        "cross_listed": ["ITEC 3506"]
    }
}


@app.get("/")
def home():
    return {"message": "Course Registration API is running"}


@app.head("/")
def home_head():
    return


def format_text(text):
    return " ".join(text.strip().split())


def get_course_codes(text):
    text = format_text(text)

    if text == "" or text.lower() == "none":
        return []

    matches = re.findall(r"\b[A-Z]{3,5}\s*\d{4}\b", text.upper())
    course_codes = []

    for match in matches:
        letters = re.search(r"[A-Z]{3,5}", match).group()
        numbers = re.search(r"\d{4}", match).group()
        course_code = letters + " " + numbers

        if course_code not in course_codes:
            course_codes.append(course_code)

    return course_codes


@app.post("/api/v1/admin/catalog/import")
async def import_catalog(file: UploadFile = File(...)):
    file_contents = await file.read()
    html_text = file_contents.decode("utf-8", errors="ignore")

    soup = BeautifulSoup(html_text, "html.parser")
    table = soup.find("table")

    if table is None:
        raise HTTPException(status_code=400, detail="No table found in HTML file")

    rows = table.find_all("tr")
    courses.clear()

    for row in rows[1:]:
        cells = row.find_all("td")

        if len(cells) < 5:
            continue

        course_code = format_text(cells[0].get_text())
        title = format_text(cells[1].get_text())
        credits_text = format_text(cells[2].get_text())
        prerequisites_text = format_text(cells[3].get_text())
        cross_listed_text = format_text(cells[4].get_text())

        try:
            credits = int(credits_text)
        except ValueError:
            credits = 0

        course_info = {
            "course_code": course_code,
            "title": title,
            "credits": credits,
            "prerequisites": get_course_codes(prerequisites_text),
            "cross_listed": get_course_codes(cross_listed_text)
        }

        course_key = course_code.replace(" ", "").upper()
        courses[course_key] = course_info

    return {
        "message": "Catalog imported successfully",
        "total_courses": len(courses)
    }


@app.get("/api/v1/catalog/courses/{course_code}")
def get_course(course_code: str):
    course_key = course_code.replace(" ", "").upper()

    if course_key not in courses:
        raise HTTPException(status_code=404, detail="Course not found")

    return courses[course_key]
