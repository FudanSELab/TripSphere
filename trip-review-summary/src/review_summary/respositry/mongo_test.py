
from motor.motor_asyncio import AsyncIOMotorClient
from mongo import ReviewEmbeddingRepository

async def test_create_embedding():
    client = AsyncIOMotorClient("mongodb+srv://LJC:asasdd@cluster0.gif9hs8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["review_summary_db"]
    
    repo = ReviewEmbeddingRepository(db)
    
    embedding_data = [0.1, 0.2, 0.3, 0.4, 0.5]
    embedding_id = await repo.create_embedding(attraction_id="eiffel_tower_123", embedding=embedding_data, review_id="review_789")
    print(f"Embedding ID: {embedding_id}")
    
    client.close()

async def test_find_by_id(o_id : str):
    client = AsyncIOMotorClient("mongodb+srv://LJC:asasdd@cluster0.gif9hs8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["review_summary_db"]
    
    repo = ReviewEmbeddingRepository(db)
    result = await repo.find_by_id(o_id)
    print(result)
    client.close()

async def test_find_by_review_id(review_id : str):
    client = AsyncIOMotorClient("mongodb+srv://LJC:asasdd@cluster0.gif9hs8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["review_summary_db"]
    
    repo = ReviewEmbeddingRepository(db)
    result = await repo.find_by_review_id(review_id)
    print(result)
    client.close()

async def test_update_embedding(ob_id : str,embedding: list[float]):
    client = AsyncIOMotorClient("mongodb+srv://LJC:asasdd@cluster0.gif9hs8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["review_summary_db"]
    repo = ReviewEmbeddingRepository(db)
    result = await repo.update_embedding(embedding_id=ob_id, embedding=embedding)
    print(result)
    client.close()

async def test_update_embedding_by_review_id(review_id : str,embedding: list[float]):
    client = AsyncIOMotorClient("mongodb+srv://LJC:asasdd@cluster0.gif9hs8.mSongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["review_summary_db"]
    repo = ReviewEmbeddingRepository(db)
    result = await repo.update_embedding_by_review_id(review_id=review_id, embedding=embedding)
    print(result)
    client.close()

async def test_delete_embedding(ob_id : str):
    client = AsyncIOMotorClient("mongodb+srv://LJC:asasdd@cluster0.gif9hs8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["review_summary_db"]
    repo = ReviewEmbeddingRepository(db)
    result = await repo.delete_embedding(embedding_id=ob_id)
    print(result)
    client.close()

async def test_find_by_attraction_id(attraction_id : str):
    client = AsyncIOMotorClient("mongodb+srv://LJC:asasdd@cluster0.gif9hs8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client["review_summary_db"]
    repo = ReviewEmbeddingRepository(db)
    result = await repo.find_by_attraction_id(attraction_id=attraction_id)
    print(result)
    client.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_find_by_attraction_id("eiffel_tower_123"))