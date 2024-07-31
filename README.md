# ollama
[![Charmhub Badge](https://charmhub.io/ollama/badge.svg)](https://charmhub.io/ollama)

Charmed [Ollama](https://github.com/ollama/ollama).

## Installation
```bash
juju deploy ollama --channel=beta
juju ssh ollama/0 ollama run llama3.1
```

## Usage
```bash
juju ssh ollama/0 curl localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt":"Why is the sky blue?"
}'
```

## Other resources

- See the [Juju SDK documentation](https://juju.is/docs/sdk) for more information about developing and improving charms.
