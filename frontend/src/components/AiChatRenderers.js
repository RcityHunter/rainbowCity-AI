import React from 'react';

// 渲染消息内容
export const renderMessageContent = (message) => {
  // 根据消息类型渲染不同内容
  switch (message.type) {
    case 'text':
      return (
        <div className="message-content">
          {message.isTyping ? message.displayedContent : message.content}
        </div>
      );
      
    case 'image':
      return (
        <div className="message-content">
          <div className="message-image-container">
            <img 
              src={message.content} 
              alt="用户上传的图片" 
              className="message-image"
              loading="lazy"
            />
          </div>
        </div>
      );
      
    case 'audio':
      return (
        <div className="message-content">
          <audio controls src={message.content} className="message-audio">
            您的浏览器不支持音频播放
          </audio>
        </div>
      );
      
    case 'video':
      return (
        <div className="message-content">
          <video 
            controls 
            src={message.content} 
            className="message-video"
            width="320"
          >
            您的浏览器不支持视频播放
          </video>
        </div>
      );
      
    case 'document':
      return (
        <div className="message-content">
          <div className="document-preview">
            <i className="fas fa-file-alt document-icon"></i>
            <a 
              href={message.content} 
              target="_blank" 
              rel="noopener noreferrer"
              className="document-link"
            >
              {message.name || '查看文档'}
            </a>
          </div>
        </div>
      );
      
    case 'mixed':
      // 混合类型，包含文本和其他内容
      return (
        <div className="message-content">
          {/* 文本部分 */}
          {message.content && (
            <div className="message-text">
              {message.content}
            </div>
          )}
          
          {/* 附件部分 */}
          {message.attachment && message.attachment.type === 'image' && (
            <div className="message-image-container">
              <img 
                src={message.attachment.preview || message.attachment.content} 
                alt="用户上传的图片" 
                className="message-image"
                loading="lazy"
              />
            </div>
          )}
        </div>
      );
      
    case 'tool_output':
      // 工具输出
      return (
        <div className="message-content tool-output">
          <div className="tool-output-header">
            <i className="fas fa-tools"></i> 工具输出
          </div>
          <div className="tool-output-content">
            {message.content}
          </div>
          {message.tool_calls && (
            <div className="tool-calls">
              {message.tool_calls.map((tool, index) => (
                <div key={index} className="tool-call">
                  <div className="tool-name">{tool.name}</div>
                  {tool.parameters && (
                    <div className="tool-parameters">
                      <pre>{JSON.stringify(tool.parameters, null, 2)}</pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      );
      
    default:
      return (
        <div className="message-content">
          {message.content}
        </div>
      );
  }
};

// 渲染附件预览
export const renderAttachmentPreviews = ({ attachments, boundRemoveAttachment }) => {
  if (attachments.length === 0) return null;
  
  return (
    <div className="attachment-previews">
      {attachments.map(attachment => (
        <div key={attachment.id} className="attachment-preview">
          {attachment.type === 'image' ? (
            <div className="image-preview">
              <img 
                src={attachment.preview} 
                alt={attachment.name || '图片预览'} 
                className="preview-image"
              />
              <button 
                className="remove-attachment" 
                onClick={() => boundRemoveAttachment(attachment.id)}
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
          ) : attachment.type === 'audio' ? (
            <div className="audio-preview">
              <i className="fas fa-file-audio"></i>
              <span className="file-name">{attachment.name}</span>
              <button 
                className="remove-attachment" 
                onClick={() => boundRemoveAttachment(attachment.id)}
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
          ) : attachment.type === 'video' ? (
            <div className="video-preview">
              <i className="fas fa-file-video"></i>
              <span className="file-name">{attachment.name}</span>
              <button 
                className="remove-attachment" 
                onClick={() => boundRemoveAttachment(attachment.id)}
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
          ) : (
            <div className="document-preview">
              <i className="fas fa-file-alt"></i>
              <span className="file-name">{attachment.name}</span>
              <button 
                className="remove-attachment" 
                onClick={() => boundRemoveAttachment(attachment.id)}
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// 渲染已保存的图片
export const renderSavedImages = ({ savedAttachments, boundRemoveAttachment }) => {
  if (!savedAttachments || savedAttachments.length === 0) return null;
  
  // 只显示图片类型的附件
  const savedImages = savedAttachments.filter(att => att.type === 'image');
  if (savedImages.length === 0) return null;
  
  return (
    <div className="saved-images">
      <div className="saved-images-header">已保存的图片</div>
      <div className="saved-images-grid">
        {savedImages.map(image => (
          <div key={image.id} className="saved-image-item">
            <img 
              src={image.preview} 
              alt={image.name || '已保存图片'} 
              className="saved-image-thumbnail"
            />
            <button 
              className="remove-saved-image" 
              onClick={() => boundRemoveAttachment(image.id)}
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
