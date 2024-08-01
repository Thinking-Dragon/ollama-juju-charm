# ollama
[![Charmhub Badge](https://charmhub.io/ollama/badge.svg)](https://charmhub.io/ollama)

Charmed [Ollama](https://github.com/ollama/ollama).

## Installation
```bash
juju deploy ollama --channel=beta
juju ssh ollama/0 ollama run llama3.1
```

## Usage
### Generating text using the juju action
```bash
juju run ollama/0 generate model="llama3.1" prompt="Why is the sky blue?"
```

### Generating text using the HTTP API
```bash
curl http://<unit-ip-address>:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt":"Why is the sky blue?"
}'
```

## Other resources

- See the [Juju SDK documentation](https://juju.is/docs/sdk) for more information about developing and improving charms.
