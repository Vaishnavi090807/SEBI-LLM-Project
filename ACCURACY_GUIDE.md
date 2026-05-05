# Accuracy Testing & Optimization Guide

## Overview
This guide helps you measure and improve LLM accuracy to reach 90%+ on investment risk assessment.

---

## Part 1: Setting Up Test Dataset

### 1.1 Create Gold Standard Data
Create a file `test_cases.json` with known outcomes:

```json
[
  {
    "company_name": "Telestone Technologies Ltd",
    "stock_code": "TELESTONE",
    "expected_risk": "HIGH",
    "expected_action": "AVOID",
    "source": "SEBI Order 2023-01",
    "reason": "Fraud and unauthorized trading"
  },
  {
    "company_name": "Parekh Aluminex Limited",
    "stock_code": "PAREKHALM",
    "expected_risk": "MEDIUM",
    "expected_action": "CAUTION",
    "source": "SEBI Warning 2023-05",
    "reason": "Regulatory non-compliance"
  },
  {
    "company_name": "Saradha Group",
    "stock_code": null,
    "expected_risk": "HIGH",
    "expected_action": "AVOID",
    "source": "SEBI Action 2023-01",
    "reason": "Ponzi scheme operator"
  }
]
```

### 1.2 Get Real Test Data
Collect 20-30 SEBI orders with known outcomes:
1. Visit https://www.sebi.gov.in/orders
2. Download PDFs
3. Create test cases with expected outputs
4. Verify by reading original SEBI documents

---

## Part 2: Accuracy Testing

### 2.1 Testing Script
Create `test_accuracy.py`:

```python
#!/usr/bin/env python3
"""
Accuracy testing for SEBI LLM system
Measures precision, recall, and F1 score
"""

import json
import sqlite3
from rag_pipeline import SEBIRAGSystem
from datetime import datetime

class AccuracyTester:
    def __init__(self, test_cases_file='test_cases.json'):
        """Initialize tester with test cases"""
        
        with open(test_cases_file, 'r') as f:
            self.test_cases = json.load(f)
        
        self.results = []
        self.rag = SEBIRAGSystem()
        self.rag.index_sebi_orders()
    
    def extract_metrics(self, response_text):
        """Extract risk level and recommendation from LLM response"""
        
        response_upper = response_text.upper()
        
        # Extract risk level
        risk_level = None
        if "HIGH" in response_upper:
            risk_level = "HIGH"
        elif "MEDIUM" in response_upper:
            risk_level = "MEDIUM"
        elif "LOW" in response_upper:
            risk_level = "LOW"
        
        # Extract recommendation
        recommendation = None
        if "AVOID" in response_upper:
            recommendation = "AVOID"
        elif "CAUTION" in response_upper:
            recommendation = "CAUTION"
        elif "SAFE" in response_upper:
            recommendation = "SAFE"
        
        return risk_level, recommendation
    
    def test_single_case(self, test_case):
        """Test a single case"""
        
        company_name = test_case['company_name']
        expected_risk = test_case['expected_risk']
        expected_action = test_case['expected_action']
        
        print(f"\n📝 Testing: {company_name}")
        print(f"   Expected: {expected_risk} / {expected_action}")
        
        # Get prediction
        advice = self.rag.generate_investment_advice(company_name)
        predicted_risk, predicted_action = self.extract_metrics(advice)
        
        print(f"   Predicted: {predicted_risk} / {predicted_action}")
        
        # Check accuracy
        risk_correct = predicted_risk == expected_risk
        action_correct = predicted_action == expected_action
        
        # Only mark as correct if BOTH are correct
        correct = risk_correct and action_correct
        
        result = {
            'company_name': company_name,
            'expected_risk': expected_risk,
            'predicted_risk': predicted_risk,
            'risk_correct': risk_correct,
            'expected_action': expected_action,
            'predicted_action': predicted_action,
            'action_correct': action_correct,
            'overall_correct': correct,
            'full_response': advice
        }
        
        status = "✅ PASS" if correct else "❌ FAIL"
        print(f"   {status}")
        
        return result
    
    def run_all_tests(self):
        """Run all test cases"""
        
        print("\n" + "="*70)
        print("SEBI LLM ACCURACY TEST SUITE")
        print("="*70)
        print(f"Total test cases: {len(self.test_cases)}\n")
        
        for test_case in self.test_cases:
            result = self.test_single_case(test_case)
            self.results.append(result)
        
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Print accuracy summary"""
        
        total = len(self.results)
        
        # Count correct predictions
        risk_correct = sum(1 for r in self.results if r['risk_correct'])
        action_correct = sum(1 for r in self.results if r['action_correct'])
        overall_correct = sum(1 for r in self.results if r['overall_correct'])
        
        print("\n" + "="*70)
        print("ACCURACY SUMMARY")
        print("="*70)
        
        print(f"\nTotal test cases: {total}")
        print(f"Overall accuracy: {overall_correct}/{total} ({100*overall_correct/total:.1f}%)")
        print(f"  Risk level accuracy: {risk_correct}/{total} ({100*risk_correct/total:.1f}%)")
        print(f"  Recommendation accuracy: {action_correct}/{total} ({100*action_correct/total:.1f}%)")
        
        # Breakdown by risk level
        print(f"\nBreakdown by expected risk level:")
        for risk in ['HIGH', 'MEDIUM', 'LOW']:
            matching = [r for r in self.results if r['expected_risk'] == risk]
            if matching:
                correct = sum(1 for r in matching if r['overall_correct'])
                print(f"  {risk}: {correct}/{len(matching)} ({100*correct/len(matching):.1f}%)")
        
        # Failed cases
        failed_cases = [r for r in self.results if not r['overall_correct']]
        if failed_cases:
            print(f"\nFailed cases ({len(failed_cases)}):")
            for r in failed_cases:
                print(f"  - {r['company_name']}: Expected {r['expected_risk']}, got {r['predicted_risk']}")
    
    def save_results(self):
        """Save detailed results to file"""
        
        filename = f"accuracy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tests': len(self.results),
                'accuracy': sum(1 for r in self.results if r['overall_correct']) / len(self.results),
                'results': self.results
            }, f, indent=2)
        
        print(f"\n✅ Results saved to: {filename}\n")

def main():
    """Run accuracy tests"""
    
    tester = AccuracyTester('test_cases.json')
    tester.run_all_tests()

if __name__ == '__main__':
    main()
```

### 2.2 Run Tests
```bash
python3 test_accuracy.py
```

Expected output:
```
======================================================================
SEBI LLM ACCURACY TEST SUITE
======================================================================
Total test cases: 25

📝 Testing: Telestone Technologies Ltd
   Expected: HIGH / AVOID
   Predicted: HIGH / AVOID
   ✅ PASS

📝 Testing: Parekh Aluminex Limited
   Expected: MEDIUM / CAUTION
   Predicted: MEDIUM / CAUTION
   ✅ PASS
...

======================================================================
ACCURACY SUMMARY
======================================================================

Total test cases: 25
Overall accuracy: 24/25 (96.0%)
  Risk level accuracy: 25/25 (100.0%)
  Recommendation accuracy: 24/25 (96.0%)

Breakdown by expected risk level:
  HIGH: 8/8 (100.0%)
  MEDIUM: 10/10 (100.0%)
  LOW: 6/6 (100.0%)
```

---

## Part 3: Identifying Problems & Solutions

### Issue 1: Risk Level Accuracy Low

**Symptom:** Predicting wrong risk levels (e.g., HIGH as MEDIUM)

**Root Causes:**
1. Ambiguous SEBI order text
2. Poor prompt design
3. Model not finding relevant documents

**Solutions:**

```python
# Solution 1: Improve Prompt Clarity
new_prompt = """You are analyzing SEBI regulatory documents.

IMPORTANT: Use ONLY these guidelines:
- HIGH RISK: Ban, fraud, insider trading, Ponzi scheme, criminal referral
- MEDIUM RISK: Warning, violation, investigation, settlement
- LOW RISK: No SEBI orders found about this company

Document context:
{context}

Respond in this EXACT format:
RISK ASSESSMENT: [HIGH/MEDIUM/LOW]
REASONS: [Cite specific phrases from SEBI document]"""

# Solution 2: Add Few-Shot Examples
prompt_with_examples = """
EXAMPLES:
Example 1 - Telestone: "ban issued, fraud" → HIGH RISK
Example 2 - Company XYZ: "warning issued" → MEDIUM RISK  
Example 3 - Company ABC: "no SEBI orders" → LOW RISK

Now analyze: {company_name}
Context: {context}"""

# Solution 3: Improve Vector Search
# Ensure relevant documents are retrieved
rag.hybrid_search(company_name, top_k=10)  # Increase from 5 to 10
```

### Issue 2: Recommendation Accuracy Low

**Symptom:** Correct risk but wrong AVOID/CAUTION/SAFE

**Root Causes:**
1. Inconsistent mapping: HIGH→AVOID
2. Model generating unexpected wording
3. Extraction logic issues

**Solutions:**

```python
# Create consistent mapping
def map_risk_to_action(risk_level):
    mapping = {
        'HIGH': 'AVOID',
        'MEDIUM': 'CAUTION',
        'LOW': 'SAFE'
    }
    return mapping.get(risk_level, 'UNKNOWN')

# Use deterministic action in prompt
prompt = """
Based on risk assessment, provide recommendation:
- If HIGH risk: Recommendation is "AVOID"
- If MEDIUM risk: Recommendation is "CAUTION"
- If LOW risk: Recommendation is "SAFE"

Risk: {risk_level}
Recommendation: [AUTO-MAPPED]"""

# Better extraction logic
def extract_action(response):
    """More robust extraction"""
    response_upper = response.upper()
    
    # Check for exact phrases
    if "AVOID" in response_upper and "AVOID" not in ["CAVOID", "SAVOID"]:
        return "AVOID"
    elif "CAUTION" in response_upper:
        return "CAUTION"
    elif "SAFE" in response_upper and "SAFE" not in ["UNSAFE"]:
        return "SAFE"
    
    return None
```

### Issue 3: Hallucinations (Making Up Information)

**Symptom:** LLM generates information not in SEBI documents

**Solutions:**

```python
# Solution 1: Add Confidence Scoring
def score_confidence(response, retrieved_docs):
    """Only return predictions with high confidence"""
    
    # Check if response references retrieved documents
    confidence = 0
    for doc in retrieved_docs:
        # Count overlap between doc and response
        doc_words = set(doc.lower().split())
        response_words = set(response.lower().split())
        overlap = len(doc_words & response_words) / len(doc_words)
        confidence = max(confidence, overlap)
    
    return confidence

# Only return if confidence > 0.7
if confidence < 0.7:
    return "Unable to determine - insufficient SEBI information"

# Solution 2: Force Grounding
prompt = """CRITICAL: Respond ONLY with information from SEBI documents.

If the company is NOT mentioned in these documents, respond:
"Company not found in SEBI orders"

Document: {context}

Response:"""

# Solution 3: Validation Against Source
def validate_response(response, source_docs):
    """Ensure all claims are in source docs"""
    claims = extract_claims(response)  # Simple NLP to extract claims
    
    for claim in claims:
        found = any(claim in doc for doc in source_docs)
        if not found:
            return False, claim  # Claim not supported
    
    return True, None
```

---

## Part 4: Optimization Techniques

### A. Prompt Engineering

**Technique 1: Chain-of-Thought**
```python
better_prompt = """
Think step by step:
1. What company are we analyzing? {company_name}
2. What SEBI documents mention this company?
3. What violations or warnings are documented?
4. Based on violations, what's the risk level?
5. Based on risk level, what's the recommendation?

Answer in format:
STEP 1: ...
STEP 2: ...
RISK: ...
RECOMMENDATION: ..."""
```

**Technique 2: Structured Output**
```python
# Request JSON output
prompt = """Respond in JSON format only:
{
  "company": "{company_name}",
  "risk_level": "HIGH/MEDIUM/LOW",
  "violations": ["violation1", "violation2"],
  "recommendation": "AVOID/CAUTION/SAFE",
  "confidence": 0.95,
  "source_quotes": ["quote from SEBI document"]
}"""
```

**Technique 3: Negative Examples**
```python
prompt = """
WRONG APPROACH: Speculating about company future performance
CORRECT APPROACH: Only stating facts from SEBI orders

WRONG: "This company might commit fraud"
CORRECT: "SEBI issued fraud charges against this company on DATE"

Now analyze {company_name} using the CORRECT approach."""
```

### B. Vector Store Optimization

```python
# Technique 1: Better Chunking
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # Smaller for better precision
    chunk_overlap=100,
    separators=[
        "\n\n",  # Paragraph breaks
        "Violation:",  # SEBI document sections
        "Order:",
        "\n",
        "."
    ]
)

# Technique 2: Metadata Filtering
vectorstore.similarity_search(
    query,
    k=10,
    filter={'risk_level': 'HIGH'}  # Only high-risk orders
)

# Technique 3: Query Expansion
queries = [
    f"fraud violations {company_name}",
    f"SEBI order {company_name}",
    f"ban regulatory action {company_name}",
    f"insider trading {company_name}"
]
all_results = []
for q in queries:
    all_results.extend(vectorstore.similarity_search(q, k=3))
```

### C. Model Selection

**Try different models:**

```python
models_to_test = [
    "mistral:7b",      # Current (good balance)
    "neural-chat:7b",  # Faster, less hallucination
    "openhermes:7b",   # Better for instructions
    "orca:7b"          # Better reasoning
]

for model in models_to_test:
    llm = Ollama(model=model)
    accuracy = test_model(llm)
    print(f"{model}: {accuracy}% accuracy")
```

---

## Part 5: Continuous Improvement

### Feedback Loop

```python
# 1. Log user feedback
class UserFeedback:
    def __init__(self):
        self.feedback_db = 'user_feedback.json'
    
    def log(self, company_name, prediction, correct):
        """Log when user says prediction is wrong"""
        with open(self.feedback_db, 'a') as f:
            json.dump({
                'company': company_name,
                'prediction': prediction,
                'marked_correct': correct
            }, f)

# 2. Mine mistakes for patterns
def analyze_mistakes():
    """Find patterns in incorrect predictions"""
    with open('user_feedback.json') as f:
        feedback = json.loads(f.read())
    
    wrong_predictions = [f for f in feedback if not f['marked_correct']]
    
    # What do they have in common?
    print(f"Total wrong: {len(wrong_predictions)}")
    print(f"Most common: {most_common_companies(wrong_predictions)}")

# 3. Retrain on mistakes
def improve_from_feedback():
    """Use feedback to improve prompts/models"""
    mistakes = analyze_mistakes()
    
    # Create new test cases from mistakes
    for mistake in mistakes:
        # Add to training data
        # Fine-tune model or adjust prompts
        pass
```

---

## Part 6: Measuring Success

### Key Metrics

| Metric | Target | How to Measure |
|--------|--------|-----------------|
| Overall Accuracy | 90%+ | test_accuracy.py |
| Risk Level Accuracy | 95%+ | Confusion matrix |
| Recommendation Accuracy | 85%+ | Correct AVOID/CAUTION/SAFE |
| Precision (False Positives) | 95%+ | Don't warn about safe companies |
| Recall (False Negatives) | 90%+ | Don't miss fraud companies |
| Latency | <10 sec | Response time |
| Hallucination Rate | <5% | % of info not in SEBI docs |

### Confusion Matrix

```python
from sklearn.metrics import confusion_matrix, classification_report
import numpy as np

# After testing
y_true = [r['expected_risk'] for r in results]
y_pred = [r['predicted_risk'] for r in results]

print(confusion_matrix(y_true, y_pred))
print(classification_report(y_true, y_pred))
```

---

## Part 7: Scaling to 90%+ Accuracy

### Roadmap

**Week 1:** Basic accuracy testing
- [ ] Create test cases (20-30)
- [ ] Run baseline tests
- [ ] Measure current accuracy

**Week 2:** Identify problems
- [ ] Analyze failed cases
- [ ] Find patterns
- [ ] Root cause analysis

**Week 3:** Implement solutions
- [ ] Better prompts
- [ ] Improved chunking
- [ ] Try different models

**Week 4:** Validation
- [ ] Retest on same cases
- [ ] Test on new cases
- [ ] Measure final accuracy

---

## Part 8: Production Checklist

Before deploying:

- [ ] Accuracy ≥ 90% on test set
- [ ] Accuracy ≥ 85% on new unseen data
- [ ] Latency < 15 seconds per query
- [ ] No major hallucinations (<5%)
- [ ] Handles edge cases (missing data, unclear docs)
- [ ] Error messages are helpful
- [ ] User feedback mechanism in place
- [ ] Monitoring/logging enabled

---

This systematic approach will help you reach and maintain 90%+ accuracy!
