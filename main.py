from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user_router
from fastapi.routing import APIRoute
from fastapi.responses import PlainTextResponse


app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, adjust as needed
    allow_headers=["*"],  # Allows all headers, adjust as needed
)

# Include routers
app.include_router(user_router.router, prefix="/users", tags=["users"])



@app.get("/routes-simple", response_class=PlainTextResponse)
async def get_routes_simple():
    """
    Returns a concise list of all routes with their paths and methods.
    """
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ", ".join(route.methods)
            routes.append(f"{methods}: {route.path}")

    return "\n".join(routes)


