# HuggingFace Spaces Deployment Guide

This guide explains how to deploy the Llama Stack Showcase to HuggingFace Spaces.

## Quick Deploy

### Option 1: Direct Upload

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Choose:
   - **Space name:** `llama-stack-showcase` (or your preferred name)
   - **SDK:** Gradio
   - **Space hardware:** CPU (free tier)
   - **Visibility:** Public

4. Upload files:
   ```bash
   # Install HuggingFace CLI
   pip install huggingface-hub
   
   # Login
   huggingface-cli login
   
   # Clone your space
   git clone https://huggingface.co/spaces/YOUR_USERNAME/llama-stack-showcase
   
   # Copy project files
   cp -r /app/llama_stack_showcase_0557/* llama-stack-showcase/
   
   # Commit and push
   cd llama-stack-showcase
   git add .
   git commit -m "Initial deployment"
   git push
   ```

### Option 2: GitHub Integration

1. Push code to GitHub
2. Create Space on HuggingFace
3. In Space settings, connect to GitHub repository
4. Select "Gradio" as SDK
5. Set environment variables in Space settings

## Required Files

Ensure these files are in your Space:

```
llama-stack-showcase/
├── app.py              # Entry point (REQUIRED)
├── requirements.txt    # Dependencies (REQUIRED)
├── src/               # Source code
│   ├── __init__.py
│   ├── client.py
│   ├── ui.py
│   └── tools/
├── demos/             # Demo agents
├── workspace/         # Output directory
└── .env              # Environment variables (set via UI)
```

## Environment Variables

Set these in your Space's **Settings > Variables and Secrets**:

| Variable | Value | Secret? |
|----------|-------|---------|
| `TOGETHER_API_KEY` | Your Together AI API key | ✅ Yes |
| `DEFAULT_MODEL` | `meta-llama/Llama-4-Scout-17B-16E-Instruct` | ❌ No |
| `LLAMA_STACK_ENDPOINT` | `https://api.together.xyz/v1` | ❌ No |

### Getting a Together AI API Key

1. Visit [api.together.xyz](https://api.together.xyz/settings/api-keys)
2. Sign up for a free account
3. Generate an API key
4. Copy it to your Space secrets

## Configuration

### app.py

The `app.py` file is the entry point. It must create a `demo` variable:

```python
from src.ui import create_ui
demo = create_ui()
```

### requirements.txt

Key dependencies for HuggingFace Spaces:

```
llama-stack>=0.7.1
llama-stack-client>=0.7.2
gradio>=6.13.0
duckduckgo-search>=8.1.1
python-dotenv>=1.2.0
rich>=15.0.0
```

## Hardware Requirements

### CPU (Free Tier)
- Suitable for all demos
- Response time: 5-15 seconds per request
- Good for: Demonstrations, testing

### GPU (Paid)
- Not required for this showcase
- Llama 4 Scout runs on Together AI's servers
- Local compute is minimal

## Troubleshooting

### Issue: "Module not found"
**Solution:** Ensure `requirements.txt` includes all dependencies

### Issue: "API key not set"
**Solution:** Check that `TOGETHER_API_KEY` is set in Space secrets

### Issue: "Client initialization failed"
**Solution:** 
- Verify API key is valid
- Check Together AI service status
- Review Space logs

### Issue: "Search not working"
**Solution:**
- DuckDuckGo search may be rate-limited
- Try again after a few minutes
- Check Space logs for errors

## Customization

### Changing the Theme

Edit `src/ui.py` to customize the Gradio theme:

```python
import gradio as gr

demo = gr.Blocks(
    theme=gr.themes.Soft(),  # or Default(), Monochrome(), etc.
    title="Your Custom Title"
)
```

### Adding More Tabs

Add new tabs in `create_ui()` function:

```python
with gr.Tab("🆕 New Demo"):
    # Your new demo UI here
    pass
```

### Custom Styling

Add custom CSS in `create_ui()`:

```python
with gr.Blocks(css="""
    .custom-class { ... }
""") as demo:
    # UI components
```

## Monitoring

### View Logs

1. Go to your Space
2. Click "Files" tab
3. View `logs/` directory
4. Or use "Factory Reboot" to restart with fresh logs

### Metrics

Monitor usage in Space settings:
- Request count
- Response times
- Error rates

## Security Best Practices

1. **Never commit API keys**
   - Always use Space secrets
   - Add `.env` to `.gitignore`

2. **Sandbox execution**
   - Code execution is already sandboxed to `workspace/`
   - 10-second timeout prevents runaway processes

3. **Input validation**
   - All file paths are validated
   - Path traversal attacks are blocked

## Updating Your Space

### Automatic Updates (GitHub)

If using GitHub integration:
1. Push changes to GitHub
2. HuggingFace automatically rebuilds

### Manual Updates

```bash
cd llama-stack-showcase
git pull origin main  # or make changes
git add .
git commit -m "Update description"
git push
```

## Sharing Your Space

Once deployed, your Space will be available at:

```
https://huggingface.co/spaces/YOUR_USERNAME/llama-stack-showcase
```

### Embed in Website

```html
<iframe
  src="https://YOUR_USERNAME-llama-stack-showcase.hf.space"
  frameborder="0"
  width="100%"
  height="800"
></iframe>
```

### Share Button

Users can share your Space using the built-in Gradio share button.

## Support

- **HuggingFace Docs:** [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- **Gradio Docs:** [gradio.app/docs](https://gradio.app/docs)
- **Issues:** [GitHub Issues](https://github.com/yourusername/llama-stack-showcase/issues)

## Example Spaces

See the live demo:
🚀 **[Live Demo](https://huggingface.co/spaces/yourusername/llama-stack-showcase)**

---

**Happy deploying! 🚀**
