# OpenAI API Setup for Word Document Processing

The system can use OpenAI GPT-4o to intelligently parse Word documents for more accurate data extraction.

## Setup Instructions

### Option 1: Environment Variable (Recommended for production)

**Windows:**
```cmd
setx OPENAI_API_KEY "your-api-key-here"
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Option 2: .env File (Recommended for development)

1. Create a file named `.env` in the project root directory
2. Add your API key:
```
OPENAI_API_KEY=your-api-key-here
```

3. The python-dotenv package will load it automatically (if installed)

## Getting an OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (you won't be able to see it again)
5. Add it using one of the methods above

## Fallback Behavior

**Without OpenAI API Key:**
- The system automatically falls back to table-based extraction
- Still extracts claims from Word documents
- Uses pattern matching and table parsing
- Works well for structured reports

**With OpenAI API Key:**
- More intelligent document understanding
- Better handling of unstructured content
- Can extract context from narrative text
- More accurate claim identification

## Cost Considerations

- GPT-4o costs approximately $0.03 per 1K tokens
- A typical monthly report uses ~15K tokens (~$0.45 per document)
- Fallback extraction is free and works for most structured documents

## Verification

To verify your API key is working:
```python
from document_processor import DocumentProcessor
proc = DocumentProcessor()
result = proc.extract_from_word("path/to/report.docx")
print(f"Extraction method: {result.get('extraction_method')}")
# Should show 'openai_llm' if API key is working
# Or 'fallback' if using basic extraction
```
