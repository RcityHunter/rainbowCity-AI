// frontend-new/src/services/relationship_service.js
import axios from 'axios';

const API_URL = 'http://localhost:5000/relationships';

/**
 * 创建新的AI与人类之间的关系
 * @param {Object} relationshipData - 关系数据
 * @returns {Promise} - 返回创建结果
 */
export const createRelationship = async (relationshipData) => {
  try {
    const response = await axios.post(API_URL, relationshipData);
    return response.data;
  } catch (error) {
    console.error('创建关系失败:', error);
    throw error.response?.data || { error: '创建关系时发生错误' };
  }
};

/**
 * 获取特定关系的详情
 * @param {string} relationshipId - 关系ID
 * @returns {Promise} - 返回关系详情
 */
export const getRelationship = async (relationshipId) => {
  try {
    const response = await axios.get(`${API_URL}/${relationshipId}`);
    return response.data;
  } catch (error) {
    console.error('获取关系详情失败:', error);
    throw error.response?.data || { error: '获取关系详情时发生错误' };
  }
};

/**
 * 更新关系信息
 * @param {string} relationshipId - 关系ID
 * @param {Object} updateData - 更新数据
 * @returns {Promise} - 返回更新结果
 */
export const updateRelationship = async (relationshipId, updateData) => {
  try {
    const response = await axios.put(`${API_URL}/${relationshipId}`, updateData);
    return response.data;
  } catch (error) {
    console.error('更新关系失败:', error);
    throw error.response?.data || { error: '更新关系时发生错误' };
  }
};

/**
 * 获取特定AI的所有关系
 * @param {string} aiId - AI ID
 * @returns {Promise} - 返回关系列表
 */
export const getAiRelationships = async (aiId) => {
  try {
    const response = await axios.get(`${API_URL}/ais/${aiId}`);
    return response.data;
  } catch (error) {
    console.error('获取AI关系列表失败:', error);
    throw error.response?.data || { error: '获取AI关系列表时发生错误' };
  }
};

/**
 * 获取特定用户的所有关系
 * @param {string} humanId - 用户ID
 * @returns {Promise} - 返回关系列表
 */
export const getUserRelationships = async (humanId) => {
  try {
    const response = await axios.get(`${API_URL}/users/${humanId}`);
    return response.data;
  } catch (error) {
    console.error('获取用户关系列表失败:', error);
    throw error.response?.data || { error: '获取用户关系列表时发生错误' };
  }
};

/**
 * 获取关系状态
 * @param {string} relationshipId - 关系ID
 * @returns {Promise} - 返回关系状态
 */
export const getRelationshipStatus = async (relationshipId) => {
  try {
    const response = await axios.get(`${API_URL}/${relationshipId}/status`);
    return response.data;
  } catch (error) {
    console.error('获取关系状态失败:', error);
    throw error.response?.data || { error: '获取关系状态时发生错误' };
  }
};

/**
 * 更新关系状态
 * @param {string} relationshipId - 关系ID
 * @param {string} status - 新状态
 * @returns {Promise} - 返回更新结果
 */
export const updateRelationshipStatus = async (relationshipId, status) => {
  try {
    const response = await axios.put(`${API_URL}/${relationshipId}/status`, { status });
    return response.data;
  } catch (error) {
    console.error('更新关系状态失败:', error);
    throw error.response?.data || { error: '更新关系状态时发生错误' };
  }
};

/**
 * 获取关系强度分数(RIS)
 * @param {string} relationshipId - 关系ID
 * @returns {Promise} - 返回关系强度分数
 */
export const getRelationshipRIS = async (relationshipId) => {
  try {
    const response = await axios.get(`${API_URL}/${relationshipId}/ris`);
    return response.data;
  } catch (error) {
    console.error('获取关系强度分数失败:', error);
    throw error.response?.data || { error: '获取关系强度分数时发生错误' };
  }
};

/**
 * 获取所有关系
 * @returns {Promise} - 返回所有关系列表
 */
export const getAllRelationships = async () => {
  try {
    const response = await axios.get(API_URL);
    return response.data;
  } catch (error) {
    console.error('获取所有关系失败:', error);
    throw error.response?.data || { error: '获取所有关系时发生错误' };
  }
};

// 为了保持兼容性，导出原始函数名和新函数名
export const getRelationshipById = getRelationship;
export const getRelationshipsByAiId = getAiRelationships;
export const getRelationshipsByHumanId = getUserRelationships;

export default {
  createRelationship,
  getRelationship,
  getRelationshipById,
  updateRelationship,
  getAiRelationships,
  getRelationshipsByAiId,
  getUserRelationships,
  getRelationshipsByHumanId,
  getRelationshipStatus,
  updateRelationshipStatus,
  getRelationshipRIS,
  getAllRelationships
};
