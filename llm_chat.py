#!/usr/bin/env python3
"""
LLM Chat for Automation Builder

Use natural language chat with a local LLM (Ollama) to execute web navigation
commands and actions through your real logged-in browser via the CDP connector.

This is the flagship experience for the Automation Builder repo:
"Talk to your browser" using an LLM that can drive the full power of
the WebBrowserConnector (goto, click, select, keyboard shortcuts, scripts, etc.).

Requirements:
- Ollama running locally (http://localhost:11434) with a capable model
  (recommended: llama3.1, qwen2.5, or mistral)
- Chrome debug session running:
    python browser_connector.py launch-browser

Run:
    python llm_chat.py

The glowing panda will appear while the agent is actively controlling the browser.
"""

import requests
import json
import time
import sys
from typing import Optional, List, Dict, Any

from browser_connector import WebBrowserConnector


class LLMBrowserAgent:
    def __init__(
        self,
        model: str = "llama3.1",
        ollama_url: str = "http://localhost:11434",
        cdp_url: str = "http://localhost:9222",
    ):
        print("Connecting to your live Chrome session...")
        self.conn = WebBrowserConnector(
            cdp_url=cdp_url,
            auto_indicator=True,
            indicator_label="\ud83d\udc3c LLM Agent",
            indicator_actions={
                "goto", "click", "select_option", "fill", "type",
                "keyboard_shortcut", "wait_for_navigation", "execute_script",
                "new_tab", "switch_to_tab", "reload"
            }
        )
        print("Connected. The glowing panda will show during actions.\n")

        self.model = model
        self.ollama_url = ollama_url
        self.conversation: List[Dict[str, str]] = []

        # Strong system prompt that teaches the LLM how to use the browser
        self.system_prompt = """You are an expert web automation agent controlling a real logged-in Chrome browser.

You have access to a powerful browser automation library called Automation Builder (WebBrowserConnector).

Available high-level actions (use these when possible):
- goto(url)
- click(selector)   # supports text=, role=, CSS, etc.
- select_option(option_text, container=optional_trigger)
- fill(selector, value)
- type(selector, text)
- keyboard_shortcut(keys)   # e.g. "Control+L", "Alt+ArrowLeft"
- execute_script(js_code)
- wait_for_navigation(pattern="**/*")
- new_tab(url=None)
- switch_to_tab(index)
- reload()
- get_title(), get_url(), get_tabs(), list_keyboard_shortcuts()

CRITICAL RULES:
1. Always start by calling list_keyboard_shortcuts() if you are unsure what navigation options exist.
2. Prefer keyboard_shortcut and select_option for reliable, human-like control.
3. Use the glowing panda indicator is already handled automatically for you.
4. Be precise with selectors. Use text= or role= when possible.
5. After performing actions, observe the result (page title, visible text, etc.) before deciding the next step.
6. If something fails, try an alternative approach (keyboard instead of click, etc.).
7. You can use multiple actions in sequence before responding to the user.

Response format:
Think step by step, then output one or more actions in this exact format:

ACTION: goto https://example.com
ACTION: select_option "Python" container="Add .gitignore"
ACTION: keyboard_shortcut "Control+L"

Or if you need more information or want to respond to the user:

THOUGHT: I need to understand the current page better.
OBSERVATION: [what you see]
RESPONSE: [your message to the user]

Never invent actions that don't exist in the list above.
"""

    def _call_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Call Ollama chat API."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.9,
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "").strip()
        except Exception as e:
            return f"ERROR: Failed to call LLM ({self.model}): {e}"

    def _parse_actions(self, llm_output: str) -> List[Dict[str, Any]]:
        """Parse ACTION: lines from the LLM response."""
        actions = []
        lines = llm_output.splitlines()
        for line in lines:
            line = line.strip()
            if line.upper().startswith("ACTION:"):
                try:
                    content = line.split(":", 1)[1].strip()
                    # Very simple parser for common patterns
                    if content.lower().startswith("goto "):
                        actions.append({"action": "goto", "url": content[5:].strip()})
                    elif content.lower().startswith("click "):
                        actions.append({"action": "click", "selector": content[6:].strip()})
                    elif content.lower().startswith("select_option "):
                        # Very naive parser
                        parts = content[14:].split("container=")
                        option = parts[0].strip().strip('"\'')
                        container = parts[1].strip().strip('"\'') if len(parts) > 1 else None
                        actions.append({"action": "select_option", "option": option, "container": container})
                    elif content.lower().startswith("fill "):
                        # fill selector "value"
                        actions.append({"action": "fill", "raw": content[5:]})
                    elif content.lower().startswith("keyboard_shortcut "):
                        actions.append({"action": "keyboard_shortcut", "keys": content[18:].strip().strip('"\'')})
                    elif content.lower().startswith("execute_script "):
                        actions.append({"action": "execute_script", "script": content[15:].strip()})
                    else:
                        actions.append({"action": "raw", "command": content})
                except Exception:
                    pass
        return actions

    def execute_action(self, action: Dict[str, Any]) -> str:
        """Execute a parsed action and return observation text."""
        try:
            act = action.get("action")
            if act == "goto":
                url = action["url"]
                self.conn.goto(url)
                return f"Navigated to {self.conn.get_url()}. Title: {self.conn.get_title()}"
            elif act == "click":
                sel = action["selector"]
                self.conn.click(sel)
                return f"Clicked '{sel}'. Current title: {self.conn.get_title()}"
            elif act == "select_option":
                self.conn.select_option(action["option"], container=action.get("container"))
                return f"Selected '{action['option']}'. Current title: {self.conn.get_title()}"
            elif act == "keyboard_shortcut":
                keys = action["keys"]
                self.conn.keyboard_shortcut(keys)
                time.sleep(0.6)
                return f"Sent keyboard shortcut '{keys}'. Current URL: {self.conn.get_url()}"
            elif act == "execute_script":
                result = self.conn.execute_script(action["script"])
                return f"Executed script. Result: {str(result)[:200]}"
            else:
                return f"Unknown or unparsed action: {action}"
        except Exception as e:
            return f"Action failed: {e}"

    def chat_loop(self):
        print("=" * 70)
        print("Automation Builder \u2014 LLM Chat")
        print("Talk naturally. The LLM will drive your real browser.")
        print(f"Model: {self.model}")
        print("Type 'quit' or 'exit' to leave.")
        print("=" * 70)
        print()

        # Seed the conversation
        self.conversation = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Give the LLM an initial observation
        initial_obs = f"Current page: {self.conn.get_url()}\nTitle: {self.conn.get_title()}"
        self.conversation.append({"role": "user", "content": f"Initial state:\n{initial_obs}\n\nHow can I help you automate the web today?"})

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break

                self.conversation.append({"role": "user", "content": user_input})

                # Get response from LLM
                print("\ud83e\udd16 Thinking...")
                llm_response = self._call_ollama(self.conversation)
                print(f"\nAgent:\n{llm_response}\n")

                self.conversation.append({"role": "assistant", "content": llm_response})

                # Parse and execute actions
                actions = self._parse_actions(llm_response)
                if actions:
                    print("Executing actions...")
                    for act in actions:
                        observation = self.execute_action(act)
                        print(f"  \u2192 {observation}")
                        # Feed observation back
                        self.conversation.append({
                            "role": "user",
                            "content": f"Observation after action: {observation}"
                        })

                    # Ask the LLM what to do next based on observations
                    follow_up = self._call_ollama(self.conversation)
                    print(f"\nAgent follow-up:\n{follow_up}\n")
                    self.conversation.append({"role": "assistant", "content": follow_up})

            except KeyboardInterrupt:
                print("\nExiting.")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    agent = LLMBrowserAgent()
    agent.chat_loop()
