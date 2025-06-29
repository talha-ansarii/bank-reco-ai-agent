from crewai import Agent, Task, Crew
from crewai_tools import FileReadTool, WebSearchTool
import pandas as pd
from typing import Dict, List, Any
import json


class GSTReconciliationCrew:
    """CrewAI-based GST reconciliation crew"""

    def __init__(self):
        self.file_read_tool = FileReadTool()

    def create_agents(self):
        """Create agents for GST reconciliation"""

        # Data Processing Agent
        data_processor = Agent(
            role="GST Data Processor",
            goal="Process and normalize GST data from GSTR-2A/2B and Books of Accounts",
            backstory="You are an expert in GST compliance and data processing. You specialize in cleaning and normalizing GST data from various sources to ensure accurate reconciliation.",
            tools=[self.file_read_tool],
            verbose=True
        )

        # Reconciliation Agent
        reconciliation_agent = Agent(
            role="GST Reconciliation Specialist",
            goal="Perform accurate matching between GSTR data and Books of Accounts",
            backstory="You are a seasoned GST reconciliation expert with deep knowledge of Indian GST regulations. You excel at identifying matches, partial matches, and discrepancies between different data sources.",
            verbose=True
        )

        # Report Generation Agent
        report_generator = Agent(
            role="GST Report Generator",
            goal="Generate comprehensive reconciliation reports and summaries",
            backstory="You are a financial reporting specialist who creates clear, actionable reports for GST reconciliation results. You ensure all discrepancies are properly documented and actionable insights are provided.",
            verbose=True
        )

        return {
            "data_processor": data_processor,
            "reconciliation_agent": reconciliation_agent,
            "report_generator": report_generator
        }

    def create_tasks(self, agents: Dict, gstr_data: Dict, books_file_path: str):
        """Create tasks for GST reconciliation"""

        # Data Processing Task
        process_data_task = Task(
            description=f"""
            Process and normalize GST data from the following sources:
            1. GSTR-2A/2B JSON data: {json.dumps(gstr_data, indent=2)}
            2. Books of Accounts Excel file: {books_file_path}
            
            Your tasks:
            - Clean and normalize GSTIN formats
            - Standardize invoice numbers
            - Convert dates to consistent format
            - Validate data integrity
            - Prepare data for reconciliation
            
            Output a structured summary of the processed data including record counts and any data quality issues found.
            """,
            agent=agents["data_processor"],
            expected_output="Structured summary of processed data with counts and quality issues"
        )

        # Reconciliation Task
        reconciliation_task = Task(
            description="""
            Perform comprehensive GST reconciliation between GSTR data and Books of Accounts.
            
            Matching criteria:
            - GSTIN: Exact match (40% weight)
            - Invoice Number: Fuzzy match with 85% threshold (30% weight)
            - Invoice Date: Within 2 days tolerance (20% weight)
            - Amount: Within ₹5 tolerance (10% weight)
            
            Categorize results into:
            1. Matched: Perfect matches
            2. Partial Matches: Partial matches requiring review
            3. GSTR Only: Present in GSTR but missing from Books
            4. Books Only: Present in Books but missing from GSTR
            
            Output detailed reconciliation results with match scores and reasons.
            """,
            agent=agents["reconciliation_agent"],
            expected_output="Detailed reconciliation results with categorized matches",
            context=[process_data_task]
        )

        # Report Generation Task
        report_generation_task = Task(
            description="""
            Generate comprehensive GST reconciliation reports based on the reconciliation results.
            
            Generate the following reports:
            1. Detailed Reconciliation Report: All matches with scores and differences
            2. Summary Report: High-level statistics and totals
            3. Unmatched GSTR Records: Records present only in GSTR
            4. Unmatched Books Records: Records present only in Books
            5. Partial Matches Report: Records requiring manual review
            
            Include actionable insights and recommendations for each category.
            Highlight high-value discrepancies and potential compliance issues.
            """,
            agent=agents["report_generator"],
            expected_output="Comprehensive set of reconciliation reports with insights",
            context=[reconciliation_task]
        )

        return [process_data_task, reconciliation_task, report_generation_task]

    def run_reconciliation(self, gstr_data: Dict, books_file_path: str) -> Dict[str, Any]:
        """Run the complete GST reconciliation process"""

        # Create agents
        agents = self.create_agents()

        # Create tasks
        tasks = self.create_tasks(agents, gstr_data, books_file_path)

        # Create crew
        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            verbose=True
        )

        # Execute the crew
        result = crew.kickoff()

        return {
            "status": "success",
            "result": result,
            "message": "GST reconciliation completed successfully using CrewAI"
        }
