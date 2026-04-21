# Demo Video Script: Code Generation Agent

## Overview

This document provides a script and structure for creating a demo video of the **Code Generation Agent** (Demo 2).

---

## Video Structure

### 1. Introduction (30 seconds)

**Visual:** Title card with project logo

**Script:**
> "Welcome to the Llama Stack Showcase! Today we're demonstrating the Code Generation Agent - an AI-powered coding assistant that generates Python code, executes it safely, and self-corrects when things go wrong."

**Key Points:**
- Project name and purpose
- Focus on Code Generation Agent
- Mention self-correction capability

---

### 2. Setup & Context (45 seconds)

**Visual:** Terminal showing project structure, .env file

**Script:**
> "Before we begin, let's look at our setup. We're using Meta's Llama Stack with Llama 4 Scout via Together AI. The agent has access to a sandboxed workspace and can execute Python code with a 10-second timeout for safety."

**Commands to show:**
```bash
# Show project structure
ls -la

# Show environment setup
cat .env | grep -v API_KEY

# Show the agent code
head -30 demos/code_agent.py
```

**Key Points:**
- Llama Stack framework
- Llama 4 Scout model
- Sandboxed execution environment
- Safety features (timeout)

---

### 3. Demo Part 1: Simple Task (2 minutes)

**Visual:** Terminal running the agent

**Task:** "Create a function to calculate fibonacci numbers"

**Script:**
> "Let's start with a simple task. We'll ask the agent to create a fibonacci function. Watch as it generates code, executes it, and succeeds on the first try."

**Commands:**
```bash
python demos/code_agent.py "Create a function to calculate fibonacci numbers"
```

**Expected Output:**
- Code generation
- Successful execution
- Output showing fibonacci sequence
- File saved message

**Key Points:**
- Show the generated code
- Highlight successful first iteration
- Show the output

---

### 4. Demo Part 2: Self-Correction (3 minutes)

**Visual:** Terminal showing multiple iterations

**Task:** "Create a script that fetches weather data from an API and plots temperature trends"

**Script:**
> "Now let's see the self-correction feature in action. We'll ask for something more complex that might have issues on the first attempt. The agent will detect errors, analyze them, and generate corrected code - up to 3 iterations."

**Commands:**
```bash
python demos/code_agent.py "Create a script that fetches weather data from an API and plots temperature trends"
```

**Expected Flow:**
1. First attempt - might fail (missing imports, API errors)
2. Error analysis shown
3. Second attempt - corrected code
4. Success or another iteration

**Key Points:**
- Show error detection
- Highlight self-correction
- Explain the iteration process
- Show final working code

---

### 5. Demo Part 3: Web UI (2 minutes)

**Visual:** Browser showing Gradio interface

**Script:**
> "The agent is also available through a web interface built with Gradio. Let's see the same functionality in a more user-friendly format."

**Actions:**
1. Open browser to `http://localhost:7860`
2. Click on "Code Agent" tab
3. Enter task: "Generate a CSV parser with pandas"
4. Click "Generate Code"
5. Show results

**Key Points:**
- Web interface convenience
- Same underlying functionality
- Accessible to non-technical users

---

### 6. Technical Deep Dive (2 minutes)

**Visual:** Code editor showing key components

**Script:**
> "Let's look at how this works under the hood. The agent uses three main components: the Llama Stack client for AI, the execution tool for sandboxed code running, and the file I/O tool for workspace management."

**Code to highlight:**

```python
# Client initialization
from src.client import create_client
client = create_client()

# Code generation
response = client.chat_completion(messages, temperature=0.3)

# Safe execution
result = executor.execute_code(code)  # 10s timeout

# Self-correction loop
for i in range(1, max_iterations + 1):
    if result.success:
        break
    else:
        # Generate corrected code
        code = self._generate_code(task, previous_error)
```

**Key Points:**
- Llama Stack client usage
- Sandboxed execution
- Iteration logic
- Error handling

---

### 7. Comparison: Llama Stack vs Raw API (1 minute)

**Visual:** Side-by-side code comparison

**Script:**
> "Notice how clean the Llama Stack code is compared to raw API calls. We get type safety, structured responses, and built-in error handling without manual HTTP management."

**Visual:** Show the comparison table from README

**Key Points:**
- Cleaner code
- Type safety
- Built-in features
- Easier maintenance

---

### 8. Conclusion (30 seconds)

**Visual:** Summary screen with links

**Script:**
> "That's the Code Generation Agent! It demonstrates how Llama Stack enables powerful agentic workflows with minimal code. Check out the GitHub repository for the full source and try it yourself!"

**Call to Action:**
- GitHub link
- Documentation link
- HuggingFace Spaces demo

---

## Recording Tips

### Terminal Setup
```bash
# Use a clean terminal with large font
# Recommended: 18pt+ font size
# Use a dark theme for better visibility

# Clear workspace before recording
rm -rf workspace/*
```

### Browser Setup
```bash
# Open Gradio UI in advance
python src/ui.py &

# Use browser zoom (125-150%) for better visibility
```

### Timing
- Total video length: ~12 minutes
- Each section can be trimmed/edited
- Pause between sections for editing

### Voiceover Tips
- Speak clearly and at moderate pace
- Explain what you're doing as you do it
- Highlight key features
- Keep technical terms accessible

---

## Alternative Demo Ideas

### Quick Demo (5 minutes)
1. Introduction (30s)
2. Simple task (1m)
3. Self-correction (2m)
4. Conclusion (30s)

### Extended Demo (20 minutes)
- Add more complex examples
- Show all three agents
- Include deployment steps
- Q&A section

---

## Resources

- **Main Repository:** https://github.com/yourusername/llama-stack-showcase
- **Llama Stack Docs:** https://github.com/meta-llama/llama-stack
- **Together AI:** https://www.together.ai/
- **Gradio:** https://gradio.app/

---

## Checklist

Before recording:
- [ ] Environment variables set
- [ ] Dependencies installed
- [ ] Workspace cleared
- [ ] Browser zoom set
- [ ] Terminal font sized up
- [ ] Test runs completed
- [ ] Script reviewed

After recording:
- [ ] Audio quality check
- [ ] Video editing
- [ ] Captions added
- [ ] Thumbnail created
- [ ] Description written
- [ ] Tags added
- [ ] Links verified
