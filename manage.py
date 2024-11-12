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

#!/usr/bin/env python3

import argparse
from pathlib import Path
import sys
import os
import subprocess
import json
import csv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import core functionality
from scripts.get_raw_data import get_raw_data
from scripts.generate_report import main as generate_report
from scripts.generate_sample_data import generate_sample_data
from scripts.visualize_results import main as visualize_main


def setup_argparse():
    parser = argparse.ArgumentParser(description="Quiz Analysis Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Raw data export
    raw_parser = subparsers.add_parser("raw", help="Export raw data as JSON")
    raw_parser.add_argument(
        "--data-dir", type=str, default="data", help="Data directory"
    )
    raw_parser.add_argument(
        "--output", type=str, default="raw_data.json", help="Output JSON file"
    )
    raw_parser.add_argument(
        "--question-col", type=str, default="question", help="Question column name"
    )
    raw_parser.add_argument(
        "--category-col", type=str, default="category", help="Category column name"
    )
    raw_parser.add_argument(
        "--answer-col", type=str, default="answer", help="Answer column name"
    )
    raw_parser.add_argument(
        "--value-col", type=str, default="value", help="Value/points column name"
    )
    raw_parser.add_argument(
        "--datetime-col", type=str, default="date_time", help="Datetime column name"
    )
    raw_parser.add_argument(
        "--userid-col", type=str, default="user_id", help="User ID column name"
    )

    # Generate sample data
    gen_parser = subparsers.add_parser("generate", help="Generate sample quiz data")
    gen_parser.add_argument(
        "--output", type=str, default="data", help="Output directory"
    )
    gen_parser.add_argument("--users", type=int, default=100, help="Number of users")

    # Generate report
    report_parser = subparsers.add_parser("report", help="Generate PDF report")
    report_parser.add_argument(
        "--data-dir", type=str, default="data", help="Data directory"
    )
    report_parser.add_argument(
        "--output", type=str, default="report", help="Output directory"
    )
    report_parser.add_argument(
        "--question-col", type=str, default="question", help="Question column name"
    )
    report_parser.add_argument(
        "--category-col", type=str, default="category", help="Category column name"
    )
    report_parser.add_argument(
        "--answer-col", type=str, default="answer", help="Answer column name"
    )
    report_parser.add_argument(
        "--value-col", type=str, default="value", help="Value/points column name"
    )
    report_parser.add_argument(
        "--datetime-col", type=str, default="date_time", help="Datetime column name"
    )
    report_parser.add_argument(
        "--userid-col", type=str, default="user_id", help="User ID column name"
    )

    # Generate visualizations
    viz_parser = subparsers.add_parser("visualize", help="Generate visualization plots")
    viz_parser.add_argument(
        "--data-dir", type=str, default="data", help="Data directory"
    )
    viz_parser.add_argument(
        "--question-col", type=str, default="question", help="Question column name"
    )
    viz_parser.add_argument(
        "--category-col", type=str, default="category", help="Category column name"
    )
    viz_parser.add_argument(
        "--answer-col", type=str, default="answer", help="Answer column name"
    )
    viz_parser.add_argument(
        "--value-col", type=str, default="value", help="Value/points column name"
    )
    viz_parser.add_argument(
        "--datetime-col", type=str, default="date_time", help="Datetime column name"
    )
    viz_parser.add_argument(
        "--userid-col", type=str, default="user_id", help="User ID column name"
    )

    return parser


def handle_raw(args):
    """Export raw data as JSON"""
    print("Exporting raw data...")

    # Create column mappings dictionary
    column_mappings = {
        "question": args.question_col,
        "category": args.category_col,
        "answer": args.answer_col,
        "value": args.value_col,
        "date_time": args.datetime_col,
        "user_id": args.userid_col,
    }

    # Create outputs/json directory
    output_dir = Path("outputs/json")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get raw data with column mappings
    raw_json = get_raw_data(args.data_dir, column_mappings)

    output_file = output_dir / args.output
    with open(output_file, "w") as f:
        f.write(raw_json)
    print(f"Raw data exported to: {output_file}")


def handle_generate(args):
    """Generate sample data"""
    print(f"Generating sample data for {args.users} users...")

    # Create outputs/sample_data directory
    output_dir = Path("outputs/sample_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Import and generate data
    from scripts.generate_sample_data import generate_sample_data

    questions, results, self_assessments = generate_sample_data(num_users=args.users)

    # Write files to our output directory
    files_to_write = [
        ("questions.csv", questions),
        ("results.csv", results),
        ("self_assessment.csv", self_assessments),
    ]

    for filename, data in files_to_write:
        output_file = output_dir / filename
        print(f"Writing {filename}...")
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)

    print(f"Sample data generated in: {output_dir}")


def handle_report(args):
    """Generate PDF report"""
    print("Generating report...")

    # Create column mappings dictionary
    column_mappings = {
        "question": args.question_col,
        "category": args.category_col,
        "answer": args.answer_col,
        "value": args.value_col,
        "date_time": args.datetime_col,
        "user_id": args.userid_col,
    }

    # Create outputs/report directory
    output_dir = Path("outputs/report").absolute()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use the main function from generate_report with column mappings
    from scripts.generate_report import main as generate_report_main

    try:
        # Run report generation with column mappings
        generate_report_main(
            data_dir=str(Path(args.data_dir).absolute()),
            output_dir=str(output_dir),
            column_mappings=column_mappings,
        )

        print(f"Report generated in: {output_dir}")
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        raise


def handle_visualize(args):
    """Generate visualizations"""
    print("Generating visualizations...")

    # Create column mappings dictionary
    column_mappings = {
        "question": args.question_col,
        "category": args.category_col,
        "answer": args.answer_col,
        "value": args.value_col,
        "date_time": args.datetime_col,
        "user_id": args.userid_col,
    }

    # Create outputs/visualizations directory
    output_dir = Path("outputs/visualizations")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use the main function from visualize_results with column mappings
    from scripts.visualize_results import main as visualize_main

    visualize_main(args.data_dir, str(output_dir), column_mappings)

    print(f"Visualizations generated in: {output_dir}")


def main():
    parser = setup_argparse()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handlers = {
        "raw": handle_raw,
        "generate": handle_generate,
        "report": handle_report,
        "visualize": handle_visualize,
    }

    handlers[args.command](args)


if __name__ == "__main__":
    main()
