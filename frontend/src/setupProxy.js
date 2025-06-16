const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // 设置代理配置，将API请求转发到后端服务器
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5000',
      changeOrigin: true,
      pathRewrite: {
        '^/api': '/api', // 保持路径不变
      },
      onProxyReq: (proxyReq, req, res) => {
        // 记录请求日志
        console.log(`[Proxy] ${req.method} ${req.path} -> ${proxyReq.protocol}//${proxyReq.host}${proxyReq.path}`);
      },
      onError: (err, req, res) => {
        console.error('[Proxy Error]', err);
        res.writeHead(500, {
          'Content-Type': 'application/json',
        });
        res.end(JSON.stringify({ error: 'Proxy Error', message: err.message }));
      }
    })
  );
};
