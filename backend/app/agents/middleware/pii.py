from langchain.agents.middleware import PIIMiddleware

email = PIIMiddleware(
    "email",
    strategy="mask", 
)

credit_card = PIIMiddleware(
    "credit_card",
    strategy="redact"
)

pii_middleware = [email, credit_card]