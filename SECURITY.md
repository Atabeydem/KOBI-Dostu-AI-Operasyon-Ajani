# Security Checklist

- Do not commit `.env` files.
- Do not hard-code API keys in Python files.
- If an API key is accidentally exposed, delete/revoke it immediately.
- Create a new API key and keep it only in your local `.env` file.
- Before pushing, run:

```bash
git status
git diff --cached
```

- For this hackathon project, prefer creating a clean repository after an accidental public secret exposure.
