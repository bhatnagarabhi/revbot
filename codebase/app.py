# long_flat_user_friendly_script.py
# This script simulates a simple, sequential data processing pipeline.
# It's designed to be easy for a human to read due to clear comments and linear flow,
# but challenging for a RAG system that primarily chunks by functions/classes,
# as all logic is at the top-level.

import os
import random
import datetime
import time
import math

# --- SECTION 1: Configuration Parameters ---
# These variables define how the script behaves.
PIPELINE_NAME = "SimpleDailyDataProcessor"
CURRENT_VERSION = "1.1.0"
MAX_RECORDS_TO_GENERATE = 10000 # Total number of data items to simulate.
BATCH_PROCESSING_SIZE = 500   # How many records to process at once.
OUTPUT_REPORT_DIR = "daily_reports"
LOG_FILE_NAME = "pipeline_activity.log"
CRITICAL_VALUE_THRESHOLD = 85.0 # A threshold for flagging important data.
DATA_ENRICHMENT_FACTOR = 1.05 # A multiplier for a specific enrichment step.
DEBUG_MESSAGES_ENABLED = True

# --- SECTION 2: Setup and Logging Initialization ---
# Prepare the environment and set up logging.

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_REPORT_DIR, exist_ok=True)

# Function to log messages (simple for this flat script)
def _log_message(message_text, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] [{PIPELINE_NAME}] {message_text}"
    print(log_entry) # Print to console
    with open(os.path.join(OUTPUT_REPORT_DIR, LOG_FILE_NAME), "a") as f:
        f.write(log_entry + "\n")

_log_message(f"Starting {PIPELINE_NAME} (Version: {CURRENT_VERSION}).")
_log_message(f"Configured to process up to {MAX_RECORDS_TO_GENERATE} records.")
_log_message(f"Output reports will be saved in: {os.path.abspath(OUTPUT_REPORT_DIR)}")

# --- SECTION 3: Data Generation Simulation ---
# Simulate fetching or generating raw data.

raw_data_items = []
_log_message("Generating synthetic raw data...")
for i in range(MAX_RECORDS_TO_GENERATE):
    record_id = f"REC_{i+1:05d}"
    # Simulate a numeric value between 0 and 100
    numeric_value = random.uniform(1.0, 99.9)
    # Simulate a category
    data_category = random.choice(['Alpha', 'Beta', 'Gamma', 'Delta'])
    # Simulate a timestamp
    creation_time = datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30))

    raw_data_entry = {
        "id": record_id,
        "value": round(numeric_value, 2),
        "category": data_category,
        "created_at": creation_time.isoformat()
    }
    raw_data_items.append(raw_data_entry)

    if (i + 1) % 2000 == 0:
        _log_message(f"Generated {i+1} records so far.")
        time.sleep(0.005) # Small pause for realism

_log_message(f"Finished data generation. Total raw records: {len(raw_data_items)}.")

# --- SECTION 4: Core Data Processing Loop ---
# This is the main analytical part where data is transformed and evaluated.

processed_count = 0
flagged_count = 0
category_totals = {'Alpha': 0.0, 'Beta': 0.0, 'Gamma': 0.0, 'Delta': 0.0}
successful_processing_records = []
error_records = []

_log_message("Beginning core data processing...")
current_batch = []
for i, record_data in enumerate(raw_data_items):
    current_batch.append(record_data)

    if len(current_batch) >= BATCH_PROCESSING_SIZE or i == MAX_RECORDS_TO_GENERATE - 1:
        _log_message(f"Processing batch of {len(current_batch)} records. Total processed: {processed_count}.")

        for item in current_batch:
            item_id = item['id']
            try:
                # Validation Step: Check if key fields exist
                if 'value' not in item or 'category' not in item:
                    raise KeyError(f"Missing essential key in record {item_id}")

                # Transformation Step 1: Apply enrichment based on a factor
                enriched_value = item['value'] * DATA_ENRICHMENT_FACTOR
                
                # Transformation Step 2: Categorization and aggregation
                if item['category'] in category_totals:
                    category_totals[item['category']] += enriched_value
                else:
                    _log_message(f"Unknown category '{item['category']}' for {item_id}. Skipping aggregation.", "WARNING")

                # Evaluation Step: Flagging critical items
                is_critical = False
                if enriched_value > CRITICAL_VALUE_THRESHOLD:
                    flagged_count += 1
                    is_critical = True
                    _log_message(f"Record {item_id} flagged as critical (Value: {enriched_value:.2f})", "HIGH_IMPACT" if DEBUG_MESSAGES_ENABLED else "INFO")

                processed_item = {
                    "id": item_id,
                    "processed_value": round(enriched_value, 2),
                    "is_critical": is_critical,
                    "original_category": item['category']
                }
                successful_processing_records.append(processed_item)
                processed_count += 1

            except KeyError as e:
                _log_message(f"Data integrity error for {item_id}: {e}", "ERROR")
                error_records.append({"id": item_id, "error": str(e), "type": "KeyError"})
            except Exception as e:
                _log_message(f"Unexpected processing error for {item_id}: {e}", "ERROR")
                error_records.append({"id": item_id, "error": str(e), "type": "GenericError"})

        current_batch = [] # Reset batch

_log_message("Finished core data processing loop.")

# --- SECTION 5: Final Aggregation and Reporting ---
# Summarize results and generate a final report.

_log_message("Starting final aggregation and report generation.")

total_successfully_processed = len(successful_processing_records)
total_errors = len(error_records)
overall_success_rate = (total_successfully_processed / MAX_RECORDS_TO_GENERATE) * 100 if MAX_RECORDS_TO_GENERATE > 0 else 0

# Calculate some derived metrics
average_processed_value = sum(r['processed_value'] for r in successful_processing_records) / total_successfully_processed if total_successfully_processed > 0 else 0

_log_message("Generating final report file.")
report_date = datetime.date.today().strftime("%Y-%m-%d")
report_file_path = os.path.join(OUTPUT_REPORT_DIR, f"{PIPELINE_NAME}_Report_{report_date}.txt")

with open(report_file_path, "w") as report_file:
    report_file.write(f"--- {PIPELINE_NAME} Daily Report ---\n")
    report_file.write(f"Version: {CURRENT_VERSION}\n")
    report_file.write(f"Report Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_file.write("-" * 50 + "\n")
    report_file.write(f"Total Records Attempted: {MAX_RECORDS_TO_GENERATE}\n")
    report_file.write(f"Records Successfully Processed: {total_successfully_processed}\n")
    report_file.write(f"Records with Errors: {total_errors}\n")
    report_file.write(f"Success Rate: {overall_success_rate:.2f}%\n")
    report_file.write(f"Items Flagged as Critical: {flagged_count}\n")
    report_file.write(f"Average Processed Value: {average_processed_value:.2f}\n")
    report_file.write("\nCategory-wise Aggregations:\n")
    for category, total in sorted(category_totals.items()):
        report_file.write(f"  {category}: {total:.2f}\n")
    report_file.write("-" * 50 + "\n")
    if total_errors > 0:
        report_file.write("WARNING: Errors occurred during processing. Check logs for details.\n")
    if flagged_count > 0:
        report_file.write("NOTE: Critical items were detected. Review immediately.\n")
    report_file.write("--- End of Report ---\n")

_log_message(f"Report generated and saved to: {os.path.abspath(report_file_path)}")

# --- SECTION 6: Cleanup and Finalization ---
# Perform any final tasks before exiting.

_log_message("Performing finalization steps...")
# Simulate writing some final state to a mock JSON file
summary_json_path = os.path.join(OUTPUT_REPORT_DIR, "summary.json")
final_summary_data = {
    "run_timestamp": datetime.datetime.now().isoformat(),
    "pipeline_status": "Completed_With_Errors" if total_errors > 0 else "Completed_Successfully",
    "processed_count": processed_count,
    "error_count": total_errors,
    "critical_items_detected": flagged_count,
    "version": CURRENT_VERSION
}
with open(summary_json_path, "w") as json_file:
    json.dump(final_summary_data, json_file, indent=4)
_log_message(f"Final summary saved to: {os.path.abspath(summary_json_path)}")

# Simulate a brief shutdown period
time.sleep(0.5)

_log_message(f"{PIPELINE_NAME} execution finished.")

# Exit the script with a status code
exit_status = 0
if total_errors > 0 or flagged_count > 0:
    exit_status = 1 # Indicate non-zero status for warnings/errors

# In a real script, you might use sys.exit(exit_status)
# For a dummy, simple print is fine, as execution might continue in some environments.
print(f"\nScript finished with exit status: {exit_status}")

