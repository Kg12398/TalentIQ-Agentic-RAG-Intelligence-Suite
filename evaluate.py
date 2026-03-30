import json
import os
import sys

# Suppress some noisy warnings if we want
import warnings
warnings.filterwarnings("ignore")

from Generation import build_rag_chain, run_rag_pipeline
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

def run_evaluation():
    dataset_path = "golden_dataset.json"
    output_path = "evaluation_report.md"
    
    if not os.path.exists(dataset_path):
        print(f"ERROR: Could not find {dataset_path}")
        sys.exit(1)
        
    print("Loading Golden Dataset...")
    with open(dataset_path, "r", encoding="utf-8") as f:
        try:
            dataset = json.load(f)
        except json.JSONDecodeError:
            print(f"ERROR: {dataset_path} contains invalid JSON.")
            sys.exit(1)
            
    print(f"Found {len(dataset)} Ground Truth questions.")

    print("\nInitializing TalentIQ RAG Pipeline (High-Speed Groq Engine)...")
    pipeline = build_rag_chain()
    
    print("Initializing LLM Judge (Llama 3.3)...")
    judge_llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.0)
    eval_prompt = PromptTemplate.from_template('''
You are a Staff AI Engineer evaluating a RAG Recruitment Bot.

USER QUESTION: {question}
GROUND TRUTH EXPECTED ANSWER: {expected}
ACTUAL SYSTEM GENERATED ANSWER: {actual}

Task: Compare the ACTUAL answer against the EXPECTED ground truth.
Did the ACTUAL answer correctly capture the meaning of the EXPECTED answer? 
- If the AI contradicted the Ground Truth, output ❌ FAIL.
- If the AI missed critical information, output 📉 PARTIAL.
- If it is semantically equivalent or accurate, output ✅ PASS.

Output FORMAT: <GRADE> - <1 sentence reasoning> (e.g. "✅ PASS - The system correctly identified Neel and Riya.")
    ''')
    eval_chain = eval_prompt | judge_llm | StrOutputParser()

    print(f"\nBeginning Evaluation Loop...\n" + "-"*50)
    
    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write("# 🔬 TalentIQ Automated RAG Evaluation Report\n\n")
        out_f.write("| Q# | User Question | Expected Truth | System Answer | Evaluation Score (LLM-as-a-Judge) |\n")
        out_f.write("|----|---------------|----------------|---------------|-----------------------------------|\n")
        
        passed_count = 0
        
        for idx, row in enumerate(dataset):
            q = row.get('input', '')
            expected = row.get('expected_output', '')
            
            print(f"[{idx+1}/{len(dataset)}] Evaluating: '{q}'")
            
            # 1. Ask TalentIQ
            try:
                result = run_rag_pipeline(q, pipeline=pipeline)
                actual = result.get('answer', "ERROR: No Answer Returned")
            except Exception as e:
                actual = f"PIPELINE CRASH: {str(e)}"
                
            # 2. Grade the Answer
            try:
                grade = eval_chain.invoke({'question': q, 'expected': expected, 'actual': actual})
                if "✅ PASS" in grade:
                    passed_count += 1
            except Exception as e:
                grade = f"EVAL CRASH: {str(e)}"
            
            # Clean newlines for Markdown table formatting
            actual_clean = actual.replace('\n', '<br>')
            grade_clean = grade.replace('\n', ' ')
            
            out_f.write(f"| {idx+1} | {q} | {expected} | {actual_clean} | **{grade_clean}** |\n")
            out_f.flush() # Save in real-time in case of crash
            
    print("-" * 50)
    print(f"\n🎉 Evaluation Complete! Result: {passed_count}/{len(dataset)} PASSED.")
    print(f"A detailed Markdown analysis has been saved to: {output_path}")

if __name__ == "__main__":
    run_evaluation()
