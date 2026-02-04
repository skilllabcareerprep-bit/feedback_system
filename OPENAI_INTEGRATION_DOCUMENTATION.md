# OpenAI Integration - Complete Documentation

## Overview
The Training Feedback System uses OpenAI's GPT-3.5-turbo model to analyze feedback responses and generate comprehensive reports.

---

## Files Involved

### 1. **settings.py** (Configuration)
**Location:** `training_feedback_system/training_feedback_system/settings.py` (Line 102-103)

```python
# OpenAI Configuration
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
```

**What it does:**
- Reads the `OPENAI_API_KEY` from environment variables (via .env file or Render Dashboard)
- Sets a default empty string if not provided
- Makes the key available to the entire Django application via `settings.OPENAI_API_KEY`

---

### 2. **utils.py** (Analysis Logic)
**Location:** `training_feedback_system/feedback/utils.py` (Lines 1-90)

#### Function: `analyze_feedback_with_openai(feedback_responses)`

**What it does:**
1. Takes all feedback responses from a training session
2. Prepares formatted feedback text including:
   - Key Learnings
   - Missing Elements
   - Average Rating (on 5-point scale)
3. Sends to OpenAI with a detailed prompt
4. Returns analysis as JSON

**Prompt Template:**
```
You are a qualitative feedback analyst for a training organization.
Analyze the feedback and provide:
1. Overall sentiment (positive/negative/mixed)
2. Key strengths of the session
3. Main areas for improvement
4. Actionable recommendations
5. Concise overall assessment (3-5 sentences)

Output: JSON object with "overall_summary" key
```

**OpenAI API Call:**
```python
client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', None))
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=1500,
    temperature=0.7
)
```

**Returns:**
- Structured JSON with overall summary if API key is configured
- Error message: "OpenAI API key not configured" if key is missing
- Error details: "Error analyzing feedback: {error message}" if API call fails

---

### 3. **models.py** (Data Storage)
**Location:** `training_feedback_system/feedback/models.py` (Lines 150-159)

```python
class FeedbackReport(models.Model):
    session = models.OneToOneField(TrainingSession, on_delete=models.CASCADE)
    openai_analysis = models.TextField(blank=True)  # Stores AI analysis
    word_document = models.FileField(upload_to='reports/', blank=True)
    # ... other fields
```

**What it does:**
- Stores the OpenAI analysis result in the database
- Allows retrieval for viewing and downloading reports

---

### 4. **views.py** (Integration)
**Location:** `training_feedback_system/feedback/views.py` (Lines 365-378)

Function: `download_report(request, session_id)`

**Flow:**
1. Get training session and all feedback responses
2. Call `analyze_feedback_with_openai(feedback_responses)`
3. Pass analysis to `generate_word_report()` for document creation
4. Return downloadable Word document

```python
ai_analysis = analyze_feedback_with_openai(feedback_responses)
report_path, report_filename = generate_word_report(session, feedback_responses, ai_analysis)
```

---

### 5. **Word Report Generation**
**Location:** `training_feedback_system/feedback/utils.py` (Lines 139-186)

Function: `generate_word_report(session, feedback_responses, ai_analysis)`

**What it does:**
1. Creates a professional Word document (.docx)
2. Includes:
   - Session title and trainer information
   - Feedback summary statistics
   - Rating charts and visualizations
   - **OpenAI AI Analysis** (if available)
3. Saves to `/media/reports/` folder
4. Returns document path for download

**Document Sections:**
- Session Header
- Feedback Summary with averages
- Individual feedback responses
- Visual charts for ratings
- **Key Learnings (from OpenAI Analysis)**
- **Recommendations (from OpenAI Analysis)**
- Overall Assessment

---

## Setup Instructions

### Local Development
Your `.env` file should contain:
```dotenv
OPENAI_API_KEY=your-openai-api-key-here
```

Get your key from: https://platform.openai.com/api-keys

### Production (Render)
1. Go to Render Dashboard → Web Service → Environment
2. Add/Update environment variable:
   - **Key:** `OPENAI_API_KEY`
   - **Value:** Your OpenAI API key (from https://platform.openai.com/api-keys)
3. Click Save
4. Click Deploy

⚠️ **Never commit API keys to GitHub!** Always use environment variables.

---

## Error Handling

### Missing API Key
```
Message: "OpenAI API key not configured"
Location: Report will still generate but without AI analysis
Fix: Add OPENAI_API_KEY to environment variables
```

### API Call Failure
```
Message: "Error analyzing feedback: {error details}"
Examples: Rate limiting, Invalid API key, Network error
Fix: Check API key validity and account status
```

### Graceful Degradation
- Reports can be generated without OpenAI analysis
- System shows "OpenAI API key not configured" in report
- Users can still download reports with charts and feedback summaries

---

## How Users Access AI Analysis

### Step 1: Submit Feedback
- Students fill feedback form with ratings and open-ended responses

### Step 2: Admin Downloads Report
- Admin goes to Session Detail
- Clicks "Download Report" button
- System triggers:
  ```
  analyze_feedback_with_openai() → generate_word_report() → Download .docx file
  ```

### Step 3: Open Report
- Opens Word document
- Sees:
  - Feedback Summary
  - Rating Charts
  - **Key Learnings (AI Summary)**
  - **Recommendations (AI Generated)**
  - Statistical Analysis

---

## Current Status ✅

- [x] OpenAI integration code written
- [x] Settings configured in Django
- [x] Models set up for storage
- [x] Views integrated for report generation
- [x] Word document generation with AI analysis
- [ ] **PENDING:** Add API key to Render Dashboard

---

## Next Steps

1. **Add API Key to Render:**
   - Go to Render Dashboard
   - Add `OPENAI_API_KEY` environment variable
   - Deploy

2. **Test Report Generation:**
   - Create training session
   - Collect feedback from students
   - Download report
   - Verify AI analysis appears in Word document

3. **Monitor API Usage:**
   - Each report generation uses ~1,500 tokens
   - Check OpenAI usage at https://platform.openai.com/usage

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Report shows "API key not configured" | Add OPENAI_API_KEY to Render Environment |
| Report generates but no AI analysis | Check API key validity at platform.openai.com |
| API call times out | Check network/Render resources |
| Report download fails | Check `/media/reports/` directory has write permissions |

