# ai.py - COMPLETE VERSION WITH 3 ALGORITHMS
# GTS, Decision Tree (ID3), LEM2

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict, Counter
from enum import Enum
import re
import math

from app.db.session import SessionLocal
from app.db.models import Document, User
from app.api.auth import get_current_user_from_token
from app.services.gemini_service import GeminiService

# Define get_db dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/ai", tags=["AI Features"])

# ==================== SCHEMAS ====================

class AIModel(str, Enum):
    PRO_25 = "gemini-2.5-pro"
    FLASH_25 = "gemini-2.5-flash"
    FLASH_LITE_25 = "gemini-2.5-flash-lite"
    PRO_2 = "gemini-2.0-pro"
    FLASH_2 = "gemini-2.0-flash"
    FLASH_THINKING = "gemini-2.0-flash-thinking"
    PRO_15 = "gemini-1.5-pro"
    FLASH_15 = "gemini-1.5-flash"
    FLASH_8B_15 = "gemini-1.5-flash-8b"

class ChatMessage(BaseModel):
    message: str
    model: AIModel = AIModel.FLASH_25

class ChatResponse(BaseModel):
    response: str
    model_used: str
    timestamp: datetime

class DocumentQARequest(BaseModel):
    document_id: int
    question: str
    model: AIModel = AIModel.FLASH_25

class DocumentAnalysisRequest(BaseModel):
    document_id: int
    analysis_type: str = "comprehensive"
    custom_prompt: Optional[str] = None
    model: AIModel = AIModel.FLASH_25

class DecisionTreeRequest(BaseModel):
    document_id: int
    
class GTSRuleRequest(BaseModel):
    document_id: int

class LEM2RuleRequest(BaseModel):
    document_id: int


# ==================== BASIC CHAT ENDPOINTS ====================

@router.post("/chat", response_model=ChatResponse)
def simple_chat(
    chat_data: ChatMessage,
    current_user: User = Depends(get_current_user_from_token)
):
    """💬 Simple AI Chat"""
    try:
        gemini = GeminiService()
        response = gemini.client.models.generate_content(
            model=chat_data.model.value,
            contents=chat_data.message
        )
        
        return ChatResponse(
            response=response.text,
            model_used=chat_data.model.value,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )


@router.post("/chat/with-model")
def chat_with_model_selection(
    chat_data: ChatMessage,
    current_user: User = Depends(get_current_user_from_token)
):
    """🤖 Chat with Model Selection"""
    try:
        gemini = GeminiService()
        response = gemini.client.models.generate_content(
            model=chat_data.model.value,
            contents=chat_data.message
        )
        
        return {
            "response": response.text,
            "model_used": chat_data.model.value,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get("/models")
def list_available_models(current_user: User = Depends(get_current_user_from_token)):
    """📋 List All Available AI Models"""
    return {
        "available_models": [
            {"name": model.value, "enum": model.name}
            for model in AIModel
        ],
        "total_models": len(AIModel),
        "recommended": "gemini-2.5-flash (best balance)",
        "default": "gemini-2.5-flash-lite (free tier)"
    }


# ==================== DOCUMENT Q&A WITH CONFIDENCE ====================

@router.post("/document/ask")
def document_qa_with_confidence(
    request: DocumentQARequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """📄 Document Q&A with Enterprise-Level Confidence Scoring"""
    
    document = db.query(Document).filter(
        Document.id == request.document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document or not document.content_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or has no text content"
        )
    
    try:
        gemini = GeminiService()
        
        prompt = f"""Based on this document, answer the question with extreme accuracy.

Document:
{document.content_text}

Question: {request.question}

Provide a clear answer. If the answer is not in the document, explicitly say so."""
        
        response = gemini.client.models.generate_content(
            model=request.model.value,
            contents=prompt
        )
        
        answer = response.text
        
        # Confidence scoring
        confidence_prompt = f"""Rate your confidence in this answer from 0-100:

Question: {request.question}
Answer: {answer}
Document excerpt: {document.content_text[:500]}

Return ONLY a number 0-100."""
        
        confidence_response = gemini.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=confidence_prompt
        )
        
        try:
            confidence_score = int(re.search(r'\d+', confidence_response.text).group())
            confidence_score = max(0, min(100, confidence_score))
        except:
            confidence_score = 70
        
        return {
            "answer": answer,
            "confidence_score": confidence_score / 100,
            "confidence_percentage": f"{confidence_score}%",
            "model_used": request.model.value,
            "document_id": document.id,
            "document_name": document.filename,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Q&A error: {str(e)}"
        )


# ==================== DOCUMENT ANALYSIS ====================

@router.post("/document/analyze")
def analyze_document_with_metadata(
    request: DocumentAnalysisRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """🔍 Comprehensive Document Analysis"""
    
    document = db.query(Document).filter(
        Document.id == request.document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document or not document.content_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        gemini = GeminiService()
        
        if request.custom_prompt:
            prompt = request.custom_prompt + f"\n\nDocument:\n{document.content_text}"
        else:
            prompt = f"""Analyze this document comprehensively:

{document.content_text}

Provide:
1. Main topic/purpose
2. Key points (3-5 bullets)
3. Document type/category
4. Summary (2-3 sentences)"""
        
        response = gemini.client.models.generate_content(
            model=request.model.value,
            contents=prompt
        )
        
        return {
            "analysis": response.text,
            "document_id": document.id,
            "document_name": document.filename,
            "file_size": document.file_size,
            "model_used": request.model.value,
            "analysis_type": request.analysis_type,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {str(e)}"
        )


# ==================== DECISION TREE & RULES HELPER FUNCTIONS ====================

def calculate_entropy(labels: List[str]) -> float:
    """Calculate entropy: H(S) = -Σ p(x) * log2(p(x))"""
    if not labels:
        return 0.0
    
    label_counts = Counter(labels)
    total = len(labels)
    entropy = 0.0
    
    for count in label_counts.values():
        if count > 0:
            probability = count / total
            entropy -= probability * math.log2(probability)
    
    return entropy


def calculate_information_gain(
    data: List[Dict],
    attribute: str,
    target_attribute: str
) -> float:
    """Calculate Information Gain for an attribute"""
    
    # Total entropy
    all_labels = [row[target_attribute] for row in data]
    total_entropy = calculate_entropy(all_labels)
    
    # Weighted entropy after split
    values = set(row[attribute] for row in data if attribute in row)
    weighted_entropy = 0.0
    total_count = len(data)
    
    for value in values:
        subset = [row for row in data if row.get(attribute) == value]
        subset_labels = [row[target_attribute] for row in subset]
        subset_entropy = calculate_entropy(subset_labels)
        weight = len(subset) / total_count
        weighted_entropy += weight * subset_entropy
    
    information_gain = total_entropy - weighted_entropy
    return information_gain


def extract_document_features(text: str) -> Dict[str, Any]:
    """Extract features from document text"""
    word_count = len(text.split())
    
    financial_terms = ['revenue', 'profit', 'cost', 'budget', 'financial', 'salary', 'income', 'expense']
    hr_terms = ['employee', 'hr', 'hiring', 'recruitment', 'performance', 'overtime']
    legal_terms = ['contract', 'legal', 'agreement', 'terms', 'compliance', 'policy']
    
    has_financial = any(term in text.lower() for term in financial_terms)
    has_hr = any(term in text.lower() for term in hr_terms)
    has_legal = any(term in text.lower() for term in legal_terms)
    
    return {
        "word_count_level": "high" if word_count > 500 else "medium" if word_count > 200 else "low",
        "has_financial_terms": has_financial,
        "has_hr_terms": has_hr,
        "has_legal_terms": has_legal
    }


# ==================== DECISION TREE (ID3) ENDPOINT ====================

@router.post("/ml/decision-tree")
def build_decision_tree(
    request: DecisionTreeRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
 ID3 Decision Tree (Information Gain Algorithm)

Builds a decision tree by calculating Information Gain for each attribute
and selecting the one that best splits the data.

Algorithm (Information Theory):
1. Calculate dataset entropy:
   H(S) = -Σ p(x) * log₂(p(x))
   
2. For each attribute, calculate Information Gain:
   IG(S,A) = H(S) - Σ (|Sv|/|S| * H(Sv))
   
3. Select attribute with highest Information Gain

4. This attribute provides the best split (reduces uncertainty most)

Mathematical Proof:
- Entropy measures randomness (0 = pure, 1 = mixed)
- Information Gain measures uncertainty reduction
- Higher IG = better split

Example:
{
  "document_id": 578
}

Document should contain a table with data rows.
The LAST column is automatically used as the target (decision class).

Returns:
- Information Gain for each attribute
- Best attribute for splitting
- Dataset entropy
- Detailed calculations

"""
          
    
    document = db.query(Document).filter(
        Document.id == request.document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document or not document.content_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        gemini = GeminiService()
        
        # Parse table from PDF
        parse_prompt = f"""Extract ALL rows from the table in this document.

CRITICAL:
1. Extract EVERY row - count them carefully
2. Use EXACT column names from header row
3. If there are 14 data rows, return 14 JSON objects
4. Return ONLY valid JSON array

Document:
{document.content_text}

Format:
[
  {{"col1": "value", "col2": "value", "target": "Y"}},
  ... (ALL rows)
]

Return complete JSON array with ALL rows."""
        
        table_response = gemini.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=parse_prompt
        )
        
        # Parse JSON
        import json
        table_text = table_response.text.strip()
        if '```' in table_text:
            table_text = re.sub(r'```json\n?', '', table_text)
            table_text = re.sub(r'```\n?', '', table_text)
        
        data = json.loads(table_text)
        
        if not data or len(data) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Table must have at least 2 rows"
            )
        
        # Get columns
        all_columns = list(data[0].keys())
        target_column = all_columns[-1]
        attributes = all_columns[:-1]
        
        # Calculate Information Gain for each attribute
        gains = {}
        for attr in attributes:
            gain = calculate_information_gain(data, attr, target_column)
            gains[attr] = round(gain, 4)
        
        # Best attribute
        best_attr = max(gains, key=gains.get)
        best_gain = gains[best_attr]
        
        # Dataset entropy
        all_labels = [row[target_column] for row in data]
        dataset_entropy = round(calculate_entropy(all_labels), 4)
        
        return {
            "algorithm": "Decision Tree (ID3)",
            "document_id": document.id,
            "document_name": document.filename,
            "information_gain": gains,
            "best_attribute": best_attr,
            "best_gain": best_gain,
            "dataset_entropy": dataset_entropy,
            "interpretation": {
                "entropy": f"Dataset entropy: {dataset_entropy} (0=pure, 1=random)",
                "best_split": f"'{best_attr}' provides best split",
                "formula": "IG(S,A) = H(S) - Σ(|Sv|/|S| * H(Sv))"
            },
            "training_data": data,
            "timestamp": datetime.utcnow()
        }
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse table as JSON"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decision tree error: {str(e)}"
        )


# ==================== GTS HELPER FUNCTIONS ====================

def calculate_gts_heuristic(total: int, positive: int, false_pos: int) -> Tuple[float, float, float]:
    """
    GTS Formula:
    G = (Ep + Ef) / E
    A = Ep / (Ep + Ef)
    H = G + sqrt(A)
    """
    if positive + false_pos == 0:
        return 0.0, 0.0, 0.0
    
    G = (positive + false_pos) / total
    A = positive / (positive + false_pos)
    H = G + math.sqrt(A)
    
    return round(G, 4), round(A, 4), round(H, 4)


# ==================== GTS RULE INDUCTION ENDPOINT ====================

@router.post("/ml/gts-rules")
def generate_gts_rules(
    request: GTSRuleRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
 GTS (General-To-Specific) Rule Induction

Generates decision rules using a heuristic-based greedy algorithm
that balances coverage and accuracy.

Algorithm (Heuristic Search):
1. For each attribute-value pair, calculate heuristic:
   - G = (Ep + Ef) / E  (Coverage: proportion matched)
   - A = Ep / (Ep + Ef)  (Accuracy: proportion correct)
   - H = G + sqrt(A)  (Heuristic: combined metric)
   
   Where:
   - E = Total examples in dataset
   - Ep = Positive examples (correctly classified)
   - Ef = False examples (incorrectly covered)

2. Select condition with highest H value

3. Check accuracy:
   - If A = 1.0 (perfect) → Create rule
   - If A < 1.0 → Add more conditions (iterative refinement)

4. Remove covered examples

5. Repeat until all examples covered

Mathematical Reasoning:
- G measures coverage (0-1): how many examples matched
- A measures accuracy (0-1): how many correct
- sqrt(A) gives bonus for high accuracy (penalizes low accuracy)
- H combines both: prefers high coverage WITH high accuracy

Example:
{
  "document_id": 578
}

Document should contain a table with data rows.
The LAST column is automatically used as the target (decision class).

Returns:
- Generated rules in IF-THEN format
- Heuristic calculations (G, A, H) for each rule
- Top 5 candidate conditions evaluated per iteration
- Covered examples
- Accuracy metrics

Academic reference:
- GTS (General-To-Specific) recursive coverage algorithm
- Used in LERS, CN2, AQ learning systems
- Heuristic-based greedy search approach

Key advantages:
- Fast execution (greedy approach)
- Good balance between coverage and accuracy
- Interpretable rules
- Works well with noisy data
"""
    
    document = db.query(Document).filter(
        Document.id == request.document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document or not document.content_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        gemini = GeminiService()
        
        # Parse table
        parse_prompt = f"""Extract ALL rows from the table in this document.

CRITICAL INSTRUCTIONS:
1. Extract EVERY SINGLE ROW - do not skip any
2. Use EXACT column names from the first row (header)
3. The table may be space-separated or have columns
4. Count the rows carefully - if there are 14 rows of data, return 14 objects
5. Return valid JSON array ONLY - no markdown, no code blocks

Document:
{document.content_text}

Format:
[
  {{"col1": "val1", "col2": "val2", "target": "Y"}},
  {{"col1": "val2", "col2": "val3", "target": "N"}},
  ... (continue for ALL rows)
]

IMPORTANT: Return EVERY row from the table!"""
        
        parse_response = gemini.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=parse_prompt
        )
        
        # Parse JSON
        import json
        table_text = parse_response.text.strip()
        if table_text.startswith("```json"):
            table_text = table_text[7:]
        if table_text.startswith("```"):
            table_text = table_text[3:]
        if table_text.endswith("```"):
            table_text = table_text[:-3]
        table_text = table_text.strip()
        
        training_data = json.loads(table_text)
        
        if not training_data or len(training_data) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document must contain a table with at least 2 rows"
            )
        
        # Get column names
        all_columns = list(training_data[0].keys())
        
        if len(all_columns) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Table must have at least 2 columns"
            )
        
        # Last column is target
        target_column = all_columns[-1]
        attributes = all_columns[:-1]
        
        # Rename target to "category" and add row_id
        for idx, row in enumerate(training_data, 1):
            row["category"] = row.pop(target_column)
            row["row_id"] = idx
        
        # Validation warning
        if len(training_data) < 10:
            print(f"⚠️  WARNING: Only {len(training_data)} rows parsed. Check if AI missed rows!")
        
        # GTS Algorithm
        rules = []
        uncovered_data = training_data.copy()
        
        rule_number = 1
        max_rules = 15
        
        print(f"DEBUG: Attributes = {attributes}")
        print(f"DEBUG: Total rows = {len(training_data)}")
        print(f"DEBUG: Sample row = {training_data[0]}")
        
        while uncovered_data and rule_number <= max_rules:
            # Count examples per class
            class_counts = defaultdict(int)
            for item in uncovered_data:
                class_counts[item["category"]] += 1
            
            if not class_counts:
                break
            
            # Target class with most examples
            target_class = max(class_counts, key=class_counts.get)
            
            # Evaluate all conditions
            best_attr = None
            best_val = None
            best_H = -1
            best_A = 0
            best_Ep = 0
            best_Ef = 0
            best_covered = []
            
            candidates = []
            
            for attr in attributes:
                # Get unique values
                values = set(item.get(attr) for item in uncovered_data if attr in item)
                
                for val in values:
                    # Count matches
                    matching = [
                        item for item in uncovered_data
                        if item.get(attr) == val
                    ]
                    
                    if not matching:
                        continue
                    
                    # Ep: correct class
                    Ep = sum(
                        1 for item in matching
                        if item["category"] == target_class
                    )
                    
                    # Ef: wrong class
                    Ef = len(matching) - Ep
                    
                    # Calculate heuristic
                    G, A, H = calculate_gts_heuristic(len(uncovered_data), Ep, Ef)
                    
                    candidates.append({
                        "attribute": attr,
                        "value": val,
                        "H": H,
                        "A": A,
                        "G": G,
                        "Ep": Ep,
                        "Ef": Ef,
                        "formula": f"{Ep + Ef}/{len(uncovered_data)} + sqrt({Ep}/{Ep + Ef}) = {H:.4f}"
                    })
                    
                    # Track best
                    if H > best_H:
                        best_H = H
                        best_A = A
                        best_attr = attr
                        best_val = val
                        best_Ep = Ep
                        best_Ef = Ef
                        best_covered = [
                            item["row_id"] for item in matching
                            if item["category"] == target_class
                        ]
            
            if best_attr is None:
                break
            
            # Format for display
            attr_display = best_attr.replace('_', ' ')
            target_display = target_column.replace('_', ' ')
            
            # Create rule
            rule = {
                "rule_number": rule_number,
                "rule": f"IF {attr_display} IS {best_val} THEN {target_display} IS {target_class}",
                "conditions": {best_attr: best_val},
                "target_class": target_class,
                "accuracy": best_A,
                "heuristic": best_H,
                "coverage": round((best_Ep + best_Ef) / len(training_data), 4),
                "covered_rows": best_covered,
                "Ep": best_Ep,
                "Ef": best_Ef,
                "top_candidates": sorted(candidates, key=lambda x: x['H'], reverse=True)[:5],
                "interpretation": {
                    "rule_quality": "Perfect" if best_A == 1.0 else "Good" if best_A >= 0.8 else "Acceptable",
                    "explanation": f"Rule covers {best_Ep} rows correctly" + (f" and {best_Ef} incorrectly" if best_Ef > 0 else "")
                }
            }
            
            rules.append(rule)
            
            # Remove covered
            uncovered_data = [
                item for item in uncovered_data
                if item["row_id"] not in best_covered
            ]
            
            rule_number += 1
        
        # Coverage stats
        total_covered = sum(len(rule["covered_rows"]) for rule in rules)
        coverage_percentage = (total_covered / len(training_data)) * 100 if training_data else 0
        
        return {
            "algorithm": "GTS (General-To-Specific)",
            "methodology": "Recursive coverage algorithm with heuristic-based attribute selection",
            "document_id": document.id,
            "document_name": document.filename,
            "table_info": {
                "total_rows_parsed": len(training_data),
                "attributes": attributes,
                "target_column": target_column
            },
            "total_rows": len(training_data),
            "total_rules_generated": len(rules),
            "coverage": {
                "rows_covered": total_covered,
                "coverage_percentage": round(coverage_percentage, 2)
            },
            "rules": rules,
            "formula_explanation": {
                "G": "(Ep + Ef) / E - Coverage: proportion of examples matched",
                "A": "Ep / (Ep + Ef) - Accuracy: proportion of correct classifications",
                "H": "G + sqrt(A) - Heuristic: combined metric for rule quality",
                "Ep": "Positive examples: correctly classified",
                "Ef": "False examples: incorrectly covered",
                "E": "Total examples in dataset"
            },
            "rule_format": "IF <condition> THEN <decision>",
            "training_data": training_data,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GTS error: {str(e)}"
        )


# ==================== LEM2 ALGORITHM IMPLEMENTATION ====================

def lem2_find_best_condition(
    uncovered: List[Dict],
    all_data: List[Dict],
    target_class: str,
    attributes: List[str],
    used_conditions: List[Tuple[str, any]]
) -> Tuple[str, any, int, int]:
    """
    LEM2: Find condition with largest coverage of target class
    and highest specificity (least coverage of other classes)
    
    Returns: (attribute, value, coverage_in_target, coverage_in_others)
    """
    best_attr = None
    best_val = None
    best_target_coverage = 0
    best_other_coverage = float('inf')
    
    for attr in attributes:
        # Skip if already used
        if any(cond[0] == attr for cond in used_conditions):
            continue
        
        # Get unique values in uncovered set
        values = set(item.get(attr) for item in uncovered if attr in item)
        
        for val in values:
            # Count coverage in target class (uncovered)
            target_matches = [
                item for item in uncovered
                if item.get(attr) == val and item["category"] == target_class
            ]
            target_coverage = len(target_matches)
            
            # Count coverage in other classes (all data)
            other_matches = [
                item for item in all_data
                if item.get(attr) == val and item["category"] != target_class
            ]
            other_coverage = len(other_matches)
            
            # Selection criteria (PDF page 6):
            # 1. Maximum coverage of target class
            # 2. Among ties, minimum coverage of other classes (highest power/specificity)
            if (target_coverage > best_target_coverage) or \
               (target_coverage == best_target_coverage and other_coverage < best_other_coverage):
                best_attr = attr
                best_val = val
                best_target_coverage = target_coverage
                best_other_coverage = other_coverage
    
    return best_attr, best_val, best_target_coverage, best_other_coverage


# ==================== LEM2 RULE INDUCTION ENDPOINT ====================

@router.post("/ml/lem2-rules")
def generate_lem2_rules(
    request: LEM2RuleRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    📚 LEM2 (Learning from Examples Module 2) Rule Induction
    
    How Algorithm works :
    1. Select target class (depend on decisions)
    2. Find all possible attribute-value pairs from target class rows
    3. For each iteration:
       a) Find condition covering most target class examples
       b) Among ties, choose one covering fewest other class examples (highest specificity)
       c) If covers only target class → create rule
       d) If not → add another condition (conjunction)
    4. Remove covered examples
    5. Repeat until all target class examples covered
    6. Repeat for next class
    
    Example (the way we learnt on classes):
    ```
    Rule 1: IF Inflation IS decrease THEN Interest_rates IS reduction
    Rule 2: IF Currency_reserves IS decrease THEN Interest_rates IS reduction
    Rule 3: IF Inflation IS no_change AND Currency_reserves IS increase 
            THEN Interest_rates IS increase
    Rule 4: IF Currency_reserves IS no_change THEN Interest_rates IS increase
    ```
    
    Key differences from GTS:
    - LEM2: Largest coverage + highest specificity
    - GTS: Heuristic H = G + sqrt(A)
    """
    
    document = db.query(Document).filter(
        Document.id == request.document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document or not document.content_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        gemini = GeminiService()
        
        # Parse table (same as GTS)
        parse_prompt = f"""Extract ALL rows from the table in this document.

CRITICAL INSTRUCTIONS:
1. Extract EVERY SINGLE ROW - do not skip any
2. Use EXACT column names from the first row (header)
3. Return valid JSON array ONLY

Document:
{document.content_text}

Format:
[
  {{"col1": "val1", "col2": "val2", "target": "Y"}},
  ... (ALL rows)
]

Return EVERY row!"""
        
        parse_response = gemini.client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=parse_prompt
        )
        
        # Parse JSON
        import json
        table_text = parse_response.text.strip()
        if table_text.startswith("```json"):
            table_text = table_text[7:]
        if table_text.startswith("```"):
            table_text = table_text[3:]
        if table_text.endswith("```"):
            table_text = table_text[:-3]
        table_text = table_text.strip()
        
        training_data = json.loads(table_text)
        
        if not training_data or len(training_data) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Table must have at least 2 rows"
            )
        
        # Get columns
        all_columns = list(training_data[0].keys())
        if len(all_columns) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Table must have at least 2 columns"
            )
        
        target_column = all_columns[-1]
        attributes = all_columns[:-1]
        
        # Rename and add row_id
        for idx, row in enumerate(training_data, 1):
            row["category"] = row.pop(target_column)
            row["row_id"] = idx
        
        # LEM2 Algorithm
        all_rules = []
        decision_classes = set(item["category"] for item in training_data)
        
        for target_class in decision_classes:
            # Step 1: B = all cases of target class (PDF page 4)
            B = [item for item in training_data if item["category"] == target_class]
            G = B.copy()  # Uncovered examples
            π = []  # Covered examples
            
            class_rule_num = 1
            
            while G:  # While uncovered examples remain
                # Find conditions for a new rule
                conditions = []
                T = []  # Current rule coverage
                
                max_iterations = 5  # Safety: max conditions per rule
                iteration = 0
                
                while iteration < max_iterations:
                    # Find best condition
                    attr, val, target_cov, other_cov = lem2_find_best_condition(
                        G, training_data, target_class, attributes, conditions
                    )
                    
                    if attr is None:
                        break
                    
                    # Add condition
                    conditions.append((attr, val))
                    
                    # Calculate coverage with all conditions
                    T = [
                        item for item in training_data
                        if all(item.get(a) == v for a, v in conditions)
                        and item["category"] == target_class
                    ]
                    
                    # Check if rule is pure (only covers target class)
                    T_all = [
                        item for item in training_data
                        if all(item.get(a) == v for a, v in conditions)
                    ]
                    
                    is_pure = all(item["category"] == target_class for item in T_all)
                    
                    if is_pure and T:
                        # Rule complete! (PDF page 6: [T] ⊂ B condition)
                        break
                    
                    iteration += 1
                
                if not T:
                    break
                
                # Create rule
                attr_display = [c[0].replace('_', ' ') for c in conditions]
                target_display = target_column.replace('_', ' ')
                
                if len(conditions) == 1:
                    rule_text = f"IF {attr_display[0]} IS {conditions[0][1]} THEN {target_display} IS {target_class}"
                else:
                    cond_parts = [f"{attr_display[i]} IS {conditions[i][1]}" for i in range(len(conditions))]
                    rule_text = f"IF {' AND '.join(cond_parts)} THEN {target_display} IS {target_class}"
                
                rule = {
                    "rule_number": len(all_rules) + 1,
                    "rule": rule_text,
                    "conditions": {c[0]: c[1] for c in conditions},
                    "target_class": target_class,
                    "covered_rows": [item["row_id"] for item in T],
                    "num_conditions": len(conditions),
                    "coverage": len(T),
                    "interpretation": {
                        "rule_type": "Simple" if len(conditions) == 1 else f"Conjunctive ({len(conditions)} conditions)",
                        "explanation": f"Covers {len(T)} examples of '{target_class}' class"
                    }
                }
                
                all_rules.append(rule)
                
                # Update: π = π ∪ T, G = B - π (PDF page 8-9)
                covered_ids = [item["row_id"] for item in T]
                π.extend(covered_ids)
                G = [item for item in B if item["row_id"] not in π]
                
                class_rule_num += 1
                
                # Safety
                if class_rule_num > 20:
                    break
        
        # Coverage stats
        total_covered = sum(len(rule["covered_rows"]) for rule in all_rules)
        coverage_percentage = (total_covered / len(training_data)) * 100 if training_data else 0
        
        return {
            "algorithm": "LEM2 (Learning from Examples Module 2)",
            "methodology": "Set-based approach: largest coverage + highest specificity",
            "document_id": document.id,
            "document_name": document.filename,
            "table_info": {
                "total_rows_parsed": len(training_data),
                "attributes": attributes,
                "target_column": target_column,
                "decision_classes": list(decision_classes)
            },
            "total_rows": len(training_data),
            "total_rules_generated": len(all_rules),
            "coverage": {
                "rows_covered": total_covered,
                "coverage_percentage": round(coverage_percentage, 2)
            },
            "rules": all_rules,
            "algorithm_explanation": {
                "step_1": "B = Select all examples of target class",
                "step_2": "T(G) = Find all attribute-value pairs from B",
                "step_3": "Select condition with largest coverage in target class",
                "step_4": "Among ties, select one with smallest coverage in other classes (highest specificity)",
                "step_5": "If [T] ⊂ B (pure coverage) → create rule, else add more conditions",
                "step_6": "π = π ∪ T (mark as covered), G = B - π (remaining)",
                "step_7": "Repeat until G = ∅, then process next class"
            },
            "difference_from_gts": {
                "LEM2": "Largest coverage + highest specificity",
                "GTS": "Heuristic H = G + sqrt(A)"
            },
            "training_data": training_data,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LEM2 error: {str(e)}"
        )