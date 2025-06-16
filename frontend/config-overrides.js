module.exports = function override(config, env) {
  // Add your webpack configuration overrides here
  return config;
};

// Override the webpack dev server configuration
module.exports.devServer = function(configFunction) {
  return function(proxy, allowedHost) {
    // Create a custom config object
    const config = configFunction(proxy, allowedHost);
    
    // Fix the allowedHosts configuration
    config.allowedHosts = ['localhost', '.localhost', '127.0.0.1'];
    
    return config;
  };
};
