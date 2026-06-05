import ollama
from typing import List, Optional

class AIGenerator:
    """Handles interactions with Ollama for generating responses"""

    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use the search tool **only** for questions about specific course content or detailed educational materials
- **One search per query maximum**
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.client = ollama.Client(host=base_url)

    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query}
        ]

        kwargs = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools

        response = self.client.chat(**kwargs)

        if response.message.tool_calls and tool_manager:
            return self._handle_tool_execution(response, messages, tool_manager)

        return response.message.content

    def _handle_tool_execution(self, initial_response, messages: List, tool_manager) -> str:
        messages.append(initial_response.message)

        for tool_call in initial_response.message.tool_calls:
            tool_result = tool_manager.execute_tool(
                tool_call.function.name,
                **tool_call.function.arguments
            )
            messages.append({
                "role": "tool",
                "content": tool_result
            })

        final_response = self.client.chat(model=self.model, messages=messages)
        return final_response.message.content
