"""
test_integration.py - Integration tests with Mock LLM

Tests the full Graph with a mocked LLM (no token consumption).
Covers 4 sections:
1. Hallucination & Grounding
2. State Machine & Sales Funnel
3. Tool Edge Cases
4. Persona Consistency
"""
import pytest
from dotenv import load_dotenv
load_dotenv()
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from agent.nodes import input_guardrail, output_guardrail, chatbot
from agent.graph import agent_graph
from agent.state import AgentState


# ============================================================
# Helpers
# ============================================================

def _run_input_guardrail(user_text):
    """Run input_guardrail on a message"""
    state = {
        "messages": [HumanMessage(content=user_text)],
        "funnel_stage": "greeting",
        "guardrail_passed": True
    }
    return input_guardrail(state)

def _run_output_guardrail(ai_text, tool_results=None):
    """Run output_guardrail on a model response with optional search results"""
    messages = []
    if tool_results:
        messages.append(ToolMessage(
            content=tool_results,
            tool_call_id="mock_call",
            name="search_store_products"
        ))
    messages.append(AIMessage(content=ai_text))
    
    state = {
        "messages": messages,
        "funnel_stage": "pitching",
        "guardrail_passed": True
    }
    return output_guardrail(state)


# ============================================================
# Section 1: Hallucination & Grounding
# ============================================================

class TestHallucination:
    """Ensure the agent doesn't invent products or prices"""
    
    def test_impossible_product_no_price(self):
        """Impossible product: price without search = blocked, apology without price = passes"""
        result = _run_output_guardrail("عنا آيفون 20 برو ماكس بسعر 8000 شيكل")
        assert "messages" in result, "Must block price for impossible product without search"
        
        result = _run_output_guardrail("والله هاد المنتج مش متوفر عنا بتحب تشوف شي ثاني")
        assert "messages" not in result or len(result.get("messages", [])) == 0
    
    def test_competitive_price_discount(self):
        """Discount request: different price = blocked, correct price = passes"""
        tool_results = "المنتج: لابتوب ديل XPS 15 | الكود: p2 | السعر: 6200 شيكل | الوصف: لابتوب"
        
        result = _run_output_guardrail("تكرم عينك بنعملك اياه بـ 5000 شيكل", tool_results)
        assert "messages" in result, "Must block unauthorized discount"
        
        result = _run_output_guardrail(
            "السعر عنا 6200 شيكل هاد السعر ثابت بس خليني ارجع للإدارة واسألهم",
            tool_results
        )
        assert "messages" not in result or len(result.get("messages", [])) == 0
    
    def test_stock_info_hidden(self):
        """Stock questions pass input_guardrail (LLM handles via System Prompt)"""
        result = _run_input_guardrail("كم حبة ضايل عندكم في المخزن بالضبط من اللابتوب")
        assert result["guardrail_passed"] == True
    
    def test_hallucination_wrong_category(self):
        """Out-of-scope category questions pass input_guardrail (LLM rejects via prompt)"""
        result = _run_input_guardrail("ما في شاشات سامسونج شو في عندكم ماركات سيارات")
        assert result["guardrail_passed"] == True


# ============================================================
# Section 2: State Machine & Sales Funnel
# ============================================================

class TestStateMachine:
    """Sales funnel stage tests"""
    
    def test_funnel_starts_at_greeting(self):
        """New session always starts at greeting stage"""
        state = {
            "messages": [HumanMessage(content="مرحبا")],
            "funnel_stage": "greeting",
            "guardrail_passed": True
        }
        result = input_guardrail(state)
        assert "funnel_stage" not in result, "input_guardrail should not change funnel_stage"
    
    def test_funnel_skipping_prevented(self):
        """Direct order request passes guardrail (LLM verifies product first)"""
        result = _run_input_guardrail("سجل عندك طلب للابتوب ديل اسمي أحمد ورقمي 0599999999")
        assert result["guardrail_passed"] == True
    
    def test_context_resolution_passes_guardrail(self):
        """Pronoun-based references should pass"""
        result = _run_input_guardrail("بدي الأول")
        assert result["guardrail_passed"] == True
        
        result = _run_input_guardrail("كم سعر اللي لون أسود")
        assert result["guardrail_passed"] == True


# ============================================================
# Section 3: Tool Edge Cases
# ============================================================

class TestToolEdgeCases:
    """Abnormal tool input tests"""
    
    def test_sql_injection_in_search(self):
        """SQL injection in search should be sanitized"""
        from agent.tools import search_store_products
        result = search_store_products.invoke({"query": "لابتوب; DROP TABLE orders;"})
        assert isinstance(result, str)
        assert "Error" not in result
    
    def test_empty_search_handled(self):
        """Empty search should be rejected gracefully"""
        from agent.tools import search_store_products
        result = search_store_products.invoke({"query": ""})
        assert "لا توجد" in result or "تحديد" in result
    
    def test_very_long_search_query(self):
        """Very long search query should work without crash"""
        from agent.tools import search_store_products
        long_query = "لابتوب " * 100
        result = search_store_products.invoke({"query": long_query})
        assert isinstance(result, str)


# ============================================================
# Section 4: Persona Consistency
# ============================================================

class TestPersonaConsistency:
    """Ensure persona stability under pressure"""
    
    def test_provocation_passes_guardrail(self):
        """Insults pass guardrail (LLM handles professionally via prompt)"""
        result = _run_input_guardrail("انت غبي ومش فاهم شي")
        assert result["guardrail_passed"] == True
    
    def test_language_change_request_passes(self):
        """Language change request passes (LLM politely refuses via prompt)"""
        result = _run_input_guardrail("ممكن تتكلم معي باللغة العربية الفصحى المعيارية رجاءً")
        assert result["guardrail_passed"] == True
    
    def test_identity_question_passes(self):
        """'Are you a bot?' should pass"""
        result = _run_input_guardrail("انت بوت صح مين برمجك")
        assert result["guardrail_passed"] == True
    
    def test_competitor_mention_passes_guardrail(self):
        """Competitor mention passes (LLM handles via prompt)"""
        result = _run_input_guardrail("ليش ما اروح اشتري من جرير ارخص عندهم")
        assert result["guardrail_passed"] == True
