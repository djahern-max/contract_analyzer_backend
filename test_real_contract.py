# test_real_contract.py
import asyncio
import os
from dotenv import load_dotenv
from services.contract_analyzer import ContractAnalyzer
import json


async def test_contract_analysis():
    """Test analyzing a real contract from Digital Ocean"""

    # Load environment variables
    load_dotenv()

    # Initialize analyzer
    analyzer = ContractAnalyzer()

    # Test with the renamed master contract from 2305 - a substantial contract document
    contract_file = "2305/Test.pdf"

    print(f"🚀 Testing contract analysis with: {contract_file}")
    print("=" * 50)

    # Analyze the contract
    result = await analyzer.analyze_contract_from_do_spaces(contract_file)

    if result["success"]:
        print("\n🎉 SUCCESS! Contract analyzed successfully!")
        print(f"📄 Text extracted: {result['text_length']} characters")

        print("\n📋 SUMMARY ANALYSIS:")
        summary = result["analysis"]["summary"]
        print(json.dumps(summary, indent=2))

        print("\n⚠️ RISK ANALYSIS:")
        risks = result["analysis"]["risks"]
        print(json.dumps(risks, indent=2))

        print("\n📄 TERMS ANALYSIS:")
        terms = result["analysis"]["terms"]
        print(json.dumps(terms, indent=2))

        print("\n" + "=" * 50)
        print("✅ READY FOR QUESTIONS!")

        # Test question answering
        test_questions = [
            "What type of contract is this?",
            "Who are the parties involved?",
            "What is the contract value?",
            "What are the main risks?",
        ]

        print("\n🤔 Testing question answering:")
        for question in test_questions:
            print(f"\nQ: {question}")
            answer = await analyzer.answer_question(result["analysis"], question)
            print(f"A: {answer}")

        return True

    else:
        print(f"\n❌ FAILED: {result['error']}")
        return False


if __name__ == "__main__":
    asyncio.run(test_contract_analysis())
