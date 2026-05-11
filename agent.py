import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

from tools import ALL_TOOLS, TOOL_FUNCTIONS

load_dotenv()
client = Anthropic()
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

SYSTEM_PROMPT = """You are a research agent that produces structured reports on topics in commerce, food delivery, and quick commerce.
When given a topic, your job is to:
1. Search for relevant information using web_search
2. Fetch the most promising URLs to read their content
3. Save key facts as notes using save_note as you find them
4. Once you have enough information (typically 3-5 useful sources), produce a final structured report

The final report should have these sections:
- Executive summary (2-3 sentences)
- Key facts (bullet points)
- Sources used

Work efficiently. Don't search the same query twice. If a search returns no results, try different wording."""
MAX_TURNS = 15  # safety limit so the agent can't loop forever


def run_agent(user_request: str):
    """Run the agent loop. Returns the final response from Claude."""
    
    # The conversation history. Grows as the agent works.
    conversation = [{"role": "user", "content": user_request}]
    
    for turn in range(MAX_TURNS):
        print(f"\n{'='*60}\n[Turn {turn + 1}]")
        
        # Ask Claude what to do next
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            ## stop_sequences=["##"],
            tools=ALL_TOOLS,
            messages=conversation,  # ← this
        )
        
        # Append Claude's response to the conversation history.
        # Note: we pass response.content directly — it's already a list of blocks.
        conversation.append({"role": "assistant", "content": response.content})
        
        # Inspect what Claude did
        print(f"Stop reason: {response.stop_reason}")
        
        # If Claude wants to use tools, run them and feed results back
        if response.stop_reason == "tool_use":
            tool_results = []
            
            for block in response.content:
                if block.type == "text":
                    print(f"[Claude says] {block.text}")
                
                elif block.type == "tool_use":
                    print(f"[Tool call] {block.name}({json.dumps(block.input)[:200]})")
                    
                    # Run the tool
                    fn = TOOL_FUNCTIONS[block.name]
                    try:
                        result = fn(block.input)
                        result_text = json.dumps(result)[:1000]
                    except Exception as e:
                        result_text = f"Tool error: {str(e)}"
                    
                    print(f"[Tool result] {result_text[:200]}...")
                    
                    # Each tool call needs a matching tool_result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })
            
            # Add ALL tool results in a single user message
            conversation.append({"role": "user", "content": tool_results})
            
            # Continue the loop — Claude will see results and decide what's next
            continue
        
        # If Claude is done, exit the loop
        if response.stop_reason == "end_turn":
            print("\n[Agent finished]")
            
            # Print the final text answer
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
            
            return final_text
        
        # Defensive: handle other stop reasons
        print(f"[Unexpected stop_reason: {response.stop_reason}]")
        return None
    
    print(f"\n[Hit MAX_TURNS={MAX_TURNS} without finishing]")
    return None


if __name__ == "__main__":
    request = "Give me a brief on the current state of quick commerce in India — players, market size, and why it's working."
    ## request = "Write me a 1-page strategic memo on whether a new q-commerce entrant could succeed in Mumbai. Address market saturation, unit economics, and likely incumbent response."
    print(f"User request: {request}\n")
    final_report = run_agent(request)

    
    
    if final_report:
        print("\n" + "="*60)
        print("FINAL REPORT:")
        print("="*60)
        print(final_report)