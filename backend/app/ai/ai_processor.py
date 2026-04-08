# backend/app/ai/ai_processor.py
import json
import os
import re
from groq import Groq, BadRequestError

from app.ai.conversation_manager import ConversationManager
from app.ai.tool_registry import ToolRegistry
from app.ai.jarvis_personality import SYSTEM_PROMPT as _DEFAULT_SYSTEM_PROMPT

_MODEL = "llama-3.3-70b-versatile"
_MAX_TOOL_ROUNDS = 5  # prevent infinite tool-call loops


class AIProcessor:
    """
    Core AI brain: receives text, runs an LLM turn (with optional tool calls),
    and returns the assistant's final text response.
    """

    def __init__(
        self,
        api_key: str,
        tool_registry: ToolRegistry = None,
        conversation_manager: ConversationManager = None,
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    ):
        self.client = Groq(api_key=api_key)
        self.tool_registry = tool_registry or ToolRegistry()
        self.conversation = conversation_manager or ConversationManager()
        self.system_prompt = system_prompt

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def process(self, user_text: str) -> str:
        """
        Process a user message and return Marvin's response.

        Steps:
          1. Persist user turn.
          2. Build messages list (system + history).
          3. Call LLM, iterate tool rounds if needed.
          4. Persist and return final assistant reply.
        """
        self.conversation.add_message("user", user_text)

        messages = self._build_messages()
        tools = self.tool_registry.get_tools_schema()
        use_tools = bool(tools)

        for round_idx in range(_MAX_TOOL_ROUNDS):
            kwargs = dict(model=_MODEL, messages=messages, temperature=0.2, max_tokens=1024)
            if use_tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            try:
                response = self.client.chat.completions.create(**kwargs)
            except BadRequestError as e:
                err_str = str(e)
                if "tool_use_failed" in err_str or "failed_generation" in err_str:
                    # Try to salvage the malformed tool call and execute it directly
                    tool_result = self._try_execute_failed_tool(err_str)
                    if tool_result:
                        print(f"AIProcessor: executed salvaged tool call → {tool_result[:80]}")
                        # Ask the model to summarise the result in natural language
                        summary_msgs = self._build_messages()
                        summary_msgs.append({
                            "role": "user",
                            "content": f"Resultado da ação: {tool_result}. Responda ao usuário em português de forma natural.",
                        })
                        summary = self.client.chat.completions.create(
                            model=_MODEL, messages=summary_msgs,
                            temperature=0.2, max_tokens=256,
                        )
                        reply = summary.choices[0].message.content or tool_result
                    else:
                        print(f"AIProcessor: tool_use_failed, retrying without tools.")
                        fallback = self.client.chat.completions.create(
                            model=_MODEL,
                            messages=self._build_messages(),
                            temperature=0.2,
                            max_tokens=512,
                        )
                        reply = fallback.choices[0].message.content or ""
                    self.conversation.add_message("assistant", reply)
                    return reply
                raise

            choice = response.choices[0]
            message = choice.message

            # Detect leaked raw function-call tags in content (model quirk)
            if not message.tool_calls and message.content and re.search(
                r"<function=\w+", message.content
            ):
                # Strip the leaked tag and retry without tools to get a clean reply
                clean_messages = self._build_messages()
                clean_messages.append({
                    "role": "user",
                    "content": "Responda em texto simples, sem usar chamadas de função.",
                })
                fallback = self.client.chat.completions.create(
                    model=_MODEL, messages=clean_messages, temperature=0.7, max_tokens=512
                )
                reply = fallback.choices[0].message.content or ""
                self.conversation.add_message("assistant", reply)
                return reply

            # No tool calls → final answer
            if not message.tool_calls:
                reply = message.content or ""
                self.conversation.add_message("assistant", reply)
                return reply

            # Append assistant message with tool_calls to the in-flight list
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                }
            )

            # Execute each tool call and append results
            for tc in message.tool_calls:
                tool_result = self.tool_registry.execute(
                    tc.function.name, tc.function.arguments
                )
                print(f"AIProcessor: tool '{tc.function.name}' → {tool_result[:120]}")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_result,
                    }
                )

            # Nudge: tell the model to stop calling tools and respond in text
            messages.append({
                "role": "user",
                "content": "Responda agora em texto com base nos resultados acima. Não chame mais ferramentas.",
            })

        # Fallback: ask LLM to summarise without more tool calls
        messages.append(
            {
                "role": "user",
                "content": "Por favor, responda com base nas informações obtidas acima.",
            }
        )
        final_response = self.client.chat.completions.create(
            model=_MODEL, messages=messages, temperature=0.7, max_tokens=512,
        )
        reply = final_response.choices[0].message.content or ""
        self.conversation.add_message("assistant", reply)
        return reply

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_messages(self) -> list[dict]:
        """Build the full messages list: system prompt + conversation history."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.conversation.get_history())
        return messages

    def _try_execute_failed_tool(self, error_str: str) -> str | None:
        """
        When Groq returns tool_use_failed, parse the malformed tool call
        from the failed_generation field and execute it directly.

        Handles patterns like:
          <function=open_application{"app_name":"calculadora"}</function>
          <function=search_web>{"query": "python"}</function>
        """
        # Locate the function name
        name_match = re.search(r'<function=(\w+)', error_str)
        if not name_match:
            return None
        tool_name = name_match.group(1)

        if not self.tool_registry.has_tool(tool_name):
            print(f"AIProcessor: salvage — tool '{tool_name}' not in registry.")
            return None

        # Search for JSON *after* the function name to avoid grabbing the outer error dict
        after_name = error_str[name_match.end():]
        args_match = re.search(r'\{[^<>]*\}', after_name)   # stop before </function>
        args_str = args_match.group(0) if args_match else "{}"

        # Fix common malformation: missing closing brace
        open_b  = args_str.count('{')
        close_b = args_str.count('}')
        args_str += '}' * max(0, open_b - close_b)

        try:
            args = json.loads(args_str)
        except json.JSONDecodeError:
            args = {}

        print(f"AIProcessor: salvaging '{tool_name}' with args={args}")
        return self.tool_registry.execute(tool_name, args)
