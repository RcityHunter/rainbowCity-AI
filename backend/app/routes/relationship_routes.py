# backend/app/routes/relationship_routes.py
from typing import List, Dict, Any
from datetime import datetime
import uuid

from flask import Blueprint, jsonify, request, current_app, abort
from app.models.relationship import Relationship, RelationshipStatus
from app.utils.relationship_utils import (
    calculate_interaction_frequency,
    calculate_emotional_density,
    calculate_collaboration_depth,
    calculate_ris,
    update_relationship_status,
)
from app.db import create, query, update as db_update

relationship_bp = Blueprint("relationships", __name__, url_prefix="/relationships")


@relationship_bp.route("", methods=["POST"])
def create_relationship() -> tuple:
    """
    Create a new relationship between an AI and a human.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        # Validate input data
        required_fields = ["ai_id", "human_id"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": f"Missing required fields: {required_fields}"}), 400
            
        # Generate relationship_id if not provided
        if "relationship_id" not in data:
            data["relationship_id"] = f"rel-{str(uuid.uuid4())}" 
            
        # Set timestamps if not provided
        now = datetime.utcnow().isoformat()
        if "init_timestamp" not in data:
            data["init_timestamp"] = now
        if "last_active_time" not in data:
            data["last_active_time"] = now
            
        # Set default values
        if "status" not in data:
            data["status"] = RelationshipStatus.ACTIVE.value
            
        # Store in SurrealDB
        result = create('relationship', data)
        
        if result:
            current_app.logger.info(f"Successfully created relationship: {data['relationship_id']}")
            return jsonify({
                "message": "Relationship created", 
                "relationship_id": data["relationship_id"]
            }), 201
        else:
            return jsonify({"error": "Failed to create relationship"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error creating relationship: {str(e)}")
        return jsonify({"error": f"Failed to create relationship: {str(e)}"}), 500


@relationship_bp.route("/<string:relationship_id>", methods=["GET"])
def get_relationship(relationship_id: str) -> tuple:
    """
    Get details of a specific relationship.

    Args:
        relationship_id (str): The ID of the relationship.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    try:
        # 查询SurrealDB
        results = query('relationship', {'relationship_id': relationship_id})
        
        # 处理查询结果
        if not results:
            return jsonify({'error': 'Relationship not found'}), 404
            
        # 返回找到的第一个匹配结果
        return jsonify(results[0]), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving relationship: {str(e)}")
        return jsonify({'error': f'Failed to retrieve relationship: {str(e)}'}), 500


@relationship_bp.route("/<string:relationship_id>", methods=["PUT"])
def update_relationship(relationship_id: str) -> tuple:
    """
    Update details of a specific relationship.

    Args:
        relationship_id (str): The ID of the relationship.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        # 首先查询关系是否存在
        results = query('relationship', {'relationship_id': relationship_id})
        if not results:
            return jsonify({"error": "Relationship not found"}), 404
            
        # 更新时间戳格式（如果提供）
        if "last_active_time" in data and data["last_active_time"] is not None:
            try:
                # 尝试解析时间戳，确保格式正确
                datetime.fromisoformat(data["last_active_time"])
            except ValueError:
                # 如果格式不正确，使用当前时间
                data["last_active_time"] = datetime.utcnow().isoformat()
                
        # 使用SurrealDB的更新函数
        result = db_update('relationship', relationship_id, data)
        
        if result:
            current_app.logger.info(f"Successfully updated relationship: {relationship_id}")
            return jsonify({"message": "Relationship updated"}), 200
        else:
            return jsonify({"error": "Failed to update relationship"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error updating relationship: {str(e)}")
        return jsonify({"error": f"Failed to update relationship: {str(e)}"}), 500


@relationship_bp.route("/ais/<string:ai_id>", methods=["GET"])
def get_ai_relationships(ai_id: str) -> tuple:
    """
    Get all relationships for a specific AI.

    Args:
        ai_id (str): The ID of the AI.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    try:
        # 查询SurrealDB中与特定AI相关的所有关系
        results = query('relationship', {'ai_id': ai_id})
        
        # 即使没有找到关系，也返回空列表而不是错误
        return jsonify(results if results else []), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving AI relationships: {str(e)}")
        return jsonify({'error': f'Failed to retrieve AI relationships: {str(e)}'}), 500


@relationship_bp.route("/users/<string:human_id>", methods=["GET"])
def get_user_relationships(human_id: str) -> tuple:
    """
    Get all relationships for a specific user.

    Args:
        human_id (str): The ID of the user.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    try:
        # 查询SurrealDB中与特定用户相关的所有关系
        results = query('relationship', {'human_id': human_id})
        
        # 即使没有找到关系，也返回空列表而不是错误
        return jsonify(results if results else []), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving user relationships: {str(e)}")
        return jsonify({'error': f'Failed to retrieve user relationships: {str(e)}'}), 500


@relationship_bp.route("/<string:relationship_id>/status", methods=["GET"])
def get_relationship_status(relationship_id: str) -> tuple:
    """
    Get the current status of a relationship.

    Args:
        relationship_id (str): The ID of the relationship.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    try:
        # 查询SurrealDB
        results = query('relationship', {'relationship_id': relationship_id})
        
        # 处理查询结果
        if not results:
            return jsonify({'error': 'Relationship not found'}), 404
            
        # 返回状态信息
        relationship = results[0]
        if 'status' in relationship:
            return jsonify({"status": relationship['status']}), 200
        else:
            # 如果没有状态字段，默认为活跃状态
            return jsonify({"status": RelationshipStatus.ACTIVE.value}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving relationship status: {str(e)}")
        return jsonify({'error': f'Failed to retrieve relationship status: {str(e)}'}), 500


@relationship_bp.route("/<string:relationship_id>/status", methods=["PUT"])
def update_relationship_status_route(relationship_id: str) -> tuple:
    """
    Update the status of a relationship.

    Args:
        relationship_id (str): The ID of the relationship.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    try:
        data = request.get_json()
        if not data or "status" not in data:
            return jsonify({"error": "Missing 'status' in request data"}), 400

        # 验证状态是否有效
        try:
            new_status = RelationshipStatus(data["status"])
            status_value = new_status.value
        except ValueError:
            return jsonify({"error": f"Invalid status: {data['status']}"}), 400

        # 首先查询关系是否存在
        results = query('relationship', {'relationship_id': relationship_id})
        if not results:
            return jsonify({"error": "Relationship not found"}), 404
            
        # 使用SurrealDB的更新函数更新状态
        update_data = {"status": status_value}
        result = db_update('relationship', relationship_id, update_data)
        
        if result:
            current_app.logger.info(f"Successfully updated relationship status: {relationship_id} to {status_value}")
            return jsonify({"message": "Relationship status updated"}), 200
        else:
            return jsonify({"error": "Failed to update relationship status"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error updating relationship status: {str(e)}")
        return jsonify({"error": f"Failed to update relationship status: {str(e)}"}), 500


@relationship_bp.route("/<string:relationship_id>/ris", methods=["GET"])
def get_relationship_ris(relationship_id: str) -> tuple:
    """
    Get the Relationship Intensity Score (RIS) for a relationship.

    Args:
        relationship_id (str): The ID of the relationship.

    Returns:
        tuple: A tuple containing the JSON response and the HTTP status code.
    """
    try:
        # 查询SurrealDB
        results = query('relationship', {'relationship_id': relationship_id})
        
        # 处理查询结果
        if not results:
            return jsonify({'error': 'Relationship not found'}), 404
            
        # 获取关系数据
        relationship = results[0]
        
        # 计算RIS分数
        interaction_count = relationship.get('interaction_count', 0)
        emotional_resonance_count = relationship.get('emotional_resonance_count', 0)
        
        interaction_frequency = calculate_interaction_frequency(interaction_count)
        emotional_density = calculate_emotional_density(emotional_resonance_count)
        collaboration_depth = calculate_collaboration_depth(relationship)
        
        ris = calculate_ris(interaction_frequency, emotional_density, collaboration_depth)
        
        # 返回结果以及各个组成部分的分数
        return jsonify({
            "ris": ris,
            "components": {
                "interaction_frequency": interaction_frequency,
                "emotional_density": emotional_density,
                "collaboration_depth": collaboration_depth
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error calculating relationship RIS: {str(e)}")
        return jsonify({'error': f'Failed to calculate relationship RIS: {str(e)}'}), 500