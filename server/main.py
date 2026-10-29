from fastapi import Depends, FastAPI, HTTPException, Response

from auth import check_password, clear_session, current_user, set_session
from llm import reply
from schemas import ChatBody, ChatOut, LoginBody, MeOut, OkOut

app = FastAPI(title="BrokerDesk")


@app.get("/health")
def health() -> OkOut:
    return OkOut()


@app.post("/api/login")
def login(body: LoginBody, response: Response) -> OkOut:
    if not check_password(body.password):
        raise HTTPException(status_code=401, detail="Wrong password")
    set_session(response)
    return OkOut()


@app.get("/api/me")
def me(user: str = Depends(current_user)) -> MeOut:
    return MeOut(user=user)


@app.post("/api/logout")
def logout(response: Response) -> OkOut:
    clear_session(response)
    return OkOut()


@app.post("/api/chat")
async def chat(body: ChatBody, user: str = Depends(current_user)) -> ChatOut:
    messages = [m.model_dump() for m in body.messages]
    return ChatOut(reply=await reply(messages))
