# PHD Prof: The Antifragile Document ETL

**If you are manually copying and pasting insights from academic PDFs into Notion, you are burning time and destroying your cognitive bandwidth.**

You already know the standard approach is broken. Basic integration scripts might work for a single file, but they crumble at scale. 

When you process dozens of PDFs, the Notion API will eventually hiccup. A 502 Bad Gateway or a 429 Rate Limit hits, your script crashes, and your workspace is suddenly littered with orphaned, half-broken pages. 

Worse? The tokens you just paid Gemini to generate are gone forever. You have to restart the batch and pay for that inference all over again. 

This is the hidden cost of fragile automation. And this is exactly what **PHD Prof** eliminates.

---

## The Paradigm Shift

PHD Prof is not a simple script. It is a relentless, **Crash-Only ETL pipeline** engineered to ingest academic PDFs, synthesize them via LLM, and inject them into Notion with absolute zero data loss. 

It acts as an automated Senior Analyst that works while you sleep.

Here is how it shifts the paradigm:

### 1. Cryptographic State Tracking (Zero Duplicates)
Standard scripts rely on file names. That is a massive vulnerability. 
PHD Prof calculates the SHA-256 hash of every single PDF. It doesn't care what you named the file. It only triggers a new extraction if the actual underlying data has mutated. It completely eliminates accidental duplicates and unnecessary API calls.

### 2. Decoupled Architecture (Zero Token Waste)
We decoupled the extraction from the load phase. 
When Gemini generates the highly dense study notes, PHD Prof instantly dumps that inference to a local `staging/` disk. If Notion goes down a second later, your data is safe. The system will simply pick up the Markdown file on the next run. You never pay for the same LLM inference twice.

### 3. Self-Healing Rollbacks
If a network error interrupts a Notion sync halfway through, you are usually left with a broken, incomplete page. 
Not anymore. PHD Prof detects interrupted "Syncing" states. On the next execution, it actively hunts down that orphaned Notion page, archives it, and performs a clean rollback before re-uploading the data from the local cache. No manual cleanup required.

---

## Installation & Setup

Stop wasting hours on manual knowledge management. Deploy the pipeline.

### Requirements
- Python 3.10+
- Google Gemini API key
- Notion integration token
- Target Notion Page or Database (Root ID)

```bash
pip install google-genai python-dotenv requests
```

### Configuration
Create a `.env` file in your root directory. This acts as the command center for your integration:

```env
GEMINI_API_KEY=your_gemini_api_key
NOTION_TOKEN=your_notion_integration_token
NOTION_ROOT_PAGE_ID=your_notion_courses_page_or_database_id
```

*Note: The `NOTION_ROOT_PAGE_ID` is the parent container that holds your courses.*

---

## Execution

Fire up the pipeline:

```bash
python pdf_to_notion.py
```

The system will prompt you for:
1. The academic subject.
2. The professor's role (to profile the LLM persona).
3. Your local PDF directory.
4. Your target Notion database.

Once configured, walk away. The system handles the entire batch, manages rate limits (capped at 20 daily calls for safety), and securely writes the state to `sync_state.json`.

Build your knowledge base systematically, without the friction.