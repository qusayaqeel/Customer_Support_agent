import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage, AIMessage
from agent.nodes import chatbot, input_guardrail

def test_system_prompt_reformulation():
    print("=== Testing System Prompt & Query Reformulation ===")
    
    # 1. حالة أولية: العميل يطلب لابتوب للبرمجة
    state = {
        "messages": [HumanMessage(content="مرحبا بدي لابتوب للبرمجة ميزانيتي 3000")],
        "funnel_stage": "discovery",
        "guardrail_passed": True
    }
    
    print("\nUser: مرحبا بدي لابتوب للبرمجة ميزانيتي 3000")
    print("User: برمجة ويب خفيفة مش ثقيلة")
    
    # 2. نمرر الرسالة للموديل مع التاريخ
    state = {
        "messages": [
            HumanMessage(content="مرحبا بدي لابتوب للبرمجة ميزانيتي 3000"),
            AIMessage(content="يا هلا فيك اخوي شو نوع البرمجة اللي بدك تعملها؟ برمجة ويب ولا برمجة ثقيلة؟"),
            HumanMessage(content="برمجة ويب خفيفة مش ثقيلة")
        ],
        "funnel_stage": "discovery",
        "guardrail_passed": True
    }
    
    result = chatbot(state)
    ai_msg = result["messages"][-1]
    
    # 3. طباعة استجابة الموديل
    if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
        print("\n[SUCCESS] Model decided to call a tool!")
        for tool in ai_msg.tool_calls:
            print(f"Tool Name: {tool['name']}")
            print(f"Tool Arguments: {tool['args']}")
            
            # التأكد من عمل الـ Reformulation
            query = tool['args'].get('query', '')
            print(f"\nOriginal Arabic Intent: للبرمجة ميزانيتي 3000")
            print(f"Reformulated Query sent to DB: {query}")
            
            if "برمجة" in query or "لابتوب" in query and len(query.split()) > 1:
                 print("-> Notice how it converted the conversational Arabic into keywords!")
    else:
        print("\n[INFO] Model replied text instead of calling tool:")
        print(f"Response: {ai_msg.content}")

if __name__ == "__main__":
    test_system_prompt_reformulation()
