from openai.types.chat import ChatCompletionMessageParam
from openai.types.responses import ResponseInputItemParam
from typing import cast

def message_to_input_items(msg: ChatCompletionMessageParam) -> list[ResponseInputItemParam]:
    """
    Convert a ChatCompletionMessageParam to a list of TResponseInputItem.
    
    This is the reverse of Converter.items_to_messages. It handles:
    - user/system/developer messages -> EasyInputMessageParam
    - assistant messages -> EasyInputMessageParam or ResponseOutputMessageParam + tool calls
    - tool messages -> FunctionCallOutput
    """
    role = msg.get("role")
    items: list[ResponseInputItemParam] = []
    
    if role in ("user", "system", "developer"):
        # Simple messages can be converted directly to EasyInputMessageParam
        item: ResponseInputItemParam = cast(ResponseInputItemParam, {
            "role": role,
            "content": msg.get("content", ""),
        })
        items.append(item)
    elif role == "assistant":
        assistant_msg = msg
        content = assistant_msg.get("content")
        tool_calls = assistant_msg.get("tool_calls")
        
        if tool_calls:
            # Assistant message with tool calls needs to be split:
            # 1. If there's content, add it as a message first
            if content:
                item: ResponseInputItemParam = cast(ResponseInputItemParam, {
                    "role": "assistant",
                    "content": content,
                })
                items.append(item)
            
            # 2. Add each tool call as a separate function_call item
            for tool_call in tool_calls:
                if tool_call.get("type") == "function":
                    item: ResponseInputItemParam = cast(ResponseInputItemParam, {
                        "type": "function_call",
                        "call_id": tool_call.get("id", ""),
                        "name": tool_call["function"]["name"],
                        "arguments": tool_call["function"]["arguments"],
                    })
                    items.append(item)
        else:
            # Assistant message without tool calls is simple
            item: ResponseInputItemParam = cast(ResponseInputItemParam, {
                "role": "assistant",
                "content": content or "",
            })
            items.append(item)
    elif role == "tool":
        # Tool message converts to function_call_output
        item: ResponseInputItemParam = cast(ResponseInputItemParam, {
            "type": "function_call_output",
            "call_id": msg.get("tool_call_id", ""),
            "output": msg.get("content", ""),
        })
        items.append(item)
    else:
        raise ValueError(f"Unsupported message role: {role}")
    
    return items