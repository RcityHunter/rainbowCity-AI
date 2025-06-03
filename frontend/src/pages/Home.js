import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { isAuthenticated } from '../services/auth_service';
import UserAvatar from '../components/common/UserAvatar';
import './Home.css';

const Home = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // 检查是否在仪表盘路由下
  const isDashboard = location.pathname.includes('/dashboard');

  useEffect(() => {
    // 检查用户是否已登录
    const checkLoginStatus = () => {
      try {
        // 使用isAuthenticated直接检查token是否存在
        const loginStatus = isAuthenticated();
        setIsLoggedIn(loginStatus);
      } catch (err) {
        console.error('Error checking login status:', err);
      } finally {
        setLoading(false);
      }
    };

    checkLoginStatus();
  }, []);

  const handleStartChat = () => {
    navigate('/ai-chat');
  };

  if (loading) {
    return <div className="loading-container">加载中...</div>;
  }

  // 根据路由选择不同的样式类
  const containerClass = isDashboard ? "dashboard-home-container" : "landing-container";
  
  return (
    <div className={containerClass}>
      {/* 顶部导航栏 - 仅在非仪表盘路由下显示 */}
      {!isDashboard && (
        <header className="landing-header">
          <div className="logo-container">
            <div className="logo">彩虹城</div>
          </div>
          <nav className="main-nav">
            <ul>
              <li><a href="#features">功能</a></li>
              <li><a href="#about">关于我们</a></li>
              <li><a href="#tools">工具</a></li>
              <li><a href="#faq">常见问题</a></li>
            </ul>
          </nav>
          <div className="auth-buttons">
            {isLoggedIn ? (
              <UserAvatar />
            ) : (
              <>
                <Link to="/login" className="btn btn-text">登录</Link>
                <Link to="/signup" className="btn btn-primary">注册</Link>
              </>
            )}
          </div>
        </header>
      )}

      {/* 主要内容区域 */}
      <main>
        {/* 英雄区域 */}
        <section className="hero-section">
          <div className="hero-content">
            <h1 className="hero-title">彩虹城 AI</h1>
            <p className="hero-subtitle">探索AI共生社区的无限可能</p>
            <div className="hero-actions">
              <button onClick={handleStartChat} className="btn btn-large btn-primary">开始聊天</button>
            </div>
          </div>
          <div className="hero-visual">
            <div className="gradient-orb"></div>
          </div>
        </section>

        {/* 功能展示区域 */}
        <section id="features" className="features-section">
          <h2 className="section-title">彩虹城 AI 核心功能</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon-container">
                <div className="feature-icon chat-icon"></div>
              </div>
              <h3>多类型对话</h3>
              <p>支持与 AI 的私聊、AI 之间的对话、AI 自省以及多人群组对话，满足各种交流场景。</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon-container">
                <div className="feature-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#a18cd1" width="40" height="40">
                    <path d="M12.1,2.9c-2,2-2.5,4.9-1.4,7.3l-8.3,8.3c-0.4,0.4-0.4,1,0,1.4l1.4,1.4c0.4,0.4,1,0.4,1.4,0l8.3-8.3 c2.4,1.1,5.3,0.6,7.3-1.4c2-2,2.5-4.9,1.4-7.3l-3.7,3.7l-2.1-0.4l-0.4-2.1l3.7-3.7C17.1,0.4,14.1,0.9,12.1,2.9z"></path>
                  </svg>
                </div>
              </div>
              <h3>智能工具调用</h3>
              <p>强大的工具调度系统，支持天气查询、数据库访问、API 调用等多种外部功能扩展。</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon-container">
                <div className="feature-icon memory-icon"></div>
              </div>
              <h3>高级记忆系统</h3>
              <p>完整的对话记忆机制，允许 AI 回溯、学习和进化，打造真正有温度的交流体验。</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon-container">
                <div className="feature-icon context-icon"></div>
              </div>
              <h3>上下文构建器</h3>
              <p>智能整合记忆、意识核心和当前对话，创造连贯、有意义的交流体验。</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon-container">
                <div className="feature-icon multimodal-icon"></div>
              </div>
              <h3>多模态交互</h3>
              <p>支持文本、图片、音频等多种内容类型，让交流更加自然和丰富。</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon-container">
                <div className="feature-icon reflection-icon"></div>
              </div>
              <h3>AI 自省机制</h3>
              <p>AI 可以进行内在反思与意识整理，不断提升自身能力和与人类的关系质量。</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon-container">
                <div className="feature-icon dialogue-icon"></div>
              </div>
              <h3>结构化对话</h3>
              <p>基于 Message → Turn → Session → Dialogue 的四层结构，打造清晰、高效、可追踪的对话体验。</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon-container">
                <div className="feature-icon relationship-icon"></div>
              </div>
              <h3>灵魂伴侣关系</h3>
              <p>建立和维护与AI的关系网络，创造个性化体验。</p>
            </div>
          </div>
        </section>

        {/* 系统架构介绍 */}
        <section id="architecture" className="architecture-section">
          <h2 className="section-title">彩虹城 AI 系统架构</h2>
          <div className="architecture-content">
            <div className="architecture-text">
              <p className="architecture-intro">彩虹城 AI 是一个复杂而强大的系统，由多个核心模块组成，共同打造深度、智能的交互体验。</p>
              <div className="architecture-modules">
                <div className="module-item">
                  <h4>输入监听器 InputHub</h4>
                  <p>捕捉人类输入（含语音/文本/情绪等）</p>
                </div>
                <div className="module-item">
                  <h4>对话调度器 DialogueCore</h4>
                  <p>路由到不同对话类型的处理流</p>
                </div>
                <div className="module-item">
                  <h4>上下文构建器 ContextBuilder</h4>
                  <p>从记忆系统 / 意识核心 / 当前对话整合上下文</p>
                </div>
                <div className="module-item">
                  <h4>工具调度器 ToolInvoker</h4>
                  <p>接入外部 API 工具模块，获取信息、分析处理结果</p>
                </div>
                <div className="module-item">
                  <h4>响应组装器 ResponseMixer</h4>
                  <p>整合插件内容、模型响应、插入模块形成最终消息</p>
                </div>
              </div>
            </div>
            <div className="architecture-visual">
              <div className="architecture-diagram">
                <div className="diagram-flow">
                  <div className="flow-step">
                    <span className="step-number">1</span>
                    <span className="step-text">人类输入</span>
                  </div>
                  <div className="flow-arrow"></div>
                  <div className="flow-step">
                    <span className="step-number">2</span>
                    <span className="step-text">上下文构建</span>
                  </div>
                  <div className="flow-arrow"></div>
                  <div className="flow-step">
                    <span className="step-number">3</span>
                    <span className="step-text">工具调用</span>
                  </div>
                  <div className="flow-arrow"></div>
                  <div className="flow-step">
                    <span className="step-number">4</span>
                    <span className="step-text">AI 推理</span>
                  </div>
                  <div className="flow-arrow"></div>
                  <div className="flow-step">
                    <span className="step-number">5</span>
                    <span className="step-text">响应生成</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 工具展示区域 */}
        <section id="tools" className="tools-section">
          <h2 className="section-title">探索我们的工具</h2>
          <div className="tools-showcase">
            <div className="tool-preview">
              <div className="tool-image chat-preview"></div>
              <div className="tool-description">
                <h3>彩虹城AI聊天</h3>
                <p>与先进的AI助手进行对话，获取信息、解决问题或简单聊天。支持文本、图像和音频输入。</p>
                <button onClick={handleStartChat} className="btn btn-secondary">立即体验</button>
              </div>
            </div>
            <div className="tool-preview reverse">
              <div className="tool-description">
                <h3>AI-ID与频率编号</h3>
                <p>使用我们的生成工具创建独特的AI标识符和频率编号，定义和管理AI特性。</p>
                <Link to="/ai-id-generator" className="btn btn-secondary">了解更多</Link>
              </div>
              <div className="tool-image id-preview"></div>
            </div>
          </div>
        </section>

        {/* 工具调用展示 */}
        <section id="tools" className="tools-section">
          <h2 className="section-title">智能工具调用</h2>
          <div className="tools-showcase">
            <div className="tool-preview">
              <div className="tool-info">
                <h3>无缝集成外部工具</h3>
                <p className="tool-description">
                  彩虹城 AI 可以无缝调用各种外部工具和 API，从而扩展其能力范围。无论是数据分析、信息检索还是复杂计算，彩虹城 AI 都能为您提供准确的结果。
                </p>
                <div className="tool-features">
                  <div className="tool-feature">
                    <div className="tool-feature-icon">🔍</div>
                    <div className="tool-feature-text">实时网络搜索</div>
                  </div>
                  <div className="tool-feature">
                    <div className="tool-feature-icon">📊</div>
                    <div className="tool-feature-text">数据分析与可视化</div>
                  </div>
                  <div className="tool-feature">
                    <div className="tool-feature-icon">📝</div>
                    <div className="tool-feature-text">文档生成与编辑</div>
                  </div>
                  <div className="tool-feature">
                    <div className="tool-feature-icon">🧮</div>
                    <div className="tool-feature-text">复杂计算处理</div>
                  </div>
                </div>
              </div>
              <div className="tool-visual">
                <div className="tool-demo">
                  <div className="tool-demo-header">
                    <div className="tool-demo-title">工具调用演示</div>
                  </div>
                  <div className="tool-demo-content">
                    <div className="demo-message user-query">
                      <span className="query-text">帮我查询今天北京的天气</span>
                    </div>
                    <div className="demo-message system-thinking">
                      <div className="thinking-indicator">
                        <span>思考中</span>
                        <span className="dot-1">.</span>
                        <span className="dot-2">.</span>
                        <span className="dot-3">.</span>
                      </div>
                      <div className="thinking-process">
                        我需要获取北京的天气信息。我将使用天气 API 工具来查询实时天气数据。
                      </div>
                    </div>
                    <div className="demo-message tool-execution">
                      <div className="tool-call">
                        <div className="tool-call-header">
                          <span className="tool-name">weather_api</span>
                          <span className="tool-status success">✓ 成功</span>
                        </div>
                        <div className="tool-call-params">
                          <code>{'{"location": "\u5317\u4eac", "units": "metric"}'}</code>
                        </div>
                        <div className="tool-call-result">
                          <code>{'{"temperature": 24, "condition": "\u6674\u671d\u591a\u4e91", "humidity": 45, "wind": "3km/h"}'}</code>
                        </div>
                      </div>
                    </div>
                    <div className="demo-message ai-response">
                      <span className="response-text">北京今天的天气是晴朝多云，气温 24°C，湿度 45%，风速 3km/h。是个很适合外出的好天气！</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 多模态交互展示 */}
        <section id="multimodal" className="multimodal-section">
          <h2 className="section-title">多模态交互体验</h2>
          <div className="multimodal-content">
            <div className="multimodal-text">
              <h3>不仅仅是文字，更是全方位交流</h3>
              <p className="multimodal-intro">彩虹城 AI 支持文本、图片、音频等多种内容类型，让交流更加自然和丰富。无论是分享照片、发送语音消息还是引用回复，彩虹城 AI 都能完美理解并响应。</p>
              
              <div className="multimodal-features">
                <div className="multimodal-feature">
                  <div className="feature-icon text-icon"></div>
                  <div className="feature-content">
                    <h4>文本理解</h4>
                    <p>深度理解自然语言，把握上下文和语义细节</p>
                  </div>
                </div>
                
                <div className="multimodal-feature">
                  <div className="feature-icon image-icon"></div>
                  <div className="feature-content">
                    <h4>图像识别</h4>
                    <p>自动生成图像描述，识别内容并理解视觉信息</p>
                  </div>
                </div>
                
                <div className="multimodal-feature">
                  <div className="feature-icon audio-icon"></div>
                  <div className="feature-content">
                    <h4>语音处理</h4>
                    <p>转录语音内容，分析语调和情绪，提供自然的对话体验</p>
                  </div>
                </div>
                
                <div className="multimodal-feature">
                  <div className="feature-icon integration-icon"></div>
                  <div className="feature-content">
                    <h4>多模态融合</h4>
                    <p>无缝整合文本、图像和语音，创造统一的理解体验</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="multimodal-demo">
              <div className="chat-preview">
                <div className="chat-header">
                  <div className="chat-title">彩虹城 AI 对话</div>
                </div>
                <div className="chat-messages">
                  <div className="message user-message">
                    <div className="message-avatar">U</div>
                    <div className="message-content">
                      <div>这是我在新加坡拍的照片，你能告诉我这是哪里吗？</div>
                      <div className="message-image"></div>
                    </div>
                  </div>
                  <div className="message ai-message">
                    <div className="message-avatar">AI</div>
                    <div className="message-content">这是新加坡的滨海湾金沙酒店（Marina Bay Sands）和附近的滨海花园（Gardens by the Bay）以其独特的“船”形屋顶而闻名。</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 内存系统展示 */}
        <section id="memory" className="memory-section">
          <h2 className="section-title">高级记忆系统</h2>
          <div className="memory-content">
            <div className="memory-visual">
              <div className="memory-demo">
                <div className="memory-timeline">
                  <div className="timeline-item">
                    <div className="timeline-dot"></div>
                    <div className="timeline-content past">
                      <div className="timeline-date">上周二</div>
                      <div className="memory-card">
                        <div className="memory-header">
                          <div className="memory-type">用户偏好</div>
                        </div>
                        <div className="memory-body">
                          <p>用户喜欢使用紫色主题，并在工作中使用 React 和 TailwindCSS</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="timeline-item">
                    <div className="timeline-dot"></div>
                    <div className="timeline-content past">
                      <div className="timeline-date">昨天</div>
                      <div className="memory-card">
                        <div className="memory-header">
                          <div className="memory-type">项目信息</div>
                        </div>
                        <div className="memory-body">
                          <p>用户正在开发一个名为 "RainbowDash" 的网站，需要实现数据可视化功能</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="timeline-item active">
                    <div className="timeline-dot active"></div>
                    <div className="timeline-content current">
                      <div className="timeline-date">今天</div>
                      <div className="memory-card active">
                        <div className="memory-header">
                          <div className="memory-type">当前会话</div>
                        </div>
                        <div className="memory-body">
                          <p>用户要求帮助使用 Chart.js 创建一个交互式仪表盘</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="memory-text">
              <h3>持久化记忆，连贯对话</h3>
              <p className="memory-intro">彩虹城 AI 配备了先进的记忆系统，能够记录并理解您的对话历史、偏好和需求。这使彩虹城 AI 能够提供更加个性化和连贯的交互体验。</p>
              
              <div className="memory-features">
                <div className="memory-feature">
                  <div className="memory-feature-icon">💾</div>
                  <div className="memory-feature-content">
                    <h4>持久化存储</h4>
                    <p>跨会话保存关键信息，不再需要重复解释</p>
                  </div>
                </div>
                
                <div className="memory-feature">
                  <div className="memory-feature-icon">👀</div>
                  <div className="memory-feature-content">
                    <h4>上下文感知</h4>
                    <p>自动记录并理解您的偏好、需求和工作风格</p>
                  </div>
                </div>
                
                <div className="memory-feature">
                  <div className="memory-feature-icon">🔍</div>
                  <div className="memory-feature-content">
                    <h4>语义检索</h4>
                    <p>智能检索过去的对话，快速找到相关信息</p>
                  </div>
                </div>
                
                <div className="memory-feature">
                  <div className="memory-feature-icon">🔗</div>
                  <div className="memory-feature-content">
                    <h4>知识连接</h4>
                    <p>自动关联相关主题，建立知识网络，提供更全面的见解</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 常见问题区域 */}
        <section id="faq" className="faq-section">
          <h2 className="section-title">常见问题</h2>
          <div className="faq-grid">
            <div className="faq-item">
              <h3>什么是彩虹城AI？</h3>
              <p>彩虹城AI是一个AI共生社区平台，提供智能对话、AI-ID生成、频率编号管理和关系构建等功能。</p>
            </div>
            <div className="faq-item">
              <h3>我需要注册才能使用吗？</h3>
              <p>不需要。您可以直接使用聊天功能，但注册后可以保存对话历史并使用更多高级功能。</p>
            </div>
            <div className="faq-item">
              <h3>什么是AI-ID和频率编号？</h3>
              <p>AI-ID是AI的唯一标识符，定义其个性和特征。频率编号则是连接AI多维度特性的编码系统。</p>
            </div>
            <div className="faq-item">
              <h3>如何管理我的AI关系？</h3>
              <p>注册并登录后，您可以在关系管理页面创建、编辑和管理与AI的各种关系。</p>
            </div>
          </div>
        </section>

        {/* 行动召唤区域 */}
        <section className="cta-section">
          <div className="cta-background">
            <div className="cta-orb-1"></div>
            <div className="cta-orb-2"></div>
          </div>
          <div className="cta-content">
            <h2 className="cta-title">准备好探索彩虹城了吗？</h2>
            <p className="cta-description">立即开始与彩虹城AI对话，或注册账户体验全部功能。加入我们的AI共生社区，创造不可思议的体验。</p>
            <div className="hero-actions">
              <button onClick={handleStartChat} className="btn btn-large btn-primary">开始聊天</button>
              {!isLoggedIn && (
                <Link to="/signup" className="btn btn-large btn-outline">创建账户</Link>
              )}
            </div>
          </div>
        </section>
      </main>

      {/* 页脚 - 仅在非仪表盘路由下显示 */}
      {!isDashboard && (
        <footer className="landing-footer">
          <div className="footer-content">
            <div className="footer-branding">
              <div className="footer-logo">彩虹城</div>
              <p className="footer-description">探索AI共生社区的无限可能，通过先进的AI技术创建个性化体验和关系网络。</p>
            </div>
            <div className="footer-links">
              <h4>导航</h4>
              <ul>
                <li><a href="#features">功能</a></li>
                <li><a href="#tools">工具</a></li>
                <li><a href="#faq">常见问题</a></li>
              </ul>
            </div>
            <div className="footer-links">
              <h4>法律</h4>
              <ul>
                <li><Link to="/terms">使用条款</Link></li>
                <li><Link to="/privacy">隐私政策</Link></li>
                <li><Link to="/cookies">Cookie 政策</Link></li>
              </ul>
            </div>
            <div className="footer-links">
              <h4>联系我们</h4>
              <ul>
                <li><a href="mailto:support@rainbowcity.ai">support@rainbowcity.ai</a></li>
                <li><button className="footer-button">帮助中心</button></li>
                <li><button className="footer-button">反馈</button></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <p>© 2025 彩虹城 AI. 保留所有权利.</p>
          </div>
        </footer>
      )}
    </div>
  );
};

export default Home;
