import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import textwrap
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Data validation and business logic
# This function acts as the mathematical engine of the auditor. It takes the raw 
# inputs and stitches them into a single master view to find discrepancies.
def validate_billing_logic(df_timesheet, df_contracts, df_billing):
    
    # We begin by merging the employee timesheets with their contract terms.
    # This aligns the reported hours with the agreed-upon project rates.
    df_step1 = pd.merge(df_timesheet, df_contracts, on="Project", how="left")
    
    # Next, we layer in the actual billing data to compare the company's 
    # financial claims against the ground-truth work records[cite: 5].
    df_master = pd.merge(df_step1, df_billing, on=["Employee_ID", "Project"], how="left")
    
    # We initialize the status columns to assume everything is correct by default.
    df_master['STATUS'] = 'OK'
    df_master['DISCREPANCY_REASON'] = ''
    
    # Logic Test 1: Checking for rate mismatches.
    # If the rate charged to the client differs from the contract rate, we flag it.
    mask_rate = df_master['Rate_Charged'] != df_master['Rate_per_Hour']
    df_master.loc[mask_rate, 'STATUS'] = 'ERROR'
    df_master.loc[mask_rate, 'DISCREPANCY_REASON'] += 'Rate Mismatch. '
    
    # Logic Test 2: Checking for contractual hour breaches.
    # We flag any instance where the billed hours exceed the weekly cap set in the contract.
    mask_max_hours = df_master['Hours_Billed'] > df_master['Max_Hours_Per_Week']
    df_master.loc[mask_max_hours, 'STATUS'] = 'ERROR'
    df_master.loc[mask_max_hours, 'DISCREPANCY_REASON'] += 'Exceeds Contract Max Hours. '
    
    # Logic Test 3: Detecting overbilling.
    # This captures scenarios where the hours billed are higher than the hours actually worked.
    mask_worked_hours = df_master['Hours_Billed'] > df_master['Hours_Worked']
    df_master.loc[mask_worked_hours, 'STATUS'] = 'ERROR'
    df_master.loc[mask_worked_hours, 'DISCREPANCY_REASON'] += 'Billed more than worked. '

    # Logic Test 4: Detecting underbilling or missing time.
    # We identify cases where the employee worked more than the client was billed for.
    mask_missing_hours = df_master['Hours_Billed'] < df_master['Hours_Worked']
    df_master.loc[mask_missing_hours, 'STATUS'] = 'ERROR'
    df_master.loc[mask_missing_hours, 'DISCREPANCY_REASON'] += 'Missing hours (Underbilling). '
    
    # We remove any trailing spaces from the error descriptions for a cleaner UI.
    df_master['DISCREPANCY_REASON'] = df_master['DISCREPANCY_REASON'].str.strip()
    return df_master

# Artificial Intelligence reasoning logic
# We use exponential backoff here because API limits can be sensitive during batch audits.
# This ensures the process is resilient and won't crash due to temporary network saturation.
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True)
def analyze_billing_errors_with_openai(df_errors, api_key):

    client = OpenAI(api_key=api_key)
    
    # We isolate only the columns necessary for the auditor to make an informed decision.
    # This reduces noise and improves the quality of the AI's reasoning.
    columns_for_ai = [
        'Employee_Name', 'Project', 'Hours_Worked', 'Hours_Billed', 
        'Max_Hours_Per_Week', 'Rate_per_Hour', 'Rate_Charged', 'DISCREPANCY_REASON'
    ]
    error_data_json = df_errors[columns_for_ai].to_json(orient="records")
    
    # The system prompt establishes the AI as a high-level financial auditor.
    # We enforce a strict JSON output to ensure the application can reliably parse the results.
    system_prompt = """
    You are an expert Financial Auditor and AI Assistant evaluating a Billing and Timesheet process.
    You MUST output your response in JSON format.
    CRITICAL: You must process EVERY single record provided. Do NOT summarize, skip, or use "..." to abbreviate. 
    The output must be exhaustive and complete for every case found in the dataset.
    """
    
    user_prompt = f"""
    I will provide you with a JSON dataset of billing records that have FAILED our mathematical validation[cite: 5].
    
    Here is the error dataset:
    {error_data_json}
    
    Your task is to analyze these errors and provide actionable business recommendations. 
    You MUST respond with a strictly valid JSON object using the following exact structure:
    
    {{
      "general_analysis": "Provide a 3-4 sentence executive summary of the overall error trends.",
      "fraud_risk_assessment": "Analyze if patterns indicate accidental typos or intentional manipulation. Assign a Risk Level (Low/Medium/High) and justify it.",
      "case_recommendations": [
        {{
          "Employee_Name": "Name from dataset",
          "Project": "Project from dataset",
          "ai_explanation": "Detailed natural language explanation of the specific mathematical failure.",
          "actionable_fix": "Specific action to fix the billing (e.g., credit note amount, rate adjustment)."
        }}
      ]
    }}
    """
    
    # We use a low temperature setting (0.2) to maintain analytical consistency and minimize hallucinations.
    response = client.chat.completions.create(
        model="gpt-5.4", 
        response_format={ "type": "json_object" }, 
        temperature=0.2, 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return json.loads(response.choices[0].message.content)

# User Interface configuration
# We set the layout to wide to better accommodate the large audit dataframes.
st.set_page_config(page_title="AI Billing Auditor", layout="wide")
st.title("AI ML Test - TP - AI Billing Auditor")

# Security check for the API key.
# In a production environment like Railway, we pull this from the platform's secrets management.
API_KEY = os.environ.get('OPENAI_API_KEY')

if not API_KEY:
    st.error("OPENAI_API_KEY not found. Add it to the Railway Variables tab.")
    st.stop()

# We place the data ingestion tools in the sidebar to keep the main dashboard focused.
with st.sidebar:
    st.header("Upload Center")
    f_contracts = st.file_uploader("1. Contracts (CSV)", type="csv")
    f_timesheets = st.file_uploader("2. Timesheets (CSV)", type="csv")
    f_billing = st.file_uploader("3. Billing (CSV)", type="csv")

# The audit only begins once all three foundational data sources are uploaded.
if f_contracts and f_timesheets and f_billing:
    
    # Step 1: Mathematical Validation.
    # We provide a manual trigger so the user can verify their uploads before processing.
    if st.button("Process Data Validation"):
        st.session_state['results'] = validate_billing_logic(
            pd.read_csv(f_timesheets), pd.read_csv(f_contracts), pd.read_csv(f_billing)
        )
    
    if 'results' in st.session_state:
        results = st.session_state['results']
        st.subheader("Validation Dashboard")
        
        # We use a visual highlight for errors to guide the auditor's eye to high-risk rows.
        st.dataframe(results.style.map(
            lambda x: 'background-color: #d9534f; color: white' if x == 'ERROR' else '', 
            subset=['STATUS']
        ), use_container_width=True)
        
        error_df = results[results['STATUS'] == 'ERROR']
        
        # Step 2: Artificial Intelligence Analysis.
        # This step is only available if mathematical discrepancies were detected.
        if not error_df.empty:
            st.divider()
            
            if st.button("Run AI Audit Analysis"):
                with st.spinner("AI Auditor is evaluating the data context..."):
                    try:
                        ai_results = analyze_billing_errors_with_openai(error_df, API_KEY)
                        
                        st.subheader("AI Executive Summary")
                        st.write(ai_results.get('general_analysis', 'No general analysis provided.'))
                        
                        st.subheader("Fraud Risk Assessment")
                        st.write(ai_results.get('fraud_risk_assessment', 'No risk assessment provided.'))
                        
                        st.subheader("Specific Case Recommendations")
                        for case in ai_results.get('case_recommendations', []):
                            # Expander components help keep the interface clean when dealing with many errors.
                            with st.expander(f"Employee: {case.get('Employee_Name')} | Project: {case.get('Project')}"):
                                st.write(f"Explanation: {case.get('ai_explanation')}")
                                st.success(f"Recommended Fix: {case.get('actionable_fix')}")
                                
                    except Exception as e:
                        st.error(f"The AI Audit encountered a problem: {str(e)}")
        else:
            st.success("The system did not detect any billing discrepancies in the current dataset.")
else:
    st.info("The auditor is ready. Please upload the contract, timesheet, and billing files in the sidebar.")
