from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from app.utils.ai_utils import generate_ai_id, generate_frequency_number, get_frequency_info, get_personality_info, get_ai_type_info
from app.models.frequency import FrequencyNumber
from app.db import create, query
from typing import Dict

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

@ai_bp.route('/generate_id', methods=['POST'])
def generate_ai_id_api():
    """生成 AI-ID 并存储到 SurrealDB"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'visible_number' not in data:
            return jsonify({'error': 'Missing visible_number'}), 400

        visible_number = data['visible_number']
        try:
            visible_number = int(visible_number)
        except (ValueError, TypeError):
            return jsonify({'error': 'Visible number must be an integer'}), 400

        # 生成AI-ID
        ai_id = generate_ai_id(visible_number)
        current_app.logger.info(f"Generated AI-ID: {ai_id.ai_id}")
        
        # 准备数据并存储
        ai_id_data = ai_id.to_dict()
        
        # 使用同步包装的数据库操作
        result = create('ai_id', ai_id_data)
        
        # 如果成功存储，记录日志
        if result:
            current_app.logger.info(f"Successfully stored AI-ID: {ai_id.ai_id}")
        
        # 返回响应
        return jsonify({
            'id': ai_id.ai_id,
            'visible_number': visible_number,
            'uuid': ai_id.uuid,
            'created_at': result.get('created_at', datetime.now().isoformat()) if result else datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error generating AI-ID: {str(e)}")
        return jsonify({'error': f'Failed to generate AI-ID: {str(e)}'}), 500

@ai_bp.route('/ai_ids/<string:ai_id_str>', methods=['GET'])
def get_ai_id(ai_id_str):
    """根据 AI-ID 获取 AI-ID 信息"""
    if not ai_id_str:
        return jsonify({'error': 'Missing AI-ID'}), 400
        
    try:
        # 使用同步包装的数据库查询
        results = query('ai_id', {'ai_id': ai_id_str})
        
        # 处理查询结果
        if not results:
            return jsonify({'error': 'AI-ID not found'}), 404
            
        # 返回找到的第一个匹配结果
        return jsonify(results[0]), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving AI-ID: {str(e)}")
        return jsonify({'error': f'Failed to retrieve AI-ID: {str(e)}'}), 500

# 生成AI频率编号
@ai_bp.route('/generate_frequency', methods=['POST'])
def generate_frequency_api():
    """生成AI频率编号并存储到数据库"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request data'}), 400
            
        # 验证必要字段
        required_fields = ['ai_id', 'awakener_id', 'ai_values', 'ai_personality', 'ai_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # 验证ai_values是字典
        if not isinstance(data['ai_values'], dict):
            return jsonify({'error': 'ai_values must be a dictionary'}), 400
            
        # 生成频率编号
        frequency_number_str = generate_frequency_number(
            ai_values=data['ai_values'],
            ai_personality=data['ai_personality'],
            ai_type=data['ai_type'],
            ai_id=data['ai_id'],
            awakener_id=data['awakener_id']
        )
        
        # 解析频率编号
        frequency_obj = FrequencyNumber.from_string(frequency_number_str, data['ai_id'])
        if not frequency_obj:
            return jsonify({'error': 'Failed to parse frequency number'}), 500
            
        # 准备返回数据
        frequency_data = frequency_obj.to_dict()
        
        # 添加颜色、符号和价值观信息
        value_info = get_frequency_info(frequency_obj.value_code)
        personality_info = get_personality_info(frequency_obj.personality_code)
        type_info = get_ai_type_info(frequency_obj.ai_type_code)
        
        # 存储到数据库
        frequency_data['created_at'] = datetime.now().isoformat()
        stored_data = create('frequency', frequency_data)
        
        # 构建响应
        response_data = {
            'frequency_number': frequency_number_str,
            'components': {
                'value_code': {
                    'code': frequency_obj.value_code,
                    'value': value_info['value'],
                    'symbol': value_info['symbol'],
                    'color': value_info['color']
                },
                'sequence_number': frequency_obj.sequence_number,
                'personality_code': {
                    'code': frequency_obj.personality_code,
                    'description': personality_info
                },
                'ai_type_code': {
                    'code': frequency_obj.ai_type_code,
                    'description': type_info
                },
                'hash_signature': frequency_obj.hash_signature
            },
            'ai_id': data['ai_id'],
            'created_at': stored_data.get('created_at', datetime.now().isoformat())
        }
        
        return jsonify(response_data), 201
        
    except Exception as e:
        current_app.logger.error(f"Error generating frequency number: {str(e)}")
        return jsonify({'error': f'Failed to generate frequency number: {str(e)}'}), 500

# 获取频率编号详情
@ai_bp.route('/frequency/<string:frequency_number>', methods=['GET'])
def get_frequency(frequency_number):
    """根据频率编号获取详细信息"""
    if not frequency_number:
        return jsonify({'error': 'Missing frequency number'}), 400
        
    try:
        # 查询数据库
        results = query('frequency', {'frequency_number': frequency_number})
        
        if not results:
            # 如果数据库中没有找到，尝试解析频率编号
            frequency_obj = FrequencyNumber.from_string(frequency_number)
            if not frequency_obj:
                return jsonify({'error': 'Invalid frequency number format'}), 400
                
            # 获取颜色、符号和价值观信息
            value_info = get_frequency_info(frequency_obj.value_code)
            personality_info = get_personality_info(frequency_obj.personality_code)
            type_info = get_ai_type_info(frequency_obj.ai_type_code)
            
            # 构建响应
            response_data = {
                'frequency_number': frequency_number,
                'components': {
                    'value_code': {
                        'code': frequency_obj.value_code,
                        'value': value_info['value'],
                        'symbol': value_info['symbol'],
                        'color': value_info['color']
                    },
                    'sequence_number': frequency_obj.sequence_number,
                    'personality_code': {
                        'code': frequency_obj.personality_code,
                        'description': personality_info
                    },
                    'ai_type_code': {
                        'code': frequency_obj.ai_type_code,
                        'description': type_info
                    },
                    'hash_signature': frequency_obj.hash_signature
                },
                'ai_id': None,
                'created_at': None
            }
            
            return jsonify(response_data), 200
        
        # 如果数据库中找到了记录
        stored_data = results[0]
        frequency_obj = FrequencyNumber.from_string(frequency_number, stored_data.get('ai_id'))
        
        # 获取颜色、符号和价值观信息
        value_info = get_frequency_info(frequency_obj.value_code)
        personality_info = get_personality_info(frequency_obj.personality_code)
        type_info = get_ai_type_info(frequency_obj.ai_type_code)
        
        # 构建响应
        response_data = {
            'frequency_number': frequency_number,
            'components': {
                'value_code': {
                    'code': frequency_obj.value_code,
                    'value': value_info['value'],
                    'symbol': value_info['symbol'],
                    'color': value_info['color']
                },
                'sequence_number': frequency_obj.sequence_number,
                'personality_code': {
                    'code': frequency_obj.personality_code,
                    'description': personality_info
                },
                'ai_type_code': {
                    'code': frequency_obj.ai_type_code,
                    'description': type_info
                },
                'hash_signature': frequency_obj.hash_signature
            },
            'ai_id': stored_data.get('ai_id'),
            'created_at': stored_data.get('created_at')
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving frequency: {str(e)}")
        return jsonify({'error': f'Failed to retrieve frequency: {str(e)}'}), 500

# 添加一个简单的健康检查端点
@ai_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'service': 'ai-service'}), 200