# Technical-Test - AI/ML - Angel Y. Payano Lanfranco

In this repository I will be delivering the completed test pack requested. This repository contains an end-to-end prototype for automated billing validation. The system identifies financial discrepancies by cross-referencing employee timesheets, contractual rate cards, and billing reports. It utilizes a hybrid architecture where Python handles strict data validation and an Large Language Model (LLM) provides qualitative analysis, fraud risk assessment, and corrective recommendations.

Key Features
Automated Validation Engine: Enforces mathematical checks for rate mismatches, contract hour violations, and billing vs. timesheet inconsistencies.

AI-Driven Audit Insights: Leverages OpenAI (gpt-5.4) to generate natural language explanations for every detected error and specific business fixes.

Fraud Risk Assessment: Analyzes error patterns across the dataset to assign a risk level (Low, Medium, or High) based on indicators of intentional manipulation or padding. In this case, the datasets are small. But if we have a large dataset then there we can find fraud patterns and have more actionable insights.

Production-Ready Architecture: Transitioned from experimental prototyping in Jupyter Notebooks to a deployed web application via Streamlit and Railway.

Technical Stack
Development: Jupyter Notebooks (Data Exploration & Prototyping)

Production: Streamlit (Web Interface)

Deployment: Railway (Cloud Hosting)

Data Processing: Pandas, NumPy

Intelligence: OpenAI API (gpt-5.4)

Security: python-dotenv for environment variable management / Secret Key within Railway.

.streamlit/: Contains the config.toml file, which manages server-side configurations including port binding, network addresses, and security headers.

app.py: The primary application engine housing the relational data logic, mathematical validation rules, and the GPT-5.4 auditing prompts.  

requirements.txt: A comprehensive list of all Python dependencies (Streamlit, Pandas, OpenAI, etc.) required to build the environment.  

Procfile: The explicit deployment instruction used by Railway to initialize the Streamlit server and bind it to the dynamic platform port.  

Test AI ML TP - Angel Yanciel Payano Lanfranco.ipynb: The original research notebook detailing the initial logic exploration and AI integration testing.

Datasets (Root): The foundation files billing.csv, contracts.csv, and timesheet.csv are located in the root directory for direct access by the application.  

.gitignore: Configured to ensure environment secrets, local caches, and temporary system files are not tracked by version control.

README.md: The technical documentation and architectural overview of the AI Billing Auditor.

Bonus Challenge: Multi-Client Scalability
The architecture of this prototype is designed to support multiple clients and varying business rules without requiring any modifications to the core Python code or AI prompts.

Relational Data Logic: Instead of hardcoding validation thresholds or rates, the system treats the contracts.csv file as a relational "Source of Truth". The scalability is achieved through:

Dynamic Mapping: The validation engine performs a relational join between the Timesheet/Billing data and the Contracts dataset using the Project identifier as a foreign key.

Agnostic Rule Enforcement: Rates, maximum weekly hours, and project-specific constraints are loaded into memory at runtime. This allows the system to validate a project with a 40-hour cap just as easily as a project with a 10-hour cap by simply updating the input CSV.

Context-Aware AI: The LLM receives the specific contract rules for each flagged record within the JSON payload. This ensures that the "AI Auditor" always reasons based on the specific contractual context of the project being analyzed.

Future Extensibility
This design pattern allows for seamless integration with enterprise SQL databases or ERP systems. By replacing the CSV loading layer with database connectors, the same validation logic can be applied to thousands of records across diverse global projects.
