"""Builds static/sample-handbook.pdf, the demo document behind "Try the sample handbook".

The company is made up. Run from the project folder:
    python scripts/make_sample_pdf.py
"""
from pathlib import Path

import pymupdf

OUTPUT = Path(__file__).resolve().parent.parent / "static" / "sample-handbook.pdf"

PAGES = [
    """
    <h1>Harbor Lane Studio: Team Handbook</h1>
    <p><i>A fictional company handbook, used as a demo document.</i></p>
    <h2>1. Who we are</h2>
    <p>Harbor Lane Studio is a design and software studio with 42 people across two offices,
    in Pune and Bengaluru. We build websites and mobile apps for small businesses and
    non-profits. This handbook explains how we work together. It applies to everyone on a
    permanent contract from their first day.</p>
    <h2>2. Working hours</h2>
    <p>Our core hours are 10:30 to 16:30, Monday to Friday. Everyone should be reachable during
    core hours. Outside them, you can plan your day as you like, as long as you work 40 hours a
    week on average. Meetings are only booked inside core hours.</p>
    <h2>3. Working from home</h2>
    <p>You can work from home up to three days a week. Tell your team lead which days by Friday
    of the week before. Every team spends Wednesday together in the office. New joiners work
    from the office for their first four weeks so they can learn how the team works.</p>
    <p>The studio pays a home-office allowance of Rs 2,000 a month towards internet and
    electricity. It is added to your salary automatically.</p>
    """,
    """
    <h2>4. Paid leave</h2>
    <p>Everyone gets 24 days of paid leave a year, plus the 10 public holidays on the studio
    calendar. Leave builds up at two days per month. You can carry up to 6 unused days into the
    next year; anything above that is lost on 31 March.</p>
    <p>Request leave in the HR portal at least two weeks ahead for anything longer than three
    days. Shorter leave needs two working days' notice.</p>
    <h2>5. Sick leave</h2>
    <p>You get 10 days of paid sick leave a year, separate from paid leave. For an absence of
    more than two days in a row, upload a doctor's note to the HR portal when you return.</p>
    <h2>6. Parental leave</h2>
    <p>Birth mothers get 26 weeks of paid leave. Other parents, including adoptive parents,
    get 4 weeks of paid leave, which can be taken any time in the first year.</p>
    <h2>7. Learning budget</h2>
    <p>Each person has a learning budget of Rs 25,000 a year for courses, books and
    conferences. Ask your team lead before booking anything over Rs 10,000.</p>
    """,
    """
    <h2>8. Travel and expenses</h2>
    <p>Book work travel through the travel desk at least seven days ahead. Train travel is
    preferred for trips under eight hours.</p>
    <p>To claim an expense, submit it in the expenses app with a photo of the receipt within
    30 days of spending the money. Claims are paid with the next month's salary. Meals while
    travelling are covered up to Rs 1,500 a day. Alcohol is never reimbursed.</p>
    <h2>9. Equipment</h2>
    <p>Everyone receives a laptop on their first day. Laptops are replaced every four years,
    or sooner if they stop working. Report lost or stolen equipment to IT within 24 hours.</p>
    <h2>10. Getting help</h2>
    <p>Questions about pay or leave go to people@harborlane.example. Problems with laptops or
    accounts go to it@harborlane.example. Anything you would rather raise in confidence can go
    to the operations director directly.</p>
    """,
]

CSS = """
body { font-family: sans-serif; font-size: 11pt; line-height: 1.45; }
h1 { font-size: 20pt; margin-bottom: 4pt; }
h2 { font-size: 13pt; margin-top: 14pt; margin-bottom: 4pt; }
p { margin-top: 0; margin-bottom: 8pt; }
"""


def main():
    pdf = pymupdf.open()
    for html in PAGES:
        page = pdf.new_page(width=595, height=842)  # A4
        page.insert_htmlbox(pymupdf.Rect(60, 60, 535, 790), html, css=CSS)
    pdf.set_metadata({"title": "Harbor Lane Studio: Team Handbook (sample)"})
    pdf.subset_fonts()  # keep only the letters used, so the file stays small
    OUTPUT.write_bytes(pdf.tobytes(garbage=3, deflate=True))
    pdf.close()
    print("Wrote", OUTPUT)


if __name__ == "__main__":
    main()
