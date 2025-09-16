#!/usr/bin/env python3
"""
Generate Linda's 7-day PRO PDFs for Weeks 1–6 without interactive shell issues.

Usage:
  python generate_linda_weeks.py
"""

from linda_meal_plan_pdf_pro import create_pdf


def main():
    for week in range(1, 7):
        create_pdf(week=week)


if __name__ == "__main__":
    main()
