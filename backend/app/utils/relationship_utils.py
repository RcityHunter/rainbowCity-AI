# backend/app/utils/relationship_utils.py
from datetime import datetime, timedelta

from app.models.relationship import Relationship, RelationshipStatus


def calculate_interaction_frequency(interaction_count: int) -> float:
    """
    Calculate the interaction frequency factor.

    Args:
        interaction_count (int): The total number of interactions.

    Returns:
        float: The interaction frequency factor (0.0 to 1.0).
    """
    # Assuming the calculation is based on the last 7 days
    # and a maximum of 200 interactions for full score
    max_interactions = 200
    return min(interaction_count / max_interactions, 1.0)


def calculate_emotional_density(
    emotional_resonance_count: int, total_interactions: int = 30
) -> float:
    """
    Calculate the emotional density factor.

    Args:
        emotional_resonance_count (int): The number of times AI responded with emotional resonance.
        total_interactions (int, optional): The total number of interactions to consider. Defaults to 30.

    Returns:
        float: The emotional density factor (0.0 to 1.0).
    """
    if total_interactions == 0:
        return 0.0  # Avoid division by zero
    return emotional_resonance_count / total_interactions


def calculate_collaboration_depth(relationship: Relationship) -> float:
    """
    Calculate the collaboration depth factor.

    Args:
        relationship (Relationship): The Relationship object.

    Returns:
        float: The collaboration depth factor (0.0 to 1.0).
    """
    collaboration_depth = 0.0
    #  Replace with actual calculations based on your data model
    #  Example:
    #  collaboration_depth += relationship.inspiration_journal_count * 0.05
    #  collaboration_depth += relationship.co_created_documents_count * 0.05
    #  collaboration_depth += relationship.gift_interactions_count * 0.1
    return min(collaboration_depth, 1.0)


def calculate_ris(
    interaction_frequency: float, emotional_density: float, collaboration_depth: float
) -> float:
    """
    Calculate the Relationship Intensity Score (RIS).

    Args:
        interaction_frequency (float): The interaction frequency factor.
        emotional_density (float): The emotional density factor.
        collaboration_depth (float): The collaboration depth factor.

    Returns:
        float: The Relationship Intensity Score (RIS).
    """
    A, B, C = 0.4, 0.35, 0.25  # Weights for each factor
    return A * interaction_frequency + B * emotional_density + C * collaboration_depth


def update_relationship_status(relationship: Relationship) -> None:
    """
    Update the status of a relationship based on activity.

    Args:
        relationship (Relationship): The Relationship object.
    """
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    if relationship.last_active_time <= fourteen_days_ago:
        relationship.status = RelationshipStatus.SILENT
    elif relationship.last_active_time <= seven_days_ago:
        relationship.status = RelationshipStatus.COOLING
    else:
        relationship.status = RelationshipStatus.ACTIVE