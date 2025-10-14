# Lead Qualification Agent README

## Overview

The Lead Qualification Agent is responsible for scoring and qualifying leads based on predefined criteria and data analysis. This agent evaluates lead quality, assigns scores, and determines readiness for further engagement in the sales pipeline.

## Model

- **Model**: xAI Grok (grok-4)
- **Framework**: agno v2.0.3
- **API Key**: XAI_API_KEY environment variable

## Role

Lead Qualification Specialist

## Functions

- Analyze lead data using pandas for statistical evaluation
- Score leads based on multiple criteria (budget, timeline, authority, need, fit)
- Generate qualification reports with recommendations
- Filter and prioritize high-quality leads for next steps
- Maintain qualification metrics and thresholds

## Tools

- `knowledge_query`: Access qualification criteria and scoring guidelines
- `database_query`: Retrieve lead data from CRM systems
- `scoring_analysis`: Perform automated scoring calculations

## Results

- Qualified leads with detailed scoring (0-100 scale)
- Actionable recommendations for each lead
- Pipeline prioritization based on lead quality
- Data-driven insights for sales team optimization
- Seamless handoff to CRM Manager for qualified leads
