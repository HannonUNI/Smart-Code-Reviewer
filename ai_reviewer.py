#!/usr/bin/env python3
"""
AI-powered code review module.
Requires: openai library and OPENAI_API_KEY environment variable.
"""

import os
from pathlib import Path

def run_ai_review(target_path, prompt_file="ai_prompt.txt"):
    """
    Reads the prompt from a file, appends the code from the target,
    and sends it to OpenAI's GPT model for a review.
    Returns the AI's response as a string, or an error message if unavailable.
    """
    # Check for OpenAI library
    try:
        import openai
    except ImportError:
        return "⚠️  OpenAI library not installed. Run: pip install openai"

    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "⚠️  OPENAI_API_KEY environment variable not set. Skipping AI review."

    # Check prompt file
    prompt_path = Path(prompt_file)
    if not prompt_path.exists():
        return f"⚠️  Prompt file '{prompt_file}' not found. Skipping AI review."

    # Read prompt
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    # Gather all Python source code from target
    target = Path(target_path)
    if target.is_file() and target.suffix == '.py':
        files = [target]
    elif target.is_dir():
        files = list(target.rglob('*.py'))
    else:
        return "⚠️  Invalid target for AI review."

    if not files:
        return "⚠️  No Python files found."

    # Concatenate code with file headers
    code_blocks = []
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            code_blocks.append(f"# File: {file_path}\n{content}")
        except Exception as e:
            code_blocks.append(f"# Error reading {file_path}: {e}")

    full_code = "\n\n".join(code_blocks)

    # Prepare the message
    user_message = f"{prompt_template}\n\nHere is the code to review:\n\n{full_code}"

    # Call OpenAI
    try:
        client = openai.OpenAI(api_key=api_key)  # new client in v1+
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo" for cheaper
            messages=[
                {"role": "system", "content": "You are a senior software engineer reviewing Python code."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ AI review failed: {e}"