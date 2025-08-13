from __future__ import annotations

"""Trainerize automation endpoints extracted from `webhook0605.py`.

Usage:
    from trainerize_routes import router as trainerize_router
    app.include_router(trainerize_router)
"""

import logging
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from pb import TrainerizeAutomation

logger = logging.getLogger(__name__)
router = APIRouter()


class ExerciseDefinition(BaseModel):
    name: str
    sets: str
    reps: str


class WorkoutDefinition(BaseModel):
    day_type: str = Field(...,
                          description="Type of workout day. E.g. 'back', 'chest_tris'.")
    exercises_list: List[ExerciseDefinition]


class BuildProgramRequest(BaseModel):
    client_name: str
    program_name: str
    workout_definitions: List[WorkoutDefinition]


@router.post("/trainerize/build-program")
async def build_trainerize_program(request_data: BuildProgramRequest):
    """Initiate building a full training program in Trainerize for a given client."""
    logger.info(
        f"[TRAINERIZE] Build program request for {request_data.client_name}")
    try:
        trainerize = TrainerizeAutomation()
        try:
            workout_defs_dict = [wd.dict()
                                 for wd in request_data.workout_definitions]
            results = trainerize.build_full_program_for_client(
                client_name=request_data.client_name,
                program_name=request_data.program_name,
                workout_definitions=workout_defs_dict,
            )
            critical_failure = any(
                step["step"] in {"navigate_to_client", "navigate_to_training_program",
                                 "create_program"} and not step["success"]
                for step in results
            )
            if critical_failure:
                logger.error(
                    f"[TRAINERIZE] Critical failure for {request_data.client_name}: {results}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": "Failed to build program due to critical error during automation.", "details": results},
                )
            logger.info(
                f"[TRAINERIZE] Program build initiated for {request_data.client_name}")
            return JSONResponse(
                status_code=200,
                content={"message": "Program build process initiated.",
                         "details": results},
            )
        finally:
            trainerize.cleanup()
    except Exception as exc:
        logger.exception("[TRAINERIZE] Unexpected error")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {exc}")
