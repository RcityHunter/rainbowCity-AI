// 这是一个临时文件，用于修复超时设置
// 将下面的代码片段替换到AiChatHandlers.js中的相应位置

// 创建超时控制器
const controller = new AbortController();
const timeoutId = setTimeout(() => {
  controller.abort();
  console.error(`[ERROR] 请求超时: ${chatEndpoint}`);
}, API_CONFIG.TIMEOUT); // 使用配置文件中的超时时间
