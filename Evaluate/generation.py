import openai
import os
import time

# 设置API密钥
# openai.api_key = "your-openai-api-key-here"  # 替换为你的API密钥
# 或者从环境变量读取
openai.api_key = os.getenv("OPENAI_API_KEY")

def generation(message):
    """
    使用OpenAI API生成代码翻译
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4.1-mini-2025-04-14",  # 或使用 "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are an expert programmer skilled in code translation between different programming languages. Focus on producing accurate, functional code that maintains the original logic and handles dependencies correctly."},
                {"role": "user", "content": message}
            ],
            max_tokens=2000,
            temperature=0.1,  # 较低的temperature确保更确定性的输出
            timeout=60
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"OpenAI API调用失败: {e}")
        # 可以添加重试逻辑
        time.sleep(5)
        raise e