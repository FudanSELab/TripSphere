import asyncio
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings


def text_to_embedding(text: str, model: str = "text-embedding-ada-002") -> List[float]:
    """
    将文本转换为嵌入向量的工具函数（同步版本）
    使用之前要在.env文件中配置好api key
    Args:
        text: 输入文本
        model: 使用的嵌入模型，默认为 "text-embedding-ada-002"
    
    Returns:
        嵌入向量（浮点数列表）
    """
    if not text or not isinstance(text, str):
        raise ValueError("输入文本必须是非空字符串")
    
    # 创建嵌入实例
    embedding_llm = OpenAIEmbeddings(model=model)
    
    # 生成嵌入向量
    embeddings = embedding_llm.embed_documents([text])
    
    # 返回第一个（也是唯一一个）嵌入向量
    return embeddings[0]


async def text_to_embedding_async(text: str, model: str = "text-embedding-ada-002") -> List[float]:
    """
    将文本转换为嵌入向量的工具函数（异步版本）
    
    Args:
        text: 输入文本
        model: 使用的嵌入模型，默认为 "text-embedding-ada-002"
        api_key: OpenAI API密钥，如果为None则使用环境变量中的密钥
    
    Returns:
        嵌入向量（浮点数列表）
    """
    if not text or not isinstance(text, str):
        raise ValueError("输入文本必须是非空字符串")
    
    # 创建嵌入实例
    embedding_llm = OpenAIEmbeddings(model=model)
    
    # 异步生成嵌入向量
    embeddings = await embedding_llm.aembed_documents([text])
    
    # 返回第一个（也是唯一一个）嵌入向量
    return embeddings[0]


# 示例使用
if __name__ == "__main__":
    # 同步示例
    try:
        text = "这是一个示例文本，用于测试嵌入功能。"
        embedding = text_to_embedding(text)
        print(f"嵌入向量长度: {len(embedding)}")
        print(f"嵌入向量前5个值: {embedding[:5]}")
    except Exception as e:
        print(f"同步转换出错: {e}")
        print("请确保已设置OPENAI_API_KEY环境变量")
    
    # 异步示例
    async def async_test():
        try:
            text = "这是异步测试文本。"
            embedding = await text_to_embedding_async(text)
            print(f"异步嵌入向量长度: {len(embedding)}")
            print(f"异步嵌入向量前5个值: {embedding[:5]}")
        except Exception as e:
            print(f"异步转换出错: {e}")
            print("请确保已设置OPENAI_API_KEY环境变量")
    
    # 运行异步示例
    asyncio.run(async_test())
    
    # 演示不同文本的嵌入
    print("\n不同文本的嵌入向量比较:")
    texts = [
        "我喜欢自然语言处理",
        "人工智能很有意思", 
        "今天天气不错"
    ]
    
    try:
        embeddings = []
        for text in texts:
            emb = text_to_embedding(text)
            embeddings.append(emb)
            print(f"'{text}' -> 向量长度: {len(emb)}")
    except Exception as e:
        print(f"批量转换出错: {e}")
        print("请确保已设置OPENAI_API_KEY环境变量")



