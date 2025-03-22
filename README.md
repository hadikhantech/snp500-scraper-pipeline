# Stock Market RAG

A repository for scraping stock market data and processing it using RAG (Retrieval Augmented Generation) techniques.

## Setup

1. Clone this repository
2. Create a `.env` file in the root directory based on the `.env.example` file
3. Set your API keys in the `.env` file

```
OPENROUTER_API_KEY=your-actual-api-key-here
HUGGINGFACE_API_KEY=your-actual-api-key-here
```

## Security

- Never commit API keys or sensitive credentials to the repository
- Use environment variables for all API keys
- The `.env` file is included in `.gitignore` to prevent accidental commits