#!/usr/bin/env python3
"""
Generate 6-week meal plans for Libby Simpson
Focuses on easy prep meals for fat loss goals
"""

import asyncio
from generate_client_weeks import generate_client_weeks

if __name__ == "__main__":
    asyncio.run(generate_client_weeks("Libby", 6))

