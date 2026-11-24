import requests

# Supondo que o FlareSolverr esteja rodando localmente na porta 8191
url_solver = "http://localhost:8191/v1"
payload = {
    "cmd": "request.get",
    "url": "https://www.marinha.mil.br/chm/dados-do-segnav/avisos-aos-navegantes",
    "maxTimeout": 60000
}
response = requests.post(url_solver, json=payload)
# O HTML da página estará em response.json()['solution']['response']