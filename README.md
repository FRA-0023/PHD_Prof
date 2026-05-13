# PHD_Prof

Automates the conversion of PDF lecture slides into structured study notes and publishes them to Notion using Gemini.

The repository currently contains a single script, `pdf_to_notion.py`, which:

- asks for the course subject and professor type once per session
- lets you choose a local folder containing PDF files
- finds the matching Notion course and destination database
- uploads each PDF to Gemini, generates notes, and writes them into Notion
- skips files that already have a page with the same title in the target database
- tracks Gemini usage in `gemini_usage.json`

## Requirements

- Python 3.10+ recommended
- A Google Gemini API key
- A Notion integration token
- Access to a Notion page or database used as the root `Courses` container

Install the Python dependencies:

```bash
pip install google-genai python-dotenv requests
```

## Environment Variables

Create a `.env` file in the repository root with:

```env
GEMINI_API_KEY=your_gemini_api_key
NOTION_TOKEN=your_notion_integration_token
NOTION_ROOT_PAGE_ID=your_notion_courses_page_or_database_id
```

`NOTION_ROOT_PAGE_ID` should point to the Notion `Courses` container that holds the course pages/databases the script navigates through.

## Usage

Run the script from the repository root:

```bash
python pdf_to_notion.py
```

Then follow the prompts to:

1. enter the subject name
2. optionally enter a professor role description
3. choose a folder containing PDF files
4. select the target course and database in Notion

The script will process every PDF in the folder automatically.

## Output Format

The Gemini prompt is designed to produce dense study notes with:

- continuous narrative paragraphs instead of bullet lists
- headings up to level 3
- inline math in `$...$`
- display math in `$$...$$`
- bold emphasis where useful

The Notion importer converts that output into native Notion blocks.

## Notes

- Gemini usage is limited by the script to 20 calls per day.
- Processed file names are used as page titles in Notion.
- The script writes usage state to `gemini_usage.json` in the repository root.