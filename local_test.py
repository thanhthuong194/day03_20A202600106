import sys
import os

# Fix path nếu cần
sys.path.append(os.path.abspath("."))

from src.core.openai_provider import OpenAIProvider
from src.tools.bank_tools import fetch_interest_rates
from src.tools.calculate import calculate_savings_interest
from src.agent.agent import ReActAgent


def create_agent():
    llm = OpenAIProvider(
        base_url="https://models.inference.ai.azure.com/",
        model_name="gpt-4o-mini"
    )

    tools = [
        {
            "name": "fetch_interest_rates",
            "description": "Lấy lãi suất ngân hàng. Tham số: bank_name (str), type_rate ('tai_quay' hoặc 'online').",
            "function": fetch_interest_rates
        },
        {
            "name": "calculate_savings_interest",
            "description": "Tính tiền lãi. Tham số: principal (float), rate_percent (float), months (int).",
            "function": calculate_savings_interest
        }
    ]

    agent = ReActAgent(llm=llm, tools=tools, max_steps=10)
    return agent


# =========================
# TEST CASES
# =========================
TEST_CASES = [
    # I. Simple
    {
        "name": "TC01_simple_max_bank",
        "query": "Gửi 100 triệu trong 6 tháng, ngân hàng nào lãi cao nhất?"
    },
    {
        "name": "TC02_simple_max_bank",
        "query": "Tôi có 200 triệu gửi 12 tháng, chọn ngân hàng lãi cao nhất"
    },
    {
        "name": "TC03_online",
        "query": "Gửi tiết kiệm online 50 triệu trong 3 tháng, bank nào tốt nhất?"
    },

    # II. Specific bank
    {
        "name": "TC04_vietcombank",
        "query": "Gửi 100 triệu vào Vietcombank trong 6 tháng thì lãi bao nhiêu?"
    },
    {
        "name": "TC05_techcombank",
        "query": "Tính giúp tôi 300 triệu gửi Techcombank kỳ hạn 12 tháng"
    },
    {
        "name": "TC06_acb",
        "query": "Nếu gửi 150 triệu ở ACB trong 9 tháng thì được bao nhiêu?"
    },

    # III. ABBank 12 months
    {
        "name": "TC07_abbank_12",
        "query": "Tôi muốn gửi 500 triệu vào AB Bank trong 12 tháng"
    },
    {
        "name": "TC08_abbank_12",
        "query": "ABBank lãi suất 12 tháng là bao nhiêu nếu tôi gửi 1 tỷ?"
    },

    # IV. Missing info
    {
        "name": "TC09_missing_months",
        "query": "Gửi 100 triệu thì ngân hàng nào lãi cao nhất?"
    },
    {
        "name": "TC10_missing_principal",
        "query": "Ngân hàng nào có lãi suất cao nhất trong 6 tháng?"
    }
]


def run_tests():
    agent = create_agent()

    print("\n===== RUN LOCAL TEST =====\n")

    for i, test in enumerate(TEST_CASES, 1):
        print(f"--- {test['name']} ---")
        print(f"Query: {test['query']}\n")

        try:
            result = agent.run(test["query"])

            print("Result:")
            print(result)

        except Exception as e:
            print(f"❌ Error: {str(e)}")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    run_tests()
