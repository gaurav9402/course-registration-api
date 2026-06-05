from fastapi import FastAPI, UploadFile, File, HTTPException
from bs4 import BeautifulSoup

app = FastAPI()

courses = {}


@app.get("/")
def home():
    return {"message": "Course Registration API is running"}


def clean_text(value):
    return value.strip()


def split_course_codes(value):
    value = value.strip()

    if value == "" or value.lower() == "none":
        return []

    codes = []

    parts = value.replace(",", " ").split()

    for i in range(len(parts) - 1):
        possible_code = parts[i] + " " + parts[i + 1]

        if parts[i].isalpha() and parts[i + 1].isdigit():
            codes.append(possible_code)

    return codes


@app.post("/api/v1/admin/catalog/import")
async def import_catalog(file: UploadFile = File(...)):
    contents = await file.read()
    html_text = contents.decode("utf-8", errors="ignore")

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

        course_code = clean_text(cells[0].get_text())
        title = clean_text(cells[1].get_text())
        credits_text = clean_text(cells[2].get_text())
        prerequisites_text = clean_text(cells[3].get_text())
        cross_listed_text = clean_text(cells[4].get_text())

        course = {
            "course_code": course_code,
            "title": title,
            "credits": int(credits_text),
            "prerequisites": split_course_codes(prerequisites_text),
            "cross_listed": split_course_codes(cross_listed_text)
        }

        courses[course_code.replace(" ", "")] = course

    return {
        "message": "Catalog imported successfully",
        "total_courses": len(courses)
    }


@app.get("/api/v1/catalog/courses/{course_code}")
def get_course(course_code: str):
    cleaned_code = course_code.replace(" ", "").upper()

    if cleaned_code not in courses:
        raise HTTPException(status_code=404, detail="Course not found")

    return courses[cleaned_code]