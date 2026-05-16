import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Laptop, ShoppingCart } from 'lucide-react';
import './App.css';

// عشوائي لتحديد جلسة العميل
const SESSION_ID = "web_user_" + Math.floor(Math.random() * 10000);
const API_URL = "http://localhost:8000/api/chat";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const messagesEndRef = useRef(null);

  // التمرير التلقائي لآخر رسالة
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // رسالة الترحيب
  useEffect(() => {
    sendMessage("/start", true);
  }, []);

  const sendMessage = async (text, isHidden = false) => {
    if (!text.trim()) return;

    if (!isHidden) {
      setMessages(prev => [...prev, { text, sender: 'user' }]);
      setInput('');
    }

    setIsLoading(true);

    try {
      const response = await axios.post(API_URL, {
        session_id: SESSION_ID,
        message: text
      });

      const { reply, products: newProducts } = response.data;
      
      setMessages(prev => [...prev, { text: reply, sender: 'bot' }]);
      
      if (newProducts && newProducts.length > 0) {
        setProducts(newProducts);
      }

    } catch (error) {
      console.error("Error sending message:", error);
      setMessages(prev => [...prev, { text: "عذراً، هناك مشكلة في الاتصال بالسيرفر.", sender: 'bot' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBuyClick = (product) => {
    const buyIntent = `قررت شراء المنتج: ${product.metadata.name} (الكود: ${product.id}). ماذا أفعل الآن؟`;
    sendMessage(buyIntent, false);
  };

  return (
    <div className="app-container" dir="rtl">
      
      {/* القسم الأيسر: عرض المنتجات (مخفي افتراضياً ويظهر عند وجود منتجات) */}
      <div className={`showcase-area ${products.length > 0 ? 'visible' : 'hidden'}`}>
        <h1 className="showcase-title">Smart Store - سمارت ستور</h1>
        
        <div className="products-grid">
          {products.map((p, idx) => (
            <div key={idx} className="product-card glass-panel">
              <div className="product-image-placeholder" style={{ padding: p.metadata.image ? 0 : '1.5rem', overflow: 'hidden' }}>
                {p.metadata.image ? (
                  <img src={p.metadata.image} alt={p.metadata.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <Laptop size={48} />
                )}
              </div>
              <h3 className="product-name">{p.metadata.name}</h3>
              <div className="product-price">{p.metadata.price} شيكل</div>
              <p className="product-desc">{p.document.split(' - ')[1] || p.document}</p>
              <button 
                className="btn-buy"
                onClick={() => handleBuyClick(p)}
              >
                شراء الآن
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* القسم الأيمن: المحادثة */}
      <div className={`chat-area glass-panel ${products.length === 0 ? 'full-screen' : ''}`}>
        
        {/* Header */}
        <div className="chat-header">
          <div className="avatar">SS</div>
          <div className="header-info">
            <h2>Smart Store Assistant</h2>
            <div className="status">
              <div className="status-dot"></div>
              <span>متصل الآن</span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="messages-container">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.sender === 'user' ? 'msg-user' : 'msg-bot'}`}>
              {msg.text}
            </div>
          ))}
          {isLoading && (
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <input 
            type="text" 
            className="chat-input"
            placeholder="اكتب رسالتك..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage(input)}
          />
          <button className="btn-send" onClick={() => sendMessage(input)}>
            <Send size={24} />
          </button>
        </div>

      </div>
    </div>
  );
}

export default App;
