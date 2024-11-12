# Quiz Analysis Tool

A command-line tool for analyzing quiz results and generating reports.

Copyright 2024 Igor Bogdanov

## Installation

1. Clone the repository:

bash
git clone <repository-url>
cd quiz-analysis-tool

2. Create a virtual environment (recommended):

bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

3. Install dependencies:

bash
pip install -r requirements.txt


## Usage

### Generate Sample Data

Generates sample quiz data for testing.

Default usage:

bash
python manage.py generate

This will generate data for 100 users in the `outputs/sample_data` directory.

Custom usage:
bash
python manage.py generate --users 90 --output custom_data

### Export Raw Data

Exports quiz data as JSON for further analysis.

Default usage (with standard column names):
bash
python manage.py raw

This will read from `data` directory and export to `outputs/json/raw_data.json`.

Custom usage (with different column names):

bash
python manage.py raw --data-dir custom_data \
--question-col "Question" \
--category-col "Theme" \
--answer-col "Correct answer" \
--value-col "Points" \
--datetime-col "Timestamp" \
--userid-col "Email address" \
--output custom_output.json

### Generate Visualizations

Creates visualization plots of quiz performance.

Default usage:

bash
python manage.py visualize

This will read from `data` directory and save plots to `outputs/visualizations`.

Custom usage:

bash
python manage.py visualize --data-dir custom_data \
--question-col "Question" \
--category-col "Theme" \
--answer-col "Correct answer" \
--value-col "Points" \
--datetime-col "Timestamp" \
--userid-col "Email address"

### Generate Report (In Development)

Generates a PDF report with analysis results.

Default usage:

bash
python manage.py report


Custom usage:

bash
python manage.py report --data-dir custom_data \
--question-col "Question" \
--category-col "Theme" \
--answer-col "Correct answer" \
--value-col "Points" \
--datetime-col "Timestamp" \
--userid-col "Email address" \
--output custom_report

## Data Format

The tool expects three CSV files in the data directory:
- `questions.csv`: Quiz questions and metadata
- `results.csv`: User responses
- `self_assessment.csv`: User self-assessment scores

### Default Column Names
- Question: `question`
- Category: `category`
- Answer: `answer`
- Value/Points: `value`
- DateTime: `date_time`
- User ID: `user_id`

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.


## Acknowledgements

Thanks to Alexander Blagochevsky for inspiration.
