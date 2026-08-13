from fastapi import FastAPI
import uvicorn

# 1. Створюємо екземпляр застосунку
app = FastAPI()

# 2. Декоратор каже: обробляй GET-запити на адресу "/"
@app.get("/")
async def root():
    # 3. Повертаємо словник, який FastAPI автоматично перетворить у JSON
    return {"message": "Привіт, світе!", "status": "active"}