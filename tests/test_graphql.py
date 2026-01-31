from fastapi.testclient import TestClient
from strict.api.server import app


def test_graphql_health():
    client = TestClient(app)
    query = """
    query {
      health {
        status
        version
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["health"]["status"] == "ok"


def test_graphql_process_request():
    client = TestClient(app)
    mutation = """
    mutation {
      processRequest(
        inputData: "GraphQL test",
        inputTokens: 5,
        processorType: LOCAL
      ) {
        result
        processorUsed
        validation {
          status
          isValid
        }
      }
    }
    """
    response = client.post("/graphql", json={"query": mutation})
    assert response.status_code == 200
    data = response.json()
    # If Ollama is not running, we might get an empty result or error in validation
    # but the GraphQL structure should be correct.
    assert "processRequest" in data["data"]
    assert "result" in data["data"]["processRequest"]
