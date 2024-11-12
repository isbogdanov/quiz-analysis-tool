# Copyright 2024 Igor Bogdanov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_loader import DataLoader


def convert_to_serializable(obj):
    """Convert numpy types to native Python types"""
    if isinstance(
        obj,
        (
            np.int_,
            np.intc,
            np.intp,
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
        ),
    ):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif pd.isna(obj):
        return None
    return obj


def format_question_data(raw_data):
    """Format question data to be more readable"""
    formatted = {
        "questions": {},
        "user_responses": {},
        "metadata": {
            "total_questions": len(raw_data["questions"]),
            "total_users": len(raw_data["users"]),
            "max_possible_score": sum(
                q["worth"] for q in raw_data["questions"].values()
            ),
        },
    }

    # Format questions
    for q_id, q_data in raw_data["questions"].items():
        formatted["questions"][q_id] = {
            "text": q_data["text"],
            "category": q_data.get("category", "no-category"),
            "correct_answer": q_data.get("correct_answer", "no-answer"),
            "worth": q_data.get("worth", 1),
        }

    # Format user responses
    for user_id, user_data in raw_data["users"].items():
        formatted["user_responses"][user_id] = {
            "score": {
                "earned": user_data["points_earned"],
                "possible": user_data["points_possible"],
                "percentage": user_data["calculated_score"],
            },
            "self_assessment": user_data["self_assessment"],
            "answers": {},
        }

        # Format individual answers
        for q_id, response in user_data["responses"].items():
            formatted["user_responses"][user_id]["answers"][q_id] = {
                "user_answer": response["answer"],
                "correct_answer": raw_data["questions"][q_id]["correct_answer"],
                "is_correct": response["is_correct"],
                "points": {
                    "earned": response["points_earned"],
                    "possible": response["worth"],
                },
            }

    return formatted


def get_raw_data(data_dir="data", column_mappings=None):
    """Get raw data as JSON string
    Args:
        data_dir (str): Path to data directory
        column_mappings (dict): Mapping of standard column names to actual names in files
    """
    # Initialize DataLoader with column mappings
    loader = DataLoader(data_dir, column_mappings)

    # Get raw data
    raw_data = loader.load_all_data()

    # Convert to serializable format
    serializable_data = convert_to_serializable(raw_data)

    # Convert to JSON
    return json.dumps(serializable_data, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Print raw JSON data
    print(get_raw_data())
